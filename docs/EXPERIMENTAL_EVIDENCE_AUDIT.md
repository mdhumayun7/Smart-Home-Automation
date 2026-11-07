# Experimental evidence audit

Forensic audit of the project against the source hierarchy, carried out independently of the
earlier audit documents. Every quantity below was recomputed from the raw per-trial records or
read from the implementation source; no value was copied from a previous report.

**Source hierarchy applied.** Implementation source first, then raw experiment outputs, then
formal specifications and model-checking results, then the manuscript, then prior documentation.
Where the manuscript and a raw artefact disagree, the artefact governs.

Audited at commit `8ae5a2b`. Backups of the pre-revision manuscript and raw results are in
`archive/pre_2026_revision/`.

---

## 1. What has actually been implemented

Read from `firmware/smart_home/smart_home.ino` (1,166 lines) and its headers.

| Mechanism | Implemented | Source evidence |
|---|---|---|
| Five-state alarm FSM | yes | `enum class SysState { DISARMED, EXIT_DELAY, ARMED, ENTRY_DELAY, ALARM }` (l.257) |
| Core pinning | yes | `xTaskCreatePinnedToCore(networkTask, "net", 8192, nullptr, 1, nullptr, 0)` (l.1149); safety is Arduino `loop()` on core 1 |
| Asymmetric mutex timeout | yes | safety: `xSemaphoreTake(statusMutex, 0)` (l.847); network: `pdMS_TO_TICKS(10)` (l.987) |
| Bounded command drain | yes | `CMD_DRAIN_PER_PASS = CMD_Q_LEN = 4` with two `static_assert`s (l.646–675) |
| Bounded event drain | yes | `for (int i = 0; i < 4 && xQueueReceive(eventQ, &e, 0) == pdTRUE; i++)` (l.1039) |
| Drop-oldest event overflow | yes | `emitEvent` dequeues one then enqueues on full (l.459–462) |
| HMAC-SHA256 + monotonic counter | yes | `AUTH_TAG_BYTES = 16`; counter persisted **before** acting (`persistCounter`, l.639) |
| Compile-time guard on remote disarm | yes | `#error` at l.235–239, with a named acknowledgement escape hatch |
| Compile-time guard on the published key | yes | rejects `AUTH_COMMANDS` with the demonstration key |
| Deauthentication detector | yes | `DEAUTH_WINDOW_MS = 2000`, `DEAUTH_THRESHOLD = 12`, `DEAUTH_COOLDOWN_MS = 10000` |
| **Flash encryption / secure boot** | **no** | not enabled anywhere; the flash image is readable |
| **Key rotation / revocation** | **no** | no mechanism exists |
| **Counter resynchronisation** | **no** | no path to reset the counter remotely; this is the owner-lockout cause |
| **Over-the-air update** | **no** | not implemented, so its security is neither claimed nor evaluated |

### Verified timing parameters

All read from source, not from any document: `PIR_CONFIRM_MS = 150`, `DEBOUNCE_MS = 40`,
`OLED_REFRESH_MS = 250`, `EXIT_DELAY_MS = ENTRY_DELAY_MS = 10000`, safety loop trailing
`delay(2)`, network task `vTaskDelay(pdMS_TO_TICKS(20))`, `cmdQ` capacity 4, `eventQ` capacity 16.

---

## 2. Evidence matrix

Every important claim, its evidence, and its classification. **No claim is promoted from one
category to another.**

