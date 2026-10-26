# Evaluation

This document sets out how the system is evaluated against the [threat model](THREAT_MODEL.md):
the method, what has been verified so far, and the exact procedure and tools for the hardware
measurements that remain. It is written so the results are reproducible and so the boundary
between "verified" and "not yet measured" is explicit.

## 1. Method

Three complementary methods are used.

1. **Formal verification (TLA+).** The alarm state machine and the authenticated-command path
   are model-checked over their whole state space. This proves properties for *all* reachable
   states, not just the ones a test happens to exercise.
2. **Software-in-the-loop (SIL) tests.** The unchanged firmware is compiled on a PC against
   models of the hardware, network, NVS and radio, and driven through attack scenarios. This
   verifies the *logic* of each defence deterministically and in CI.
3. **Hardware measurement.** On a real ESP32, with a logic analyser and a controlled broker,
   the physical quantities (latency, recovery time, current, detection timing) are measured.
   This is the part that still has to be run; the procedure and tools are given in Section 4.

What SIL cannot show is stated plainly: real radio timing, true parallel execution on the two
cores, electrical behaviour, and the effectiveness of radio-layer attacks in practice. Those
require Section 4.

## 2. Formal results

TLC checks `formal/AlarmFSM.tla` against `formal/AlarmFSM.cfg` and reports no violations over
the complete state space (25 distinct states at `MaxCtr = 4`). The properties proved:

| Property | Meaning |
|---|---|
| `NoUnauthRemoteDisarm` | No unauthenticated remote command ever disarms the system. |
| `CounterMonotonic` | The replay counter never decreases. |
| `NoAlarmWhenDisarmed` | The siren is never active while disarmed. |
| `EntryLeadsToResolve` | An entry delay always ends in alarm or disarm (no stuck state). |
| `AlarmReArms` | The alarm always ends in re-arm or disarm. |

The spec was mutation-tested: deliberately letting an unauthenticated disarm take effect makes
TLC report the `NoUnauthRemoteDisarm` violation, so the property is not vacuous.

Run it with `./formal/run_tlc.sh` (also a CI job).

## 3. Software-in-the-loop attack results

Each threat is mapped to the SIL scenario that exercises it. "Baseline" is the behaviour
without the v2.2 defence (an unauthenticated prototype, or firmware v1 for the power-cut case);
"hardened" is firmware v2.2. All hardened results are produced by `./tests/host/run_tests.sh`
in CI.

| Threat | Attack in SIL | Baseline | Hardened (v2.2) | Scenario |
|---|---|---|---|---|
| T1 Spoofing | Publish a forged `DISARM` (wrong key) | Accepted: alarm disarmed | Rejected, `cmd_badmac`, state unchanged | `auth` |
| T2 Replay | Resend a captured signed `DISARM` | Accepted: alarm disarmed | Rejected, `cmd_replay` | `auth` |
| T2 Replay across reset | Replay after the device reboots | Accepted | Rejected: counter floor restored from NVS | `auth` |
| T4 Deauth flood | Burst of deauth/disassoc frames | Undetected | Detected, `wifi_deauth`, once per cooldown | `wifiguard` |
| T4/T5 Link drop while armed | Wi-Fi lost while armed | Silent | `link_lost` event raised | `linklost` |
| T6 Alarm under outage | Network down during intrusion | (v1) no detection | Local alarm runs; events queued in order | `network`, `arm_alarm` |
| T7 Power cut while armed | Reset while armed | (v1) disarmed silently | Restored to armed; open door re-triggers | `restore`, `restore_door` |
| T8 Fake alert injection | Forged/tampered ESP-NOW alert | Accepted by a naive receiver | Rejected: bad HMAC or stale counter | `alert` |
| T12 PIR false trigger | Lone PIR edge, no corroboration | Alarm (false) | In AND-fusion, suppressed until radar agrees | `fusion` |

Test totals: 19 scenarios x 3 clock start values x 2 arduino-esp32 core APIs = 114 runs, plus
4 build-configuration checks and 2 shared-header-sync checks (120 checks), all passing, with
`-Werror` and JSON validation of every MQTT payload.

## 4. Hardware measurement procedure (to be run)

The following measurements complete the evaluation on real hardware. Each has a tool or a
documented method. Record the results in the empty table at the end.

### 4.1 Setup

- ESP32 DevKit with the v2.2 firmware, a private broker (e.g. Mosquitto on a laptop), and a
  logic analyser or oscilloscope on the sensor and output pins.
- A second ESP32 flashed with `firmware/espnow_receiver` for the fallback-channel test.
- `pip install paho-mqtt` for the measurement tools.

### 4.2 Command-authentication defences (automated)

```bash
python3 tools/eval_commands.py --host <broker> --device <id> --key <key> --start-counter 1000
```

Confirms on real hardware what Section 3 shows in SIL: forged and replayed commands are
rejected and only a fresh signed command is accepted. Expected: all checks PASS.

### 4.3 Command latency and reconnect time (automated)

```bash
python3 tools/measure.py latency   --host <broker> --device <id> [--key <key>]
python3 tools/measure.py reconnect --host <broker> --device <id>   # then power-cycle the router
```

Reports round-trip command latency (min/median/max) and the offline-to-online recovery time.

### 4.4 Detection latency (logic analyser)

Put one probe on the PIR OUT pin and one on the buzzer pin. Trigger the PIR and measure the
time from the confirmed PIR edge to the entry-delay beep starting. Expected from the design:
the 150 ms confirmation window plus the ~2 ms loop period. Repeat 20 times; report the median.

### 4.5 Deauth resilience (manual, your own network only)

On a Wi-Fi network you own, with permission, run a deauthentication flood against the device's
MAC using a standard 802.11 testing tool. Confirm that (a) the device emits `wifi_deauth` and
`link_lost`, (b) the local siren still responds to a sensor trigger during the flood, and
(c) the ESP-NOW receiver still shows the alert. Do not run this against any network you do not
own. Record the detection time and whether the local alarm was affected.

### 4.6 Energy and build cost

Report the flash and RAM from CI (already measured): see the README build-size table. For
energy, measure the average current in `ARMED` with a USB power meter, and the extra current
while TLS is connecting, to quantify the cost of the security features.

### 4.7 Results table (fill in on hardware)

| Metric | Expected | Measured |
|---|---|---|
| Command-authentication checks (tool 4.2) | all PASS | |
| Command latency, median | | |
| Reconnect time after outage | within WIFI_RETRY + MQTT_RETRY | |
| Detection latency, median | ~150 ms + loop period | |
| `wifi_deauth` raised under flood | yes | |
| Local alarm works during flood | yes | |
| ESP-NOW alert delivered during flood | yes | |
| Average current, ARMED | | |

## 5. Comparison with current work (2026)

The project is positioned against recent work rather than older references:

- MQTT-over-TLS overhead on the ESP32 has already been measured in the literature (latency
  rising roughly 14% on an ESP32-C3), so simply adding TLS is treated as a deployment step,
  not a contribution. The contribution here is the end-to-end, measured resilience of a
  *safety-critical alarm* under combined attacks, with availability as the headline metric.
- On-device ML intrusion detection for the ESP32 exists (decision-tree/NN on collected
  traffic). This project instead hardens the application-layer command path and the
  availability of the alarm itself, and verifies the state machine formally - a complementary,
  lighter-weight angle suited to a single always-on node.

A full literature search should be completed before claiming novelty in any write-up; the
references above are a starting point, not a survey.
