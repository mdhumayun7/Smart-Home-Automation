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
#include "authmac.h"
#include "wifi_guard.h"
#include "alertmsg.h"
#include "sensor_fusion.h"

#define FW_VERSION "2.2.0"

// ============================================================================
//  Configuration
// ============================================================================

// ---- Pins -------------------------------------------------------------------
constexpr uint8_t PIN_PIR       = 13;  // PIR OUT            (input)
constexpr uint8_t PIN_RADAR     = 33;  // mmWave radar presence OUT (input), used when fusion is on
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

// ---- Wi-Fi attack detection -------------------------------------------------
// Passively watch for a deauthentication / disassociation flood, the usual way to knock
// a Wi-Fi alarm off the network and silence it. A burst of such frames is reported as a
// "wifi_deauth" event; losing the link while armed is reported as "link_lost". Both are
// treated as security events, not mere connectivity glitches. This only observes frames;
// it never transmits. Promiscuous capture needs the real radio, so it is ESP32 only.
#ifndef ENABLE_WIFI_GUARD
#  define ENABLE_WIFI_GUARD 1
#endif
constexpr uint32_t DEAUTH_WINDOW_MS   = 2000;   // observation window
constexpr uint32_t DEAUTH_THRESHOLD   = 8;      // frames in the window that signal a flood
constexpr uint32_t DEAUTH_COOLDOWN_MS = 10000;  // at most one report per 10 s

// ---- ESP-NOW fallback alert channel -----------------------------------------
// When MQTT is unreachable, send signed alerts for critical events over ESP-NOW to a
// nearby receiver node (see firmware/espnow_receiver). Needs the receiver's MAC in
// secrets.h (SECRET_ESPNOW_PEER) and a shared SECRET_ALERT_KEY; off by default.
#ifndef ENABLE_ESPNOW
#  define ENABLE_ESPNOW 0
#endif
#ifndef SECRET_ALERT_KEY
#  define SECRET_ALERT_KEY "demo-alert-key-change-me"
#endif
#ifndef SECRET_ESPNOW_PEER
#  define SECRET_ESPNOW_PEER {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF}   // broadcast until set
#endif

// ---- Sensor fusion ----------------------------------------------------------
// Combine the PIR with an mmWave presence radar (LD2410 OUT on PIN_RADAR). Default is
// PIR only, so existing hardware and behaviour are unchanged. FUSION_AND reduces false
// alarms by requiring both sensors to agree within FUSION_WINDOW_MS; FUSION_OR raises
// sensitivity. See sensor_fusion.h.
#ifndef FUSION_MODE
#  define FUSION_MODE FUSION_PIR_ONLY
#endif
constexpr uint32_t FUSION_WINDOW_MS = 1500;

// 0 = passive piezo buzzer driven with a 2.7 kHz tone (also what Wokwi needs to make sound).
// 1 = active buzzer with built-in oscillator, driven with a plain HIGH/LOW level.
#define BUZZER_ACTIVE 0
constexpr uint32_t BUZZER_FREQ_HZ = 2700;

// ---- Authenticated commands -------------------------------------------------
// A command on the MQTT topic is only trusted if it carries a valid HMAC-SHA256 tag
// over a strictly increasing counter. The tag proves the sender holds the shared key
// (integrity + source), and the counter stops an eavesdropper from replaying a
// captured "DISARM". The key is stored in secrets.h; the demo key below is public.
//
// Wire format of a signed command:  <CMD>:<counter>:<hex-tag>
//   e.g.  DISARM:42:5f3c9e7a1b2d4c6e8a0f1234567890ab
// <CMD> is ARM, DISARM or STATUS; <counter> is a decimal that must exceed the last
// accepted one; <hex-tag> is the first AUTH_TAG_BYTES of HMAC-SHA256(key, "<CMD>:<counter>").
#ifndef AUTH_COMMANDS
#  define AUTH_COMMANDS 0      // 1 = require signed commands; unsigned ones are rejected
#endif
#ifndef SECRET_CMD_KEY
#  define SECRET_CMD_KEY "demo-shared-key-change-me"   // public demo key; override in secrets.h
#endif
constexpr size_t AUTH_TAG_BYTES = 16;   // 128-bit tag: ample against forgery, short on the wire

