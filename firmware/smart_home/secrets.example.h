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

// ---- Authenticated commands (v2.2) -----------------------------------------
// Shared key for HMAC-signed commands. Use a long random string. With AUTH_COMMANDS 1,
// unsigned commands are rejected and a signed command may also disarm (replay- and
// forgery-proof). Sign commands with tools/sign_command.py using the same key.
#define SECRET_CMD_KEY       "change-me-to-a-long-random-string"
// #define AUTH_COMMANDS      1

// ---- ESP-NOW fallback alert channel (v2.2) ---------------------------------
// Shared key and receiver MAC for signed ESP-NOW alerts when MQTT is unreachable.
// #define ENABLE_ESPNOW      1
#define SECRET_ALERT_KEY     "change-me-to-another-long-random-string"
// #define SECRET_ESPNOW_PEER {0x24,0x6F,0x28,0x11,0x22,0x33}   // receiver MAC

// ---- Sensor fusion (v2.2) --------------------------------------------------
// Add an LD2410 mmWave radar on PIN_RADAR and require both sensors to agree.
// #define FUSION_MODE        FUSION_AND

// Remote DISARM without command signing. Only allowed with TLS and credentials, or with
// AUTH_COMMANDS (enforced at compile time). Prefer AUTH_COMMANDS.
// #define ALLOW_REMOTE_DISARM 1
