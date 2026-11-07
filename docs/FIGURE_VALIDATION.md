# Figure-by-figure validation report

Written in response to a request for publication-quality validation of Figures 1–8, with a
technical-correctness check, a readability check at actual publication scale, a vector check,
a caption review, and confirmation that each figure matches the results, for every figure.

Scientific correctness took priority over appearance throughout. No result was changed to make
a figure look better. Two figures gained content because they were omitting a measured result
(Figure 8) or an implemented component (Figure 1); one was rebuilt because it described an
earlier, smaller version of the study (Figure 6).

---

## How the checks are run

Three scripts gate this, and all three are committed and runnable. They replace visual
inspection, which does not catch any of the three failures they find.

```bash
# 1. regenerate every diagram, then both plotted figures
python3 docs/figures/make_diagrams.py
python3 experiments/make_ablation_figures.py

# 2. printed point size of the smallest label in every figure the manuscript includes
python3 -I experiments/check_figure_type.py

# 3. clipped or overflowing labels, measured in the real font
python3 -I experiments/check_figure_fit.py

# 4. every plotted and quoted value, recomputed from the raw per-trial records
python3 -I experiments/validate_figures.py

# 5. rebuild the manuscript
cd paper && pdflatex manuscript.tex && pdflatex manuscript.tex && pdflatex manuscript.tex
```

Each script exits non-zero on failure, so all four can gate a build.

### Why these three checks and not inspection

**`check_figure_type.py`** reads each `\includegraphics` line out of `manuscript.tex`, finds
the matching SVG, takes the smallest `font-size` in it, and computes what that label prints at
on the A4 text block (450.7 pt wide with 1 in margins). Printed size is
`font_units × textwidth_pt × width_fraction / canvas_width_units`. A diagram inspected at
screen resolution gives no information about this at all.

Before this revision, **every one of the six diagrams printed below the 6 pt floor that
publishers set**, between 3.87 pt and 4.52 pt. That is unreadable on paper and no amount of
looking at the PNG reveals it.

**`check_figure_fit.py`** measures every label in the real DejaVu face at its real size with
Pillow, works out its drawn extent from the text anchor, and checks it against the tightest
enclosing `<rect>` and against the canvas. It found **45 overflowing labels** across the
diagram set, including several in figures that had already been inspected and judged clean.

**`validate_figures.py`** recomputes every plotted value from `results/ablation.jsonl` — the
raw per-trial records, not the derived summary the figures read — so a figure agreeing with a
stale aggregate cannot pass. It also refuses any diagram that hard-codes a `Table N` or
`Figure N` cross-reference into the artwork, which is how a figure silently goes stale when a
table is inserted above it.

### Current status

```
text block: 450.7 pt;  floor: 6.0 pt

figure                      frac   canvas  min unit  prints at
--------------------------------------------------------------
architecture.pdf            1.00     1100      16.0     6.56 pt
command_flow.pdf            1.00     1100      16.0     6.56 pt
ablation_results.pdf        1.00       (matplotlib - sized in pt by figstyle)
acl_architecture.pdf        1.00     1160      16.0     6.22 pt
credential_matrix.pdf       1.00       (matplotlib - sized in pt by figstyle)
experimental_setup.pdf      1.00     1100      16.0     6.56 pt
guard_decision.pdf          1.00     1180      16.0     6.11 pt
security_paths.pdf          1.00     1160      16.0     6.22 pt

every diagram label clears the 6 pt floor at its printed size
every label fits inside its box and inside the canvas
every plotted and quoted value matches the raw records
```

---

## Changes that apply to the whole set

