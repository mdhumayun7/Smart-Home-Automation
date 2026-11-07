# Final submission checklist

Status of every submission requirement at commit `5fbe123`. Each row carries the evidence that
established it, not an assertion that it is done.

**Summary: the academic report is complete. The journal manuscript is not submission-ready.**
Seven items are outstanding, six of which require the author or the supervisor and cannot be
resolved by further work on the repository.

---

## 1. Deliverables

| # | Deliverable | Path | Status |
|---|---|---|---|
| 1 | Journal manuscript, PDF | `FINAL_SUBMISSION_PACKAGE/manuscript/FINAL_MANUSCRIPT.pdf` | 31 pages, built clean |
| 2 | Manuscript source | `FINAL_SUBMISSION_PACKAGE/manuscript/manuscript.tex` | present |
| 3 | Research and implementation report, PDF | `FINAL_SUBMISSION_PACKAGE/report/COMPLETE_RESEARCH_AND_IMPLEMENTATION_REPORT.pdf` | **98 pages**, built clean |
| 4 | The same report, editable | `…/COMPLETE_RESEARCH_AND_IMPLEMENTATION_REPORT.docx` | pandoc 3.1.3, 8 figures carried over |
| 5 | Source code and experiments archive | `FINAL_SUBMISSION_PACKAGE/source_code/COMPLETE_SOURCE_CODE_AND_EXPERIMENTS.zip` | 212 files, 7.5 MB, extraction verified |
| 6 | Archive README | `…/source_code/README_SOURCE.md` | present |
| 7 | Figure collection | `FINAL_SUBMISSION_PACKAGE/figures/COMPLETE_FIGURE_COLLECTION.zip` | 54 files, 43 figure files, 7.2 MB |
| 8 | Figure preview | `…/figures/ALL_FIGURES_PREVIEW.pdf` | 16 pages, 15 figures |
| 9 | Submission files | `…/manuscript/submission_files/` | highlights, competing-interest draft, similarity file |
| 10 | Reproducibility guide | `FINAL_SUBMISSION_PACKAGE/REPRODUCIBILITY_GUIDE.md` | present |
| 11 | Supporting reports | `FINAL_SUBMISSION_PACKAGE/reports/` | 13 documents |

---

## 2. Build verification

| Check | Result | Command |
|---|---|---|
| Manuscript build | 31 pages, **0 errors, 0 warnings** | `pdflatex manuscript.tex` ×3 |
| Manuscript references | 22/22 bibitems, 35 cross-references, **0 dangling** | build log |
| Report build | 98 pages, **0 errors, 0 undefined references** | `pdflatex report.tex` ×3 |
| Report floats | 8 figures, 26 tables, all numbered and referenced | `report.lof`, `report.lot` |
| Manuscript fonts | 35 fonts, **0 Type 3, 0 not embedded** | `pdffonts` |
| Report fonts | 43 fonts, **0 Type 3, 0 not embedded** | `pdffonts` |
| Worst overfull box, report | 19.2 pt | build log |
| Abstract length | **249 words** | measured past `\begin{document}` |
| Keywords | 7 | manuscript source |

---

## 3. Verification suites, all re-run

| Suite | Result |
|---|---|
| `tests/host/run_tests.sh` | **129 assertions pass**, including 3 negative build tests that require a defective configuration to fail to compile |
| `formal/run_tlc.sh` | 3 configurations: 25 and 660 distinct states with no error, and the **required violation** in the third |
| `experiments/test_conformance.py` | **19,529 transitions, 0 disallowed**, negative control rejected |
| `experiments/test_harness.py` | all metamorphic and differential properties hold |
| `experiments/corpus/test_rule.py` | **8/8 controls pass** |
| `experiments/validate_figures.py` | every plotted and quoted value matches the raw records |
| `experiments/check_figure_type.py` | every label clears the 6 pt floor; tightest is 6.22 pt |
| `experiments/check_figure_fit.py` | every label fits its box and the canvas |

---

## 4. Integrity checks

| Check | Result |
|---|---|
| Every reported count recomputed from raw artefacts | matches (`docs/COMPLETE_RESEARCH_AUDIT.md` §2) |
| Both Fisher *p*-values recomputed | 3.53 × 10⁻¹⁸⁴ and 9.83 × 10⁻¹¹⁹ |
| Wilson interval recomputed | [12.9, 21.3] |
| Figure SVGs regenerate byte-identically | yes |
| Broker experiment re-run on a clean install | all 8 verdicts identical |
| Archive contains no secrets | enforced by the builder, verified by a positive control |
| `secrets.h` excluded, `secrets.example.h` retained | yes |
| Archive extracts and its scripts run | verified |
| Report `\code{}` path references resolve to real files | 30/30 (the other 5 are globs, device paths and MQTT topics) |
| No fabricated results, measurements, citations or approvals | no hardware data exists and none is presented; no similarity percentage claimed; no supervisor approval claimed |

