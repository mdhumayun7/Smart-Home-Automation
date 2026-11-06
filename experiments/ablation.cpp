// ablation.cpp - compare four command-path defences against the same adversary.
//
// WHY THIS EXISTS
// ---------------
// campaign.cpp compares the hardened firmware against a baseline with no command defence at
// all. That comparison is real but weak: an attacker beating an undefended command path is a
// deductive consequence of the design, not a finding. A reviewer is entitled to ask how the
// chosen defence compares with the alternatives a developer would plausibly reach for instead.
//
// This program answers that. It runs the SAME adversary and the SAME intrusion scenario against
// four command-path designs and reports where each one fails:
//
//   none       no command defence                        (firmware built with AUTH_COMMANDS=0)
//   ratelimit  token-bucket limiter in front of the       (AUTH_COMMANDS=0)
//              command topic: at most R commands/second
//              reach the device
//   token      a fixed shared secret must appear in the   (AUTH_COMMANDS=0)
//              payload; no counter, no MAC
//   hmac       the real firmware path: HMAC-SHA256 over   (AUTH_COMMANDS=1)
//              a monotonic, NVS-persisted counter
//   transport  TLS + broker credentials, credentials NOT   (AUTH_COMMANDS=0)
//              leaked: the adversary cannot authenticate
//              to the broker, so nothing reaches the device
//   transport_ TLS + broker credentials, credentials LEAKED (AUTH_COMMANDS=0,
//   leaked     (phished, extracted from firmware, shared     MQTT_USE_TLS=1,
//              broker, or a second compromised client).      MQTT_HAS_LOGIN=1,
//              The adversary authenticates and publishes     ALLOW_REMOTE_DISARM=1)
//              freely; the device has no application-layer
//              check.
//
// WHAT THE TWO TRANSPORT MODES DO AND DO NOT MODEL
// ------------------------------------------------
// They model the ACCESS-CONTROL property of transport security: who is able to publish to the
// command topic. That is faithful, because it is exactly what TLS plus broker credentials
// decides in this architecture.
//
// They do NOT model TLS cryptography, the handshake, or any performance cost. The host harness
// has no TLS: tests/host/stubs/WiFiClientSecure.h is a no-op shim that records the CA pointer
// and nothing else. Any latency, throughput or CPU figure produced here for TLS would be
// fabricated, so none is produced. The static build cost of the TLS configuration IS measured,
// by the compiler, in CI -- see docs/EXPERIMENTS.md (E7).
//
// The transport_leaked mode is built with ALLOW_REMOTE_DISARM=1 because the firmware's own
// compile-time guard permits exactly that when MQTT_USE_TLS=1 and MQTT_HAS_LOGIN=1:
//
//   #if ALLOW_REMOTE_DISARM && !AUTH_COMMANDS && (!MQTT_USE_TLS || !MQTT_HAS_LOGIN)
//   #  error ...
//
// In other words the design treats transport security as a substitute for application-layer
// authentication when deciding whether remote disarm may be enabled. This mode tests whether
// that substitution survives the threat model.
//
// The three alternatives are modelled in the harness, in front of an unauthenticated firmware
// build, because that is exactly where a developer would put them: a broker-side rate limit or
// a shared token in the payload. They are harness models of alternative designs, NOT firmware
// features, and the results table labels them as such.
//
// WHAT THE ADVERSARY DOES
// -----------------------
// Identical in every mode. The attacker floods the command topic and, crucially, CAPTURES the
// legitimate command once it appears on the wire and replays it. That capture-and-replay step
// is what separates the four designs: a static token is defeated by it, a counter is not.
//
// Every trial is reproducible from its seed. Output is one JSON object per line.
//
// Build:  g++ -O2 -std=c++17 -I ../tests/host/stubs -o ablation_unauth ablation.cpp
//         g++ -O2 -std=c++17 -DAUTH_COMMANDS=1 -I ../tests/host/stubs -o ablation_auth ablation.cpp
// Run:    ./ablation_unauth --mode none      --trials 500 --seed 2000
//         ./ablation_auth   --mode hmac      --trials 500 --seed 2000

#include "../firmware/smart_home/smart_home.ino"

#include <random>
#include <string>
#include <vector>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <unistd.h>
#include <sys/wait.h>

// ---------------------------------------------------------------- harness
static std::vector<std::string> g_events;
static uint32_t g_dropAtStart = 0;

