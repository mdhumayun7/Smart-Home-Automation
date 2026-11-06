# Architecture, traceability and formal models

Phases 1, 2, 4, 5 and 6 of the publication package: the project audit and traceability matrix, the
end-to-end architecture, the formal state machine with its transition table, the event-delivery
architecture with its honest delivery guarantee, and the command execution model.

Every row below was verified against the source at commit `34a1d5c`, firmware v2.2.0. Line numbers
refer to `firmware/smart_home/smart_home.ino` unless stated otherwise. Where a mechanism is **not**
implemented it says so rather than describing an intention.

---

## 1. Traceability matrix

### 1.1 Architecture element to implementation

| Architecture element | Implementation location | Verified by |
|---|---|---|
| Safety domain (core 1) | Arduino `loop()`, `tickSafety()` | `tests/host/test_firmware.cpp` scenarios `basic`, `arm_alarm` |
| Network domain (core 0) | `networkTask()`, pinned by `xTaskCreatePinnedToCore(networkTask, "net", 8192, nullptr, 1, nullptr, 0)` | `network` scenario; `formal/Isolation.tla` |
| Safety → network queue | `eventQ = xQueueCreate(16, sizeof(Event))` | `NoSilentLoss` invariant; queue-race scenario |
| Network → safety queue | `cmdQ = xQueueCreate(4, sizeof(CmdMsg))` | `remote`, `auth` scenarios |
| Non-blocking status snapshot | `xSemaphoreTake(statusMutex, 0)` in safety loop; `pdMS_TO_TICKS(10)` in network task | `formal/Isolation.tla` `SafetyCanAlwaysStep` |
| Five-state FSM | `SysState` enum (L258-295), `setState()` (L444), `tickSafety()` (L655-690) | `formal/AlarmFSM.tla`; 19 host scenarios |
| State persistence | `persistArmed()` called from `setState()` (L449-450) | `persist`, `restore`, `restore_door` scenarios |
| HMAC-SHA256 authentication | `firmware/smart_home/authmac.h`, `verifySigned()` | RFC 4231 vectors in `authmac.h`; `auth` scenario |
| Replay protection | `cmdCounter` compare + `persistCounter()` | `AlarmFSM.tla` `CounterMonotonic`; `auth` scenario |
| Constant-time tag compare | `authmac::ct_equal()` | Code inspection; no timing test exists |
| Deauth detection | `firmware/smart_home/wifi_guard.h` `DeauthDetector::observe()`; `wifiSniffer()` IRAM callback | `wifiguard` scenario |
| ESP-NOW fallback alert | `firmware/smart_home/alertmsg.h`; `firmware/espnow_receiver/` | `alert` scenario; CI compiles with `-DENABLE_ESPNOW=1` |
| Sensor fusion | `firmware/smart_home/sensor_fusion.h` `fusion_step()` | `fusion` scenario; CI compiles `-DFUSION_MODE=FUSION_AND` |
| Watchdog | `ENABLE_LOOP_WDT`, watchdog kick in `loop()` | `diag` scenario (reset reason in boot event) |
| Wrap-safe timing | `(uint32_t)(now - since) >= interval` throughout | Every scenario run at 3 clock starts, one near the wrap |

### 1.2 Claim to evidence

