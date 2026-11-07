# Reproducibility guide

How to reproduce every result in the manuscript and the report, what each command establishes,
and which results cannot be reproduced and why.

Repository: `github.com/mdhumayun7/Smart-Home-Automation`

---

## 1. What is reproducible, and to what degree

| Result | Reproducible | Degree |
|---|---|---|
| E1, E2 adversarial campaign, 6,000 trials | yes | bit-exact, fixed seeds |
| E3 command-path ablation, 3,600 trials | yes | bit-exact, fixed seeds |
| E4 fuzzing, 3,000,000 iterations | yes | bit-exact, fixed seeds |
| E5 detector sensitivity, 180 cells | yes | bit-exact, fixed seeds |
| E6 live broker, 8 scenarios | yes | **verdicts** identical; log timestamps and client IDs differ |
| E7 corpus study, 135 projects | partly | the committed corpus reproduces exactly; a re-fetch will not return the same 135 projects |
| E8 trace conformance, 19,529 transitions | yes | bit-exact |
| E9 model checking | yes | bit-exact state counts |
| Figures | yes | SVG **byte-identical**; PDFs differ only in embedded creation timestamps |
| Resource cost on the target | yes | requires the Arduino toolchain |
| Hardware conditions A–D | **no** | **they were never run; no data exists** |

### Why the results are deterministic

Seeds are fixed at 1000, 2000 and 7. The ablation harness forks per trial, so no trial can
influence the next through accumulated state. All statistics are implemented with the Python
standard library only, so no external package version can change a reported value.

---

## 2. Environment

The committed results were produced with:

| Component | Version |
|---|---|
| GCC / g++ | 13.3.0 |
| Python | 3.13.18 |
| TLC | TLC2 2026.10.24.013619 (rev `2ef2af8`), from `tla2tools.jar` v1.8.0 |
| Mosquitto | 2.0.18 |
| matplotlib | 3.11.2 |
| pdflatex | TeX Live 2024 |
| pandoc | 3.1.3 |
| arduino-esp32 | 2.0.17 and 3.3.12, both evaluated |

```bash
pip install -r requirements.txt
```

The verification and experiment results need GCC, Python, Java and Mosquitto. The firmware
resource measurement additionally needs `arduino-cli` with the `esp32:esp32` core.

---

## 3. Verification suites

Run these first. Each would fail if a known defect recurred.

```bash
bash tests/host/run_tests.sh
```
129 assertions over the firmware logic. **Three of them are negative build tests: they pass when
the compiler refuses the defective configuration.** A build that succeeds there is a test
failure.

```bash
bash formal/run_tlc.sh
```
Expected output:

```
AlarmFSM             166 states generated,   25 distinct, no error      PASS
Isolation          2,686 states generated,  660 distinct, no error      PASS
AlarmFSM_unsafe    Invariant NoUnauthRemoteDisarm is violated           PASS
```

The third configuration **must report a violation.** It sets `AllowUnauthDisarm = TRUE`, modelling
the defective build. A passing run means the invariant has become vacuous again, which is the
regression this check exists to catch, and the runner treats it as a build failure. It requires
the specific string `Invariant NoUnauthRemoteDisarm is violated`, not merely a non-zero exit, so
that a syntax error or a missing constant cannot be mistaken for the expected violation.

```bash
python3 experiments/test_conformance.py
```
19,529 firmware transitions (7,044 + 5,282 + 7,206) checked against the transition relation
parsed from `formal/AlarmFSM.tla`. Expect **0 disallowed transitions**, and the negative control
— a forbidden `Disarmed → Alarm` transition — **rejected**. Without that control a checker that
accepted everything would also report zero violations.

```bash
python3 experiments/test_harness.py
python3 experiments/corpus/test_rule.py
```
Harness metamorphic and differential properties; 8 corpus-rule controls including this project's
own pre-repair guard as a positive control and its repaired guard as a negative control.

---

## 4. Experiments

### E1, E2 — the adversarial campaign

```bash
bash experiments/run.sh
```
Writes `experiments/results/summary.json`, `fuzz.json` and `sensitivity.jsonl`.

Expect across 6,000 trials: **no adversary disarms the device and no safety invariant is
violated.** With authentication a legitimate command takes effect in all 3,000 trials regardless
of attack rate; in the baseline, flooding starves it in every flooded trial.

The fuzzing campaign (E4) should report **no crash, no sanitizer report and no accepted input**
across 3,000,000 iterations. Note what this is evidence of: memory safety and parser robustness.
Against a 128-bit tag, zero forgeries in three million attempts is the expected outcome whether
the implementation is sound or not.

E5 should reproduce the detector's shipped-default failure: **1,597 of 2,000 benign ten-minute
runs trigger (79.9%)** at threshold 8 within a 2,000 ms window. The firmware now ships
`DEAUTH_THRESHOLD = 12`.

### E3 — the command-path ablation

```bash
bash experiments/run_ablation.sh
python3 experiments/analyse_ablation.py
```
Writes `experiments/results/ablation.jsonl`, 3,600 trials across 12 configurations.

