# Validation report — 2026 revision

Every Part 15 quality gate, run as an actual check with its command and output, not asserted.

Manuscript: 35 pages. Report: 100 pages. All suites pass.

---

## 1. Scientific checks

| Gate | Result | How established |
|---|---|---|
| Every contribution explicitly supported | **pass** | C1–C5 each name their evidence and the limits of that evidence; each also names what is *not* novel |
| Every mathematical symbol defined | **pass** | §1.2 of `MATHEMATICAL_MODEL_AND_PROOFS.md` tabulates every symbol with its value, unit, source identifier and **line number** in `smart_home.ino` |
| Every theorem has justified assumptions and a valid proof | **pass, with one demotion** | Theorem 1 was demoted to **Proposition 7** and reframed as a budget decomposition after two reviewers independently judged it presented above its weight. (T3) is explicitly labelled an assumption rather than a derivation |
| Every numerical result traceable to source data | **pass** | 21-row evidence matrix in `EXPERIMENTAL_EVIDENCE_AUDIT.md` §2; all 10 abstract numeric tokens checked individually |
| Every statistical result reproducible | **pass, after correction** | `mcnemar_exact` and `icc_oneway` now implemented in `analyse_ablation.py`; figures regenerate from raw records with 59 assertions |
| Every security claim respects the threat model | **pass** | Trust assumptions (broker, controller host, radio stack) now stated before Table 2; no result claimed to survive a compromised broker |
| Every formal claim respects the model boundary | **pass** | Coverage now stated quantitatively: two specifications over 1,166 firmware lines, with explicit lists of what is and is not modelled, including that **neither model represents execution time** |
| Every physical limitation clearly stated | **pass** | In the abstract, §5, §12, §14, §15 and the conclusion — not confined to a closing paragraph |
| No unsupported generalisation remains | **pass** | Corpus §11 reframed to lead with the null result; the word "framework" does not appear in the contribution list |
| No fabricated reference exists | **pass** | 23 bibitems; 5 new ones verified against publisher pages; one venue left **explicitly unasserted** rather than invented |

### Forbidden-term scan

```
grep -rniE "guaranteed real-time|complete isolation|universally secure|zero vulnerability|
production.ready|proven for all|revolutionary|unprecedented|cutting.edge|state.of.the.art|seamless"
  → no matches
```

---

## 2. Technical checks

| Gate | Result |
|---|---|
| LaTeX compiles | **pass** — manuscript 0 errors, report 0 errors |
| No undefined references | **pass** — 0 in both documents |
| No missing citations | **pass** — 23 bibitems, 23 cited keys, **0 cited-but-undefined, 0 defined-but-uncited** |
| No duplicate bibliography entries | **pass** — no duplicate `\bibitem` keys |
| No broken figures | **pass** — 8 `\includegraphics`, all resolve |
| All tables and figures referenced | **pass** — 0 unreferenced figure or table labels. 8 equation labels are unreferenced, which is conventional for numbered display equations |
| No inconsistent equations | **pass** — 0 LaTeX warnings of any kind in either build |
| PDF page layout checked | **pass** — figures on pages 9, 10, 19, 21, 21, 25, 26, 28; tables on 5, 7, 13, 15, 17, 17, 19, 20, 20, 23, 24. No float cluster at the end, which was a defect in an earlier revision |
| Fonts | **pass** — 35 fonts, **0 Type 3, 0 not embedded** |
| Supplementary material consistent with the final manuscript | **pass** — package rebuilt from the final sources in the same pass |

### Verified publisher constraints

| Constraint | Limit | Actual |
|---|---|---|
| Abstract | **250 words (hard)** | **249** |
| Keywords | ≤ 7 | 7 |
| Page or word limit | **none stated** for research articles | 35 pages |
| Highlights | 5 bullets, ≤ 85 characters | 5, longest 80 |

An intermediate edit in this revision pushed the abstract to 264 words, over the verified hard
limit. It was caught by re-measuring rather than by assumption, and tightened to 249 while keeping
the new non-monotonicity clause.

---

## 3. Verification suites, all re-run at the final commit