// 0 = remote DISARM is refused. With AUTH_COMMANDS a signed DISARM is safe (the counter and
// tag defeat replay and forgery), so remote disarm is permitted when commands are authenticated.
// Without authentication it still needs TLS and a broker login, because otherwise anyone who
// learns the topic could switch the alarm off.
#ifndef ALLOW_REMOTE_DISARM
#  define ALLOW_REMOTE_DISARM 0
#endif
#if ALLOW_REMOTE_DISARM && !AUTH_COMMANDS && (!MQTT_USE_TLS || !MQTT_HAS_LOGIN)
#  error "ALLOW_REMOTE_DISARM needs AUTH_COMMANDS 1, or MQTT_USE_TLS 1 with broker credentials"
#endif

#define TZ_STRING "IST-5:30"

// ============================================================================
//  Types
// ============================================================================

enum class SysState : uint8_t { DISARMED, EXIT_DELAY, ARMED, ENTRY_DELAY, ALARM };
enum class Cmd      : uint8_t { ARM, DISARM, STATUS };

// A command as it crosses from the network task (core 0) to the safety loop (core 1).
// The MAC is verified on core 0; the replay-counter check and its NVS write happen on
// core 1, where all other NVS access lives, so the counter has a single owner.
struct CmdMsg {
  Cmd      cmd;
  bool     authed;   // carried a valid MAC over its counter
  uint32_t ctr;      // sender's counter (meaningful only when authed)
};

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
static SensorFusion fusion;

static uint32_t  eventCount  = 0;
static uint32_t  eventSeq    = 0;
static uint32_t  cmdCounter  = 0;      // highest accepted authenticated command counter
[[maybe_unused]] static uint32_t alertCounter = 0;  // ESP-NOW alert counter, persisted across resets
static Preferences prefs;
static bool      nvsOk       = false;

// Sends an ESP-NOW fallback alert for a critical event when MQTT is down. Defined later;
// a no-op when ESP-NOW is disabled or off-device.
static void espnowOnEvent(const char* type);
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
static volatile uint32_t deauthAlerts = 0;   // set by the Wi-Fi monitor, read by the loop
static bool      wasWifiUp   = false;        // previous Wi-Fi state, for link-loss detection
static uint32_t  lastDeauthSeen = 0;         // loop-side copy of the alert count

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
  espnowOnEvent(type);
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

// ---- Wi-Fi monitor ---------------------------------------------------------
#if ENABLE_WIFI_GUARD
static DeauthDetector deauthDet;

#if defined(ARDUINO_ARCH_ESP32)
#include <esp_wifi.h>
// Promiscuous callback: runs in Wi-Fi context, so it must be short and must not call the
// event path directly. It only parses the 802.11 frame-control byte and, when a flood is
// detected, bumps a counter the safety loop reads. Subtypes 0x0C = deauth, 0x0A = disassoc.
static void IRAM_ATTR wifiSniffer(void* buf, wifi_promiscuous_pkt_type_t type) {
  if (type != WIFI_PKT_MGMT) return;
  const wifi_promiscuous_pkt_t* p = (const wifi_promiscuous_pkt_t*)buf;
  uint8_t fc = p->payload[0];
  uint8_t ftype = (fc >> 2) & 0x3;
  uint8_t fsub  = (fc >> 4) & 0xF;
  if (ftype != 0 /* management */) return;
  if (fsub != 0x0C && fsub != 0x0A) return;
  if (deauth_observe(deauthDet, millis())) deauthAlerts++;
}

