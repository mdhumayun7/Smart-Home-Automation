# Independent reproduction guide

Everything needed to reproduce this project's results, including the one experiment the authors
could not perform. Written for a researcher with no prior contact with this project.

If you reproduce the hardware experiment, please open an issue or contact the author; the
measurement is the project's single open question and independent data is genuinely wanted.

---

## Three levels of evidence

This project distinguishes three levels and does not conflate them. Level 3 **has not been
reached**, by anyone, at the time of writing.

| Level | What it is | Status |
|---|---|---|
| **1** | Formal verification, model checking, simulation, fuzzing, ablation, sensitivity analysis | **Complete and reproducible.** Section 2 reproduces it in about an hour, with no hardware |
| **2** | A complete hardware validation framework: firmware, wiring, instrumentation, protocol, collection and analysis scripts | **Complete.** Section 3 is that framework |
| **3** | Actual physical measurements on real boards, with independently collected raw data | **NOT PERFORMED.** No physical measurement exists in this repository, and no latency figure is claimed anywhere |

The authors do not have access to the required hardware. Level 2 is provided so that someone who
does can close the gap, and so that the absence of Level 3 is transparent rather than papered
over.

---

## 1. What you need

### For Level 1 (software only)

A Linux or macOS machine with `g++` supporting C++17, Python 3.9 or later, and a Java runtime
(11 or later) for the model checker. No hardware, no network access beyond the first run, which
downloads the TLA+ tools.

### For Level 2 and 3 (hardware)

| Item | Quantity | Specification | Approximate cost |
|---|---|---|---|
| ESP32 DevKit board | 2 | ESP32-WROOM-32, 30-pin or 38-pin DevKit v1. Dual-core Xtensa LX6. **Must be dual-core**: ESP32-C3 and ESP32-S2 are single-core and cannot run the pinned configuration | £5–8 each |
| USB cables | 2 | Data-capable micro-USB or USB-C, matching your boards | — |
| Jumper wires | 4 | Female-to-female | — |
| PIR sensor | 1 | HC-SR501, or a push button to simulate the trigger | £2 |
| Passive buzzer | 1 | Any 3.3 V passive piezo | £1 |
| Logic analyser | 0 or 1 | **Optional.** The second ESP32 is the measuring instrument. A logic analyser (for example a Saleae clone, 24 MHz, 8 channel) gives an independent cross-check | £8 |

Total is roughly £20–30. One board is the device under test, the other is the measuring
instrument.

**Condition D only** additionally requires an RF-shielded enclosure or an isolated radio
environment, plus institutional permission. Conditions A, B and C need none of this.

---

## 2. Reproducing Level 1

```bash
git clone https://github.com/mdhumayun7/Smart-Home-Automation.git
cd Smart-Home-Automation
```

### 2.1 Host test suite — about 1 minute

```bash
./tests/host/run_tests.sh
```

Expect **120 PASS, 0 FAIL**. This compiles the unmodified firmware against host models of
Arduino, FreeRTOS, Wi-Fi, MQTT, non-volatile storage and the display, then runs 19 scenarios at
3 clock start values across 2 framework versions, plus build-configuration and header checks.
One clock start sits just below the 32-bit millisecond wrap.

### 2.2 Formal verification — about 1 minute

```bash
./formal/run_tlc.sh
```

Downloads tla2tools v1.8.0 on first run, then model-checks both specifications. Expect:

```
PASS AlarmFSM      25 distinct states
PASS Isolation     2686 states generated, 660 distinct, depth 26
```

### 2.3 Adversarial campaign and fuzzing — 45–60 minutes

```bash
cd experiments && ./run.sh
```

Runs 6,000 seeded trials and 3,000,000 fuzzing iterations. Each trial forks a child process,
because the firmware's globals are file-scope and would otherwise leak between trials; this is
why it is fork-bound and slower than the work suggests. For a quick check:

```bash
TRIALS=300 FUZZ_ITERS=200000 ./run.sh    # about 3 minutes
```

Verify reproduction by confirming `git status experiments/results/` reports no modification: the
outputs should regenerate byte-identically from the committed seeds.

### 2.4 Ablation and sensitivity — about 20 minutes

```bash
cd experiments && ./run_ablation.sh
```

Produces `results/ablation_summary.md` and `results/ablation_results.pdf`. Expect the
eleven-design table, the credential-compromise matrix, the availability breakdown by attack
rate, the Fisher exact comparisons and the detector sweep. Takes about 50 minutes at the
default 300 trials per design.

### E6: access control against a real Mosquitto broker

The one testbed measurement in this repository. Everything else is simulation or formal
analysis; this talks to an actual broker.

```bash
sudo apt-get install -y --no-install-recommends mosquitto mosquitto-clients
pip3 install paho-mqtt
./experiments/broker/run.sh
```