| Claim | Evidence | Status |
|---|---|---|
| The safety function never blocks on the network | `Isolation.tla` `SafetyCanAlwaysStep`, 660 distinct states, no violation | **Verified (logical)** |
| The network side never writes alarm state | `Isolation.tla` `NoNetworkWrite` | **Verified (logical)** |
| No event is lost without being counted | `Isolation.tla` `NoSilentLoss`; queue-race scenario | **Verified (logical)** |
| Forged commands are rejected | 6,000-trial campaign, 0 attacker disarms; 3M fuzz iterations, 0 accepted | **Verified (simulation)** |
| Replayed commands are rejected | `AlarmFSM.tla` `CounterMonotonic`; `auth` scenario; fuzz corpus stale-counter class | **Verified (simulation)** |
| An unauthenticated remote command never disarms | `AlarmFSM.tla` `NoUnauthRemoteDisarm`, mutation-tested | **Verified (logical)** |
| Command authentication preserves command availability under flood | Campaign: 3,000/3,000 hardened vs 500/3,000 baseline | **Verified (simulation)** |
| No memory-safety or UB defects in the command parser | 3,000,000 iterations under ASan + UBSan | **Verified (simulation)** |
| Security features cost ≈3 KB flash, ≈170 B RAM | CI compiler output, two core versions | **Verified (measured)** |
| **Physical sensor-to-siren latency is invariant under radio stress** | None | **NOT VERIFIED — the open claim** |
| Deauth detector false-positive rate under ordinary churn | None | **NOT VERIFIED** |
| Per-command CPU cost of HMAC verification | None | **NOT VERIFIED** |
| Energy cost of security features | None | **NOT VERIFIED** |
| Real-world false-alarm rate of fusion modes | None | **NOT VERIFIED** |

### 1.3 Incomplete, unused or planned components

| Component | Status |
|---|---|
| `experiments/hardware/` (probe firmware, collection, analysis) | **Complete but never run.** No hardware data exists |
| `tools/eval_commands.py`, `tools/measure.py` | **Complete but never run against hardware** |
| Flash encryption, secure boot v2 | **Not implemented.** Threat T10, future work |
| Signed OTA update | **Not implemented.** Threat T11 |
| True anti-mask sensing | **Not implemented.** Threat T12; fusion raises the bar only |
| TLS for MQTT (`MQTT_USE_TLS`) | **Implemented but off by default**, and never exercised against a real TLS broker |
| ESP-NOW (`ENABLE_ESPNOW`) | **Implemented, compiles in CI, off by default**, never run on two physical boards |
| Sensor fusion (`FUSION_MODE`) | **Implemented, compiles in CI, defaults to `FUSION_PIR_ONLY`**, logic tested, never run with a physical LD2410 |

### 1.4 Inconsistencies and technical risks on record

| Item | Status |
|---|---|
| File header announced v2.1.0 while `FW_VERSION` was 2.2.0 | **Fixed** (commit `5e1e2f1`) |
| `EVALUATION.md` stated the literature survey was outstanding | **Fixed** (commit `5e1e2f1`) |
| Published demo keys in `secrets.example.h` | **By design**, documented; must be overridden. Risk if a user ships defaults |
| Harness stubs authored by the same person as the firmware | **Open risk.** A shared misconception would be invisible to both. See `PEER_REVIEW.md` §E2 |
| Statistical test is vacuous in simulation (zero variance) | **Documented**, and flagged for removal from the results table. See `PEER_REVIEW.md` §B2 |
| Formal models abstract away timing, which is the phenomenon under study | **Open, inherent.** See `PEER_REVIEW.md` §C1 |

---

## 2. End-to-end architecture

### 2.1 Component inventory

| Component | Purpose | Inputs | Outputs | Depends on | Location |
|---|---|---|---|---|---|
| `tickSafety()` | The safety FSM. Sole writer of alarm state | Debounced sensor edges, `cmdQ` messages, `millis()` | `setState()` calls, `eventQ` enqueues, output flags | Nothing on the network side | L655-690 |
| `readInputs()` | Debounce and confirmation filtering | GPIO 13 (PIR), 14 (door), 27 (button), 33 (radar) | `pirEdge`, `doorOpened`, `buttonPressed` | `fusion_step()` when enabled | L~575 |
| `setState()` | The only state-transition point | Target state, event type, source, time | Mutates `state`, `stateSince`, `statusDirty`; emits event; persists armed flag | `emitEvent()`, `persistArmed()` | L444-451 |
| `driveOutputs()` | Actuation | `state`, `stateSince`, beep flags | GPIO 23 (buzzer), 25/26 (LEDs) | None | L~694 |
| `emitEvent()` | Event creation and enqueue | Type, source | `eventQ` entry with `seq`, timestamps | `eventQ` | L~415-430 |
| `networkTask()` | All network activity, pinned to core 0 | `eventQ`, `sharedStatus`, MQTT socket | MQTT publishes, `cmdQ` enqueues | Wi-Fi, NTP, MQTT, ESP-NOW | pinned at setup |
| `verifySigned()` | Command authentication | Raw payload | Verb, counter, authentication verdict | `authmac.h` | network side |
| `DeauthDetector` | Radio-layer flood detection | Frame counts from `wifiSniffer()` | Boolean "flood detected" | None (pure logic) | `wifi_guard.h` |
| `wifiSniffer()` | Promiscuous 802.11 callback, `IRAM_ATTR` | Raw frames | Increments a counter | ESP-IDF Wi-Fi | L~565-580 |
| `fusion_step()` | PIR and radar agreement | PIR and radar assertion times | Fire / no-fire | None (pure logic) | `sensor_fusion.h` |