static void wifiGuardBegin() {
  deauth_init(deauthDet, DEAUTH_WINDOW_MS, DEAUTH_THRESHOLD, DEAUTH_COOLDOWN_MS);
  esp_wifi_set_promiscuous(true);
  wifi_promiscuous_filter_t filter = { .filter_mask = WIFI_PROMIS_FILTER_MASK_MGMT };
  esp_wifi_set_promiscuous_filter(&filter);
  esp_wifi_set_promiscuous_rx_cb(&wifiSniffer);
}
#else
static void wifiGuardBegin() { deauth_init(deauthDet, DEAUTH_WINDOW_MS, DEAUTH_THRESHOLD, DEAUTH_COOLDOWN_MS); }
#endif  // ARDUINO_ARCH_ESP32

// Called from the safety loop. Raises a "wifi_deauth" event when the monitor has flagged a
// flood, and a "link_lost" event when Wi-Fi drops while the system is armed (an attempt to
// silence the alarm is itself worth recording and escalating).
static void wifiGuardStep(uint32_t now) {
  if (deauthAlerts != lastDeauthSeen) {
    lastDeauthSeen = deauthAlerts;
    emitEvent("wifi_deauth", "radio");
  }
  bool up = netWifiUp;
  bool armed = (state != SysState::DISARMED);
  if (wasWifiUp && !up && armed) emitEvent("link_lost", "radio");
  wasWifiUp = up;
}
#endif  // ENABLE_WIFI_GUARD

// ---- ESP-NOW fallback sender -----------------------------------------------
#if ENABLE_ESPNOW && defined(ARDUINO_ARCH_ESP32)
#include <esp_now.h>
static bool espnowReady = false;

static void espnowBegin() {
  static uint8_t peer[6] = SECRET_ESPNOW_PEER;
  if (esp_now_init() != ESP_OK) { Serial.println("ESP-NOW init failed"); return; }
  esp_now_peer_info_t pi = {};
  memcpy(pi.peer_addr, peer, 6);
  pi.channel = 0;            // use the current Wi-Fi channel
  pi.encrypt = false;        // our own HMAC authenticates the payload
  if (esp_now_add_peer(&pi) != ESP_OK) { Serial.println("ESP-NOW add_peer failed"); return; }
  espnowReady = true;
  alertCounter = nvsOk ? prefs.getULong("alertctr", 0) : 0;
}

// Map a critical event name to an alert code; 0 means "not critical, do not send".
static uint8_t alertCodeFor(const char* type) {
  if (!strcmp(type, "alarm"))       return ALERT_ALARM;
  if (!strcmp(type, "entry_delay")) return ALERT_ENTRY;
  if (!strcmp(type, "wifi_deauth")) return ALERT_WIFI_DEAUTH;
  if (!strcmp(type, "link_lost"))   return ALERT_LINK_LOST;
  return 0;
}

static void espnowOnEvent(const char* type) {
  if (!espnowReady) return;
  if (netMqttUp) return;                 // MQTT is the primary path; fall back only when it is down
  uint8_t code = alertCodeFor(type);
  if (!code) return;
  static uint8_t peer[6] = SECRET_ESPNOW_PEER;
  uint32_t ctr = ++alertCounter;
  if (nvsOk) prefs.putULong("alertctr", ctr);
  AlertMsg m;
  alert_build(m, SECRET_ALERT_KEY, strlen(SECRET_ALERT_KEY), code, ctr, millis(), deviceId);
  esp_now_send(peer, (const uint8_t*)&m, sizeof m);
}
#else
static void espnowBegin() {}
static void espnowOnEvent(const char* type) { (void)type; }
#endif  // ENABLE_ESPNOW

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
  bool pirRise = confirmed && !pirConfirmed;
  pirConfirmed = confirmed;

  // Fuse with the mmWave radar. In PIR-only mode (the default) this returns the PIR edge
  // unchanged. The radar is only read when fusion is enabled, so the pin can stay unused.
  if (FUSION_MODE == FUSION_PIR_ONLY) {
    pirEdge = pirRise;
  } else {
    bool radarPresent = digitalRead(PIN_RADAR) == HIGH && pirWarm(now);
    pirEdge = fusion_step(fusion, pirRise, radarPresent, now);
  }

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

