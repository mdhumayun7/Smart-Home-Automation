# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## 2.1.0 - 2026-10-12

### Added
- Armed state stored in NVS and restored after a power cut or reset; a door found open at power-up starts the entry delay.
- Task watchdog on the safety loop; the boot event reports the reset reason (power-on, watchdog, brown-out, ...).
- Optional `secrets.h` for Wi-Fi and broker credentials (`secrets.example.h` provided, file git-ignored).
- Optional TLS (port 8883) with CA certificate and broker login.
- Home Assistant MQTT discovery: the device appears as an alarm control panel; the state message carries the Home Assistant state name (`ha`).
- Sequence number (`seq`) on every event so clients can detect gaps and duplicates.
- `ARM_AWAY` accepted as an alias of `ARM`.
- CI compiles the firmware for the ESP32 with arduino-esp32 2.0.17 and the latest 3.x release and reports flash and RAM usage.
- Host tests for persistence, restore, diagnostics, discovery and the queue race; every MQTT payload is validated as JSON; tests build with `-Werror`.
- State machine and event sequence diagrams; demo video of a software-in-the-loop run.
- `SECURITY.md` with the threat model.

### Changed
- Remote `DISARM` can only be enabled together with TLS and a broker login (compile-time check).
- MQTT packet buffer raised to 1024 bytes for the discovery message.

### Fixed
- When the offline queue overflowed while the network task was delivering the backlog, an event could be removed without being published or counted. The network task now takes the event out of the queue before publishing and puts it back at the front if the link drops; unrecoverable events are counted in `dropped`.

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