### 2.2 Trust boundaries

```
 ┌─ UNTRUSTED ────────────────────────────────────────────────────┐
 │  2.4 GHz radio environment   ·   MQTT broker and its clients   │
 └──────────────┬──────────────────────────────┬──────────────────┘
                │ 802.11 frames                │ MQTT command topic
                ▼                              ▼
 ┌─ BOUNDARY 1: radio ──────────┐  ┌─ BOUNDARY 2: command auth ───┐
 │ wifiSniffer: counts only,    │  │ verifySigned: HMAC tag +      │
 │ never transmits, never       │  │ counter freshness. Runs on    │
 │ reaches the event path       │  │ CORE 0, before cmdQ           │
 │ directly                     │  │                               │
 └──────────────┬───────────────┘  └───────────────┬──────────────┘
                │                                  │ only verdict + verb cross
                ▼                                  ▼
 ┌─ TRUSTED: safety domain, core 1 ──────────────────────────────┐
 │  Local sensors (trusted by assumption) · FSM · siren · NVS    │
 └───────────────────────────────────────────────────────────────┘
```

The design intent is that **no untrusted input reaches the safety domain without crossing a
boundary that reduces it to a verdict plus an enumerated verb.** `formal/Isolation.tla` is the
formal statement of the corresponding isolation property.

Full threat enumeration: `docs/THREAT_MODEL.md` (12 threats, T1-T12).

### 2.3 Deployment architecture

| Node | Role | Required |
|---|---|---|
| ESP32 DevKit | Alarm device running `firmware/smart_home` | Yes |
| MQTT broker | Event transport, command source, Last Will observer | Optional — the alarm is fully functional offline |
| Home Assistant | Consumer, auto-configured by retained discovery messages | Optional |
| Second ESP32 | `firmware/espnow_receiver`, out-of-band alert sink | Optional (`ENABLE_ESPNOW`) |
| Third ESP32 | `experiments/hardware/latency_probe`, independent measuring instrument | Experiments only |

**Failure paths that are implemented:** Wi-Fi loss (retry every `WIFI_RETRY_MS`, `link_lost` event
when armed), MQTT loss (retry every `MQTT_RETRY_MS`, events queue up to 16), broker-side detection
of device loss (Last Will), power cut (armed state restored from NVS, open door starts entry delay),
firmware hang (task watchdog reset, reset reason reported in the boot event), OLED failure
(non-fatal, logic continues).

---

## 3. Formal state machine (Phase 4)

### 3.1 States

| State | Meaning | Entry action | Exit condition |
|---|---|---|---|
| `DISARMED` | Idle. Sensors monitored but do not trigger | `persistArmed(false)`, 150 ms beep when entered via `disarm()` | Button press, or authenticated `ARM` |
| `EXIT_DELAY` | Armed, grace period to leave | — | `EXIT_DELAY_MS` elapsed, button, or `DISARM` |
| `ARMED` | Active. Sensor assertions trigger | `persistArmed(true)`, 300 ms beep on timer entry | Sensor trigger, button, or `DISARM` |
| `ENTRY_DELAY` | Triggered, grace period to disarm | — | `ENTRY_DELAY_MS` elapsed, button, or `DISARM` |
| `ALARM` | Siren active | `alarmCount++` | `ALARM_DURATION_MS` elapsed, button, or `DISARM` |

