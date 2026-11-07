# Conditions A–C: a runbook

A focused, optional runbook for the three hardware conditions that need **no institutional
permission and no RF-shielded enclosure**. Condition D is excluded deliberately; it is covered
in `HARDWARE_VALIDATION_PLAN.md` §7 and must not be attempted without written permission.

**Nothing here has been run. No measurement exists, and none is reported in the manuscript.**
This document is a procedure, not a result.

Why it is worth doing: A–C address the objection a reviewer is most likely to raise, and B and
C are precisely where the simulated results most need a physical counterpart. Cost is about
**£25 and an afternoon**.

---

## Before you start

Four things must be true. If any is false, stop and fix it first.

- [ ] Two **dual-core** ESP32 boards (ESP32-WROOM-32 DevKit). An ESP32-C3 or -S2 is
      single-core and **cannot test the configuration this paper is about.**
- [ ] A machine with USB and `arduino-cli`, with the `esp32:esp32` core installed.
- [ ] A Wi-Fi network **you control** and an MQTT broker you control.
- [ ] `firmware/smart_home/secrets.h` created from the example, with the **demo keys
      replaced**. The build refuses `AUTH_COMMANDS=1` with the published demo key.

## Shopping list

| Item | Qty | Note |
|---|---|---|
| ESP32-WROOM-32 DevKit v1 | 2 | one is the device under test, one is the probe |
| micro-USB or USB-C data cable | 2 | charge-only cables are a silent failure |
| Jumper wires, female-to-female | 3 | two signals and the common ground |
| Push button, momentary | 1 | substitutes for the PIR, so no 10 s warm-up per trial |
| Passive piezo buzzer | 1 | the siren line being sensed |
| Breadboard, half size | 1 | — |

A PIR (HC-SR501) is optional for A–C: the button gives the same rising edge without the
warm-up, and the quantity measured starts at the sensor edge either way.

---

## Step 1 — Wire it

Diagram: `docs/images/hardware_rig.pdf`.

| Device under test | → | Probe | Probe constant |
|---|---|---|---|
| GPIO 13 (sensor line) | → | GPIO 34 | `PIN_PIR_SENSE` |
| GPIO 23 (buzzer / siren line) | → | GPIO 35 | `PIN_BUZZ_SENSE` |
| GND | → | GND | — |

**The common ground is not optional.** Without a shared reference the two clocks have nothing
in common and the numbers are meaningless. This is the most frequent way this rig is got
wrong.

GPIO 34 and 35 are input-only on the ESP32, so the probe physically cannot drive a line it is
meant to observe.

## Step 2 — Flash both boards

```bash
# device under test, hardened configuration
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/smart_home \
  --build-property "compiler.cpp.extra_flags=-DAUTH_COMMANDS=1"
arduino-cli upload --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 firmware/smart_home

# probe
arduino-cli compile --fqbn esp32:esp32:esp32 experiments/hardware/latency_probe
arduino-cli upload --fqbn esp32:esp32:esp32 -p /dev/ttyUSB1 experiments/hardware/latency_probe
```

Record both `arduino-cli version` and the `esp32:esp32` core version. They belong in the paper.

## Step 3 — Sanity check before collecting anything

Do not skip this. Collecting 600 samples against a miswired rig wastes the afternoon.

```bash
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition A --n 5 --out /tmp/smoke.csv
cat /tmp/smoke.csv
```

- [ ] Five rows appear, with `latency_us` values in a plausible range and not all identical.
- [ ] Zero or negative values mean the two edges are swapped — check which pin goes where.
- [ ] No rows at all means the probe is not seeing edges — check the common ground first.

Delete `/tmp/smoke.csv`. It is not data.

## Step 4 — Collect

**Do not reflash the device under test between conditions.** The firmware must be
byte-identical across all three, or you are comparing two systems rather than two load levels.

```bash
# A — control: Wi-Fi up, broker reachable, no other traffic
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition A --n 200 --out results_hw.csv

# B — legitimate MQTT load: frequent STATUS requests, large retained payloads
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition B --n 200 --out results_hw.csv

# C — command-interface stress: high-rate publication on the device's own command topic
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition C --n 200 --out results_hw.csv
```

`collect.py` appends, so all three accumulate in one file. Let the system return to the armed
state between samples.

**Why 200 and not 50.** At 200 samples per condition the pre-registered test detects a shift
of about 0.29 standard deviations (α = 0.05, power = 0.80) — roughly 52 µs if the idle spread
is 180 µs. At 50 it only detects about 0.59 SD, which would miss a degradation that still
matters against a 10-second entry delay. The full power table is in
`HARDWARE_VALIDATION_PLAN.md` §6.

Collection order: run A first, then B, then C, then **A again** as a drift check. If the second
A differs from the first, something in the environment moved and the run is not trustworthy.

## Step 5 — Analyse

```bash
python3 experiments/hardware/analyse_hw.py --in results_hw.csv --control A
```

Prints n, median, p95 and maximum per condition, applies the **pre-registered** two-sided
Mann–Whitney *U* test with tie correction against A, and writes `fig_hw_latency.pdf`.

**The test was committed before any data existed. Do not substitute a different test after
seeing the data.** If you think the pre-registered test is wrong, say so in the paper and
report both.

## Step 6 — Record

Commit alongside the CSV:

- [ ] `results_hw.csv` — the raw per-trial records, all conditions
- [ ] `fig_hw_latency.pdf` and `.png`
- [ ] Board revisions, `arduino-cli` version, `esp32:esp32` core version
- [ ] Room temperature and whether anything else was on the Wi-Fi channel
- [ ] Start and end timestamps per condition
- [ ] Anything that went wrong, including runs you discarded and why

The last item matters most. Four harness defects were found during the simulation work, two of
which flattered the intended conclusion. Write down what went wrong while you still remember.

---

## Reading the result

| Outcome | What it means | What to do |
|---|---|---|
| B and C indistinguishable from A, **and** p95 and max unchanged | supports H2 for these load classes | report it; D remains open |
| Median holds but p95 or max grows | **not** support. The alarm's obligation is a bound, not an average | report the tail; it is the more interesting finding |
| B or C differs from A | contradicts H2 under load the design was expected to tolerate | report it; this is the more important result |
| Second A differs from first A | the environment drifted | discard and re-run |

**Either direction is publishable.** If pinning with bounded queues holds, that is a useful
positive result for a very large installed base. If it does not, that is more important still,
because the advice is standard.

---

## If you run these, what changes in the paper

Do **not** change any of this unless the data exists.

| Item | Change |
|---|---|
| Figure 6 panel B | becomes a results panel; the dotted frame, the "Not yet measured" heading and the red line all come out |
| Evidence taxonomy | gains a sixth category: physical measurement |
| H2 | stops being "Requires hardware; not tested here" |
| Abstract and conclusion | the sentence "no latency figure is reported" must change — **and it must not be removed without the measurement behind it** |
| Title | `VERSION_STRATEGY.md`'s Version A title becomes available, but only with A–D complete; A–C alone do not license a timing-isolation claim |
| `HARDWARE_VALIDATION_PLAN.md` §11 | the list of things that must not change — revisit it line by line |

With A–C done and D outstanding, the honest framing is: *the mitigation holds under
legitimate and command-layer load; behaviour under radio-layer load remains unmeasured.* That
is a stronger paper than the current one and still not a timing-isolation claim.
