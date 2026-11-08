# Threats to validity and reproducibility

Organised by validity type, then a reproducibility checklist. Each threat states what it
endangers, what was done about it, and what remains.

Nothing here is hedging around a claim made more strongly elsewhere. Where a threat contradicts a
stronger reading of a result, the threat is correct.

---

## 1. Construct validity

*Does the measurement measure the thing the claim is about?*

### 1.1 Simulated latency measures the simulator, not the device

**The most important construct threat in this work.** The host harness advances a logical clock.
Verified directly from the raw records: `safety_latency_ms ∈ {0, 151}` across all 3,600 ablation
trials, and every campaign attack rate reports `latency_stdev: 0.0`. The latency is a constant by
construction.

Consequence: **no timing claim of any kind is supported, and none is made.** Any latency figure
from this data would describe the simulator's arithmetic.

### 1.2 A degenerate test was labelled as a pass — found and fixed in this revision

`analyse.py` ran a Mann–Whitney *U* test of latency under each attack rate against the no-attack
control. Because every observation in both samples is the same constant, the rank-sum statistic has
zero variance and the test **cannot reject under any data**. The verdict column nonetheless read
"indistinguishable" for all five rates.

A test that cannot fail has not found agreement. `summary.md` did carry the caveat in bold prose,
so the degeneracy was disclosed to a human reader; `summary.json` did not, so any tool or reader
consuming the machine-readable artefact took the verdict at face value.

**Fixed.** Both `analyse.py` and the pre-registered `analyse_hw.py` now return and label the
degenerate case, and the JSON carries a `degenerate_zero_variance` flag. The statistical method is
unchanged, which is what makes the change compatible with pre-registration.

This is the same error as the vacuous invariant, in the project's own analysis code, and it is the
fifth instance of the pattern this work is about.

### 1.3 Alarm activation is not security

In the `none`, `ratelimit` and `token` arms the alarm fires in all 300 trials, and all three are
completely defeated by capture-and-replay. A single-metric evaluation would have ranked "no command
defence" equal to a message authentication code.

**Mitigation:** three metrics are reported separately — alarm activation, operator availability and
replay resistance — and the ablation figure needs three panels for exactly this reason.

### 1.4 Zero forgeries is not evidence of authentication soundness

3,000,000 fuzz iterations producing no accepted input is the **expected** outcome against a 128-bit
tag whether the implementation is sound or not, since a chance forgery has probability 2⁻¹²⁸.

**Mitigation:** the campaign is reported as evidence of memory safety and parser robustness only,
and the manuscript says so explicitly.

### 1.5 The benign traffic model is an assumption

The detector sensitivity sweep models benign management-frame arrivals as a Poisson process. No
capture of real management traffic was available. `analyse_ablation.py` states this in its own
output: the benign arrival model is an assumption, not a measurement.

Consequence: the 79.9% false-positive figure characterises the detector's **logic against a stated
arrival process**, not its behaviour on a real network. The conditional phrasing travels with the
figure wherever it appears.

### 1.6 Aggregates can misrepresent their own result

The rate limiter's aggregate availability is 737/1,250 (59.0%). Per attack rate the figures are
82/250 at 10 commands/s, **0/250 at 100**, 155/250 at 1,000, and 250/250 at both 5,000 and 20,000.
The aggregate reads as "degrades availability by 41%"; the measured behaviour is a complete lockout
at one rate and no cost at all at two others.

**Fixed in this revision:** the per-rate breakdown and its practical consequence — a defender who
tunes against the worst flood they can generate measures no cost and meets the lockout in the field
two orders of magnitude lower — now appear in the results rather than only the mechanism.

---

## 2. Internal validity

*Could something other than the stated cause explain the result?*

### 2.1 Two statistical errors in the reported tests — found and corrected in this revision

**The design is matched pairs and was analysed as independent samples.** All twelve ablation arms
run on the identical seed set (2000–2299) with the identical seed-to-attack-rate mapping. Verified:
every arm's sorted seed list and every arm's seed→attack-rate map are equal. The analysis script's
own prose said the arms were "run on identical seeds" and then applied Fisher's exact test, which
assumes independence.

**Separately, the availability metric is clustered.** Five operator attempts per trial share that
trial's token-bucket phase. In the rate-limiter arm **231 of 250 trials admitted either all five
attempts or none** (93 at 0/5, 138 at 5/5, 19 mixed). ICC = 0.669, design effect 3.68, so 1,250
attempts carry the information of roughly **340** independent observations.

