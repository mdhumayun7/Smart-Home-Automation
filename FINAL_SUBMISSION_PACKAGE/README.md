# Final submission package

*Unverified Assumptions in Embedded Safety Firmware: Configuration, Specification and
Response-Time Defects in an MQTT Alarm System*

MD Humayun, SVNIT Surat. Assembled 7 November 2026.

**Start with [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md).** It gives the status of
every requirement and names the five things that block submission.

For the supervisor, read [`reports/SUPERVISOR_REVIEW_NOTES.md`](reports/SUPERVISOR_REVIEW_NOTES.md)
first; §11 holds the four decisions being requested.

## Contents

```
manuscript/
  FINAL_MANUSCRIPT.pdf      the paper, 31 pages
  manuscript.tex            LaTeX source; the bibliography is embedded, so
                            there is no separate .bib file

figures/
  COMPLETE_FIGURE_COLLECTION.zip   every figure as vector PDF, editable SVG
                                   and 600 DPI PNG, with a manifest and
                                   SHA-256 checksums
  ALL_FIGURES_PREVIEW.pdf          all 15 figures in one document, each at the
                                   width it prints at

supplementary_material/
  README.md                 an index of the experimental data, formal models,
                            firmware and analysis scripts, by their canonical
                            repository paths. Nothing is copied: a second copy
                            goes stale, which is the defect this revision cycle
                            removed from paper/.

reports/                    eleven reports (see below)

SUBMISSION_CHECKLIST.md     every requirement, with status
```

## The reports

| Report | What it answers |
|---|---|
| `SUPERVISOR_REVIEW_NOTES.md` | the whole project in ten minutes, and the four decisions needed |
| `FINAL_REPOSITORY_AUDIT.md` | is the repository consistent, pushed and reproducible? |
| `FINAL_SCIENTIFIC_REVIEW.md` | a reviewer-style audit; every number recomputed |
| `CONSISTENCY_AUDIT.md` | the eleven-point check against the raw artefacts |
| `FIGURE_VALIDATION.md` | figure by figure: source, correctness, printed size, caption |
| `TITLE_ASSESSMENT.md` | why the title changed; five candidates scored |
| `JOURNAL_SELECTION_AND_GUIDELINES.md` | venue fit, what is verified, what is not |
| `SIMILARITY_SCREENING_CHECKLIST.md` | what was reviewed by hand; how to obtain the report |
| `HARDWARE_VALIDATION_PLAN.md` | conditions A–D: what they need and what blocks them |
| `CONTRIBUTIONS.md` | why eight claimed contributions became five |
| `VERSION_STRATEGY.md` | two honest framings, and which is submittable today |

## Rebuilding anything here

From a checkout of the repository:

```bash
cd paper && pdflatex manuscript.tex && pdflatex manuscript.tex && pdflatex manuscript.tex
python3 tools/build_figure_collection.py      # the ZIP and its manifest
python3 tools/build_figure_preview.py         # the preview PDF
```

## One thing to be clear about

The paper is **technically complete**, not submission-ready. The similarity report, the
supervisor's approval, the target journal's Guide for Authors, two missing declarations and
the hardware measurement are all outstanding, and none of them could be resolved from the
environment this package was assembled in. `SUBMISSION_CHECKLIST.md` says which is which.
