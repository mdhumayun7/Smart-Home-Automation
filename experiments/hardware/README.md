# Hardware experiment: safety-latency invariance (the measurement apparatus)

This directory specifies the **measurement side** of the headline experiment (claim C5 in
`docs/RESEARCH.md`): whether the sensor-to-siren latency of the safety loop stays constant
when the device is under stress on its own radio and command interface.

Scope and safety: this document covers only how to **instrument and measure** the device.
It deliberately does **not** describe how to generate radio-layer attacks. Any adversarial
RF or network load must be produced only inside an authorized, isolated test environment
(an RF-shielded enclosure or a network you own), under your institution's policy and with
permission, using established tooling you already have approval to run. Never direct any such
load at a network or device you do not own. If you cannot run attacks within those rules,
report the four non-attack conditions below and state the attack condition as future work.

## What is measured

One quantity, measured externally: the time from the **confirmed PIR edge** to the **buzzer
output going active**. It is measured with a logic analyser or a second microcontroller timer,
never by the device under test itself, so the measurement does not share the CPU whose
contention is being studied.

## Conditions (compared)

| # | Condition | Purpose |
|---|---|---|
| A | Idle network | Baseline latency distribution |
| B | Heavy *legitimate* MQTT traffic (frequent STATUS, large retained payloads) | Load without an attacker |
| C | Command-interface stress (high-rate command injection on your own broker) | The application-layer path, same as the SIL campaign but on real silicon |
| D | Radio-layer stress (authorized testbed only) | The on-chip coupling path SIL cannot model |

Conditions A-C need no attack tooling and can be run anywhere. Condition D is the one that
requires the authorized RF environment above; it is the novel measurement, but the paper
stands on A-C plus the formal isolation result even if D cannot be run.

## Apparatus in this directory

- `latency_probe/latency_probe.ino` - a sketch for a **separate** ESP32 (the measurer, not the
  device under test). It watches two GPIO lines wired to the alarm's PIR line and buzzer line
  and timestamps the interval with the hardware timer, printing one CSV row per intrusion.
  Using a separate board keeps the measurement clock independent of the device under load.
- `collect.py` - reads the CSV rows from the probe over serial and writes a tidy data file
  tagged with the condition label.
- `analyse_hw.py` - applies the **same** Mann-Whitney U test as the simulation analysis to the
  hardware latency samples, comparing each loaded condition against condition A, and emits the
  results table and a box-plot figure.

## Procedure (measurement only)

1. Flash the alarm firmware (v2.2, `AUTH_COMMANDS 1`) on the device under test. Flash
   `latency_probe` on the measurer. Wire the probe's two input pins to the alarm's PIR and
   buzzer pins and share a common ground.
2. For each condition A-D, trigger the PIR ~50 times (a bench function generator or a manual
   jig both work) and record the probe's interval rows with `collect.py --condition A` etc.
3. Run `analyse_hw.py`. It reports median and tail latency per condition and the test of
   whether each loaded distribution differs from condition A, and writes `fig_hw_latency.pdf`.
4. Record the numbers in the results table in `docs/EVALUATION.md`.

## Interpreting the outcome

- If the distributions are statistically indistinguishable, the core-pinning isolation claim
  holds on this SoC under these conditions - a positive, publishable result that extends the
  wired-industrial finding of Fischer et al. to single-chip Wi-Fi SoCs.
- If a loaded condition inflates the median or the tail, that is the more interesting result:
  it would show that core pinning alone does **not** isolate the safety function on this class
  of device, which directly challenges the standard advice and is worth reporting.

Either way the finding is reported with the measured distributions, not asserted.
