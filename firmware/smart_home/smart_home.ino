/*
 * Smart Home Surveillance System  -  firmware v2.0.0
 * Target : ESP32 DevKit (Wokwi simulation or real hardware)
 * Author : MD Humayun
 *
 * What changed compared with v1
 *   - No blocking delay() anywhere in the safety path (v1 froze for 5 s per alarm).
 *   - Detection no longer depends on Wi-Fi: the alarm works fully offline.
 *   - Real arm / disarm state machine with exit delay, entry delay and alarm timeout.
 *   - Door sensor and arm button added; PIR gets warm-up time and confirmation filter.
 *   - Networking runs in its own FreeRTOS task on core 0, so slow DNS / TCP / MQTT
 *     calls can never stall the buzzer, LEDs or sensor scanning on core 1.
 *   - Real MQTT notifications (v1 only printed "Sending notification" to Serial),
 *     with Last Will, heartbeat, retained state and remote ARM / STATUS commands.
 *   - Events raised while offline are queued (16 deep) and delivered on reconnect.
 *   - Display failure no longer halts the program.
 *
 * Libraries (Wokwi: libraries.txt):  Adafruit SSD1306, Adafruit GFX Library, PubSubClient
 */

#include <Wire.h>
#include <WiFi.h>
#include <time.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <PubSubClient.h>

#define FW_VERSION "2.0.0"

// ============================================================================
//  Configuration
// ============================================================================

// ---- Pins -------------------------------------------------------------------
constexpr uint8_t PIN_PIR       = 13;  // PIR OUT            (input)
constexpr uint8_t PIN_BUZZER    = 23;  // buzzer +           (output)
constexpr uint8_t PIN_DOOR      = 14;  // door switch to GND (input, pull-up) HIGH = open
constexpr uint8_t PIN_ARM_BTN   = 27;  // arm/disarm button to GND (input, pull-up)
constexpr uint8_t PIN_LED_ARMED = 26;  // green LED          (output)
constexpr uint8_t PIN_LED_ALARM = 25;  // red LED            (output)
constexpr uint8_t PIN_SDA       = 21;  // OLED SDA
constexpr uint8_t PIN_SCL       = 22;  // OLED SCL

// ---- Timing (ms) ------------------------------------------------------------
constexpr uint32_t EXIT_DELAY_MS      = 10000;  // time to leave after pressing ARM
constexpr uint32_t ENTRY_DELAY_MS     = 10000;  // time to disarm after a trigger
constexpr uint32_t ALARM_DURATION_MS  = 30000;  // siren length, then system re-arms
constexpr uint32_t PIR_WARMUP_MS      = 10000;  // use 30000-60000 on a real HC-SR501
constexpr uint32_t PIR_CONFIRM_MS     = 150;    // PIR must stay HIGH this long
constexpr uint32_t DEBOUNCE_MS        = 40;
constexpr uint32_t OLED_REFRESH_MS    = 250;
constexpr uint32_t STATUS_COPY_MS     = 500;    // loop -> network task snapshot rate
constexpr uint32_t HEARTBEAT_MS       = 30000;
constexpr uint32_t WIFI_RETRY_MS      = 15000;
constexpr uint32_t MQTT_RETRY_MS      = 5000;

// ---- Network ----------------------------------------------------------------
// Wokwi-GUEST is the open Wi-Fi provided by the simulator (channel 6 connects fastest).
// For real hardware move credentials out of the source (separate secrets.h, not committed).
const char*    WIFI_SSID    = "Wokwi-GUEST";
const char*    WIFI_PASS    = "";
constexpr int  WIFI_CHANNEL = 6;

// Public test broker: anyone can read or write your topics. Fine for a demo, not for a home.
// For deployment use a private broker with username/password and TLS (port 8883).
const char*    MQTT_HOST    = "broker.hivemq.com";
constexpr uint16_t MQTT_PORT = 1883;
const char*    MQTT_USER    = nullptr;
const char*    MQTT_PASS    = nullptr;
#define TOPIC_ROOT "svnit/smarthome"

// 0 = passive piezo buzzer driven with a 2.7 kHz tone (also what Wokwi needs to make sound).
// 1 = active buzzer with built-in oscillator, driven with a plain HIGH/LOW level.
#define BUZZER_ACTIVE 0
constexpr uint32_t BUZZER_FREQ_HZ = 2700;

// 0 = remote DISARM is refused (recommended on an unauthenticated broker).
#define ALLOW_REMOTE_DISARM 0

