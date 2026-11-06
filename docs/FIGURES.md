# Figure index and captions

Every figure exists as SVG (editable vector), PDF (for LaTeX) and PNG (for the README and
slides). Sources: `docs/figures/make_diagrams.py` for Figures 5-9, hand-authored SVG for
Figures 1-4, `experiments/make_figures.py` for Figure 10.

Regenerate everything with:

```bash
python3 docs/figures/make_diagrams.py     # Figures 5-9, and PDF exports of 1-4
python3 experiments/make_figures.py       # Figure 10
```

---

## Conventions used across all figures

These are stated here so a reader can interpret any figure without a per-figure legend.

| Convention | Meaning |
|---|---|
| **Solid border** | Implemented and exercised |
| **Dashed border** (`6 4`) | Optional feature: implemented and compiled in CI, never run on hardware |
| **Dotted border** (`2 4`) | Experiment apparatus: built and committed, never run |
| **Solid arrow** | Control or data flows this way |
| **Dashed arrow** (`4 3`) | Reporting or rejection path, not a control path |
| **Dotted arrow** | Observation only; no data path |
| Fill lightness | The only visual encoding besides line style. No distinction is carried by hue alone, so every figure survives greyscale printing and the common forms of colour-vision deficiency |

Typography is one font stack at four sizes throughout. The smallest type is 11 px in a figure at
most 1100 units wide, which is about 8 pt at a 90 mm single-column width.

---

## The figures

### Figure 1 — System architecture
`docs/images/architecture.{svg,pdf,png}`

> **Fig. 1.** Overall system architecture of the dual-core alarm. The safety domain on core 1
> owns the alarm state machine, sensing and actuation; the network domain on core 0 owns Wi-Fi,
> MQTT and command authentication. The two communicate only through two bounded queues and a
> status snapshot guarded by a zero-timeout mutex.

### Figure 2 — Alarm state machine
`docs/images/state_machine.{svg,pdf,png}`

> **Fig. 2.** The five-state alarm machine. Transitions are driven by sensor edges, the local
> button, authenticated remote commands and timeouts. The dashed region marks the states from
> which a disarm is accepted. Full transition table with guards and actions:
> `ARCHITECTURE.md` §3.2.

### Figure 3 — Event sequence
`docs/images/event_sequence.{svg,pdf,png}`

> **Fig. 3.** Event lifecycle from sensor assertion to MQTT publication, showing the bounded
> event queue, the drop-oldest-and-count overflow policy and the requeue-to-front retry. The
> delivery guarantee is at-most-once; see `ARCHITECTURE.md` §4.2.

### Figure 4 — Circuit wiring
`docs/images/circuit_wiring.{svg,pdf,png}`

> **Fig. 4.** Wiring of the reference device: PIR, door reed switch, arm button, buzzer, two
> status LEDs and an I2C OLED, with the optional mmWave radar input.

### Figure 5 — Command execution flow
`docs/images/command_flow.{svg,pdf,png}`

> **Fig. 5.** Command execution across the two cores. Parsing and HMAC-SHA256 verification run
> entirely on the network core, so a command flood consumes no safety-core time; only a verdict
> and an enumerated verb cross into the safety domain, through a bounded four-deep queue that
> the safety loop reads with a zero timeout. The replay counter is committed to non-volatile
> storage before the command is acted on, so an interruption cannot leave a command replayable.

### Figure 6 — Command sequence
`docs/images/command_sequence.{svg,pdf,png}`

> **Fig. 6.** Sequence diagram for an authenticated remote disarm. Dashed arrows are reporting
> rather than control: the system implements no command-acknowledgement protocol, and the
> operator infers the outcome from the retained state topic and the event stream.

### Figure 7 — Deployment architecture
`docs/images/deployment.{svg,pdf,png}`

> **Fig. 7.** Deployment architecture and software environment. Only the alarm device and its
> peripherals are required; the broker, consumer and fallback node are optional, and the alarm
> is fully functional offline. The measurement rig at right is built and committed but has not
> been run, which is the project's one open experimental step.

### Figure 8 — Research methodology
`docs/images/methodology.{svg,pdf,png}`

> **Fig. 8.** Methodology. Four independent evidence routes address the research question.
> Formal verification, simulation and fuzzing are complete and together establish *logical*
> isolation. The hardware route, which alone can establish *timing* isolation, is specified and
> unrun; no latency figure is claimed anywhere in this work.

### Figure 9 — Experimental setup
`docs/images/experimental_setup.{svg,pdf,png}`

> **Fig. 9.** Experimental setup. (A) The simulation harness compiles the unmodified firmware
> against host stubs and drives it with seeded adversarial input; because the harness advances a
> logical clock, latency variance is identically zero, which is why the statistical analysis is
> reported as pre-registered rather than as a result. (B) The hardware rig uses a second ESP32 as
> an independent measuring instrument across four conditions; conditions A-C need no RF isolation,
> while condition D requires an authorised isolated environment.

### Figure 10 — Adversarial campaign results
`experiments/results/fig_campaign.{pdf,png}`

> **Fig. 10.** Results of the 6,000-trial adversarial campaign against attack rates from 0 to
> 20,000 msg/s. Without command authentication the attacker arms the system in every flooded
> trial and the legitimate command is starved in every flooded trial; with authentication the
> attacker never succeeds and the legitimate command succeeds in all 3,000 trials. Palette
> validated for colour-vision deficiency (CVD ΔE 24.7) with distinct markers and line styles so
> the figure remains readable in greyscale.

---

## Figures that do not exist yet

Honest gaps, to be produced only once the data exists:

| Figure | Blocked on |
|---|---|
| Latency distribution per experimental condition | Hardware conditions A-C |
| Latency CDF, hardened vs baseline under radio stress | Hardware condition D |
| Ablation across the four security mechanisms | Ablation study (`PEER_REVIEW.md` §C5) |
| Parameter sensitivity surface | Sensitivity study (`PEER_REVIEW.md` §C4) |

No placeholder or illustrative version of any of these has been produced, because a figure
showing invented data is a fabrication regardless of how it is labelled.

---

## Licensing

All figures are original work by the author, generated from source in this repository. No figure
reuses third-party material, so no permissions are required for reproduction in a journal
submission.