| | Before | After |
|---|---|---|
| Type scale | diagrams at 11–18 units; `architecture.svg` on its own 12–23 scale | one four-size scale, 16 / 17.5 / 19.5 / 22 units, in `SZ` in `make_diagrams.py` |
| Typeface | six diagrams in DejaVu Sans, two matplotlib figures in a serif face | DejaVu Sans throughout, set once in `experiments/figstyle.py` |
| Figure width | 0.92, 0.95, 0.96 and 1.0 `\textwidth`, which silently changed the printed type size per figure | all `\textwidth` |
| In-figure titles | five diagrams repeated their caption as artwork | removed; the caption carries the title, which is the convention in every target venue |
| Colour semantics | red meant "unsafe" in Figures 7 and 8, "a step that blocked an attack" elsewhere in Figure 8, and "local outputs" in Figure 1 | red means exactly one thing across the set: an unauthorised command was acted on |
| Core colours | Figure 1 and Figure 2 used different tints for the same two cores | core 0 blue, core 1 green, in both |
| Colour alone | — | every distinction is also carried by a border style, a text label, or a printed number; palette checked for deuteranopia and for greyscale luminance separation |
| Cross-references | one diagram had "Measured in Table 3" baked into the artwork, and the credential table is Table 8 | no diagram carries a baked-in number; `validate_figures.py` fails the build if one reappears |
| Vector output | — | all eight are vector PDF; PNG is generated only for the repository README |

---

## Figure 1 — System architecture

| | |
|---|---|
| Source | `docs/figures/make_diagrams.py`, function `architecture()` |
| Output | `docs/images/architecture.{svg,pdf,png}`, canvas 1100 × 1190, PDF 34 kB |
| Regenerate | `python3 docs/figures/make_diagrams.py` |
| Printed size | 6.56 pt, clears the floor |
| Vector | yes, PDF via cairosvg from SVG |
| Fit check | pass |

**Before.** A hand-authored SVG with its own six-size type scale (12 to 23 units). Smallest
label printed at **4.52 pt**. Raising its type in place had already been tried and burst the
layout, because its boxes were sized to the old type.

**After.** Rebuilt as generated artwork on the shared scale.

**Technical correctness.** Every constant was re-read from
`firmware/smart_home/smart_home.ino` rather than copied from the old figure:

| Shown | Source line |
|---|---|
| GPIO 13, 14, 27, 23, 26, 25, 21, 22 | `PIN_PIR`, `PIN_DOOR`, `PIN_ARM_BTN`, `PIN_BUZZER`, `PIN_LED_ARMED`, `PIN_LED_ALARM`, `PIN_SDA`, `PIN_SCL` |
| debounce 40 ms | `DEBOUNCE_MS = 40` |
| PIR 10 s warm-up, 150 ms confirm | `PIR_WARMUP_MS`, `PIR_CONFIRM_MS` |
| exit and entry delay 10 s | `EXIT_DELAY_MS`, `ENTRY_DELAY_MS` |
| alarm 30 s | `ALARM_DURATION_MS` |
| OLED 250 ms (4 Hz) | `OLED_REFRESH_MS = 250` |
| Wi-Fi retry 15 s, MQTT retry 5 s | `WIFI_RETRY_MS`, `MQTT_RETRY_MS` |
| heartbeat 30 s | `HEARTBEAT_MS` |
| buzzer 2.7 kHz | `BUZZER_FREQ_HZ = 2700` |
| cmdQ 4 deep, eventQ 16 deep | `CMD_Q_LEN = 4`, `xQueueCreate(16, …)` |
| snapshot 500 ms; safety 0 ms, network 10 ms | `STATUS_COPY_MS`, `xSemaphoreTake(statusMutex, 0)`, `xSemaphoreTake(statusMutex, pdMS_TO_TICKS(10))` |

**Three content corrections.**

1. **The status snapshot was missing.** The firmware shares three things between the cores,
   not two. The figure drew two queues and its own subtitle said the cores "share nothing but
   two bounded queues", which contradicted the caption. The asymmetric mutex timeout is the
   isolation mechanism the paper argues for, so omitting it removed the figure's main point.
