# Experiment record and evidence taxonomy

Every result this project reports, classified by what kind of evidence it actually is, with the
metadata needed to reproduce or challenge it.

The categories below are **not interchangeable**. A simulation result is not a measurement, and
nothing in this repository is presented as one when it is not.

---

## 1. Evidence taxonomy

| # | Category | Used here? |
|---|---|---|
| 1 | Physical hardware measurement | **No.** Nothing in this project has been measured on a board |
| 2 | Testbed measurement | **No** |
| 3 | Simulation result | **Yes.** E2, E3, E4, E5 below |
| 4 | Emulation result | **No** |
| 5 | Formal verification result | **Yes.** E1 below |
| 6 | Analytical or theoretical result | **Yes**, in one narrow place: the 2⁻¹²⁸ forgery probability of a 128-bit tag, which is a property of the construction, not a measurement |
| 7 | Synthetic-data demonstration | **Yes.** E5's benign arrival model is synthetic and is labelled as such wherever its numbers appear |
| 8 | Literature-reported result | **Yes.** Every figure attributed to prior work in `RELATED_WORK.md` and `LITERATURE_LOG.md` keeps its citation and its original experimental context |

The single exception that matters most: **the project's headline claim is in category 1, and
category 1 is empty.** Physical sensor-to-siren latency under radio stress has not been
measured, and no number for it appears anywhere.

---

## 2. Shared environment

Unless an entry says otherwise, every experiment below was run in this environment.

| Field | Value |
|---|---|
| Code version | commit at time of run, recorded per experiment |
| OS kernel | Linux 6.18.44 |
| Compiler | g++ 13, `-O2 -std=c++17 -Wall -Wextra` |
| Python | 3.13.16, standard library only for analysis |
| Java (TLC) | OpenJDK 21.0.12.1 locally; CI uses Temurin 17. TLC results identical on both |
| TLA+ tools | tla2tools v1.8.0, pinned in `formal/run_tlc.sh` |
| Device target | ESP32 DevKit, `esp32:esp32:esp32`, arduino-esp32 2.0.17 and 3.3.12 (compiled, not run) |

**The harness compiles the unmodified firmware** against host stubs for Arduino, FreeRTOS, WiFi,
MQTT, NVS and the OLED. The firmware source is not altered for testing, which is what makes the
simulation results meaningful at all.

---

## 3. Experiment records

### E1 — Formal verification of the state machine and the isolation argument

| Field | Value |
|---|---|
| **Category** | **5. Formal verification result** |
| Objective | Prove that no unauthenticated command disarms, the counter never decreases, the siren never runs while disarmed, and the safety step stays enabled no matter what the network task does |
| Artifacts | `formal/AlarmFSM.tla`, `formal/Isolation.tla`, `.cfg` files, `formal/run_tlc.sh` |
| Parameters | `AlarmFSM`: `MaxCtr = 4`. `Isolation`: `QCap`, `MaxEvents` per `.cfg` |
| Runs | Exhaustive state-space enumeration, deterministic, no seeds |
| Raw result | `AlarmFSM` 25 distinct states. `Isolation` 2,686 states generated, 660 distinct, graph depth 26. No violations |
| Validation | **Mutation-tested.** Injecting the corresponding defect makes TLC report the expected violation, so the properties are not vacuous |
| Reproduce | `./formal/run_tlc.sh` |
| **Limitations** | The network task is abstracted to discrete actions and is **not a source of timing interference**. TLC therefore bounds the logical design space and says nothing about contention for bus, cache or interrupt controller — which is exactly where the research question lives |

### E2 — Adversarial campaign (hardened vs undefended)

