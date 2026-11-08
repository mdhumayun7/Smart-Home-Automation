# Mathematical model and proofs

A formal account of the safety path, its response time and its bounded work, derived from the
implementation rather than from a generic model. Every symbol is defined, every assumption is
named and labelled by how it was established, and every result states what it does and does not
license.

**Standing rule for this document.** No numerical value is assigned to an unmeasured quantity.
Where a number would be needed and none exists, the quantity stays symbolic. Where a figure uses
hypothetical values it is labelled an analytical illustration, never a result.

**Provenance of every constant.** All parameters below were read from
`firmware/smart_home/smart_home.ino` during this revision, with line numbers, and not copied from
any document.

---

## 1. System model

### 1.1 Entities

The firmware is modelled as two tasks, three shared objects and an environment.

| Symbol | Meaning | Source |
|---|---|---|
| $\tau_s$ | **Safety task**: the Arduino `loop()`, pinned to core 1 | `loop()`, l.1152 |
| $\tau_n$ | **Network task**: `networkTask`, pinned to core 0, priority 1 | `xTaskCreatePinnedToCore(..., 0)`, l.1149 |
| $Q_c$ | Command queue, capacity $N_c$, written by $\tau_n$, read by $\tau_s$ | `xQueueCreate(CMD_Q_LEN, ...)`, l.1095 |
| $Q_e$ | Event queue, capacity $N_e$, written by $\tau_s$, read by $\tau_n$ | `xQueueCreate(16, ...)`, l.1094 |
| $M$ | Status-snapshot mutex | `xSemaphoreCreateMutex()`, l.1096 |
| $\mathcal{I}$ | Interrupt subsystem, including the closed-source radio driver | platform |

### 1.2 Constants, with units

Every value verified from source.

| Symbol | Value | Unit | Identifier | Line |
|---|---|---|---|---|
| $T_{\mathrm{conf}}$ | 150 | ms | `PIR_CONFIRM_MS` | 84 |
| $T_{\mathrm{deb}}$ | 40 | ms | `DEBOUNCE_MS` | 85 |
| $T_{\mathrm{oled}}$ | 250 | ms | `OLED_REFRESH_MS` | 86 |
| $T_{\mathrm{exit}}, T_{\mathrm{entry}}$ | 10 000 | ms | `EXIT_DELAY_MS`, `ENTRY_DELAY_MS` | 80–81 |
| $N_c$ | 4 | entries | `CMD_Q_LEN` | 646 |
| $D_c$ | 4 | entries/pass | `CMD_DRAIN_PER_PASS` | 665 |
| $N_e$ | 16 | entries | event queue capacity | 1094 |
| $D_e$ | 4 | entries/cycle | network event drain bound | 1039 |
| $\delta_s$ | 2 | ms | trailing `delay(2)` in `loop()` | 1165 |
| $P_n$ | 20 | ms | `vTaskDelay(pdMS_TO_TICKS(20))` in `networkTask` | 1056 |
| $W$ | 2000 | ms | `DEAUTH_WINDOW_MS` | 156 |
| $\theta$ | 12 | frames | `DEAUTH_THRESHOLD` | 164 |
| $T_{\mathrm{cool}}$ | 10 000 | ms | `DEAUTH_COOLDOWN_MS` | 165 |
| $\mathrm{tag}$ | 16 | bytes | `AUTH_TAG_BYTES` (128-bit truncated) | — |

### 1.3 State and the safety function

The alarm state is $\sigma \in \Sigma = \{\textsf{Disarmed}, \textsf{ExitDelay}, \textsf{Armed},
\textsf{EntryDelay}, \textsf{Alarm}\}$ (`enum class SysState`, l.257). The persisted replay
counter is $k \in \mathbb{N}$.

The quantity of interest is the **sensor-to-siren latency**
$$L = t_{\text{siren}} - t_{\text{sensor}},$$
and the safety requirement is $L \le L_{\max}$ for a deadline $L_{\max}$ fixed by the application.

### 1.4 Ownership, which is what makes the analysis possible

| Object | Written by | Read by | Access discipline |
|---|---|---|---|
| $\sigma$, $k$ | $\tau_s$ **only** | $\tau_s$ | exclusive; no network write path exists |
| $Q_c$ | $\tau_n$ | $\tau_s$ | both zero-timeout |
| $Q_e$ | $\tau_s$ | $\tau_n$ | both zero-timeout; drop-oldest on full |
| $M$ | both | both | **asymmetric timeout**: $\tau_s$ uses 0, $\tau_n$ uses 10 ms |

