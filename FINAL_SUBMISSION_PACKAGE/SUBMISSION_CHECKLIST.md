# Submission checklist

Target venue: **Journal of Systems Architecture** (Elsevier), ISSN 1383-7621.
Prepared 7 November 2026. Repository `mdhumayun7/Smart-Home-Automation`.

Status codes:

| Code | Meaning |
|---|---|
| **DONE** | Completed and verified here, with the verification reproducible |
| **APPROVAL** | Completed, awaiting an external sign-off |
| **BLOCKED** | Pending hardware or institutional resources |
| **N/A** | Not applicable |
| **UNVERIFIED** | Could not be checked from this environment |
| **TODO** | Outstanding, and the author can do it |

---

## 1. Scientific content

| # | Item | Status | Evidence |
|---|---|---|---|
| 1.1 | Every reported count reconciles to a committed artefact | **DONE** | `FINAL_SCIENTIFIC_REVIEW.md` §D; 9,600 / 3,600 / 3,000,000 / 180 / 8 / 135 / 19,529 all recomputed |
| 1.2 | Every statistic recomputes from raw records | **DONE** | both Fisher *p*, both Wilson bounds, 59.0 %, 79.9 %, 16.7 %, 0/1250 — exact |
| 1.3 | All 9 credential-table cells verified | **DONE** | 0 mismatches, including the disarm column |
| 1.4 | Formal verification reproduces | **DONE** | 25 and 660 distinct states; three TLC configurations, including the one that must fail |
| 1.5 | Trace conformance with a working negative control | **DONE** | 19,529 transitions, 0 disallowed |
| 1.6 | Real-broker experiment reproduces | **DONE** | 8/8 verdicts identical on a fresh container and a fresh Mosquitto |
| 1.7 | No physical timing result claimed | **DONE** | targeted search found none; H2 marked untested |
| 1.8 | Zero corpus hits not presented as zero prevalence | **DONE** | stated explicitly, with the mechanism behind the zero |
| 1.9 | Nine confirmed projects as an existence claim | **DONE** | matches `manual_validation.json` |
| 1.10 | Loopback broker not presented as a deployment | **DONE** | stated twice |
| 1.11 | Host fuzzing not presented as hardware fuzzing | **DONE** | scope added to §Fuzzing in this cycle |
| 1.12 | Threat model separates physical from remote access | **DONE** | E′ added as a row in this cycle; *Access* column is load-bearing |
| 1.13 | No new vulnerability or mechanism claimed | **DONE** | stated; attack class cited as published |
| 1.14 | **Hardware conditions A–C** | **BLOCKED** | ~£25 of hardware. `HARDWARE_VALIDATION_PLAN.md` §10 |
| 1.15 | **Hardware condition D** | **BLOCKED** | RF-shielded enclosure + written institutional permission |

## 2. Manuscript

| # | Item | Status | Evidence |
|---|---|---|---|
| 2.1 | Compiles without error | **DONE** | 3 passes, exit 0 |
| 2.2 | Zero LaTeX warnings | **DONE** | — |
| 2.3 | No undefined references or citations | **DONE** | 48 labels, 0 dangling |
| 2.4 | No orphan table or figure labels | **DONE** | all 11 tables and 8 figures referenced |
| 2.5 | No overfull box over 20 pt | **DONE** | — |
| 2.6 | Bibliography complete | **DONE** | 22 entries, 22 cited, 0 orphaned |
| 2.7 | DOIs on all references | **TODO** | 5 missing: `mcreview2026`, `espwn2023`, `mqtttls2026`, `zeghida2024`; ISBN for `lamport2002` |
| 2.8 | Title supported by every section | **DONE** | `FINAL_REPOSITORY_AUDIT.md` §4 |
| 2.9 | Page count | **DONE** | 31 pages |
| 2.10 | Abstract within the venue's limit | **UNVERIFIED** | ~430 words; the limit is in the unreachable Guide for Authors. **Likely over.** |
| 2.11 | Keywords within the permitted range | **UNVERIFIED** | 10 supplied |
| 2.12 | Reference style matches the venue | **UNVERIFIED** | numbered; JSA is typically numbered Elsevier style |
| 2.13 | Reformat to `elsarticle` | **TODO** | one line; the preamble already carries the alternative |
| 2.14 | Highlights (3–5 bullets) | **UNVERIFIED** | not prepared; confirm whether required |
| 2.15 | **Declaration of competing interest** | **TODO** | **absent from the manuscript** |
| 2.16 | **Funding statement** | **TODO** | **absent from the manuscript** |
| 2.17 | Declaration of generative AI use | **DONE** | standalone section, Elsevier form |
| 2.18 | Data availability statement | **TODO** | repository is public; confirm the required wording |
| 2.19 | Ethics / human subjects | **N/A** | no human or animal subjects |
| 2.20 | CRediT author statement | **UNVERIFIED** | single author; confirm whether required |

## 3. Figures

