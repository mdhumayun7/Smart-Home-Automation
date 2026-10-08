#pragma once
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cstdarg>
#include <ctime>
#include <string>
#include <vector>
#include <deque>
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
inline uint32_t g_now = 0;
inline uint8_t g_pin[40] = {0};
inline uint8_t g_out[40] = {0};
inline uint32_t g_buzzEdges = 0;
inline bool g_verbose = false;
inline unsigned long millis() { return g_now; }
inline void delay(uint32_t) {}
inline void pinMode(uint8_t, uint8_t) {}
inline int digitalRead(uint8_t p) { return g_pin[p]; }
inline void digitalWrite(uint8_t p, uint8_t v) {
  if (p == 23 && g_out[p] != v) g_buzzEdges++;
  g_out[p] = v;
}
#ifndef ESP_ARDUINO_VERSION_MAJOR
#define ESP_ARDUINO_VERSION_MAJOR 3
#endif
inline void ledcBuzz(uint8_t pin, uint32_t f) { uint8_t v = f ? 1 : 0; if (g_out[pin] != v) g_buzzEdges++; g_out[pin] = v; }
#if ESP_ARDUINO_VERSION_MAJOR >= 3
inline bool ledcAttach(uint8_t, uint32_t, uint8_t) { return true; }
inline uint32_t ledcWriteTone(uint8_t pin, uint32_t f) { ledcBuzz(pin, f); return f; }
#else
inline void ledcSetup(uint8_t, uint32_t, uint8_t) {}
inline void ledcAttachPin(uint8_t, uint8_t) {}
inline uint32_t ledcWriteTone(uint8_t ch, uint32_t f) { ledcBuzz(23, f); return f; }
#endif
struct Print {
  virtual void sink(const char* s) = 0;
  void print(const char* s) { sink(s); }
  void println(const char* s) { sink(s); sink("\n"); }
  void println() { sink("\n"); }
};
struct SerialClass : Print {
  void sink(const char* s) override { if (g_verbose) fputs(s, stdout); }
  void begin(unsigned long) {}
  void printf(const char* f, ...) __attribute__((format(printf, 2, 3))) {
    if (!g_verbose) return;
    va_list a; va_start(a, f); vprintf(f, a); va_end(a);
  }
};
inline SerialClass Serial;
struct EspClass { uint64_t getEfuseMac() { return 0x112233445566ULL; } };
inline EspClass ESP;
inline std::vector<std::string> g_tzCalls;
inline void configTzTime(const char* tz, const char* s1, const char* = nullptr) { g_tzCalls.push_back(std::string(tz) + "@" + s1); }