// Persist the command counter only when it advances, so replay protection survives a reset.
static void persistCounter(uint32_t v) {
  if (!nvsOk || v <= cmdCounter) return;
  cmdCounter = v;
  prefs.putULong("cmdctr", v);
}

static void handleCommands(uint32_t now) {
  CmdMsg m;
  while (xQueueReceive(cmdQ, &m, 0) == pdTRUE) {
    // Marker from the network task for a command whose MAC did not verify.
    if (!m.authed && m.ctr == 0xFFFFFFFFu) { emitEvent("cmd_badmac", "remote"); continue; }

    if (m.authed) {
      // Reject a replay: the counter must strictly advance.
      if (m.ctr <= cmdCounter) { emitEvent("cmd_replay", "remote"); continue; }
      persistCounter(m.ctr);
    }
#if AUTH_COMMANDS
    else {
      // Authentication is required but this command was unsigned.
      emitEvent("cmd_unauth", "remote");
      continue;
    }
#endif
    const char* src = m.authed ? "remote_auth" : "remote";
    switch (m.cmd) {
      case Cmd::ARM:
        if (state == SysState::DISARMED) beginArm(src, now);
        else emitEvent("cmd_ignored", src);
        break;
      case Cmd::DISARM:
        // A validly signed command proves the key holder sent it, so disarm is safe even
        // when unauthenticated remote disarm is off. ALLOW_REMOTE_DISARM keeps the old
        // escape hatch for a TLS + login deployment without command signing.
        if (m.authed || ALLOW_REMOTE_DISARM) {
          if (state != SysState::DISARMED) disarm(src, now);
          else emitEvent("cmd_ignored", src);
        } else {
          emitEvent("cmd_rejected", src);
        }
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

// Map a verb (already upper-cased) to a command. Returns false for anything unknown.
static bool parseVerb(const char* v, Cmd& out) {
  if      (strcmp(v, "ARM") == 0 || strcmp(v, "ARM_AWAY") == 0) out = Cmd::ARM;
  else if (strcmp(v, "DISARM") == 0) out = Cmd::DISARM;
  else if (strcmp(v, "STATUS") == 0) out = Cmd::STATUS;
  else return false;
  return true;
}

// Verify a signed command "<VERB>:<ctr>:<hex-tag>". On success fills cmd and ctr and
// returns true. The MAC is computed over the exact "<VERB>:<ctr>" bytes as received
// (before upper-casing), so the signer and the device agree on one canonical string.
static bool verifySigned(const char* s, unsigned len, Cmd& cmd, uint32_t& ctr) {
  const char* c1 = (const char*)memchr(s, ':', len);
  if (!c1) return false;
  const char* rest = c1 + 1;
  unsigned restLen = len - (unsigned)(rest - s);
  const char* c2 = (const char*)memchr(rest, ':', restLen);
  if (!c2) return false;

  unsigned verbLen = (unsigned)(c1 - s);
  unsigned ctrLen  = (unsigned)(c2 - rest);
  const char* tag  = c2 + 1;
  unsigned tagLen  = len - (unsigned)(tag - s);
  if (verbLen == 0 || verbLen > 10 || ctrLen == 0 || ctrLen > 10) return false;
  if (tagLen != AUTH_TAG_BYTES * 2) return false;

  char verb[12];
  memcpy(verb, s, verbLen); verb[verbLen] = 0;
  for (unsigned i = 0; i < verbLen; i++) if (verb[i] >= 'a' && verb[i] <= 'z') verb[i] -= 32;
  if (!parseVerb(verb, cmd)) return false;

  uint32_t v = 0;
  for (unsigned i = 0; i < ctrLen; i++) {
    if (rest[i] < '0' || rest[i] > '9') return false;
    v = v * 10 + (uint32_t)(rest[i] - '0');
  }
  ctr = v;

  uint8_t want[AUTH_TAG_BYTES];
  if (authmac::hex_decode(tag, tagLen, want, sizeof want) != (int)AUTH_TAG_BYTES) return false;

  uint8_t full[32];
  unsigned signedLen = (unsigned)(c2 - s);   // "<VERB>:<ctr>" exactly as received
  authmac::hmac_sha256((const uint8_t*)SECRET_CMD_KEY, strlen(SECRET_CMD_KEY),
                       (const uint8_t*)s, signedLen, full);
  return authmac::ct_equal(full, want, AUTH_TAG_BYTES);
}

static void onMqttMessage(char* topic, uint8_t* payload, unsigned int len) {
  (void)topic;
  if (len == 0 || len > 80) return;

  CmdMsg m = {};
  // A colon marks the signed form "<VERB>:<ctr>:<tag>".
  if (memchr(payload, ':', len) != nullptr) {
    if (verifySigned((const char*)payload, len, m.cmd, m.ctr)) {
      m.authed = true;
      xQueueSend(cmdQ, &m, 0);
    } else {
      m.cmd = Cmd::STATUS; m.authed = false; m.ctr = 0;    // marker: a bad signed command
      // Flag it so the safety loop can log a rejection; STATUS is harmless if mis-flagged.
      static const CmdMsg bad = { Cmd::STATUS, false, 0xFFFFFFFFu };
      xQueueSend(cmdQ, &bad, 0);
      Serial.println("MQTT: signed command failed verification");
    }
    return;
  }

  // Plain, unsigned command (no colon).
  char buf[16];
  if (len >= sizeof buf) len = sizeof buf - 1;
  memcpy(buf, payload, len);
  buf[len] = 0;
  for (unsigned i = 0; i < len; i++) if (buf[i] >= 'a' && buf[i] <= 'z') buf[i] -= 32;
  if (!parseVerb(buf, m.cmd)) { Serial.printf("MQTT: unknown command '%s'\n", buf); return; }
  m.authed = false; m.ctr = 0;
  xQueueSend(cmdQ, &m, 0);
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
  if (FUSION_MODE != FUSION_PIR_ONLY) pinMode(PIN_RADAR, INPUT);
  fusion_init(fusion, FUSION_MODE, FUSION_WINDOW_MS);
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
  cmdQ        = xQueueCreate(4,  sizeof(CmdMsg));
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
  cmdCounter     = nvsOk ? prefs.getULong("cmdctr", 0) : 0;   // replay floor survives resets
#if RESTORE_ARMED_ON_BOOT
  if (persistedArmed) {
    setState(SysState::ARMED, "restored_armed", "nvs", bootMs);
    if (door.stable) trigger("door_open", "door", bootMs);   // door found open at power-up
  }
#endif

#if ENABLE_LOOP_WDT
  enableLoopWDT();   // the Arduino loop task now feeds the task watchdog on every pass
#endif

#if ENABLE_WIFI_GUARD
  wifiGuardBegin();
#endif
  espnowBegin();

  xTaskCreatePinnedToCore(networkTask, "net", 8192, nullptr, 1, nullptr, 0);
}

void loop() {
  uint32_t now = millis();
  bool pirEdge, doorOpened, buttonPressed;

  readInputs(now, pirEdge, doorOpened, buttonPressed);
  handleCommands(now);
  runStateMachine(now, pirEdge, doorOpened, buttonPressed);
#if ENABLE_WIFI_GUARD
  wifiGuardStep(now);
#endif
  driveOutputs(now);
  updateDisplay(now);
  copyStatusForNetwork(now);
  delay(2);
}
