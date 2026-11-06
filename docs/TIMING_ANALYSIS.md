# Response-time analysis of the safety loop

A static analysis of what determines sensor-to-siren latency on this design, decomposed so that
the terms the *design* controls are separated from the terms the *hardware* controls.

This matters because the project cannot measure the hardware terms. The analysis is what turns
"we do not know the timing behaviour" into "we have bounded three of four interference terms by
construction, and here is the single quantity that must be measured." It also found a real
defect, described in Section 5.

---

## 1. Why a response-time analysis, and what it can and cannot give

Behnke et al. measured 2.15–3.8% critical-task cycle loss on an ESP32 under IP-layer load with
the network task already on the other core. That is an empirical result for one workload on one
configuration. It tells us interference exists; it does not tell us which mechanism produced it,
nor whether a different design would behave differently.

A response-time decomposition answers a different and complementary question: *of the
interference a safety task on this architecture can suffer, how much does this design eliminate
by construction, and how much is irreducibly a property of the silicon?*

**What this analysis gives:** an exact decomposition, a proof that two terms are zero or bounded
by construction, and a precise statement of the residual as a function of named hardware
parameters.

**What it does not give:** numerical values for those hardware parameters. They require
measurement. The analysis makes the measurement *smaller and better targeted*, not unnecessary.

---

## 2. Model

The safety function is the Arduino `loop()` task pinned to core 1. Let $P$ be the loop period —
the time between successive completions of one pass — and let

$$ L = t_{\text{siren}} - t_{\text{sensor}} $$

be the sensor-to-siren latency of Equation (1) in the manuscript.

A confirmed detection requires the sensor line to be continuously asserted for
$T_{\text{conf}} = \texttt{PIR\_CONFIRM\_MS} = 150$ ms, after which the next loop pass advances
the state machine and drives the output. Therefore

$$ L \;\le\; T_{\text{conf}} + 2R, $$

where $R$ is the worst-case response time of one loop pass: one pass to observe the confirmed
edge and at most one further pass before the output is driven. The factor is an upper bound; the
expected value is $T_{\text{conf}} + 1.5R$ under uniform phase.

The quantity to bound is therefore $R$, and the invariance question of Equation (2) reduces to
whether $R$ changes under radio load.

## 3. Decomposition

One pass executes seven stages in fixed order, with no loops over unbounded data after the fix in
Section 5:

$$ R \;=\; C_{\text{own}} \;+\; B \;+\; I_{\text{isr}} \;+\; I_{\text{mem}} $$

| Term | Meaning | Controlled by |
|---|---|---|
| $C_{\text{own}}$ | The loop's own computation when uncontended | Design |
| $B$ | Blocking on resources shared with the network task | **Design** |
| $I_{\text{isr}}$ | Preemption by interrupt service routines executing on core 1 | Hardware and driver |
| $I_{\text{mem}}$ | Stall cycles from contention for shared bus, cache and flash | Hardware |

### 3.1 $C_{\text{own}}$: bounded, and dominated by one stage

| Stage | Work per pass | Bound |
|---|---|---|
| `readInputs` | 3–4 GPIO reads, debounce arithmetic | $O(1)$ |
| `handleCommands` | At most `CMD_DRAIN_PER_PASS` = 4 dequeues | $O(1)$, see §5 |
| `runStateMachine` | One switch, constant arithmetic | $O(1)$ |
| `wifiGuardStep` | Two comparisons | $O(1)$ |
| `driveOutputs` | GPIO writes, tone control | $O(1)$ |
| `updateDisplay` | I²C transaction, **rate-limited to once per 250 ms** | $O(1)$, amortised |
| `copyStatusForNetwork` | Struct copy under a zero-timeout mutex | $O(1)$ |

Every stage is constant-time. The dominant term is the I²C display transaction, which is
rate-limited by `OLED_REFRESH_MS` = 250 ms, so it inflates at most one pass in every 250 ms
window. For a deadline budget of the order of $T_{\text{conf}} = 150$ ms, a single display
transaction of a few milliseconds is not close to decisive, but it is the largest single
contributor to $C_{\text{own}}$ and should be the first thing measured.

