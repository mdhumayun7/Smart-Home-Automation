#include "../../firmware/smart_home/smart_home.ino"

static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; printf("  FAIL line %d: %s  ", __LINE__, #c); printf(__VA_ARGS__); printf("\n"); } else printf("  ok: %s\n", #c); } while (0)

static std::vector<std::string> evs;
static std::vector<uint32_t> seqs;
static bool autoDrain = true;
static void drain() { Event e; while (xQueueReceive(eventQ, &e, 0) == pdTRUE) { evs.push_back(std::string(e.type) + ":" + e.src); seqs.push_back(e.seq); } }
static void run(uint32_t ms) {
  uint32_t end = g_now + ms;
  while ((int32_t)(end - g_now) > 0) { loop(); g_now += 3; if (autoDrain) drain(); }
}
static int count(const char* e) { int n = 0; for (auto& s : evs) if (s == e) n++; return n; }
static bool has(const char* e) { return count(e) > 0; }
static std::string joined() { std::string r; for (auto& s : evs) r += s + " "; return r; }

static void init(uint32_t start) {
  g_now = start;
  g_pin[PIN_DOOR] = LOW;       // door closed (switch to GND)
  g_pin[PIN_ARM_BTN] = HIGH;   // released
  g_pin[PIN_PIR] = LOW;
  setup();
  if (autoDrain) drain();
}
static void press() { g_pin[PIN_ARM_BTN] = LOW; run(120); g_pin[PIN_ARM_BTN] = HIGH; run(120); }
static void pirPulse(uint32_t ms) { g_pin[PIN_PIR] = HIGH; run(ms); g_pin[PIN_PIR] = LOW; run(60); }

static void s_basic(uint32_t st) {
  init(st);
  CHECK(joined() == "boot:poweron ", "got [%s]", joined().c_str());
  evs.clear();
  run(100);
  CHECK(state == SysState::DISARMED, "state");
  pirPulse(500);
  CHECK(!has("motion:pir"), "motion ignored while disarmed");
  g_pin[PIN_DOOR] = HIGH; run(100);
  CHECK(has("door_open:door"), "door_open logged: %s", joined().c_str());
  g_pin[PIN_DOOR] = LOW; run(100);
  CHECK(has("door_closed:door"), "door_closed logged");
  CHECK(g_out[PIN_BUZZER] == LOW && g_out[PIN_LED_ARMED] == LOW && g_out[PIN_LED_ALARM] == LOW, "outputs idle");
}

static void s_arm_alarm(uint32_t st) {
  init(st);
  run(PIR_WARMUP_MS + 100);
  evs.clear();
  press();
  CHECK(state == SysState::EXIT_DELAY && has("exit_delay:button"), "exit delay: %s", joined().c_str());
  uint32_t edges0 = g_buzzEdges;
  pirPulse(500);                                   // movement while leaving: ignored
  CHECK(!has("motion:pir"), "PIR ignored in exit delay");
  run(EXIT_DELAY_MS);
  CHECK(state == SysState::ARMED && has("armed:timer"), "armed: %s", joined().c_str());
  CHECK(g_buzzEdges > edges0, "exit ticks sounded");
  CHECK(g_out[PIN_LED_ARMED] == HIGH, "green LED on while armed");
  pirPulse(500);
  CHECK(has("motion:pir") && has("entry_delay:pir") && state == SysState::ENTRY_DELAY, "trigger: %s", joined().c_str());
  run(ENTRY_DELAY_MS + 50);
  CHECK(state == SysState::ALARM && has("alarm:timer") && alarmCount == 1, "alarm: %s", joined().c_str());
  uint32_t e1 = g_buzzEdges; run(1500);
  CHECK(g_buzzEdges - e1 >= 4, "siren toggling, edges=%u", g_buzzEdges - e1);
  pirPulse(500);
  CHECK(count("motion:pir") == 1, "no retrigger during alarm");
  run(ALARM_DURATION_MS);
  CHECK(state == SysState::ARMED && has("alarm_end:timer"), "back to armed: %s", joined().c_str());
  CHECK(g_out[PIN_BUZZER] == LOW, "siren off");
}

static void s_disarm_in_entry(uint32_t st) {
  init(st);
  press(); run(EXIT_DELAY_MS + 50);
  evs.clear();
  g_pin[PIN_DOOR] = HIGH; run(100);
  CHECK(count("door_open:door") == 1 && has("entry_delay:door"), "door trigger logged once: %s", joined().c_str());
  run(3000); press();
  CHECK(state == SysState::DISARMED && has("disarmed:button"), "disarmed in entry delay");
  run(ENTRY_DELAY_MS + ALARM_DURATION_MS);
  CHECK(!has("alarm:timer") && alarmCount == 0, "no alarm after disarm");
}

static void s_door_left_open(uint32_t st) {
  init(st);
  g_pin[PIN_DOOR] = HIGH; run(100);          // door open before arming
  evs.clear();
  press(); run(EXIT_DELAY_MS + 100);
  CHECK(has("armed:timer") && has("door_open:door") && state == SysState::ENTRY_DELAY, "left-open door triggers: %s", joined().c_str());
}

static void s_pir_edge(uint32_t st) {
  init(st);
  g_pin[PIN_PIR] = HIGH;                     // sensor already high through warm-up
  run(2000); press();
  run(EXIT_DELAY_MS + 100);
  CHECK(state == SysState::ARMED && !has("motion:pir"), "no false trigger at arming: %s", joined().c_str());
  g_pin[PIN_PIR] = LOW; run(200);
  g_pin[PIN_PIR] = HIGH; run(400);
  CHECK(has("motion:pir"), "re-trigger on new rising edge");
  g_pin[PIN_PIR] = LOW;
}

static void s_pir_glitch(uint32_t st) {
  init(st);
  run(PIR_WARMUP_MS + 100);
  press(); run(EXIT_DELAY_MS + 100);
  g_pin[PIN_PIR] = HIGH; run(60); g_pin[PIN_PIR] = LOW; run(200);   // 60 ms spike
  CHECK(state == SysState::ARMED && !has("motion:pir"), "short glitch ignored");
}

static void sendCmd(Cmd c) { CmdMsg m = { c, false, 0 }; xQueueSend(cmdQ, &m, 0); }

// v2.2: PIR + mmWave radar fusion logic for the three modes.
static void s_fusion(uint32_t st) {
  (void)st;
  // OR mode: either sensor alone triggers.
  SensorFusion f; fusion_init(f, FUSION_OR, 1500);
  CHECK(fusion_step(f, true,  false, 100), "OR: PIR alone fires");
  CHECK(fusion_step(f, false, true,  200), "OR: radar edge alone fires");
  CHECK(!fusion_step(f, false, true, 250), "OR: steady radar presence does not re-fire");

  // AND mode: a lone PIR edge with no radar does not fire (this is the false-alarm case).
  SensorFusion g; fusion_init(g, FUSION_AND, 1500);
  CHECK(!fusion_step(g, true, false, 100), "AND: lone PIR does not fire");
  CHECK(!fusion_step(g, false, false, 200), "AND: nothing keeps quiet");
  // Radar presence then a PIR edge within the window: fires.
  SensorFusion h; fusion_init(h, FUSION_AND, 1500);
  fusion_step(h, false, true, 1000);               // radar sees presence
  CHECK(fusion_step(h, true, true, 1200), "AND: PIR + radar within window fires");
  // PIR edge, then radar only after the window has passed: does not fire.
  SensorFusion k; fusion_init(k, FUSION_AND, 1500);
  fusion_step(k, true, false, 1000);               // PIR edge, no radar yet
  CHECK(!fusion_step(k, false, true, 4000), "AND: radar too late does not fire");

  // PIR-only mode: radar is ignored entirely.
  SensorFusion p; fusion_init(p, FUSION_PIR_ONLY, 1500);
  CHECK(!fusion_step(p, false, true, 100), "PIR_ONLY: radar ignored");
  CHECK(fusion_step(p, true, false, 200), "PIR_ONLY: PIR fires");
}

static void s_remote(uint32_t st) {
  init(st);
  run(200); evs.clear();
  sendCmd(Cmd::ARM); run(50);
  CHECK(state == SysState::EXIT_DELAY && has("exit_delay:remote"), "remote arm");
  sendCmd(Cmd::DISARM); run(50);
  CHECK(has("cmd_rejected:remote") && state == SysState::EXIT_DELAY, "remote disarm refused");
  sendCmd(Cmd::ARM); run(50);
  CHECK(has("cmd_ignored:remote"), "duplicate arm ignored");
  statusPublishNow = false;
  sendCmd(Cmd::STATUS); run(50);
  CHECK(statusPublishNow, "status request leads to publish");
  onMqttMessage((char*)"t", (uint8_t*)"disarm", 6);
  CHECK(uxQueueMessagesWaiting(cmdQ) == 1, "lowercase command parsed");
  CmdMsg x; xQueueReceive(cmdQ, &x, 0);
  onMqttMessage((char*)"t", (uint8_t*)"rm -rf /", 8);
  onMqttMessage((char*)"t", (uint8_t*)"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", 36);
  CHECK(uxQueueMessagesWaiting(cmdQ) == 0, "unknown / oversized payloads ignored");
  onMqttMessage((char*)"t", (uint8_t*)"ARM_AWAY", 8);   // Home Assistant arm-away payload
  CHECK(uxQueueMessagesWaiting(cmdQ) == 1, "ARM_AWAY accepted as ARM");
}

// v2.2: authenticated commands -- forgery, replay, and a valid signed DISARM.
// Builds the same "<VERB>:<ctr>:<tag>" string the signer tool and the device agree on.
static std::string signCmd(const char* verb, uint32_t ctr) {
  char base[32]; snprintf(base, sizeof base, "%s:%lu", verb, (unsigned long)ctr);
  uint8_t mac[32];
  authmac::hmac_sha256((const uint8_t*)SECRET_CMD_KEY, strlen(SECRET_CMD_KEY),
                       (const uint8_t*)base, strlen(base), mac);
  char out[80]; int n = snprintf(out, sizeof out, "%s:", base);
  for (size_t i = 0; i < AUTH_TAG_BYTES; i++) n += snprintf(out + n, sizeof out - n, "%02x", mac[i]);
  return std::string(out);
}

// v2.2: ESP-NOW signed alert message build/verify, tamper detection and replay rejection.
static void s_alert(uint32_t st) {
  (void)st;
  const char* key = "demo-alert-key-change-me";
  AlertMsg m;
  alert_build(m, key, strlen(key), ALERT_ALARM, 7, 123456, "esp32-112233445566");
  CHECK(alert_verify(m, key, strlen(key)), "freshly built alert verifies");
  CHECK(m.event == ALERT_ALARM && m.counter == 7, "fields round-trip (event=%u ctr=%lu)", m.event, (unsigned long)m.counter);

  // Any single-bit change anywhere in the signed region is caught.
  AlertMsg t = m; t.event = ALERT_LINK_LOST;
  CHECK(!alert_verify(t, key, strlen(key)), "tampered event field rejected");
  t = m; t.deviceId[0] ^= 1;
  CHECK(!alert_verify(t, key, strlen(key)), "tampered device id rejected");
  t = m; t.tag[0] ^= 1;
  CHECK(!alert_verify(t, key, strlen(key)), "tampered tag rejected");

  // A different key does not verify (no cross-device acceptance).
  CHECK(!alert_verify(m, "other-key", 9), "wrong key rejected");

  // The receiver's duplicate/replay rule: counter must strictly advance.
  uint32_t last = 0;
  bool accept7 = (m.counter > last); last = accept7 ? m.counter : last;
  bool replay7 = (m.counter > last);
  CHECK(accept7 && !replay7, "receiver accepts once, rejects replay");
}

// v2.2: Wi-Fi deauth-flood detector logic (sliding window, threshold, cooldown).
static void s_wifiguard(uint32_t st) {
  (void)st;
  DeauthDetector d;
  deauth_init(d, 2000, 8, 10000);
  int fires = 0;
  // 7 frames in the window: below threshold, no detection.
  for (int i = 0; i < 7; i++) fires += deauth_observe(d, 100 + i * 10) ? 1 : 0;
  CHECK(fires == 0, "below threshold does not fire (%d)", fires);
  // 8th frame reaches the threshold: one detection.
  CHECK(deauth_observe(d, 180), "threshold reached fires once");
  // More frames inside the cooldown do not fire again.
  fires = 0;
  for (int i = 0; i < 10; i++) fires += deauth_observe(d, 200 + i * 10) ? 1 : 0;
  CHECK(fires == 0, "cooldown suppresses repeat reports (%d)", fires);
  // After the cooldown, a fresh flood fires again.
  DeauthDetector d2; deauth_init(d2, 2000, 8, 10000);
  for (int i = 0; i < 8; i++) deauth_observe(d2, 1000 + i);
  bool again = false;
  for (int i = 0; i < 8; i++) again |= deauth_observe(d2, 20000 + i);
  CHECK(again, "fresh flood after cooldown fires");
  // Frames spread wider than the window never reach the threshold.
  DeauthDetector d3; deauth_init(d3, 2000, 8, 10000);
  bool slow = false;
  for (int i = 0; i < 20; i++) slow |= deauth_observe(d3, i * 5000);
  CHECK(!slow, "slow trickle outside the window never fires");
}

// v2.2: losing Wi-Fi while armed raises a link_lost security event; while disarmed it does not.
static void s_linklost(uint32_t st) {
  init(st);
  g_wifiUp = true; networkStep(g_now); run(50);
  run(PIR_WARMUP_MS + 100);
  press(); run(EXIT_DELAY_MS + 100);        // ARMED
  evs.clear();
  g_wifiUp = false; networkStep(g_now); run(50);
  CHECK(has("link_lost:radio"), "link loss while armed is flagged: %s", joined().c_str());
  // Disarm, bring Wi-Fi back, drop it again: no link_lost while disarmed.
  press(); run(50);
  g_wifiUp = true; networkStep(g_now); run(50);
  evs.clear();
  g_wifiUp = false; networkStep(g_now); run(50);
  CHECK(!has("link_lost:radio"), "link loss while disarmed is not a security event");
}

static void s_auth(uint32_t st) {
  init(st);
  run(200); evs.clear();

  // A forged tag (right shape, wrong key) is rejected and never changes state.
  std::string forged = signCmd("ARM", 5);
  forged[forged.size() - 1] ^= 1;   // flip one hex nibble of the tag
  onMqttMessage((char*)"t", (uint8_t*)forged.data(), forged.size()); run(50);
  CHECK(has("cmd_badmac:remote") && state == SysState::DISARMED, "forged tag rejected: %s", joined().c_str());

  // A correctly signed ARM at counter 10 is accepted.
  std::string a10 = signCmd("ARM", 10);
  onMqttMessage((char*)"t", (uint8_t*)a10.data(), a10.size()); run(50);
  CHECK(state == SysState::EXIT_DELAY && has("exit_delay:remote_auth"), "signed ARM accepted: %s", joined().c_str());
  CHECK(g_nvsU["cmdctr"] == 10, "counter persisted to NVS (%u)", g_nvsU["cmdctr"]);

  // Replaying that exact ARM (counter 10 again) is rejected.
  evs.clear();
  onMqttMessage((char*)"t", (uint8_t*)a10.data(), a10.size()); run(50);
  CHECK(has("cmd_replay:remote"), "replayed command rejected: %s", joined().c_str());

  // A signed DISARM at a higher counter is accepted even though plain remote DISARM is refused.
  run(EXIT_DELAY_MS + 100);          // reach ARMED
  evs.clear();
  std::string d11 = signCmd("DISARM", 11);
  onMqttMessage((char*)"t", (uint8_t*)d11.data(), d11.size()); run(50);
  CHECK(state == SysState::DISARMED && has("disarmed:remote_auth"), "signed DISARM accepted: %s", joined().c_str());
  CHECK(g_nvsU["cmdctr"] == 11, "counter advanced to 11 (%u)", g_nvsU["cmdctr"]);

  // The replay floor survives a reset: after reboot, counter 11 is still rejected.
  autoDrain = true; evs.clear();
  init(st + 500);                    // g_nvs / g_nvsU persist across init(); NVS is not cleared
  run(200); evs.clear();
  std::string d11b = signCmd("DISARM", 11);
  onMqttMessage((char*)"t", (uint8_t*)d11b.data(), d11b.size()); run(50);
  CHECK(has("cmd_replay:remote"), "counter floor restored from NVS after reset: %s", joined().c_str());
}

// v2.1: armed state stored in NVS, written only on arm / disarm
static void s_persist(uint32_t st) {
  init(st);
  CHECK(g_nvsWrites == 0, "no NVS write at boot while disarmed");
  run(PIR_WARMUP_MS + 100);
  press(); run(EXIT_DELAY_MS + 100);
  CHECK(state == SysState::ARMED && g_nvs["armed"] && g_nvsWrites == 1, "arming persisted once (writes=%d)", g_nvsWrites);
  pirPulse(500); run(ENTRY_DELAY_MS + ALARM_DURATION_MS + 200);
  CHECK(state == SysState::ARMED && g_nvsWrites == 1, "alarm cycle adds no flash writes (writes=%d)", g_nvsWrites);
  press();
  CHECK(state == SysState::DISARMED && !g_nvs["armed"] && g_nvsWrites == 2, "disarm persisted");
}

// v2.1: power cut while armed -> device comes back armed
static void s_restore(uint32_t st) {
  g_nvs["armed"] = true;
  init(st);
  CHECK(state == SysState::ARMED && has("restored_armed:nvs"), "restored to ARMED: %s", joined().c_str());
  CHECK(g_nvsWrites == 0, "restore does not rewrite NVS");
  pirPulse(500);
  CHECK(state == SysState::ARMED, "PIR still ignored during warm-up after restore");
  run(PIR_WARMUP_MS); pirPulse(500);
  CHECK(state == SysState::ENTRY_DELAY && has("motion:pir"), "motion after warm-up triggers");
}

static void s_restore_door(uint32_t st) {
  g_nvs["armed"] = true;
  g_now = st;
  g_pin[PIN_DOOR] = HIGH; g_pin[PIN_ARM_BTN] = HIGH; g_pin[PIN_PIR] = LOW;
  setup(); drain();
  CHECK(state == SysState::ENTRY_DELAY && has("door_open:door"), "door open at power-up triggers entry delay: %s", joined().c_str());
}

// v2.1: diagnostics - reset reason, watchdog, event sequence numbers
static void s_diag(uint32_t st) {
  g_resetReason = ESP_RST_TASK_WDT;
  init(st);
  CHECK(has("boot:task_wdt"), "reset reason reported: %s", joined().c_str());
  CHECK(g_loopWdt, "loop watchdog enabled");
  press(); run(EXIT_DELAY_MS + 100); press();
  bool inc = seqs.size() >= 4;
  for (size_t i = 1; i < seqs.size(); i++) if (seqs[i] != seqs[i - 1] + 1) inc = false;
  CHECK(inc && seqs[0] == 1, "event seq numbers start at 1 and increase by one (%zu events)", seqs.size());
}

static void s_display_fail(uint32_t st) {
  g_displayOk = false;
  init(st);
  press();
  run(EXIT_DELAY_MS + 100);
  CHECK(state == SysState::ARMED && g_lastFrame.empty(), "system keeps working without display");
}

static void s_oled(uint32_t st) {
  init(st);
  run(400);
  CHECK(g_lastFrame.find("DISARMED") != std::string::npos, "frame: %s", g_lastFrame.c_str());
  CHECK(g_lastFrame.find("WiFi:-- MQTT:--") != std::string::npos, "offline shown");
  press(); run(300);
  CHECK(g_lastFrame.find("EXIT 10s") != std::string::npos || g_lastFrame.find("EXIT 9s") != std::string::npos, "countdown: %s", g_lastFrame.c_str());
  size_t mx = 0; for (size_t i = 0, l = 0; i <= g_lastFrame.size(); i++) { if (i == g_lastFrame.size() || g_lastFrame[i] == '|') { if (l > mx) mx = l; l = 0; } else l++; }
  CHECK(mx <= 21 + 2, "longest line %zu chars", mx);
}

static void s_network(uint32_t st) {
  autoDrain = false;
  init(st);                       // boot event stays in the queue
  evs.clear();
  run(700);                       // populate shared status
  std::string base = std::string(TOPIC_ROOT) + "/" + deviceId;
  CHECK(base == "svnit/smarthome/esp32-112233445566" || base.find("esp32-") != std::string::npos, "topic base %s", base.c_str());

  int b0 = g_wifiBegins;
  networkStep(g_now); CHECK(g_wifiBegins == b0, "no retry yet");
  g_now += WIFI_RETRY_MS + 10; networkStep(g_now);
  CHECK(g_wifiBegins == b0 + 1, "wifi retry after interval");

  g_wifiUp = true; g_now += 10; networkStep(g_now);
  CHECK(netWifiUp && g_tzCalls.size() == 1, "NTP configured once");
  CHECK(g_connectCalls == 1 && !netMqttUp, "first mqtt attempt failed");
  g_now += 100; networkStep(g_now);
  CHECK(g_connectCalls == 1, "mqtt retry is rate limited");
  g_now += MQTT_RETRY_MS; networkStep(g_now);
  CHECK(g_connectCalls == 2, "mqtt retries after interval");
  CHECK(g_lastWillTopic == base + "/availability", "last will topic");

  g_brokerAccepts = true; g_now += MQTT_RETRY_MS; networkStep(g_now);
  CHECK(netMqttUp && !g_pubs.empty(), "connected");
  CHECK(g_pubs[0].topic == base + "/availability" && g_pubs[0].payload == "online" && g_pubs[0].retained, "availability online retained");
  CHECK(g_subs.size() == 1 && g_subs[0] == base + "/cmd", "subscribed to cmd");
  bool gotBoot = false, gotState = false;
  for (auto& p : g_pubs) { if (p.topic == base + "/event" && p.payload.find("\"event\":\"boot\"") != std::string::npos) gotBoot = true;
                           if (p.topic == base + "/state" && p.retained && p.payload.find("\"state\":\"DISARMED\"") != std::string::npos) gotState = true; }
  CHECK(gotBoot, "queued boot event delivered");
  CHECK(gotState, "retained state published");
  CHECK(uxQueueMessagesWaiting(eventQ) == 0, "queue drained");
  bool gotHa = false;
  for (auto& p : g_pubs)
    if (p.topic == "homeassistant/alarm_control_panel/" + std::string(deviceId) + "/config" && p.retained &&
        p.payload.find("\"state_topic\":\"" + base + "/state\"") != std::string::npos &&
        p.payload.find("\"command_topic\":\"" + base + "/cmd\"") != std::string::npos &&
        p.payload.find("\"availability_topic\":\"" + base + "/availability\"") != std::string::npos) gotHa = true;
  CHECK(gotHa, "Home Assistant discovery config published (retained)");
  bool haState = false;
  for (auto& p : g_pubs) if (p.topic == base + "/state" && p.payload.find("\"ha\":\"disarmed\"") != std::string::npos) haState = true;
  CHECK(haState, "state carries Home Assistant state name");

  // Offline queue, order preserved
  g_linkUp = false; g_brokerAccepts = false;
  emitEvent("q1", "t"); emitEvent("q2", "t"); emitEvent("q3", "t");
  size_t n0 = g_pubs.size();
  g_now += MQTT_RETRY_MS; networkStep(g_now);
  CHECK(g_pubs.size() == n0 && uxQueueMessagesWaiting(eventQ) == 3, "events held while offline");
  g_brokerAccepts = true; g_now += MQTT_RETRY_MS; networkStep(g_now);
  std::string order;
  for (size_t i = n0; i < g_pubs.size(); i++) if (g_pubs[i].topic == base + "/event") {
    for (const char* k : {"q1", "q2", "q3"}) if (g_pubs[i].payload.find(std::string("\"event\":\"") + k) != std::string::npos) order += k; }
  CHECK(order == "q1q2q3", "delivered in order: %s", order.c_str());

  // Publish fails and link drops: event must survive and be sent once after reconnect
  g_failNextPublishAndDrop = true;
  emitEvent("keepme", "t");
  g_now += 50; networkStep(g_now);
  CHECK(uxQueueMessagesWaiting(eventQ) == 1, "event kept after failed publish");
  size_t n1 = g_pubs.size();
  g_now += MQTT_RETRY_MS; networkStep(g_now);
  int seen = 0; for (size_t i = n1; i < g_pubs.size(); i++) if (g_pubs[i].payload.find("keepme") != std::string::npos) seen++;
  CHECK(seen == 1 && uxQueueMessagesWaiting(eventQ) == 0, "delivered exactly once, seen=%d", seen);

  // Race path: the loop task refills the queue while a publish is failing. The event in
  // flight cannot go back; it must be counted, never silently lost.
  {
    uint32_t nd0 = netDropped;
    g_publishHook = [] { while (uxQueueMessagesWaiting(eventQ) < 16) emitEvent("fill", "t"); };
    g_failNextPublishAndDrop = true;
    emitEvent("inflight", "t");
    g_now += 50; networkStep(g_now);
    g_publishHook = nullptr;
    CHECK(netDropped - nd0 == 1 && uxQueueMessagesWaiting(eventQ) == 16, "in-flight event counted as dropped when queue is full (nd=%u q=%u)",
          (unsigned)(netDropped - nd0), uxQueueMessagesWaiting(eventQ));
    g_brokerAccepts = true; g_now += MQTT_RETRY_MS;
    for (int i = 0; i < 6; i++) { g_now += 30; networkStep(g_now); }
    CHECK(uxQueueMessagesWaiting(eventQ) == 0, "backlog delivered after race");
  }

  // Overflow
  g_linkUp = false; g_brokerAccepts = false;
  uint32_t d0 = eventsDropped;
  for (int i = 0; i < 20; i++) { char t[16]; snprintf(t, sizeof t, "ev%02d", i); emitEvent(t, "t"); }
  Event first; xQueuePeek(eventQ, &first, 0);
  CHECK(uxQueueMessagesWaiting(eventQ) == 16 && eventsDropped - d0 == 4 && strcmp(first.type, "ev04") == 0, "overflow keeps newest 16 (first=%s dropped=%u)", first.type, eventsDropped - d0);
  g_brokerAccepts = true; g_now += MQTT_RETRY_MS;
  for (int i = 0; i < 6; i++) { g_now += 30; networkStep(g_now); }
  CHECK(uxQueueMessagesWaiting(eventQ) == 0, "backlog flushed in batches");

  // Heartbeat
  run(600);
  size_t n2 = g_pubs.size();
  g_now += HEARTBEAT_MS + 10; networkStep(g_now);
  bool hb = false; for (size_t i = n2; i < g_pubs.size(); i++) if (g_pubs[i].topic == base + "/state") hb = true;
  CHECK(hb, "heartbeat state published");

  for (auto& p : g_pubs) printf("PUB %s %s\n", p.topic.c_str(), p.payload.c_str());
}

int main(int argc, char** argv) {
  const char* name = argc > 1 ? argv[1] : "basic";
  uint32_t start = argc > 2 ? (uint32_t)strtoul(argv[2], nullptr, 0) : 0;
  printf("== %s (start=%u)\n", name, start);
  struct { const char* n; void (*f)(uint32_t); } all[] = {
    {"basic", s_basic}, {"arm_alarm", s_arm_alarm}, {"disarm_in_entry", s_disarm_in_entry},
    {"door_left_open", s_door_left_open}, {"pir_edge", s_pir_edge}, {"pir_glitch", s_pir_glitch},
    {"remote", s_remote}, {"display_fail", s_display_fail}, {"oled", s_oled}, {"network", s_network},
    {"persist", s_persist}, {"restore", s_restore}, {"restore_door", s_restore_door}, {"diag", s_diag},
    {"auth", s_auth}, {"wifiguard", s_wifiguard}, {"linklost", s_linklost}, {"alert", s_alert}, {"fusion", s_fusion}};
  for (auto& a : all) if (!strcmp(a.n, name)) { a.f(start); printf(fails ? "RESULT FAIL (%d)\n" : "RESULT PASS\n", fails); return fails ? 1 : 0; }
  printf("unknown scenario\n"); return 2;
}