Initial state: `DISARMED` (L308). On boot with `RESTORE_ARMED_ON_BOOT` and a persisted armed flag,
`setState(ARMED, "restored_armed", "nvs", bootMs)` runs instead (L1068). **There is no terminal
state**; the machine runs until power loss or reset.

### 3.2 Transition table

Source → destination, with the triggering event, the guard, and the action. Verified against
L655-690, L545-570 and L1068.

| # | Source | Event / condition | Guard | Action | Destination |
|---|---|---|---|---|---|
| T1 | `DISARMED` | Button press | — | `beginArm("button")` | `EXIT_DELAY` |
| T2 | `DISARMED` | Cmd `ARM` / `ARM_AWAY` | authenticated, or `AUTH_COMMANDS=0` | `beginArm(src)` | `EXIT_DELAY` |
| T3 | `EXIT_DELAY` | Timer | `now − stateSince ≥ EXIT_DELAY_MS` | `setState`, 300 ms beep; **then** if `door.stable` → T7 | `ARMED` |
| T4 | `ARMED` | PIR confirmed | `pirEdge`, past warm-up, fusion satisfied | `trigger("motion","pir")` | `ENTRY_DELAY` |
| T5 | `ARMED` | Door opened | `doorOpened` | `trigger("door_open","door")` | `ENTRY_DELAY` |
| T6 | `ENTRY_DELAY` | Timer | `now − stateSince ≥ ENTRY_DELAY_MS` | `alarmCount++` | `ALARM` |
| T7 | `ARMED` | Trigger with `ENTRY_DELAY_MS == 0` | compile-time | `alarmCount++` | `ALARM` |
| T8 | `ALARM` | Timer | `now − stateSince ≥ ALARM_DURATION_MS` | `setState("alarm_end")` | `ARMED` |
| T9 | any ≠ `DISARMED` | Button press | — | `disarm("button")`, 150 ms beep | `DISARMED` |
| T10 | any ≠ `DISARMED` | Cmd `DISARM` | `authed ∨ ALLOW_REMOTE_DISARM` | `disarm(src)` | `DISARMED` |
| T11 | boot | Power-on | `RESTORE_ARMED_ON_BOOT` ∧ NVS armed flag set | `setState("restored_armed","nvs")` | `ARMED` |

### 3.3 Rejected transitions

These are **non-transitions**: the machine stays put and emits a diagnostic event. They are part of
the specification, not error handling bolted on.

| Condition | Event emitted | Resulting state |
|---|---|---|
| Cmd `DISARM`, not authenticated, `ALLOW_REMOTE_DISARM=0` | `cmd_rejected` | unchanged |
| Cmd `DISARM` while already `DISARMED` | `cmd_ignored` | `DISARMED` |
| Cmd `ARM` while not `DISARMED` | `cmd_ignored` | unchanged |
| Command with a bad HMAC tag | `cmd_badmac` | unchanged |
| Command with `counter ≤ cmdCounter` | `cmd_replay` | unchanged |
| Command unsigned while `AUTH_COMMANDS=1` | `cmd_unauth` | unchanged |
| Malformed payload (unparseable) | none — silently dropped | unchanged |

The last row is deliberate: emitting an event per malformed payload would turn a command flood into
an event flood, which is the denial-of-service the bounded queue exists to prevent.

### 3.4 Invariants

Checked by TLC in `formal/AlarmFSM.tla` (25 distinct states) and `formal/Isolation.tla` (660
distinct states, depth 26). Both mutation-tested.

| Invariant | Statement |
|---|---|
| `NoAlarmWhenDisarmed` | The siren is never active while `state = DISARMED` |
| `NoUnauthRemoteDisarm` | No unauthenticated remote command causes a transition to `DISARMED` |
| `CounterMonotonic` | `cmdCounter` never decreases |
| `SafetyCanAlwaysStep` | `(safetySteps < MaxEvents) ⇒ ENABLED SafetyStep` |
| `NoNetworkWrite` | `netOwnsState = FALSE` always |
| `QueueBounded` | `queued ≤ QCap` |
| `NoSilentLoss` | `produced = delivered + queued + dropped` |

