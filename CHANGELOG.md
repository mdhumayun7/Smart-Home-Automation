# Changelog

## 2.0.0

### Changed
- Replaced the five blocking `delay(1000)` buzzer calls with non-blocking `millis()` logic.
- Motion detection no longer depends on Wi-Fi; the alarm works offline.
- Notifications are real MQTT events instead of a Serial message.
- Display initialisation failure no longer halts the program.

### Added
- Arm / disarm state machine (DISARMED, EXIT_DELAY, ARMED, ENTRY_DELAY, ALARM).
- Door switch and ARM button inputs with debouncing; PIR warm-up and confirmation filter.
- Network task on core 0 with Wi-Fi/NTP/MQTT reconnect, Last Will, heartbeat and retained state.
- Offline event queue (16 deep) and remote `ARM` / `STATUS` commands.
- Status LEDs, tone-driven buzzer, richer OLED status screen.
- Wokwi circuit, architecture and wiring diagrams.
- Host-side tests and CI.

### Fixed
- Buzzer beep timer could leave the buzzer on after about 25 days of uptime (found by the wrap-around tests).

## 1.0.0

Initial Wokwi prototype: ESP32, PIR sensor, buzzer and OLED with blocking alarm logic.
