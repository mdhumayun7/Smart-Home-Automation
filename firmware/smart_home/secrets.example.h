// Copy this file to secrets.h in the same folder and fill in your values.
// secrets.h is listed in .gitignore and must never be committed.
// Without secrets.h the firmware uses the Wokwi Wi-Fi and the public HiveMQ broker.
#pragma once

// ---- Wi-Fi ------------------------------------------------------------------
#define SECRET_WIFI_SSID     "your-ssid"
#define SECRET_WIFI_PASS     "your-wifi-password"
#define SECRET_WIFI_CHANNEL  0            // 0 = scan all channels

// ---- MQTT broker ------------------------------------------------------------
#define SECRET_MQTT_HOST     "broker.example.com"
#define MQTT_USE_TLS         1            // 1 = TLS on port 8883 (recommended)
#define SECRET_MQTT_PORT     8883
#define SECRET_MQTT_USER     "alarm-device"
#define SECRET_MQTT_PASS     "change-me"

// PEM certificate of the certificate authority that signed the broker's certificate.
#define SECRET_MQTT_CA_CERT \
  "-----BEGIN CERTIFICATE-----\n" \
  "...\n" \
  "-----END CERTIFICATE-----\n"

// Remote DISARM over MQTT. Only allowed with TLS and credentials (enforced at compile time).
// #define ALLOW_REMOTE_DISARM 1