| Comparison | As reported (Fisher) | Correct (McNemar exact, paired) |
|---|---|---|
| Transport arms, alarm activation | 9.83 × 10⁻¹¹⁹ | **5.53 × 10⁻⁷⁶** |
| Availability, rate limit vs MAC | 3.53 × 10⁻¹⁸⁴ | **1.93 × 10⁻³⁴** |

Every conclusion is unchanged and both remain decisive; a cluster-robust check gives *z* = 13.6 on
a difference of 0.4104 with SE 0.0301. But the precision was overstated by roughly 43 and 150
orders of magnitude, and **the error was anti-conservative.**

**Fixed.** `mcnemar_exact` and `icc_oneway` are implemented in `analyse_ablation.py` so the
corrected figures are reproducible; McNemar is primary, the clustering is quantified in the output,
and Fisher is retained as an explicitly labelled sensitivity analysis.

### 2.2 Four defects were found in the measurement infrastructure itself

Two of the four produced results that flattered the intended conclusion.

1. **Unattributable availability.** A failed command was recorded without the reason, so a refusal
   by policy and a refusal by rate limit were indistinguishable.
2. **A token-bucket refill introduced by the first repair**, which changed the arrival pattern and
   so changed the quantity being measured.
3. **A single-attempt measurement that measured bucket phase** rather than admission rate. This is
   why the availability denominator is five attempts per trial — and, per §2.1, why those attempts
   are clustered.
4. **A 40 ms button hold against a 40 ms debounce**, a boundary condition that made the legitimate
   local path unreliable in the harness and had nothing to do with the firmware.

A fifth, in the corpus rule, is at §3.3.

**Mitigation:** every repair is accompanied by a control that would fail if the defect recurred.
That is the only reason the remaining results are reported with confidence — not because the
harness is assumed correct, but because specific named ways in which it was wrong are now tested
against.

### 2.3 A vacuous invariant passed continuous integration

`NoUnauthRemoteDisarm` was unfalsifiable in the specification that shipped: the model asserted the
refusal rather than deriving it from the build parameter, so `badDisarm` was left `UNCHANGED` on
every path. TLC reported success on every push.

**Mitigation:** the switch is now a model parameter, and a third configuration **requires** a
violation of the named invariant, matching the specific string
`Invariant NoUnauthRemoteDisarm is violated` so that a parse error cannot pass as the expected
failure.

### 2.4 The harness is not the firmware

The firmware logic is compiled against stub headers. The logic itself is unmodified — the same
`smart_home.ino`, differing only in the headers it includes — but the surrounding environment is a
model: no radio, no true parallel execution, no contention for shared silicon, no real clock.

### 2.5 E′ is a run designed as a control

The run reported as threat scenario E′ is recorded in `broker_acl.jsonl` as `E-control`, designed
to show that E's signature is genuinely valid and that the access-control list is what refuses it.
The capability set is identical to a compromised controller host, so the reinterpretation is sound,
but the run was not designed as a threat scenario.

**Fixed in this revision:** the correspondence is now stated in the manuscript rather than left to
be inferred, so a reviewer checking the artefact is not misled by the absence of a run named E′.

---

## 3. External validity

*How far do the results travel?*

### 3.1 A single system

One firmware artefact, one microcontroller, one broker. The defects found are defects in **this**
system. The *categories* — an unverified configuration assumption, a vacuous specification, an
unbounded drain — are argued to generalise; the specific instances are not claimed to.

### 3.2 The corpus is biased by construction, and the precise rule found nothing

135 projects from 22 fixed GitHub queries, ≥ 3 stars, ≤ 80 MB, excluding archived repositories and
forks. **437 projects were rejected on the star threshold alone**, plus 36 duplicates, 9 oversize
and 6 archived.

GitHub projects with stars are not deployed products: the sample over-represents educational and
hobby code and under-represents commercial firmware, which is largely not public.

- **Rule 1 returned 0 hits across 135 projects.** Reported as a zero. **No claim is made that the
  pattern is widespread.**
- Rule 2 flagged 18; manual reading gave 9 confirmed and 9 false positives. **This is an existence
  claim, not a rate.** Rule 2 over-counts monitoring projects and under-counts non-GPIO actuation —
  three of the nine confirmed cases actuate through Modbus, RF or serial frames and were caught
  only by an incidental GPIO write.

**Calibration.** Shen et al. (ISSTA 2025) report a 34% false-positive rate applying CodeQL to 258
open-source embedded projects selected almost identically, and decline population-level claims from
that larger corpus. This work's 50% (9/18) is in the expected range for such a heuristic, and its
smaller sample supports strictly less.

