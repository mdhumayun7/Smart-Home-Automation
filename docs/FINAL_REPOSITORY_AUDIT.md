# Final repository and manuscript audit

Phase 1 of the finalization task. Everything below was established by inspecting the
repository at the stated commit and re-running the artefacts, not by reading earlier reports.

**Audit date:** 7 November 2026
**HEAD at audit start:** `31576ec471ceef05c1f430de50e2242a5c7a3317`

---

## 1. Git state

```
$ git rev-parse HEAD
31576ec471ceef05c1f430de50e2242a5c7a3317

$ git status --short
(empty)

$ git fetch origin && git rev-parse origin/main
31576ec471ceef05c1f430de50e2242a5c7a3317
```

| Check | Result |
|---|---|
| Working tree clean at audit start | yes |
| Local HEAD == `origin/main` | **yes** |
| All reported commits pushed | **yes**, none outstanding |
| Total commits in history | 60 |
| Commits since `87dcba5` (where this revision cycle began) | **10** |

The repository remote reports a rename from `smart-home-automation` to
`Smart-Home-Automation`; pushes succeed and GitHub redirects. Updating the local remote URL is
a one-line convenience, not a correctness issue.

### Resolving reporting discrepancy 1 — commit count

The previous report said "ten commits" in one place and "nine increments" in another. **The
correct figure is ten.** The prose was wrong, not the repository. The ten, oldest first:

| # | Hash | Subject |
|---|---|---|
| 1 | `db8690a` | Measure printed figure type size, and raise the diagram type scale |
| 2 | `f95e0c8` | Add a mechanical overflow check, and rebuild Figure 8 |
| 3 | `8fbfabe` | Rebuild Figures 2, 4 and 7 so no label is clipped |
| 4 | `0891e3c` | Rebuild Figure 6 so it lists the experiments that actually exist |
| 5 | `59b46d7` | Replace the hand-authored Figure 1 with a generated one |
| 6 | `6e645a4` | Fix float placement, correct five captions, add the status snapshot to Figure 1 |
| 7 | `4215c76` | Change the title: it claimed a property the paper does not establish |
| 8 | `7318ad4` | Scientific consistency audit: three defects found and fixed |
| 9 | `480902c` | Version B: five evidence categories, and one loose isolation claim tightened |
| 10 | `31576ec` | Remove figure PDFs copied into `paper/` |

Commits 1–6 are the figure work; 7–10 are the title, the audit, the evidence taxonomy and a
cleanup. "Nine" appears to have been a miscount of the figure-rebuild subset.

---

## 2. Manuscript build

Built from a clean state — `.aux`, `.log`, `.out` and `.toc` deleted first — with three
`pdflatex` passes.

| Check | Result |
|---|---|
| Compilation exit status | 0 |
| **Pages** | **30** |
| `LaTeX Warning` occurrences | **0** |
| Undefined references | **0** |
| `Overfull \hbox` exceeding 20 pt | **0** |
| Missing graphics files | **0** |

### Resolving reporting discrepancy 2 — page count

`CONSISTENCY_AUDIT.md` recorded 31 pages; the delivered PDF has 30. **30 is correct.**

The 31 was measured immediately after the float-placement change in commit `6e645a4`, which
moved eight floats from `[t]`/`figure*` to `[htbp]`/`figure` and briefly added a page. Two
later commits — `7318ad4` (the expanded broker-table caption and the extra control row) and
`480902c` (the five-category evidence taxonomy) — reflowed the document back to 30. The audit
document carried the intermediate figure forward. `CONSISTENCY_AUDIT.md` has been corrected
and now states 30 with a note explaining the discrepancy.

A clean rebuild reproduces 30 pages.

---

## 3. Title

The manuscript source carries the recommended title, and so does the built PDF.

```latex
\title{\textbf{Unverified Assumptions in Embedded Safety Firmware:\\
Configuration, Specification and Response-Time Defects\\
in an MQTT Alarm System}}
```

```
$ pdftotext -layout paper/manuscript.pdf - | head -3
    Unverified Assumptions in Embedded Safety Firmware:
    Configuration, Specification and Response-Time Defects
                  in an MQTT Alarm System
```

**The old title does not survive anywhere** except in the three documents that exist to record
the decision (`TITLE_ASSESSMENT.md`, `VERSION_STRATEGY.md`, `REVIEWER_ASSESSMENT.md`), where it
is quoted deliberately.

