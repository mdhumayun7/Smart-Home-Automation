// sensor_fusion.h - combine a PIR sensor with an mmWave presence radar (e.g. LD2410).
//
// A PIR alone both misses (a still intruder stops radiating a changing signature) and
// false-triggers (a warm draught, sunlight on a wall). An mmWave radar sees fine motion
// and presence but reacts to movement behind thin walls. Fusing the two lets the installer
// trade sensitivity against false alarms:
//
//   FUSION_PIR_ONLY : the PIR edge only (default; unchanged behaviour).
//   FUSION_OR       : either sensor triggers      -> highest sensitivity.
//   FUSION_AND      : both agree within a window   -> fewest false alarms.
//
// The radar's digital presence pin is read like any other input; this header holds only the
// combining logic, so the trade-off can be measured on recorded traces without hardware.
#pragma once
#include <stdint.h>

enum FusionMode : uint8_t { FUSION_PIR_ONLY = 0, FUSION_OR = 1, FUSION_AND = 2 };

struct SensorFusion {
  uint8_t  mode;
  uint32_t windowMs;    // for FUSION_AND: how recently the other sensor must have agreed
  uint32_t lastPir;     // last PIR confirmation time
  uint32_t lastRadar;   // last time radar reported presence
  bool     radarPrev;   // previous radar level, for edge detection
  bool     seeded;
};

static inline void fusion_init(SensorFusion& f, uint8_t mode, uint32_t windowMs) {
  f.mode = mode; f.windowMs = windowMs;
  f.lastPir = 0; f.lastRadar = 0; f.radarPrev = false; f.seeded = false;
}

// Returns a single intrusion edge for this pass. pirEdge is the PIR's confirmed rising edge;
// radarPresent is the radar's current presence level.
static inline bool fusion_step(SensorFusion& f, bool pirEdge, bool radarPresent, uint32_t now) {
  if (!f.seeded) {
    // Put both "last seen" times before the window so neither counts as recent at start-up.
    f.lastPir = f.lastRadar = now - f.windowMs - 1;
    f.seeded = true;
  }
  bool radarEdge = radarPresent && !f.radarPrev;
  f.radarPrev = radarPresent;
  if (pirEdge)      f.lastPir = now;
  if (radarPresent) f.lastRadar = now;

  switch (f.mode) {
    case FUSION_OR:
      return pirEdge || radarEdge;
    case FUSION_AND: {
      bool pirWithRadar   = pirEdge   && (radarPresent || (uint32_t)(now - f.lastRadar) <= f.windowMs);
      bool radarWithPir   = radarEdge && (pirEdge      || (uint32_t)(now - f.lastPir)   <= f.windowMs);
      return pirWithRadar || radarWithPir;
    }
    case FUSION_PIR_ONLY:
    default:
      return pirEdge;
  }
}