Expect exactly:

| Arm | Alarm | 95% Wilson | Avail. | Replay | Disarms |
|---|---|---|---|---|---|
| No command defence | 300/300 | [98.7, 100.0] | 100.0% | 100% | 0 |
| Token-bucket rate limit | 300/300 | [98.7, 100.0] | **59.0%** | 100% | 0 |
| Static shared token | 300/300 | [98.7, 100.0] | 100.0% | 100% | 0 |
| TLS, credentials held | 300/300 | [98.7, 100.0] | 100.0% | 0% | 0 |
| TLS, credentials leaked | **50/300** | **[12.9, 21.3]** | 100.0% | 100% | 246 |
| HMAC-SHA256 + counter | 300/300 | [98.7, 100.0] | 100.0% | 0% | 0 |
| TLS+ACL, shared credential | 50/300 | [12.9, 21.3] | 100.0% | 100% | 246 |
| TLS+ACL, controller credential | 50/300 | [12.9, 21.3] | 100.0% | 100% | 246 |
| TLS+ACL, device credential | 300/300 | [98.7, 100.0] | 100.0% | 0% | 0 |
| HMAC, controller cred + key | 50/300 | [12.9, 21.3] | **0.0%** | 98% | 234 |
| TLS+ACL+HMAC, device cred + key | 300/300 | [98.7, 100.0] | 100.0% | 0% | 0 |
| TLS+ACL+HMAC, controller cred + key | 50/300 | [12.9, 21.3] | **0.0%** | 98% | 234 |

Two Fisher exact tests, one-sided: rate limiter against the others,
*p* = 3.53 × 10⁻¹⁸⁴; transport leaked against transport held, *p* = 9.83 × 10⁻¹¹⁹.

Availability denominators are **1,250 operator attempts per arm**, not 300. A single attempt per
trial measured where in the token bucket's refill cycle the attempt landed rather than the
admission rate; this is one of the four harness defects documented in the report.

The two **0 of 1,250** rows are the owner-lockout result. The adversary signs commands with a
counter far above the operator's; the device persists it, as replay resistance requires; every
later legitimate command then carries a lower counter and is correctly rejected as a replay.

### E6 — the live broker

```bash
bash experiments/broker/setup.sh     # private CA, server certificate, passwords, ACL files
bash experiments/broker/run.sh       # 8 scenarios
python3 experiments/broker/validate_acl.py
```

Requires Mosquitto 2.0.x and OpenSSL. `setup.sh` generates key material locally; **none of it is
in the repository**, and the archive excludes `*.key`, `*.pem`, `*.crt` and `passwd*` for that
reason.

Expect these eight verdicts:

| | Adversary identity | Connected | Delivered | Would execute |
|---|---|---|---|---|
| control | controller (legitimate) | yes | yes | yes |
| A | no credentials | **no** | no | no |
| C | controller credential | yes | yes | **yes** |
| D | device credential | yes | **no** | no |
| E | device credential + key | yes | **no** | no |
| E′ | controller credential + key | yes | yes | **yes** |
| control | controller, shared ACL | yes | yes | yes |
| B | shared credential | yes | yes | **yes** |

**E and E′ are the decisive pair.** The same valid signature is refused when it arrives from the
device identity and accepted when it arrives from the controller identity. What stops scenario E
is the access control list, not the signature.

In MQTT 3.1.1 a PUBACK is **not** evidence of delivery, and the absence of a return code means
*refused by policy*. The harness reads the broker's own log rather than inferring from the
client's acknowledgement.

### E7 — the corpus study

```bash
export GITHUB_TOKEN=...
bash experiments/corpus/fetch_corpus.sh
python3 experiments/corpus/build_corpus.py
python3 experiments/corpus/analyse_guards.py
```

Expect, against the **committed** corpus: rule 1 **0 hits** across 135 projects; rule 2 flags
**18**, of which 9 were manually confirmed and 9 were false positives.

A re-fetch will not return the same 135 projects: the result depends on the state of third-party
repositories and on the GitHub search API at fetch time. The corpus metadata, the commit pins and
the rejection counts are committed so the *analysis* reproduces without re-fetching, and the
eight rule controls reproduce independently of the corpus.

**The 18-of-135 figure is not a prevalence estimate.** Rule 2 over-counts monitoring projects by
roughly half and under-counts non-GPIO actuation by an unknown amount.

---

## 5. Figures

```bash
python3 docs/figures/make_diagrams.py
python3 experiments/make_ablation_figures.py
python3 experiments/validate_figures.py
python3 experiments/check_figure_type.py
python3 experiments/check_figure_fit.py
```

`validate_figures.py` recomputes every plotted value from the raw per-trial records in
`ablation.jsonl`, not from the derived summary — reading the summary would only confirm that the
summary and the figure agree. 59 assertions; all must pass. Section 5 fails the build if any
diagram hard-codes a `Table N` or `Figure N` cross-reference.