`CITATION.cff` titles the *software artefact*, not the paper, and is correctly distinct.

---

## 4. Does the manuscript consistently support the title?

Checked section by section. The title asserts three things: that the subject is unverified
assumptions, that there are three defects of three kinds, and — by omission — that no timing
measurement is claimed.

| Section | Supports the title | Evidence |
|---|---|---|
| Abstract | yes | Opens "Both are *assertions* … neither is checked. This paper reports what happens when each is falsified cheaply." Names all three defects. Closes by stating no latency figure is reported. |
| Introduction, central claim | yes | Block-quoted at line 140: "A security property asserted in build configuration, and a timing property asserted in design, are both unverified claims." |
| Contribution 1 | yes | configuration defect, found by ablation |
| Contribution 2 | yes | response-time defect, found by decomposition |
| Third instance (pre-list paragraph) | yes | vacuous invariant, found by mutating the specification |
| Methodology (evidence categories) | yes | five labelled categories; H2 (timing isolation) marked "Requires hardware; not tested here" |
| Results | yes | the one loose sentence — "the isolation property behaving as intended" — was tightened in `480902c` to say *logical* isolation and to note the harness advances a logical clock |
| Discussion | yes | the guard's unsound inference is the centrepiece |
| `sec:vacuity` | yes | a section of its own for the specification defect |
| `sec:timing` | yes | the decomposition and the drain it exposed |
| Conclusion | yes | rewritten in `4215c76`; closes on three defects in three kinds of assumption, each found cheaply |
| Figure captions | yes | none claims isolation or measured timing; Figure 6's states no number comes from the hardware panel |

**No section contradicts the title, and no section still claims timing isolation.**

---

## 5. Tables, equations, citations, captions, cross-references

Measured by parsing `manuscript.tex`:

| Item | Count | Status |
|---|---|---|
| `\bibitem` entries | 22 | all cited |
| Distinct `\cite` keys | 22 | all defined |
| Uncited bibliography entries | 0 | — |
| Undefined citations | 0 | — |
| `\label` definitions | 48 | — |
| Dangling `\ref` targets | 0 | — |
| Orphan table / figure labels | **0** | every table and figure is referenced in the text |
| `\includegraphics` | 8 | all at `width=\textwidth` |
| `figure` environments | 8 | no `figure*` remains (it cannot float properly in a one-column class) |
| `table` + `table*` environments | 9 + 2 = 11 | matches the 11 table labels |

Eight equation labels (`eq:Lbound`, `eq:accept`, `eq:decomp`, `eq:latency`, `eq:residual`,
`eq:spec`, `eq:tag`, `eq:u`) are defined but not `\ref`-ed. This is not a defect: they label
displayed equations for completeness, and a search confirms **no hard-coded equation numbers
appear in the prose**, so nothing can drift out of sync. Left as is.

### Figure placement

All eight floats land beside the text that references them:

| Figure | Page |
|---|---|
| 1 System architecture | 8 |
| 2 Command execution flow | 9 |
| 3 Command-path ablation | 16 |
| 4 Broker access control | 18 |
| 5 Security compromise comparison | 18 |
| 6 Experimental setup | 22 |
| 7 Compile-guard comparison | 24 |
| 8 Transport vs command authorisation | 25 |

Before `6e645a4` all eight reached the reader on pages 26–30 of a 30-page paper.

---

## 6. Do the supporting documents reflect 9,600 trials and twelve configurations?

| Document | Status |
|---|---|
| `paper/manuscript.tex` | correct: 9,600 and 12 throughout, with `tab:accounting` reconciling each count to a named artefact |
| `docs/CONTRIBUTIONS.md` | corrected in `7318ad4` (was 9,300 / eleven configurations) |
| `docs/SUBMISSION_CHECKLIST.md` | corrected in `7318ad4` (was 6,000 + 3,300 = 9,300) |
| `docs/CONSISTENCY_AUDIT.md` | correct; the 9,300 mentions in it describe the defect it fixed |
| `docs/VERSION_STRATEGY.md` | correct |
| `docs/Q2_GATE.md` | superseded-banner added; its body is a dated assessment against the eleven-arm campaign and is preserved as such |
| `docs/JOURNAL_ASSESSMENT.md` | count-correction banner added; conclusions unaffected |
| `README.md` | **corrected in this audit**: it described the manuscript as 25 pages. Now 30, and the three new reports are listed in the documentation table. |