#define TZ_STRING "IST-5:30"

// ============================================================================
//  Types
// ============================================================================

enum class SysState : uint8_t { DISARMED, EXIT_DELAY, ARMED, ENTRY_DELAY, ALARM };
enum class Cmd      : uint8_t { ARM, DISARM, STATUS };

struct Event {
  uint32_t epoch;     // UTC seconds, 0 if clock not yet synced
  uint32_t upMs;      // millis() at the moment of the event
  char     type[16];
  char     src[12];
};

struct Status {
  SysState state;
  bool     doorOpen;
  bool     pirActive;
  bool     pirWarm;
  uint32_t events;
  uint32_t dropped;
  uint32_t alarms;
  uint32_t upMs;
};

struct Debounced {
  uint8_t  pin;
  bool     stable;     // last accepted level (true = HIGH)
  bool     lastRaw;
  uint32_t changedAt;
};

static const char* stateName(SysState s) {
  switch (s) {
    case SysState::DISARMED:    return "DISARMED";
    case SysState::EXIT_DELAY:  return "EXIT_DELAY";
    case SysState::ARMED:       return "ARMED";
    case SysState::ENTRY_DELAY: return "ENTRY_DELAY";
    case SysState::ALARM:       return "ALARM";
  }
  return "?";
}

// ============================================================================
//  Globals
// ============================================================================

// ---- Safety core (loop task, core 1) ---------------------------------------
static Adafruit_SSD1306 display(128, 64, &Wire, -1);
static bool      displayOk   = false;

static SysState  state       = SysState::DISARMED;
static uint32_t  stateSince  = 0;
static uint32_t  bootMs      = 0;
static uint32_t  beepUntil   = 0;
static bool      beeping     = false;

static Debounced door        = {PIN_DOOR,    true, true, 0};   // HIGH = open
static Debounced armBtn      = {PIN_ARM_BTN, true, true, 0};   // LOW  = pressed
static bool      pirHigh     = false;
static uint32_t  pirHighSince = 0;
static bool      pirConfirmed = false;

static uint32_t  eventCount  = 0;
static uint32_t  alarmCount  = 0;
static volatile uint32_t eventsDropped = 0;
static char      lastEvent[16] = "none";

static uint32_t  lastOled    = 0;
static uint32_t  lastCopy    = 0;
static bool      statusDirty = false;   // set on state change; copied, then published

// ---- Shared between the two cores ------------------------------------------
static QueueHandle_t     eventQ      = nullptr;   // loop  -> network
static QueueHandle_t     cmdQ        = nullptr;   // network -> loop
static SemaphoreHandle_t statusMutex = nullptr;
static Status            sharedStatus = {};
static volatile bool     statusPublishNow = false;
static volatile bool     netWifiUp   = false;
static volatile bool     netMqttUp   = false;
static volatile int8_t   netRssi     = 0;

// ---- Network core (network task, core 0) -----------------------------------
static WiFiClient   wifiClient;
static PubSubClient mqtt(wifiClient);
static char deviceId[24];
static char topicAvail[64], topicState[64], topicEvent[64], topicCmd[64];
static uint32_t lastWifiTry = 0, lastMqttTry = 0, lastHeartbeat = 0;

// ============================================================================
//  Small helpers
// ============================================================================

// Buzzer driver: works with both arduino-esp32 2.x (channel based LEDC) and 3.x (pin based).
static bool buzzerOn = false;

static void buzzerInit() {
#if BUZZER_ACTIVE
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
#elif defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_BUZZER, BUZZER_FREQ_HZ, 8);
  ledcWriteTone(PIN_BUZZER, 0);
#else
  ledcSetup(0, BUZZER_FREQ_HZ, 8);
  ledcAttachPin(PIN_BUZZER, 0);
  ledcWriteTone(0, 0);
#endif
  buzzerOn = false;
}

static void buzzerSet(bool on) {
  if (on == buzzerOn) return;          // only touch the hardware when the state changes
  buzzerOn = on;
#if BUZZER_ACTIVE
  digitalWrite(PIN_BUZZER, on ? HIGH : LOW);
#elif defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWriteTone(PIN_BUZZER, on ? BUZZER_FREQ_HZ : 0);
#else
  ledcWriteTone(0, on ? BUZZER_FREQ_HZ : 0);
#endif
}

static bool timeSynced() { return time(nullptr) > 1700000000L; }

