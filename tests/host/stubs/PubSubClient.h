#pragma once
#include "WiFi.h"
struct Pub { std::string topic, payload; bool retained; };
inline std::vector<Pub> g_pubs;
inline std::vector<std::string> g_subs;
inline bool g_brokerAccepts = false;   // can connect() succeed
inline bool g_linkUp = false;          // socket currently alive
inline int  g_connectCalls = 0;
inline bool g_failNextPublishAndDrop = false;
inline std::string g_lastWillTopic;
struct PubSubClient {
  void (*cb)(char*, uint8_t*, unsigned int) = nullptr;
  PubSubClient(WiFiClient&) {}
  PubSubClient& setServer(const char*, uint16_t) { return *this; }
  PubSubClient& setCallback(void (*c)(char*, uint8_t*, unsigned int)) { cb = c; return *this; }
  PubSubClient& setKeepAlive(uint16_t) { return *this; }
  PubSubClient& setSocketTimeout(uint16_t) { return *this; }
  bool setBufferSize(uint16_t) { return true; }
  bool connect(const char*, const char*, const char*, const char* willTopic, uint8_t, bool, const char*) {
    g_connectCalls++; g_lastWillTopic = willTopic ? willTopic : "";
    g_linkUp = g_brokerAccepts; return g_linkUp; }
  bool connected() { return g_linkUp; }
  int state() { return -2; }
  bool loop() { return g_linkUp; }
  bool subscribe(const char* t) { g_subs.push_back(t); return true; }
  bool publish(const char* t, const char* p) { return publish(t, p, false); }
  bool publish(const char* t, const char* p, bool r) {
    if (!g_linkUp) return false;
    if (g_failNextPublishAndDrop) { g_failNextPublishAndDrop = false; g_linkUp = false; return false; }
    g_pubs.push_back({t, p, r}); return true; }
};
