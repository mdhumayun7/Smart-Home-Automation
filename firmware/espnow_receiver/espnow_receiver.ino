/*
 * ESP-NOW alert receiver for the Smart Home Surveillance System.
 *
 * A second ESP32 on a separate power supply. It listens for signed ESP-NOW alerts from the
 * alarm and, on a valid one, sounds a local buzzer and prints the event. Because ESP-NOW is
 * peer-to-peer and does not use the home access point, these alerts still arrive when the
 * alarm's Wi-Fi link has been deauth-attacked or the router is down. Alerts are
 * authenticated with HMAC-SHA256 and carry a counter, so the receiver trusts only the real
 * device and ignores duplicates and stale replays.
 *
 * Put the SAME shared key here as in the alarm's secrets.h (ALERT_KEY). authmac.h and
 * alertmsg.h are shared copies of the alarm's headers; CI checks they stay identical.
 *
 * Libraries: none beyond the ESP32 core.
 */
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include "alertmsg.h"

// Must match SECRET_ALERT_KEY in the alarm's secrets.h.
#ifndef ALERT_KEY
#  define ALERT_KEY "demo-alert-key-change-me"
#endif

constexpr uint8_t PIN_BUZZER = 23;
constexpr uint8_t PIN_LED    = 2;

static uint32_t lastCounter = 0;       // highest accepted counter, to drop replays
static uint32_t buzzUntil   = 0;
static bool     buzzing     = false;

// The receive-callback signature changed between arduino-esp32 2.x and 3.x.
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
static void onRecv(const esp_now_recv_info_t* info, const uint8_t* data, int len) {
  (void)info;
#else
static void onRecv(const uint8_t* mac, const uint8_t* data, int len) {
  (void)mac;
#endif
  if (len != (int)sizeof(AlertMsg)) return;
  AlertMsg m;
  memcpy(&m, data, sizeof m);
  if (!alert_verify(m, ALERT_KEY, strlen(ALERT_KEY))) {
    Serial.println("rejected: bad signature");
    return;
  }
  uint32_t ctr = m.counter;            // struct is little-endian; ESP32 is little-endian
  if (ctr <= lastCounter) { Serial.printf("ignored replay/dup counter=%lu\n", (unsigned long)ctr); return; }
  lastCounter = ctr;

  Serial.printf("ALERT %-12s from %s counter=%lu up=%lu ms\n",
                alert_name(m.event), m.deviceId, (unsigned long)ctr, (unsigned long)m.upMs);
  digitalWrite(PIN_LED, HIGH);
  buzzUntil = millis() + 5000;         // sound for 5 s, non-blocking
  buzzing = true;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_LED, LOW);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  if (esp_now_init() != ESP_OK) { Serial.println("ESP-NOW init failed"); return; }
  esp_now_register_recv_cb(onRecv);
  uint8_t ch = 1;
  esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE);   // must match the alarm's ESPNOW_CHANNEL
  Serial.println("ESP-NOW receiver ready");
}

void loop() {
  uint32_t now = millis();
  if (buzzing && (int32_t)(now - buzzUntil) >= 0) { buzzing = false; digitalWrite(PIN_LED, LOW); }
  digitalWrite(PIN_BUZZER, (buzzing && (now % 600) < 400) ? HIGH : LOW);   // pulsed siren
  delay(5);
}