static uint32_t epochNow() { return timeSynced() ? (uint32_t)time(nullptr) : 0; }

static void copyStr(char* dst, size_t n, const char* src) { snprintf(dst, n, "%s", src); }

// Returns true once when the stable level changes.
static bool debounceUpdate(Debounced& d, uint32_t now) {
  bool raw = digitalRead(d.pin) == HIGH;
  if (raw != d.lastRaw) { d.lastRaw = raw; d.changedAt = now; }
  if (raw != d.stable && (now - d.changedAt) >= DEBOUNCE_MS) {
    d.stable = raw;
    return true;
  }
  return false;
}

static void emitEvent(const char* type, const char* src) {
  Event e = {};
  e.epoch = epochNow();
  e.upMs  = millis();
  copyStr(e.type, sizeof e.type, type);
  copyStr(e.src,  sizeof e.src,  src);
  eventCount++;
  copyStr(lastEvent, sizeof lastEvent, type);
  if (xQueueSend(eventQ, &e, 0) != pdTRUE) {      // queue full: drop the oldest
    Event old;
    xQueueReceive(eventQ, &old, 0);
    xQueueSend(eventQ, &e, 0);
    eventsDropped++;
  }
  Serial.printf("[%8lu] EVENT %-12s src=%s\n", (unsigned long)e.upMs, type, src);
}

static void setState(SysState next, const char* evType, const char* src, uint32_t now) {
  state      = next;
  stateSince = now;
  statusDirty = true;
  emitEvent(evType, src);
}

static bool pirWarm(uint32_t now) { return (now - bootMs) >= PIR_WARMUP_MS; }

static void startBeep(uint32_t now, uint32_t ms) { beeping = true; beepUntil = now + ms; }

// ============================================================================
//  Safety logic
// ============================================================================

static void beginArm(const char* src, uint32_t now) {
  setState(SysState::EXIT_DELAY, "exit_delay", src, now);
}

static void disarm(const char* src, uint32_t now) {
  setState(SysState::DISARMED, "disarmed", src, now);
  startBeep(now, 150);
}

static void trigger(const char* cause, const char* src, uint32_t now) {
  emitEvent(cause, src);
  if (ENTRY_DELAY_MS == 0) {
    alarmCount++;
    setState(SysState::ALARM, "alarm", "timer", now);
  } else {
    setState(SysState::ENTRY_DELAY, "entry_delay", src, now);
  }
}

static void readInputs(uint32_t now, bool& pirEdge, bool& doorOpened, bool& buttonPressed) {
  pirEdge = doorOpened = buttonPressed = false;

  // PIR: must stay HIGH for PIR_CONFIRM_MS and be past warm-up.
  bool raw = digitalRead(PIN_PIR) == HIGH;
  if (raw) {
    if (!pirHigh) { pirHigh = true; pirHighSince = now; }
  } else {
    pirHigh = false;
  }
  bool confirmed = pirHigh && (now - pirHighSince) >= PIR_CONFIRM_MS && pirWarm(now);
  pirEdge = confirmed && !pirConfirmed;
  pirConfirmed = confirmed;

  // Door: HIGH = open (pull-up, switch closes to GND).
  if (debounceUpdate(door, now)) {
    if (door.stable && state == SysState::ARMED) {
      doorOpened = true;           // trigger() will log the event, so do not log it twice
    } else {
      emitEvent(door.stable ? "door_open" : "door_closed", "door");
    }
  }

  // Button: LOW = pressed, act on the press edge.
  if (debounceUpdate(armBtn, now) && !armBtn.stable) buttonPressed = true;
}

static void handleCommands(uint32_t now) {
  Cmd c;
  while (xQueueReceive(cmdQ, &c, 0) == pdTRUE) {
    switch (c) {
      case Cmd::ARM:
        if (state == SysState::DISARMED) beginArm("remote", now);
        else emitEvent("cmd_ignored", "remote");
        break;
      case Cmd::DISARM:
#if ALLOW_REMOTE_DISARM
        if (state != SysState::DISARMED) disarm("remote", now);
#else
        emitEvent("cmd_rejected", "remote");
#endif
        break;
      case Cmd::STATUS:
        statusDirty = true;
        break;
    }
  }
}