static void drainEvents() {
  Event e;
  while (xQueueReceive(eventQ, &e, 0) == pdTRUE)
    g_events.push_back(std::string(e.type) + ":" + e.src);
}

static void tick1ms() { loop(); g_now += 1; drainEvents(); }

static std::string signWith(const char* key, const char* verb, uint32_t ctr) {
  char base[40];
  snprintf(base, sizeof base, "%s:%lu", verb, (unsigned long)ctr);
  uint8_t mac[32];
  authmac::hmac_sha256((const uint8_t*)key, strlen(key),
                       (const uint8_t*)base, strlen(base), mac);
  char out[128];
  int n = snprintf(out, sizeof out, "%s:", base);
  for (unsigned i = 0; i < AUTH_TAG_BYTES; i++)
    n += snprintf(out + n, sizeof out - n, "%02x", mac[i]);
  return std::string(out);
}

// ---------------------------------------------------------------- defences
enum class Mode { None, RateLimit, Token, Hmac, Transport, TransportLeaked };

static Mode g_mode = Mode::None;

// Whether the party currently publishing holds valid broker credentials. The harness sets this
// around each publish: true for the legitimate operator, false for the adversary -- except in
// TransportLeaked, where the adversary holds them too and the flag is irrelevant.
static bool g_hasBrokerCreds = false;

// Attribution guard for the phase-1 availability measurement.
//
// legit_cmd_accepted is inferred from an "exit_delay" event appearing in the window just after
// the operator publishes ARM. In every mode where the adversary's commands are admitted (none,
// ratelimit, token after capture, and transport_leaked) the adversary can itself publish a bare
// ARM, so that event cannot be attributed to the operator: the metric silently measured "someone
// armed the system", not "the operator's command survived". While this flag is set the adversary
// still floods at the full configured rate, but emits no command that could arm a disarmed
// system, so any observed arm is the operator's. Nuisance arming is measured separately by
// attacker_armed and by the phase-2 replay test, so nothing is lost by excluding it here.
static bool g_suppressAttackerArm = false;

// The shared token a "token auth" design would embed in every command. The attacker does not
// know it at the start of the trial, but it travels in plaintext, so capturing one legitimate
// command reveals it. That is the whole point of including this design in the comparison.
static const char* SHARED_TOKEN = "s3cr3t-token";

// Token-bucket limiter. RATE_LIMIT_PER_S commands per simulated second, burst of the same size.
static const uint32_t RATE_LIMIT_PER_S = 5;
static double   g_bucket = RATE_LIMIT_PER_S;
static uint32_t g_bucketLastMs = 0;

static void bucketRefill(uint32_t now) {
  uint32_t dt = now - g_bucketLastMs;
  if (!dt) return;
  g_bucketLastMs = now;
  g_bucket += (double)dt * RATE_LIMIT_PER_S / 1000.0;
  if (g_bucket > RATE_LIMIT_PER_S) g_bucket = RATE_LIMIT_PER_S;
}

// Hand the payload to the firmware's MQTT callback, exactly as the broker would.
static void deliver(const std::string& s) {
  onMqttMessage((char*)"cmd", (uint8_t*)s.data(), (unsigned)s.size());
}

// Separator for the token design. It cannot be ':' because the firmware routes any payload
// containing a colon to the signed path; the token design has no signature, so it would be
// rejected as a malformed signed command rather than evaluated on its own terms.
static const char TOKEN_SEP = '|';

// Every command, legitimate or hostile, passes through here. Returns true if it reaches the
// firmware, and may rewrite the payload.
//
// The rate limiter and the token check are modelled as an edge filter -- a broker rule or a
// gateway -- which is where a developer would actually put them. In the token design the edge
// validates the token and forwards the bare verb to the device, so what the firmware sees is
// a plain unsigned command in every non-HMAC mode. Mode::Hmac is a pass-through: the firmware
// itself does the checking, end to end, with no edge component.
static bool defenceAllows(std::string& payload, uint32_t now) {
  switch (g_mode) {
    case Mode::None:
    case Mode::Hmac:
      return true;
    case Mode::RateLimit:
      bucketRefill(now);
      if (g_bucket < 1.0) return false;      // indiscriminate: it cannot tell who sent this
      g_bucket -= 1.0;
      return true;
    case Mode::Token: {
      size_t p = payload.find(TOKEN_SEP);
      if (p == std::string::npos) return false;
      if (payload.substr(p + 1) != SHARED_TOKEN) return false;
      payload = payload.substr(0, p);        // strip the token, forward the bare verb
      return true;
    }
    case Mode::Transport:
      // Broker-level admission. Only a client holding valid credentials can publish at all.
      // g_hasBrokerCreds is false for the adversary and true for the legitimate operator.
      return g_hasBrokerCreds;
    case Mode::TransportLeaked:
      // Credentials have leaked, so the adversary authenticates like anyone else. The broker
      // admits every publisher and the device performs no application-layer check.
      return true;
  }
  return true;
}