2. **The broker box presented the public demo broker as the only configuration.** The ACL
   matrix has since been reproduced against a private Mosquitto with TLS and per-client ACLs,
   so the box now names both.
3. **The client link was labelled "ARM, STATUS"**, omitting DISARM — the one command the whole
   paper is about.

**Caption review.** Rewritten. It now states the mutex timeouts explicitly (0 ms on the safety
side, 10 ms on the network side, so the network side cannot hold it long enough to delay the
alarm) and says every constant is transcribed from `smart_home.ino`. The previous caption
mentioned the status snapshot that the figure did not draw.

**Matches the results.** The figure makes no quantitative claim; every value is a firmware
constant, checked above.

---

## Figure 2 — Command execution flow

| | |
|---|---|
| Source | `make_diagrams.py`, function `command_flow()` |
| Output | `docs/images/command_flow.{svg,pdf,png}`, canvas 1100 × 760, PDF 31 kB |
| Printed size | 6.56 pt | 
| Vector | yes | Fit check | pass |

**Problems found.** Five overflowing labels and one structural error.

- The rejection box carried a 79-character line in a 460-unit box: it overran by 200 units on
  each side, across the enclosing band.
- The `authorise and execute` box overran by 55 units at each end, and its text ran underneath
  the adjacent `response` box.
- The queue badge sat across the core-1 boundary line, so the one object that crosses the
  domain boundary appeared to belong to the safety domain.
- The badge's own second line overflowed it.

**Fixes.** Rejection box widened to 580 units and its text split over two lines; the
authorise box widened to 560 and set in three lines; the badge moved into the gap between the
two domain bands, which is what it represents, with an arrow carrying the path into the safety
core.

**Technical correctness.** The stages, the event names (`cmd_badmac`, `cmd_unauth`,
`cmd_replay`, `cmd_rejected`, `cmd_ignored`), the `xQueueReceive(cmdQ, &m, 0)` call and the
"NVS write before acting" ordering are all taken from `handleCommands` and `networkTask`.
`CMD_Q_LEN = 4` matches the badge.

**Caption review.** Unchanged; it was already accurate and matches the drawing.

---

## Figure 3 — Command-path ablation

| | |
|---|---|
| Source | `experiments/make_ablation_figures.py`, `figure_ablation()`; style in `experiments/figstyle.py` |
| Output | `experiments/results/ablation_results.{pdf,png}`, 20 kB PDF |
| Regenerate | `python3 experiments/make_ablation_figures.py` |
| Printed size | set in points by `figstyle`: 8 pt value labels, 8.5 pt tick labels, 9.5 pt panel titles at `\textwidth` |
| Vector | yes, matplotlib PDF with `pdf.fonttype: 42` (TrueType embedded, not Type 3, which most publishers reject) |
| Fit check | not applicable (matplotlib lays out its own text) |

**Technical correctness.** `make_ablation_figures.py` asserts the shape of the aggregate
before drawing: it refuses to produce a figure if any arm does not hold exactly 300 valid
trials, because the caption's sample size would then be wrong. Separately,
`validate_figures.py` recomputes all eighteen plotted values from `ablation.jsonl` and the
Wilson interval drawn in panel (a):

```
transport_leaked: alarm 16.7%   95% Wilson [12.9, 21.3]   ok
ratelimit:        availability 59.0%                      ok
… 30 checks, 0 mismatches
```

**Design.** Horizontal bars, because six design names do not fit as vertical tick labels at a
legible size. Panel (c) inverts the reading — there a high value is the failure — so its
colour rule is inverted with it, and blue continues to mean "this design holds the property"
in all three panels. A zero-height bar is invisible, so zeros carry a tick marker in the row's
own colour; an earlier version drew that marker in a fixed colour, which asserted the opposite
of the bar it stood in for in one panel.