| Suite | Result |
|---|---|
| `tests/host/run_tests.sh` | **129 checks pass** (120 scenario + 4 build-configuration + 3 negative build-guard + 2 header-synchrony) |
| `formal/run_tlc.sh` | **3/3**: `AlarmFSM` PASS, `Isolation` PASS, `AlarmFSM_unsafe` PASS **by reporting the required violation** |
| `experiments/test_conformance.py` | all 19,529 observed transitions permitted; negative control rejected |
| `experiments/corpus/test_rule.py` | **8/8 controls pass** |
| `experiments/test_harness.py` | all metamorphic and differential properties hold |
| `experiments/validate_figures.py` | every plotted and quoted value matches the raw records |
| `experiments/check_figure_type.py` | every label clears the 6 pt floor |
| `experiments/check_figure_fit.py` | every label fits its box and the canvas |

**Campaign re-run from scratch.** The full 6,000-trial campaign and the 3,000,000-iteration fuzzing
run were re-executed in this revision. Diffing the regenerated `summary.json` against the
pre-change copy gave **exactly 10 differing leaf values, all of them the intended verdict
relabelling**. Every trial outcome reproduced identically.

---

## 4. Publication-readiness checks

| Gate | Verdict |
|---|---|
| Title accurately reflects the contribution | **pass, retained with reasons.** It leads with assumptions, names all three dimensions, says "Response-Time **Defects**" (which is what was found), and signals single-system scope with "**an** MQTT Alarm System" |
| Abstract matches the results | **pass.** Updated in this revision so the rate-limiter claim no longer presents the aggregate alone |
| Research gap supported by literature | **pass.** Five absences in §5 of `RELATED_WORK_COMPARISON.md`, each traceable to a specific verified work |
| Novelty distinguishable from prior work | **pass, and narrowed.** Vacuity detection is acknowledged as 20-plus-year-old prior art; the counter-lockout mechanism is credited to Wara and Yu with only the measurement claimed |
| Mathematical analysis adds genuine value | **pass, after revision.** It now yields $c_{\mathrm{i2c}} = 24.48$ ms by arithmetic, a latency bound of ~175 ms + interference, a feasibility verdict (160 ms infeasible), and $\partial R/\partial\lambda = 0$. The trivial result was demoted |
| Limitations transparent | **pass** |
| Journal is a verified scope fit | **partial.** Scope, article types and APC verified from publisher pages. **Quartiles and metric years could not be verified** — the indexing source returned an automated challenge, which was not circumvented |
| Not claiming Q2 readiness merely from volume of experiments | **pass.** `JOURNAL_SELECTION_2026.md` states that no quartile is asserted anywhere and that Q2 status must be confirmed by the author through institutional access |

---

## 5. What this revision changed in the science

Five substantive changes, as distinct from presentation.

**1. Two statistical errors corrected.** The ablation is a matched-pairs design — all twelve arms on
the identical seed set with the identical seed-to-attack-rate mapping — and was analysed with
Fisher's exact test, which assumes independence. Separately, the availability metric is clustered:
five attempts per trial share that trial's token-bucket phase, and 231 of 250 rate-limiter trials
admitted all five or none (ICC 0.669, design effect 3.68).

| Comparison | As reported | Corrected (McNemar exact, paired) |
|---|---|---|
| Transport arms | 9.83 × 10⁻¹¹⁹ | **5.53 × 10⁻⁷⁶** |
| Availability | 3.53 × 10⁻¹⁸⁴ | **1.93 × 10⁻³⁴** |

Conclusions unchanged; precision was overstated by ~43 and ~150 orders of magnitude, and the error
was **anti-conservative**.

**2. A real number where there had been a symbol.** $c_{\mathrm{i2c}} = 24.48$ ms, derived from the
bus clock and transfer length — both read from source — with no hardware. It yields
$L \lesssim 175$ ms + interference, and the verdict that **a 160 ms deadline is infeasible for this
firmware before interference is considered**.

**3. A tighter latency bound, and an undocumented dependency.** Because `driveOutputs` precedes
`updateDisplay`, only the interrupted pass can contain a display transaction, giving
$L \le T_{\mathrm{conf}} + R_{\mathrm{full}} + R_{\mathrm{pre}}$. **The order of two adjacent calls
is load-bearing for the deadline** and nothing in the code says so.