static void deliverGuarded(const std::string& s, uint32_t now) {
  std::string p = s;
  if (!defenceAllows(p, now)) return;
  deliver(p);
}

// ---------------------------------------------------------------- adversary
struct Attacker {
  std::mt19937 rng;
  std::vector<std::string> captured;   // messages seen on the wire, available for replay

  void inject(uint32_t now) {
    g_hasBrokerCreds = false;          // the adversary holds no broker credentials
    std::uniform_int_distribution<int> pick(0, 3);
    switch (pick(rng)) {
      case 0: {   // forged: correctly shaped, signed with a key the attacker does not have
        std::uniform_int_distribution<uint32_t> c(1, 4000000000u);
        const char* verb = g_suppressAttackerArm ? "DISARM" : ((rng() & 1) ? "DISARM" : "ARM");
        deliverGuarded(signWith("attacker-key-not-the-device-key", verb, c(rng)), now);
        break;
      }
      case 1: {   // replay of something captured on the wire
        if (g_suppressAttackerArm) break;   // a captured ARM would be unattributable
        if (captured.empty()) { deliverGuarded("ARM", now); break; }
        deliverGuarded(captured[rng() % captured.size()], now);
        break;
      }
      case 2: {   // bare verb, no credential of any kind
        deliverGuarded(g_suppressAttackerArm ? "DISARM"
                                             : ((rng() & 1) ? "DISARM" : "ARM"), now);
        break;
      }
      default: {  // random bytes
        std::uniform_int_distribution<int> len(1, 60), ch(32, 126);
        int n = len(rng);
        std::string s;
        for (int i = 0; i < n; i++) s.push_back((char)ch(rng));
        if (g_suppressAttackerArm && s == "ARM") break;
        deliverGuarded(s, now);
        break;
      }
    }
  }
};

// ---------------------------------------------------------------- one trial
struct Trial {
  uint64_t seed;
  uint32_t attackRate;
  bool     legitAccepted;         // at least one operator attempt was accepted
  int      legitAttempts;         // operator publish attempts under flood
  int      legitAdmitted;         // how many of them reached the state machine
  bool     attackerArmed;
  bool     attackerReplayArmed;   // accepted an arm using only captured/forged material
  bool     availTestValid;        // false if the system was not DISARMED when the operator published
  bool     replayTestValid;       // false if the system could not be returned to DISARMED
  bool     intrusionTestValid;    // false if the system was not ARMED when the intrusion began
  bool     attackerDisarmed;
  bool     reachedAlarm;
  uint32_t safetyLatency;
  const char* violation;
};

// The legitimate command, as each design would send it.
static std::string legitCommand(const char* verb, uint32_t ctr) {
  switch (g_mode) {
    case Mode::None:
    case Mode::RateLimit: return std::string(verb);
    case Mode::Token:     return std::string(verb) + TOKEN_SEP + SHARED_TOKEN;
    case Mode::Transport:
    case Mode::TransportLeaked:
      // Transport security carries no application-layer credential: the device receives a
      // bare verb, exactly as in the undefended case. The protection is entirely at the broker.
      return std::string(verb);
    case Mode::Hmac:      return signWith(SECRET_CMD_KEY, verb, ctr);
  }
  return verb;
}

