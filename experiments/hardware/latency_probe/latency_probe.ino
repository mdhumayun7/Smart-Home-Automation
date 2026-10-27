/*
 * Latency probe - runs on a SEPARATE ESP32, not the alarm under test.
 *
 * It measures the time from the alarm's PIR line going high to the alarm's buzzer line going
 * active, using the hardware timer of this independent board. Keeping the measurement on its
 * own chip means the clock doing the timing is never the clock under load, so a latency change
 * cannot be an artefact of the device under test timing itself.
 *
 * Wiring: PIN_PIR_SENSE to the alarm's PIR OUT line, PIN_BUZZ_SENSE to the alarm's buzzer line,
 * and a common ground between the two boards. Both are inputs here.
 *
 * Output: one CSV row per intrusion on the serial port: index,latency_us
 */
#include <Arduino.h>

constexpr uint8_t PIN_PIR_SENSE  = 34;   // input-only pins are fine for sensing
constexpr uint8_t PIN_BUZZ_SENSE = 35;

volatile uint64_t tPir = 0;
volatile bool     armed = false;         // waiting for the buzzer edge after a PIR edge
volatile uint32_t index = 0;

void IRAM_ATTR onPir() {
  if (!armed) { tPir = (uint64_t)esp_timer_get_time(); armed = true; }
}

void IRAM_ATTR onBuzz() {
  if (armed) {
    uint64_t dt = (uint64_t)esp_timer_get_time() - tPir;
    // Print from the ISR-safe path: stash and let loop() emit.
    Serial.printf("%lu,%llu\n", (unsigned long)index++, (unsigned long long)dt);
    armed = false;
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PIR_SENSE, INPUT);
  pinMode(PIN_BUZZ_SENSE, INPUT);
  attachInterrupt(PIN_PIR_SENSE, onPir, RISING);
  attachInterrupt(PIN_BUZZ_SENSE, onBuzz, RISING);
  Serial.println("# latency_probe ready: index,latency_us");
}

void loop() {
  // A PIR edge with no buzzer within 2 s means the trigger did not lead to an alarm
  // (e.g. it was disarmed); reset so the next intrusion is measured cleanly.
  static uint64_t lastCheck = 0;
  uint64_t now = (uint64_t)esp_timer_get_time();
  if (armed && now - tPir > 2000000ULL) armed = false;
  if (now - lastCheck > 1000000ULL) lastCheck = now;   // heartbeat tick, no output
  delay(5);
}
