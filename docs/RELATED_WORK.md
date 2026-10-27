# Related work and research positioning

A survey of the literature this project sits in, and a precise statement of what is and is not
already answered. Every entry below was checked against the publisher or preprint record; where
a field could not be confirmed it is marked rather than guessed.

The question the project asks:

> On a single-chip Wi-Fi SoC, where the attacked radio driver shares the die, the RTOS scheduler
> and the interrupt controller with the safety task, does pinning the safety task to its own core
> actually isolate it?

The survey is organised by the five bodies of work that question touches. The last column of each
table says, in one line, why that work does not already answer it.

---

## 1. Real-time operation and timing isolation under attack or interference

This is the closest body of work. The consistent finding is that separation helps; the consistent
platform is large (Linux-class, hypervisor-capable, or multi-core application processors with an
MMU).

| Ref | Work | Platform | Finding | Why the question stays open |
| --- | --- | --- | --- | --- |
| [F20] | Fischer et al., *Analysis of Industrial Device Architectures for Real-Time Operations under Denial of Service Attacks*, arXiv:2007.08885, 2020 | Linux-class industrial boards | Pinning the control task to a dedicated core holds 1 ms cycle jitter nearly constant under wired SYN/ARP floods; only a separate co-processor is acceptable for hard real-time | The attacked interface is a *separate* NIC, and the flood is *wired*. The core that is being protected does not share silicon with the attacked radio |
| [BD26] | Burns and Davis, *Mixed Criticality Systems: A Review*, 14th and final edition, University of York, February 2026 | Survey | The canonical survey of mixed-criticality scheduling, multiprocessor analysis and industrial practice since Vestal (2007) | Treats criticality as a *scheduling* problem under benign timing assumptions; adversarial interference originating inside the device's own driver stack is not the model |
| [M25] | Meszlényi et al., *Towards Timing Isolation for Mixed-Criticality Communication in Software-Defined Vehicles*, arXiv:2508.13652, 2025 | 2x Dell Precision 3680, Intel i9-14900, Ubuntu 24.04 PREEMPT-RT, Intel I226 NICs | Priority-based middleware scheduling plus AF_XDP kernel bypass plus dedicated NIC queues keeps real-time DDS latency and jitter predictable under heavy best-effort interference | x86 with a PREEMPT-RT kernel and hardware NIC queues. None of these mechanisms exist on a 240 MHz MCU with no MMU |
| [H24] | Hoornaert et al., *Mcti: mixed-criticality task-based isolation*, *Real-Time Systems* 60(2):328-365, 2024, doi:10.1007/s11241-024-09425-5 | Xilinx UltraScale+ ZCU102, 4x Cortex-A53, Jailhouse hypervisor, FPGA memory scheduler | Co-designed CPU-time and memory-bandwidth isolation; on overload the interconnect switches from fair to fixed-priority arbitration so the critical task keeps running | Requires a hypervisor, performance-counter regulation and an FPGA-hosted memory scheduler. The target class here has none of the three |

**Position.** The mechanism this literature recommends (spatial separation plus a resource
regulator) is unavailable on the hardware consumers actually deploy. What remains available on an
ESP32 is core pinning and queue discipline alone. Whether that residual mechanism is sufficient is
an empirical question about a specific silicon and radio driver, and it has not been measured.

---

## 2. Wi-Fi radio-layer attacks, and the ESP32 as both target and weapon