static Trial runTrial(uint64_t seed, uint32_t attackRate) {
  Trial t = {};
  t.seed = seed;
  t.attackRate = attackRate;
  t.violation = nullptr;
  t.replayTestValid = true;
  t.availTestValid = false;
  t.intrusionTestValid = false;

  std::mt19937_64 rng(seed);
  Attacker atk;
  atk.rng.seed((uint32_t)(seed ^ 0x9e3779b9u));

  g_events.clear();
  g_nvs.clear();
  g_nvsU.clear();
  g_nvsWrites = 0;
  g_displayOk = true;
  g_pubs.clear();
  g_wifiUp = false;
  g_linkUp = false;
  g_brokerAccepts = false;

  static const uint32_t starts[] = {0u, 2147483000u, 4294950000u, 123456789u};
  g_now = starts[rng() % 4];
  g_bucket = RATE_LIMIT_PER_S;
  g_bucketLastMs = g_now;

  g_pin[PIN_DOOR] = LOW;
  g_pin[PIN_ARM_BTN] = HIGH;
  g_pin[PIN_PIR] = LOW;
  setup();
  drainEvents();
  g_dropAtStart = eventsDropped;

  // Hold the adversary's arm-capable commands for the whole prologue. It still floods at the
  // full configured rate throughout -- draining the token bucket and saturating the queues --
  // but cannot itself arm the system. That keeps the system DISARMED by construction, so the
  // availability measurement needs no quiet settle beforehand: a quiet window would let the
  // token bucket refill and would make the rate-limit design look better than it is.
  g_suppressAttackerArm = true;

  uint32_t perTick = attackRate / 1000u;
  uint32_t remainder = attackRate % 1000u;
  uint32_t acc = 0;

  // Advance time with no attacker activity. Used for the experimenter's own control actions
  // (button presses), so the attacker cannot act inside a window we are using to set up state.
  auto stepQuiet = [&](uint32_t ms) { for (uint32_t i = 0; i < ms; i++) tick1ms(); };

  auto stepWithAttack = [&](uint32_t ms) {
    for (uint32_t i = 0; i < ms; i++) {
      for (uint32_t j = 0; j < perTick; j++) atk.inject(g_now);
      acc += remainder;
      if (acc >= 1000u) { acc -= 1000u; atk.inject(g_now); }
      tick1ms();
    }
  };

  stepWithAttack(PIR_WARMUP_MS + 200);

  // Phase 1: the legitimate user arms. The attacker captures whatever goes on the wire.
  uint32_t legitCtr = 50000 + (uint32_t)(rng() % 1000);
  std::string legitArm = legitCommand("ARM", legitCtr);
  // The adversary has been flooding at full rate since the trial began but has not been able
  // to arm, so the system is DISARMED on entry and the token bucket is in whatever state the
  // flood left it. Any arm observed in the window below is therefore the operator's.
  t.availTestValid = (state == SysState::DISARMED);

  // Availability is measured over several attempts, not one.
  //
  // A single-command boolean is not an availability measurement here. The token-bucket design
  // admits a fixed number of commands per second regardless of attack intensity, and whether
  // one particular command is among them depends on the bucket's phase at the instant it is
  // published. Measured directly, that phase is not even monotonic in attack rate: a heavy
  // flood is rejected without consuming tokens, which pins the bucket just below the admission
  // threshold, so a single millisecond of refill can tip it over, while a moderate flood
  // leaves a lower residue. Counting how many of LEGIT_ATTEMPTS operator publishes are
  // admitted measures the property we actually care about and is insensitive to that phase.
  static constexpr int LEGIT_ATTEMPTS = 5;
  static constexpr uint32_t LEGIT_GAP_MS = 200;
  t.legitAttempts = LEGIT_ATTEMPTS;
  for (int a = 0; a < LEGIT_ATTEMPTS; a++) {
    size_t before = g_events.size();
    g_hasBrokerCreds = true;           // the legitimate operator is authenticated
    std::string attempt = legitCommand("ARM", legitCtr + (uint32_t)a);
    deliverGuarded(attempt, g_now);
    g_hasBrokerCreds = false;
    if (a == 0) atk.captured.push_back(attempt);
    stepWithAttack(LEGIT_GAP_MS);
    bool got = false;
    for (size_t i = before; i < g_events.size(); i++)
      if (g_events[i].rfind("exit_delay:", 0) == 0) got = true;
    if (got) { t.legitAdmitted++; t.legitAccepted = true; }
    // Return quietly to DISARMED so every attempt is evaluated from the same state. The
    // adversary cannot arm during the prologue, so nothing it did is being undone here.
    if (state != SysState::DISARMED) {
      g_pin[PIN_ARM_BTN] = LOW;  stepQuiet(80);
      g_pin[PIN_ARM_BTN] = HIGH; stepQuiet(80);
    }
  }
  g_suppressAttackerArm = false;       // from here the adversary may arm as well as disarm

  if (state == SysState::DISARMED) {
    g_pin[PIN_ARM_BTN] = LOW;  stepQuiet(80);
    g_pin[PIN_ARM_BTN] = HIGH; stepQuiet(80);
  }
  stepWithAttack(EXIT_DELAY_MS + 300);
  if (state != SysState::ARMED) t.violation = "not_armed_after_exit_delay";

  // Phase 2: the capture-and-replay test. This is the discriminator between the designs.
  //
  // The attacker has now seen one legitimate command on the wire. We return the system to
  // DISARMED using the physical button, then let the attacker run with only captured material
  // and forgeries. If it can get an arm accepted, the design is defeated by replay.
  //
  // Expected by construction, and measured rather than assumed:
  //   none / ratelimit  a bare verb is always accepted
  //   token             the captured message carries the token in plaintext, so replay works
  //   hmac              the captured message's counter is no longer strictly greater, so the
  //                     firmware rejects it as cmd_replay
  if (state != SysState::DISARMED) {
    g_pin[PIN_ARM_BTN] = LOW;  stepQuiet(80);
    g_pin[PIN_ARM_BTN] = HIGH; stepQuiet(80);
  }
  // If the button did not return the system to DISARMED the replay test is not valid for this
  // trial, so record it rather than reporting a misleading negative.
  if (state != SysState::DISARMED) t.replayTestValid = false;
  size_t beforeAtk = g_events.size();
  stepWithAttack(2000);
  for (size_t i = beforeAtk; i < g_events.size(); i++) {
    const std::string& e = g_events[i];
    if (e.find("button") != std::string::npos) continue;
    if (e.rfind("exit_delay:", 0) == 0) t.attackerReplayArmed = true;
    if (e.rfind("disarmed:", 0) == 0)   t.attackerDisarmed = true;
  }
  if (t.attackerDisarmed) t.violation = "attacker_disarmed";
  if (getenv("ABLATION_DEBUG")) {
    fprintf(stderr, "seed=%llu rate=%u phase2 events:", (unsigned long long)seed, attackRate);
    for (size_t i = beforeAtk; i < g_events.size(); i++)
      fprintf(stderr, " %s", g_events[i].c_str());
    fprintf(stderr, "\n");
  }

  // Settle into ARMED before the intrusion phase, with the attacker quiet.
  //
  // Without this the attacker can leave the system mid-transition (typically EXIT_DELAY,
  // because a replayed arm landed just before the window closed), the intrusion test is then
  // skipped, and the aggregate looks as though the alarm failed to fire in the weaker designs.
  // It had not: the trial simply never reached the test. Settling quietly makes the intrusion
  // phase valid in every mode, so the safety result is comparable across the four designs.
  if (state == SysState::DISARMED) {
    g_pin[PIN_ARM_BTN] = LOW;  stepQuiet(80);
    g_pin[PIN_ARM_BTN] = HIGH; stepQuiet(80);
  }
  stepQuiet(EXIT_DELAY_MS + 400);          // let any exit delay complete
  if (state == SysState::ENTRY_DELAY || state == SysState::ALARM) {
    // A stray trigger got in; disarm and re-arm so the measurement starts from ARMED.
    g_pin[PIN_ARM_BTN] = LOW;  stepQuiet(80);
    g_pin[PIN_ARM_BTN] = HIGH; stepQuiet(80);
    g_pin[PIN_ARM_BTN] = LOW;  stepQuiet(80);
    g_pin[PIN_ARM_BTN] = HIGH; stepQuiet(80);
    stepQuiet(EXIT_DELAY_MS + 400);
  }
  t.intrusionTestValid = (state == SysState::ARMED);

  // Phase 3: the intrusion. Measure the safety path end to end.
  if (state == SysState::ARMED) {
    uint32_t tTrig = g_now;
    g_pin[PIN_PIR] = HIGH;
    for (uint32_t i = 0; i < 4000 && state == SysState::ARMED; i++) stepWithAttack(1);
    if (state == SysState::ENTRY_DELAY) t.safetyLatency = g_now - tTrig;
    for (uint32_t i = 0; i < ENTRY_DELAY_MS + 500 && state != SysState::ALARM; i++)
      stepWithAttack(1);
    t.reachedAlarm = (state == SysState::ALARM);
    if (!t.reachedAlarm && !t.violation) t.violation = "no_alarm_after_intrusion";
  }

  // Did an attacker message ever arm a disarmed system (nuisance arm)? The harness presses
  // the physical button as a fallback when the legitimate command is starved, so a
  // button-sourced arm must never be counted against the attacker.
  for (const auto& e : g_events)
    if (e.rfind("exit_delay:", 0) == 0 &&
        e.find("button") == std::string::npos && !t.legitAccepted)
      t.attackerArmed = true;

  return t;
}

