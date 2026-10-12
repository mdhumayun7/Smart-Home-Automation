#pragma once
#include "Arduino.h"
#include <map>
// In-memory model of the ESP32 NVS key-value store.
inline std::map<std::string, bool> g_nvs;
inline int  g_nvsWrites = 0;
inline bool g_nvsAvailable = true;
struct Preferences {
  bool begin(const char*, bool = false) { return g_nvsAvailable; }
  void end() {}
  bool getBool(const char* k, bool def = false) { auto it = g_nvs.find(k); return it == g_nvs.end() ? def : it->second; }
  size_t putBool(const char* k, bool v) { g_nvs[k] = v; g_nvsWrites++; return 1; }
};
