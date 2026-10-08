#include "../../firmware/smart_home/smart_home.ino"

static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { fails++; printf("  FAIL line %d: %s  ", __LINE__, #c); printf(__VA_ARGS__); printf("\n"); } else printf("  ok: %s\n", #c); } while (0)

static std::vector<std::string> evs;
static bool autoDrain = true;
static void drain() { Event e; while (xQueueReceive(eventQ, &e, 0) == pdTRUE) evs.push_back(std::string(e.type) + ":" + e.src); }
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
  CHECK(joined() == "boot:system ", "got [%s]", joined().c_str());
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

static void s_remote(uint32_t st) {
  init(st);
  run(200); evs.clear();
  Cmd c = Cmd::ARM;    xQueueSend(cmdQ, &c, 0); run(50);
  CHECK(state == SysState::EXIT_DELAY && has("exit_delay:remote"), "remote arm");
  c = Cmd::DISARM;     xQueueSend(cmdQ, &c, 0); run(50);
  CHECK(has("cmd_rejected:remote") && state == SysState::EXIT_DELAY, "remote disarm refused");
  c = Cmd::ARM;        xQueueSend(cmdQ, &c, 0); run(50);
  CHECK(has("cmd_ignored:remote"), "duplicate arm ignored");
  statusPublishNow = false;
  c = Cmd::STATUS;     xQueueSend(cmdQ, &c, 0); run(50);
  CHECK(statusPublishNow, "status request leads to publish");
  onMqttMessage((char*)"t", (uint8_t*)"disarm", 6);
  CHECK(uxQueueMessagesWaiting(cmdQ) == 1, "lowercase command parsed");
  Cmd x; xQueueReceive(cmdQ, &x, 0);
  onMqttMessage((char*)"t", (uint8_t*)"rm -rf /", 8);
  onMqttMessage((char*)"t", (uint8_t*)"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", 36);
  CHECK(uxQueueMessagesWaiting(cmdQ) == 0, "unknown / oversized payloads ignored");
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
    {"remote", s_remote}, {"display_fail", s_display_fail}, {"oled", s_oled}, {"network", s_network}};
  for (auto& a : all) if (!strcmp(a.n, name)) { a.f(start); printf(fails ? "RESULT FAIL (%d)\n" : "RESULT PASS\n", fails); return fails ? 1 : 0; }
  printf("unknown scenario\n"); return 2;
}