**(A1) Exclusive ownership of the safety state.** $\tau_n$ never writes $\sigma$ or drives the
siren. *Established:* source inspection, and formally as `NoNetworkWrite` in `Isolation.tla`.

**(A2) Asymmetric mutex timeout.** $\tau_s$ acquires $M$ with timeout 0 (l.847); $\tau_n$ with
10 ms (l.987). *Established:* source.

**(A3) Bounded drains.** $\tau_s$ dequeues at most $D_c = N_c$ commands per pass (l.680);
$\tau_n$ dequeues at most $D_e = 4$ events per cycle (l.1039). *Established:* source, plus two
`static_assert`s that fail compilation if $D_c \neq N_c$ or $D_c \le 0$.

**(A4) Non-blocking enqueue with accounted loss.** On a full $Q_e$, `emitEvent` dequeues the
oldest and enqueues the new one (l.459–462), so the write never blocks and the loss is counted.
*Established:* source, and formally as `QueueBounded` and `NoSilentLoss`.

**(A5) FreeRTOS honours a zero timeout without blocking.** *Established:* documented API
behaviour. **Not independently verified in this work** — it is an assumption, and it is the one
assumption on which $B = 0$ rests.

---

## 2. Response-time decomposition

### 2.1 From $L$ to $R$

Let $R$ be the worst-case response time of one pass of $\tau_s$, and $P$ the loop period.

A confirmed detection requires the sensor line asserted continuously for $T_{\mathrm{conf}}$,
after which a pass observes the confirmed edge and a pass drives the output.

**Proposition 1.** $L \le T_{\mathrm{conf}} + 2R$.

*Proof.* The confirmation predicate becomes true at some instant $t_0$. The pass that evaluates it
next begins no later than $t_0$ and completes by $t_0 + R$; in the worst case the edge is
evaluated just after a pass has read the input, so the observing pass completes by $t_0 + 2R$ at
the latest, and the output is driven within that same pass by `driveOutputs`, which follows
`runStateMachine` in program order (l.1156–1160). Hence
$L \le T_{\mathrm{conf}} + 2R$. ∎

### 2.1.1 A tighter bound, and why the stage order is load-bearing

Proposition 1 is loose, and once $c_{\mathrm{i2c}}$ is known (§2.3.1) the looseness is worth
removing, because it is 24 ms wide.

The loop's program order is `readInputs`, `handleCommands`, `runStateMachine`, `wifiGuardStep`,
**`driveOutputs`**, `updateDisplay`, `copyStatusForNetwork` (l.1156–1164). The siren is asserted by
`driveOutputs`, which runs **before** `updateDisplay`. Define

- $R_{\text{full}}$ — a complete pass, including a display transaction when one is due;
- $R_{\text{pre}}$ — the prefix from `readInputs` through `driveOutputs`, which **never** includes
  the display transaction.

**Proposition 1′.** $L \le T_{\mathrm{conf}} + R_{\text{full}} + R_{\text{pre}}$.

*Proof.* In the worst case the predicate becomes true immediately after `readInputs` of some pass.
That pass must finish, costing at most $R_{\text{full}}$. The next pass then observes the edge and
asserts the siren at `driveOutputs`, costing at most $R_{\text{pre}}$. ∎

This is tighter than $T_{\mathrm{conf}} + 2R$ by one display transaction, because only the
*interrupted* pass can contain one. With $R_{\text{pre}}$ microsecond-scale and
$R_{\text{full}} \approx 24.5$ ms plus interference:

$$L \lesssim 150 + 24.5 + \varepsilon + 2(I_{\mathrm{isr}} + I_{\mathrm{mem}})
       \approx 175\ \text{ms} + \text{interference}.$$

**The stage order is therefore load-bearing for the latency bound.** Moving `updateDisplay` before
`driveOutputs` — an edit with no visible effect — would add a second display transaction to the
worst case and cost roughly 24.5 ms of latency. Nothing in the code records this, and it is exactly
the class of undocumented assumption this work is about. It belongs in a comment at the call site.

The factor 2 is an upper bound arising from phase: under a uniform phase assumption the
expectation is $T_{\mathrm{conf}} + 1.5R$. **This is an expectation under an assumed phase
distribution, not a measurement.**

### 2.2 The decomposition

One pass executes seven stages in fixed program order with no loop over unbounded data (after the
repair in §5):

$$\boxed{R = C_{\mathrm{own}} + B + I_{\mathrm{isr}} + I_{\mathrm{mem}}}$$

| Term | Meaning | Determined by |
|---|---|---|
| $C_{\mathrm{own}}$ | the pass's own computation, uncontended | design |
| $B$ | blocking on resources shared with $\tau_n$ | **design** |
| $I_{\mathrm{isr}}$ | preemption by ISRs executing on core 1 | hardware and driver |
| $I_{\mathrm{mem}}$ | stall cycles from contention for bus, cache and flash | hardware |