| Field | Value |
|---|---|
| **Category** | **3. Simulation result** |
| Objective | Validate that the implementation matches the design under adversarial command injection |
| Artifacts | `experiments/campaign.cpp`, `experiments/analyse.py` |
| Seeds | base 1000, trial *k* uses `1000 + k`; fully deterministic |
| Parameters | 3,000 trials per build; attack rates 0, 10, 100, 1,000, 5,000, 20,000 msg/s; 500 trials per rate |
| Runs | 6,000 trials total (2 builds × 3,000) |
| Raw data | `experiments/results/campaign_*.jsonl` (git-ignored, regenerates identically) |
| Aggregates | `experiments/results/summary.md`, `summary.json` (committed) |
| Raw result | 0 attacker-caused disarms, 0 invariant violations. Baseline attacker-armed in 2,500/2,500 flooded trials, hardened 0. Legitimate command: 3,000/3,000 hardened, 500/3,000 baseline |
| Statistical treatment | **None reported.** Latency variance is identically zero, so any test is trivially satisfied and carries no information. The analysis is pre-registered for hardware instead |
| Reproduce | `cd experiments && ./run.sh` |
| **Limitations** | The security outcome follows deductively from the construction; this validates the implementation, it does not discover anything. The informative result is the availability one. The baseline is weak by construction, which is why E3 exists |

### E3 — Command-path design ablation

| Field | Value |
|---|---|
| **Category** | **3. Simulation result** |
| Objective | Answer the fair-baseline objection: compare the chosen defence against the alternatives a developer would plausibly use instead |
| Artifacts | `experiments/ablation.cpp`, `experiments/analyse_ablation.py` |
| Seeds | base 2000, trial *k* uses `2000 + k`, identical seed sequence in all four modes |
| Designs compared | `none` (no defence), `ratelimit` (token bucket, 5 commands/s), `token` (static shared secret in the payload), `hmac` (the real firmware path) |
| Runs | 300 trials per design, 1,200 total, across the same six attack rates |
| Raw data | `experiments/results/ablation.jsonl` (committed) |
| Aggregates | `experiments/results/ablation_summary.md`, `.json` |
| Reproduce | `cd experiments && ./run_ablation.sh` |
| **Limitations** | The three alternatives are **harness models of edge defences**, not firmware features — a broker rule or gateway, which is where a developer would put them. They are not implementations of any specific product. Transport security with broker credentials is **not** among the baselines and should be added before publication |

Two harness defects were found and fixed while building this experiment, both of which had
produced misleading output:

1. The attacker could act during the experimenter's own button presses and re-arm the system
   before the measurement window opened, so the replay test silently reported false negatives.
   Control actions now advance time with the attacker quiet (`stepQuiet`).
2. The attacker could leave the system mid-transition, so the intrusion phase was skipped and
   the aggregate looked as though the alarm had failed to fire in the weaker designs. It had
   not; the trial never reached the test. The system is now settled into `ARMED` quietly before
   the intrusion phase, and `intrusion_test_valid` records any trial where that failed.

### E4 — Command-parser fuzzing

| Field | Value |
|---|---|
| **Category** | **3. Simulation result** |
| Objective | Find memory-safety and undefined-behaviour defects in the one input a network peer fully controls |
| Artifacts | `experiments/fuzz_cmd.cpp` |
| Seeds | 7 |
| Parameters | 3,000,000 iterations; 6 input classes; AddressSanitizer + UndefinedBehaviorSanitizer |
| Oracle | No state change and no counter advance for any input lacking a valid tag |
| Raw result | `{"iterations":3000000,"well_formed_shapes":1500000,"accepted":0,"final_state":"ARMED","counter_advanced":false}` |
| Reproduce | `cd experiments && ./run.sh` |
| **Limitations** | Zero forgeries is the **expected** outcome against a 128-bit tag and is not independent evidence that authentication is sound. The informative content is the absence of memory-safety defects. One early "finding" was a false positive: a case-flipped hex digit decodes to identical tag bytes, so the input was the genuine command |

### E5 — Deauthentication detector parameter sensitivity

| Field | Value |
|---|---|
| **Category** | **3. Simulation result** over a **7. synthetic** arrival model |
| Objective | Measure the false-positive rate and detection latency of the detector across its parameter space, which had never been characterised |
| Artifacts | `experiments/sensitivity.cpp` |
| Seeds | 11 |
| Parameters | Thresholds 3, 5, 8, 12, 20; windows 500, 1,000, 2,000, 5,000 ms; benign rates 0.5-60 frames/min; attack rates 5-500 frames/s |
| Runs | 2,000 benign runs of 10 simulated minutes per grid cell; 500 attack runs per cell |
| Raw data | `experiments/results/sensitivity.jsonl` (committed), 180 rows |
| Reproduce | `cd experiments && ./run_ablation.sh` |
| **Limitations** | **The benign arrival model is an assumption, not a measurement.** No capture of real 802.11 management traffic was available, so Poisson arrivals at a stated rate stand in for it. These numbers characterise the detector's *logic*; they are not a false-positive rate for any real network. Obtaining one requires a passive capture on a production network and is future work |

