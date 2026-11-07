# Submission checklist

Target venue: **Journal of Systems Architecture: Embedded Software Design** (Elsevier).
Print ISSN 1383-7621, Online ISSN 1873-6165.

Checked against the **official Guide for Authors, retrieved 7 November 2026**. Every row marked
*verified* was read from Elsevier's own page, not inferred.

| Code | Meaning |
|---|---|
| **DONE** | Completed and verified here, reproducibly |
| **CONFIRM** | Draft prepared in the publisher's required form; **needs the author's explicit confirmation** — not a declaration anyone else can make |
| **AUTHOR** | Outstanding, and the author can resolve it |
| **BLOCKED** | Needs hardware or institutional resources |
| **UNVERIFIED** | Could not be checked without circumventing bot protection or without library access |
| **N/A** | Not applicable |

---

## Correction to the previous version of this checklist

The previous version recorded the competing-interest and funding declarations as **absent**.
**That was wrong.** Both were present, inside a combined `\section*{Declarations}` block as
`\textbf{Funding.}` and `\textbf{Conflicts of interest.}`; the check that reported them missing
searched for standalone `\section{Funding}` and did not match. They have since been promoted to
their own sections with Elsevier's required titles and standard wording, so the outcome is the
same — but the earlier finding was a false positive in my own check, not a defect in the paper.

---

## 1. Journal requirements, from the official Guide for Authors

| # | Requirement (verified) | Status | Evidence |
|---|---|---|---|
| 1.1 | Article type: original research article | **DONE** | three types accepted; this is the first |
| 1.2 | **No page or word limit for research articles** | **DONE** | none stated in the Guide; 31 pages is fine |
| 1.3 | **Abstract ≤ 250 words**, standalone, avoid references | **DONE** | rewritten from 521 to **249**, counted programmatically |
| 1.4 | **1–7 keywords**, avoid "and"/"of" | **DONE** | **7**, none containing "and" or "of" |
| 1.5 | **Highlights: 3–5 bullets, ≤ 85 chars each**, separate file with "highlights" in the name | **DONE** | `paper/submission/highlights.txt` — 5 bullets, longest **80** chars |
| 1.6 | Reference style: `[n]` in order of appearance; formatting not strict at submission | **DONE** | 22 entries, 22 cited, 0 orphaned, 0 undefined |
| 1.7 | Numbered sections, subsections 1.1/1.1.1; cross-reference by number | **DONE** | 14 numbered sections; no reference to "the text" |
| 1.8 | **Vector figures as EPS/PDF with fonts embedded**, no Type 3 | **DONE** | `pdffonts`: all 8, every font embedded, **0 Type 3** |
| 1.9 | Do not combine multiple graphs in one file, except where meant to be compared | **DONE** | Figures 3 and 5 are multi-panel and fall under the Guide's stated exception; captions say the panels are to be compared |
| 1.10 | Raster ≥ 300 dpi (photographs) / 1000 dpi (bitmapped line drawings) | **N/A** | all submission figures are vector; the 600 dpi PNGs are supplied for convenience only |
| 1.11 | Data statement required at submission | **DONE** | own `Data availability` section |
| 1.12 | GenAI declaration, new section before the reference list, exact title | **DONE** | retitled to "…in the manuscript preparation process"; sits before the bibliography |
| 1.13 | Title page: title, names, affiliation with full postal address and country | **AUTHOR** | title, name and affiliation present; **full postal address and country to add** |
| 1.14 | **Corresponding author's email on the title page** | **AUTHOR** | **absent — must be added** |
| 1.15 | **Declaration of competing interest**: 8 categories, declarations tool, `.doc`/`.docx` upload | **CONFIRM** | section rewritten to Elsevier's wording; `paper/submission/declaration-of-competing-interest.md` ready to convert. `docs/DECLARATIONS.md` §1 |
| 1.16 | **Funding**: sources and sponsor's role, or a statement of no involvement | **CONFIRM** | Elsevier's standard no-funding sentence applied. `docs/DECLARATIONS.md` §2 |
| 1.17 | **CRediT** contribution statement using the official role names | **CONFIRM** | own section, exact taxonomy. **Open: sole author, or supervisor as co-author with *Supervision*?** `docs/DECLARATIONS.md` §3 |
| 1.18 | Acknowledgements, if any: separate section before the references, not on the title page | **AUTHOR** | none present; needed only if someone is to be thanked |
| 1.19 | Supplementary material: cite in text, submit with the manuscript | **AUTHOR** | decide what, if anything, is formally supplementary vs. just the public repository |
| 1.20 | Open access decision | **AUTHOR** | APC **USD 2,260 excl. tax**, or subscription route at **no cost**; check for an SVNIT agreement |

