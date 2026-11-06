// sensitivity.cpp - parameter sensitivity for the deauthentication detector.
//
// WHY THIS EXISTS
// ---------------
// The detector's threshold and window were chosen with a stated rationale but never measured.
// A detector that fires on ordinary network churn is worse than no detector: it trains the
// owner to ignore it, and on this device each report costs an event-queue slot. The internal
// review recorded this as an open gap; this program closes it for the simulated case.
//
// WHAT IS MEASURED
// ---------------
// Two quantities, swept over the (threshold, window) grid:
//
//   false-positive rate   fraction of benign runs in which the detector fires at least once,
//                         with management frames arriving as a Poisson process at a benign
//                         rate. Deauthentication and disassociation frames DO occur normally:
//                         access points send them on roaming, idle timeout, load balancing
//                         and reboot. The benign rates swept here cover that range.
//
//   detection latency     simulated ms from the start of an attack burst to the first report,
//                         at a given attack rate. Lower is better, but lowering the threshold
//                         to get it raises the false-positive rate: that trade-off is the
//                         point of the sweep.
//
// IMPORTANT SCOPE LIMIT
// ---------------------
// The benign arrival model is an ASSUMPTION, not a measurement. No capture of real management
// frame traffic was available. These results therefore characterise the detector's LOGIC
// against a stated model; they are not a measured false-positive rate for any real network.
// A real rate requires a passive capture on a production network, which is listed as future
// work. Results are labelled "simulation, synthetic arrival model" accordingly.
//
// Build:  g++ -O2 -std=c++17 -I ../firmware/smart_home -o sensitivity sensitivity.cpp
// Run:    ./sensitivity --seed 11 --runs 2000 > results/sensitivity.jsonl

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <random>
#include <vector>
#include <algorithm>

// The detector is pure logic with no Arduino dependency, so it compiles standalone.
#include "../firmware/smart_home/wifi_guard.h"

// Benign management-frame rates to sweep, in frames per minute. The low end is a quiet home
// network; the high end is a busy multi-AP environment with frequent roaming.
static const double BENIGN_FPM[] = {0.5, 2.0, 6.0, 20.0, 60.0};

// Attack rates to sweep, in frames per second, spanning a slow trickle to a saturating flood.
static const double ATTACK_FPS[] = {5.0, 20.0, 100.0, 500.0};

// The detector's ring buffer holds 32 timestamps and deauth_init clamps the threshold to 32,
// so thresholds are swept only within that implementation limit.
static const uint32_t THRESHOLDS[] = {3, 5, 8, 12, 20};
static const uint32_t WINDOWS_MS[] = {500, 1000, 2000, 5000};

// One benign run: OBS_MS of simulated time with Poisson arrivals at fpm. Returns true if the
// detector fired at least once, which in deployment means one spurious wifi_deauth event.
static bool benignRun(std::mt19937_64& rng, uint32_t threshold, uint32_t windowMs, double fpm) {
  const uint32_t OBS_MS = 600000;            // ten simulated minutes per run
  DeauthDetector d;
  deauth_init(d, windowMs, threshold, 10000);

  const double perMs = fpm / 60000.0;
  std::exponential_distribution<double> gap(perMs);

  double tNext = gap(rng);
  for (uint32_t now = 0; now < OBS_MS; now++) {
    while (tNext <= (double)now) {
      if (deauth_observe(d, now)) return true;
      tNext += gap(rng);
    }
  }
  return false;
}

// One attack run: benign background plus an attack burst starting at t=1000 ms. Returns the
// simulated ms from burst start to the first report, or 0 if the detector never fired.
static uint32_t attackRun(std::mt19937_64& rng, uint32_t threshold, uint32_t windowMs,
                          double benignFpm, double attackFps) {
  const uint32_t OBS_MS = 60000;
  const uint32_t BURST_AT = 1000;
  DeauthDetector d;
  deauth_init(d, windowMs, threshold, 10000);

  std::exponential_distribution<double> benignGap(benignFpm / 60000.0);
  std::exponential_distribution<double> atkGap(attackFps / 1000.0);

  double tBenign = benignGap(rng);
  double tAtk = (double)BURST_AT + atkGap(rng);

  for (uint32_t now = 0; now < OBS_MS; now++) {
    while (tBenign <= (double)now) {
      if (deauth_observe(d, now) && now >= BURST_AT) return now - BURST_AT;
      tBenign += benignGap(rng);
    }
    while (tAtk <= (double)now) {
      if (deauth_observe(d, now)) return now >= BURST_AT ? now - BURST_AT : 0;
      tAtk += atkGap(rng);
    }
  }
  return 0;
}

int main(int argc, char** argv) {
  uint64_t seed = 11;
  int runs = 2000;
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--seed") && i + 1 < argc) seed = strtoull(argv[++i], nullptr, 10);
    else if (!strcmp(argv[i], "--runs") && i + 1 < argc) runs = atoi(argv[++i]);
  }

  std::mt19937_64 rng(seed);

  for (uint32_t th : THRESHOLDS) {
    for (uint32_t w : WINDOWS_MS) {
      for (double fpm : BENIGN_FPM) {
        int fired = 0;
        for (int r = 0; r < runs; r++) if (benignRun(rng, th, w, fpm)) fired++;
        printf("{\"kind\":\"benign\",\"threshold\":%u,\"window_ms\":%u,"
               "\"benign_fpm\":%.1f,\"runs\":%d,\"fired\":%d,\"fp_rate\":%.6f}\n",
               th, w, fpm, runs, fired, (double)fired / runs);
      }
      for (double fps : ATTACK_FPS) {
        std::vector<uint32_t> lat;
        int missed = 0;
        for (int r = 0; r < runs / 4; r++) {
          uint32_t l = attackRun(rng, th, w, 2.0, fps);
          if (l == 0) missed++; else lat.push_back(l);
        }
        uint32_t med = 0;
        if (!lat.empty()) {
          std::sort(lat.begin(), lat.end());
          med = lat[lat.size() / 2];
        }
        printf("{\"kind\":\"attack\",\"threshold\":%u,\"window_ms\":%u,"
               "\"attack_fps\":%.1f,\"runs\":%d,\"missed\":%d,\"median_detect_ms\":%u}\n",
               th, w, fps, runs / 4, missed, med);
      }
    }
  }
  return 0;
}
