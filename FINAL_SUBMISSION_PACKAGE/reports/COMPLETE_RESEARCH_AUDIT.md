# Complete research audit

Full re-verification of the repository and of every reported quantity, carried out at commit
`f9a902d` as the first phase of the final documentation work. Earlier reports were treated as
claims to be checked, not as established facts.

This document records what was checked, what matched, and — in section 3 — the four things that
did not.

---

## 1. Repository state

| Item | Value | How established |
|---|---|---|
| HEAD | `f9a902d84532f792efc0f18b5f89e80b3ffb5ce9` | `git rev-parse HEAD` |
| Commits on the branch | 66 | `git rev-list --count HEAD` |
| Working tree | clean | `git status` |
| Source files | 64 | `tools/build_report_data.py` |
| Lines of code | 7,293 | `tools/build_report_data.py` |
| Firmware version | v2.2.0 | `firmware/smart_home/smart_home.ino` |

### Documents

| Document | Pages | Verified |
|---|---|---|
| `paper/manuscript.pdf` | 31 | 0 errors, 0 warnings, 0 undefined references, 22/22 bibitems resolved, 35 cross-references with 0 dangling |
| `report/report.pdf` | 98 | 0 errors, 0 undefined references, 8 figures, 26 tables |

Manuscript abstract: **249 words**, measured by stripping command names while keeping their
arguments, anchored past `\begin{document}` so the header comment at line 14 is not matched.
Keywords: **7**.

---

## 2. Every reported quantity, recomputed from raw records

Recomputed from the raw per-trial artefacts, not from derived summaries.

### Trial accounting

| Experiment | Reported | Recomputed | Source |
|---|---|---|---|
| E1 campaign, baseline | 3,000 trials | 3,000 | `summary.json` |
| E2 campaign, hardened | 3,000 trials | 3,000 | `summary.json` |
| E3 ablation | 3,600 trials, 12 configurations | 3,600 | `ablation.jsonl` |
| **Adversarial trials, total** | **9,600** | **9,600** | 3,000 + 3,000 + 3,600 |
| E4 fuzzing | 3,000,000 iterations | 3,000,000 | `fuzz.json` |
| E5 sensitivity | 180 grid cells | 180 | `sensitivity.jsonl` |
| E6 broker | 8 scenarios | 8 | `broker_acl.jsonl` |
| E7 corpus | 135 projects | 135 | `corpus.json` |
| E8 conformance | 19,529 transitions | 7,044 + 5,282 + 7,206 = 19,529 | `test_conformance.py` |
| E9 model checking | 25 and 660 distinct states | 25 and 660 | TLC, re-run |

### Statistics

| Claim | Recomputed | Status |
|---|---|---|
| Leaked-credential alarm activation 16.7% | 50/300 = 16.67% | exact |
| 95% Wilson interval [12.9%, 21.3%] | [12.9, 21.3] | exact |
| Rate limiter admits 59.0% of operator commands | 737/1250 = 58.96% | exact |
| Fisher exact, rate limiter vs others | 3.53 × 10⁻¹⁸⁴ | exact |
| Fisher exact, transport leaked vs held | 9.83 × 10⁻¹¹⁹ | exact |
| Adversary disarms in 246 of 300 trials | 246 | exact |
| Owner lockout, 0 of 1,250 operator commands | 0/1250 | exact |
| Detector default fired in 79.9% of benign runs | 1,597/2,000 = 79.85% | exact |

### Corpus

| Claim | Recomputed | Status |
|---|---|---|
| Rule 1 hits | 0 across 135 projects | exact |
| Rule 2 flagged | 18 of 135 | exact |
| Manual confirmation | 9 confirmed, 9 false positive | exact |
| Rule controls | 8, all pass | re-run |

### Model checking, re-run in full

```
AlarmFSM.cfg          166 states generated,   25 distinct, no error            PASS
Isolation.cfg       2,686 states generated,  660 distinct, no error            PASS
AlarmFSM_unsafe.cfg Invariant NoUnauthRemoteDisarm is violated                 PASS (required)
```

The third configuration passes by **failing**: its required outcome is a violation, and the
runner additionally requires the specific invariant name in TLC's output so that a syntax error
cannot be mistaken for the expected violation.

### Test suites, re-run in full

129 host assertions (including 3 negative build tests that require a defective configuration to
fail to compile), 19,529 conformance transitions with the negative control rejected, the harness
metamorphic and differential properties, 8 corpus controls, 59 figure assertions. **All pass.**

### Reproducibility

- Every figure SVG regenerates **byte-identically**. The PDFs differ only in embedded creation
  timestamps.
- The broker experiment was re-run against a freshly installed Mosquitto 2.0.18 in a clean
  environment: **all eight verdicts identical**, differing only in log timestamps and random
  client identifiers.

---

## 3. Discrepancies found by this audit

Four. Each is recorded with its cause and its resolution rather than silently corrected.

### 3.1 Lines of code were undercounted by 259 lines

**Reported:** 62 files, 6,566 lines of code.
**Correct:** 64 files, 7,293 lines of code.

Two causes, and they account for the difference exactly:

| Cause | Lines |
|---|---|
| Two files added since the previous count (`tools/build_source_archive.py`, `tools/build_report_data.py`) | +468 |
| **A defect in the previous counting method** | +259 |
| | 6,566 + 468 + 259 = **7,293** |