## 2. Journal verification

| # | Item | Status | Evidence |
|---|---|---|---|
| 2.1 | Scope fit | **DONE** | embedded systems and software, real-time systems, from the Guide itself |
| 2.2 | Case-study condition understood | **DONE** | "must contribute more than just a design" — confirmed as the journal's standing position |
| 2.3 | Guide for Authors read in full | **DONE** | retrieved 7 Nov 2026 |
| 2.4 | CiteScore / Impact Factor | **DONE** | **9.1 / 5.3** |
| 2.5 | **Reference year for those metrics** | **UNVERIFIED** | read the page; the year is genuinely not stated |
| 2.6 | **Indexing** | **DONE** | **Scopus, SCIE, SJR, SNIP, Ei Compendex** |
| 2.7 | **Quartile** | **UNVERIFIED** | SCImago served a Cloudflare challenge (HTTP 403); **not circumvented**. SCIE indexing means a JCR quartile exists — read it from JCR via the library |
| 2.8 | Publication model | **DONE** | hybrid: open access supported, subscription available |
| 2.9 | APC | **DONE** | USD 2,260 excluding taxes; institutional agreements may cover it |
| 2.10 | Submission system | **DONE** | online system linked from the Guide |
| 2.11 | Relevant special issue | **DONE** | *Timing-Verifiable Intelligent Real-Time Systems* — **deadline 31 Oct 2026 has passed**; submit to the regular issue |
| 2.12 | Alternatives identified | **DONE** | ACM TECS; Empirical Software Engineering; IEEE Embedded Systems Letters |

## 3. Scientific content

| # | Item | Status | Evidence |
|---|---|---|---|
| 3.1 | Every count reconciles to a committed artefact | **DONE** | 9,600 / 3,600 / 3,000,000 / 180 / 8 / 135 / 19,529 |
| 3.2 | Every statistic recomputes from raw records | **DONE** | both Fisher *p*, both Wilson bounds, 59.0 %, 79.9 %, 16.7 %, 0/1250 |
| 3.3 | All 9 credential-table cells verified | **DONE** | 0 mismatches, disarm column included |
| 3.4 | Formal verification reproduces | **DONE** | 25 and 660 states; **3/3** TLC configurations |
| 3.5 | Trace conformance with a working negative control | **DONE** | 19,529 transitions, 0 disallowed |
| 3.6 | Real-broker experiment reproduces | **DONE** | 8/8 verdicts on a fresh container |
| 3.7 | No physical timing result claimed | **DONE** | targeted search; H2 marked untested |
| 3.8 | Zero corpus hits ≠ zero prevalence | **DONE** | stated, with the mechanism |
| 3.9 | Nine confirmed projects as an existence claim | **DONE** | matches `manual_validation.json` |
| 3.10 | Loopback broker not presented as a deployment | **DONE** | stated twice |
| 3.11 | Host fuzzing not presented as hardware fuzzing | **DONE** | scope stated in §Fuzzing |
| 3.12 | Threat model separates physical from remote access | **DONE** | E′ is a row; *Access* column is load-bearing |
| 3.13 | No new vulnerability or mechanism claimed | **DONE** | stated; attack class cited as published |

## 4. Manuscript build

| # | Item | Status | Evidence |
|---|---|---|---|
| 4.1 | Compiles, 3 passes, exit 0 | **DONE** | — |
| 4.2 | **Zero LaTeX warnings** | **DONE** | — |
| 4.3 | No undefined references or citations | **DONE** | 35 refs, 0 dangling |
| 4.4 | No orphan table or figure labels | **DONE** | all 11 tables, all 8 figures referenced |
| 4.5 | No overfull box over 20 pt | **DONE** | — |
| 4.6 | Page count | **DONE** | **31 pages** |
| 4.7 | DOIs on all references | **AUTHOR** | 5 missing. **Not a submission blocker** — Elsevier applies its style and requests missing data at proof stage |
| 4.8 | Reformat to `elsarticle` | **AUTHOR** | optional; the Guide does not require it at submission. Preamble already carries the alternative |

## 5. Figures

| # | Item | Status | Evidence |
|---|---|---|---|
| 5.1 | All 8 vector PDF, fonts embedded, no Type 3 | **DONE** | verified with `pdffonts` |
| 5.2 | Every label clears the 6 pt print floor | **DONE** | 6.11–6.56 pt |
| 5.3 | No clipped or overflowing labels | **DONE** | measured in the real font |
| 5.4 | Every plotted value matches the raw records | **DONE** | recomputed from `ablation.jsonl` |
| 5.5 | Consistent typography and colour semantics | **DONE** | one scale, one typeface; red means one thing |
| 5.6 | Meaning never carried by colour alone | **DONE** | border style, labels, printed numbers |
| 5.7 | Captions match the artwork | **DONE** | all 8 reviewed |
| 5.8 | No stale cross-reference in artwork | **DONE** | enforced by `validate_figures.py` |
| 5.9 | Figure 6 distinguishes run from not-run | **DONE** | dotted, red line, caption repeats it |
| 5.10 | Figure 8 shows the controller+key result | **DONE** | third row, 50/300, measured |
| 5.11 | Figures placed near their references | **DONE** | pages 8–25 |