| Ref | Work | Contribution | Relation to this work |
| --- | --- | --- | --- |
| [C26] | Carbajal and Jodeiri Akbarfam, *A Software-Defined Testbed for Quantifying Deauthentication Resilience in Modern Wi-Fi Networks*, arXiv:2602.23513, 2026 | Measures five Wi-Fi configurations from open to WPA3 against deauthentication; PMF blocks the attack under WPA2 and WPA3 in the conditions tested | Measures whether the **link** drops. Says nothing about whether the device's **application** still meets its deadline while the link is being attacked. This is the exact boundary this project crosses |
| [K26] | Kremser and Graffi, *Evaluating the ESP32-S3 for Wi-Fi Penetration Testing Through the Development of Deauther32 and HackHeld32*, *Sensors* 26(11):3287, 2026, doi:10.3390/s26113287 | ESP32-S3 firmware that transmits spoofed deauthentication frames (the ESP-IDF transmit path rejects them, so the compiled image is patched); notes reduced effectiveness against PMF networks | Establishes that the attack is cheap, portable and available against exactly this device class. It is the threat, not the defence |
| [CCF23] | Cayre, Cauquil and Francillon, *ESPwn32: Hacking with ESP32 System-on-Chips*, 17th IEEE Workshop on Offensive Technologies (WOOT'23), 2023 | Reverse-engineers ESP32/S3/C3 BLE ROM components; hooks internal functions, injects and alters link-layer packets, reconfigures the radio for ANT+ and proprietary 2.4 GHz protocols, jams BLE advertising via calibration manipulation | Shows the radio subsystem of this SoC family is reachable and manipulable from software. Supports the threat model's assumption that radio-layer stress is a realistic in-scope condition |

**Position.** The attack side is well established and specifically demonstrated on this chip
family. The defence side has been evaluated at the *network* layer (does the link survive) and not
at the *application safety* layer (does the siren still sound on time).

---

## 3. Security and performance of the ESP32 application stack

| Ref | Work | Contribution | Relation to this work |
| --- | --- | --- | --- |
| [A26] | Azhar, Azwar and Asroni, *Performance and Security Analysis of MQTT over TLS on ESP32-Based IoT Systems*, *J. Applied Informatics and Computing*, 2026 | Quantifies the latency and resource cost of MQTT-over-TLS on an ESP32-C3 | Measures transport cost under benign conditions. Does not address what happens to a safety function when the transport is attacked |
| [I26] | Ieropoulos et al., *Empowering IoT Security: On-Device Intrusion Detection in Resource Constrained Devices*, arXiv:2605.13159, 2026 | Runs ML-based intrusion detection on the ESP32 itself | Optimises detection accuracy on-device. Detection is a different objective from continuity of the safety function, and an on-device detector is itself load on the contended chip |

**Position.** Work on this platform optimises transport security or detection quality. Neither
treats the safety function's deadline as the dependent variable.

---

## 4. Formal verification for embedded and IoT systems

| Ref | Work | Contribution | Relation to this work |
| --- | --- | --- | --- |
| [Kr23] | Krichen, *A Survey on Formal Verification and Validation Techniques for Internet of Things*, *Applied Sciences* 13(14):8122, 2023, doi:10.3390/app13148122 | Surveys formal verification and validation for IoT: abstract interpretation, model checking, deductive verification; tooling includes Prolog, Maude, Event-B/Rodin/ProB, Simulink | TLA+ does not appear in the survey. Applying TLC to a deployed consumer alarm's safety FSM and to its task-isolation argument is not a covered practice |
| [L02] | Lamport, *Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers*, Addison-Wesley, 2002 | The specification language and the TLC model checker used here | Method reference |

**Position.** Formal methods for IoT are surveyed and practised, but the specific use here, a TLA+
model of the *isolation argument itself* (network task given no fairness, maximally adversarial,
proving the safety step stays enabled), is not a pattern the survey literature records for this
device class. Both specifications here are additionally mutation-tested, so the properties are
demonstrably non-vacuous.

---

## 5. Fuzzing embedded firmware

| Ref | Work | Contribution | Relation to this work |
| --- | --- | --- | --- |
| [Y22] | Yun et al., *Fuzzing of Embedded Systems: A Survey*, *ACM Computing Surveys*, 2022, doi:10.1145/3538644 | The reference survey of embedded fuzzing approaches and their rehosting problems | Positions the method used here; the full author list could not be confirmed from an accessible record and is cited as "et al." |
| [B25] | Bley, Scharnowski, Wörner, Schloegel and Holz, *Protocol-Aware Firmware Rehosting for Effective Fuzzing of Embedded Network Stacks*, ACM, 2025, doi:10.1145/3719027.3765125 (arXiv:2509.13740) | Pemu infers which protocols a firmware speaks and wraps fuzz inputs in valid packets so the fuzzer reaches deeper network-stack layers | State of the art in reaching embedded network code. Complementary: this project fuzzes the *application-layer command parser* in a host harness, which is a narrower target with a stronger oracle (no state change, no counter advance) |
| [T26] | Tharindu, Jayasena and Mishra, *SysFuSS: System-Level Firmware Fuzzing with Selective Symbolic Execution*, arXiv:2602.02243, February 2026 | Full-system emulated firmware fuzzing that switches to targeted symbolic execution when coverage stalls | The current frontier for whole-firmware coverage. Cited as the natural extension path beyond this project's parser-level harness |

**Position.** The fuzzing done here is deliberately narrow and is not claimed as a contribution to
fuzzing technique. It is evidence for one security property (the authenticated command path
rejects everything that is not a correctly signed, fresh command) with a precise oracle.

---

## What the literature leaves open

Combining the five positions above:

1. Timing isolation under attack is studied on platforms that can separate the attacked interface
   from the protected core ([F20], [M25], [H24]). The single-chip Wi-Fi SoC cannot.
2. Deauthentication resilience is quantified at the link layer ([C26]) on devices for which the
   attack is cheap and demonstrated ([K26], [CCF23]). Application-level deadline survival is not
   measured.
3. ESP32 security work targets transport cost and detection accuracy ([A26], [I26]), not safety
   continuity.
4. Formal verification for IoT does not record TLA+ isolation arguments for this device class
   ([Kr23]).

The open question is therefore narrow, concrete and testable: **does core pinning on an ESP32-class
SoC preserve the sensor-to-siren deadline while the chip's own radio driver is under stress?**

This project supplies the full apparatus to answer it, and answers the part that can be answered
without silicon:

- **Answered (logical isolation).** Two TLC-checked TLA+ models, including one in which the
  network task is given no fairness and may stall unboundedly, flood, fail to publish or crash,
  prove the safety step remains enabled and that the network side can never write the alarm state.
  6,000 seeded adversarial trials and 3,000,000 sanitizer-backed fuzz iterations find no invariant
  violation and no accepted forged or replayed command.
- **Open (physical timing isolation).** Sensor-to-siren latency distribution under on-chip radio
  stress. This is a property of the silicon and the radio driver, not of the logic, so it cannot be
  simulated. The apparatus, instrumentation and protocol are in `experiments/hardware/`.

The paper states this split explicitly and claims no number it has not measured.

---

## Candidate venues

| Venue | Fit | Note |
| --- | --- | --- |
| ACM/IEEE workshops on IoT and embedded security (e.g. WOOT, CPSIoTSec-class) | Strong | [CCF23] appeared at WOOT; the measurement framing suits an offensive/defensive-measurement workshop |
| *Sensors* / *Applied Sciences* (MDPI) | Strong | [K26], [Kr23] appeared here; the device class and measurement style match |
| ISEA ICSP (IIT Madras) and comparable Indian security conferences | Good | Appropriate for a first submission with a reproducible artifact |
| RTAS / *Real-Time Systems* | Only with hardware results | This audience will expect the measured latency distributions ([H24] appeared in *Real-Time Systems*) |

---

## Verification note

Each reference above was resolved against a publisher page or preprint record. Two candidate
sources identified during the search could not be retrieved for verification and are therefore
**not cited anywhere in this project**, rather than cited on the strength of a search snippet:

- a systematic review of smart-home IoT security in *Big Data and Cognitive Computing* (publisher
  page not retrievable in this environment);
- a blockchain-assisted lightweight smart-home authentication scheme in a ScienceDirect journal
  (publisher blocks automated retrieval).

If either is wanted in the final submission, retrieve the record manually and add it with the
confirmed fields.
