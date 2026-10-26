// wifi_guard.h - detect a Wi-Fi deauthentication / disassociation flood.
//
// A common way to silence a Wi-Fi alarm is to flood 802.11 deauth or disassoc
// management frames so the device is knocked off the network and its MQTT alerts stop.
// The device cannot be tricked into believing it is still online, but it CAN tell a
// deliberate attack apart from an ordinary outage: a burst of deauth/disassoc frames in
// a short window is characteristic of the attack, not of a router simply losing power.
//
// This header holds only the decision logic, as a sliding-window counter, so it can be
// unit-tested on a PC with no radio. The on-device promiscuous-mode capture that feeds it
// lives in the sketch behind ENABLE_WIFI_GUARD. Nothing here transmits; it only observes.
#pragma once
#include <stdint.h>

struct DeauthDetector {
  uint32_t windowMs;      // observation window
  uint32_t threshold;     // frames within the window that count as a flood
  uint32_t cooldownMs;    // minimum gap between two reported detections
  // state
  uint32_t times[32];     // ring buffer of recent frame timestamps (ms)
  uint8_t  head;
  uint8_t  count;
  uint32_t lastReport;
  bool     reportedOnce;
};

static inline void deauth_init(DeauthDetector& d, uint32_t windowMs,
                               uint32_t threshold, uint32_t cooldownMs) {
  d.windowMs = windowMs;
  d.threshold = threshold > 32 ? 32 : threshold;
  d.cooldownMs = cooldownMs;
  d.head = 0;
  d.count = 0;
  d.lastReport = 0;
  d.reportedOnce = false;
}

// Record one deauth/disassoc frame seen at time `now`. Returns true exactly on the
// transition where the count within the window first reaches the threshold, and not
// again until the cooldown has passed, so one attack raises one event rather than a storm.
static inline bool deauth_observe(DeauthDetector& d, uint32_t now) {
  const uint8_t cap = 32;
  d.times[d.head] = now;
  d.head = (uint8_t)((d.head + 1) % cap);
  if (d.count < cap) d.count++;

  uint32_t within = 0;
  for (uint8_t i = 0; i < d.count; i++) {
    uint32_t t = d.times[i];
    if ((uint32_t)(now - t) <= d.windowMs) within++;   // wrap-safe elapsed
  }

  if (within >= d.threshold) {
    if (!d.reportedOnce || (uint32_t)(now - d.lastReport) >= d.cooldownMs) {
      d.lastReport = now;
      d.reportedOnce = true;
      return true;
    }
  }
  return false;
}
