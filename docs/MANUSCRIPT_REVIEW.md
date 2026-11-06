# Section-by-section verification report

Full-length manuscript: `paper/manuscript.tex`, 17 pages, compiles with zero errors and zero
overfull boxes. The short letters-format version is preserved at `paper/paper.tex`.

Reviewed 6 November 2026 against source code, committed experimental outputs, and verified
publication records. Each section was read, fact-checked, critically assessed, rewritten, and
checked for cross-section consistency before moving to the next.

**Status key:** Pass / Needs Improvement / Major Revision / Blocked.

---

## 1. Section status

| # | Section | Facts verified against | Reviewer status | Note |
|---|---|---|---|---|
| 1 | Title | Contribution claims | **Pass** | Rewritten. The old title asked a question the paper does not answer; it now names the mitigation and its evaluation, which is what the paper delivers |
| 2 | Abstract | All result files | **Pass** | Rewritten to lead with what Behnke established, then what remains open. States the simulation-only limit explicitly |
| 3 | Keywords | — | **Pass** | Six terms, within the five-to-six range both candidate venues accept |
| 4 | Introduction | `LITERATURE_LOG.md`, `RELATED_WORK.md` | **Pass** | Rebuilt around the three gaps that survive the literature check. Contributions each state their evidence and its limits |
| 5 | Background / Related Work | 18 verified records | **Pass** | Behnke line leads. Each distinction checked against the source paper, not assumed |
| 6 | System and Threat Model | `THREAT_MODEL.md`, source | **Pass** | New. Formalises latency and the invariance property, and splits it into logical and timing halves — this split is what makes the honesty structural rather than a disclaimer |
| 7 | Design | `smart_home.ino`, `ARCHITECTURE.md` | **Pass** | Three mechanisms each tied to a failure mode. Mutex asymmetry and counter-before-action ordering explained, both verified in source |
| 8 | Formal Verification | `formal/*.tla`, TLC output | **Pass** | State counts re-read from a fresh TLC run. Abstraction boundary stated as its own subsection |
| 9 | Implementation | Source, CI output | **Pass** | Build figures taken from CI compiler output, labelled as static sizes only |
| 10 | Experimental Methodology | `EXPERIMENTS.md` | **Pass** | Evidence categories declared up front. Hypotheses H1 and H2 separated by what evidence each needs |
| 11 | Results | `summary.json`, `ablation_summary.json`, `fuzz.json`, `sensitivity.jsonl` | **Pass** | Every number re-read from committed output. No hypothesis test reported on zero-variance data |
| 12 | Open Experiment (hardware) | `experiments/hardware/` | **Blocked** | Correctly written as a specification, not a result. Blocked on hardware, not on writing |
| 13 | Discussion | Results sections | **Pass** | Explains *why* the availability result holds (admission by validity, not arrival order) rather than restating numbers |
| 14 | Threats to Validity | All experiments | **Pass** | Construct validity named as the most serious threat, which is accurate |
| 15 | Limitations and Future Work | `EXPERIMENTS.md` §4 | **Pass** | Eight limitations, ordered priorities |
| 16 | Conclusion | Whole manuscript | **Pass** | Claims scoped to the tested platform. No number claimed that was not measured |
| 17 | Declarations | Venue requirements | **Needs Improvement** | Complete, but AI disclosure placement differs by venue: IEEE requires it in Acknowledgements, Elsevier in a declarations section. Currently satisfies both by appearing in Acknowledgements |
| 18 | References | Publisher/preprint records | **Needs Improvement** | 18 records verified. Two fields remain unverified: the full author list of Yun et al., and the proceedings name for Bley et al. |

**Totals: 15 Pass, 2 Needs Improvement, 1 Blocked.**

---

## 2. What changed and why

Substantive changes, not polish:

| Change | Reason |
|---|---|
| Title rewritten | The question form promised an answer the paper does not have |
| Gap claim rebuilt | The original was falsified by Behnke et al. (2020) |
| Positioning table restructured | Its old differentiator was exactly what Behnke measured |
| Formal model's abstraction boundary made a subsection | A reviewer reading the spec would find it; better stated than discovered |
| Statistical test moved to a pre-registered plan | Reporting $p = 1.0$ on zero-variance data invites the suspicion the authors did not understand the test |
| Ablation added | The original baseline was defeated by construction |
| Sensitivity analysis added, firmware changed | The shipped threshold was wrong by a wide margin |
| Fuzzing reframed | Zero forgeries against a 128-bit tag is expected, not evidence |
| Threat model formalised | Needed so the latency claim has a definition to be true or false of |
| Claims scoped to the tested platform | Generalisation to a device class was not supported |

---

## 3. Fact-verification record

Every quantitative claim traced to its source.