| # | Item | Status | Evidence |
|---|---|---|---|
| 3.1 | All 8 vector PDF | **DONE** | manifest in the figure collection |
| 3.2 | Fonts embedded, not Type 3 | **DONE** | `pdf.fonttype: 42` in `figstyle.py` |
| 3.3 | Every label clears the 6 pt print floor | **DONE** | 6.11–6.56 pt; `check_figure_type.py` |
| 3.4 | No clipped or overflowing labels | **DONE** | `check_figure_fit.py`, measured in the real font |
| 3.5 | Every plotted value matches the raw records | **DONE** | `validate_figures.py`, recomputed from `ablation.jsonl` |
| 3.6 | Consistent typography and colour semantics | **DONE** | one scale, one typeface, red means one thing |
| 3.7 | Meaning never carried by colour alone | **DONE** | border style, labels and printed numbers throughout |
| 3.8 | Captions match the artwork | **DONE** | all 8 reviewed; 5 changed |
| 3.9 | No stale cross-reference baked into artwork | **DONE** | enforced by `validate_figures.py` |
| 3.10 | Figure 6 distinguishes run from not-run | **DONE** | panel B dotted, red line, caption repeats it |
| 3.11 | Figure 8 shows the controller+key result | **DONE** | third row, 50/300, measured |
| 3.12 | 600 DPI raster supplied | **DONE** | at the printed width, not an arbitrary canvas |
| 3.13 | Figures placed near their references | **DONE** | pages 8–25, not 26–30 |
| 3.14 | Venue's figure format requirements | **UNVERIFIED** | Guide for Authors unreachable; PDF and 600 DPI PNG both ready |

## 4. Reproducibility

| # | Item | Status | Evidence |
|---|---|---|---|
| 4.1 | Host test suite | **DONE** | 129 pass, 0 fail |
| 4.2 | Figures regenerate byte-identically | **DONE** | every SVG; PDFs differ only in creation timestamp |
| 4.3 | Simulations regenerate from committed seeds | **DONE** | — |
| 4.4 | Broker experiment reproduces | **DONE** | fresh container, fresh Mosquitto, 8/8 |
| 4.5 | Corpus commit-pinned | **DONE** | 135 SHAs in `commit_shas.tsv` |
| 4.6 | CI runs every check | **DONE** | `.github/workflows/ci.yml` |
| 4.7 | Independent reproduction guide | **DONE** | `REPRODUCTION.md` |
| 4.8 | Hardware analysis path verified | **DONE** | end to end on synthetic input, labelled as a script test |

## 5. Venue requirements

| # | Item | Status | Evidence |
|---|---|---|---|
| 5.1 | Scope fit confirmed from the publisher | **DONE** | Elsevier's own aims and scope |
| 5.2 | Case-study condition understood | **DONE** | "must contribute more than just a design" — addressed by the method framing |
| 5.3 | **Guide for Authors read in full** | **UNVERIFIED** | two attempts, client error from the site; not circumvented |
| 5.4 | Metrics | **DONE** | CiteScore 9.1, IF 5.3, from Elsevier's Insights page |
| 5.5 | Reference year for those metrics | **UNVERIFIED** | not stated on the page |
| 5.6 | **Quartile** | **UNVERIFIED** | SCImago unreachable; Scopus and JCR need library access. **No quartile is claimed.** |
| 5.7 | Open access decision | **TODO** | APC USD 2,260 excl. tax, or the subscription route at no cost |
| 5.8 | Submission system | **UNVERIFIED** | presumably Editorial Manager |
| 5.9 | Alternatives identified | **DONE** | ACM TECS, Empirical Software Engineering, IEEE ESL |

## 6. Integrity and approvals

| # | Item | Status | Evidence |
|---|---|---|---|
| 6.1 | No verbatim external text | **DONE** | all 9 quoted strings are the author's own terms or the protocol |
| 6.2 | External results attributed | **DONE** | Behnke et al.'s figures named, cited, marked as theirs |
| 6.3 | Self-overlap with the public repository measured | **DONE** | 0.7 % of manuscript sentences |
| 6.4 | Unsupported claims reviewed | **DONE** | 1 found and removed in this cycle |
| 6.5 | **Institutional similarity report** | **BLOCKED** | no licensed tool here; SVNIT must run it. Checklist in `SIMILARITY_SCREENING_CHECKLIST.md` §6 |
| 6.6 | Similarity percentage | **BLOCKED** | **not claimed, and must not be until a report exists** |
| 6.7 | Prior publication declared | **TODO** | public repository; no preprint, no conference version |
| 6.8 | **Dissertation overlap ruled on** | **APPROVAL** | Decision 4 for the supervisor |
| 6.9 | **Supervisor approval** | **APPROVAL** | `SUPERVISOR_REVIEW_NOTES.md` §11 |

---

## Summary

| Status | Count |
|---|---|
| **DONE** | 48 |
| **TODO** (author can resolve) | 8 |
| **UNVERIFIED** (needs the Guide for Authors or library access) | 9 |
| **BLOCKED** (hardware or institution) | 5 |
| **APPROVAL** (supervisor) | 2 |
| **N/A** | 1 |

### The paper is NOT submission-ready

**Technically it is complete**: every scientific item in §1–§4 that can be verified here is
verified, and reproducible. That is a different thing from being ready to submit.

**Five items block submission and none can be resolved from here:**

1. The institutional similarity report (6.5).
2. Supervisor approval (6.9) and the dissertation-overlap ruling (6.8).
3. The Guide for Authors, which gates nine unverified formatting items — including the
   abstract length, which is probably over (2.10).
4. The competing-interest and funding declarations, which are simply absent (2.15, 2.16).
5. Hardware conditions A–D (1.14, 1.15) — not strictly blocking, but A–C cost about £25 and
   would address the objection most likely to cost an acceptance.

**Do not submit until items 1–4 are closed.**
