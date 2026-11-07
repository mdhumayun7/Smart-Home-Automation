# Complete figure collection

Every figure generated for *Unverified Assumptions in Embedded Safety Firmware:
Configuration, Specification and Response-Time Defects in an MQTT Alarm System*.

Repository: `mdhumayun7/Smart-Home-Automation`
Commit: see `git rev-parse HEAD` in the repository this was built from
Built by `tools/build_figure_collection.py`

## What is here

| | Count |
|---|---|
| Manuscript figures (Figures 1-8) | 8 |
| Additional repository figures | 7 |
| Figure files in total (PDF + SVG + PNG) | 43 |

Each figure folder holds three formats:

- **`.pdf`** - publication-quality vector, the exact file the manuscript embeds. Fonts are
  embedded; matplotlib figures use `pdf.fonttype 42` (TrueType, not Type 3, which most
  publishers reject).
- **`.svg`** - editable vector source, for the six hand-drawn diagrams. The two plotted
  figures (03 and 05) are produced by matplotlib and have no SVG intermediate; their editable
  form is the Python in `source_files/`.
- **`.png`** - raster at **600 DPI** measured at the width the figure occupies in the
  manuscript (`\textwidth` = 6.24 in on A4 with 1 in margins), which is above the 300 DPI
  floor publishers set and matches the 600 DPI most prefer for line art.

`manifest.csv` lists every file with its format, byte size, pixel dimensions, effective DPI,
the script that generates it, and its SHA-256.

## Mapping to the manuscript

| # | Folder | Title | Manuscript page |
|---|---|---|---|
| 1 | `figure_01_architecture` | System Architecture | 8 |
| 2 | `figure_02_command_flow` | Command Execution Flow | 9 |
| 3 | `figure_03_ablation_results` | Command-Path Ablation Results | 16 |
| 4 | `figure_04_acl_architecture` | Broker Access Control Architecture | 18 |
| 5 | `figure_05_credential_matrix` | Security Compromise Comparison | 18 |
| 6 | `figure_06_experimental_setup` | Experimental Setup | 22 |
| 7 | `figure_07_guard_decision` | Compile-Guard Comparison | 24 |
| 8 | `figure_08_security_paths` | Transport Security vs Command Authorization | 25 |

The seven figures under `additional_readme_figures/` document the repository and are **not
part of the submission**. One of them, `hardware_rig`, is the wiring and instrumentation
diagram for the measurement that has **not been performed**; it carries a red banner saying
so.

## Regenerating everything

From a checkout of the repository at the commit above:

```bash
python3 docs/figures/make_diagrams.py          # the hand-drawn diagrams
python3 experiments/make_ablation_figures.py   # the two plotted figures
python3 tools/build_figure_collection.py       # rebuild this archive and its manifest
```

The archive is not committed as a binary: it is derived entirely from files in the
repository, and a committed copy would go stale the moment a figure changed.

Every SVG regenerates byte-identically from these two scripts; the PDFs differ only in their
embedded creation timestamp. The sources are copied into `source_files/` for reference, but
the canonical copies live in the repository.

## Validating everything

```bash
python3 -I experiments/check_figure_type.py    # printed point size against the 6 pt floor
python3 -I experiments/check_figure_fit.py     # clipped or overflowing labels
python3 -I experiments/validate_figures.py     # plotted values against the raw records
```

All three exit non-zero on failure, so they can gate a build. The captured output of the run
that produced this archive is in `validation/validation_results.txt`: **59 assertions, 0
failures**.

`validation/FIGURE_VALIDATION.md` is the figure-by-figure report: for each figure, the source
file, the regeneration command, the technical-correctness check, the readability check at
printed scale, the vector check, the caption review, and confirmation that it matches the
results.

## Verifying this archive

```bash
cd COMPLETE_FIGURE_COLLECTION
sha256sum -c validation/SHA256SUMS.txt
```

## A note on what these figures claim

Figure 6 panel B describes a hardware rig that **has not been run**. It is drawn dotted,
headed "Not yet measured", and carries a red line saying no result in the paper comes from
it. No figure in this collection reports a physical timing measurement, because none has been
taken.