---

## 5. Verified journal requirements

| Requirement | Status | Evidence |
|---|---|---|
| Guide for Authors obtained | **verified** | retrieved from the publisher's own site |
| Page limit | **verified** | 31 pages |
| Reference count and format | **verified** | 22, numbered, 0 dangling |
| Abstract length | **verified** | 249 words |
| Keyword count | **verified** | 7 |
| Structured declarations in the publisher's named sections | **verified** | CRediT, competing interest, funding, data availability, ethics, generative AI |
| Highlights | **verified** | 5 bullets, longest 80 of 85 characters |
| Figure format and font embedding | **verified** | 8 figures, vector, fully embedded, 0 Type 3 |
| Data availability statement | **verified** | present |

---

## 6. Outstanding items

Seven. Six require the author or the supervisor.

| # | Item | Blocks submission | What is needed |
|---|---|---|---|
| 1 | **Institutional similarity report** | **yes** | No licensed tool was available. The prepared file and procedure are in `paper/submission/similarity/`. **No similarity percentage is claimed anywhere, official or otherwise.** |
| 2 | **Supervisor approval** | **yes** | Not obtained. Review notes are in `docs/SUPERVISOR_REVIEW_NOTES.md`. |
| 3 | **Dissertation-overlap ruling** | **yes** | Not made. An explicit ruling is requested in the supervisor package. |
| 4 | **Three author declarations** | **yes** | Competing interest, funding, and the sole-author-versus-supervisor-co-author question. Drafted in `docs/DECLARATIONS.md`. **No funding or conflict information is invented, and no declaration is made on the authors' behalf.** |
| 5 | **Corresponding author's email and postal address** | **yes** | Not present on the title page. |
| 6 | Five missing DOIs | no | `mcreview2026`, `espwn2023`, `mqtttls2026`, `zeghida2024`, and an ISBN for `lamport2002`. |
| 7 | **Hardware conditions A–D** | no | Not executed; **no hardware data exists**. The protocol is pre-registered and published. See below. |
| — | Journal quartile and metric years | no | **Unverified.** The ranking source returned an automated challenge, which was **not** circumvented. No quartile is asserted anywhere. |

### On item 7

No physical ESP32 was available: no serial devices, no USB, no `arduino-cli`, no Python `serial`
module, and no wireless interface. No RF-shielded enclosure, which condition D requires.

The manuscript and the report are written so that **no result depends on hardware data**. No
latency figure is reported anywhere, logical isolation and physical timing invariance are kept
distinct wherever either appears, and panel B of Figure 6 is labelled as not yet measured. The
pre-registered analysis — two-sided Mann–Whitney *U*, α = 0.05, power 0.80, *n* = 200 per
condition — was committed before any data existed, so the conditions can be run by someone else
without the test being chosen after the measurements.

This item therefore does not block submission of what is claimed. It does leave the work's central
timing question open, which the manuscript states as its principal limitation.

---

## 7. Known open design problems

Not defects in the reporting, but unresolved problems in the artefact, recorded so that a reader
of the code knows they are open.

1. **Owner lockout under key compromise.** Two configurations admit 0 of 1,250 operator commands:
   the adversary advances the persisted replay counter beyond the operator's reach. A candidate
   repair — counter resynchronisation authenticated by the physically present local button — is
   identified and **not implemented or evaluated**.
2. **Scenario E′.** The layered configuration falls to a compromised controller host and survives
   a device flash dump, which is the opposite of the cost ordering a defender would choose.
   Mitigation requires an authority off the controller host, and none is implemented.

---

## 8. Final status

| | |
|---|---|
| Academic report for institutional submission | **complete**, pending the author's signatures on the declaration and acknowledgement pages and the supervisor's certificate |
| Journal manuscript | **not submission-ready.** Items 1–5 above are outstanding and each blocks submission |
| Scientific content | verified against raw artefacts; no fabricated results, measurements, citations or approvals |
| Repository | clean, all suites pass, every figure and count reproducible |

**Nothing in this package should be read as a claim of supervisor approval, institutional
approval, similarity clearance, or hardware measurement. None of the four exists.**
