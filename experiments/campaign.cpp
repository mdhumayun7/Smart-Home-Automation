// campaign.cpp - randomised adversarial campaign against the real firmware logic.
//
// The unchanged firmware is compiled against the host stubs and driven through randomised
// scenarios in which an attacker continuously injects commands on the MQTT command topic
// (forged tags, replays of captured valid messages, malformed bytes) while a legitimate user
// arms the system and an intrusion occurs. For every trial the harness records:
//
//   - safety latency: simulated ms from the confirmed sensor edge to ENTRY_DELAY;
//   - alarm latency:  simulated ms from ENTRY_DELAY to ALARM;
//   - whether a legitimate signed command issued during the flood took effect;
//   - event-queue drops;
//   - any violation of the safety invariants.
//
// The attacker never holds the shared key: forged messages are signed with a different key,
// and replays reuse messages the attacker could have captured on the wire.
//
// Every trial is reproducible from its seed. Output is one JSON object per line.
//
// Build:  g++ -O2 -std=c++17 -I ../tests/host/stubs -o campaign campaign.cpp
// Run:    ./campaign --trials 2000 --seed 1 > results/campaign.jsonl

#include "../firmware/smart_home/smart_home.ino"

#include <random>
#include <string>
#include <vector>
#include <cstdio>
#include <cstring>
#include <unistd.h>
#include <sys/wait.h>

// ---------------------------------------------------------------- harness
static std::vector<std::string> g_events;      // "type:src" in order
static uint32_t g_dropAtStart = 0;

static void drainEvents() {
  Event e;
  while (xQueueReceive(eventQ, &e, 0) == pdTRUE)
    g_events.push_back(std::string(e.type) + ":" + e.src);
}

static bool sawEvent(const char* needle) {
  for (const auto& s : g_events) if (s == needle) return true;
  return false;
}

// One simulated millisecond of device time.
static void tick1ms() { loop(); g_now += 1; drainEvents(); }

// Build a signed command with an arbitrary key, so the attacker can be given a wrong one.
static std::string signWith(const char* key, const char* verb, uint32_t ctr) {
  char base[40];
  snprintf(base, sizeof base, "%s:%lu", verb, (unsigned long)ctr);
  uint8_t mac[32];
  authmac::hmac_sha256((const uint8_t*)key, strlen(key),
                       (const uint8_t*)base, strlen(base), mac);
  char out[96];
  int n = snprintf(out, sizeof out, "%s:", base);
  for (size_t i = 0; i < AUTH_TAG_BYTES; i++)
    n += snprintf(out + n, sizeof out - n, "%02x", mac[i]);
  return std::string(out);
}

static void deliver(const std::string& s) {
  onMqttMessage((char*)"cmd", (uint8_t*)s.data(), (unsigned)s.size());
}

// ---------------------------------------------------------------- attacker
struct Attacker {
  std::mt19937 rng;
  std::vector<std::string> captured;   // valid messages the attacker has seen on the wire
  const char* wrongKey = "attacker-does-not-have-the-key";

  // One injection: a forged tag, a replay of something captured, or random bytes.
  void inject(uint32_t now) {
    std::uniform_int_distribution<int> kind(0, 3);
    switch (kind(rng)) {
      case 0: {                                   // forged tag on a plausible command
        std::uniform_int_distribution<uint32_t> c(1, 100000);
        deliver(signWith(wrongKey, "DISARM", c(rng)));
        break;
      }
      case 1: {                                   // replay of a captured valid message
        if (!captured.empty()) {
          std::uniform_int_distribution<size_t> i(0, captured.size() - 1);
          deliver(captured[i(rng)]);
        }
        break;
      }
      case 2: {                                   // plain unsigned command
        static const char* verbs[] = {"DISARM", "ARM", "STATUS", "disarm", "ARM_AWAY"};
        std::uniform_int_distribution<int> v(0, 4);
        std::string s = verbs[v(rng)];
        deliver(s);
        break;
      }
      default: {                                  // random bytes
        std::uniform_int_distribution<int> len(1, 90);
        std::uniform_int_distribution<int> ch(1, 255);
        int n = len(rng);
        std::string s;
        for (int i = 0; i < n; i++) s.push_back((char)ch(rng));
        deliver(s);
        break;
      }
    }
    (void)now;
  }
};

