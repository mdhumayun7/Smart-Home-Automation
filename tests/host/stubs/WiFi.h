#pragma once
#include "Arduino.h"
#include "freertos/FreeRTOS.h"
#define WL_CONNECTED 3
#define WL_DISCONNECTED 6
#define WIFI_STA 1
inline bool g_wifiUp = false;
inline int g_wifiBegins = 0;
struct WiFiClient {};
struct WiFiClass {
  int status() { return g_wifiUp ? WL_CONNECTED : WL_DISCONNECTED; }
  void begin(const char*, const char*, int = 0) { g_wifiBegins++; }
  void disconnect() {}
  void mode(int) {}
  void setAutoReconnect(bool) {}
  int RSSI() { return -55; }
};
inline WiFiClass WiFi;
