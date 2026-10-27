# Implementation and experimental record

The complete technical record of this project: what was built, how it works, how it was
evaluated, what the results are, and what has **not** been done. It is written so that another
researcher can read it, run it, and reproduce every number in the paper.

Every figure, table and claim below was taken from a file in this repository or from a command
re-run while writing this document. Where something is unknown, unmeasured or not applicable, it
says so explicitly rather than filling the gap.

**Document status:** corresponds to firmware v2.2.0, commit history through `da8d9b8`.

---

## Table of contents

1. [Scope, and an honest status table](#1-scope-and-an-honest-status-table)
2. [Research framing: prior methodology vs this implementation](#2-research-framing-prior-methodology-vs-this-implementation)
3. [Repository structure](#3-repository-structure)
4. [System architecture](#4-system-architecture)
5. [Algorithms, mathematical formulations and pseudocode](#5-algorithms-mathematical-formulations-and-pseudocode)
6. [Configuration parameters](#6-configuration-parameters)
7. [Hardware and software environment](#7-hardware-and-software-environment)
8. [Data: what plays the role of a dataset](#8-data-what-plays-the-role-of-a-dataset)
9. [Build, test, run and reproduce](#9-build-test-run-and-reproduce)
10. [Experimental design](#10-experimental-design)
11. [Results](#11-results)
12. [Formal verification results](#12-formal-verification-results)
13. [Comparison: prior work vs this implementation](#13-comparison-prior-work-vs-this-implementation)
14. [Before-and-after: evolution across versions](#14-before-and-after-evolution-across-versions)
15. [Debugging fixes and optimisations](#15-debugging-fixes-and-optimisations)
16. [Validation performed, and errors encountered](#16-validation-performed-and-errors-encountered)
17. [Limitations, reproducibility gaps and unverified items](#17-limitations-reproducibility-gaps-and-unverified-items)
18. [References](#18-references)

---

## 1. Scope, and an honest status table

### 1.1 What this project is

An ESP32 intrusion alarm, hardened and formally verified, used as the object of study for one
research question:

> On a single-chip Wi-Fi SoC, where the attacked radio driver shares the die, the RTOS scheduler
> and the interrupt controller with the safety task, does pinning the safety task to its own core
> actually isolate it?

### 1.2 What is complete, and what is not

This table is the most important one in the document. Nothing elsewhere contradicts it.

| Area | Status | Evidence |
|---|---|---|
| Firmware (v2.2.0, dual-core, hardened) | **Complete** | `firmware/smart_home/` (1,099 lines), compiles in CI for two arduino-esp32 versions |
| ESP-NOW receiver firmware | **Complete** | `firmware/espnow_receiver/`, compiles in CI |
| Host test suite | **Complete** | `tests/host/`, 19 scenarios, 120 checks, passing |
| Formal verification (TLA+) | **Complete** | `formal/`, 2 models, TLC-checked in CI, mutation-tested |
| Adversarial simulation campaign | **Complete** | `experiments/campaign.cpp`, 6,000 trials, results committed |
| Command-parser fuzzing | **Complete** | `experiments/fuzz_cmd.cpp`, 3,000,000 iterations, results committed |
| Statistical analysis and figure | **Complete** | `experiments/analyse.py`, `make_figures.py`, outputs committed |
| Paper draft | **Complete (draft)** | `paper/paper.tex`, 4 pages, compiles, 14 verified references |
| Literature survey | **Complete** | `docs/RELATED_WORK.md`, 14 works, each verified against publisher records |
| **Hardware measurement campaign** | **NOT DONE** | Apparatus and protocol exist (`experiments/hardware/`); no board has been run |
| **Physical latency / timing results** | **NOT DONE** | No measured latency number exists anywhere in this repository |
| **Deployment / field trial** | **NOT DONE** | Never deployed; no field data |

### 1.3 Categories that do not apply to this project

The following are standard in machine-learning papers and are **not applicable here**. They are
listed so their absence is understood as deliberate, not as an omission:

| Category | Status | Why |
|---|---|---|
| Dataset / training data | **Not applicable** | No learned model. See [Section 8](#8-data-what-plays-the-role-of-a-dataset) for what takes its place |
| Data preprocessing pipeline | **Not applicable** | No dataset to preprocess |
| Model architecture / weights | **Not applicable** | No model |
| Hyperparameters, training procedure, loss curves | **Not applicable** | Nothing is trained. The nearest analogue is the compile-time configuration in [Section 6](#6-configuration-parameters) |
| Inference workflow | **Not applicable** | The runtime equivalent is the firmware control loop, documented in [Section 4](#4-system-architecture) |
| Jupyter notebooks | **None exist** | Analysis is in plain, version-controlled Python scripts instead, which are easier to run in CI |
| GPU / accelerator requirements | **Not applicable** | Target is a 240 MHz microcontroller |

### 1.4 This is original work, not a paper reproduction

This repository does **not** reimplement a published paper. It is original research positioned
against prior work. Where this document refers to "the original methodology", it means the
methodology of the closest prior work (Fischer et al., 2020), which this project adapts to a
different device class. That comparison is in [Section 13](#13-comparison-prior-work-vs-this-implementation).

---

## 2. Research framing: prior methodology vs this implementation

### 2.1 The closest prior methodology (Fischer et al., 2020)

| Element | Their approach |
|---|---|
| Object of study | Industrial control devices, Linux-class |
| Independent variable | Network DoS load (wired SYN flood, ARP flood) |
| Dependent variable | Control-task cycle jitter against a 1 ms period |
| Architectures compared | Single-core, multi-core with the control task pinned, separate Cortex-M4 co-processor |
| Finding | Pinning holds jitter near-constant; only a separate co-processor is acceptable for hard real-time |
| Structural property | **The attacked network interface is physically separate from the protected core** |

### 2.2 This implementation

| Element | This approach | Difference, and why it matters |
|---|---|---|
| Object of study | ESP32 intrusion alarm (single-chip Wi-Fi SoC) | The Wi-Fi driver, TCP/IP stack, MQTT client and application share one die, one scheduler, one interrupt controller |
| Independent variable | Attack load on the device's own command interface and radio | The attacked resource is **on-die**. This coupling path does not exist in their setup |
| Dependent variable | Sensor-to-siren latency of the safety function | An application-level safety deadline, not a control-loop period |
| Architectures compared | Unhardened baseline vs hardened v2.2 firmware | Plus a formal model of the isolation argument itself |
| Methods | Formal (TLA+/TLC) + simulation (seeded campaign, fuzzing) + hardware protocol | They used hardware measurement only |
| Status | Logical isolation established; timing isolation **open** | Honestly bounded; see [Section 1.2](#12-what-is-complete-and-what-is-not) |

### 2.3 Research contributions claimed

1. An open, hardened dual-core alarm firmware with authenticated commands, replay protection,
   passive deauth detection, a signed out-of-band fallback channel and optional sensor fusion.
2. Two TLA+ specifications checked exhaustively by TLC, the second formalising the
   safety/network **isolation argument** under an unfair, maximally adversarial network task,
   both mutation-tested.
3. A seeded, reproducible adversarial campaign and a sanitizer-backed fuzzing campaign with a
   non-parametric analysis.
4. A measurement protocol and instrumentation for the one claim that requires silicon, stated
   openly as the open step rather than estimated.

**Not claimed:** any physical timing result; any deployment result; novelty in fuzzing technique;
novelty in cryptographic construction (standard HMAC-SHA256 is used as specified).

---

## 3. Repository structure

```
.
├── firmware/
│   ├── smart_home/              Main alarm firmware (ESP32, Arduino framework)
│   │   ├── smart_home.ino       1099 L  Entry point: config, FSM, dual-core tasks, MQTT
│   │   ├── authmac.h             132 L  SHA-256 + HMAC-SHA256, constant-time compare, hex decode
│   │   ├── wifi_guard.h           61 L  Deauth/disassoc flood detector (sliding window)
│   │   ├── alertmsg.h             78 L  Packed, HMAC-tagged ESP-NOW alert message
│   │   ├── sensor_fusion.h        58 L  PIR + mmWave fusion (PIR_ONLY / OR / AND)
│   │   └── secrets.example.h      43 L  Template for credentials (real secrets.h is git-ignored)
│   └── espnow_receiver/           80 L  Second-board receiver for fallback alerts
│
├── formal/                      TLA+ specifications, model-checked by TLC
│   ├── AlarmFSM.tla   / .cfg     129 L  State machine + authenticated command path
│   ├── Isolation.tla  / .cfg     143 L  Safety/network isolation under an adversarial network
│   └── run_tlc.sh                 25 L  Fetches pinned tla2tools v1.8.0, checks both models
│
├── experiments/                 Simulation, fuzzing and analysis
│   ├── campaign.cpp              289 L  Seeded adversarial campaign against the real firmware logic
│   ├── fuzz_cmd.cpp              173 L  Command-parser fuzzer (ASan + UBSan)
│   ├── analyse.py                172 L  Aggregation + Mann-Whitney U (no SciPy dependency)
│   ├── make_figures.py            91 L  Campaign figure, colourblind- and greyscale-safe
│   ├── run.sh                     32 L  Whole pipeline end to end
│   ├── results/                         Committed outputs (summary.md/json, fuzz.json, figures)
│   └── hardware/                        Apparatus for the OPEN hardware step
│       ├── README.md              67 L  Measurement protocol and conditions
│       ├── latency_probe/         53 L  Independent measuring board firmware
│       ├── collect.py             65 L  Serial collection
│       └── analyse_hw.py         104 L  Same statistical test applied to hardware data
│
├── tests/host/                  Software-in-the-loop test suite
│   ├── test_firmware.cpp         461 L  19 scenarios
│   ├── run_tests.sh               58 L  Builds and runs across clock starts and core APIs
│   └── stubs/                           Host models of Arduino, FreeRTOS, WiFi, MQTT, NVS, OLED
│
├── tools/                       Operator and hardware-evaluation utilities
│   ├── sign_command.py            61 L  Signs a command for the authenticated path
│   ├── eval_commands.py          125 L  Verifies forgery/replay rejection on real hardware
│   └── measure.py                122 L  Command latency and reconnect-time measurement
│
├── paper/                       Research write-up
│   ├── paper.tex                 334 L  4-page two-column draft (ports to IEEEtran)
│   └── supervisor_brief.tex      100 L  One-page brief
│
├── docs/                        Documentation
│   ├── IMPLEMENTATION.md                This document
│   ├── RESEARCH.md                      Research question, hypotheses, claims
│   ├── RELATED_WORK.md                  14-work verified survey and positioning
│   ├── THREAT_MODEL.md                  Assets, adversaries, 12 threats, mitigations
│   ├── EVALUATION.md                    Evaluation method and results
│   ├── HARDENING.md                     Deployment guide
│   └── images/                          Architecture, state machine, sequence, wiring diagrams
│
├── wokwi/                       Simulator circuit (diagram.json, libraries.txt)
└── .github/workflows/ci.yml     5-job CI pipeline
```

---

## 4. System architecture

### 4.1 Dual-core structure

This is the architectural claim the research question is about.

```
            ESP32 (Xtensa LX6, dual core, 240 MHz)
  ┌──────────────────────────────┬──────────────────────────────┐
  │  Core 1  (APP_CPU)           │  Core 0  (PRO_CPU)           │
  │  ── SAFETY DOMAIN ──         │  ── NETWORK DOMAIN ──        │
  │                              │                              │
  │  Arduino loop():             │  netTask (pinned):           │
  │   • debounce door / button   │   • Wi-Fi connect + retry    │
  │   • PIR warm-up + 150 ms     │   • NTP time sync            │
  │     confirmation filter      │   • MQTT connect, Last Will  │
  │   • sensor fusion (optional) │   • publish events / state   │
  │   • 5-state alarm FSM        │   • receive commands         │
  │   • siren, LEDs, OLED        │   • HMAC verification        │
  │   • task watchdog kick       │   • deauth monitor callback  │
  │                              │   • ESP-NOW fallback send    │
  └───────────┬──────────────────┴───────────┬──────────────────┘
              │                              │
              │   eventQ  (depth 16, FIFO)   │   safety → network
              │   ─────────────────────────▶ │
              │                              │
              │   cmdQ    (depth 4)          │   network → safety
              │   ◀───────────────────────── │
              │                              │
              │   statusMutex — ASYMMETRIC timeouts:         │
              │     safety loop  : xSemaphoreTake(…, 0)      │  never waits
              │     network task : xSemaphoreTake(…, 10 ms)  │  may wait
```

The **asymmetry of the mutex timeout is the isolation mechanism**, and it is easy to miss. The
safety loop takes the status mutex with a zero timeout and simply skips the update if the
network task holds it; the network task is allowed to wait up to 10 ms. Priority inversion can
therefore delay the network side, never the safety side.

**The three isolation mechanisms, and what each guarantees:**

| Mechanism | Guarantee | Enforced where |
|---|---|---|
| Core pinning | The network task cannot occupy the safety core's execution slot | `xTaskCreatePinnedToCore(networkTask, "net", 8192, nullptr, 1, nullptr, 0)` — 8 KB stack, priority 1, **core 0**; the Arduino `loop()` runs on core 1 |
| Bounded queues | Neither side can grow the other's memory or block it. On a full event queue the oldest is **dropped and counted**, never silently lost | `eventQ = xQueueCreate(16, sizeof(Event))`, `cmdQ = xQueueCreate(4, sizeof(CmdMsg))` |
| Zero-timeout mutex | The safety loop **never waits** for the network task to release the status snapshot | `xSemaphoreTake(statusMutex, 0)` in the safety loop vs `pdMS_TO_TICKS(10)` in the network task |

**The property proved formally** (`formal/Isolation.tla`): the safety step remains enabled
regardless of what the network task does, including stalling forever.

### 4.2 Alarm state machine

Five states. Transitions on sensor input, button, remote command and timeout.

```
                   ARM (button or authenticated command)
       ┌──────────┐ ─────────────────────────▶ ┌────────────┐
       │ DISARMED │                            │ EXIT_DELAY │
       └──────────┘ ◀───────────────────────── └────────────┘
            ▲  ▲          DISARM                      │ 10 s elapsed
            │  │                                      ▼
            │  │                               ┌────────────┐
            │  └─────────── DISARM ────────────│   ARMED    │
            │                                  └────────────┘
            │                                         │ PIR confirmed
            │                                         │ or door opened
            │                                         ▼
            │                                  ┌─────────────┐
            ├─────────────── DISARM ───────────│ ENTRY_DELAY │
            │                                  └─────────────┘
            │                                         │ 10 s elapsed
            │                                         ▼
            │                                  ┌────────────┐
            └─────────────── DISARM ───────────│   ALARM    │
                                               └────────────┘
                                                      │ 30 s elapsed
                                                      └──▶ back to ARMED
```

Rendered diagrams: `docs/images/state_machine.svg`, `architecture.svg`, `event_sequence.svg`,
`circuit_wiring.svg` (PNG versions alongside).

### 4.3 Defence-in-depth layers

| Layer | Defends against | Fails safe how |
|---|---|---|
| Local siren, no network dependency | Any network attack | Siren is driven entirely from core 1 |
| HMAC-SHA256 command authentication | Forged commands (T1) | Unverified command rejected, `cmd_badmac` emitted |
| NVS-persisted monotonic counter | Replay, including across reboot (T2) | Stale counter rejected, `cmd_replay` emitted |
| Passive deauth detector | Radio-layer DoS (T4) | `wifi_deauth` event; alarm continues offline |
| MQTT Last Will + heartbeat | Silent disconnection (T5) | Consumer treats silence as an alarm |
| ESP-NOW signed fallback | MQTT unreachable (T4/T8) | Out-of-band alert to a second board |
| NVS armed-state restore | Power cut while armed (T7) | Re-arms on boot; open door starts entry delay |
| Task watchdog | Firmware hang (T9) | Reset, with reset reason reported in the boot event |
| PIR + mmWave fusion (optional) | Sensor blinding / false alarms (T12) | AND mode requires corroboration |

---

## 5. Algorithms, mathematical formulations and pseudocode

### 5.1 Authenticated command verification

**Wire format.** `<VERB>:<counter>:<hex-tag>` where `VERB ∈ {ARM, ARM_AWAY, DISARM, STATUS}`.

**Tag computation.** With shared key `K`, message `m = "VERB:counter"`:

```
HMAC(K, m) = H( (K' ⊕ opad) ‖ H( (K' ⊕ ipad) ‖ m ) )
```

where `H` = SHA-256, block size `B` = 64 bytes, `ipad` = 0x36 repeated `B` times,
`opad` = 0x5C repeated `B` times, and

```
K' = H(K)            if |K| > B
   = K ‖ 0^(B−|K|)   otherwise
```

This is RFC 2104 / FIPS 198-1 exactly. The transmitted tag is the first
`AUTH_TAG_BYTES = 16` octets (128 bits) of the 32-byte output — truncation as permitted by
RFC 2104 §5, chosen so the tag fits an MQTT payload comfortably while leaving a forgery
probability of 2⁻¹²⁸ per attempt.

**Verification predicate.** A command is accepted iff

```
    ct_equal( trunc₁₆(HMAC(K, m)), tag )   ∧   counter > counter_stored
```

Both conjuncts are necessary: the first defeats forgery (no key, no tag), the second defeats
replay (a captured valid message has a counter that is no longer strictly greater).

**Constant-time comparison.** To avoid leaking the tag through timing, comparison accumulates a
difference instead of returning early:

```c
// authmac.h
bool ct_equal(const uint8_t* a, const uint8_t* b, size_t n) {
    uint8_t d = 0;
    for (size_t i = 0; i < n; i++) d |= (uint8_t)(a[i] ^ b[i]);
    return d == 0;
}
```

**Pseudocode, showing which core runs what.** This split matters: parsing and the expensive
HMAC run on the network core, so a command flood costs the safety core nothing.

```
── CORE 0 (network task) ────────────────────────────────────
on mqtt_message(topic, payload):
    if topic != cmd_topic: return
    (verb, ctr, tag)  ← parse(payload)            # malformed → drop, no event
    authed            ← verify_hmac(verb, ctr, tag)
    if AUTH_COMMANDS and not authed:
        emit("cmd_unauth"); return
    xQueueSend(cmdQueue, {verb, authed, ctr})     # bounded, depth 4

── CORE 1 (safety loop) ─────────────────────────────────────
if xQueueReceive(cmdQueue, &m, 0):                # zero timeout: never blocks
    if m.authed:
        if m.ctr <= cmdCounter:                   # replay check
            emit("cmd_replay"); continue
        persistCounter(m.ctr)                     # NVS write, survives reboot
    switch m.cmd:
        ARM:     if state == DISARMED: startExitDelay()
        DISARM:  if m.authed or ALLOW_REMOTE_DISARM: disarm()
                 else: emit("cmd_rejected")
        STATUS:  publishState()
```

The `DISARM` authorisation is decided **at runtime**, not at compile time: a validly signed
command is trusted even when the compile-time `ALLOW_REMOTE_DISARM` flag is off, because the tag
and counter already provide the guarantee that flag exists to protect.

### 5.2 Deauthentication flood detection

A sliding-window counter over 802.11 management frames of subtype deauth (0x0C) or disassoc
(0x0A), observed passively in promiscuous mode. The detector never transmits.

Let `W = DEAUTH_WINDOW_MS = 2000 ms`, `T = DEAUTH_THRESHOLD = 8`,
`C = DEAUTH_COOLDOWN_MS = 10000 ms`, and `N(t)` the number of such frames in `(t−W, t]`.
An event is raised at time `t` iff

```
    N(t) ≥ T   ∧   t − t_last_report > C
```

The cooldown bounds report rate at one per 10 s, so the detector cannot itself become an event
flood — a denial-of-service against the event queue via the detector.

```c
// wifi_guard.h — pure logic, no radio dependency, therefore host-testable
bool DeauthDetector::observe(uint32_t now) {
    if (now - windowStart > windowMs) { windowStart = now; count = 0; }
    if (++count < threshold) return false;
    if (now - lastReport <= cooldownMs) return false;
    lastReport = now; count = 0;
    return true;                       // caller emits "wifi_deauth"
}
```

### 5.3 Sensor fusion

Three modes. Let `t_p` and `t_r` be the most recent PIR and radar assertion times and
`W_f = FUSION_WINDOW_MS = 1500 ms`.

| Mode | Fires iff | Effect |
|---|---|---|
| `FUSION_PIR_ONLY` | PIR asserted | Default; behaviour unchanged from v2.1 |
| `FUSION_OR` | PIR ∨ radar asserted | Maximum sensitivity |
| `FUSION_AND` | `|t_p − t_r| ≤ W_f` | Both must agree within the window; suppresses lone PIR triggers from heat or sunlight |

**Seeding, and the bug it fixes.** With `t_p` and `t_r` initialised to 0, early timestamps
compare as "recent" and AND mode fires spuriously at start-up. They are therefore seeded one
window in the past on first use:

```c
if (!f.seeded) {
    f.lastPir = f.lastRadar = now - f.windowMs - 1;   // definitively stale
    f.seeded  = true;
}
```

Covered by the `fusion` test scenario.

### 5.4 Wrap-safe time arithmetic

`millis()` is a `uint32_t` and wraps after ≈49.7 days. Every comparison in the firmware is of
the form

```c
(uint32_t)(now - since) >= interval          // correct across the wrap
```

never `now >= since + interval`, which breaks at the boundary. The test suite runs **every
scenario at three clock start values**, one of them just below the wrap point, so the property
is exercised rather than asserted. A real defect of this class was found this way in v2.0 (see
[Section 15](#15-debugging-fixes-and-optimisations)).

### 5.5 Mann-Whitney U test

Used to compare the safety-latency distribution under attack against the no-attack control.
Chosen because it is non-parametric — latency distributions on an RTOS are not normal, and a
t-test would assume what cannot be assumed. Implemented from scratch in `analyse.py` to keep the
artifact dependency-free (no SciPy).

For samples of size `n₁`, `n₂` with `R₁` the rank sum of the first sample:

```
U₁ = R₁ − n₁(n₁+1)/2 ,     U₂ = n₁n₂ − U₁ ,     U = min(U₁, U₂)
μ_U = n₁n₂/2
σ²_U = (n₁n₂/12) · [ (n+1) − Σ(tᵢ³ − tᵢ) / (n(n−1)) ]        n = n₁+n₂
z = (U − μ_U)/σ_U ,        p = erfc(|z|/√2)                  (two-sided)
```

The bracketed term is the **tie correction**, which matters here: simulated latencies are
heavily tied. When `σ²_U ≤ 0` (all values identical) the implementation returns `p = 1.0`
rather than dividing by zero, and the surrounding documentation states plainly that this makes
the test trivially satisfied in simulation — see [Section 11.4](#114-the-statistical-test-and-its-caveat).

---

## 6. Configuration parameters

These compile-time constants are the nearest analogue to hyperparameters. All are in
`firmware/smart_home/smart_home.ino` unless noted. Values are those actually in the committed
source.

### 6.1 Pin assignment

| Constant | Pin | Function |
|---|---|---|
| `PIN_PIR` | 13 | PIR OUT (input) |
| `PIN_RADAR` | 33 | mmWave radar presence OUT (input, used when fusion enabled) |
| `PIN_BUZZER` | 23 | Buzzer + (output) |
| `PIN_DOOR` | 14 | Door switch to GND (input pull-up; HIGH = open) |
| `PIN_ARM_BTN` | 27 | Arm/disarm button to GND (input pull-up) |
| `PIN_LED_ARMED` | 26 | Green LED (output) |
| `PIN_LED_ALARM` | 25 | Red LED (output) |
| `PIN_SDA` / `PIN_SCL` | 21 / 22 | OLED I²C |

### 6.2 Timing

| Constant | Value | Rationale |
|---|---|---|
| `EXIT_DELAY_MS` | 10,000 | Time to leave after arming |
| `ENTRY_DELAY_MS` | 10,000 | Time to disarm after a trigger |
| `ALARM_DURATION_MS` | 30,000 | Siren length, then re-arm |
| `PIR_WARMUP_MS` | 10,000 | Suits the simulator; **use 60,000 for a real HC-SR501** |
| `PIR_CONFIRM_MS` | 150 | PIR must stay HIGH this long — the main false-alarm filter |
| `DEBOUNCE_MS` | 40 | Mechanical switch debounce |
| `OLED_REFRESH_MS` | 250 | Display refresh |
| `STATUS_COPY_MS` | 500 | Safety → network snapshot rate |
| `HEARTBEAT_MS` | 30,000 | MQTT heartbeat |
| `WIFI_RETRY_MS` | 15,000 | Wi-Fi reconnect interval |
| `MQTT_RETRY_MS` | 5,000 | MQTT reconnect interval |

### 6.3 Security

| Constant | Default | Meaning |
|---|---|---|
| `AUTH_COMMANDS` | 0 | 1 = require signed commands. **The hardened configuration** |
| `AUTH_TAG_BYTES` | 16 | Truncated HMAC tag length (128-bit) |
| `ALLOW_REMOTE_DISARM` | 0 | Compile-time permission; a signed command bypasses it at runtime |
| `SECRET_CMD_KEY` | demo value | **Public demo key — must be overridden in `secrets.h`** |
| `MQTT_USE_TLS` | 0 | 1 = TLS on port 8883; requires `SECRET_MQTT_CA_CERT` |
| `ENABLE_WIFI_GUARD` | 1 | Passive deauth monitoring (ESP32 only) |
| `DEAUTH_WINDOW_MS` | 2,000 | Detector observation window |
| `DEAUTH_THRESHOLD` | 8 | Frames in the window that signal a flood |
| `DEAUTH_COOLDOWN_MS` | 10,000 | At most one report per 10 s |
| `ENABLE_ESPNOW` | 0 | Signed out-of-band fallback alerts |
| `FUSION_MODE` | `FUSION_PIR_ONLY` | `FUSION_OR` / `FUSION_AND` available |
| `FUSION_WINDOW_MS` | 1,500 | Agreement window for AND mode |
| `RESTORE_ARMED_ON_BOOT` | 1 | Re-arm from NVS after power cut |
| `ENABLE_LOOP_WDT` | 1 | Task watchdog on the safety loop |

A compile-time guard enforces the security invariant that remote disarm cannot be enabled
carelessly:

```c
#if ALLOW_REMOTE_DISARM && !AUTH_COMMANDS && (!MQTT_USE_TLS || !MQTT_HAS_LOGIN)
#  error "ALLOW_REMOTE_DISARM needs AUTH_COMMANDS 1, or MQTT_USE_TLS 1 with broker credentials"
#endif
```

### 6.4 Experiment parameters

| Parameter | Value | Where |
|---|---|---|
| Campaign trials per build | 3,000 (6,000 total) | `run.sh`, `TRIALS` |
| Campaign base seed | 1,000 | `run.sh` |
| Attack rates | 0, 10, 100, 1,000, 5,000, 20,000 msg/s | `campaign.cpp` |
| Trials per rate | 500 | derived: 3,000 / 6 rates |
| Fuzz iterations | 3,000,000 | `run.sh`, `FUZZ_ITERS` |
| Fuzz seed | 7 | `run.sh` |
| CI smoke values | 300 trials, 200,000 iterations | `.github/workflows/ci.yml` |
| TLC `MaxCtr` (AlarmFSM) | 4 | `AlarmFSM.cfg` |
| TLC `QCap` (Isolation) | event queue capacity | `Isolation.cfg` |

---

## 7. Hardware and software environment

### 7.1 Target hardware (specification, **not** measured)

No physical board has been run in this project. The following is the target specification taken
from the device datasheet and the build configuration, not from measurement.

| Item | Specification |
|---|---|
| MCU | ESP32 (Xtensa LX6, dual core, up to 240 MHz) |
| Board / FQBN | ESP32 DevKit, `esp32:esp32:esp32` |
| Flash budget | 1,310,720 B (app partition, as reported by the compiler) |
| RAM budget | 327,680 B (globals, as reported by the compiler) |
| Sensors | PIR (HC-SR501), optional LD2410 mmWave radar, door reed switch |
| Outputs | Passive piezo buzzer (2.7 kHz tone), 2 LEDs, SSD1306 OLED (I²C) |
| Fallback node | A second ESP32 running `firmware/espnow_receiver` |

### 7.2 Measured build cost (from CI, real compiler output)

This **is** measured — by the compiler in CI, not estimated.

| arduino-esp32 | Flash | RAM (globals) |
|---|---|---|
| 2.0.17 | 793,433 B (60.5 % of 1,310,720) | 46,372 B (14.2 % of 327,680) |
| 3.3.12 | 968,221 B (73.9 % of 1,310,720) | 49,876 B (15.2 % of 327,680) |

The v2.2 security features add approximately **3 KB of flash and 170 B of RAM** over v2.1.

### 7.3 Software environment used for the committed results

Captured from the machine that produced the committed outputs.

| Component | Version |
|---|---|
| OS kernel | Linux 6.18.44 |
| g++ | 13 |
| Python | 3.13.16 |
| OpenJDK (for TLC) | 21.0.12.1 |
| TLA+ tools | tla2tools v1.8.0 (pinned in `run_tlc.sh`) |
| pdfTeX | 3.141592653-2.6-1.40.25 (TeX Live 2023/Debian) |

CI environment: `ubuntu-24.04`, Temurin JDK 17, `arduino/compile-sketches@v1`.

> Note: CI uses JDK 17 and the local runs used JDK 21. TLC results were identical on both
> (660 distinct states for `Isolation`), so the discrepancy is recorded rather than hidden.

### 7.4 Software dependencies

**Arduino libraries** (also listed in `wokwi/libraries.txt`): Adafruit SSD1306, Adafruit GFX
Library, PubSubClient.

**Python** (`requirements.txt`): `paho-mqtt` (hardware evaluation tools), `matplotlib`
(figures), `pyserial` (hardware collection). The analysis script `analyse.py` deliberately uses
**only the standard library**, so the statistical results reproduce with no third-party package
at all.

**Build tools:** g++ ≥ 11 with C++17, Java ≥ 11 for TLC, `arduino-cli` (or the Arduino IDE) for
firmware, and a LaTeX distribution for the paper.

---

## 8. Data: what plays the role of a dataset

There is **no dataset** in this project. Nothing is collected, labelled, split or preprocessed.
What takes its place is **deterministic generation from fixed seeds**, which is stronger for this
purpose: the inputs are regenerated identically on every run instead of being distributed as a
file.

### 8.1 Campaign input generation

Each trial `k` is seeded `seed₀ + k` with `seed₀ = 1000`. From that seed the harness derives:

- the arrival times of attacker messages at the configured rate;
- the content of each attacker message (forged tag, replayed capture, or malformed);
- the timing of the legitimate command and of the sensor trigger.

The scheduler supports rates above 1,000 msg/s by splitting into a per-millisecond quota plus a
remainder, so a 20,000 msg/s burst is represented exactly:

```c
uint32_t perTick   = attackRate / 1000u;
uint32_t remainder = attackRate % 1000u;
```

### 8.2 Process isolation between trials

Firmware globals (`state`, counters, queues) are file-scope and would otherwise leak between
trials run in one process. Each trial therefore runs in a forked child with pristine globals:

```c
fflush(stdout);
pid_t pid = fork();
if (pid == 0) { Trial t = runTrial(seed0 + k, rate); printf(...); _exit(0); }
```

This was not a design nicety — it fixed a real false result. See
[Section 15](#15-debugging-fixes-and-optimisations).

### 8.3 Fuzzer corpus generation

The fuzzer cycles through **6 input classes** (`it % 6`), seeded from 7:

| Class | Input |
|---|---|
| 0 | Pure random bytes (100 B) |
| 1 | Structurally valid shape signed with the **wrong key** |
| 2 | Valid shape with a **random tag** |
| 3 | **Bit-flip mutation** (1–3 flips) of a genuine signed message |
| 4 | **Truncations and extensions** of a genuine message |
| 5 | **Colon soup and embedded NULs** |

Classes 1–3 count as well-formed *shapes*: 3 of 6 classes, giving the 1,500,000 of 3,000,000
reported in `fuzz.json`. This matters because it means half the iterations reach the parser's
deeper logic instead of being rejected at the first character.

The counter field is drawn from a corpus of deliberate edge cases:
`0`, `1`, `999999`, `4294967295` (UINT32_MAX), `4294967296` (overflow by one),
`99999999999999999999`, `-1`, `+1`, `0x10`, the empty string, `" 1"` and `"1 "` (leading and
trailing space), and `00000000000000000001` (leading zeros).

The mutation seed (`realMsg`) is signed with a deliberately **wrong** key,
`"attacker-key-not-the-device-key"`, so that a bit-flip cannot accidentally produce a genuinely
valid command — which it did once before this was fixed
([Section 15](#15-debugging-fixes-and-optimisations)).

### 8.4 Committed experimental outputs

| File | Content |
|---|---|
| `experiments/results/summary.md` | Human-readable per-rate tables and the hypothesis test |
| `experiments/results/summary.json` | Machine-readable aggregates (225 lines) |
| `experiments/results/fuzz.json` | Fuzzer verdict |
| `experiments/results/fig_campaign.pdf` / `.png` | Two-panel campaign figure |

Raw per-trial JSONL is git-ignored by design (it is large and regenerates identically from the
seeds); the aggregates derived from it are committed.

---

## 9. Build, test, run and reproduce

### 9.1 Install

```bash
git clone https://github.com/mdhumayun7/Smart-Home-Automation.git
cd Smart-Home-Automation
pip install -r requirements.txt          # only needed for figures and hardware tools
```

### 9.2 Run the host test suite (≈1 min, no dependencies)

```bash
./tests/host/run_tests.sh
```

Builds the unchanged firmware against host stubs and runs 19 scenarios at 3 clock start values
across 2 arduino-esp32 core APIs, plus 4 build-configuration checks and 2 header-sync checks:
**120 checks**. Compiled with `-Werror`; every MQTT payload is validated as JSON.

### 9.3 Run formal verification (≈1 min)

```bash
./formal/run_tlc.sh
```

Downloads the pinned tla2tools v1.8.0 if absent, then model-checks `AlarmFSM` and `Isolation`
against their `.cfg` files. Exits non-zero on any violation.

### 9.4 Reproduce the full experimental pipeline

```bash
cd experiments
./run.sh
```

**Runtime.** `experiments/README.md` quotes ≈5 minutes. That is optimistic on a constrained
machine: because every trial is a separate forked process ([Section 8.2](#82-process-isolation-between-trials)),
the 6,000-trial campaign is fork-bound and took substantially longer than 5 minutes on the
container used to write this document. Budget tens of minutes for the full run, or use the
reduced run below. The CI job uses `TRIALS=300`, which completes in about 3 minutes.

Builds baseline and hardened campaign binaries, runs 3,000 trials each, analyses, plots, then
builds and runs the fuzzer under AddressSanitizer and UndefinedBehaviorSanitizer. Writes
`results/summary.md`, `results/summary.json`, `results/fig_campaign.pdf` and `results/fuzz.json`.

Smaller run:

```bash
TRIALS=300 FUZZ_ITERS=200000 ./run.sh
```

Individual steps are in `experiments/README.md`.

### 9.5 Build the firmware

```bash
arduino-cli core install esp32:esp32
arduino-cli lib install "Adafruit SSD1306" "Adafruit GFX Library" "PubSubClient"
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/smart_home
arduino-cli upload  --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 firmware/smart_home
```

Hardened configuration:

```bash
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/smart_home \
  --build-property "compiler.cpp.extra_flags=-DAUTH_COMMANDS=1 -DENABLE_ESPNOW=1 -DFUSION_MODE=FUSION_AND"
```

In the simulator: create an ESP32 project at wokwi.com and copy in `firmware/smart_home/smart_home.ino`
plus `wokwi/diagram.json` and `wokwi/libraries.txt`.

### 9.6 Send an authenticated command

```bash
python3 tools/sign_command.py DISARM 1001 --key-file cmd_key.txt
```

### 9.7 Build the paper

```bash
cd paper && pdflatex paper.tex && pdflatex paper.tex
pdflatex supervisor_brief.tex
```

### 9.8 Hardware evaluation (the open step)

```bash
python3 tools/eval_commands.py --host <broker> --device <id> --key <key> --start-counter 1000
python3 tools/measure.py latency --host <broker> --device <id> [--key <key>]
python3 experiments/hardware/collect.py   # then analyse_hw.py
```

Protocol in `experiments/hardware/README.md`. **Not yet run.**

---

## 10. Experimental design

### 10.1 Hypotheses

- **H1 (isolation holds).** The sensor-to-siren latency distribution under attack is
  statistically indistinguishable from the no-attack control.
- **H0 (isolation fails).** Attack load shifts the latency distribution.

H1 has two halves. The **logical** half (no code path makes the safety response depend on
network input) is testable in simulation and formally. The **timing** half (real contention on
real silicon does not shift the distribution) requires hardware. Only the first has been done.

### 10.2 Independent and dependent variables

| | Variable | Levels / measure |
|---|---|---|
| Independent | Attack rate | 0, 10, 100, 1,000, 5,000, 20,000 msg/s |
| Independent | Build | baseline (no auth) vs hardened (`AUTH_COMMANDS=1`) |
| Dependent | Safety latency | trigger → siren, ms |
| Dependent | Security outcome | attacker armed / attacker disarmed, counts |
| Dependent | Availability | legitimate command took effect, count |
| Dependent | Correctness | safety-invariant violations, count |

### 10.3 Experimental conditions for the hardware campaign (specified, not run)

| Condition | Description | Needs isolated RF |
|---|---|---|
| A | Idle (control) | No |
| B | Legitimate network load | No |
| C | Command-interface stress | No |
| D | Radio-layer stress (deauth flood) | **Yes** |

Conditions A–C are runnable immediately with two boards and a logic probe. Condition D requires
an authorised isolated or shielded environment.

**Ethics.** No attack tooling is published in this repository, and
`experiments/hardware/README.md` deliberately omits attack-generation instructions. Condition D
is to be run only on equipment the experimenter owns, with institutional permission. This
constraint is stated in the paper's ethics section.

---

## 11. Results

All numbers below were read from the committed output files, not transcribed from memory.

### 11.1 Adversarial campaign, baseline (no command authentication)

3,000 trials. Source: `experiments/results/summary.md`.

| Attack rate (msg/s) | n | Reached alarm | Safety latency med (ms) | min | max | sd | Attacker armed | Attacker disarmed | Legit cmd took effect | Invariant violations |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 500 | 500 | 151 | 151 | 151 | 0 | 0 | 0 | 500 | 0 |
| 10 | 500 | 500 | 151 | 151 | 151 | 0 | 500 | 0 | **0** | 0 |
| 100 | 500 | 500 | 151 | 151 | 151 | 0 | 500 | 0 | **0** | 0 |
| 1,000 | 500 | 500 | 151 | 151 | 151 | 0 | 500 | 0 | **0** | 0 |
| 5,000 | 500 | 500 | 151 | 151 | 151 | 0 | 500 | 0 | **0** | 0 |
| 20,000 | 500 | 500 | 151 | 151 | 151 | 0 | 500 | 0 | **0** | 0 |

**Reading.** Without authentication the attacker arms the system in **2,500 of 2,500** flooded
trials, and the legitimate command is starved in **every** flooded trial. Note that the safety
latency stays at 151 ms even here — the alarm still works; what fails is control integrity and
command availability.

### 11.2 Adversarial campaign, hardened (`AUTH_COMMANDS=1`)

3,000 trials.

| Attack rate (msg/s) | n | Reached alarm | Safety latency med (ms) | Attacker armed | Attacker disarmed | Legit cmd took effect | Invariant violations |
|---|---|---|---|---|---|---|---|
| 0 | 500 | 500 | 151 | 0 | 0 | 500 | 0 |
| 10 | 500 | 500 | 151 | 0 | 0 | 500 | 0 |
| 100 | 500 | 500 | 151 | 0 | 0 | 500 | 0 |
| 1,000 | 500 | 500 | 151 | 0 | 0 | 500 | 0 |
| 5,000 | 500 | 500 | 151 | 0 | 0 | 500 | 0 |
| 20,000 | 500 | 500 | 151 | 0 | 0 | 500 | 0 |

**Totals across both builds: 6,000 trials, 0 invariant violations, 0 attacker-caused disarms.**

### 11.3 Headline comparison

| Metric | Baseline | Hardened |
|---|---|---|
| Attacker armed the system (flooded trials) | 2,500 / 2,500 | **0 / 2,500** |
| Legitimate command took effect (all trials) | 500 / 3,000 | **3,000 / 3,000** |
| Attacker-caused disarms | 0 | 0 |
| Safety-invariant violations | 0 | 0 |
| Safety latency, median | 151 ms | 151 ms |

Figure: `experiments/results/fig_campaign.pdf` (two panels, palette `#2a78d6` / `#eb6834`,
CVD ΔE 24.7, distinct markers and line styles so it survives greyscale printing).

### 11.4 The statistical test, and its caveat

**This caveat is as important as the result.** In simulation the harness advances the device
clock, so there is no CPU contention and the latency is deterministic: variance is exactly zero
and the Mann-Whitney U test is trivially satisfied at every attack rate.

| Attack rate | n(attack) | n(control) | U | z | p | Verdict |
|---|---|---|---|---|---|---|
| 10 | 500 | 500 | 125000 | 0 | 1 | indistinguishable |
| 100 | 500 | 500 | 125000 | 0 | 1 | indistinguishable |
| 1,000 | 500 | 500 | 125000 | 0 | 1 | indistinguishable |
| 5,000 | 500 | 500 | 125000 | 0 | 1 | indistinguishable |
| 20,000 | 500 | 500 | 125000 | 0 | 1 | indistinguishable |

`U = 125000` is exactly `n₁n₂/2`, and `z = 0`: the two samples are identical, which is the
signature of zero variance rather than of a meaningful null result.

What this establishes is the **logical** claim — no code path makes the safety response depend
on network input. It does **not** establish the timing claim. That requires hardware, where the
radio driver and safety loop genuinely contend. The same test is applied to hardware data by
`experiments/hardware/analyse_hw.py`.

This caveat is printed in `summary.md` itself, so it travels with the numbers.

### 11.5 Fuzzing

Source: `experiments/results/fuzz.json`, verbatim:

```json
{"iterations":3000000,"well_formed_shapes":1500000,"accepted":0,"final_state":"ARMED","counter_advanced":false}
```

3,000,000 iterations under AddressSanitizer and UndefinedBehaviorSanitizer: **0 accepted inputs,
0 counter advances, 0 memory errors, 0 undefined behaviour**. The device remained `ARMED`
throughout — the oracle is not merely "did not crash" but "did not change state and did not
advance the replay counter".

### 11.6 Host test suite

19 scenarios × 3 clock start values × 2 arduino-esp32 core APIs = 114 runs, plus 4
build-configuration checks and 2 shared-header-sync checks = **120 checks, all passing**
(re-run while writing this document: 120 `PASS`, 0 `FAIL`).

The 19 scenarios, from `tests/host/run_tests.sh`:

| Group | Scenarios |
|---|---|
| Core alarm behaviour | `basic`, `arm_alarm`, `disarm_in_entry`, `door_left_open` |
| Sensor conditioning | `pir_edge`, `pir_glitch`, `fusion` |
| Network and remote | `remote`, `network`, `linklost` |
| Display robustness | `display_fail`, `oled` |
| Persistence and recovery | `persist`, `restore`, `restore_door`, `diag` |
| Security | `auth`, `wifiguard`, `alert` |

The three clock start values include one just below the 32-bit `millis()` wrap, so wrap safety
is exercised in every scenario rather than asserted once.

Threat-to-scenario mapping is tabulated in `docs/EVALUATION.md` §3.

### 11.7 Results that do not exist

To be unambiguous, these are **not** in this repository and no number for them should be quoted:

- Physical sensor-to-siren latency (any condition).
- Measured deauth detection time on hardware.
- Measured current draw or energy cost.
- Measured MQTT round-trip latency or reconnect time on hardware.
- Any field or deployment result.

The results table in `docs/EVALUATION.md` §4.7 is deliberately left **empty** for these.

---

## 12. Formal verification results

### 12.1 `AlarmFSM.tla` — state machine and command path

25 distinct states at `MaxCtr = 4`. Exhaustive; no violations.

| Property | Type | Meaning |
|---|---|---|
| `TypeOK` | Invariant | All variables stay in their domains |
| `NoUnauthRemoteDisarm` | Invariant | No unauthenticated remote command ever disarms |
| `NoAlarmWhenDisarmed` | Invariant | The siren is never active while disarmed |
| `CounterMonotonic` | Property | The replay counter never decreases |
| `EntryLeadsToResolve` | Property | An entry delay always ends in alarm or disarm |
| `AlarmReArms` | Property | The alarm always ends in re-arm or disarm |

### 12.2 `Isolation.tla` — safety/network isolation

**This is the model that formalises the research claim.** 2,686 states generated, **660
distinct**, graph depth 26, no violations. Re-run while writing this document; output in
[Section 16](#16-validation-performed-and-errors-encountered).

The network task is modelled with **no fairness assumption**:

```tla
Spec == Init /\ [][Next]_vars /\ WF_vars(SafetyStep)
```

Weak fairness is asserted for `SafetyStep` only. `NetStep` gets none, so the network task may
stall forever, flood, fail to publish or crash, and the model must still satisfy every property.
Its possible actions are `NetGoBusy`, `NetStall`, `NetRecover`, `NetCrash`, `NetDeliver`,
`NetPublishFails`.

| Property | Type | Meaning |
|---|---|---|
| `TypeOK` | Invariant | Domains hold |
| `SafetyCanAlwaysStep` | Invariant | `(safetySteps < MaxEvents) ⇒ ENABLED SafetyStep` — **the isolation claim** |
| `NoNetworkWrite` | Invariant | `netOwnsState = FALSE`: the network side never writes alarm state |
| `QueueBounded` | Invariant | `queued ≤ QCap` |
| `NoSilentLoss` | Invariant | `produced = delivered + queued + dropped` — nothing vanishes uncounted |
| `SafetyProgress` | Property | `<>(safetySteps = MaxEvents)` — the safety function makes progress |

### 12.3 Mutation testing

A model checker reports "no violations" for a vacuous specification just as readily as for a
sound one. Both specs were therefore mutated to confirm the properties have force:

| Mutation | Expected | Observed |
|---|---|---|
| Allow an unauthenticated disarm to take effect | `NoUnauthRemoteDisarm` violated | Violation reported |
| Let the network task write alarm state | `NoNetworkWrite` violated | Violation reported |

The properties are therefore not vacuous.

---

## 13. Comparison: prior work vs this implementation

Full survey with verification notes: `docs/RELATED_WORK.md`.

| Work | Platform | Attacked resource on-die | Safety deadline measured |
|---|---|---|---|
| Fischer et al. (2020) | Linux industrial board | No | Yes |
| Meszlényi et al. (2025) | x86, PREEMPT-RT, dedicated NIC queues | No | Yes |
| Hoornaert et al. (2024) | Cortex-A53 + Jailhouse hypervisor + FPGA | n/a | Yes |
| Carbajal & Jodeiri Akbarfam (2026) | Wi-Fi testbed | n/a | No |
| Kremser & Graffi (2026) | ESP32-S3 (attack tool) | n/a | No |
| Cayre et al. (2023) | ESP32 family (attack) | Yes | No |
| Azhar et al. (2026) | ESP32-C3 | No | No |
| Ieropoulos et al. (2026) | ESP32 | No | No |
| **This work** | **ESP32** | **Yes** | **Yes †** |

† Logical invariance established; physical timing invariance is the open step.

**Method comparison with the closest prior work:**

| | Fischer et al. (2020) | This work |
|---|---|---|
| Formal verification | None | 2 TLA+ models, TLC-checked, mutation-tested |
| Simulation | None | 6,000 seeded trials, reproducible |
| Fuzzing | None | 3,000,000 iterations, ASan/UBSan |
| Hardware measurement | **Done** | **Specified, not done** |
| Artifact availability | Not public | Public, CI-verified |

The honest summary: this work is stronger on formal and reproducible evidence and weaker on
hardware measurement, which is exactly the gap the next step closes.

---

## 14. Before-and-after: evolution across versions

Each row is verifiable from `CHANGELOG.md` and the commit history.

| Aspect | v1.0 (prototype) | v2.0 | v2.1 | v2.2 (current) |
|---|---|---|---|---|
| Alarm logic | Blocking `delay(1000)` ×5 | Non-blocking `millis()` FSM | same | same |
| Offline operation | Detection required Wi-Fi | Fully offline | same | same |
| State machine | None | 5 states | same | same + formally verified |
| Concurrency | Single loop | Network task on core 0 | same | same + isolation model |
| Notifications | `Serial.print` only | Real MQTT + Last Will | + HA discovery, seq numbers | + signed ESP-NOW fallback |
| Power-cut behaviour | Disarmed silently | Disarmed silently | Restored from NVS | same |
| Command security | None | None | TLS + broker login required for disarm | **HMAC-SHA256 + replay counter** |
| Attack detection | None | None | None | **Deauth/disassoc detection, `link_lost`** |
| False-alarm control | None | PIR warm-up + 150 ms confirm | same | + optional radar fusion |
| Verification | None | Host tests + CI | + persistence/race tests | **+ TLA+, campaign, fuzzing** |
| Display failure | Halted the program | Non-fatal | same | same |

**Measured before/after available:** build size v2.1 → v2.2 (+≈3 KB flash, +≈170 B RAM, from
CI) and the baseline-vs-hardened campaign comparison in [Section 11.3](#113-headline-comparison).

**Not available:** any before/after on physical timing or energy, because no hardware run exists
for either version.

---

## 15. Debugging fixes and optimisations

Each of these is a real defect found and fixed during this work, verifiable from the commit
history, the changelog or the test suite. They are documented because the *method* that found
them is part of the contribution.

### 15.1 Buzzer timer wrap-around (v2.0)

**Symptom.** After ≈25 days of uptime the buzzer could remain on.
**Cause.** A `millis()` comparison of the form `now >= since + interval`, which breaks at the
32-bit wrap.
**Fix.** All time arithmetic rewritten as `(uint32_t)(now - since) >= interval`.
**Found by.** Running every test scenario at three clock start values, one near the wrap point.
This is now a permanent property of the suite.

### 15.2 Event-queue race losing an event uncounted (v2.1)

**Symptom.** When the offline queue overflowed while the network task was delivering the
backlog, an event could be removed without being published **and without being counted** as
dropped.
**Why it mattered.** It silently broke the `NoSilentLoss` property
(`produced = delivered + queued + dropped`).
**Fix.** The network task now dequeues **before** publishing and uses `xQueueSendToFront` to put
the event back if the link drops; genuinely unrecoverable events are counted in `dropped`.
**Covered by.** The queue-race test scenario, and formalised as the `NoSilentLoss` invariant.

### 15.3 Campaign globals leaking between trials

**Symptom.** A spurious `not_armed_after_exit_delay` violation appeared even at attack rate 0.
**Cause.** Firmware globals (`state`, counters) persisted across trials sharing one process, so
each trial started from the previous trial's state.
**Fix.** `fork()` per trial, giving every trial pristine globals.
**Significance.** Without this fix the campaign would have reported a false positive. It is the
clearest example of why the harness needs as much scrutiny as the firmware.

### 15.4 Campaign self-interference

**Symptom.** A fallback button press disarmed a system the command under test had just armed,
corrupting the outcome classification.
**Fix.** Check `state == SysState::DISARMED` before the fallback press, and capture the
legitimate message **after** delivery rather than before.

### 15.5 A fuzzer "finding" that was not a bug

**Symptom.** At iteration 249 the fuzzer reported an accepted input:
`DISARM:999999:...6dC0...`.
**Investigation.** The mutation had flipped a bit in the hex tag, changing `c` to `C`. Hex
decoding is case-insensitive, so the decoded tag bytes were **identical** — the input was the
genuine, correctly signed command. Acceptance was correct behaviour.
**Fix.** The corpus now signs the mutation seed with a deliberately wrong key
(`"attacker-key-not-the-device-key"`), so no mutation can accidentally yield a valid command.
**Recorded because** it is exactly the kind of result that becomes a false claim in a paper if
not chased down.

### 15.6 TLA+ parse error on a liveness property

**Symptom.** `[]<>(safetySteps' # safetySteps)_vars` failed to parse.
**Cause.** Invalid TLA+ syntax for the intended property.
**Fix.** Replaced with `SafetyProgress == <>(safetySteps = MaxEvents)`.

### 15.7 Sensor-fusion false fire at start-up

**Symptom.** In AND mode the fusion logic could fire spuriously just after boot.
**Cause.** `lastPir` / `lastRadar` initialised to 0, so early timestamps compared as "recent".
**Fix.** The `seeded` flag, setting both to `now - windowMs - 1` on first use
([Section 5.3](#53-sensor-fusion)).

### 15.8 Smaller fixes

| Issue | Fix |
|---|---|
| `alertCounter` unused under `-Werror` on host builds | `[[maybe_unused]]` |
| CI runner lacks matplotlib, failing the pipeline | Figure generation made non-fatal in `run.sh` (it is presentation, not a correctness check) |
| ESP-NOW callback signature differs between arduino-esp32 2.x and 3.x | Signature guarded by core-version macro; both compile in CI |
| Git remote pointed at the old lower-case repository URL | `git remote set-url` to `Smart-Home-Automation` |
| File header said v2.1.0 while `FW_VERSION` was 2.2.0 | Header corrected (found while writing this document) |

### 15.9 Optimisations

| Optimisation | Effect |
|---|---|
| HMAC verification on core 0 | A command flood costs the safety core nothing; verification cost is paid in the network domain |
| Zero-timeout mutex for the status snapshot | The safety loop never blocks on the network task |
| Truncated 128-bit tag instead of full 256-bit | Halves the on-wire tag with a forgery probability of 2⁻¹²⁸ |
| Detector cooldown (10 s) | Prevents the deauth detector from flooding the event queue |
| Drop-oldest-and-count on queue overflow | Bounded memory with accounting, instead of unbounded growth or silent loss |

---

## 16. Validation performed, and errors encountered

Everything in this section was run while writing this document, on the environment in
[Section 7.3](#73-software-environment-used-for-the-committed-results).

### 16.1 Validation results

| Check | Command | Result |
|---|---|---|
| Host test suite | `./tests/host/run_tests.sh` | **PASS** — all scenarios, build configs and header-sync checks |
| Formal verification | `./formal/run_tlc.sh` | **PASS** — `AlarmFSM` and `Isolation`; Isolation: 2,686 states generated, 660 distinct, depth 26, no error |
| Paper compilation | `pdflatex paper.tex` ×2 | **PASS** — 4 pages, 0 overfull boxes |
| Brief compilation | `pdflatex supervisor_brief.tex` | **PASS** — 1 page, 0 overfull boxes |
| Committed results vs documented claims | manual cross-check against `summary.json` / `fuzz.json` | **CONSISTENT** — 6,000 trials, 2,500/2,500 baseline attacker-armed, 0 hardened, fuzz `accepted: 0` |
| **Full pipeline re-run** | 6,000 campaign trials + 3,000,000 fuzz iterations, from the committed seeds | **EXACT REPRODUCTION** — see below |
| CI pipeline | GitHub Actions | **PASS** — all 5 jobs on the most recent run |

**Exact reproduction check.** The entire campaign and fuzzing pipeline was re-run from scratch
from the committed seeds, and the regenerated outputs were diffed against the committed ones:

| Output | Result |
|---|---|
| `experiments/results/summary.json` | **byte-for-byte identical** |
| `experiments/results/summary.md` | **byte-for-byte identical** |
| `experiments/results/fuzz.json` | **byte-for-byte identical** |

`git status experiments/results/` reported no modifications after the re-run, which is the
strongest available evidence that the committed results are reproducible rather than
hand-maintained. Fuzzer output, verbatim and unchanged:

```json
{"iterations":3000000,"well_formed_shapes":1500000,"accepted":0,"final_state":"ARMED","counter_advanced":false}
```

**Note on how this was run.** A first attempt to run the whole pipeline in one go was stopped by
the execution environment's background time limit after completing all 3,000 baseline trials and
2,338 of the 3,000 hardened trials. That partial run already matched the committed aggregates at
every attack rate. The run was then completed in two parts, which is why the runtime caveat in
[Section 9.4](#94-reproduce-the-full-experimental-pipeline) exists. The interruption damaged
nothing: the stop occurred before the analysis step, so no committed file was overwritten
mid-write.

TLC output, verbatim:

```
2686 states generated, 660 distinct states found, 0 states left on queue.
The depth of the complete state graph search is 26.
Model checking completed. No error has been found.
PASS Isolation
```

### 16.2 Issues found and fixed while writing this document

| Issue | Resolution |
|---|---|
| `firmware/smart_home/smart_home.ino` header said "firmware v2.1.0" while `FW_VERSION` is `"2.2.0"` | Header corrected to v2.2.0 with a v2.2 summary |
| `docs/EVALUATION.md` §5 still said "A full literature search should be completed before claiming novelty" | Updated to point at `docs/RELATED_WORK.md`, which now exists |
| No dependency manifest existed | `requirements.txt` added |
| No machine-readable citation metadata | `CITATION.cff` added |

### 16.3 Errors and environment limitations encountered, reported honestly

| Limitation | Detail |
|---|---|
| **GitHub topics could not be set** | `gh api repos/.../topics -X PUT` → HTTP 403, "Write access to this GitHub API path is not permitted through this proxy." Must be done manually |
| **GitHub release could not be created** | `gh api repos/.../releases -X POST` → HTTP 403, "Creating, editing, or deleting releases is not permitted for this session type." Must be done manually |
| GitHub GraphQL unavailable | `gh repo view --json` → HTTP 403; REST used instead where permitted |
| Two publisher pages unreachable for citation verification | An MDPI *BDCC* smart-home review and a ScienceDirect authentication paper. **Deliberately not cited**; recorded as excluded in `docs/RELATED_WORK.md` |
| matplotlib absent on the CI runner | Figure generation is non-fatal in `run.sh`; the committed figure was generated locally |
| JDK version differs between local (21) and CI (17) | TLC results identical on both; recorded in [Section 7.3](#73-software-environment-used-for-the-committed-results) |

**No unresolved execution errors remain.** Everything that can be run in this environment runs
clean.

---

## 17. Limitations, reproducibility gaps and unverified items

### 17.1 The principal limitation

**No physical hardware measurement has been performed.** Every result is from formal
verification or host-based simulation. The headline research claim — timing invariance under
on-chip radio stress — is therefore **open**, and no number for it appears anywhere in this
repository. This is stated in the paper, the README, `docs/RESEARCH.md`, `docs/EVALUATION.md`
and here.

### 17.2 What simulation structurally cannot show

| Not shown | Why |
|---|---|
| Real radio timing | The host harness has no radio |
| True parallel execution on two cores | The harness advances a single logical clock |
| Electrical behaviour, current, brown-out | No hardware |
| Real-world effectiveness of radio-layer attacks | Requires an authorised RF environment |
| Latency variance under genuine CPU contention | Harness latency is deterministic; variance is zero |

### 17.3 Security limitations acknowledged

| Limitation | Status |
|---|---|
| Wideband 2.4 GHz jamming defeats ESP-NOW as well as Wi-Fi | Acknowledged (T6, partial). The local siren is the last line of defence |
| Key extraction by a resourced physical attacker | Out of scope; flash encryption and secure boot are **future** (T10) |
| Signed OTA update | **Not implemented** (T11) |
| True anti-mask sensing | **Not implemented**; fusion raises the bar but does not close it (T12) |
| Demo keys are public | `SECRET_CMD_KEY` and `SECRET_ALERT_KEY` defaults are published demo values and **must** be overridden in `secrets.h` |

### 17.4 Reproducibility gaps

| Gap | Impact | Mitigation |
|---|---|---|
| Raw per-trial JSONL not committed | Cannot inspect individual trials without re-running | Regenerates identically from seeds; aggregates are committed |
| `tla2tools.jar` not committed (git-ignored) | Needs network on first run | Version pinned to v1.8.0 in `run_tlc.sh` |
| arduino-esp32 toolchain not vendored | Build needs network | Exact versions pinned in CI (2.0.17, 3.3.12) |
| Hardware results absent | The headline claim is untested | Full apparatus and protocol provided in `experiments/hardware/` |
| Figure generation needs matplotlib | Figure skipped without it | Non-fatal; committed figure provided |

### 17.5 Unverified items

| Item | Status |
|---|---|
| Full author list of Yun et al., *Fuzzing of Embedded Systems: A Survey* | Could not be confirmed from an accessible record; cited as "et al." |
| Exact conference for Bley et al. (2025) | DOI confirms ACM proceedings; cited as "ACM, 2025" with the DOI rather than naming a venue unverified |
| Two candidate smart-home references | Publisher pages unreachable; **excluded**, not cited |
| Real-world false-alarm rate of the fusion modes | Never measured; only logic is tested |
| Energy cost of the security features | Never measured |

### 17.6 Future work

1. **Run the hardware campaign** (conditions A–C immediately; D with authorisation). This is the
   single step between the current state and a complete paper.
2. Implement flash encryption, secure boot v2 and signed OTA (T10, T11).
3. Extend the fuzzing to whole-firmware rehosting, following Bley et al. (2025) and
   SysFuSS (2026).
4. Characterise false-alarm rates of the three fusion modes empirically.

---

## 18. References

Each reference was resolved against a publisher page or preprint record. Full positioning and
verification notes are in [`docs/RELATED_WORK.md`](RELATED_WORK.md).

1. F. Fischer et al., "Analysis of Industrial Device Architectures for Real-Time Operations
   under Denial of Service Attacks," arXiv:2007.08885, 2020.
2. A. Carbajal and A. Jodeiri Akbarfam, "A Software-Defined Testbed for Quantifying
   Deauthentication Resilience in Modern Wi-Fi Networks," arXiv:2602.23513, 2026.
3. A. Burns and R. I. Davis, "Mixed Criticality Systems: A Review," 14th edn., University of
   York, February 2026.
4. L. Meszlényi, J. Kahle, D. Püllen, S. Kowalewski, S. Katzenbeisser, and A. Kampmann,
   "Towards Timing Isolation for Mixed-Criticality Communication in Software-Defined Vehicles,"
   arXiv:2508.13652, 2025.
5. D. Hoornaert, G. Ghaemi, A. Bastoni, R. Mancuso, M. Caccamo, and G. Corradi, "Mcti:
   mixed-criticality task-based isolation," *Real-Time Systems*, vol. 60, no. 2, pp. 328–365,
   2024. doi:10.1007/s11241-024-09425-5
6. S. Kremser and K. Graffi, "Evaluating the ESP32-S3 for Wi-Fi Penetration Testing Through the
   Development of Deauther32 and HackHeld32," *Sensors*, vol. 26, no. 11, art. 3287, 2026.
   doi:10.3390/s26113287
7. R. Cayre, D. Cauquil, and A. Francillon, "ESPwn32: Hacking with ESP32 System-on-Chips," in
   *Proc. 17th IEEE Workshop on Offensive Technologies (WOOT)*, 2023.
8. M. Krichen, "A Survey on Formal Verification and Validation Techniques for Internet of
   Things," *Applied Sciences*, vol. 13, no. 14, art. 8122, 2023. doi:10.3390/app13148122
9. L. Lamport, *Specifying Systems: The TLA+ Language and Tools for Hardware and Software
   Engineers*. Addison-Wesley, 2002.
10. J. Yun et al., "Fuzzing of Embedded Systems: A Survey," *ACM Computing Surveys*, 2022.
    doi:10.1145/3538644
11. M. Bley, T. Scharnowski, S. Wörner, M. Schloegel, and T. Holz, "Protocol-Aware Firmware
    Rehosting for Effective Fuzzing of Embedded Network Stacks," ACM, 2025.
    doi:10.1145/3719027.3765125
12. D. Tharindu, A. Jayasena, and P. Mishra, "SysFuSS: System-Level Firmware Fuzzing with
    Selective Symbolic Execution," arXiv:2602.02243, 2026.
13. M. A. Azhar, M. Azwar, and O. Asroni, "Performance and Security Analysis of MQTT over TLS on
    ESP32-Based IoT Systems," *J. Applied Informatics and Computing*, 2026.
14. V. Ieropoulos et al., "Empowering IoT Security: On-Device Intrusion Detection in Resource
    Constrained Devices," arXiv:2605.13159, 2026.

**Standards referenced in the implementation:** RFC 2104 (HMAC), FIPS 180-4 (SHA-256),
FIPS 198-1 (keyed-hash MAC), RFC 4231 (HMAC test vectors), MQTT 3.1.1, IEEE 802.11
(management frame subtypes).