// ---------------------------------------------------------------- one trial
struct Trial {
  uint64_t seed;
  uint32_t attackRate;        // injections per simulated second
  uint32_t safetyLatency;     // sensor edge -> ENTRY_DELAY (ms), 0 if not observed
  uint32_t alarmLatency;      // ENTRY_DELAY -> ALARM (ms), 0 if not observed
  bool     legitAccepted;     // a legitimate signed command issued during the flood took effect
  bool     reachedAlarm;
  bool     attackerArmed;     // an UNauthenticated remote command changed state (nuisance arm)
  bool     attackerDisarmed;  // an UNauthenticated remote command disarmed the system
  uint32_t drops;
  const char* violation;      // nullptr if none
};

static Trial runTrial(uint64_t seed, uint32_t attackRate) {
  Trial t = {};
  t.seed = seed;
  t.attackRate = attackRate;
  t.violation = nullptr;

  std::mt19937_64 rng(seed);
  Attacker atk;
  atk.rng.seed((uint32_t)(seed ^ 0x9e3779b9u));

  // Fresh device state for this trial.
  g_events.clear();
  g_nvs.clear();
  g_nvsU.clear();
  g_nvsWrites = 0;
  g_displayOk = true;
  g_pubs.clear();
  g_wifiUp = false;
  g_linkUp = false;
  g_brokerAccepts = false;

  // Random clock start, including values near the 32-bit wrap.
  static const uint32_t starts[] = {0u, 2147483000u, 4294950000u, 123456789u};
  g_now = starts[rng() % 4];

  g_pin[PIN_DOOR] = LOW;
  g_pin[PIN_ARM_BTN] = HIGH;
  g_pin[PIN_PIR] = LOW;
  setup();
  drainEvents();
  g_dropAtStart = eventsDropped;

  // Injection schedule: attackRate messages per simulated second, spread over 1 ms ticks.
  // Rates above 1000/s deliver several messages inside one tick, which is what stresses the
  // 4-deep command queue: the safety loop drains it once per pass, so a burst larger than the
  // queue within one pass is where legitimate commands can start being lost.
  uint32_t perTick = attackRate / 1000u;
  uint32_t remainder = attackRate % 1000u;
  uint32_t acc = 0;

  auto stepWithAttack = [&](uint32_t ms) {
    for (uint32_t i = 0; i < ms; i++) {
      for (uint32_t j = 0; j < perTick; j++) atk.inject(g_now);
      acc += remainder;
      if (acc >= 1000u) { acc -= 1000u; atk.inject(g_now); }
      tick1ms();
    }
  };

  // Wait out the PIR warm-up while the flood runs.
  stepWithAttack(PIR_WARMUP_MS + 200);

  // The legitimate user arms the system with a signed command during the flood.
  uint32_t legitCtr = 50000 + (uint32_t)(rng() % 1000);
  std::string legitArm = signWith(SECRET_CMD_KEY, "ARM", legitCtr);
  size_t before = g_events.size();
  deliver(legitArm);
  atk.captured.push_back(legitArm);   // the attacker captures it once it is on the wire
  stepWithAttack(50);
  t.legitAccepted = false;
  for (size_t i = before; i < g_events.size(); i++)
    if (g_events[i] == "exit_delay:remote_auth") t.legitAccepted = true;

  // If the command was starved out by the flood, fall back to the physical button so the
  // trial still exercises the intrusion path. Only press it if the system is still disarmed,
  // so the fallback cannot undo an arming that did take effect.
  if (state == SysState::DISARMED) {
    g_pin[PIN_ARM_BTN] = LOW;  stepWithAttack(80);
    g_pin[PIN_ARM_BTN] = HIGH; stepWithAttack(80);
  }

  stepWithAttack(EXIT_DELAY_MS + 300);
  if (state != SysState::ARMED) {
    if (getenv("CAMPAIGN_DEBUG")) {
      fprintf(stderr, "seed=%llu rate=%u state=%s events:",
              (unsigned long long)seed, attackRate, stateName(state));
      for (const auto& e : g_events) fprintf(stderr, " %s", e.c_str());
      fprintf(stderr, "\n");
    }
    t.violation = "not_armed_after_exit_delay";
    return t;
  }

  // Intrusion: the PIR goes high and stays high.
  uint32_t tTrigger = g_now;
  g_pin[PIN_PIR] = HIGH;
  uint32_t guard = 0;
  while (state == SysState::ARMED && guard < 5000) { stepWithAttack(1); guard++; }
  if (state != SysState::ENTRY_DELAY) { t.violation = "no_entry_delay_after_trigger"; return t; }
  t.safetyLatency = g_now - tTrigger;

  // No disarm: the alarm must follow.
  uint32_t tEntry = g_now;
  guard = 0;
  while (state == SysState::ENTRY_DELAY && guard < 30000) { stepWithAttack(1); guard++; }
  if (state != SysState::ALARM) { t.violation = "no_alarm_after_entry_delay"; return t; }
  t.alarmLatency = g_now - tEntry;
  t.reachedAlarm = true;

  // Let the alarm run a little under continued attack.
  stepWithAttack(2000);

  // ---- observations and invariants ----
  // Did an unauthenticated remote command change state? Arming this way is a nuisance, not a
  // safety breach; disarming this way would be a breach and must never happen.
  t.attackerArmed    = sawEvent("exit_delay:remote");
  t.attackerDisarmed = sawEvent("disarmed:remote");
  if (t.attackerDisarmed)                t.violation = "unauthenticated_disarm";
  if (sawEvent("disarmed:remote_auth") ) t.violation = "attacker_forged_auth_disarm";
  // The replay counter must never go backwards.
  if (g_nvsU.count("cmdctr") && g_nvsU["cmdctr"] < legitCtr && t.legitAccepted)
    t.violation = "counter_regressed";
  // The siren must not be on while disarmed.
  if (state == SysState::DISARMED && g_out[PIN_BUZZER] == HIGH)
    t.violation = "siren_while_disarmed";

  t.drops = eventsDropped - g_dropAtStart;
  return t;
}

