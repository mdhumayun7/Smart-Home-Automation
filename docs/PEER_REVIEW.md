# Simulated peer review and pre-submission audit

**This is a simulated review, not an actual journal review.** It was produced internally to find
the objections a real reviewer would raise, before an editor does. It is deliberately adversarial.
Nothing here has been softened because the work is our own.

Reviewed artifact: firmware v2.2.0, `paper/paper.tex` (4 pages), `docs/` and `experiments/` at
commit `34a1d5c`. Review date: 6 November 2026.

---

## Part A — Overall assessment

**Recommendation: major revision.** At a device-level systems or security journal, submitted as it
stands, the most likely outcomes are major revision requiring new experiments, or reject. At IEEE
Embedded Systems Letters, whose stated remit is early-stage embedded research, it is a plausible
submission but reviewers will still press hard on Concern 1.

**What is genuinely strong.** The engineering is careful and the evidential discipline is unusual.
Two TLC-checked specifications, one of which models the isolation argument under an unfair
adversarial network task, is more formal rigour than most papers in this space carry. Mutation
testing the specifications is a step most authors skip and reviewers appreciate. The artifact is
reproducible to the byte, which is rare. The documentation states what has not been done rather
than blurring it. A reviewer will notice all of this.

**What stops it being publishable today.** The paper poses one research question and then does not
answer it. Everything below follows from that.

---

## Part B — Major concerns

### B1. The central research question is not answered

The paper asks whether core pinning isolates the safety function on a single-chip Wi-Fi SoC when
the chip's own radio driver is attacked. It then establishes, formally and in simulation, that no
*code path* makes the safety response depend on network input. That is a different and much weaker
claim than the one in the title.

The question is about **contention on shared silicon** — cache, bus, interrupt controller, the
closed-source radio driver's ISR behaviour. None of that exists in a host harness. A reviewer will
read the title, look for a latency distribution under radio stress, not find one, and stop there.

This is not a presentational problem that can be fixed by rewording. Either the measurement is
made, or the paper's claim must retreat to "we formally verify logical isolation and specify a
protocol for measuring timing isolation", which is a substantially less interesting contribution
and probably not enough for a Q2 systems journal on its own.

**Required:** run hardware conditions A–C at minimum. These need two ESP32 boards and a logic
probe, no RF isolation, no clearance. Condition D can remain future work with justification.

### B2. The statistical analysis is vacuous as presented

`summary.md` reports Mann-Whitney U with `U = 125000`, `z = 0`, `p = 1.0` at every attack rate.
`U = n₁n₂/2` exactly, because the simulated latency has zero variance — every trial returns
151 ms.

The documentation is honest about this, and that honesty is to its credit. But a reviewer will ask
why a hypothesis test is reported at all. Running a test on two identical constant-valued samples
is not evidence of indistinguishability; it is an arithmetic identity. Presenting it in a results
table invites the suspicion that the authors either did not understand the test or hoped the reader
would not look.

**Required:** remove the test from the results table, or move it to the methods section as "the
analysis that will be applied to hardware data, pre-registered here", which is a legitimate and
even admirable framing. Keep the caveat text either way.

### B3. The baseline is a straw man

The comparison is "no command authentication" versus "HMAC-SHA256 with a replay counter". The
result — that an attacker can arm an unauthenticated system and cannot arm an authenticated one —
is a deductive consequence of the design, not an empirical finding. 2,500 of 2,500 versus 0 of
2,500 is what a correct implementation must produce. Six thousand trials do not add information to
a claim that follows from the construction.

What the campaign *does* usefully establish is the **availability** result: the legitimate command
is starved in every flooded baseline trial and succeeds in 3,000 of 3,000 hardened trials. That is
less obvious and worth foregrounding, because it is about queue discipline rather than
cryptography.

**Required:** either reframe the campaign as a validation-of-implementation exercise rather than a
scientific comparison, or add a baseline that is not trivially defeated. Candidates: TLS with
broker authentication but no application-layer signing; a rate-limiting defence; 802.11w PMF at
the link layer. Comparing against alternative *mitigations* is the comparison a reviewer wants.

### B4. Novelty is thin as framed

"No prior work measures a safety deadline on a SoC whose own radio driver is the attacked resource"
is a true and verified gap. But a gap in the literature is not automatically a contribution. A
reviewer may reasonably respond that the gap exists because the answer is uninteresting or
predictable, and will want to know what we expect to *learn*.

The paper would be far stronger if it stated a falsifiable prediction with a mechanism behind it —
for example, that Wi-Fi driver ISR activity on core 0 will inflate core 1's worst-case latency by a
bounded amount through shared-bus and cache interference, with an expected magnitude. Then the
measurement either confirms or refutes something. At present the hypothesis is "nothing will
happen", which is hard to make exciting even if true.

