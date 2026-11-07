# Hardware validation plan: conditions A–D

Phase 3 of the finalization task.

**Status: not executed. No physical measurement exists, and none is reported anywhere in the
manuscript.** This document says what would be required, verifies that the analysis path works,
and records exactly what is blocking.

It consolidates material that already exists in `REPRODUCTION.md` §3 and
`experiments/hardware/README.md`; those remain the canonical step-by-step instructions for
someone with the boards in front of them. What this document adds is the feasibility
determination, a sample-size analysis, a verified end-to-end test of the analysis script, a
wiring figure, and the dependency list.

---

## 1. Feasibility in the current environment

Checked directly rather than assumed:

| Requirement | Probe | Result |
|---|---|---|
| Serial devices for two boards | `ls /dev/ttyUSB* /dev/ttyACM*` | **none present** |
| Toolchain to flash firmware | `which arduino-cli` | **not installed, and nothing to flash** |
| Serial library | `python3 -c "import serial"` | **not installed** |
| A wireless interface for conditions B–D | `ls /sys/class/net` | `eth0 ifb0 lo` — **no radio** |
| Two ESP32 boards, jumper wires, PIR, buzzer | physical | **not present** |
| RF-shielded enclosure for condition D | physical | **not present** |

**Verdict: conditions A, B, C and D cannot be executed here.** This is a cloud container with
no USB, no radio and no physical hardware. The missing items are not software that could be
installed; they are boards, wires and a shielded enclosure.

Per the task's instruction, nothing was simulated and presented as a measurement. The plan
below is what an equipped laboratory would follow.

---

## 2. What is being measured, and why it needs a second board

One quantity, per trial:

> **L = t₁ − t₀**, the interval from the confirmed sensor edge to the siren line going active,
> in microseconds.

The hypothesis under test is **H2** as stated in the manuscript:

> F_Λ ≐ F₀ for radio-layer load Λ across the operating range

— that is, the distribution of L under load is the same as the distribution at idle.

L is timed by a **second board with its own clock**, never by the device under test. This is
not fastidiousness. The hypothesis is about whether the device's own timing degrades under
load; a device timing itself would be measuring with the very clock whose behaviour is in
question, and a uniform slowdown would be invisible.

---

## 3. Bill of materials

| Item | Qty | Specification | Why this one | Approx. cost |
|---|---|---|---|---|
| ESP32 DevKit board | 2 | ESP32-WROOM-32, DevKit v1, 30- or 38-pin | **Must be dual-core Xtensa LX6.** ESP32-C3 and ESP32-S2 are single-core and cannot run the pinned configuration the paper is about, so they cannot test it | £5–8 each |
| USB data cable | 2 | micro-USB or USB-C to match the boards | charge-only cables are a common and silent failure | — |
| Jumper wires, female-to-female | 3 | — | two signal lines plus the common ground | £1 |
| PIR sensor | 1 | HC-SR501 | the real sensor, for fidelity | £2 |
| Push button | 1 | momentary, any | substitutes for the PIR in A–C and removes the HC-SR501's warm-up from every trial | £0.20 |
| Passive buzzer | 1 | 3.3 V piezo | the siren line being sensed | £1 |
| Breadboard | 1 | half size | — | £2 |
| Logic analyser | 0 or 1 | **optional**, 8-channel 24 MHz clone | an independent cross-check on the probe's own timing | £8 |
| **Condition D only** | | | | |
| RF-shielded enclosure | 1 | shielded box or anechoic space | **mandatory for D**; see §7 | institutional |

Roughly **£20–30** for conditions A–C. Condition D's requirement is institutional, not
monetary.

One board is the device under test (DUT); the other is the measuring instrument (the probe).

---

## 4. Wiring and instrumentation

The rig is drawn in **`docs/images/hardware_rig.pdf`** (source: `hardware_rig()` in
`docs/figures/make_diagrams.py`), which carries a red banner saying it has not been built. The
DUT's own peripherals wire as in `docs/images/circuit_wiring.pdf`.

| DUT pin | Function | → Probe pin | Probe constant |
|---|---|---|---|
| GPIO 13 | PIR input line | GPIO 34 | `PIN_PIR_SENSE` |
| GPIO 23 | Buzzer output (siren line) | GPIO 35 | `PIN_BUZZ_SENSE` |
| GND | Ground | GND | — **required**, a common reference |

GPIO 34 and 35 are input-only on the ESP32, which suits sensing and removes any risk of the
probe driving a line it is supposed to observe. The probe attaches rising-edge interrupts to
both and timestamps them with its own hardware timer.

**Without the common ground the two boards have no shared reference and the readings are
meaningless.** This is the most common way this rig is got wrong.

---

## 5. Procedure

### 5.1 Flash