### 3.3 The corpus rule was wrong at first

The rule initially returned zero against **this project's own pre-repair guard**, because it treated
any mention of the authentication identifier as evidence that authentication was required — and in
the defective guard that identifier appears *negated*. Until this was found, the zero result was
meaningless.

**Mitigation:** eight controls now exist, including this project's pre-repair guard as a positive
control and its repaired guard as a negative control. All eight pass.

### 3.4 One broker, one version, one configuration

Mosquitto 2.0.18 over TLS 1.2 with a private certificate authority, on **loopback**. Scenario E's
containment depends on the ACL being deny-by-default and on the device identity lacking write
access on the command topic. A different broker, version or permissive list would change the
result. EMQX, HiveMQ, VerneMQ and AWS IoT Core were not tested and their authorisation models
differ.

Loopback also removes every network effect that a deployment has: no loss, no reordering, no
latency, no concurrent clients.

### 3.5 Platform and framework dependence

ESP32-WROOM-32 with arduino-esp32 2.0.17 and 3.3.12, which differ by roughly 175 kB of flash.
Behaviour under ESP-IDF directly, under other framework versions, or on other dual-core
microcontrollers was not evaluated. The isolation argument depends on there being two cores and on
FreeRTOS honouring a zero-timeout semaphore acquisition.

### 3.6 The closed-source radio driver

The Wi-Fi driver is closed-source and its interrupt behaviour is undocumented at the granularity a
WCET analysis needs. Interrupt core affinity is set by the SDK and is not guaranteed to keep all
radio work on core 0. This is why $I_{\mathrm{isr}}$ and $I_{\mathrm{mem}}$ cannot be bounded
statically — a platform limitation, not a limitation of effort.

---

## 4. Conclusion validity

*Do the conclusions follow from the results?*

### 4.1 No multiplicity correction is applied

Twelve arms are compared and each is a fixed, pre-declared configuration rather than a selected
subset, so none is applied. Stated so a reader can judge the decision rather than infer it. Both
primary *p*-values are far from any correction threshold, but that is a property of these results,
not a defence of the choice.

### 4.2 Statistical power is not the binding constraint, except where there is no data

Effect sizes here are extreme — 250 of 250 and 112 of 112 discordant pairs in one direction — so
power is ample for the comparisons made. The binding constraint is the **absence** of a comparison:
the timing hypothesis has no data at all, and its protocol is powered at 0.80 to detect a 0.29 SD
shift with *n* = 200 per condition.

### 4.3 Logical isolation does not imply physical timing invariance

The distinction is maintained wherever either appears, and this is the single most likely misreading
of the work. The model establishes that the safety task's enabling condition is independent of every
network-side variable, so no network behaviour can **block** it, and the asymmetric mutex timeout
makes the blocking term zero by construction. Whether the **total** loop period is invariant to
network load on real silicon is an empirical question about cache contention, bus arbitration,
interrupt latency, radio duty cycle and thermal behaviour. It has not been answered.

### 4.4 A conditional theorem is not a real-time guarantee

Theorem 1 assumes the per-pass interference bound it needs, and yields no number because
$\bar{C}$ and $\bar{I}$ are symbolic. It converts "does this design meet its deadline?" into "is
$\bar{I}$ small enough?" That is progress, not an answer, and it is not an experimentally validated
real-time guarantee.

### 4.5 Selected properties of a bounded abstraction, not a verified firmware

The two specifications abstract the state machine and the task/queue structure of a 1,166-line
firmware. Not modelled: the HMAC computation, the command parser, NVS persistence and its failure
modes, detector arithmetic, sensor fusion, display, MQTT client, ESP-NOW — and **execution time**,
which the models have no notion of. `MaxCtr = 4` bounds the counter space.

The correct statement is that **selected properties of a bounded abstraction were checked
exhaustively**, not that the firmware was verified.

---

## 5. Scope exclusions

| Excluded | Why, and what it means |
|---|---|
| Side-channel and fault-injection attack | No equipment. Power analysis against the HMAC is a known attack class and was not evaluated |
| Flash encryption and secure boot | Not enabled. The flash-dump threat is *contained* by authorisation, not *prevented* |
| Key rotation and revocation | **No mechanism exists.** A compromised key cannot be retired |
| Counter resynchronisation | **No mechanism exists.** This is the direct cause of the owner lockout |
| Over-the-air update | Not implemented, so its security is neither claimed nor evaluated |
| The controller host | Treated as trusted infrastructure. Scenario E′ is what happens when that fails, and the layered build does not survive it |
| Long-term operation | No soak test. Flash wear from counter commits, clock drift and fragmentation over months were not evaluated |
| Usability | No human-factors study. The availability figures are measured proportions; no claim is made about how users would respond |