The decomposition is **exhaustive for this structure**: a pass can be delayed only by its own
work, by waiting for a shared resource, by preemption, or by memory-system stalls. There is no
fifth channel, because $\tau_s$ makes no synchronous call to $\tau_n$ and performs no blocking I/O
(the one I²C transaction is rate-limited, §2.3).

### 2.3 $C_{\mathrm{own}}$ is $O(1)$ per pass

| Stage | Work | Bound |
|---|---|---|
| `readInputs` | 3–4 GPIO reads, debounce arithmetic | $O(1)$ |
| `handleCommands` | at most $D_c = 4$ dequeues, each $O(1)$ | $O(1)$ by (A3) |
| `runStateMachine` | one switch, constant arithmetic | $O(1)$ |
| `wifiGuardStep` | two comparisons | $O(1)$ |
| `driveOutputs` | GPIO writes, tone control | $O(1)$ |
| `updateDisplay` | one I²C transaction, **rate-limited to one per $T_{\mathrm{oled}}$** | $O(1)$, amortised |
| `copyStatusForNetwork` | struct copy under a zero-timeout mutex | $O(1)$ |

Write $C_{\mathrm{own}} = c_0 + D_c\,c_{\mathrm{cmd}} + [\text{display pass}]\,c_{\mathrm{i2c}}$,
where $c_0$ bounds the constant stages, $c_{\mathrm{cmd}}$ one dequeue-and-dispatch, and
$c_{\mathrm{i2c}}$ one display transaction.

### 2.3.1 $c_{\mathrm{i2c}}$ derived by arithmetic, and it dominates

$c_{\mathrm{i2c}}$ **can** be bounded without hardware, from the bus clock and the transfer
length, and doing so changes the analysis materially.

From source: `Adafruit_SSD1306 display(128, 64, &Wire, -1)` (l.338) and
`Wire.setClock(400000)` (l.1079). `Adafruit_SSD1306::display()` writes the entire framebuffer.

| Quantity | Value |
|---|---|
| Framebuffer | $128 \times 64 / 8 = 1024$ bytes |
| I²C chunks of 32 bytes | 32 |
| Per chunk: address byte + `0x40` data-mode byte | $32 \times 2 = 64$ bytes |
| Bytes on the wire | 1088 |
| Bit-times at 9 per byte (8 data + ACK) | 9792 |
| **At $f_{\mathrm{scl}} = 400$ kHz** | **$c_{\mathrm{i2c}} = 24.48$ ms** |
| At 100 kHz, had the clock not been raised | 97.92 ms |

This neglects START/STOP conditions and any clock stretching, so it is a lower bound on the
transaction and the true figure is slightly larger.

**$c_{\mathrm{i2c}} = 24.48$ ms dominates $C_{\mathrm{own}}$ by more than an order of
magnitude.** Every other stage is tens of GPIO operations and constant arithmetic — microseconds.
So on a display pass, $C_{\mathrm{own}} \approx 24.5$ ms; on every other pass it is small. The
display term is not merely "the largest"; it is essentially the whole of $C_{\mathrm{own}}$.

$c_0$ and $c_{\mathrm{cmd}}$ remain symbolic: bounding them needs a cycle-accurate Xtensa model or
a measurement, and both are microsecond-scale against a 24.48 ms term, so they do not affect any
conclusion below.

### 2.4 $B = 0$, with the argument stated exactly

**Proposition 2.** Under (A1), (A2), (A3), (A5): $B = 0$ for $\tau_s$, unconditionally, and
independently of the behaviour of $\tau_n$ — including if $\tau_n$ holds $M$ indefinitely.

*Proof.* The only resource $\tau_s$ shares with $\tau_n$ that could block it is $M$. By (A2) and
(A5) the acquisition `xSemaphoreTake(statusMutex, 0)` either succeeds immediately or returns
failure immediately; on failure the stage is skipped and the pass continues (`return` at l.847).
The two queues are accessed with timeout 0 on both sides (A3, A4), so neither can block $\tau_s$
either. By (A1) there is no other shared object. Therefore no reachable state of $\tau_n$ can make
$\tau_s$ wait, and $B = 0$. ∎

**Corollary 2.1 (what this does and does not give).** The *blocking* term is zero by construction.
Priority inversion can delay $\tau_n$; it cannot delay $\tau_s$. This is the content of
`SafetyCanAlwaysStep`, verified exhaustively over 660 distinct states with $\tau_n$ granted **no
fairness at all**.

