# Research Plan

This document states the research question, the gap it fills, the claims, and what evidence
supports each claim. It is the basis for the paper draft in `paper/`.

## 1. Motivation

Consumer smart-home security devices are overwhelmingly built on **single-chip Wi-Fi SoCs**
(ESP32/ESP8266 class), where the radio stack, the network protocol stack and the application
all run on the same silicon and under the same scheduler. This is different from the
industrial devices studied in the real-time security literature, where the control task runs
on a physically separate core or co-processor.

For an intrusion alarm, the property that matters most is not confidentiality but
**availability of the safety function**: when an intruder is detected, the siren must sound
within a bounded time, *including while the device itself is under attack*.

## 2. Gap in the literature

| Prior work | What it establishes | What it leaves open |
|---|---|---|
| Fischer et al., *Analysis of Industrial Device Architectures for Real-Time Operations under DoS* (2020) | On Linux-class industrial devices, pinning the control task to a separate core keeps 1 ms cycle jitter near zero under **wired** SYN/ARP floods; a separate Cortex-M4 co-processor is the only architecture acceptable for hard real-time | Does not cover single-chip Wi-Fi SoCs, where the attacked radio driver shares the chip; does not use **radio-layer** attacks |
| Carbajal and Akbarfam, *A Software-Defined Testbed for Quantifying Deauthentication Resilience in Modern Wi-Fi Networks* (2026) | Measures **network-layer** resilience (disconnection rate, time-to-disruption) across WPA/PMF/WPA3 configurations | Measures whether the link drops, not whether the device's **application safety function** still meets its deadline |
| MQTT-over-TLS overhead on ESP32 (2026) | Latency and packet-size cost of TLS on an ESP32-C3 | Transport cost only; no attack conditions, no safety-function timing |
| On-device ML IDS for ESP32 (2026) | A classifier can run on the device and detect DoS/MitM with high accuracy | Detection accuracy, not continuity of the protected function under attack |
| FreeRTOS performance studies on ESP32 multi-core | Baseline scheduling and IPC performance | Benign conditions only |

**The open question.** On a single-chip Wi-Fi SoC, does pinning the safety function to the
application core actually isolate it from an attack on the device's own radio? The attack
loads the on-chip Wi-Fi driver and its interrupt handlers, a coupling path that does not exist
in the wired, physically-separated architectures already studied.

## 3. Research question and hypothesis

> **RQ.** On a dual-core Wi-Fi SoC, is the sensor-to-siren latency of a safety function pinned
> to the application core invariant to attacks directed at the device's own radio and command
> interface?

- **H1 (isolation holds).** The latency distribution under attack is statistically
  indistinguishable from baseline.
- **H0 (isolation leaks).** Attack conditions inflate latency or its tail.

Either outcome is a result. A measured leak would be the more consequential finding, because
core pinning is the standard advice for this platform.

## 4. Claims and supporting evidence

| # | Claim | Evidence | Status |
|---|---|---|---|
| C1 | The architecture admits no control path by which network input can block or alter the safety path | TLA+ model + TLC exhaustive check of the isolation property | **done** (`formal/`) |
| C2 | The command interface cannot be driven into an unsafe state by a malicious peer | Exhaustive/randomized adversarial campaigns and fuzzing of the real firmware logic | **done** (`experiments/`) |
| C3 | Command authentication resists forgery and replay, including across reboot | Known-answer crypto tests + SIL scenarios + hardware tool | SIL done; hardware pending |
| C4 | Radio attacks on the device are detected and escalated out-of-band | SIL scenarios for detector and signed fallback alerts | SIL done; hardware pending |
| C5 | **Sensor-to-siren latency is invariant under radio-layer attack** | Hardware measurement under four conditions | **pending hardware** |
| C6 | The security mechanisms cost little | Flash/RAM from CI; latency overhead on hardware | partly done |

C5 is the paper's headline and is the one experiment that cannot be simulated: it is a
property of the silicon and the radio driver, not of the logic. The apparatus for it is in
`experiments/hardware/`.

## 5. Threats to validity

- **Construct.** SIL campaigns establish *logical* invariance only; they cannot show physical
  timing invariance. This is why C5 is measured on hardware and is reported separately.
- **Internal.** Attack intensity must be controlled and recorded; latency must be measured
  with an external logic analyser, not by the device's own clock, to avoid the measurement
  sharing the resource under contention.
- **External.** Results are for one SoC family and one firmware. Generalisation to other
  single-chip Wi-Fi SoCs is a stated limitation.
- **Ethical.** Radio-layer experiments are conducted only in a shielded/own-network setting
  with permission; no third-party network is attacked.

## 6. Status

Formal and simulation evidence is complete and reproducible. The hardware campaign (C5, and
hardware confirmation of C3, C4, C6) is specified in `experiments/hardware/` and must be run
before submission.