| Claim in manuscript | Source | Status |
|---|---|---|
| 2.15–3.8% / 3.17–6.67% cycle loss | Behnke et al. 2020, via Glasgow Enlighten 268149 | **Verified** |
| 93% fewer interrupts, 80% less runtime | Behnke et al. 2022, via arXiv 2201.00594 | **Verified** |
| 7.5-fold per-packet reduction; pinning not evaluated | Behnke et al. 2023, via Enlighten 297447 / arXiv 2305.01985 | **Verified** |
| 25 / 660 distinct states, depth 26 | Fresh TLC run | **Verified** |
| 6,000 trials, 2,500/2,500, 500 vs 3,000/3,000 | `summary.json` | **Verified** |
| Ablation table, all 12 cells | `ablation_summary.json`, 1,200 trials | **Verified** |
| Sensitivity table, all 7 rows | `sensitivity.jsonl`, 180 rows | **Verified** |
| 3,000,000 iterations, 0 accepted | `fuzz.json` | **Verified** |
| 793,433 B / 46,372 B; 968,221 B / 49,876 B | CI compiler output | **Verified** |
| 151 ms constant safety latency | Campaign and ablation records | **Verified** |
| ≈3 kB flash, ≈170 B RAM delta | v2.1 vs v2.2 CI comparison | **Verified** |
| $2^{-128}$ forgery probability | Analytical, from 128-bit truncation | **Verified (analytical)** |
| 120 host checks | Fresh run | **Verified** |
| Any physical latency figure | — | **Not claimed anywhere** |

---

## 4. Hardware scenario plan

The manuscript is written so either pathway is incorporated without restructuring. Sections 1–11
and 13–16 are hardware-independent. Only the items below change.

### Scenario 1 — hardware becomes available

| Item | Change |
|---|---|
| §12 heading | "The Open Experiment" → "Hardware Evaluation" |
| §12 body | Protocol stays as the method; measured distributions added as results |
| New table | Latency distribution per condition: $n$, median, IQR, min, max, standard deviation |
| New figure | Latency CDF per condition, or violin plot |
| New statistics | The pre-registered Mann–Whitney $U$ applied, with effect size |
| Abstract | "we report no latency figure" → the measured finding |
| §1 contributions | Item 5 becomes a measurement rather than a protocol |
| §10 hypotheses | H2 moves from untested to supported or refuted |
| §13 Discussion | The conditional paragraph resolves to whichever outcome occurred |
| §14 Construct validity | The principal threat is discharged |
| §15 Limitations | H1 removed from the list |
| §16 Conclusion | States the measured outcome |
| Venue | JSA becomes the strong target |

**If the measurement refutes H2** — that is, latency shifts materially under load — the paper
becomes *more* valuable, not less. It would show that the standard mitigation given to developers
of this device class is insufficient, against a large installed base. The manuscript must then be
retitled and the framing inverted, but no experiment is wasted.

### Scenario 2 — hardware does not become available

| Item | Change |
|---|---|
| §12 | Stays a specification; retitled "Specification of the Pending Measurement" |
| §1 contributions | Reordered to lead with the ablation and the formal isolation result |
| Title | Drop the question form entirely; lead with the verified contribution |
| Abstract | Opens on the design-separation finding rather than the open question |
| §15 | Hardware validation becomes the headline future direction |
| Venue | A venue accepting design-and-verification work without physical measurement. IEEE ESL's "early-stage research" remit fits, at the cost of cutting to four pages |

**Honest assessment of Scenario 2:** the paper is publishable but at a lower tier, and reviewers
at a systems journal will ask why a measurement needing two inexpensive boards was not performed.
The verified contributions — the ablation and the formal isolation model — are real but modest.

### Hardware validation checklist

| # | Step | Status |
|---|---|---|
| 1 | Two ESP32 DevKit boards | **Not acquired** |
| 2 | Logic probe or logic analyser | **Not acquired** |
| 3 | Probe firmware (`experiments/hardware/latency_probe/`) | **Written** |
| 4 | Serial collection script (`collect.py`) | **Written** |
| 5 | Analysis script (`analyse_hw.py`), pre-registered | **Written** |
| 6 | Wiring and pin map documented | **Written** (`circuit_wiring.svg`, hardware README) |
| 7 | Conditions A–C defined | **Written** |
| 8 | Condition D defined | **Written**; needs RF isolation and permission |
| 9 | Flash both boards, verify probe sees both edges | Pending |
| 10 | Pilot run, 100 trials condition A, check noise floor | Pending |
| 11 | Full run, conditions A–C | Pending |
| 12 | Repeat for variability; record raw data | Pending |
| 13 | Run pre-registered analysis | Pending |
| 14 | Generate figures from measured data | Pending |
| 15 | Compare with simulation and formal results | Pending |
| 16 | Update manuscript per Scenario 1 | Pending |

Steps 3–8 are complete. Steps 1 and 2 are the only true blockers for conditions A–C.

---

## 5. Remaining work

| Item | Blocker | Who |
|---|---|---|
| Hardware conditions A–C | Two boards, a probe | You |
| Condition D | Isolated RF, institutional permission | You and Dr. Zaveri |
| Two citation fields | IEEE Xplore / ACM DL access | You, via institution |
| Transport-security ablation arm | None; implementable in the existing harness | Can be added on request |
| Final venue decision | Depends on hardware outcome | You and Dr. Zaveri |
| Similarity check | Tool access | You. Expect repository self-overlap, which is explainable |
| Publisher template | Venue decision | One-line class change, documented in the file header |

---

## 6. Readiness

The manuscript is **complete, internally consistent and fact-checked**, and it is **not
submission-ready**, for the single reason recorded in §12 and §14: the construct the title names
is not the construct the experiments measure. That gap is closed by two boards and a probe, not
by further writing.