**This experiment changed the firmware.** At threshold 8 with a 2,000 ms window — the shipped
default — the detector fired spuriously in **79.9%** of benign ten-minute runs at 60 frames per
minute, which is an ordinary busy multi-AP environment. Raising the threshold to **12** reduces
that to **0.25%** while still detecting every swept attack rate with zero misses, at a cost of
about 214 ms of extra detection latency at 20 frames/s. `DEAUTH_THRESHOLD` was changed from 8 to
12 on that evidence, with the rationale recorded at the constant.

This is the clearest case in the project of an experiment finding a real defect in a shipped
parameter rather than confirming a design.

### E6 — Build cost

| Field | Value |
|---|---|
| **Category** | **1. Physical measurement**, in the narrow sense that a real compiler measured it — but of the binary, not of the running device |
| Objective | Quantify the resource cost of the security features |
| Source | `arduino/compile-sketches` output in CI, both core versions |
| Raw result | arduino-esp32 2.0.17: 793,433 B flash (60.5%), 46,372 B RAM (14.2%). 3.3.12: 968,221 B flash (73.9%), 49,876 B RAM (15.2%). v2.2 security features add ≈3 KB flash, ≈170 B RAM over v2.1 |
| **Limitations** | Static size only. **No CPU-time, latency or energy cost has been measured**, and all three are open |

---

## 4. Experiments that have not been run

Listed so their absence is explicit rather than inferred.

| ID | Experiment | Blocked on | Why it matters |
|---|---|---|---|
| **H1** | Physical sensor-to-siren latency, conditions A-C (idle, legitimate load, command stress) | Two ESP32 boards and a logic probe | **The submission gate.** No RF isolation or permission needed |
| **H2** | Same, condition D (radio-layer stress) | Authorised isolated RF environment, institutional permission | The headline claim |
| H3 | Per-command CPU cost of HMAC verification | Hardware, or a cycle-accurate measurement | Reviewers will ask the cost of the defence |
| H4 | Energy cost of the security features and of promiscuous-mode monitoring | Hardware and a power monitor | Battery relevance |
| H5 | Real benign management-frame rate on a production network | A passive capture | Would replace E5's synthetic model with a measurement |
| H6 | False-alarm rate of the three sensor-fusion modes | Hardware with a real PIR and LD2410 | Fusion is implemented but its benefit is unquantified |
| H7 | Second platform (ESP32-C3, single-core RISC-V) | A second board | Would support any device-class claim; the single-core variant cannot pin at all and is the more interesting case |

Apparatus and protocol for H1 and H2 are committed in `experiments/hardware/`.

---

## 5. Reproduction commands

```bash
./tests/host/run_tests.sh          # 120 checks
./formal/run_tlc.sh                # E1
cd experiments && ./run.sh         # E2, E4
cd experiments && ./run_ablation.sh # E3, E5
```

All seeds are fixed. The E2 and E4 pipeline has been verified to regenerate
`summary.json`, `summary.md` and `fuzz.json` **byte-for-byte identically**.

---

## 6. Rules followed

- No result was fabricated, extrapolated, hand-edited or estimated.
- Tables and figures are generated programmatically from recorded output.
- Negative and inconclusive results are reported: E2's statistical test is uninformative and
  says so; E5 found a defect in the shipped parameters; two harness bugs in E3 are documented
  rather than quietly fixed.
- No parameter was tuned to make a result look better. The one parameter change
  (`DEAUTH_THRESHOLD`) was driven by a measured false-positive rate and its cost is stated.
- Where a claim needs hardware, it is marked pending physical validation and no simulated
  substitute is offered.