The previous count was produced by an ad-hoc command that applied the `#` line-comment prefix to
every language. In C and C++ that is not a comment: it is the preprocessor. Every `#include`,
`#define`, `#if` and `#error` line in the firmware and the harnesses was therefore discarded as a
comment. `experiments/ablation.cpp` was reported at 369 lines of code and is 384.

The irony is worth recording: the lines discarded were precisely the preprocessor lines, and the
central finding of this research is a defect in a preprocessor guard.

**Resolution.** The counting rule is now implemented in `tools/build_report_data.py` with a
per-language comment prefix table and explicit `/* ... */` block-comment handling, and the
definition is stated in the script: a line counts as code if anything remains after removing
block comments and a trailing line comment.

### 3.2 The appendix generator did not exist

`report/report.tex` carried a header comment stating that `report/generated/*.tex` is written by
`tools/build_report_data.py`, and that script was not in the repository. The generated files had
been produced by ad-hoc commands, so the counts in appendices A and B were not reproducible and
the header comment was false.

**Resolution.** The script now exists and regenerates all five files. It additionally **fails**
if a curated entry in appendix G or H names an experiment artefact, figure file or generator
script that is not present, so an editorial label cannot outlive the thing it labels.

### 3.3 Appendix A counted build artefacts as source

Regenerating the directory listing mechanically showed `formal/` with 21 files rather than 7, and
`paper/` with 10 rather than 7. The cause is TLC's trace files — a `.tla` and a `.bin` per failing
run, 12 files — together with LaTeX intermediates and built PDFs. The appendix would have
described the most recent build rather than the repository's source.

**Resolution.** Run artefacts and build output are excluded from the listing, with the exclusion
and its reason recorded in the script.

### 3.4 The commit hash on the report title page was stale

`report/generated/meta.tex` recorded `b31c617`, two commits behind, so the report identified the
wrong repository state as the one it described. Regenerated.

---

## 4. What remains unestablished

Unchanged by this audit, and restated so that nothing here is mistaken for a resolved item.

### Hardware

**No physical ESP32 was available.** Hardware conditions A–D were not executed and **no hardware
data exists.** The probe establishing this is recorded in the report's Appendix I: no
`/dev/ttyUSB*` or `/dev/ttyACM*` devices, no USB subsystem, no `arduino-cli`, no Python `serial`
module, and only `eth0`, `ifb0` and `lo` as network interfaces — no wireless interface of any
kind. No RF-shielded enclosure.

Consequently:

- No latency figure is reported anywhere in either document.
- **Logical isolation is proved; physical timing invariance is unmeasured and unclaimed.** The
  distinction is maintained wherever either appears.
- Panel B of Figure 6 remains labelled as not yet measured.
- On-device memory safety is not established; the fuzzing ran on a host build under sanitizers
  that do not exist for the Xtensa target.

The pre-registered analysis plan — two-sided Mann–Whitney *U* with tie correction, α = 0.05,
power 0.80, *n* = 200 per condition — was committed before any data existed. The analysis script
was verified end to end on explicitly synthetic input as a script self-test, and that synthetic
file was deliberately **not** committed so it cannot be mistaken for data.
`results_hw_TEMPLATE.csv` carries the schema and no rows.

### Items requiring the author or the supervisor

| Item | Status |
|---|---|
| Supervisor approval | **not obtained** |
| Dissertation-overlap ruling | **not made** |
| Institutional similarity report | **does not exist.** No similarity percentage is claimed anywhere, official or otherwise |
| Competing-interest declaration | drafted; **requires author confirmation** |
| Funding declaration | drafted; **requires author confirmation**. No funding is invented |
| Authorship contribution statement | the sole-author versus supervisor-co-author question is the author's to settle |
| Corresponding author's email and postal address | **not present** on the title page |
| Journal quartile and metric years | **unverified.** The ranking source returned an automated challenge, which was **not** circumvented |
| Five missing DOIs | `mcreview2026`, `espwn2023`, `mqtttls2026`, `zeghida2024`, and an ISBN for `lamport2002` |

The declaration, certificate and acknowledgement pages of the report are unsigned drafts. The
certificate page is explicitly marked as a template and carries no approval or signature.

### Open design problems

Two, identified by this work and **not fixed** in the artefact:

1. **Owner lockout under key compromise.** Two configurations admit 0 of 1,250 operator commands,
   because the adversary advances the persisted replay counter beyond the operator's reach.
2. **Scenario E′.** The layered configuration falls to a compromised controller host and survives
   a device flash dump, which is the opposite of the cost ordering a defender would choose.

---

## 5. Audit conclusion

Every quantity reported in the manuscript and the report matches its raw artefact. Three
discrepancies were found in the *reporting infrastructure* — an undercount of lines of code, a
generator that did not exist, and a directory listing that counted build output — and one in
*document metadata*, a stale commit hash. All four are resolved, and the generator that resolves
three of them now fails the build if a curated label names something absent.

**The manuscript is not journal-submission-ready.** Hardware conditions A–D, institutional
similarity screening, supervisor approval, the dissertation-overlap ruling, three author
declarations, the corresponding author's contact details and five DOIs are all outstanding. Each
is listed above with its exact status.
