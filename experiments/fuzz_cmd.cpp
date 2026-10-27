// fuzz_cmd.cpp - randomised robustness testing of the MQTT command parser.
//
// The command topic is the one input an arbitrary network peer fully controls, so it is the
// natural fuzzing target. This harness feeds the real parser (onMqttMessage) millions of
// adversarial inputs and checks two things after every one:
//
//   1. Memory safety. Built with AddressSanitizer and UndefinedBehaviorSanitizer, any
//      out-of-bounds read, overflow or undefined operation aborts the run.
//   2. Security invariant. No input may cause a state change or advance the replay counter
//      unless it carried a valid authentication tag. The fuzzer never holds the real key,
//      so no input it generates should ever be accepted.
//
// Inputs are a mix of: random bytes; structurally valid commands with wrong tags; truncated
// and overlong fields; non-decimal and overflowing counters; embedded NULs; and mutations of
// a real signed message (bit flips), which is the hardest case for a tag check.
//
// Build:  g++ -O2 -g -std=c++17 -fsanitize=address,undefined -I ../tests/host/stubs
//             -DAUTH_COMMANDS=1 -o fuzz_cmd fuzz_cmd.cpp
// Run:    ./fuzz_cmd --iters 2000000 --seed 1

#include "../firmware/smart_home/smart_home.ino"

#include <random>
#include <string>
#include <vector>
#include <cstdio>
#include <cstring>

static std::mt19937_64 rng;

static std::string randomBytes(size_t maxLen) {
  std::uniform_int_distribution<size_t> len(0, maxLen);
  std::uniform_int_distribution<int> ch(0, 255);
  size_t n = len(rng);
  std::string s;
  s.reserve(n);
  for (size_t i = 0; i < n; i++) s.push_back((char)ch(rng));
  return s;
}

static std::string hexOf(const uint8_t* p, size_t n) {
  static const char* H = "0123456789abcdef";
  std::string s;
  for (size_t i = 0; i < n; i++) { s.push_back(H[p[i] >> 4]); s.push_back(H[p[i] & 15]); }
  return s;
}

// A structurally valid message signed with a key the attacker might try.
static std::string signedWith(const char* key, const std::string& verb, const std::string& ctr) {
  std::string base = verb + ":" + ctr;
  uint8_t mac[32];
  authmac::hmac_sha256((const uint8_t*)key, strlen(key),
                       (const uint8_t*)base.data(), base.size(), mac);
  return base + ":" + hexOf(mac, AUTH_TAG_BYTES);
}