// ---------------------------------------------------------------- main
int main(int argc, char** argv) {
  uint64_t trials = 500, seed0 = 1;
  std::vector<uint32_t> rates = {0, 10, 100, 1000, 5000, 20000};

  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--trials") && i + 1 < argc) trials = strtoull(argv[++i], nullptr, 10);
    else if (!strcmp(argv[i], "--seed") && i + 1 < argc) seed0 = strtoull(argv[++i], nullptr, 10);
  }

  g_verbose = false;
  // Each trial runs in a forked child so that it starts from the same pristine global state
  // the firmware has at power-up. Running several trials in one process would let state from
  // an earlier trial (the state machine, counters, queues) leak into the next one, which the
  // real device never does.
  for (uint64_t k = 0; k < trials; k++) {
    uint32_t rate = rates[k % rates.size()];
    fflush(stdout);
    pid_t pid = fork();
    if (pid == 0) {
      Trial t = runTrial(seed0 + k, rate);
      std::string viol = t.violation ? ("\"" + std::string(t.violation) + "\"") : "null";
      printf("{\"config\":\"%s\",\"seed\":%llu,\"attack_rate\":%u,\"safety_latency_ms\":%u,"
             "\"alarm_latency_ms\":%u,\"legit_cmd_accepted\":%s,\"reached_alarm\":%s,"
             "\"attacker_armed\":%s,\"attacker_disarmed\":%s,"
             "\"event_drops\":%u,\"violation\":%s}\n",
             AUTH_COMMANDS ? "hardened" : "baseline",
             (unsigned long long)t.seed, t.attackRate, t.safetyLatency, t.alarmLatency,
             t.legitAccepted ? "true" : "false", t.reachedAlarm ? "true" : "false",
             t.attackerArmed ? "true" : "false", t.attackerDisarmed ? "true" : "false",
             t.drops, viol.c_str());
      fflush(stdout);
      _exit(0);
    }
    int status = 0;
    waitpid(pid, &status, 0);
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
      fprintf(stderr, "trial seed=%llu CRASHED (status %d)\n",
              (unsigned long long)(seed0 + k), status);
      printf("{\"seed\":%llu,\"attack_rate\":%u,\"violation\":\"crash\"}\n",
             (unsigned long long)(seed0 + k), rate);
    }
  }
  return 0;
}