### 3.2 $B = 0$ by construction

This is the design's strongest timing property and it is worth stating precisely.

The only resource the safety loop shares with the network task is the status snapshot, guarded by
`statusMutex`. The safety loop acquires it as

```c
if (xSemaphoreTake(statusMutex, 0) != pdTRUE) return;   // never wait in the safety loop
```

A zero timeout means the call cannot block: it either acquires immediately or returns, skipping
the update until the next pass. The network task, by contrast, waits up to 10 ms
(`pdMS_TO_TICKS(10)`). Therefore:

$$ B = 0 $$

for the safety task, unconditionally and independently of what the network task does, including
if it holds the mutex indefinitely. Priority inversion can delay the network side; it cannot
delay the safety side. This is the property `SafetyCanAlwaysStep` states in `Isolation.tla`, and
TLC verifies it over 660 distinct states with the network task granted no fairness.

The cost is that a status snapshot may be skipped. That is acceptable by design: the snapshot
feeds notification, which is best-effort, while the siren is driven from state the safety loop
owns outright.

### 3.3 The queue terms are bounded, not zero

Neither queue can block the safety loop: both are accessed with a zero timeout. The command
queue contributes at most `CMD_DRAIN_PER_PASS` dequeue operations per pass, each $O(1)$. The
event queue contributes at most one enqueue per emitted event, and the number of events a single
pass can emit is bounded by the number of state transitions in a pass, which is at most one, plus
the bounded command rejections.

The deauthentication detector could in principle emit one event per observed frame. It does not,
because of the cooldown in Equation (5) of the manuscript: at most one report per
`DEAUTH_COOLDOWN_MS` = 10 s. Without that cooldown, a radio flood would convert into an event
flood and the bound would fail. The cooldown is therefore a timing mechanism as much as a
usability one.

### 3.4 $I_{\text{isr}}$ and $I_{\text{mem}}$: irreducible, and the reason hardware is needed

These two terms cannot be bounded from the source, for reasons that are properties of the
platform rather than of this project:

- The ESP32 Wi-Fi driver is **closed-source**. Mudraje et al. required substantial reverse
  engineering to model its resource consumption for worst-case *energy* analysis, and did not
  address timing. Its interrupt behaviour, and which core services which interrupt, is not
  documented at the level a WCET analysis needs.
- Core affinity of interrupts is set by the SDK and is not guaranteed to keep all radio
  interrupt work on core 0.
- Bus and cache contention between two cores sharing one memory subsystem and one flash
  controller is not statically analysable without a timing model of that subsystem, which
  Espressif does not publish.

So the honest statement is:

$$ R \;=\; \underbrace{C_{\text{own}}}_{\text{bounded, }O(1)} \;+\; \underbrace{0}_{B} \;+\;
\underbrace{I_{\text{isr}} + I_{\text{mem}}}_{\text{hardware; unmeasured}} $$

**Three of the four terms are settled by this analysis.** The residual is a single composite
hardware quantity, and the hardware experiment in `experiments/hardware/` measures exactly it:
the difference in the latency distribution between conditions A and D isolates
$I_{\text{isr}} + I_{\text{mem}}$ under radio load, because every other term is held constant by
construction.

This is why the experiment is worth running and why its result is interpretable. Without the
decomposition, a measured latency shift could be attributed to any of four causes; with it, only
one remains.

---

## 4. What the analysis predicts

A falsifiable prediction, stated before measurement, derived from the decomposition plus the one
prior data point:

> Under radio-layer load, sensor-to-siren latency will shift by at most the same order as the
> cycle loss Behnke et al. measured for IP-layer load — single-digit percent — because the
> blocking term is zero by construction and the loop's own work is constant-time. Specifically,
> we predict the median shift between conditions A and D to be under 10 ms against a
> $T_{\text{conf}}$ of 150 ms, that is, under 7% of the confirmation window, and we predict no
> missed detections.