**4. A fifth instance of the paper's own thesis, in its own analysis code.** A Mann–Whitney test on
constant data reported "indistinguishable" — a test that cannot reject under any data, labelled as
having passed. Disclosed in prose in `summary.md` but not in `summary.json`. Both analysis scripts
now return and label the degenerate case; the statistical method is unchanged.

**5. A claim withdrawn.** The report stated the counter-induced owner lockout had not been reported
for counter-based replay protection. Wara and Yu state the mechanism as background for ZigBee frame
counters. **Withdrawn in both chapters**; only the measurement and the coupling it implies are now
claimed.

### Three new design weaknesses exposed and not fixed

1. The display refresh runs on the safety task at 24.48 ms, more than ten times the rest of the
   loop. It belongs off the safety task or chunked across passes.
2. The stage order is load-bearing and undocumented.
3. The event queue has no priority scheme and enters sustained overflow whenever the loop period is
   under 25 ms, so an alarm event can be dropped while command-rejection events are delivered.

### Honesty corrections to this revision's own work

- An earlier draft of the evidence audit said the manuscript "reports only the aggregate" for the
  rate limiter. The manuscript did state the non-monotonicity and its mechanism; what it lacked
  were the per-rate numbers. **The audit finding was overstated and is corrected in place.**
- The manuscript reported 120 host checks in two places. That is the scenario subtotal; the suite
  prints 129. **Corrected, with the breakdown given.**
- A rounding tie (1597/2000 = 79.85%) was rendered 79.8% by one tool and 79.9% by the documents.
  **All now report the fraction with two decimals**, removing the ambiguity rather than picking a
  convention.

---

## 6. Deliverables

| Part 14 item | Path | Status |
|---|---|---|
| 1 | `FINAL_SUBMISSION_PACKAGE/manuscript/FINAL_REVISED_MANUSCRIPT.pdf` | 35 pages |
| 2 | `FINAL_SUBMISSION_PACKAGE/manuscript/FINAL_REVISED_MANUSCRIPT.tex` | present |
| 3 | Complete LaTeX source and bibliography | 23 bibitems, 0 dangling |
| 4 | `docs/RESEARCH_CONTRIBUTION_AND_NOVELTY.md` | present |
| 5 | `docs/MATHEMATICAL_MODEL_AND_PROOFS.md` | present, 606 lines |
| 6 | `docs/EXPERIMENTAL_EVIDENCE_AUDIT.md` | present, 21-row evidence matrix |
| 7 | `docs/LITERATURE_REVIEW_2026.md` | present, 5 new verified references |
| 8 | `docs/RELATED_WORK_COMPARISON.md` | present, 4 comparison tables |
| 9 | `docs/THREATS_TO_VALIDITY.md` | present, 4 validity types + checklist |
| 10 | `docs/JOURNAL_SELECTION_2026.md` | present, 3 ranked candidates |
| 11 | `docs/SIMULATED_PEER_REVIEW.md` | present, 3 reviewers + editor |
| 12 | `docs/RESPONSE_TO_REVIEWERS.md` | present, all 14 items resolved |
| 13 | `REPRODUCIBILITY_GUIDE.md` | present, updated with the corrected tests |
| 14 | Updated figures and generation scripts | 8 figures regenerate byte-identically |
| 15 | This validation report | — |
| — | `docs/REFRAMING_DECISION.md` (Part 9) | present |
| — | Source archive | 245 files, 9.12 MB, extraction verified |

**Originals preserved.** `archive/pre_2026_revision/` holds the pre-revision manuscript source, its
PDF and a copy of the raw results directory, all at commit `8ae5a2b`. Nothing was overwritten.

---

## 7. Outstanding items — unchanged by this revision

Five require the author or the supervisor and **block submission**: institutional similarity
screening, supervisor approval, the dissertation-overlap ruling, the three author declarations, and
the corresponding author's email and postal address.

Non-blocking: five missing DOIs, one unverifiable venue, hardware conditions A–D, and
**confirmation of any journal's current quartile through institutional Scopus or JCR access** —
which could not be done from here and must not be inferred from a publisher's own claim.

**Nothing in this package claims supervisor approval, institutional approval, similarity clearance,
a journal quartile, or a hardware measurement. None of the five exists.**