Liveness: `EntryLeadsToResolve`, `AlarmReArms`, `SafetyProgress`. Fairness is asserted for
`SafetyStep` only — `WF_vars(SafetyStep)` — so the network task may starve forever and the
properties must still hold.

---

## 4. Event-delivery architecture (Phase 5)

### 4.1 Lifecycle

| Stage | Mechanism | Location |
|---|---|---|
| Generation | `emitEvent(type, src)` on the safety core | L415-430 |
| Identification | `e.seq = ++eventSeq`, monotonic since boot, plus `epoch` (NTP) and `upMs` | L419, L237 |
| Enqueue | `eventQ`, depth 16, FIFO | L428 |
| Overflow handling | Oldest dequeued and discarded, `eventsDropped++` | L428 |
| Drain | Network task takes **at most 4 per cycle** | L972 |
| Transport | MQTT `publish(topicEvent, msg)` — JSON payload | L915 |
| Retry | On publish failure, `xQueueSendToFront()` to preserve order; if that fails, `netDropped++` | L975 |
| Acknowledgement | **None.** See §4.2 | — |
| State reporting | `publish(topicState, msg, true)` — **retained**, includes `dropped` and `queued` | L934 |
| Liveness to consumer | Last Will, retained availability `"online"`, heartbeat every `HEARTBEAT_MS` | L900 |

### 4.2 Delivery guarantee: at-most-once

This must be stated precisely, because overclaiming here is a common reviewer catch.

**The guarantee is at-most-once.** Justification:

- Events are published with `PubSubClient::publish()`, which is **MQTT QoS 0**. The library does
  not implement QoS 1 or 2 for publishing. There is therefore **no broker acknowledgement**, and
  the device cannot know whether an event arrived.
- An event can be lost in two distinct ways: **dropped at the queue** when more than 16 events are
  pending (counted in `eventsDropped`), or **lost in transit** after a successful local `publish()`
  call (not counted, and not knowable by the device).
- There is **no duplicate suppression** on the consumer side, and the single requeue-to-front retry
  happens only when `publish()` returns failure locally, so a duplicate is possible if the broker
  received a message the client believed had failed.

| Property | Supported? | Basis |
|---|---|---|
| At-most-once | **Yes** | QoS 0, no retransmission loop |
| At-least-once | **No** | No acknowledgement, no persistent retry |
| Exactly-once | **No** | Neither of the above |
| Ordering (FIFO) | **Yes, for queued events** | FIFO queue; `xQueueSendToFront` preserves order on retry |
| Loss detectability | **Yes, by the consumer** | `seq` gaps reveal loss; `dropped` and `queued` are published in the retained state |
| Durability across reboot | **No, for events** | `eventQ` is RAM only. Armed state and the replay counter **are** persisted in NVS |

**The design decision this reflects:** the alarm is not a logging system. Local actuation is the
safety guarantee, and notification is best-effort with the loss made visible. Accordingly the
system is engineered so that losing an event is *observable* rather than *impossible*: hence the
sequence numbers, the `dropped` counter in the retained state, and the `NoSilentLoss` invariant.

### 4.3 Event catalogue

Verified by extracting every `emitEvent` call site and every `setState` event type.

| Event type | Origin | Meaning |
|---|---|---|
| `boot` | setup | Device started; carries reset reason and firmware version |
| `exit_delay`, `armed`, `entry_delay`, `alarm`, `alarm_end`, `disarmed` | `setState()` | State transitions |
| `restored_armed` | boot path | Armed state restored from NVS |
| `motion`, `door_open` | `trigger()` | Trigger cause, emitted *before* the state change |
| `cmd_unauth` | network core | Unsigned command while `AUTH_COMMANDS=1` |
| `cmd_badmac` | network core | HMAC tag verification failed |
| `cmd_replay` | safety core | Counter not strictly greater than stored |
| `cmd_rejected` | safety core | `DISARM` refused for lack of authorisation |
| `cmd_ignored` | safety core | Command valid but a no-op in the current state |
| `wifi_deauth` | safety core | Deauth/disassoc flood threshold crossed |
| `link_lost` | safety core | Wi-Fi dropped while armed |

