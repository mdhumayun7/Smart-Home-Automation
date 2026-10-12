#pragma once
#include "WiFi.h"
inline const char* g_caCert = nullptr;
struct WiFiClientSecure : WiFiClient { void setCACert(const char* c) { g_caCert = c; } };