No stale count survives outside the two banner-marked historical assessments and the audit
entry that records the fix.

---

## 7. Re-running everything

Every suite was re-run from the committed sources on a clean container.

| Suite | Command | Result |
|---|---|---|
| Firmware logic tests | `./tests/host/run_tests.sh` | **129 PASS, 0 FAIL** |
| Model checking, 3 configurations | `./formal/run_tlc.sh` | PASS `AlarmFSM`; PASS `Isolation`; PASS `AlarmFSM_unsafe` (violation required and reported) |
| Harness metamorphic + differential | `python3 -I experiments/test_harness.py` | all properties hold |
| Corpus rule controls | `python3 -I experiments/corpus/test_rule.py` | 8 / 8 pass |
| Trace conformance | `python3 -I experiments/test_conformance.py` | 19,529 transitions, 0 disallowed, negative control rejects |
| Real-broker access control | `./experiments/broker/run.sh` | 8 scenarios; **all verdicts identical to the committed run** |
| Printed type size | `python3 -I experiments/check_figure_type.py` | all 6 diagrams clear the 6 pt floor |
| Label fit | `python3 -I experiments/check_figure_fit.py` | no clipped or overflowing label |
| Plotted values vs raw records | `python3 -I experiments/validate_figures.py` | every value matches |

Combined across the three figure checks: **59 assertions, 0 failures.**

### Figure regeneration is byte-exact

Regenerating every figure from source and diffing against the committed copies:

```
$ python3 docs/figures/make_diagrams.py && python3 experiments/make_ablation_figures.py
$ git diff --name-only -- docs/images/*.svg
(empty)
```

**Every SVG regenerates byte-identically.** The PDFs differ only in their embedded creation
timestamp — identical byte sizes — which is cairosvg and matplotlib recording the build date.
This establishes that the figures in the manuscript are exactly what the committed sources
produce.

### The broker re-run reproduces

The eight scenarios were re-run against a freshly installed Mosquitto 2.0.18 in a new
container. All eight verdicts — connection accepted, delivered to device, command would
execute, HMAC verifies — are identical to the committed run. The only diff is in the broker's
own log lines:

```
-1794034880: Denied PUBLISH from device-9495947c (… 'home/alarm/esp32-1/cmd', … (6 bytes))
+1794055151: Denied PUBLISH from device-39152995 (… 'home/alarm/esp32-1/cmd', … (6 bytes))
```

Timestamp and random client identifier only; the denial itself, the topic and the message size
are unchanged. `broker_acl_summary.md` predicts exactly this, and it holds.

---

## 8. Repository inventory

| Directory | Files | Contents |
|---|---|---|
| `paper/` | 10 | manuscript source and PDF, short letters-format version, supervisor brief |
| `firmware/` | 9 | `smart_home.ino` v2.2.0 and shared headers |
| `formal/` | 31 | TLA+ specifications, three TLC configurations, runner, `tla2tools.jar` |
| `experiments/` | 48 | harness, ablation, fuzzer, sensitivity, corpus study, broker testbed, figure generators, five check scripts, committed results |
| `docs/` | 66 | 14 analysis documents, figure sources, generated images |
| `tests/` | 15 | host test suite |
| `tools/` | 3 | command signer, evaluator, measurement helper |
| `wokwi/` | 2 | simulator circuit |

165 tracked files.

---

## 9. Defects found by this audit

| # | Defect | Severity | Status |
|---|---|---|---|
| 1 | `README.md` described the manuscript as 25 pages | minor, user-visible | fixed |
| 2 | `README.md` documentation table omitted the three new reports | minor | fixed |
| 3 | `CONSISTENCY_AUDIT.md` stated 31 pages | minor, internal inconsistency | fixed, with the explanation |
| 4 | Previous report said "nine increments" | reporting error only, repository correct | resolved here |

**No scientific defect was found by this audit.** No result, statistic, table cell, figure
value or claim required correction.

---

## 10. Verdict

The repository is internally consistent, fully reproducible from committed sources, and the
manuscript compiles cleanly to 30 pages with no warnings and no unresolved references.

This is **technical completion**. It is not submission readiness, which additionally requires
the hardware measurement (Phase 3), the target journal's current requirements (Phase 4), an
institutional similarity report (Phase 5) and supervisor approval (Phase 7) — none of which
this audit can supply.