**It does not follow that $R$ is invariant to network load**, because $I_{\mathrm{isr}}$ and
$I_{\mathrm{mem}}$ are untouched by the argument. Proposition 2 is a statement about waiting, not
about time.

**Cost of the construction.** A status snapshot may be skipped. That is acceptable by design: the
snapshot feeds best-effort notification, while the siren is driven from state $\tau_s$ owns
outright by (A1).

### 2.5 The residual

$$R = \underbrace{C_{\mathrm{own}}}_{O(1),\ \text{symbolic}} + \underbrace{0}_{B}
      + \underbrace{I_{\mathrm{isr}} + I_{\mathrm{mem}}}_{\text{hardware; unmeasured}}$$

Three of four terms are settled. The residual is a **single composite hardware quantity**, and
that is what makes the pre-registered hardware experiment interpretable: with every other term
held constant by construction, a measured shift between conditions A and D is attributable to
$I_{\mathrm{isr}} + I_{\mathrm{mem}}$ and to nothing else. Without the decomposition a shift would
be attributable to any of four causes.

Why these two cannot be bounded from the source, for platform reasons rather than reasons of
effort: the ESP32 Wi-Fi driver is closed-source and its interrupt behaviour is undocumented at the
granularity a WCET analysis needs; interrupt core affinity is set by the SDK and is not guaranteed
to keep all radio work on core 0; and bus, cache and flash contention between two cores sharing
one memory subsystem is not statically analysable without a vendor timing model that is not
published.

---

## 3. A conditional deadline condition (a budget decomposition)

The useful result available without hardware is a **sufficient condition**, stated so that the
unmeasured quantity appears exactly once and the condition becomes a measurement target.

### 3.1 Assumptions

- **(T1)** (A1)–(A5) hold.
- **(T2)** $C_{\mathrm{own}} \le \bar{C}$ for a finite constant $\bar{C}$. *Justified* by §2.3
  (every stage $O(1)$, display amortised); $\bar{C}$ is **symbolic**.
- **(T3)** Interference over any single pass is bounded: $I_{\mathrm{isr}} + I_{\mathrm{mem}} \le
  \bar{I}$. **This is an assumption, not a derivation.** $\bar{I}$ is symbolic and no numerical
  value is assigned to it anywhere.
- **(T4)** $\tau_s$ is the only task pinned to core 1, so it suffers no task-level preemption —
  only ISR-level. **This is an assumption about the build and it is not verified here, which is a
  weakness.** It is true of the *application* tasks: the firmware creates exactly one task of its
  own, `networkTask`, and pins it to core 0 (l.1149), while `loop()` runs in the framework's
  `loopTask`, pinned to core 1 by the arduino-esp32 default. It is **not** true that core 1 is
  otherwise empty: the SDK maintains a per-core idle task, and an inter-processor-call task, on
  each core. The idle task cannot preempt $\tau_s$ because it runs at the lowest priority. The
  IPC task runs at a high priority and *can* preempt, but only while another core is executing a
  cross-core call, which this firmware never issues directly. Framework timer and event tasks have
  affinities set by SDK configuration that this work did not audit.

  Confirming (T4) needs a task-list dump from a running device — `uxTaskGetSystemState` or
  `vTaskList` — reporting each task's core affinity and priority. That is a two-line addition to
  the firmware and a serial capture, and it is listed in the hardware runbook as a prerequisite
  measurement rather than claimed as done. **Until then, (T4) should be read as "no application
  task preempts $\tau_s$", which is established, rather than "nothing preempts $\tau_s$", which is
  not.**

### 3.2 Theorem

> **On the status of this result.** It is presented as a *budget decomposition*, not dignified as a
> theorem. With $B = 0$ established and both remaining terms assumed bounded, the inequality below
> follows immediately from its own hypotheses, and the rearrangement into a feasibility condition is
> algebra. Its value is organisational — it collapses every design-controlled quantity into one
> symbol and isolates the hardware dependence in another — not mathematical. The substantive
> results in this document are Propositions 3–6, and Proposition 5 in particular.

**Proposition 7 (conditional deadline satisfaction).** Under (T1)–(T4),
$$R \le \bar{C} + \bar{I},$$
and consequently
$$L \le T_{\mathrm{conf}} + 2(\bar{C} + \bar{I}).$$
Hence the safety deadline $L \le L_{\max}$ is met whenever
$$\boxed{\;\bar{C} + \bar{I} \;\le\; \frac{L_{\max} - T_{\mathrm{conf}}}{2}\;}$$