`check_figure_type.py` fails if any label would print below 6 pt. The printed size is

```
pt_printed = font_units × (450.74 pt × width_fraction) / canvas_width_units
```

which is invisible on screen: a 17.5-unit label on a 1,900-unit canvas at `\textwidth` prints at
4.2 pt. `check_figure_fit.py` measures every label in the real DejaVu faces with Pillow and fails
on clipping.

Expect every SVG to regenerate **byte-identically**.

---

## 6. Documents

```bash
cd paper   && pdflatex manuscript.tex   # three passes
cd report  && pdflatex report.tex       # three passes, for the ToC, LoF and LoT
```

Expect: manuscript 31 pages, 0 errors, 0 warnings, 0 undefined references, 22/22 bibitems
resolved. Report 98 pages, 0 errors, 0 undefined references, 8 figures, 26 tables.

Before building the report, regenerate its data so the commit hash and counts match the tree:

```bash
python3 tools/build_report_data.py
```

This fails if any curated appendix entry names a file that is not present.

```bash
python3 tools/build_figure_collection.py   # the distributable figure archive
python3 tools/build_figure_preview.py      # the 16-page preview
python3 tools/build_source_archive.py      # the source archive
```

---

## 7. Firmware

```bash
cp firmware/smart_home/secrets.example.h firmware/smart_home/secrets.h
# Edit secrets.h: set Wi-Fi credentials and REPLACE the demonstration keys.
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/smart_home \
  --build-property "compiler.cpp.extra_flags=-DAUTH_COMMANDS=1"
```

Expected resource cost at build time:

| Framework | Flash | of budget | RAM | of budget |
|---|---|---|---|---|
| arduino-esp32 2.0.17 | 793,433 B | 60.5% | 46,372 B | 14.2% |
| arduino-esp32 3.3.12 | 968,221 B | 73.9% | 49,876 B | 15.2% |

The 175 kB difference is a property of the framework, not of this firmware.

**Two configurations are rejected at compile time**, and that rejection is the correct outcome:

- `ALLOW_REMOTE_DISARM=1` without `AUTH_COMMANDS=1`, unless
  `ACKNOWLEDGE_UNAUTHENTICATED_DISARM` is defined. The escape hatch exists only so the research
  baseline stays reproducible.
- `AUTH_COMMANDS=1` with the published demonstration key. Authentication against a published key
  is not authentication.

---

## 8. What cannot be reproduced

### Hardware conditions A–D

**They were never run. No hardware data exists, and none can be derived from what is here.**

No physical ESP32 was available in the environment that produced these results: no
`/dev/ttyUSB*` or `/dev/ttyACM*` devices, no USB subsystem, no `arduino-cli`, no Python `serial`
module, and only `eth0`, `ifb0` and `lo` as network interfaces. No RF-shielded enclosure, which
condition D requires.

Consequently **no latency figure is reported anywhere in this project**, and no timing claim is
made. The simulation harness advances a logical clock, so safety latency is the same constant in
every trial and its variance is identically zero — a property of the simulator, not a finding
about the firmware. **Logical isolation is proved; physical timing invariance is unmeasured.**

To run the conditions yourself:

```bash
# Flash the device under test and the probe, then:
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition A --n 200 --out results_hw.csv
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition B --n 200 --out results_hw.csv
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition C --n 200 --out results_hw.csv
python3 experiments/hardware/analyse_hw.py --in results_hw.csv --control A
```

Two requirements are easy to get wrong and invalidate the measurement:

- **The two boards must share a common ground.** Without it they have no shared reference and the
  readings are meaningless.
- **Do not reflash the device under test between conditions.** The firmware must be
  byte-identical across all four, or the comparison is between two systems rather than two load
  levels.

The analysis is **pre-registered**: two-sided Mann–Whitney *U* with tie correction, α = 0.05,
power 0.80, *n* = 200 per condition, detecting a 0.29 SD shift. It was committed before any data
existed. **Do not substitute a different test after seeing the data.** The full protocol is in
`docs/HARDWARE_VALIDATION_PLAN.md` and the step-by-step procedure for A–C in
`docs/HARDWARE_A_TO_C_RUNBOOK.md`.

`experiments/hardware/analyse_hw.py` was verified end to end on explicitly synthetic input as a
script self-test. That synthetic file was deliberately **not** committed, so it cannot be
mistaken for data. `results_hw_TEMPLATE.csv` carries the schema `condition,index,latency_us` and
no rows.

### Similarity screening

No licensed tool was available. **No similarity percentage is claimed anywhere in this project,
official or otherwise.** `paper/submission/similarity/` contains the prepared file and the
procedure for institutional screening.

### Journal metrics

The ranking source returned an automated challenge, which was **not** circumvented. **No journal
quartile is asserted anywhere in this work.**

---

## 9. Continuous integration

`.github/workflows/` re-runs the formal verification and a reduced adversarial campaign on every
push, so neither the vacuity defect nor a silently accepting conformance checker can recur
without the build failing.