| # | Research claim | Supporting evidence | Verification method | Evidence strength | Remaining limitation |
|---|---|---|---|---|---|
| 1 | A build guard accepting TLS + broker login as publisher authority is unsound | MQTT 3.1.1 re-origination semantics; 300-trial arm; live broker scenarios B and C | Analytical + simulation + testbed | **Strong.** Mechanism, measured cost and live-broker confirmation agree | Single protocol version; one broker implementation |
| 2 | That defect costs the safety property | 50/300 alarm activation vs 300/300 control; 246/300 disarms; Fisher *p* = 9.83 × 10⁻¹¹⁹ | Simulation, 300 trials per arm | **Strong** within the harness adversary model | Harness, not hardware; adversary model is ours |
| 3 | Availability, integrity and the safety function fail independently | 12-arm ablation, 3,600 trials, three metrics per arm | Simulation | **Strong.** Dissociation is visible in the raw records | Simulated workload; three metrics are not exhaustive |
| 4 | A token-bucket rate limit costs 41% of operator commands | 737/1,250 admitted; Fisher *p* = 3.53 × 10⁻¹⁸⁴ | Simulation | **Strong** as a proportion | **Aggregate hides a non-monotonicity** — see §5.1 |
| 5 | Broker authorisation and application-layer authentication fail under different compromises; neither dominates | 9-cell matrix; live-broker scenarios D, E vs C, E′ | Simulation + **testbed measurement** | **Strong.** The decisive pair was measured against real broker software | One broker, one version, one ACL |
| 6 | A flash dump is contained by per-client authorisation | Live scenario E: valid signature, `delivered_to_device = False` | Testbed measurement | **Strong**, and correctly attributed: the ACL, not the signature, refuses it | Contingent on deny-by-default ACL and on the device identity lacking command write |
| 7 | The layered build falls to a compromised controller host (E′) | Live `E-control` run; ablation arm `acl_hmac_controllerdump` 50/300 | Testbed + simulation | **Strong** | See §5.2 on the control/threat dual role of this run |
| 8 | A monotonic counter becomes an owner lockout under key compromise | 0/1,250 operator commands admitted in two arms | Simulation | **Strong**, and unanticipated | Mechanism explained analytically; not observed in a deployment |
| 9 | No unauthorised disarm occurs with command authentication | 6,000 campaign trials, 0 violations; exhaustive model checking | Simulation + **formally verified** | **Strong** within the model's bounds and the harness's adversary | Bounded abstraction; `MaxCtr = 4` |
| 10 | No network behaviour can block the safety task (**logical** isolation) | `SafetyCanAlwaysStep` over 660 distinct states, network task given no fairness | **Formally verified** | **Strong** — and strictly logical | Says nothing about time; see claim 12 |
| 11 | $B = 0$ for the safety task | Zero-timeout `xSemaphoreTake` in source; `Isolation.tla` | Analytical + formally verified | **Strong** for the *blocking* term | Assumes FreeRTOS honours a zero timeout (documented, not independently verified here) |
| 12 | **Physical timing invariance** | — | — | **NOT ESTABLISHED** | No hardware; no measurement exists. Claim is not made anywhere |
| 13 | Three of four interference terms are settled by construction | Response-time decomposition, `docs/TIMING_ANALYSIS.md` | **Mathematically derived** | **Moderate–strong.** Derivation is sound; $C_{\text{own}}$ is $O(1)$ but unquantified | $I_{\text{isr}} + I_{\text{mem}}$ require hardware |
| 14 | The safety loop had no static execution bound before the repair | Source history; the `while` drain; two `static_assert`s now | Analytical | **Strong** | — |
| 15 | The repair is behaviour-preserving | Campaign and fuzzing re-run; outputs byte-identical | Simulation (differential) | **Strong** | Byte-identity is over the summaries, not every intermediate |
| 16 | `NoUnauthRemoteDisarm` was vacuous as shipped | The action left `badDisarm` `UNCHANGED` on every path | **Formally verified** (by the inverted configuration) | **Strong.** The violation is now required and observed | — |
| 17 | Parser is memory-safe | 3,000,000 iterations, ASan + UBSan, no report | Simulation | **Moderate.** Host build only | Sanitizers do not exist for Xtensa; **not** evidence of authentication soundness |
| 18 | Firmware conforms to the specification | 19,529 transitions, 0 disallowed, negative control rejected | Formal + simulation | **Strong** for the modelled states | Three ablation modes only |
| 19 | Detector's shipped default was badly wrong | 1,597/2,000 benign runs triggered (79.85%) at threshold 8 | Simulation | **Strong** relative to the benign model | **The benign model is a Poisson assumption, not a capture.** See §5.3 |
| 20 | The guard pattern occurs in other projects | Rule 1: **0/135**. Rule 2: 18/135 flagged, 9 confirmed by hand | Corpus study | **Weak — existence only** | Biased corpus; **no prevalence claim is supportable** |
| 21 | The guard pattern is widespread | — | — | **NOT ESTABLISHED, and not claimed** | Rule 1 returned zero; the zero is reported as a zero |

### Classification summary

| Category | Claims |
|---|---|
| Formally verified | 9 (partly), 10, 11 (partly), 16, 18 (partly) |
| Mathematically derived | 11, 13, 14 |
| Experimentally demonstrated (testbed) | 5, 6, 7 |
| Simulated | 2, 3, 4, 8, 9, 15, 17, 19 |
| Analytically supported | 1, 13 |
| Literature-supported | the prior ESP32 interference data point only |
| Assumed | the benign management-frame arrival model (§5.3); FreeRTOS zero-timeout semantics |
| **Not established** | **12 (physical timing invariance), 21 (prevalence)** |

---

## 3. What depends on synthetic workloads or host execution

