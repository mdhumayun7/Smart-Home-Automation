/*
 * Smart Home Surveillance System  -  firmware v2.1.0
 * Target : ESP32 DevKit (Wokwi simulation or real hardware)
 * Author : MD Humayun
 *
 * New in v2.1
 *   - Armed state is stored in NVS and restored after a power cut or reset.
 *   - Loop task is supervised by the ESP32 task watchdog; the boot event reports
 *     the reset reason (power-on, watchdog, brown-out, ...).
 *   - Credentials live in an optional secrets.h (not committed); optional TLS and
 *     broker authentication. Remote DISARM cannot be enabled without TLS.
 *   - Home Assistant MQTT discovery: the device appears as an alarm panel.
 *   - Every event carries a sequence number so a client can detect gaps and duplicates.
 *   - Fixed a race in which an event could be lost without being counted when the
 *     offline queue overflowed while the network task was delivering the backlog.
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
#include <Preferences.h>
#include <esp_system.h>

#define FW_VERSION "2.1.0"

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
constexpr uint32_t PIR_WARMUP_MS      = 10000;  // 10 s suits Wokwi; use 60000 on a real HC-SR501
constexpr uint32_t PIR_CONFIRM_MS     = 150;    // PIR must stay HIGH this long
constexpr uint32_t DEBOUNCE_MS        = 40;
constexpr uint32_t OLED_REFRESH_MS    = 250;
constexpr uint32_t STATUS_COPY_MS     = 500;    // loop -> network task snapshot rate
constexpr uint32_t HEARTBEAT_MS       = 30000;
constexpr uint32_t WIFI_RETRY_MS      = 15000;
constexpr uint32_t MQTT_RETRY_MS      = 5000;

// ---- Network ----------------------------------------------------------------
// Real credentials go in secrets.h next to this file (copy secrets.example.h; the file
// is git-ignored). Without it the defaults below are used: the open Wi-Fi of the Wokwi
// simulator and the public HiveMQ broker, which anyone can read and write.
#if defined(__has_include)
#  if __has_include("secrets.h")
#    include "secrets.h"
#  endif
#endif
#ifndef SECRET_WIFI_SSID
#  define SECRET_WIFI_SSID "Wokwi-GUEST"
#  define SECRET_WIFI_PASS ""
#endif
#ifndef SECRET_WIFI_CHANNEL
#  define SECRET_WIFI_CHANNEL 6        // Wokwi connects fastest on channel 6; 0 = scan
#endif
#ifndef SECRET_MQTT_HOST
#  define SECRET_MQTT_HOST "broker.hivemq.com"
#endif
#ifndef MQTT_USE_TLS
#  define MQTT_USE_TLS 0               // 1 = TLS (port 8883) with the CA certificate below
#endif
#ifndef SECRET_MQTT_PORT
#  define SECRET_MQTT_PORT (MQTT_USE_TLS ? 8883 : 1883)
#endif
#ifndef SECRET_MQTT_USER
#  define SECRET_MQTT_USER nullptr
#  define SECRET_MQTT_PASS nullptr
#  define MQTT_HAS_LOGIN 0
#else
#  define MQTT_HAS_LOGIN 1
#endif
#if MQTT_USE_TLS && !defined(SECRET_MQTT_CA_CERT)
#  error "MQTT_USE_TLS needs SECRET_MQTT_CA_CERT (PEM of the broker's CA) in secrets.h"
#endif

const char*    WIFI_SSID    = SECRET_WIFI_SSID;
const char*    WIFI_PASS    = SECRET_WIFI_PASS;
constexpr int  WIFI_CHANNEL = SECRET_WIFI_CHANNEL;
const char*    MQTT_HOST    = SECRET_MQTT_HOST;
constexpr uint16_t MQTT_PORT = SECRET_MQTT_PORT;
const char*    MQTT_USER    = SECRET_MQTT_USER;
const char*    MQTT_PASS    = SECRET_MQTT_PASS;
#define TOPIC_ROOT "svnit/smarthome"

// Home Assistant MQTT discovery (retained config under homeassistant/alarm_control_panel/).
#define HA_DISCOVERY 1
#define HA_PREFIX "homeassistant"

// Restore the armed state from NVS after a power cut or reset (recommended).
#define RESTORE_ARMED_ON_BOOT 1

// Supervise the safety loop with the task watchdog (default timeout 5 s).
#define ENABLE_LOOP_WDT 1

// 0 = passive piezo buzzer driven with a 2.7 kHz tone (also what Wokwi needs to make sound).
// 1 = active buzzer with built-in oscillator, driven with a plain HIGH/LOW level.
#define BUZZER_ACTIVE 0
constexpr uint32_t BUZZER_FREQ_HZ = 2700;

// 0 = remote DISARM is refused. It can only be enabled together with TLS and a broker
// login, because otherwise anyone who learns the topic could switch the alarm off.
#ifndef ALLOW_REMOTE_DISARM
#  define ALLOW_REMOTE_DISARM 0
#endif
#if ALLOW_REMOTE_DISARM && (!MQTT_USE_TLS || !MQTT_HAS_LOGIN)
#  error "ALLOW_REMOTE_DISARM requires MQTT_USE_TLS 1 and broker credentials in secrets.h"
#endif

#define TZ_STRING "IST-5:30"

// ============================================================================
//  Types
// ============================================================================

enum class SysState : uint8_t { DISARMED, EXIT_DELAY, ARMED, ENTRY_DELAY, ALARM };
enum class Cmd      : uint8_t { ARM, DISARM, STATUS };

struct Event {
  uint32_t seq;       // increases by one per event since boot; gaps reveal losses
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

// State names in the vocabulary of the Home Assistant MQTT alarm control panel.
static const char* haStateName(SysState s) {
  switch (s) {
    case SysState::DISARMED:    return "disarmed";
    case SysState::EXIT_DELAY:  return "arming";
    case SysState::ARMED:       return "armed_away";
    case SysState::ENTRY_DELAY: return "pending";
    case SysState::ALARM:       return "triggered";
  }
  return "unknown";
}

static const char* resetReasonName(esp_reset_reason_t r) {
  switch (r) {
    case ESP_RST_POWERON:   return "poweron";
    case ESP_RST_EXT:       return "external";
    case ESP_RST_SW:        return "software";
    case ESP_RST_PANIC:     return "panic";
    case ESP_RST_INT_WDT:   return "int_wdt";
    case ESP_RST_TASK_WDT:  return "task_wdt";
    case ESP_RST_WDT:       return "wdt";
    case ESP_RST_DEEPSLEEP: return "deepsleep";
    case ESP_RST_BROWNOUT:  return "brownout";
    default:                return "unknown";
  }
}

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
static uint32_t  eventSeq    = 0;
static Preferences prefs;
static bool      nvsOk       = false;
static bool      persistedArmed = false;
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
static volatile uint32_t netDropped  = 0;    // events the network task had to discard

// ---- Network core (network task, core 0) -----------------------------------
#if MQTT_USE_TLS
#include <WiFiClientSecure.h>
static WiFiClientSecure netClient;
#else
static WiFiClient       netClient;
#endif
static PubSubClient mqtt(netClient);
static char deviceId[24];
static char topicAvail[64], topicState[64], topicEvent[64], topicCmd[64], topicHa[96];
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
  e.seq   = ++eventSeq;
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

// Writes the armed flag to NVS only when it changes (one write per arm and per disarm),
// so flash wear is negligible. A write takes a few milliseconds.
static void persistArmed(bool armed) {
  if (!nvsOk || armed == persistedArmed) return;
  prefs.putBool("armed", armed);
  persistedArmed = armed;
}

static void setState(SysState next, const char* evType, const char* src, uint32_t now) {
  state      = next;
  stateSince = now;
  statusDirty = true;
  emitEvent(evType, src);
  if (next == SysState::ARMED)    persistArmed(true);
  if (next == SysState::DISARMED) persistArmed(false);
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
  if      (strcmp(buf, "ARM") == 0 || strcmp(buf, "ARM_AWAY") == 0) c = Cmd::ARM;
  else if (strcmp(buf, "DISARM") == 0) c = Cmd::DISARM;
  else if (strcmp(buf, "STATUS") == 0) c = Cmd::STATUS;
  else { Serial.printf("MQTT: unknown command '%s'\n", buf); return; }
  xQueueSend(cmdQ, &c, 0);
}

// Home Assistant discovery: the device shows up as an alarm control panel. The panel
// reads the "ha" field of the state message and sends ARM / DISARM on the command topic.
static void publishDiscovery() {
  char msg[720];
  snprintf(msg, sizeof msg,
           "{\"name\":\"Alarm\",\"unique_id\":\"%s_alarm\",\"state_topic\":\"%s\","
           "\"value_template\":\"{{ value_json.ha }}\",\"command_topic\":\"%s\","
           "\"payload_arm_away\":\"ARM\",\"payload_disarm\":\"DISARM\","
           "\"supported_features\":[\"arm_away\"],\"code_arm_required\":false,"
           "\"code_disarm_required\":false,\"availability_topic\":\"%s\","
           "\"device\":{\"identifiers\":[\"%s\"],\"name\":\"Smart Home Surveillance\","
           "\"manufacturer\":\"MD Humayun\",\"model\":\"ESP32 DevKit v1\",\"sw_version\":\"%s\"}}",
           deviceId, topicState, topicCmd, topicAvail, deviceId, FW_VERSION);
  mqtt.publish(topicHa, msg, true);
}

static bool connectMqtt() {
  bool ok = mqtt.connect(deviceId, MQTT_USER, MQTT_PASS, topicAvail, 1, true, "offline");
  if (!ok) { Serial.printf("MQTT connect failed, rc=%d\n", mqtt.state()); return false; }
  mqtt.publish(topicAvail, "online", true);
  mqtt.subscribe(topicCmd);
#if HA_DISCOVERY
  publishDiscovery();
#endif
  statusPublishNow = true;
  Serial.println("MQTT connected");
  return true;
}

static bool publishEvent(const Event& e) {
  char msg[176];
  snprintf(msg, sizeof msg,
           "{\"id\":\"%s\",\"seq\":%lu,\"ts\":%lu,\"up\":%lu,\"event\":\"%s\",\"src\":\"%s\"}",
           deviceId, (unsigned long)e.seq, (unsigned long)e.epoch, (unsigned long)e.upMs, e.type, e.src);
  return mqtt.publish(topicEvent, msg);
}

static void publishState() {
  Status s;
  if (xSemaphoreTake(statusMutex, pdMS_TO_TICKS(10)) != pdTRUE) return;
  s = sharedStatus;
  xSemaphoreGive(statusMutex);

  char msg[360];
  snprintf(msg, sizeof msg,
           "{\"id\":\"%s\",\"fw\":\"%s\",\"ts\":%lu,\"state\":\"%s\",\"ha\":\"%s\",\"door\":\"%s\",\"pir\":\"%s\","
           "\"rssi\":%d,\"events\":%lu,\"alarms\":%lu,\"dropped\":%lu,\"queued\":%u,\"up_s\":%lu}",
           deviceId, FW_VERSION, (unsigned long)epochNow(), stateName(s.state), haStateName(s.state),
           s.doorOpen ? "open" : "closed",
           !s.pirWarm ? "warmup" : (s.pirActive ? "motion" : "idle"),
           (int)netRssi, (unsigned long)s.events, (unsigned long)s.alarms,
           (unsigned long)(s.dropped + netDropped), (unsigned)uxQueueMessagesWaiting(eventQ),
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

  // Deliver queued events oldest first. The event is taken out of the queue before it is
  // published, so the loop task's drop-oldest overflow handling can never remove a
  // different event than the one in flight. If the link drops, the event goes back to
  // the front of the queue and is retried after reconnecting.
  Event e;
  for (int i = 0; i < 4 && xQueueReceive(eventQ, &e, 0) == pdTRUE; i++) {
    if (publishEvent(e)) continue;
    if (mqtt.connected()) { netDropped++; continue; }           // unsendable message
    if (xQueueSendToFront(eventQ, &e, 0) != pdTRUE) netDropped++;  // queue refilled meanwhile
    break;
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
  snprintf(topicHa,    sizeof topicHa,    "%s/alarm_control_panel/%s/config", HA_PREFIX, deviceId);

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(1024);   // discovery config is about 700 bytes
  mqtt.setKeepAlive(30);
  mqtt.setSocketTimeout(3);
#if MQTT_USE_TLS
  netClient.setCACert(SECRET_MQTT_CA_CERT);
#endif

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
  emitEvent("boot", resetReasonName(esp_reset_reason()));

  // Restore the armed state after a power cut, so cutting the supply cannot disarm the house.
  nvsOk = prefs.begin("alarm", false);
  persistedArmed = nvsOk && prefs.getBool("armed", false);
#if RESTORE_ARMED_ON_BOOT
  if (persistedArmed) {
    setState(SysState::ARMED, "restored_armed", "nvs", bootMs);
    if (door.stable) trigger("door_open", "door", bootMs);   // door found open at power-up
  }
#endif

#if ENABLE_LOOP_WDT
  enableLoopWDT();   // the Arduino loop task now feeds the task watchdog on every pass
#endif

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