*Proof.* By §2.2, $R = C_{\mathrm{own}} + B + I_{\mathrm{isr}} + I_{\mathrm{mem}}$. By
Proposition 2, $B = 0$. By (T2) and (T3) the remaining terms are bounded by $\bar{C}$ and
$\bar{I}$, giving $R \le \bar{C} + \bar{I}$. Substituting into Proposition 1 yields the latency
bound, and rearranging the requirement $T_{\mathrm{conf}} + 2(\bar{C} + \bar{I}) \le L_{\max}$
gives the stated condition. ∎

### 3.3 Interpretation, and the limit of the result

**What it gives.** A single scalar feasibility test. Every design-controlled quantity has
been collapsed into $\bar{C}$, the blocking term is gone, and the entire hardware dependence sits
in $\bar{I}$. An engineer with a deadline $L_{\max}$ and a measurement of $\bar{I}$ can decide
feasibility without re-deriving anything.

With $T_{\mathrm{conf}} = 150$ ms, the budget available to $\bar{C} + \bar{I}$ is
$(L_{\max} - 150)/2$ ms. The confirmation window, not the loop, dominates the latency budget — a
useful structural observation: $T_{\mathrm{conf}}$ is a design parameter the application chooses,
while $\bar{I}$ is not.

**What it does not give, stated plainly.**

1. It is **conditional**. (T3) assumes the per-pass interference bound it needs. The theorem
   converts "does the design meet its deadline?" into "is $\bar{I}$ small enough?", which is
   progress, not an answer.
2. It yields **no number**. $\bar{C}$ and $\bar{I}$ are symbolic, so no feasibility verdict is
   reached here.
3. It is **not** an experimentally validated real-time guarantee. A real-time guarantee requires a
   measured or certified WCET on the target. This is a conditional statement whose hypothesis is
   unverified on hardware.
4. (T3) is **exactly what the hardware experiment measures.** Conditions A–D estimate the
   distribution of $I_{\mathrm{isr}} + I_{\mathrm{mem}}$ under four load levels; the theorem is
   what makes that measurement decisive rather than merely descriptive.

**Distinction maintained.** Proposition 7 is a *conditional mathematical statement*. The project
has *no experimentally validated real-time guarantee*, and none is claimed anywhere.

---

## 4. Bounded-work and backlog analysis

Deterministic arrival and service bounds are used throughout. **No stochastic arrival model is
assumed:** the adversary's command rate is adversarial rather than random, and no capture of real
MQTT traffic was available, so a Poisson or exponential assumption would be fabricated. The
arrival-curve/service-curve formulation of network calculus is used because it needs only an upper
envelope on arrivals, which an adversary model can legitimately supply.

### 4.1 The command queue

$Q_c$ is written by $\tau_n$ and read by $\tau_s$, capacity $N_c = 4$, drain bound $D_c = 4$.

Let $A_c(t)$ be the cumulative commands offered to $Q_c$ in any window of length $t$, with arrival
curve $\alpha_c(t) \ge A_c(t)$. $\tau_s$ serves at most $D_c$ per pass with period $P$, giving
service curve $\beta_c(t) = D_c \lfloor t/P \rfloor$.

**Proposition 3 (the queue cannot grow unboundedly, and cannot block).** The backlog in $Q_c$
satisfies $q_c(t) \le N_c$ for all $t$, for every arrival process whatsoever.

*Proof.* $Q_c$ is a fixed-capacity FreeRTOS queue written with timeout 0. When full, the enqueue
*fails* and the command is discarded by $\tau_n$; it does not block and it does not grow the
queue. Hence $q_c(t) \le N_c$ identically. ∎

The consequence matters more than the bound: **overload is converted into command loss on the
network side, never into delay on the safety side.** An adversary flooding the command topic can
cause its own and the operator's commands to be dropped — which is the availability effect
measured in the ablation — but cannot lengthen a pass of $\tau_s$ beyond $D_c$ dequeues.

**Proposition 4 (single-pass drain).** Since $D_c = N_c$, any backlog present at the start of a
pass is fully drained by the end of that pass. Work arriving during a pass waits at most one
further period, so the worst-case queueing delay for an accepted command is $2P$.

*Proof.* Immediate from $D_c = N_c$ and the loop structure. ∎

**Why $D_c = N_c$ exactly, and why both `static_assert`s exist.**

- $D_c < N_c$: a full queue needs $\lceil N_c/D_c \rceil$ passes, so the delay for the last
  command depends on how full the queue was, and under sustained arrival the backlog persists for
  an unbounded number of passes.
- $D_c > N_c$: unreachable given Proposition 3, but if the capacity were later raised, the pass's
  worst case would again depend on the arrival rate — **which is precisely the defect of §5**.