| Experiment | Environment | Consequence |
|---|---|---|
| E1, E2 campaign | host build, logical clock | **Latency is the constant 151 ms in all 6,000 trials, variance 0.0.** No timing information whatever |
| E3 ablation | host build, logical clock | Same: `safety_latency_ms ∈ {0, 151}` across all 3,600 records |
| E4 fuzzing | host build + sanitizers | Memory safety on the host, not on Xtensa |
| E5 sensitivity | simulated Poisson benign traffic | Characterises detector logic, not any real network |
| E6 broker | **real Mosquitto 2.0.18 over TLS 1.2, loopback** | Real broker software; **loopback, not a deployed network** |
| E7 corpus | static analysis of third-party source | Biased sample; no execution |
| E8 conformance | host traces vs parsed TLA+ relation | Modelled states only |
| E9 model checking | bounded abstraction | No notion of duration |

**Verified:** `sorted(set(r['safety_latency_ms'] for r in ablation.jsonl)) == [0, 151]`, and every
campaign rate reports `latency_stdev: 0.0`. Any latency claim from this data would be a claim
about the simulator.

---

## 4. Reproducibility

| Property | Status |
|---|---|
| Fixed seeds | 1000 (campaign, ablation), 7 (fuzzing); 300 distinct per-trial seeds in the ablation |
| Per-trial isolation | fork-per-trial; no state carries between trials |
| Statistics dependencies | Python standard library only — no package version can change a reported value |
| Figure values | recomputed from raw records by `validate_figures.py`, 59 assertions |
| Figure determinism | every SVG regenerates byte-identically |
| Broker verdicts | reproduced identically on a clean Mosquitto install |
| Formal results | 25 and 660 distinct states, reproduced |
| **Raw campaign JSONL** | **not committed** — only `summary.json`. Regeneration requires re-running `experiments/run.sh`. See §5.4 |

---

## 5. Audit findings

Five. Two are substantive.

### 5.1 The rate-limiter result is non-monotonic, and the manuscript reports only the aggregate

This is the most significant reporting gap found by this audit.

The aggregate figure is 737/1,250 operator commands admitted (59.0%). Broken out by attack rate,
the raw records give:

| Attack rate (cmd/s) | 10 | 100 | 1000 | 5000 | 20000 |
|---|---|---|---|---|---|
| Operator commands admitted | 82/250 | **0/250** | 155/250 | 250/250 | 250/250 |

**Availability is not monotonically decreasing in attack intensity.** A moderate flood locks the
operator out completely; an extreme flood does not affect them at all. The mechanism is in the
limiter: an arrival that finds the bucket below the admission threshold is rejected *without
consuming a token*, which pins the bucket just under the threshold and leaves enough refill for
the next legitimate arrival.

The aggregate 59% is arithmetically correct and scientifically misleading: it reads as "the
limiter degrades availability by 41%", when the measured behaviour is "the limiter can deny the
operator entirely at one attack rate and not at all at another". The per-rate table exists in
`analyse_ablation.py` output and the mechanism is explained in `docs/SECURITY_ANALYSIS.md` §9, so
this is a reporting gap in the manuscript rather than an unexamined result.

**Action:** the per-rate breakdown and the mechanism must appear in the manuscript's results, not
only the aggregate.

### 5.2 Scenario E′ is the `E-control` run, and the manuscript does not say so

In the raw broker records the eighth scenario is named `E-control`, with the recorded note:
*"the same signed command from an identity the ACL permits, to show the signature itself is valid
and the ACL is what stops scenario E"*.

The manuscript presents this run as threat scenario **E′** — a compromised controller host
holding both a permitted credential and the command key.

The reinterpretation is **sound**: the capability set is identical, since the controller identity
plus a valid signature is exactly what a compromised controller host possesses. But the run was
*designed* as a methodological control and is *reported* as a threat scenario, and the manuscript
does not disclose the dual role. A reviewer checking the artefact will find no scenario named E′.

**Action:** state the correspondence explicitly in the manuscript and in the artefact, so the
traceability is visible rather than inferred.

### 5.3 The benign traffic model in E5 is an assumption, correctly labelled

`analyse_ablation.py` states it plainly: *"The benign arrival model is an assumption, not a
measurement"* — no capture of real management traffic was available, so a Poisson arrival model
is used. This is disclosed and the disclosure is accurate.

Recorded here because the 79.85% false-positive figure is one of the paper's more quotable
numbers and its validity is conditional on that model. It characterises the detector's logic
against a stated arrival process, not its behaviour on a real network.

**No action beyond keeping the conditional phrasing** wherever the figure appears.

### 5.4 A degenerate statistical test was labelled as a pass

