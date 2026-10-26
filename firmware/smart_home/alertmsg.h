// alertmsg.h - signed alert message shared by the alarm and the ESP-NOW receiver.
//
// When MQTT cannot be reached (Wi-Fi deauth-attacked, router down, broker unreachable),
// the alarm sends critical events over ESP-NOW to a nearby receiver node on a separate
// supply. ESP-NOW is peer-to-peer and does not use the access point, so a deauth flood
// aimed at the AP does not stop it (a wideband jammer still would; see the docs).
//
// Each alert is authenticated with HMAC-SHA256 over its fixed fields, so the receiver
// trusts only the real device and an attacker cannot inject fake alerts to cause alarm
// fatigue. The counter lets the receiver drop duplicates and stale replays.
//
// The struct is packed and endian-explicit so the same bytes are produced on the sender
// and checked on the receiver, and so the build/verify logic can be unit-tested on a PC.
#pragma once
#include <stdint.h>
#include <string.h>
#include "authmac.h"

#pragma pack(push, 1)
struct AlertMsg {
  uint8_t  magic[2];   // 'S','H' - quick reject of foreign ESP-NOW traffic
  uint8_t  version;    // 1
  uint8_t  event;      // AlertEvent
  uint32_t counter;    // monotonic, little-endian
  uint32_t upMs;       // sender millis(), little-endian
  char     deviceId[20];
  uint8_t  tag[8];     // first 8 bytes of HMAC-SHA256(key, all fields above)
};
#pragma pack(pop)

enum AlertEvent : uint8_t {
  ALERT_ALARM     = 1,
  ALERT_ENTRY     = 2,
  ALERT_WIFI_DEAUTH = 3,
  ALERT_LINK_LOST = 4,
  ALERT_TAMPER    = 5,
};

static inline void wr32(uint8_t* p, uint32_t v) {
  p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}

// Fill `m` and its tag. `key` is the shared secret; `deviceId` is copied and truncated.
static inline void alert_build(AlertMsg& m, const char* key, size_t keyLen,
                               uint8_t event, uint32_t counter, uint32_t upMs,
                               const char* deviceId) {
  memset(&m, 0, sizeof m);
  m.magic[0] = 'S'; m.magic[1] = 'H';
  m.version = 1;
  m.event = event;
  wr32((uint8_t*)&m.counter, counter);
  wr32((uint8_t*)&m.upMs, upMs);
  snprintf(m.deviceId, sizeof m.deviceId, "%s", deviceId);
  uint8_t full[32];
  size_t signedLen = sizeof(AlertMsg) - sizeof(m.tag);   // everything before the tag
  authmac::hmac_sha256((const uint8_t*)key, keyLen, (const uint8_t*)&m, signedLen, full);
  memcpy(m.tag, full, sizeof m.tag);
}

// Returns true if `m` is a well-formed alert with a valid tag for `key`.
static inline bool alert_verify(const AlertMsg& m, const char* key, size_t keyLen) {
  if (m.magic[0] != 'S' || m.magic[1] != 'H' || m.version != 1) return false;
  uint8_t full[32];
  size_t signedLen = sizeof(AlertMsg) - sizeof(m.tag);
  authmac::hmac_sha256((const uint8_t*)key, keyLen, (const uint8_t*)&m, signedLen, full);
  return authmac::ct_equal(full, m.tag, sizeof m.tag);
}

static inline const char* alert_name(uint8_t event) {
  switch (event) {
    case ALERT_ALARM:       return "ALARM";
    case ALERT_ENTRY:       return "ENTRY_DELAY";
    case ALERT_WIFI_DEAUTH: return "WIFI_DEAUTH";
    case ALERT_LINK_LOST:   return "LINK_LOST";
    case ALERT_TAMPER:      return "TAMPER";
    default:                return "UNKNOWN";
  }
}