**Caption review.** Changed. The request was that sample sizes appear in the figure or the
caption; they were in neither. The caption now states *n* = 300 per bar in panels (a) and (c)
and 1,250 operator attempts per bar in panel (b).

**Matches the results.** Yes, by recomputation from the raw records, not from the summary.

---

## Figure 4 — Broker access control

| | |
|---|---|
| Source | `make_diagrams.py`, function `acl_architecture()` |
| Output | `docs/images/acl_architecture.{svg,pdf,png}`, canvas 1160 × 686, PDF 22 kB |
| Printed size | 6.22 pt | Vector | yes | Fit check | pass |

**Problems found.** Three overflowing labels, one stale cross-reference, one incomplete claim.

- The subtitle was a single 135-character line that ran 31 units off each edge of the canvas.
- Two body lines overran their cards.
- The summary box ended "Measured in Table 3." **The credential table is Table 8.** A number
  baked into artwork cannot be checked by LaTeX and goes stale the moment a table is inserted
  above it. The reference is gone, the caption carries it via `\ref`, and
  `validate_figures.py` now fails the build if any diagram reintroduces one.
- The summary stated only the compromise the layered build *survives*. The request was to show
  "precisely which compromises each configuration withstands or fails against", and stating
  one direction implied the layered configuration is unconditional.

**Fixes.** Canvas narrowed from 1200 to 1160 (6.01 pt to 6.22 pt). Subtitle split over two
lines. Card text rewrapped at 33 characters. The summary box now gives both directions: a
flash dump yields the device credential and the key together and the ACL still refuses that
identity; a compromised controller host yields a credential the ACL must permit together with
the key, and neither layer refuses it.

**Technical correctness.** The permission matrix was checked line by line against
`experiments/broker/setup.sh`:

| Figure | `acl_perclient` |
|---|---|
| controller: publish on cmd = allow | `user operator` / `topic write home/alarm/+/cmd` |
| controller: subscribe to cmd = deny | not granted — deny-by-default once `acl_file` is set |
| controller: publish on stat = deny | only `topic read home/alarm/+/stat` is granted |
| device: subscribe to cmd = allow | `user device` / `topic read home/alarm/+/cmd` |
| device: publish on stat = allow | `topic write home/alarm/+/stat` |
| device: publish on cmd = deny | not granted |

A terminology mismatch was found and fixed: the figure says *controller* and the broker
username is `operator`. The figure now records both, so the artwork, the manuscript and
`experiments/broker/` share one vocabulary.

**Caption review.** Rewritten. It no longer says "as modelled" — the matrix is also the
Mosquitto `acl_file` — gives the broker usernames, and states both failure directions.

---

## Figure 5 — Security compromise comparison

| | |
|---|---|
| Source | `make_ablation_figures.py`, `figure_matrix()` |
| Output | `experiments/results/credential_matrix.{pdf,png}`, 18 kB PDF |
| Vector | yes, fonttype 42 | Fit check | not applicable |

**Technical correctness.** Nine rows, indexed by which secret the adversary holds rather than
by mechanism, which is the comparison the paper is making. Every one of the nine rows was
checked against both `ablation_summary.json` and the nine cells of Table 8:

```
ok  TLS only, no secret                 alarm 300/300  admitted 1250/1250  disarm no
ok  TLS only, any broker credential     alarm  50/300  admitted 1250/1250  disarm yes
ok  TLS + ACL, shared credential        alarm  50/300  admitted 1250/1250  disarm yes
ok  TLS + ACL, controller credential    alarm  50/300  admitted 1250/1250  disarm yes
ok  TLS + ACL, device credential        alarm 300/300  admitted 1250/1250  disarm no
ok  HMAC, any broker credential         alarm 300/300  admitted 1250/1250  disarm no
ok  HMAC, controller credential + key   alarm  50/300  admitted    0/1250  disarm yes
ok  TLS+ACL+HMAC, device cred + key     alarm 300/300  admitted 1250/1250  disarm no
ok  TLS+ACL+HMAC, controller cred + key alarm  50/300  admitted    0/1250  disarm yes

9 cells checked; 0 mismatches
```