Produces `results/broker_acl.jsonl` and `results/broker_acl_summary.md`. It generates a private
CA, a server certificate, a password file with three identities and two ACL variants into
`experiments/broker/run/`, starts Mosquitto on loopback port 18883 with TLS, and runs eight
scenarios. The generated keys are throwaway and deliberately not committed.

Expect: the connection refused with no credentials; the command delivered when the stolen
identity is the controller's or the single shared account; `Denied PUBLISH` in the broker log
and no delivery when the stolen identity is the device's, including when the command carries a
signature that genuinely verifies. Takes under a minute.

---

## 3. Reproducing Level 2 and performing Level 3

This is the open experiment. Read Section 3.6 before condition D.

### 3.1 What is being measured, and why externally

One quantity: the interval from the **confirmed sensor edge** to the **siren line going active**.

It is measured by a second board with its own clock, never by the device under test. This is not
fastidiousness: the hypothesis concerns whether the device's own timing degrades under load, so a
device timing itself would be using the very clock whose behaviour is in question.

### 3.2 Wiring

Device under test (DUT) runs `firmware/smart_home`. Probe runs
`experiments/hardware/latency_probe`.

| DUT pin | Function | Connect to probe pin |
|---|---|---|
| GPIO 13 | PIR input line | GPIO 34 (`PIN_PIR_SENSE`) |
| GPIO 23 | Buzzer output | GPIO 35 (`PIN_BUZZ_SENSE`) |
| GND | Ground | GND — **required**, a common ground reference |

GPIO 34 and 35 are input-only on the ESP32, which suits sensing. The probe attaches rising-edge
interrupts to both and timestamps them with its own hardware timer.

The DUT's own peripherals wire as in `docs/images/circuit_wiring.pdf`. For conditions A–C a push
button on GPIO 13 can substitute for the PIR sensor, which removes the HC-SR501's 60-second
warm-up from every trial.

### 3.3 Flashing

```bash
arduino-cli core install esp32:esp32
arduino-cli lib install "Adafruit SSD1306" "Adafruit GFX Library" "PubSubClient"

cp firmware/smart_home/secrets.example.h firmware/smart_home/secrets.h
# Edit secrets.h: set your Wi-Fi credentials and REPLACE the demo keys.

# Device under test, hardened configuration
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/smart_home \
  --build-property "compiler.cpp.extra_flags=-DAUTH_COMMANDS=1"
arduino-cli upload --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 firmware/smart_home

# Probe board
arduino-cli compile --fqbn esp32:esp32:esp32 experiments/hardware/latency_probe
arduino-cli upload --fqbn esp32:esp32:esp32 -p /dev/ttyUSB1 experiments/hardware/latency_probe
```

The demo keys in `secrets.example.h` are public. Replace them.

### 3.4 Conditions

Run every condition against the same DUT without reflashing between them, so the firmware is
identical throughout.

| Condition | Setup | RF isolation |
|---|---|---|
| **A — Idle** | Wi-Fi connected, broker reachable, no other traffic. Establishes the control distribution and the probe's own noise floor | Not required |
| **B — Legitimate load** | Normal MQTT traffic: frequent STATUS commands, large retained payloads | Not required |
| **C — Command stress** | High-rate publication on the DUT's command topic from your own broker | Not required |
| **D — Radio stress** | 802.11 deauthentication and disassociation frames directed at the DUT | **Required** |

Collect at least 50 samples per condition; 200 is better. Between samples allow the system to
return to the armed state.

```bash
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition A --n 200 --out results_hw.csv
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition B --n 200 --out results_hw.csv
python3 experiments/hardware/collect.py --port /dev/ttyUSB1 --condition C --n 200 --out results_hw.csv
```

`collect.py` appends, so all conditions accumulate in one file.

### 3.5 Data schema and analysis

`results_hw.csv` has one row per trial:

| Column | Type | Meaning |
|---|---|---|
| `condition` | string | A, B, C or D |
| `index` | integer | Index within the condition, as written by `collect.py` |
| `latency_us` | integer | Microseconds from the sensor edge to the siren edge, as timed by the probe |

Then:

```bash
python3 experiments/hardware/analyse_hw.py --in results_hw.csv --control A
```

This prints n, median, 95th percentile and maximum per condition, applies the **pre-registered**
two-sided Mann–Whitney *U* test with tie correction against the control, and writes
`fig_hw_latency.pdf`. The test and its implementation were committed before any data existed;
please do not substitute a different test after seeing the data.

### 3.6 Ethics and legality — read before condition D

Deauthentication frames disrupt any device on the targeted network.

- Run condition D **only** on equipment you own, inside an RF-shielded enclosure or a
  demonstrably isolated environment.
- Obtain institutional permission **first**.
- Directing such traffic at a network you do not own is illegal in most jurisdictions.

**This repository deliberately contains no attack-generation tooling or procedure**, and
condition D intentionally does not specify how to produce the frames. If you are not in a
position to run it lawfully, report conditions A–C and state D as future work. That is a
legitimate and publishable outcome; conditions A–C alone test whether the design's own network
stack perturbs the safety path.

