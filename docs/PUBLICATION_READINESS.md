# Final publication-readiness assessment

Assessed 6 November 2026, after the decision that the author will not personally perform the
hardware measurements and will instead publish a complete independent validation framework.

**Verdict: conditionally ready.** Specifically, ready for submission to a venue that accepts
formal and simulation-based evaluation, with the physical measurement presented as an open
question supported by a public framework. Not ready for a venue that requires measured results
for the central claim.

---

## 1. What changed with the no-hardware decision

The decision forced a repositioning, and the repositioning improved the paper.

Previously the manuscript asked whether core pinning holds a safety deadline under radio load,
and then could not answer. A paper that poses a question and leaves it open is weak regardless
of how well the rest is executed.

The paper now makes three claims it can actually support, and treats the unanswerable one as a
contributed apparatus rather than a deficit:

| Position | Before | Now |
|---|---|---|
| Title | A question the paper cannot answer | Names what is delivered: verification, analysis, protocol |
| Central claim | Timing invariance (unverified) | Logical isolation (verified) plus a decomposition bounding three of four interference terms |
| Hardware | A gap | A contributed framework, with the analysis that makes its result interpretable |
| Honesty | A disclaimer | Structural: H1 and H2 are separated by the evidence each requires |

---

## 2. Two new contributions, neither requiring hardware

### 2.1 Response-time decomposition

The strongest addition. The safety loop's worst-case response time decomposes as
$R = C_{\mathrm{own}} + B + I_{\mathrm{isr}} + I_{\mathrm{mem}}$, and the analysis establishes:

- $B = 0$ **unconditionally**, because the safety loop acquires its only shared resource with a
  zero timeout. Priority inversion can delay the network task and cannot delay the safety task.
  This is the same property TLC verifies, derived independently.
- $C_{\mathrm{own}}$ is constant-time in every stage, with the dominant I²C stage rate-limited.
- The residual is a single composite hardware quantity.

This converts the open question from four unknowns to one, and makes a future measurement
*interpretable*: a measured shift can be attributed to $I_{\mathrm{isr}} + I_{\mathrm{mem}}$ and
nothing else. It also yields a pre-registered, falsifiable prediction.

**Why it matters for the no-hardware position:** it is a theoretical contribution that stands on
its own, is standard methodology in real-time systems venues, and reduces rather than restates
the gap.

### 2.2 A defect the analysis found

Establishing that every loop stage is constant-time revealed that one was not: the command queue
was drained with an unbounded loop, leaving the safety loop with no static bound on its own
execution time. Termination rested on the drain rate exceeding the fill rate, which is
probabilistic and weakest in the default build, where enqueueing costs only a parse. The drain
is now bounded to the queue capacity.

The methodological point is the valuable part. **No other technique applied to this project
could have found it:** 120 host checks passed, 3,000,000 fuzz iterations found nothing, 6,000
adversarial trials reported no violation, and the TLA+ models have no notion of execution time.
It was found by asking what bounds each stage and finding one with no answer. That is a concrete
argument for including static timing analysis alongside testing and model checking, which is
itself worth saying in a systems venue.

---

## 3. Journal suitability, honestly assessed

The question that matters for Approach A: **does the target venue accept work evaluated by
formal methods and simulation rather than physical measurement?**

### 3.1 Journal of Systems Architecture — the evidence says yes

Three verified data points:

1. **JSA published the closest competing work.** Behnke et al. (2023), vol. 140, art. 102891.
   Scope fit is demonstrated rather than argued.
2. **That paper's headline hardware mechanism was simulated, not built.** Its multiqueue NIC was
   evaluated with a Python/SimPy simulator together with an ESP32; the NIC itself was never
   fabricated, and the paper does not establish that ESP32-class radio hardware could implement
   it. JSA therefore has a direct precedent, in this exact research area, for accepting a
   simulated evaluation of a mechanism that does not physically exist.
3. **Formal verification is within scope.** The journal's stated scope covers "design
   automation, related methods and tools," and it has a publication history in embedded formal
   verification.

Our evidential position is arguably *stronger* than that precedent: our mechanism is implemented
and runs on real silicon; what is unmeasured is one timing property of it. Behnke's NIC does not
exist at all.

**Caveats that remain.** JSA's CiteScore quartile and current Guide for Authors could not be
retrieved in this environment; both must be checked directly. And the readership includes the
authors of the closest prior measurement, who will reasonably ask why a measurement needing two
£6 boards was not performed. The framework-as-contribution answer must be made explicitly in the
cover letter, not left for the reviewer to infer.

### 3.2 Alternatives

| Venue | Fit under Approach A | Note |
|---|---|---|
| **JSA** (Elsevier) | **Strong** | Precedent above. Full length suits the content. Verify quartile and author guide |
| **IEEE Embedded Systems Letters** | Moderate | "Early-stage research" remit fits, and no APC on the traditional route, but the 4-page limit (longer submissions returned without review) cannot hold a 19-page manuscript |
| **JSAN** (MDPI) | Moderate | Scope covers security and system architecture; JCR Q2; CHF 2,000 |
| **Computers** (MDPI) | Moderate | JCR Q2, CHF 1,800, broader scope |
| Real-Time Systems (Springer) | **Weak** | This readership will expect measured timing. Do not submit without hardware |