**On not exaggerating the layered configuration.** The bottom row is the layered build under a
compromised controller host: 16.7 % alarm activation and 0 % operator availability. It is
drawn at the same weight as every other row and in the fail colour, with its value printed. No
visual device favours the layered configuration. The owner-lockout result — 0 of 1,250 — is
visible as a marked zero rather than an absent bar.

**Caption review.** Unchanged; it already stated that the layered configuration "withstands
every single-secret compromise and a device flash dump, and falls to a compromised controller
host", which is exactly what the figure shows.

---

## Figure 6 — Experimental setup

| | |
|---|---|
| Source | `make_diagrams.py`, function `experimental_setup()` |
| Output | `docs/images/experimental_setup.{svg,pdf,png}`, canvas 1100 × 614, PDF 26 kB |
| Printed size | 6.56 pt | Vector | yes | Fit check | pass |

**Problem found: the figure described an earlier, smaller study.** It listed two experiments,
a campaign and a fuzzer. Since it was drawn, the ablation (E3), the sensitivity sweep (E5), the
real-broker testbed (E6) and the corpus study have all been run and are reported in the paper,
and **none of them appeared in the figure**. A reader comparing Figure 6 with the trial
accounting in Table 6 would have found the figure short by 3,600 trials, 180 grid cells, 8
broker scenarios and 135 projects. Eleven labels also overflowed.

**Fixes.** Panel A rebuilt around the full inventory. Every count drawn was checked against its
committed artefact:

| Drawn | Artefact | Verified |
|---|---|---|
| 6,000 trials, rates 0–20,000 msg/s | `summary.json` | 3,000 baseline + 3,000 hardened over 6 rates |
| 3,600 trials, 12 configurations, 300 each | `ablation.jsonl` | 3,600 records, 12 modes, 300 per mode |
| 3,000,000 iterations | `fuzz.json` | `iterations: 3000000` |
| 180 grid cells | `sensitivity.jsonl` | 180 lines |
| 8 scenarios, Mosquitto 2.0.18 | `broker_acl.jsonl` | 8 lines |
| 135 projects, commit-pinned | `corpus/commit_shas.tsv` | 135 lines; `corpus.json` `n_projects: 135` |
| guard rule, 8 controls, 0 hits | `corpus/test_rule.py`, `findings.json` | 8 controls pass; `rule1_total_hits: 0` |

**On never implying the hardware has been measured.** Panel B keeps a dotted frame throughout,
is headed "Not yet measured", and carries in red: *rig specified; no result in this paper comes
from it*. The per-row "no RF isolation" column became a footnote, where it no longer collides
with the longest condition label.

**Caption review.** Rewritten, because it had become wrong in a way that mattered. It called
panel A "the simulation harness used for all results" — but E6 ran against a live Mosquitto
instance and is not a simulation, and the paper's evidence taxonomy depends on that
distinction. The caption now separates the host simulation (E1–E5) from the real-broker
testbed (E6), points at the trial-accounting table, and repeats that no number anywhere in the
paper comes from panel B.

---

## Figure 7 — Compile-guard comparison

| | |
|---|---|
| Source | `make_diagrams.py`, function `guard_decision()` |
| Output | `docs/images/guard_decision.{svg,pdf,png}`, canvas 1180 × 692, PDF 29 kB |
| Printed size | 6.11 pt | Vector | yes | Fit check | pass |

**Problems found.** Eight overflowing labels; a decision diamond too narrow for the identifier
inside it, so `UNAUTHENTICATED_DISARM` crossed the diamond's edges; a stray arrowhead left in
mid-air where two "yes" edges merged; and a colour error.