$D_c = N_c$ is the unique choice making the per-pass work bound both tight and independent of
arrivals. The two `static_assert`s fail compilation if the relationship is broken, so the
analysis cannot drift from the code.

### 4.2 The event queue, and a real backlog bound

$Q_e$ is the interesting direction: written by $\tau_s$, served by $\tau_n$, capacity $N_e = 16$,
drain bound $D_e = 4$ per network cycle of period $P_n = 20$ ms.

**Service curve.** $\beta_e(t) = D_e \lfloor t / P_n \rfloor$, i.e. a long-run service rate of
$$\rho_e = D_e / P_n = 4/20\ \text{ms} = 200\ \text{events/s}.$$
This is a **best case**: it assumes the broker accepts each publication. On failure the event is
returned to the front of the queue (l.1040–1043), so the effective rate is lower and
link-dependent.

**Arrival curve.** $\tau_s$ emits events only on a state transition or a command rejection. Per
pass: at most one state transition, and at most $D_c = 4$ command rejections. So
$$\alpha_e(t) \le (1 + D_c)\left\lceil \frac{t}{P} \right\rceil = 5\left\lceil \frac{t}{P}\right\rceil .$$

**Proposition 5 (sustained-overload condition).** $Q_e$ experiences sustained overload iff the
long-run arrival rate exceeds $\rho_e$, i.e. iff
$$\frac{1 + D_c}{P} \;>\; \frac{D_e}{P_n}.$$
With $D_c = 4$, $D_e = 4$, $P_n = 20$ ms, the condition is $5/P > 0.2$ per ms, i.e.
$$P < 25\ \text{ms}.$$

**This condition is met on all but one pass in 125.** The loop's trailing `delay(2)` gives
$P \ge 2$ ms, and on a non-display pass $P \approx \delta_s + C_{\mathrm{own}} \approx 2$ ms,
far below the 25 ms threshold. The exception is the display pass: by §2.3.1 it costs
$2 + 24.48 \approx 26.5$ ms, which is *above* the threshold, so a display pass is the one pass
during which the network side can get ahead of the producer. Since the display refreshes once per
$T_{\mathrm{oled}} = 250$ ms and a non-display pass takes about 2 ms, roughly one pass in 125 is
of this kind, and the service deficit of the other 124 dominates. So in the worst
case — a sustained adversarial command flood where every dequeued command is rejected and every
rejection emits an event — **the event queue is driven into sustained overflow**, and the
drop-oldest policy of (A4) is not an edge case but the operating regime.

**Proposition 6 (the overflow is safe, and accounted).** Under sustained overflow the queue
backlog remains $q_e(t) \le N_e = 16$, $\tau_s$ is never delayed, and every produced event is
delivered, still queued, or counted as dropped:
$$\text{produced} = \text{delivered} + \text{queued} + \text{dropped}.$$

*Proof.* The bound is (A4): `emitEvent` dequeues before enqueueing, so capacity is never exceeded
and the write never blocks. The accounting identity is `NoSilentLoss`, verified exhaustively in
`Isolation.tla` over 660 distinct states. ∎

**The design consequence, which the analysis makes visible.** Notification is the component that
degrades under command flood, by design, and it degrades by losing the *oldest* events. An
operator watching the event stream during an attack sees the most recent rejections and loses the
earliest ones — including, potentially, the first evidence that an attack began. This is a real
observability limitation, it follows from the queue discipline rather than from a bug, and it is
not a safety limitation: $\sigma$ and the siren are unaffected by (A1).

### 4.3 Why the detector's cooldown is a timing mechanism

The deauthentication detector could in principle emit one event per observed frame, which would
convert a radio flood directly into an event flood and make $\alpha_e$ unbounded in $\Lambda$.

It does not, because of the cooldown: at most one report per $T_{\mathrm{cool}} = 10$ s. This
adds at most $1/T_{\mathrm{cool}} = 0.1$ events/s to $\alpha_e$, which is negligible against
$\rho_e = 200$ events/s.

$T_{\mathrm{cool}}$ is therefore **a timing mechanism as much as a usability one**, and removing it
to make the detector more responsive would break the arrival bound. This is recorded because it is
the kind of coupling that an engineer tuning the detector would not expect.

### 4.4 Starvation and priority

$\tau_s$ cannot be starved: by (T4) it is alone on core 1, and by Proposition 2 it never waits on
$\tau_n$. $\tau_n$ *can* be starved of events in the sense that it may lose them to drop-oldest,
and it can be delayed arbitrarily by a slow or dead link — both modelled adversarially in
`Isolation.tla`, where $\tau_n$ is granted no fairness and `SafetyProgress` still holds.