**Recommendation: JSA**, with the framework contribution argued explicitly in the cover letter.

---

## 4. Reviewer gate, re-scored

Re-running the fifteen questions from `Q2_GATE.md` under the new positioning.

| # | Question | Before | Now | Why it changed |
|---|---|---|---|---|
| 1 | Problem important to readership? | Pass | **Pass** | — |
| 2 | Gap current to 6 Nov 2026? | Partial | **Pass** | Gap narrowed and verified against the competing line |
| 3 | Primary contribution clear and non-trivial? | Partial | **Pass** | Now the verified ablation, the formal isolation model and the response-time decomposition, all complete |
| 4 | Distinguishable from closest prior work? | Pass | **Pass** | — |
| 5 | Assumptions realistic and stated? | Pass | **Pass** | — |
| 6 | Methodology detailed enough? | Pass | **Pass** | Strengthened by the decomposition |
| 7 | Baselines relevant and fair? | Partial | **Partial** | Four-design ablation, but transport security still absent |
| 8 | Experiments sufficient for every central claim? | **FAIL** | **Pass** | The central claims are now ones the experiments support; H2 is explicitly a hypothesis with a framework, not a claim |
| 9 | Physical measurement required for a headline claim? | **Blocked** | **Pass** | No headline claim now depends on it |
| 10 | Results interpreted correctly? | Pass | **Pass** | — |
| 11 | Negative results and limitations discussed? | Pass | **Pass** | Strengthened: a defect found in our own design is reported |
| 12 | Independently reproducible? | Pass | **Pass** | `REPRODUCTION.md` extends this to the hardware experiment |
| 13 | Figures necessary and accurate? | Pass | **Pass** | — |
| 14 | Citations accurate and current? | Partial | **Partial** | Two fields still unverified |
| 15 | Complies with venue scope and rules? | Partial | **Partial** | Depends on the venue decision; format port is a one-line change |

**Score: 12 Pass, 3 Partial, 0 Fail, 0 Blocked** (previously 8 Pass, 5 Partial, 1 Fail,
1 Blocked).

The Fail and the Blocked cleared not because the hardware was run, but because the paper no
longer claims anything that requires it.

---

## 5. Likely reviewer objections, and the answers

| Objection | Answer | Strength |
|---|---|---|
| "Why no hardware measurement? The boards cost £6." | Stated plainly in the limitations; the framework is contributed so any lab can perform it; the decomposition reduces what must be measured to one quantity | **Honest but will still cost something.** The most likely source of a revision request |
| "Simulation cannot establish timing." | Agreed, and stated. No timing claim is made from simulation | **Strong** |
| "The ablation's alternatives are harness models, not real systems." | Correct, and labelled. They model where a developer would place such defences | **Adequate** |
| "The sensitivity analysis uses a synthetic arrival model." | Correct, and labelled. It characterises detector logic, not a real network | **Adequate** |
| "The contribution is incremental over Behnke." | Three distinctions, each verified against the source papers: pinning never evaluated as a mitigation, all prior load is IP-layer, no adversarial or formal treatment | **Strong** |
| "TLA+ models are small." | 25 and 660 states, but mutation-tested, and the abstraction boundary is stated explicitly | **Adequate** |
| "The prediction is untested." | It is labelled a prediction and pre-registered so it cannot be adjusted later | **Strong** |
| "Single platform." | Scoped explicitly; no device-class claim is made | **Adequate** |

---

## 6. Minimum additional work before submission

| # | Item | Effort | Blocker |
|---|---|---|---|
| 1 | Verify JSA quartile via Scopus Sources and read its Guide for Authors | 20 min | Institutional access |
| 2 | Resolve two citation fields (Yun author list, Bley venue) | 20 min | IEEE Xplore / ACM DL |
| 3 | Port to the publisher template | 1 hour | Venue decision |
| 4 | Run a similarity check | 1 hour | Tool access. Expect repository self-overlap, which is explainable |
| 5 | Supervisor review of claims and venue | — | Dr. Zaveri |
| 6 | Add a transport-security arm to the ablation | 2 hours | None; can be done on request |

Items 1–5 are a day's work and none requires hardware. Item 6 is optional and would close the
remaining Partial on baseline fairness.

---

## 7. The honest bottom line

The manuscript is complete, internally consistent, fact-checked against source and committed
results, and reproducible. Its claims are now matched to its evidence.

It is **conditionally ready**: submittable to JSA or a comparable venue once items 1–5 are done,
with the understanding that a reviewer may still request the hardware measurement. If that
request comes, the framework in `REPRODUCTION.md` means it can be satisfied by anyone with two
boards, including a reviewer or a collaborator, rather than requiring the work to restart.

What this assessment does not do is guarantee acceptance. No checklist can, and a paper whose
central timing question remains open is, in candour, more likely to attract a major revision
than a straight accept. The honest framing is that this is a good paper about what it actually
did, rather than a weak paper about what it wished it had measured.