### 3.7 What would support or contradict the hypothesis

Stated in advance so the result cannot be reinterpreted afterwards. Reasoning:
`docs/TIMING_ANALYSIS.md` §4.

**Supports timing invariance:**
- Median latency shift between A and each loaded condition under 10 ms, against a 150 ms sensor
  confirmation window.
- No change in distribution shape; no heavy upper tail.
- No missed detections in any condition.

**Contradicts it:**
- Median shift above 10 ms.
- A heavy upper tail, indicating occasional long interrupt storms even when the median holds.
- Any missed or late detection.
- Any condition in which the siren fails to sound.

A contradicting result is **more** valuable than a confirming one. It would show that the
mitigation routinely recommended to developers of this device class is insufficient, across a
very large installed base. Please report it either way.

### 3.8 Troubleshooting

| Symptom | Likely cause | Remedy |
|---|---|---|
| `collect.py` reports no samples | Probe not seeing edges | Check the common ground. Both boards must share GND |
| Latency reads as 0 or absurdly large | Probe interrupts firing on the wrong edge or a floating pin | Confirm GPIO 34/35 are wired to the DUT's PIR and buzzer lines, not to each other |
| First trigger never fires | HC-SR501 warm-up | Wait 60 s after power-up, or raise `PIR_WARMUP_MS`, or use a push button |
| Every trial reports the same microsecond value | DUT not actually under load, or the probe is self-triggering | Verify load is reaching the DUT; check its serial output |
| `pyserial` import error | Dependency missing | `pip install -r requirements.txt` |
| Compile fails on `WiFi.h` | Wrong board core | `arduino-cli core install esp32:esp32`; select an ESP32 DevKit, not an ESP8266 |
| Probe resets repeatedly | Brown-out from powering both boards off one USB port | Use separate USB ports or a powered hub |
| Latency much larger than ~150 ms | Display stage, or a stale `PIR_CONFIRM_MS` | Expected total is roughly `PIR_CONFIRM_MS` plus two loop periods. See `TIMING_ANALYSIS.md` §2 |

### 3.9 Reporting

Please include your raw `results_hw.csv`, the board revisions and the arduino-esp32 version, how
load was generated for each condition, and the `analyse_hw.py` output. Raw data matters more
than conclusions; it lets others re-analyse without repeating the setup.

---

## 4. Repository map

| Path | Contents |
|---|---|
| `firmware/smart_home/` | Device firmware. `smart_home.ino` plus four dependency-free headers |
| `firmware/espnow_receiver/` | Second-board receiver for out-of-band alerts |
| `formal/` | TLA+ specifications and the TLC runner |
| `experiments/` | Campaign, ablation, sensitivity and fuzzing harnesses, with analysis scripts |
| `experiments/hardware/` | The Level 2 framework: probe firmware, collection, analysis |
| `tests/host/` | 120-check host suite and the platform stubs |
| `docs/` | Architecture, timing analysis, threat model, literature log, experiment records |
| `paper/` | `manuscript.tex` (full length) and `paper.tex` (short) |

---

## 5. Known limitations of the reproduction

Honest statement of what reproducing this will and will not tell you.

- **Level 1 reproduces exactly**; it has been verified to regenerate byte-identical outputs. But
  it establishes *logical* isolation only. The simulation harness advances a logical clock, so
  latency variance is identically zero and no timing conclusion can be drawn from it.
- **The sensitivity analysis uses a synthetic arrival model.** Benign management-frame arrivals
  are modelled as Poisson at a stated rate because no capture of real traffic was available. The
  false-positive rates characterise the detector's logic, not any real network.
- **The ablation's alternative designs are harness models**, not implementations of specific
  products. The broker is modelled as a per-identity permission on the command topic. Those
  semantics are no longer only assumed: `experiments/broker/run.sh` reproduces all eight
  access-control scenarios against a real Mosquitto 2.0.18 instance with TLS, password
  authentication and per-client ACL files, and the broker agreed with the model in every case.
  What remains unmodelled is everything outside those semantics: ACL pattern syntax, wildcards,
  bridged or clustered brokers, client-certificate identities and revocation after a leak. The
  testbed also runs on loopback with a private CA, so it validates policy, not networking.
- **The broker experiment does not reproduce byte-identically**, unlike everything else here.
  It talks to a live broker, so log timestamps and randomly generated client identifiers differ
  on every run. The scenario verdicts, topics and message sizes do not.
- **No runtime TLS cost is measured anywhere.** `WiFiClientSecure` is real in the firmware but a
  no-op shim in the host stubs, so no handshake latency, encryption overhead or throughput
  figure is reported from simulation. The only TLS cost reported is static flash and RAM,
  measured by the real compiler in CI.
- **All results concern one chip** and two framework versions. Nothing here supports claims about
  single-chip Wi-Fi SoCs as a class. The single-core variants are arguably the more interesting
  case, since they cannot pin at all.
- **No energy or CPU-time cost has been measured** for any security feature.