---

## 5. Command execution model (Phase 6)

### 5.1 Lifecycle, and which core runs each stage

The core split is the security-relevant design decision: parsing and the expensive HMAC run on the
network core, so a command flood consumes no safety-core time.

| Stage | Core | Mechanism |
|---|---|---|
| Source | — | MQTT command topic, or the local button (which bypasses this path entirely) |
| Structure | — | `<VERB>:<counter>:<hex-tag>`, `VERB ∈ {ARM, ARM_AWAY, DISARM, STATUS}` |
| Topic filter | 0 | Non-command topics discarded |
| Parse | 0 | Malformed payloads dropped silently (§3.3) |
| Authentication | 0 | `verifySigned()`: HMAC-SHA256 over `"VERB:counter"`, 128-bit truncated tag, `ct_equal` |
| Rejection on bad tag | 0 | `cmd_badmac` / `cmd_unauth`, never enqueued |
| Dispatch | 0 → 1 | `xQueueSend(cmdQ, {verb, authed, ctr})`, depth 4 |
| Dequeue | 1 | `xQueueReceive(cmdQ, &m, 0)` — zero timeout, never blocks |
| Freshness | 1 | `m.ctr > cmdCounter`, else `cmd_replay` |
| Counter commit | 1 | `persistCounter(m.ctr)` to NVS **before** acting |
| Authorisation | 1 | `DISARM` requires `m.authed ∨ ALLOW_REMOTE_DISARM` |
| Execution | 1 | `beginArm()` / `disarm()` / `publishState()` |
| Response | 0 | Retained state publish, plus an event for the outcome |
| Failure handling | — | Every rejection path emits a distinct event; no retry, no negative acknowledgement to the sender |

**There is no command acknowledgement protocol.** A sender infers the outcome from the retained
state topic and the event stream. That is a design limitation, stated here rather than dressed up.

### 5.2 Why the counter is persisted before acting

If the device acted first and persisted afterwards, a power cut in between would leave the counter
stale and the command replayable. Persisting first means a crash can at worst burn a counter value
without executing the command, which fails safe: a legitimate sender simply increments and retries,
while an attacker gains nothing.

### 5.3 Runtime versus compile-time authorisation

`ALLOW_REMOTE_DISARM` is a **compile-time** flag, but a validly signed command is honoured even
when it is off:

```c
case Cmd::DISARM:
  if (m.authed || ALLOW_REMOTE_DISARM) { ... }
  else { emitEvent("cmd_rejected", src); }
```

The flag exists to prevent unauthenticated remote disarm. A correct HMAC tag over a fresh counter
already provides the guarantee the flag protects, so requiring both would be redundant. A
compile-time guard enforces the converse — the flag cannot be enabled without either authentication
or TLS-plus-credentials:

```c
#if ALLOW_REMOTE_DISARM && !AUTH_COMMANDS && (!MQTT_USE_TLS || !MQTT_HAS_LOGIN)
#  error "ALLOW_REMOTE_DISARM needs AUTH_COMMANDS 1, or MQTT_USE_TLS 1 with broker credentials"
#endif
```

`AlarmFSM.tla`'s `NoUnauthRemoteDisarm` is the formal statement of this rule, and mutation testing
confirms the property has force: allowing an unauthenticated disarm in the model produces a
violation.

---

## 6. Cross-references

| Topic | Document |
|---|---|
| Full implementation record, algorithms, configuration, results | `IMPLEMENTATION.md` |
| Research question, hypotheses, claims | `RESEARCH.md` |
| Verified literature survey and positioning | `RELATED_WORK.md` |
| Threats T1-T12 and mitigations | `THREAT_MODEL.md` |
| Evaluation method and the open hardware procedure | `EVALUATION.md` |
| Deployment guidance | `HARDENING.md` |
| Candidate journals, verified | `JOURNAL_TARGETS.md` |
| Simulated peer review and threats to validity | `PEER_REVIEW.md` |
