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
| Fill lightness | Every fill stays near-white, so no distinction depends on hue alone and all figures survive greyscale printing and the common forms of colour-vision deficiency |

Colour, where used, is a **secondary** cue reinforcing a label, and the same palette means the
same thing in every figure:

| Colour | Domain |
|---|---|
| Blue | Sensing, or a participant outside the device |
| Amber | Core 0, the network domain |
| Green | Core 1, the safety domain |
| Purple | Internal shared resource: queues and non-volatile storage |
| Red | Local outputs, or a rejection path |
| Slate | Cloud, broker and user-side components |

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

> **Fig. 6.** UML sequence for an authenticated remote disarm, in nine numbered steps.
> Participants are coloured by the domain they belong to and the trust boundary is marked:
> parsing and HMAC verification complete on core 0, so a forged or malformed command is rejected
> before the bounded queue and never reaches the safety core. The replay counter is committed to
> flash at step 5, before the command is acted on, so an interruption can at worst burn a counter
> value rather than leave the command replayable. Dashed arrows are reporting rather than
> control: the system implements no command-acknowledgement protocol, and steps 7 to 9 are
> best-effort at MQTT QoS 0, so the operator infers the outcome from the retained state topic and
> the event stream.

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

### Figure 11 — Transport-layer admission against application-layer authorization

`docs/images/security_paths.svg` (source: `docs/figures/make_diagrams.py`)

> **Fig. 11.** Where broker credentials decide admission and where the command key decides
> authority. The broker terminates TLS and re-originates every message, so an arriving command
> carries no evidence of its publisher. In the default build a command is acted on only if its
> HMAC-SHA256 tag verifies under `SECRET_CMD_KEY` and its counter exceeds the value in NVS, so
> an adversary holding leaked broker credentials but not the key is rejected (`cmd_badmac`) and
> the alarm still fires in all 300 trials. With `ALLOW_REMOTE_DISARM` set and
> `AUTH_COMMANDS` unset — the configuration whose compile guard this work removed — the tag
> check is short-circuited and the same adversary disarms the system, leaving the alarm to fire
> in only 50 of 300 trials. The control arm, identical in both builds, shows an adversary
> without credentials refused at the broker. Every relationship drawn is taken from
> `handleCommands` in the firmware and from `deliverGuarded` in the ablation harness; the counts
> are measured, from `experiments/results/ablation.jsonl`.

### Figure 12 — Command-path ablation results

`experiments/results/ablation_results.pdf` (source: `experiments/make_ablation_figures.py`)

> **Fig. 12.** Six command-path designs against the same adversary, on identical seeds, 300
> trials each. (a) The safety function holds in every design except the leaked-credential arm,
> where the alarm fires in 16.7 % of trials (95 % Wilson CI [12.9 %, 21.3 %]); bars show the
> point estimate and whiskers the Wilson interval. (b) Only the token-bucket rate limit harms
> operator availability, admitting 59.0 % of operator attempts under flood; the effect is not
> monotonic in attack rate, for the reason given in `docs/SECURITY_ANALYSIS.md` §9. (c)
> Capture-and-replay defeats every design except TLS with credentials held and the MAC with a
> monotonic counter. No design satisfies all three properties except the latter. Host-simulation
> results; see `docs/EXPERIMENTS.md` for the evidence taxonomy.

### Figure 13 — Credential-compromise comparison

`experiments/results/credential_matrix.pdf` (source: `experiments/make_ablation_figures.py`)

> **Fig. 13.** Safety-function activation and operator availability under each combination of
> controls and compromised secret, 300 trials per row on identical seeds. Neither broker-side
> authorization nor application-layer authentication dominates: a per-client ACL contains a
> compromised device credential but not a compromised controller, while a MAC survives
> credential compromise but not key compromise, and the key resides in the same flash image as
> the device's broker credentials. Only the layered configuration survives every row. Panel (b)
> also shows the owner-lockout result: under key compromise the adversary advances the
> persisted replay counter beyond the operator's range, and the operator is admitted in 0 of
> 1250 attempts. Model-based broker admission; see `docs/SECURITY_ANALYSIS.md` §3a for what is
> and is not modelled.

---

## Figures that do not exist yet

Honest gaps, to be produced only once the data exists:

| Figure | Blocked on |
|---|---|
| Latency distribution per experimental condition | Hardware conditions A-C |
| Latency CDF, hardened vs baseline under radio stress | Hardware condition D |
| Measured TLS handshake latency and encryption overhead | Hardware; the host harness has no TLS implementation, so no runtime TLS cost can be measured there |
| ACL behaviour against a real broker | A running Mosquitto instance with per-client ACLs. Needs a container, no hardware |

No placeholder or illustrative version of any of these has been produced, because a figure
showing invented data is a fabrication regardless of how it is labelled.

---

## Licensing

All figures are original work by the author, generated from source in this repository. No figure
reuses third-party material, so no permissions are required for reproduction in a journal
submission.