Event priority is **not** implemented: $Q_e$ is FIFO with drop-oldest, so an alarm event and a
command-rejection event are treated identically. Under the sustained-overflow regime of
Proposition 5 an alarm event can therefore be dropped while rejection events are delivered.
**This is a genuine design weakness exposed by this analysis and it is not fixed.** A two-queue or
priority-tagged scheme would address it. It is a notification weakness, not a safety one, since
the siren does not depend on $Q_e$.

---

## 5. The defect the analysis exposed

Writing §2.3 required establishing that every stage is constant-time. One was not.

`handleCommands` drained the queue with an unbounded loop:

```c
while (xQueueReceive(cmdQ, &m, 0) == pdTRUE) { ... }     // before
```

$\tau_s$ therefore had **no static bound on $C_{\mathrm{own}}$**. Core 0 can enqueue while core 1
dequeues, so termination rested on the drain rate exceeding the fill rate — a probabilistic
argument, and a weak one in the default build, where `AUTH_COMMANDS=0` means an enqueue costs only
a parse with no HMAC to throttle it.

The asymmetry was also backwards: $\tau_n$ already bounded its own event drain to $D_e = 4$, while
$\tau_s$ — the task whose timing the design exists to protect — bounded nothing.

The repair sets $D_c = N_c$ with the two `static_assert`s. By Proposition 4 no functional
behaviour changes, and this was **verified rather than assumed**: the full 6,000-trial campaign and
the 3,000,000-iteration fuzzing run were repeated against the modified firmware and the
regenerated outputs were byte-identical.

**Why this is the clearest argument for doing the analysis.** The defect was invisible to every
other method applied: the test suite passed, the fuzzer found nothing, the campaign reported no
violation, and the TLA+ models have no notion of duration, so they could not have caught it. It was
found by asking what bounds each stage, and finding that one stage had no answer.

---

## 6. Sensitivity and feasibility — analytical illustration only

> **Label.** Everything in this section is an **analytical illustration** computed from
> Theorem 1 with hypothetical values substituted for $\bar{C}$ and $\bar{I}$. **No value here is a
> measurement, and none is evidence about this or any device.** The purpose is to show which
> parameters the feasibility condition is sensitive to.

### 6.1 Deadline feasibility boundary

The condition is $\bar{C} + \bar{I} \le (L_{\max} - T_{\mathrm{conf}})/2$. With
$T_{\mathrm{conf}} = 150$ ms, and now with $\bar{C} \approx c_{\mathrm{i2c}} = 24.48$ ms from
§2.3.1:

| $L_{\max}$ (ms) | Budget for $\bar{C} + \bar{I}$ (ms) | Remaining for $\bar{I}$ after $\bar{C} = 24.48$ |
|---|---|---|
| 160 | 5 | **none — infeasible on the display term alone** |
| 200 | 25 | 0.5 ms |
| 250 | 50 | 25.5 ms |
| 300 | 75 | 50.5 ms |
| 500 | 175 | 150.5 ms |

**This is the most consequential number the analysis produces.** A 160 ms deadline is infeasible
for this firmware *before any interference is considered*, purely because a full-frame SSD1306
write at 400 kHz occupies the safety loop for 24.48 ms. At a 200 ms deadline the design has about
half a millisecond of interference budget, which no amount of core pinning will protect. Only at
250 ms and beyond does the interference term have room to be the interesting quantity.

The remedy is a design change the analysis points straight at: move the display refresh off the
safety task, or write it in chunks across passes. Neither was done, because this bound was derived
during the present revision in response to the observation that $c_{\mathrm{i2c}}$ did not need
hardware to compute.

The budget is linear in $L_{\max}$ with slope $1/2$, and $T_{\mathrm{conf}}$ consumes a fixed
150 ms before the loop is considered at all. **Structural reading: for any plausible $\bar{C}$ and
$\bar{I}$ on this class of device — microseconds to low milliseconds — the confirmation window
dominates the budget.** The design decision with the largest latency consequence is therefore the
choice of $T_{\mathrm{conf}}$, not anything about the loop. That conclusion is robust to the
hypothetical values, which is why it is worth stating.

### 6.2 Sensitivity to interference

Interference enters the latency bound with coefficient 2, via Proposition 1. So a per-pass
interference of $\bar{I}$ costs $2\bar{I}$ of latency. For the prior-measured order of
single-digit-percent cycle loss to matter against a 150 ms confirmation window, $\bar{I}$ would
have to reach several milliseconds per pass — which is why the pre-registered experiment is
powered to detect a shift of 0.29 SD, tens of microseconds, rather than milliseconds.
**Whether it reaches that is unmeasured.**

### 6.3 Sensitivity to the drain bound