static void runStateMachine(uint32_t now, bool pirEdge, bool doorOpened, bool buttonPressed) {
  if (buttonPressed) {
    if (state == SysState::DISARMED) beginArm("button", now);
    else                             disarm("button", now);
    return;
  }

  uint32_t elapsed = now - stateSince;
  switch (state) {
    case SysState::DISARMED:
      break;

    case SysState::EXIT_DELAY:
      if (elapsed >= EXIT_DELAY_MS) {
        setState(SysState::ARMED, "armed", "timer", now);
        startBeep(now, 300);
        if (door.stable) trigger("door_open", "door", now);   // left open after exit
      }
      break;

    case SysState::ARMED:
      if (pirEdge)         trigger("motion",    "pir",  now);
      else if (doorOpened) trigger("door_open", "door", now);
      break;

    case SysState::ENTRY_DELAY:
      if (elapsed >= ENTRY_DELAY_MS) {
        alarmCount++;
        setState(SysState::ALARM, "alarm", "timer", now);
      }
      break;

    case SysState::ALARM:
      if (elapsed >= ALARM_DURATION_MS) setState(SysState::ARMED, "alarm_end", "timer", now);
      break;
  }
}

// ============================================================================
//  Outputs
// ============================================================================

static void driveOutputs(uint32_t now) {
  uint32_t t = now - stateSince;
  if (beeping && (int32_t)(now - beepUntil) >= 0) beeping = false;   // wrap-safe
  bool buzz = beeping;
  bool green = false, red = false;

  switch (state) {
    case SysState::DISARMED:
      break;
    case SysState::EXIT_DELAY:
      buzz  = buzz || (t % 1000) < 60;      // slow tick
      green = ((now / 500) % 2) == 0;
      break;
    case SysState::ARMED:
      green = true;
      break;
    case SysState::ENTRY_DELAY:
      buzz = buzz || (t % 400) < 150;       // fast beeps
      red  = ((now / 500) % 2) == 0;
      break;
    case SysState::ALARM:
      buzz = buzz || (t % 600) < 400;       // siren
      red  = ((now / 100) % 2) == 0;
      break;
  }
  buzzerSet(buzz);
  digitalWrite(PIN_LED_ARMED, green ? HIGH : LOW);
  digitalWrite(PIN_LED_ALARM, red   ? HIGH : LOW);
}

static void updateDisplay(uint32_t now) {
  if (!displayOk || (now - lastOled) < OLED_REFRESH_MS) return;
  lastOled = now;

  char line[40];
  uint32_t left = 0;
  if (state == SysState::EXIT_DELAY)  left = (EXIT_DELAY_MS  - (now - stateSince) + 999) / 1000;
  if (state == SysState::ENTRY_DELAY) left = (ENTRY_DELAY_MS - (now - stateSince) + 999) / 1000;

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  display.setTextSize(2);
  display.setCursor(0, 0);
  switch (state) {
    case SysState::DISARMED:    snprintf(line, sizeof line, "DISARMED");        break;
    case SysState::EXIT_DELAY:  snprintf(line, sizeof line, "EXIT %lus", (unsigned long)left);  break;
    case SysState::ARMED:       snprintf(line, sizeof line, "ARMED");           break;
    case SysState::ENTRY_DELAY: snprintf(line, sizeof line, "ENTRY %lus", (unsigned long)left); break;
    case SysState::ALARM:       snprintf(line, sizeof line, "ALARM!");          break;
  }
  display.print(line);

  display.setTextSize(1);
  snprintf(line, sizeof line, "WiFi:%s MQTT:%s", netWifiUp ? "OK" : "--", netMqttUp ? "OK" : "--");
  display.setCursor(0, 18); display.print(line);

  const char* pirTxt = !pirWarm(now) ? "WARM" : (pirConfirmed ? "MOVE" : "IDLE");
  snprintf(line, sizeof line, "Door:%s PIR:%s", door.stable ? "OPEN" : "CLOSED", pirTxt);
  display.setCursor(0, 27); display.print(line);

  snprintf(line, sizeof line, "Last:%s", lastEvent);
  display.setCursor(0, 36); display.print(line);

  snprintf(line, sizeof line, "Evt:%lu Alm:%lu Q:%u", (unsigned long)eventCount,
           (unsigned long)alarmCount, (unsigned)uxQueueMessagesWaiting(eventQ));
  display.setCursor(0, 45); display.print(line);

  if (timeSynced()) {
    time_t tt = time(nullptr);
    struct tm tmv;
    localtime_r(&tt, &tmv);
    snprintf(line, sizeof line, "%02d:%02d:%02d IST", tmv.tm_hour, tmv.tm_min, tmv.tm_sec);
  } else {
    uint32_t s = now / 1000;
    snprintf(line, sizeof line, "up %02lu:%02lu:%02lu", (unsigned long)(s / 3600),
             (unsigned long)((s / 60) % 60), (unsigned long)(s % 60));
  }
  display.setCursor(0, 54); display.print(line);
  display.display();
}