**The colour error.** The `#error` outcome — the corrected guard refusing to build — was drawn
in red. Refusing an unsafe build is the *protective* outcome, and under the figure's own colour
rule red says the opposite. It is now green, and a key states the rule: red marks a build in
which an unauthenticated DISARM can be acted on, green marks one in which it cannot. Under that
rule the corrected panel has no red in it, which is the point the figure is making.

**Technical correctness.** The decision logic was transcribed from the preprocessor conditions
in `smart_home.ino`:

- Before: `ALLOW_REMOTE_DISARM` → `AUTH_COMMANDS`? → if no, `MQTT_USE_TLS && MQTT_HAS_LOGIN`?
  → if yes, compiles. Both branches reach the same outcome box, which is the defect: a signed
  build reaches it legitimately, an unsigned one through the unsound transport test.
- After: `ALLOW_REMOTE_DISARM` → `AUTH_COMMANDS`? → if no,
  `ACKNOWLEDGE_UNAUTHENTICATED_DISARM` defined? → if no, `#error`.

**Caption review.** Unchanged; it already described both branches reaching the same outcome
and the repair removing the unsound branch rather than adding a mechanism.

---

## Figure 8 — Transport security versus command authorisation

| | |
|---|---|
| Source | `make_diagrams.py`, function `security_paths()` |
| Output | `docs/images/security_paths.{svg,pdf,png}`, canvas 1160 × 856, PDF 27 kB |
| Printed size | 6.22 pt | Vector | yes | Fit check | pass |

**Problem found: the figure omitted a measured result, and the omission was the one the
request named.** The brief was explicit — *do not imply that layered security survives a
compromised controller host holding both the permitted credential and command key*. Under
`AUTH_COMMANDS` the figure showed two rows: the operator succeeding, and an adversary with
leaked credentials but no key being rejected. An adversary holding **both** a permitted
credential and the key was absent, so the panel implied the signed build is unconditional.

**Fix.** A third row, measured, not asserted. The adversary holding the controller credential
and the command key is admitted by the broker, passes the device's tag and counter checks
because the signature is genuine, and disarms the system; the alarm fires in 50 of 300 trials
(`acl_hmac_controllerdump` in `ablation.jsonl`, 16.7 %). A line beneath the panel says what the
row is: a compromised controller host, holding a credential the ACL must permit plus the key,
refused by neither layer.

**The colour error.** Red previously marked both an intermediate check that *blocked* an attack
(`tag fails: cmd_badmac`) and an outcome in which the attack *succeeded*. Those are opposite
things. Colour is now confined to the Outcome column; the Publisher, Broker and Device-check
columns are neutral and say what happened in words. A key states the rule, and every outcome
also prints its count, so no meaning rests on colour alone.

**Technical correctness.** Broker admission is modelled by `deliverGuarded`/`admit` in
`experiments/ablation.cpp`; the device-side checks are `handleCommands` in `smart_home.ino`.
The three counts drawn — 300/300, 50/300, 300/300 — are checked against the raw records by
`validate_figures.py`, which also verifies that the literal strings `300/300` and `50/300`
still appear in the SVG and still agree with the data.

**Caption review.** Rewritten to describe the new row.

---

## Figures not in the manuscript

`command_sequence`, `deployment`, `methodology`, `state_machine`, `event_sequence` and
`circuit_wiring` live in `docs/images/` and appear in the repository README. They were brought
to the same standard — 22 further overflowing labels fixed — so the whole set reads as one
system, but they are not part of the submission and are not validated against results here.

---

## Unresolved

None for Figures 1–8. All eight pass the type-size check, the fit check and the value check,
and all eight captions have been reviewed against what the figure now draws.

The one standing caveat is not a figure defect: **Figure 6 panel B describes apparatus that has
not been run.** It is drawn as such — dotted frame, "Not yet measured", a red line saying no
result comes from it — and the caption repeats it. If conditions A–C are ever measured, that
panel becomes a results figure and both it and the caption must be rewritten.