## 6. Reproducibility

| # | Item | Status | Evidence |
|---|---|---|---|
| 6.1 | Host test suite | **DONE** | **129 pass, 0 fail** |
| 6.2 | Figures regenerate byte-identically | **DONE** | every SVG |
| 6.3 | Simulations regenerate from seeds | **DONE** | — |
| 6.4 | Broker experiment reproduces | **DONE** | fresh container, fresh Mosquitto |
| 6.5 | Corpus commit-pinned | **DONE** | 135 SHAs |
| 6.6 | CI runs every check | **DONE** | `.github/workflows/ci.yml` |
| 6.7 | Independent reproduction guide | **DONE** | `REPRODUCTION.md` |
| 6.8 | Hardware analysis path verified | **DONE** | end to end on synthetic input, labelled as a script test |

## 7. Integrity and approvals

| # | Item | Status | Evidence |
|---|---|---|---|
| 7.1 | No verbatim external text | **DONE** | all 9 quoted strings are the author's own terms or the protocol |
| 7.2 | External results attributed | **DONE** | Behnke et al. named, cited, marked as theirs |
| 7.3 | Self-overlap with the public repository measured | **DONE** | **0.7 %** of manuscript sentences |
| 7.4 | Unsupported claims reviewed | **DONE** | 1 found and removed |
| 7.5 | Similarity screening file prepared with settings | **DONE** | `paper/submission/similarity/` |
| 7.6 | **Institutional similarity report** | **BLOCKED** | no licensed tool here; SVNIT must run it |
| 7.7 | Similarity percentage | **BLOCKED** | **not claimed, and must not be until a report exists** |
| 7.8 | Prior publication declared | **AUTHOR** | public repository; no preprint, no conference version |
| 7.9 | **Dissertation overlap ruled on** | **CONFIRM** | supervisor decision 4 |
| 7.10 | **Supervisor approval** | **CONFIRM** | `SUPERVISOR_REVIEW_NOTES.md` §11 |

## 8. Hardware (optional, not a submission requirement)

| # | Item | Status | Evidence |
|---|---|---|---|
| 8.1 | Conditions A–C | **BLOCKED** | ~£25 of hardware; no permission needed. Runbook: `docs/HARDWARE_A_TO_C_RUNBOOK.md` |
| 8.2 | Condition D | **BLOCKED** | RF-shielded enclosure **and** written institutional permission |
| 8.3 | Protocol, BoM, wiring, data template, power analysis | **DONE** | `docs/HARDWARE_VALIDATION_PLAN.md` |

---

## Summary

| Status | Count |
|---|---|
| **DONE** | 62 |
| **AUTHOR** (author can resolve) | 8 |
| **CONFIRM** (author/supervisor must confirm) | 5 |
| **BLOCKED** (institution or hardware) | 4 |
| **UNVERIFIED** (bot protection or library access) | 2 |
| **N/A** | 1 |

### What now blocks submission

Down from five to **four**, and all four are external:

1. **Institutional similarity report** (7.6). Everything needed to run it is prepared.
2. **Supervisor approval** (7.10) and the **dissertation-overlap ruling** (7.9).
3. **Three declarations needing the author's explicit confirmation** (1.15, 1.16, 1.17) — these
   are legally meaningful statements and cannot be made by anyone else. Sign-off sheet:
   `docs/DECLARATIONS.md`.
4. **Title-page completion** (1.13, 1.14): the corresponding author's email is required and is
   currently absent.

**No longer blocking:** the Guide for Authors is retrieved and all nine formatting requirements
are resolved or prepared; the abstract is within the limit; keywords are within range;
Highlights exist; figure formats are verified compliant; there is no page limit.

**Not blocking, contrary to the earlier assessment:** the five missing DOIs. The Guide states
reference formatting is not strictly required at submission, and that Elsevier applies its own
style and requests missing data at proof stage.

**Not a submission requirement at all:** hardware A–D. Worth doing on the merits, not for
compliance.

### The paper is still not submission-ready

Technically it is complete and now also **format-compliant with the verified Guide for
Authors**. What remains is entirely administrative and external: one institutional report,
three author confirmations, one supervisor approval, and an email address.
