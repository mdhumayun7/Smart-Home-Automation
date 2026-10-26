# Hardening Guide

The default build is a demonstration: open Wi-Fi, a public broker, no command signing. This
guide turns it into a deployable system. Steps are ordered by how much security they add for
the effort. Each maps to a threat in [THREAT_MODEL.md](THREAT_MODEL.md).

## 1. Move secrets out of the source (T10)

Copy `firmware/smart_home/secrets.example.h` to `secrets.h` (git-ignored) and set your Wi-Fi
and broker details. Never commit real credentials or keys.

## 2. Authenticate commands (T1, T2)

Set a strong shared key and require signed commands:

```c
#define SECRET_CMD_KEY  "a long random string, at least 32 bytes"
#define AUTH_COMMANDS   1
```

With `AUTH_COMMANDS 1`, unsigned commands are rejected (`cmd_unauth`). A valid signed command
also authorizes remote disarm, because the counter and tag defeat replay and forgery. Send
commands with:

```bash
python3 tools/sign_command.py DISARM 1001 --key-file cmd_key.txt
```

The counter must strictly increase and must beat the device's stored value across reboots.
Keep a counter file on the sender side, or start well above any value used before.

## 3. Encrypt and authenticate the transport (T3)

Use a private broker (e.g. Mosquitto) with per-device credentials and TLS:

```c
#define MQTT_USE_TLS      1
#define SECRET_MQTT_HOST  "broker.example.com"
#define SECRET_MQTT_USER  "alarm-device-01"
#define SECRET_MQTT_PASS  "..."
#define SECRET_MQTT_CA_CERT "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n"
```

On the broker, restrict each device with an ACL to only its own topic subtree. Measured TLS
overhead on the ESP32 is small (see [EVALUATION.md](EVALUATION.md)).

## 4. Enable the Wi-Fi attack monitor and the fallback channel (T4, T5, T8)

The deauth monitor is on by default (`ENABLE_WIFI_GUARD 1`). For the fallback alert, flash a
second ESP32 with `firmware/espnow_receiver`, set a shared alert key, and give the alarm the
receiver's MAC:

```c
#define ENABLE_ESPNOW       1
#define SECRET_ALERT_KEY    "another long random string"
#define SECRET_ESPNOW_PEER  {0x24,0x6F,0x28,0x11,0x22,0x33}   // receiver MAC
```

Put the same `ALERT_KEY` in the receiver sketch. Note the ESP-NOW channel caveat: a device
connected to an access point uses the AP's channel, so set the receiver to that channel. A
wideband jammer (T6) defeats ESP-NOW too; the local siren remains the last line of defence.

## 5. Survive power loss and hangs (T7, T9)

On by default: `RESTORE_ARMED_ON_BOOT 1` and `ENABLE_LOOP_WDT 1`. Add a small battery or
supercapacitor backup so a brief mains cut does not reset the device at all, and a tamper
switch on the enclosure wired like the door contact.

## 6. Reduce false alarms with sensor fusion (T12)

Add an LD2410 mmWave radar on `PIN_RADAR` and require both sensors to agree:

```c
#define FUSION_MODE  FUSION_AND   // or FUSION_OR for maximum sensitivity
```

`FUSION_AND` suppresses a lone PIR trigger until the radar corroborates it within
`FUSION_WINDOW_MS`, cutting heat/sunlight false alarms.

## 7. Secure the firmware image (T10, T11) - future

Not yet implemented; the path is:

- Enable ESP32 flash encryption and secure boot v2 so secrets in NVS and the image are
  protected at rest and only signed firmware boots.
- Add signed over-the-air updates (verify an image signature before applying).

## 8. Production checklist

- [ ] `secrets.h` present, not committed; strong unique keys.
- [ ] `AUTH_COMMANDS 1`; command counter seeded above any previous value.
- [ ] `MQTT_USE_TLS 1`; private broker; per-device credentials; topic ACLs.
- [ ] ESP-NOW receiver deployed on separate power; `SECRET_ESPNOW_PEER` set.
- [ ] `PIR_WARMUP_MS` set to ~60 s for a real HC-SR501.
- [ ] Battery backup and tamper switch fitted.
- [ ] Flash encryption and secure boot enabled.
- [ ] A consumer treats loss of the heartbeat / `offline` Last Will as an alarm.