```bash
arduino-cli core install esp32:esp32
arduino-cli lib install "Adafruit SSD1306" "Adafruit GFX Library" "PubSubClient"

cp firmware/smart_home/secrets.example.h firmware/smart_home/secrets.h
# Edit secrets.h: set Wi-Fi credentials and REPLACE the demo keys. They are public,
# and the build refuses AUTH_COMMANDS=1 with the published demo key.

# Device under test, hardened configuration
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/smart_home \
  --build-property "compiler.cpp.extra_flags=-DAUTH_COMMANDS=1"
arduino-cli upload --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 firmware/smart_home

# Probe
arduino-cli compile --fqbn esp32:esp32:esp32 experiments/hardware/latency_probe
arduino-cli upload --fqbn esp32:esp32:esp32 -p /dev/ttyUSB1 experiments/hardware/latency_probe
```

### 5.2 Collect

**Do not reflash the DUT between conditions.** The firmware must be byte-identical across all
four, or the comparison is between two systems rather than two load levels.

```bash
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition A --n 200 --out results_hw.csv
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition B --n 200 --out results_hw.csv
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition C --n 200 --out results_hw.csv
# D only inside a shielded enclosure, with permission — see section 7
```

`collect.py` appends, so all conditions accumulate in one file. Allow the system to return to
the armed state between samples.

### 5.3 Analyse

```bash
python3 experiments/hardware/analyse_hw.py --in results_hw.csv --control A
```

This prints n, median, 95th percentile and maximum per condition, applies the
**pre-registered** two-sided Mann–Whitney *U* test with tie correction against condition A,
and writes `fig_hw_latency.pdf`.

The test and its implementation were committed before any data existed. **Do not substitute a
different test after seeing the data.**

---

## 6. Conditions, and what each would show

| Condition | Setup | RF isolation | What it establishes |
|---|---|---|---|
| **A — Idle** | Wi-Fi connected, broker reachable, no other traffic | none | The control distribution F₀, and the probe's own noise floor. Everything else is compared against this. |
| **B — Legitimate load** | Normal MQTT traffic: frequent STATUS, large retained payloads | none | Whether ordinary operation perturbs the safety path. A difference here would be the most damaging result for the design, because it needs no adversary. |
| **C — Command stress** | High-rate publication on the DUT's own command topic from your broker | none | The hardware counterpart of the simulated flood. The simulation says the safety core is untouched; this is where that is actually tested. |
| **D — Radio stress** | 802.11 deauthentication and disassociation frames at the DUT | **required** | The paper's central open question. Behnke et al. measured degradation from IP load; D asks whether the mitigation holds under load on the radio itself. |

### Sample size

Planning for the pre-registered test, α = 0.05, power = 0.80, equal n per group. The effect
size is expressed in standard deviations so it holds whatever the idle spread turns out to be,
then read back as microseconds for three plausible spreads:

| n per condition | A = P(X>Y) | Detectable shift (SD) | sd = 100 µs | sd = 180 µs | sd = 300 µs |
|---|---|---|---|---|---|
| 30 | 0.709 | 0.78 | 78 µs | 140 µs | 233 µs |
| 50 | 0.662 | 0.59 | 59 µs | 106 µs | 177 µs |
| 100 | 0.614 | 0.41 | 41 µs | 74 µs | 123 µs |
| **200** | **0.581** | **0.29** | **29 µs** | **52 µs** | **87 µs** |
| 400 | 0.557 | 0.20 | 20 µs | 37 µs | 61 µs |

**200 samples per condition is the right target.** At 50 the test can only detect a shift of
about 0.59 SD, which would miss a degradation that still matters for a 10-second entry delay.
At 400 the return diminishes and collection time roughly doubles.

### What would support or contradict H2

- **Supports:** B, C and D each indistinguishable from A, with the tail (p95, max) also
  unchanged. A median that holds while the tail grows is *not* support — the alarm's
  obligation is a bound, not an average.
- **Contradicts:** any condition differing from A at the pre-registered test, or a p95 or
  maximum that grows materially while the median holds.
- **Either way it is a result.** If pinning with queue discipline holds under radio load, that
  is a useful positive finding for a very large installed base. If it does not, that is more
  important still, because it would mean the standard advice given to developers of these
  devices is insufficient.

---

## 7. Condition D: isolation, legality and ethics

**Read before attempting D.**

Conditions A, B and C need no RF isolation and no special permission. They can be run on a
desk.

Condition D generates 802.11 deauthentication and disassociation frames. Doing so:

- **must** take place inside an RF-shielded enclosure or an otherwise isolated radio
  environment, so no frame reaches a network or device you do not own;
- **must** have your institution's permission, obtained in advance and in writing;
- **must** use tooling you already have approval to run.

**This repository deliberately publishes no attack tooling.** `experiments/hardware/README.md`
covers only how to instrument and measure; it does not describe how to generate the load, and
that omission is intentional.