$\partial C_{\mathrm{own}} / \partial D_c = c_{\mathrm{cmd}}$, so the per-pass cost is linear in
the drain bound. Raising $N_c$ (and hence $D_c$) buys fewer dropped commands under flood at a
linear cost in worst-case pass length. This is the single explicit trade-off the queue design
exposes, and the current choice $N_c = D_c = 4$ sits at the point where a full queue drains in one
pass.

Lowering $D_c$ below $N_c$ does not reduce the worst case usefully — it merely spreads the same
work over more passes while making the delay arrival-dependent, per §4.1.

### 6.4 Sensitivity to command arrival rate

**The most important sensitivity result, and it is a null one.** After the repair,
$$\frac{\partial R}{\partial \lambda_{\mathrm{cmd}}} = 0,$$
where $\lambda_{\mathrm{cmd}}$ is the adversary's command rate. $R$ is independent of arrival rate
because the per-pass work is capped at $D_c$ dequeues regardless of how many commands arrive, and
by Proposition 3 excess arrivals are discarded at enqueue rather than queued.

**Before the repair this derivative was not zero and had no finite bound.** That is the defect of
§5, expressed as a sensitivity.

This is also the one place where the analysis and the simulation agree on a point the simulation
could not establish alone: the ablation measured the alarm firing in 300/300 trials at every attack
rate up to 20,000 commands/s, which is consistent with $\partial R/\partial \lambda = 0$ — but the
simulation advances a logical clock, so it could not have detected a non-zero derivative. The
analysis is what makes the simulation's result interpretable rather than vacuous.

---

## 7. Summary: what is proved, what is assumed, what is unmeasured

| Result | Status | Depends on |
|---|---|---|
| Proposition 1, $L \le T_{\mathrm{conf}} + 2R$ | **derived** | program order of the loop stages |
| $R = C_{\mathrm{own}} + B + I_{\mathrm{isr}} + I_{\mathrm{mem}}$ | **derived**, exhaustive for this structure | no synchronous call, no blocking I/O |
| $C_{\mathrm{own}} = O(1)$ | **derived** | (A3), display rate limit |
| Proposition 2, $B = 0$ | **derived**, and formally verified as a logical property | (A1), (A2), (A3), **(A5)** |
| Proposition 7, conditional deadline budget | **derived**, and trivially so | (T1)–(T4), with **(T3) assumed** |
| Proposition 3, $q_c \le N_c$ | **derived** | fixed-capacity queue, zero-timeout write |
| Proposition 4, single-pass drain | **derived** | $D_c = N_c$, enforced by `static_assert` |
| Proposition 5, overload iff $P < 25$ ms | **derived** | verified constants $D_c, D_e, P_n$ |
| Proposition 6, bounded and accounted overflow | **derived**, formally verified | (A4) |
| $\partial R / \partial \lambda_{\mathrm{cmd}} = 0$ | **derived** | (A3), Proposition 3 |
| $c_{\mathrm{i2c}} = 24.48$ ms, hence $\bar{C}$ | **derived by arithmetic** | bus clock and transfer length, both read from source |
| Proposition 1′, tighter latency bound | **derived** | program order: `driveOutputs` precedes `updateDisplay` |
| $L \lesssim 175$ ms + interference | **derived**, conditional on $\bar{I}$ | §2.1.1 with §2.3.1 |
| Numerical values of $\bar{I}$, and hence of $R$ and $L$ | **UNMEASURED** | hardware |
| (T4), that *nothing* preempts $\tau_s$ | **ASSUMED, not verified** | needs a task-list dump from a device |
| Physical timing invariance | **NOT ESTABLISHED** | hardware |
| §6 tables | **analytical illustration, hypothetical inputs** | — |

### Three design weaknesses this analysis exposed and did not fix

1. **No event priority.** $Q_e$ is FIFO with drop-oldest, so under the sustained-overflow regime of
   Proposition 5 an alarm event can be dropped while command-rejection events are delivered.
2. **The cooldown is load-bearing for the arrival bound**, not merely for usability. Tuning the
   detector to report more often would invalidate §4.3.
3. **The display refresh runs on the safety task and costs 24.48 ms**, which is more than ten
   times the rest of the loop and makes a 160 ms deadline infeasible before interference is even
   considered. It should be moved to the network task or chunked across passes. **Not fixed.**
4. **The stage order is load-bearing and undocumented.** `driveOutputs` must precede
   `updateDisplay` or the worst-case latency gains a whole display transaction (§2.1.1). Nothing in
   the code says so. **Not fixed.**
5. **(T4) is assumed rather than verified**, so the no-preemption claim covers application tasks
   only.