**Required:** sharpen the hypothesis into a mechanism-backed prediction with an expected effect
size. This also fixes B1's framing problem.

### B5. Single platform, single vendor, one configuration

All claims concern one SoC family, one RTOS, one Wi-Fi stack and one application. Generalisation to
"single-chip Wi-Fi SoCs" as a class is not supported. The ESP32-C3 (RISC-V, single core) and
ESP32-S3 would behave differently, and the single-core variant is arguably the more interesting
case because it cannot pin at all.

**Required:** scope the claims to the tested platform explicitly in the abstract and conclusion, or
add a second platform.

---

## Part C — Moderate concerns

### C1. The formal models may be too abstract to carry the weight placed on them

25 and 660 distinct states are small. A reviewer who reads `Isolation.tla` will ask what the
abstraction discards: it models the network task as a small set of discrete actions
(`NetGoBusy`, `NetStall`, `NetCrash`, …), not as a source of timing interference. So the model
proves that *in the abstraction*, the safety step stays enabled. The abstraction is exactly where
the timing question lives, and the model cannot see it.

The mutation testing helps and should be kept — it shows the properties are not vacuous. But the
paper should state the abstraction boundary explicitly rather than let a reader infer that TLC has
settled the isolation question.

### C2. The fuzzing result is near-tautological

3,000,000 iterations against a parser guarded by a 128-bit truncated HMAC, finding zero accepted
inputs, is the expected outcome; a forgery would require roughly 2¹²⁸ attempts. The result
genuinely demonstrates memory safety under ASan and UBSan, which is worth stating, but it should be
presented as *absence of memory-safety defects*, not as evidence that authentication works. The
corpus-design story (the case-insensitive hex bit-flip that produced a valid command) is more
interesting than the headline number and deserves the space.

### C3. No resource or energy cost reported

Security features have a cost. Flash and RAM deltas are reported from compiler output (+≈3 KB,
+≈170 B), which is good, but there is no CPU-time cost for HMAC verification per command, no energy
measurement, and no analysis of what the deauth detector's promiscuous-mode monitoring costs in
power or airtime. For a battery-relevant device class a reviewer will ask.

### C4. No sensitivity analysis

Parameters such as `DEAUTH_THRESHOLD` (8), `DEAUTH_WINDOW_MS` (2000), `PIR_CONFIRM_MS` (150) and
`FUSION_WINDOW_MS` (1500) are fixed with stated rationale but no sensitivity study. The deauth
detector's false-positive rate under ordinary network churn is unmeasured, and a detector that
cries wolf is worse than none.

### C5. No ablation

With four independent security mechanisms (authentication, replay counter, deauth detection, ESP-NOW
fallback) and three fusion modes, an ablation showing each mechanism's individual contribution is
both feasible in simulation and expected by reviewers.

---

## Part D — Minor concerns

| # | Concern |
|---|---|
| D1 | Four pages is thin for a full journal article. Appropriate for IEEE ESL, under-length elsewhere |
| D2 | One citation (`fuzzsurvey2022`) carries an unverified author list and is cited as "et al."; resolve it before submission |
| D3 | `pemu2025` is cited as "ACM, 2025" with a DOI rather than a named venue; confirm the proceedings name |
| D4 | The campaign figure is good (colourblind- and greyscale-safe, validated ΔE) but is the only results figure. A latency distribution plot is needed once hardware data exists |
| D5 | No graphical abstract or highlights, required or requested by several candidate journals |
| D6 | Demo keys are published in `secrets.example.h`. Correct practice, but state explicitly in the paper that evaluation used freshly generated keys |
| D7 | The 151 ms constant latency deserves a one-line explanation in the results (it is `PIR_CONFIRM_MS` plus loop overhead), otherwise it reads as suspicious |

---

## Part E — Threats to validity

Written as the paper's own threats section should be written.

### E1. Construct validity

The dependent variable in simulation is *logical* latency measured on a synthetic clock the harness
itself advances. It is named "safety latency" but it does not measure the physical quantity of
interest. The construct and the measure diverge, and this is the single largest validity threat in
the current work.

### E2. Internal validity

Mitigated well. Per-trial process isolation via `fork()` was introduced precisely because global
state leaked between trials and produced a false violation — an internal-validity threat that was
found and fixed rather than missed. Seeds are fixed, the pipeline reproduces byte-identically, and
CI re-runs a reduced version on every push. Remaining threat: the harness stubs are written by the
same author as the firmware, so a shared misconception could be invisible to both.

### E3. External validity

Limited. One SoC, one core version pair (2.0.17 and 3.3.12), one application, no deployment, no
field data, no real sensors. Claims about "consumer intrusion alarms" generally rest on the premise
that this design is representative, which is argued but not demonstrated.

