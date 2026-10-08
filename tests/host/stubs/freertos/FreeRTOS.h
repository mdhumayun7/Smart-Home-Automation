#pragma once
#include "../Arduino.h"
typedef void* QueueHandle_t;
typedef void* SemaphoreHandle_t;
typedef int BaseType_t;
typedef uint32_t TickType_t;
#define pdTRUE 1
#define pdFALSE 0
#define pdMS_TO_TICKS(x) (x)
struct StubQueue { size_t item, cap; std::deque<std::vector<uint8_t>> q; };
inline QueueHandle_t xQueueCreate(uint32_t len, uint32_t item) { return new StubQueue{item, len, {}}; }
inline BaseType_t xQueueSend(QueueHandle_t h, const void* it, TickType_t) {
  auto* q = (StubQueue*)h; if (q->q.size() >= q->cap) return pdFALSE;
  q->q.emplace_back((const uint8_t*)it, (const uint8_t*)it + q->item); return pdTRUE; }
inline BaseType_t xQueueReceive(QueueHandle_t h, void* it, TickType_t) {
  auto* q = (StubQueue*)h; if (q->q.empty()) return pdFALSE;
  memcpy(it, q->q.front().data(), q->item); q->q.pop_front(); return pdTRUE; }
inline BaseType_t xQueuePeek(QueueHandle_t h, void* it, TickType_t) {
  auto* q = (StubQueue*)h; if (q->q.empty()) return pdFALSE;
  memcpy(it, q->q.front().data(), q->item); return pdTRUE; }
inline unsigned uxQueueMessagesWaiting(QueueHandle_t h) { return (unsigned)((StubQueue*)h)->q.size(); }
inline SemaphoreHandle_t xSemaphoreCreateMutex() { return (void*)1; }
inline BaseType_t xSemaphoreTake(SemaphoreHandle_t, TickType_t) { return pdTRUE; }
inline BaseType_t xSemaphoreGive(SemaphoreHandle_t) { return pdTRUE; }
inline void vTaskDelay(TickType_t) {}
inline BaseType_t xTaskCreatePinnedToCore(void (*)(void*), const char*, uint32_t, void*, unsigned, void*, int) { return pdTRUE; }