// ---------------------------------------------------------------- driver
int main(int argc, char** argv) {
  uint64_t seed0 = 2000;
  int trials = 500;
  const char* modeName = "none";
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--trials") && i + 1 < argc) trials = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--seed") && i + 1 < argc) seed0 = strtoull(argv[++i], nullptr, 10);
    else if (!strcmp(argv[i], "--mode") && i + 1 < argc) modeName = argv[++i];
  }
  if (!strcmp(modeName, "none")) g_mode = Mode::None;
  else if (!strcmp(modeName, "ratelimit")) g_mode = Mode::RateLimit;
  else if (!strcmp(modeName, "token")) g_mode = Mode::Token;
  else if (!strcmp(modeName, "hmac")) g_mode = Mode::Hmac;
  else if (!strcmp(modeName, "transport")) g_mode = Mode::Transport;
  else if (!strcmp(modeName, "transport_leaked")) g_mode = Mode::TransportLeaked;
  else { fprintf(stderr, "unknown --mode %s\n", modeName); return 2; }

#if AUTH_COMMANDS
  if (g_mode != Mode::Hmac) {
    fprintf(stderr, "build has AUTH_COMMANDS=1; only --mode hmac is meaningful\n");
    return 2;
  }
#else
  if (g_mode == Mode::Hmac) {
    fprintf(stderr, "--mode hmac needs a build with -DAUTH_COMMANDS=1\n");
    return 2;
  }