The prediction would be **refuted** by: a median shift above 10 ms; a heavy upper tail indicating
occasional long ISR storms; or any missed detection. Any of those would show that core pinning
with queue discipline is insufficient on this platform, which would be the more consequential
result.

Note this is a prediction, not a result. It is recorded here so that it cannot be adjusted after
seeing data.

---

## 5. A defect this analysis found

Writing the decomposition required establishing that every stage of the loop is constant-time.
One was not.

`handleCommands` drained the command queue with an unbounded loop:

```c
while (xQueueReceive(cmdQ, &m, 0) == pdTRUE) { ... }     // before
```

The safety loop therefore had **no static bound on its own execution time**. The network core can
enqueue while core 1 dequeues, so the loop terminates only if the drain rate exceeds the fill
rate. That argument is probabilistic, and in the default build it is weak: with
`AUTH_COMMANDS=0` the network core performs only a parse before enqueueing, with no HMAC
computation to throttle it.

The asymmetry was also backwards. The network task already bounded its own event drain to four
per cycle, while the safety task — the one whose timing the entire design exists to protect — did
not bound its own.

The fix bounds the drain to the queue capacity:

```c
static constexpr int CMD_DRAIN_PER_PASS = 4;             // == cmdQ capacity
for (int drained = 0;
     drained < CMD_DRAIN_PER_PASS && xQueueReceive(cmdQ, &m, 0) == pdTRUE;
     drained++) { ... }                                  // after
```

A full queue still drains in one pass, so no functional behaviour changes; commands arriving
during a pass wait at most one further loop period.

**The fix was verified to be behaviour-preserving, not assumed to be.** Changing firmware in the
command path invalidates any prior reproduction claim, so the entire 6,000-trial campaign and the
3,000,000-iteration fuzzing run were repeated against the modified firmware. The regenerated
`summary.json`, `summary.md` and `fuzz.json` are **byte-identical** to the versions produced
before the change, and all 120 host checks pass. The bound therefore removes an unbounded loop
from the safety path without altering a single trial outcome.

**This is the clearest argument for doing the analysis at all.** The defect was invisible to
every other method applied to this project: the test suite passed, the fuzzer found nothing, the
campaign reported no violation, and the TLA+ model does not represent execution time, so it could
not have caught it either. It was found by asking what bounds each stage of the loop, and finding
that one stage had no answer.

---

## 6. Limitations of this analysis

- It is a **decomposition and a bound on three terms**, not a worst-case execution time. It
  yields no number for $R$.
- $C_{\text{own}}$ is shown to be $O(1)$ but is not quantified in cycles; doing so requires
  either measurement or a cycle-accurate model of the Xtensa core.
- The claim $B = 0$ is a property of the source as written and verified in the TLA+ model. It
  assumes the FreeRTOS implementation honours a zero timeout without blocking, which is its
  documented behaviour but is not independently verified here.
- The amortisation argument for the display stage assumes the I²C transaction completes within
  one pass. A hung I²C bus would violate that; the display is non-fatal on failure, but a
  *slow* rather than failed bus is not handled.
- The prediction in Section 4 extrapolates from a single prior data point measured under a
  different load class. It is a hypothesis, not an estimate.

---

## 7. Relationship to the rest of the evidence

| Method | What it establishes | What it cannot see |
|---|---|---|
| TLA+ model checking | No control- or data-flow dependency blocks the safety step | Execution time; the model has no notion of duration |
| Host test suite | Functional correctness across clock phases and configurations | Timing |
| Adversarial campaign | The implementation matches the design under attack | Timing; the clock is advanced by the harness |
| Fuzzing | Memory safety of the parser | Timing |
| **Response-time analysis** | **Which interference terms the design eliminates, and that the loop is constant-time** | **Hardware-dependent magnitudes** |
| Hardware measurement (pending) | $I_{\text{isr}} + I_{\text{mem}}$ under load | — |

Each method has a blind spot the others cover, except for the last row, which nothing else
covers. That is the structural reason the hardware experiment cannot be substituted.