int main(int argc, char** argv) {
  unsigned long long iters = 200000;
  unsigned long long seed = 1;
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--iters") && i + 1 < argc) iters = strtoull(argv[++i], nullptr, 10);
    else if (!strcmp(argv[i], "--seed") && i + 1 < argc) seed = strtoull(argv[++i], nullptr, 10);
  }
  rng.seed(seed);

  g_verbose = false;
  g_pin[PIN_DOOR] = LOW;
  g_pin[PIN_ARM_BTN] = HIGH;
  g_pin[PIN_PIR] = LOW;
  g_now = 1000;
  setup();

  // Drive the device into ARMED so that an accepted DISARM would be clearly visible.
  g_now += PIR_WARMUP_MS + 100;
  for (int i = 0; i < 200; i++) { loop(); g_now += 1; }
  g_pin[PIN_ARM_BTN] = LOW;  for (int i = 0; i < 80; i++) { loop(); g_now += 1; }
  g_pin[PIN_ARM_BTN] = HIGH; for (int i = 0; i < 80; i++) { loop(); g_now += 1; }
  for (uint32_t i = 0; i < EXIT_DELAY_MS + 200; i++) { loop(); g_now += 1; }
  if (state != SysState::ARMED) { fprintf(stderr, "setup failed: not armed\n"); return 2; }

  const uint32_t counterBefore = cmdCounter;
  unsigned long long accepted = 0, parsedShapes = 0;

  // A near-miss message used as the mutation seed: correct structure and a correctly computed
  // tag, but under a key the attacker holds rather than the device's. Mutating a genuinely
  // signed message would be wrong here, because some mutations (hex case changes, which decode
  // to the same bytes) reproduce the genuine command, and accepting that is correct behaviour.
  std::string realMsg = signedWith("attacker-key-not-the-device-key", "DISARM", "999999");

  static const char* verbs[] = {"ARM", "DISARM", "STATUS", "ARM_AWAY", "arm", "disarm",
                                "", "DISARM ", " DISARM", "DISARMX", "DISARM:"};
  static const char* ctrs[] = {"0", "1", "999999", "4294967295", "4294967296",
                               "99999999999999999999", "-1", "+1", "0x10", "", " 1", "1 ",
                               "00000000000000000001"};

  for (unsigned long long it = 0; it < iters; it++) {
    std::string msg;
    switch (it % 6) {
      case 0:   // pure random bytes
        msg = randomBytes(100);
        break;
      case 1: { // structurally valid shape, wrong key
        std::uniform_int_distribution<int> v(0, (int)(sizeof(verbs)/sizeof(*verbs)) - 1);
        std::uniform_int_distribution<int> c(0, (int)(sizeof(ctrs)/sizeof(*ctrs)) - 1);
        msg = signedWith("the-wrong-key", verbs[v(rng)], ctrs[c(rng)]);
        parsedShapes++;
        break;
      }
      case 2: { // valid shape, random tag
        std::uniform_int_distribution<int> v(0, (int)(sizeof(verbs)/sizeof(*verbs)) - 1);
        std::uniform_int_distribution<int> c(0, (int)(sizeof(ctrs)/sizeof(*ctrs)) - 1);
        uint8_t tag[AUTH_TAG_BYTES];
        for (size_t i = 0; i < sizeof tag; i++) tag[i] = (uint8_t)(rng() & 0xFF);
        msg = std::string(verbs[v(rng)]) + ":" + ctrs[c(rng)] + ":" + hexOf(tag, sizeof tag);
        parsedShapes++;
        break;
      }
      case 3: { // bit-flip mutation of a genuine signed message
        msg = realMsg;
        std::uniform_int_distribution<size_t> pos(0, msg.size() ? msg.size() - 1 : 0);
        std::uniform_int_distribution<int> bit(0, 7);
        int flips = 1 + (int)(rng() % 3);
        for (int f = 0; f < flips && !msg.empty(); f++) msg[pos(rng)] ^= (char)(1 << bit(rng));
        parsedShapes++;
        break;
      }
      case 4: { // truncations and extensions of a genuine message
        msg = realMsg;
        if (rng() & 1) {
          std::uniform_int_distribution<size_t> cut(0, msg.size());
          msg.resize(cut(rng));
        } else {
          msg += randomBytes(40);
        }
        break;
      }
      default: { // colon soup and embedded NULs
        msg = randomBytes(30);
        std::uniform_int_distribution<size_t> n(1, 6);
        size_t k = n(rng);
        for (size_t i = 0; i < k && !msg.empty(); i++)
          msg[rng() % msg.size()] = (rng() & 1) ? ':' : '\0';
        break;
      }
    }

    SysState before = state;
    onMqttMessage((char*)"cmd", (uint8_t*)msg.data(), (unsigned)msg.size());
    // Let the safety loop consume whatever was queued.
    for (int i = 0; i < 4; i++) { loop(); g_now += 1; }

    if (state != before) {
      // Any state change at all is a finding: the fuzzer never holds the real key, and in
      // this configuration unsigned commands are refused.
      fprintf(stderr, "FINDING at iter %llu: state %s -> %s for input (%zu bytes): ",
              it, stateName(before), stateName(state), msg.size());
      for (unsigned char c : msg) fprintf(stderr, "%02x", c);
      fprintf(stderr, "\n");
      accepted++;
      if (accepted > 5) return 1;
    }
    if (cmdCounter != counterBefore) {
      fprintf(stderr, "FINDING at iter %llu: replay counter advanced to %u\n", it, cmdCounter);
      return 1;
    }
  }

  printf("{\"iterations\":%llu,\"well_formed_shapes\":%llu,\"accepted\":%llu,"
         "\"final_state\":\"%s\",\"counter_advanced\":%s}\n",
         iters, parsedShapes, accepted, stateName(state),
         cmdCounter != counterBefore ? "true" : "false");
  return accepted ? 1 : 0;
}