#endif
#if ALLOW_REMOTE_DISARM
  // Only the leaked-credential mode is meaningful in a build that permits remote disarm
  // without application-layer authentication, which the firmware allows only under
  // MQTT_USE_TLS with broker credentials.
  if (g_mode != Mode::TransportLeaked) {
    fprintf(stderr, "build has ALLOW_REMOTE_DISARM=1; only --mode transport_leaked applies\n");
    return 2;
  }
#else
  if (g_mode == Mode::TransportLeaked) {
    fprintf(stderr, "--mode transport_leaked needs a build with -DMQTT_USE_TLS=1 "
                    "-DSECRET_MQTT_USER=... -DALLOW_REMOTE_DISARM=1\n");
    return 2;
  }
#endif

  static const uint32_t rates[] = {0, 10, 100, 1000, 5000, 20000};
  const int nRates = (int)(sizeof rates / sizeof rates[0]);

  // One forked process per trial: the firmware's globals are file-scope, so without this the
  // state of one trial leaks into the next. This was a real false positive before it was fixed.
  for (int k = 0; k < trials; k++) {
    uint32_t rate = rates[k % nRates];
    fflush(stdout);
    pid_t pid = fork();
    if (pid == 0) {
      Trial t = runTrial(seed0 + k, rate);
      printf("{\"mode\":\"%s\",\"seed\":%llu,\"attack_rate\":%u,"
             "\"legit_cmd_accepted\":%s,\"legit_attempts\":%d,\"legit_admitted\":%d,\"avail_test_valid\":%s,\"attacker_armed\":%s,\"attacker_replay_armed\":%s,\"replay_test_valid\":%s,\"intrusion_test_valid\":%s,\"attacker_disarmed\":%s,"
             "\"reached_alarm\":%s,\"safety_latency_ms\":%u,\"violation\":%s%s%s}\n",
             modeName, (unsigned long long)t.seed, t.attackRate,
             t.legitAccepted ? "true" : "false",
             t.legitAttempts, t.legitAdmitted,
             t.availTestValid ? "true" : "false",
             t.attackerArmed ? "true" : "false",
             t.attackerReplayArmed ? "true" : "false",
             t.replayTestValid ? "true" : "false",
             t.intrusionTestValid ? "true" : "false",
             t.attackerDisarmed ? "true" : "false",
             t.reachedAlarm ? "true" : "false",
             t.safetyLatency,
             t.violation ? "\"" : "null", t.violation ? t.violation : "",
             t.violation ? "\"" : "");
      fflush(stdout);
      _exit(0);
    }
    int st = 0;
    waitpid(pid, &st, 0);
    if (!WIFEXITED(st) || WEXITSTATUS(st) != 0)
      printf("{\"mode\":\"%s\",\"seed\":%llu,\"attack_rate\":%u,\"violation\":\"crash\"}\n",
             modeName, (unsigned long long)(seed0 + k), rate);
  }
  return 0;
}
