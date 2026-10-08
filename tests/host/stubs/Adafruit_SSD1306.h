#pragma once
#include "Adafruit_GFX.h"
#define SSD1306_SWITCHCAPVCC 0x02
#define SSD1306_WHITE 1
inline bool g_displayOk = true;
inline std::string g_frame, g_lastFrame;
struct Adafruit_SSD1306 : Adafruit_GFX {
  Adafruit_SSD1306(uint8_t, uint8_t, TwoWire*, int8_t) {}
  bool begin(uint8_t = SSD1306_SWITCHCAPVCC, uint8_t = 0, bool = true, bool = true) { return g_displayOk; }
  void clearDisplay() { g_frame.clear(); }
  void display() { g_lastFrame = g_frame; }
  void setTextColor(uint16_t) {}
  void setTextSize(uint8_t) {}
  void setCursor(int16_t, int16_t) { g_frame += "|"; }
  void sink(const char* s) override { g_frame += s; }
};