### E4. Conclusion validity

The statistical conclusion is unsupported as presented (B2). The formal conclusions are sound within
their abstraction but that abstraction excludes the phenomenon under study (C1). The security
conclusions follow deductively from the construction rather than from the experiment (B3), which
makes them valid but uninformative.

### E5. Bias and confounding

No blinding, and the analysis author is the implementation author. In simulation this matters less
than it would for hardware measurement, where expectancy effects on setup and outlier handling are
real. For the hardware campaign, the measurement protocol should be fixed in writing before data
collection, and the analysis script committed before the first run — both are already the case in
`experiments/hardware/`, which is good practice and should be stated in the paper as
pre-registration.

---

## Part F — Desk-reject risks, prioritised

| Risk | Severity | Fix |
|---|---|---|
| Central claim untested on hardware | **Critical** | Run conditions A–C |
| Scope mismatch at a sensing-focused journal | High | Choose JSAN or IEEE ESL over *Sensors* |
| Under-length for a full journal article | Medium | Target IEEE ESL, or expand with hardware results and ablation |
| Vacuous statistics in the results table | Medium | Move the test to methods as pre-registered analysis |
| Missing journal declarations | Low | Covered by the submission package |
| Unverified citation fields | Low | Resolve D2 and D3 |

---

## Part G — Prioritised action plan

**Before any submission:**

1. Run hardware conditions A–C and fold the measured distributions into the results. *(Fixes B1,
   E1, partially B4.)*
2. Move the Mann-Whitney test to methods as a pre-registered analysis. *(Fixes B2, E4.)*
3. Reframe the campaign as implementation validation plus an availability result, and add at least
   one non-trivial baseline. *(Fixes B3.)*
4. State the formal models' abstraction boundary explicitly. *(Fixes C1.)*
5. Scope all claims to the tested platform. *(Fixes B5.)*
6. Resolve the two unverified citation fields. *(Fixes D2, D3.)*

**Strongly recommended:**

7. Sharpen the hypothesis into a mechanism-backed prediction with an expected effect size. *(B4.)*
8. Add an ablation over the four security mechanisms. *(C5.)*
9. Add a sensitivity study over the detector and sensor parameters, including a false-positive rate
   for the deauth detector under ordinary churn. *(C4.)*
10. Report the per-command CPU cost of HMAC verification. *(C3.)*

**Optional:**

11. Second platform (ESP32-C3) to support the device-class claim. *(B5.)*
12. Energy measurement. *(C3.)*

Items 1–6 are the submission gate. Items 7–10 are what move a paper from "accepted after major
revision" toward "accepted with minor revision".

---

## Part H — Response-to-reviewers template

For use if the paper is submitted and receives comments. One row per reviewer point.

| ID | Reviewer point (verbatim) | Our response | Change made | Location in revised manuscript |
|---|---|---|---|---|
| R1.1 | | | | |
| R1.2 | | | | |
| R2.1 | | | | |

Conventions to follow when filling it in:

- Quote the reviewer verbatim; never paraphrase a criticism into something easier to answer.
- State plainly where you disagree, with evidence. Reviewers respect a defended position more than
  capitulation on a point you believe is wrong.
- Where a requested experiment is genuinely out of reach, say so and explain why, rather than
  promising it vaguely.
- Give exact section, page and line numbers for every change.

### Revision tracking table

| # | Concern | Source | Status | Evidence of fix |
|---|---|---|---|---|
| B1 | Central claim untested on hardware | Internal review | Open | — |
| B2 | Vacuous statistical test in results | Internal review | Open | — |
| B3 | Straw-man baseline | Internal review | Open | — |
| B4 | Novelty framing | Internal review | Open | — |
| B5 | Single-platform generalisation | Internal review | Open | — |
| C1 | Formal abstraction boundary unstated | Internal review | Open | — |
| C2 | Fuzzing result near-tautological | Internal review | Open | — |
| C3 | No resource or energy cost | Internal review | Open | — |
| C4 | No sensitivity analysis | Internal review | Open | — |
| C5 | No ablation | Internal review | Open | — |
| D2 | Unverified citation author list | Internal review | Open | — |
| D3 | Unconfirmed venue for pemu2025 | Internal review | Open | — |
| D7 | 151 ms constant unexplained | Internal review | Open | — |

---

## Part I — What this review does not do

It does not guarantee acceptance anywhere, and no checklist can. It does not substitute for your
supervisor's judgement about venue or about whether this work should be submitted as a journal
article at all rather than a workshop paper, which may be the better first step. And it is not an
actual review: a real reviewer may raise concerns absent here, or care little about concerns listed
here.