`experiments/analyse.py` computes a Mann–Whitney *U* test of latency under each attack rate
against the no-attack control. Because the harness advances a logical clock, every observation in
both samples is the same constant, so the rank-sum statistic has zero variance. The function
detected this and returned *p* = 1.0, and the verdict column read **"indistinguishable"** for all
five rates.

A test that cannot reject under *any* data has not found that the distributions agree. This is
the same error as the vacuous TLA+ invariant — a check incapable of failing, reported as having
passed — occurring in the project's own analysis code, and it is the fifth instance of the
pattern this research is about.

In mitigation, `summary.md` already carried the caveat in bold directly above the table: *"the
variance is zero and the test below is trivially satisfied"*. So the degeneracy was disclosed in
the human-readable summary. It was **not** disclosed in `summary.json`, whose `verdict` field any
tool or reader would take at face value.

**Action taken.** `mann_whitney_u` in `experiments/analyse.py` now returns a fourth value marking
the degenerate case, and the verdict reads *"degenerate: zero variance, test cannot reject"*, with
a `degenerate_zero_variance` flag in the JSON. The same labelling was applied to
`experiments/hardware/analyse_hw.py`. **The statistical method is unchanged** — this alters only
how a degenerate case is labelled, which is why it is compatible with that script's
pre-registration.

### 5.5 Minor: a rounding inconsistency

`analyse_ablation.py` prints the detector's false-positive rate as `0.7985` in the table and
describes it as "79.8%" in the surrounding prose. The correct rounding is 79.9%, which is the
figure used in the manuscript and the report.

---

## 6. Claims whose strength exceeds their evidence

Checked explicitly, since this is the audit's main purpose.

| Candidate overclaim | Verdict |
|---|---|
| Any physical timing or latency claim | **None found.** `grep` for latency claims in the manuscript returns only the definition of the invariance property and explicit statements that it is unmeasured |
| "Complete isolation" | **Not present.** The manuscript decomposes invariance into logical and timing isolation and attributes different evidence to each |
| Prevalence from the corpus | **Not present.** Reported as 0/135 for rule 1 and as an existence claim for rule 2 |
| Fuzzing as authentication evidence | **Correctly bounded.** The manuscript states that zero forgeries against a 128-bit tag is the expected outcome either way |
| Layered build as unconditionally secure | **Corrected earlier in the project.** E′ is now reported, and the earlier draft's "survives every case" is recorded as a retracted claim |
| Rate limiter cost | **Overclaim by omission** — see §5.1. The aggregate is defensible; presenting it alone is not |
| "indistinguishable" latency verdict | **Was an overclaim in the machine-readable artefact** — fixed, §5.4 |

---

## 7. Formal verification coverage

Honest coverage, since Part 5 forbids claiming exhaustive verification of the firmware.

| Firmware element | Modelled | Where |
|---|---|---|
| Five-state FSM and its transitions | **yes** | `AlarmFSM.tla` |
| Authenticated command acceptance, counter monotonicity | **yes** | `AlarmFSM.tla`, `ctr` |
| Unauthenticated remote disarm, as a build parameter | **yes** | `AllowUnauthDisarm` |
| Two-task structure, queue bounds, drop accounting | **yes** | `Isolation.tla` |
| Safety task enabledness under adversarial network | **yes** | `SafetyCanAlwaysStep` |
| HMAC computation itself | no | assumed correct; checked differentially against an independent implementation in `test_harness.py` |
| Command parser | no | fuzzed instead |
| NVS persistence and its failure modes | no | — |
| Detector arithmetic | no | swept instead |
| Sensor fusion, display, MQTT client, ESP-NOW | no | out of model scope |
| **Execution time** | **no** | the models have no notion of duration |

Of roughly 1,166 firmware lines, the two specifications abstract the state machine and the
task/queue structure. **The correct statement is that selected properties of a bounded abstraction
were checked exhaustively, not that the firmware was verified.**

---

## 8. Conclusions of the audit

1. Every quantitative claim in the manuscript traces to a raw artefact and recomputes correctly.
2. No physical-timing claim is made anywhere, and the distinction between logical isolation and
   timing invariance is maintained consistently.
3. The strongest evidence in the project is the live-broker E/E′ pair and the ablation's
   independence result. The weakest is the corpus study, which is correctly reported as a null
   result plus an existence claim.
4. Two reporting defects were found: the rate-limiter aggregate hiding a non-monotonicity
   (§5.1), and the undisclosed control/threat dual role of the E′ run (§5.2). Both are addressed
   in this revision.
5. One infrastructure defect was found and fixed: a degenerate test labelled as a pass (§5.4).
6. The project's central thesis now has **five** instances, four of which are in its own
   artefacts: the build guard, the vacuous invariant, the unbounded drain, the harness defects,
   and the degenerate latency test found by this audit.