static void copyStatusForNetwork(uint32_t now) {
  if ((now - lastCopy) < STATUS_COPY_MS && !statusDirty) return;
  if (xSemaphoreTake(statusMutex, 0) != pdTRUE) return;   // never wait in the safety loop
  lastCopy = now;
  sharedStatus.state     = state;
  sharedStatus.doorOpen  = door.stable;
  sharedStatus.pirActive = pirConfirmed;
  sharedStatus.pirWarm   = pirWarm(now);
  sharedStatus.events    = eventCount;
  sharedStatus.dropped   = eventsDropped;
  sharedStatus.alarms    = alarmCount;
  sharedStatus.upMs      = now;
  xSemaphoreGive(statusMutex);
  if (statusDirty) {            // publish only after the snapshot is in place
    statusDirty = false;
    statusPublishNow = true;
  }
}

// ============================================================================
//  Network task (core 0)
// ============================================================================

static void onMqttMessage(char* topic, uint8_t* payload, unsigned int len) {
  (void)topic;
  char buf[16];
  if (len >= sizeof buf) len = sizeof buf - 1;
  memcpy(buf, payload, len);
  buf[len] = 0;
  for (unsigned i = 0; i < len; i++) if (buf[i] >= 'a' && buf[i] <= 'z') buf[i] -= 32;

  Cmd c;
  if      (strcmp(buf, "ARM")    == 0) c = Cmd::ARM;
  else if (strcmp(buf, "DISARM") == 0) c = Cmd::DISARM;
  else if (strcmp(buf, "STATUS") == 0) c = Cmd::STATUS;
  else { Serial.printf("MQTT: unknown command '%s'\n", buf); return; }
  xQueueSend(cmdQ, &c, 0);
}

static bool connectMqtt() {
  bool ok = mqtt.connect(deviceId, MQTT_USER, MQTT_PASS, topicAvail, 1, true, "offline");
  if (!ok) { Serial.printf("MQTT connect failed, rc=%d\n", mqtt.state()); return false; }
  mqtt.publish(topicAvail, "online", true);
  mqtt.subscribe(topicCmd);
  statusPublishNow = true;
  Serial.println("MQTT connected");
  return true;
}

static bool publishEvent(const Event& e) {
  char msg[160];
  snprintf(msg, sizeof msg,
           "{\"id\":\"%s\",\"ts\":%lu,\"up\":%lu,\"event\":\"%s\",\"src\":\"%s\"}",
           deviceId, (unsigned long)e.epoch, (unsigned long)e.upMs, e.type, e.src);
  return mqtt.publish(topicEvent, msg);
}

static void publishState() {
  Status s;
  if (xSemaphoreTake(statusMutex, pdMS_TO_TICKS(10)) != pdTRUE) return;
  s = sharedStatus;
  xSemaphoreGive(statusMutex);

  char msg[320];
  snprintf(msg, sizeof msg,
           "{\"id\":\"%s\",\"fw\":\"%s\",\"ts\":%lu,\"state\":\"%s\",\"door\":\"%s\",\"pir\":\"%s\","
           "\"rssi\":%d,\"events\":%lu,\"alarms\":%lu,\"dropped\":%lu,\"queued\":%u,\"up_s\":%lu}",
           deviceId, FW_VERSION, (unsigned long)epochNow(), stateName(s.state),
           s.doorOpen ? "open" : "closed",
           !s.pirWarm ? "warmup" : (s.pirActive ? "motion" : "idle"),
           (int)netRssi, (unsigned long)s.events, (unsigned long)s.alarms,
           (unsigned long)s.dropped, (unsigned)uxQueueMessagesWaiting(eventQ),
           (unsigned long)(s.upMs / 1000));
  mqtt.publish(topicState, msg, true);   // retained: a new subscriber sees the last state at once
}