In many jurisdictions transmitting deauthentication frames at equipment you do not own is a
criminal offence regardless of intent. If the isolation and the permission cannot both be
obtained, **do not run condition D.** A paper reporting A, B and C with D openly outstanding
is a sound paper; one reporting D obtained improperly is not.

---

## 8. The analysis path has been verified

The analysis script was run end to end to confirm the path works before anyone buys hardware.

> **This was a script self-test on synthetic input. It is not a measurement, and no number
> from it appears in the manuscript or anywhere else.** The input was generated by a seeded
> random draw with a deliberately shifted condition D, purely to confirm that the
> pre-registered test discriminates when it should and does not when it should not.

```
$ python3 -I experiments/hardware/analyse_hw.py --in SELFTEST_synthetic.csv --control A

cond     n    median       p95       max
A      200     4.204     4.503     4.763
B      200     4.183     4.472     4.692
C      200     4.179     4.499     4.729
D      200     5.089     5.405     5.571

Mann-Whitney U vs condition A:
  B: U=18622.0 z=-1.192 p=0.2333 -> indistinguishable
  C: U=18998.5 z=-0.866 p=0.3864 -> indistinguishable
  D: U=7.5     z=-17.292 p=0.0   -> DIFFERENT

wrote fig_hw_latency.pdf / .png
```

The script parses the schema, computes the summary statistics, applies the test with tie
correction, reports the three comparisons correctly against data of known shape, and produces
the figure. **The analysis path is ready; only the data is missing.**

The synthetic file was not committed, so it cannot later be mistaken for a measurement.

---

## 9. Artefacts in the repository

| Path | What it is | State |
|---|---|---|
| `REPRODUCTION.md` §3 | Canonical step-by-step hardware guide: wiring, flashing, conditions, schema, analysis, troubleshooting, falsification criteria | complete |
| `experiments/hardware/README.md` | Measurement-side specification and the scope limitation on attack tooling | complete |
| `experiments/hardware/latency_probe/` | Probe firmware: rising-edge ISRs, hardware timer | complete |
| `experiments/hardware/collect.py` | Serial collection into `results_hw.csv` | complete, **untested against real hardware** |
| `experiments/hardware/analyse_hw.py` | Summary statistics, pre-registered Mann–Whitney *U*, box plot | complete and **verified end to end** (§8) |
| `experiments/hardware/results_hw_TEMPLATE.csv` | Data-collection template documenting the schema | **added by this phase** |
| `docs/images/hardware_rig.pdf` | Wiring and instrumentation diagram | **added by this phase** |
| `docs/HARDWARE_VALIDATION_PLAN.md` | This document | **added by this phase** |

---

## 10. Remaining dependencies

Ordered by what blocks what.

| # | Dependency | Type | Blocks | Who can resolve it |
|---|---|---|---|---|
| 1 | Two dual-core ESP32 DevKit boards, wires, PIR, buzzer, breadboard | physical, ~£25 | A, B, C, D | the author, or the department |
| 2 | A machine with USB and `arduino-cli` | physical | A, B, C, D | the author |
| 3 | A Wi-Fi network and an MQTT broker the author controls | environment | B, C | the author |
| 4 | `collect.py` exercised against a real probe for the first time | software risk | A, B, C, D | the author, once #1 and #2 exist |
| 5 | RF-shielded enclosure or isolated radio environment | institutional | **D only** | the department |
| 6 | Written institutional permission for 802.11 management-frame transmission | institutional | **D only** | supervisor and department |
| 7 | Approved attack tooling the author already has permission to run | institutional | **D only** | supervisor and department |

**A, B and C are blocked only by dependencies 1–4: roughly £25 and an afternoon.** D is blocked
by institutional items that money does not resolve.

This matters for the submission decision. `docs/VERSION_STRATEGY.md` argues for submitting
Version B now and treating the measurement as follow-up work. If dependencies 1–4 are obtained,
A–C alone would substantially strengthen the paper even with D outstanding, because B and C are
where the simulated results most need a physical counterpart.

---

## 11. What must not change in the manuscript

Until these experiments are run and reported:

- **Figure 6 panel B stays labelled "Not yet measured"**, dotted, with its red line saying no
  result in the paper comes from it.
- **No latency figure is reported.** The abstract and conclusion both say so explicitly.
- **H2 stays marked "Requires hardware; not tested here"** in the hypotheses.
- **The title stays free of any timing-isolation claim.**
- **"Testbed measurement" in the evidence taxonomy continues to mean the Mosquitto broker
  only**, never this rig.

If the experiments are run, Figure 6 panel B becomes a results figure, the evidence taxonomy
gains a sixth category for physical measurement, and `docs/VERSION_STRATEGY.md`'s Version A
title becomes available again — but only then.