---

## 6. Two open design problems

Identified by this work and **not fixed** in the artefact.

1. **Owner lockout under key compromise.** Two configurations admit 0 of 1,250 operator commands:
   the adversary advances the persisted replay counter beyond the operator's reach. **The mechanism
   is not new** — Wara and Yu state it as background for ZigBee frame counters, without a citation
   and without an experiment — but it had not been measured. A candidate repair, counter
   resynchronisation authenticated by the physically present local button, is **not implemented or
   evaluated**, and the obvious alternatives weaken the replay resistance the counter exists to
   provide.
2. **Scenario E′.** The layered configuration falls to a compromised controller host and survives a
   device flash dump — the opposite of the cost ordering a defender would choose, since the flash
   dump needs physical access and the controller compromise does not. Mitigation requires an
   authority that does not reside on the controller, and none is implemented.

A third weakness emerged from the bounded-work analysis in this revision: **the event queue has no
priority scheme.** It is FIFO with drop-oldest, and the analysis shows it enters sustained overflow
whenever the loop period is below 25 ms, which it always is. An alarm event can therefore be dropped
while command-rejection events are delivered. This is a notification weakness rather than a safety
one — the siren does not depend on the queue — and it is not fixed.

---

## 7. Reproducibility checklist

| Item | Status |
|---|---|
| **Source code availability** | Public repository `github.com/mdhumayun7/Smart-Home-Automation`, verified to contain every artefact cited. Archive of 213 files at `FINAL_SUBMISSION_PACKAGE/source_code/` |
| **Build instructions** | `REPRODUCIBILITY_GUIDE.md` and `README_SOURCE.md`, with the exact commands |
| **Environment versions** | GCC 13.3.0, Python 3.13.18, TLC2 2026.10.24.013619 (rev `2ef2af8`), Mosquitto 2.0.18, matplotlib 3.11.2, pdflatex TeX Live 2024, pandoc 3.1.3, arduino-esp32 2.0.17 and 3.3.12 |
| **Dependency versions** | `requirements.txt`. **All statistics are stdlib-only**, so no package version can change a reported value |
| **Dataset and corpus details** | 135-project corpus with the 22 queries, selection criteria, commit pins and rejection counts (437 stars, 36 duplicate, 9 size, 6 archived) in `corpus.json` |
| **Experiment commands** | One per experiment in `REPRODUCIBILITY_GUIDE.md` §4 |
| **Random seeds** | Fixed: 1000 (campaign, ablation), 7 (fuzzing); 300 distinct per-trial seeds 2000–2299, shared across arms — which is what makes the design paired |
| **Raw result availability** | `ablation.jsonl`, `sensitivity.jsonl`, `broker_acl.jsonl`, `fuzz.json`, `corpus.json` committed. **Raw campaign JSONL is not committed** — only `summary.json`; regeneration requires re-running `experiments/run.sh` |
| **Figure-generation commands** | `make_diagrams.py`, `make_ablation_figures.py`, with `validate_figures.py` recomputing every plotted value from raw records (59 assertions) |
| **Formal verification commands** | `formal/run_tlc.sh`, three configurations; the third **must** report a violation |
| **Expected outputs** | Stated per experiment in `REPRODUCIBILITY_GUIDE.md`, including the full 12-arm table |
| **Determinism verified** | Fork-per-trial; figure SVGs regenerate **byte-identically**; the 6,000-trial campaign was re-run from scratch in this revision and **every trial outcome reproduced identically**, the only diff being the intended verdict relabelling |
| **Broker reproducibility** | All 8 verdicts reproduced on a clean Mosquitto 2.0.18 install; only log timestamps and random client IDs differed |

### What cannot be reproduced

- **Hardware conditions A–D: never run; no data exists.** `results_hw_TEMPLATE.csv` carries the
  schema and no rows. The analysis script was verified on explicitly synthetic input as a script
  self-test, and that file was deliberately **not** committed so it cannot be mistaken for data.
- **The corpus fetch.** It depends on third-party repository state and the GitHub search API, so a
  re-fetch will not return the same 135 projects. The fetched corpus and rejection counts are
  committed so the *analysis* reproduces; the eight rule controls reproduce independently.
- **Similarity screening.** No licensed tool was available. **No similarity percentage is claimed,
  official or otherwise.**
- **Journal quartile.** The indexing source returned an automated challenge, which was **not**
  circumvented. No quartile is asserted anywhere in this work.