// One iteration of the network state machine. Kept separate from the task body so it
// can be unit-tested on a PC.
static void networkStep(uint32_t now) {
  bool w = WiFi.status() == WL_CONNECTED;
  if (w && !netWifiUp) {
    configTzTime(TZ_STRING, "pool.ntp.org", "time.google.com");
    Serial.println("Wi-Fi connected");
  }
  netWifiUp = w;

  if (!w) {
    netMqttUp = false;
    if ((now - lastWifiTry) >= WIFI_RETRY_MS) {
      lastWifiTry = now;
      WiFi.disconnect();
      WiFi.begin(WIFI_SSID, WIFI_PASS, WIFI_CHANNEL);
    }
    return;
  }
  netRssi = (int8_t)WiFi.RSSI();

  if (!mqtt.connected()) {
    netMqttUp = false;
    if ((now - lastMqttTry) < MQTT_RETRY_MS) return;
    lastMqttTry = now;
    if (!connectMqtt()) return;
  }
  netMqttUp = true;
  mqtt.loop();

  // Deliver queued events oldest first; remove from the queue only after a good publish.
  Event e;
  for (int i = 0; i < 4 && xQueuePeek(eventQ, &e, 0) == pdTRUE; i++) {
    bool ok = publishEvent(e);
    if (!ok && !mqtt.connected()) break;   // link lost: keep the event, retry after reconnect
    xQueueReceive(eventQ, &e, 0);          // delivered (or unpublishable): remove it
  }

  if (statusPublishNow || (now - lastHeartbeat) >= HEARTBEAT_MS) {
    statusPublishNow = false;
    lastHeartbeat = now;
    publishState();
  }
}

static void networkTask(void*) {
  for (;;) {
    networkStep(millis());
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

// ============================================================================
//  Arduino entry points
// ============================================================================

void setup() {
  Serial.begin(115200);

  pinMode(PIN_PIR,       INPUT);
  pinMode(PIN_DOOR,      INPUT_PULLUP);
  pinMode(PIN_ARM_BTN,   INPUT_PULLUP);
  pinMode(PIN_LED_ARMED, OUTPUT);
  pinMode(PIN_LED_ALARM, OUTPUT);
  buzzerInit();
  digitalWrite(PIN_LED_ARMED, LOW);
  digitalWrite(PIN_LED_ALARM, LOW);

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);
  displayOk = display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  if (displayOk) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("Smart Home Security");
    display.println("firmware v" FW_VERSION);
    display.println("starting...");
    display.display();
  } else {
    Serial.println("SSD1306 not found - continuing without display");   // alarm must still work
  }

  eventQ      = xQueueCreate(16, sizeof(Event));
  cmdQ        = xQueueCreate(4,  sizeof(Cmd));
  statusMutex = xSemaphoreCreateMutex();

  uint64_t mac = ESP.getEfuseMac();
  snprintf(deviceId, sizeof deviceId, "esp32-%04X%08X", (unsigned)(mac >> 32) & 0xFFFF, (unsigned)mac);
  snprintf(topicAvail, sizeof topicAvail, "%s/%s/availability", TOPIC_ROOT, deviceId);
  snprintf(topicState, sizeof topicState, "%s/%s/state",        TOPIC_ROOT, deviceId);
  snprintf(topicEvent, sizeof topicEvent, "%s/%s/event",        TOPIC_ROOT, deviceId);
  snprintf(topicCmd,   sizeof topicCmd,   "%s/%s/cmd",          TOPIC_ROOT, deviceId);

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(512);
  mqtt.setKeepAlive(30);
  mqtt.setSocketTimeout(3);

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASS, WIFI_CHANNEL);

  bootMs = stateSince = millis();
  lastWifiTry   = bootMs;                    // WiFi.begin() was just called above
  lastHeartbeat = bootMs;
  lastMqttTry   = bootMs - MQTT_RETRY_MS;    // allow the first MQTT attempt immediately
  door.stable   = door.lastRaw   = digitalRead(PIN_DOOR)    == HIGH;
  armBtn.stable = armBtn.lastRaw = digitalRead(PIN_ARM_BTN) == HIGH;

  Serial.printf("Device %s, topics under %s/%s/\n", deviceId, TOPIC_ROOT, deviceId);
  emitEvent("boot", "system");

  xTaskCreatePinnedToCore(networkTask, "net", 8192, nullptr, 1, nullptr, 0);
}

void loop() {
  uint32_t now = millis();
  bool pirEdge, doorOpened, buttonPressed;

  readInputs(now, pirEdge, doorOpened, buttonPressed);
  handleCommands(now);
  runStateMachine(now, pirEdge, doorOpened, buttonPressed);
  driveOutputs(now);
  updateDisplay(now);
  copyStatusForNetwork(now);
  delay(2);
}
