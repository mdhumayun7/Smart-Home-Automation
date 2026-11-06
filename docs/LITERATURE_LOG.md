# Literature search log

A dated, reproducible record of the literature search behind `RELATED_WORK.md`. It exists so a
reviewer can see what was searched, what was screened out and why, and so the search can be
repeated.

**This is a documented search log, not a systematic review.** No PRISMA protocol was followed,
no second screener was involved, and coverage is not claimed to be exhaustive. Calling it a
systematic review would be inaccurate.

---

## 1. Parameters

| Field | Value |
|---|---|
| Search cutoff | **6 November 2026** |
| Date range searched | 2021 to cutoff, plus foundational work outside that window where needed |
| Date of search | 6 November 2026 |
| Searcher | MD Humayun (single screener) |
| Topic | Real-time and safety-task behaviour on single-chip Wi-Fi SoCs under network and radio-layer load; ESP32 security; formal verification of embedded task isolation |

**Note on 2026.** The year was not complete at the cutoff. Papers dated 2026 found here are
those published or made available online by 6 November 2026, including early-access and
online-first items. No claim is made about work appearing later in 2026.

## 2. Sources

| Source | How reached | Outcome |
|---|---|---|
| arXiv | Direct fetch of abstract and PDF pages | **Usable.** Several references verified here |
| ACM Digital Library | Direct fetch | **Blocked** for automated retrieval. DOIs verified indirectly via author preprints |
| IEEE Xplore | Direct fetch | **Not reachable** in this environment. IEEE items verified via author preprints and institutional repositories |
| ScienceDirect / Elsevier | Direct fetch | **Blocked.** Elsevier items verified via arXiv preprints and repository copies carrying the DOI |
| SpringerLink | Direct fetch | **Usable** for some items |
| MDPI | Direct fetch of article and flyer pages | **Usable** |
| University repositories (Glasgow Enlighten, TU Berlin DepositOnce) | Direct fetch | **Usable.** Primary route for the IEEE and Elsevier items below |
| Publisher pages (IEEE CEDA, MDPI) | Direct fetch | **Usable** for journal metadata |
| SCImago, Scopus Sources | Direct fetch | **Blocked.** See `JOURNAL_TARGETS.md` §1.2 |
| Web search | Discovery only | Used to locate candidates, never as a verification source |

**Verification rule applied:** a reference is cited only if its title, authors, venue and year
were read from a publisher page, an author preprint, or an institutional repository copy. Search
snippets and aggregator sites (researcher.life, letpub, peeref, resurchify, journalsearches,
editage, journalmetrics) were used for **discovery only and never for verification**; several
appeared in results and were discarded.

## 3. Search strings

Run on 6 November 2026.

| # | Query | Intent |
|---|---|---|
| S1 | `ESP32 FreeRTOS core pinning task interference latency measurement WiFi load 2026` | Find anyone measuring core-pinning effectiveness on this chip |
| S2 | `microcontroller real-time task deadline degradation under network denial of service measurement` | **Closest competing work** |
| S3 | `Behnke real-time IoT network interrupts mitigation embedded 2022 2023 2024 follow-up` | Follow the competing research line forward |
| S4 | `802.11 deauthentication flood impact embedded device CPU application task latency measurement` | Radio-layer load specifically |
| S5 | `arxiv 2025 2026 embedded IoT device real-time task isolation wireless interference mitigation evaluation ESP32 RISC-V` | Recent work to the cutoff |
| S6 | `formal verification TLA+ embedded firmware state machine model checking IoT` | Formal-methods positioning |
| S7 | `mixed-criticality multicore interference safety task isolation real-time 2025` | Timing-isolation literature |
| S8 | `embedded firmware fuzzing IoT rehosting survey 2025 2026` | Fuzzing positioning |
| S9 | `smart home security system attack replay authentication constrained device HMAC 2025` | Application-domain security |
| S10 | `Scopus indexed journals embedded systems IoT security Q2 2026 CiteScore quartile` | Venue selection |

S2 and S3 were the decisive queries. They were run specifically to look for work that would
**contradict or pre-empt** the project's claim, not to find supporting citations.

## 4. Screening

**Inclusion:** peer-reviewed or preprint work that (a) measures or models real-time/safety task
behaviour on resource-constrained devices under network or radio load, (b) attacks or defends
the ESP32 family, (c) applies formal verification to embedded task behaviour, or (d) is needed
to position the fuzzing method.

**Exclusion:** vendor blogs, tutorials and forum posts (no peer review, no measurement
protocol); papers where the device is only an application platform with no timing or security
claim; aggregator pages; items whose bibliographic record could not be verified.

| Stage | Count |
|---|---|
| Candidates surfaced across S1-S10 | ~90 |
| Passed title/abstract screen | 24 |
| Full record verified against publisher, preprint or repository | 19 |
| **Cited in the project** | **18** |
| Excluded after verification attempt failed | 2 (recorded in `RELATED_WORK.md` §7) |

Notable exclusions at the title screen: a large volume of ESP32 tutorial and blog material
surfaced by S1 (no measurement protocol), and deauthentication-attack papers predating 2015 that
concern the attack mechanism rather than victim-side impact.

---

## 5. The decisive finding

**S2 and S3 surfaced a research line that materially weakens the project's original gap claim.**
It is recorded here in full because it changed the paper.

### 5.1 Behnke et al. (2020), IEEE IPCCC

> I. Behnke, L. Pirl, L. Thamsen, R. Danicki, A. Polze, O. Kao, "Interrupting Real-Time IoT
> Tasks: How Bad Can It Be to Connect Your Critical Embedded System to the Internet?",
> *2020 IEEE 39th International Performance Computing and Communications Conference (IPCCC)*,
> 6-8 November 2020. Verified via University of Glasgow Enlighten repository, record 268149.

**What they did, and why it matters here.** They measured a periodic critical task's *lateness*
on an **ESP32** (dual-core, 160 MHz, FreeRTOS, closed-source Wi-Fi driver) and a Particle Photon,
under IP packet load of 10, 100 and 1,000 pps plus 120,000 pps bursts, with the UDP server
running **on the other core**.

**Their result contradicts the null hypothesis this project implicitly assumed.** The critical
task lost roughly **2.15-3.8%** of its cycles with packets to a listened port, and **3.17-6.67%**
with packets to an unused port. Once the MCU saturates, lateness grows roughly linearly with
packet rate. They conclude that command-and-control over IP is unsuitable for hard real-time
tasks.

**Consequence for this project.** The claim "no prior work measures real-time degradation on an
ESP32 under on-chip network load" is **false** and has been removed. Any framing in which the
expected outcome is "nothing happens" is also unsupportable: prior measurement says something
does happen, even with the network task on a separate core.

### 5.2 The follow-up line

| Work | Verified details | What it contributes |
|---|---|---|
| Behnke, Wiesner, Danicki, Thamsen (2022) | "A Priority-Aware Multiqueue NIC Design for Real-Time IoT Devices", *ACM SAC '22*, doi:10.1145/3477314.3507165. Verified via arXiv 2201.00594 | A **hardware** mitigation: per-flow NIC queues with interrupt moderation. 93% fewer interrupts, 80% less added runtime for the critical task at 5,000 pkt/s. **The NIC was simulated in SimPy, never built**, and the paper does not establish applicability to ESP32-class silicon |
| Behnke, Blumschein, Danicki, Wiesner, Thamsen, Kao (2023) | "Towards a Real-Time IoT: Approaches for Incoming Packet Processing in Cyber-Physical Systems", *Journal of Systems Architecture*, vol. 140, art. 102891, doi:10.1016/j.sysarc.2023.102891. Verified via Glasgow Enlighten 297447 and arXiv 2305.01985 | A **software** mitigation: early priority-based demultiplexing in the driver, 7.5x faster per-packet handling, prototyped on a **Xilinx Zynq-7000**, measured on a single core |

### 5.3 What survives, and why

Three distinctions were checked against the papers themselves, not assumed.

| # | Distinction | Evidence it holds |
|---|---|---|
| 1 | **Core pinning is never evaluated as a mitigation** | The JSA 2023 paper states the ESP32's second core is used "to separate the observed processes from the test system, not as a mitigation", and does not discuss CPU affinity as a strategy. Their evaluated mitigations are a simulated NIC and a Zynq driver patch — neither deployable on a stock ESP32 today |
| 2 | **All load is IP-layer** | Every experiment in the line uses UDP or MODBUS/TCP packets. 802.11 deauthentication and disassociation frames are management frames handled in the MAC and driver **below** the IP stack, and are processed whether or not a socket is listening. This is a different interference path and is unmeasured |
| 3 | **No adversarial model, and no formal methods** | The 2020 paper states it does not model deliberate attacks; the 2023 paper describes its floods as volumetric stress, "not a security evaluation". Neither uses formal verification |

**The revised, defensible contribution** is therefore *not* "first to measure", but: an
evaluation of **core pinning plus bounded-queue discipline as a software-only, deployable
mitigation**, under **radio-layer adversarial load**, with the isolation argument **formally
verified**. The novelty matrix in `RELATED_WORK.md` §8 records this.

**The hypothesis is now sharper.** Rather than predicting invariance, the project can state a
mechanism-backed prediction with a prior effect size: Behnke measured 2-4% cycle loss at the IP
layer with cross-core separation, so the question becomes whether radio-layer load inflates a
sensor-to-siren deadline beyond its margin, and whether queue discipline bounds it. That is
falsifiable in a way the original framing was not.

---

## 6. Other verified work from this search

Full positioning in `RELATED_WORK.md`.

| Work | Status | Relevance |
|---|---|---|
| Mudraje et al., "Reverse Engineering the ESP32-C3 Wi-Fi Drivers for Static Worst-Case Analysis of Intermittently-Powered Systems", arXiv:2501.17684v3 (2025-04-03), doi:10.1145/3722572.3727926 | Verified | Reverse-engineers the closed-source ESP32-C3 Wi-Fi driver for static **worst-case energy** analysis. Confirms the driver is opaque and analysable only with effort. Does **not** do timing/WCET or task interference |
| Kremser and Graffi, *Sensors* 26(11):3287 (2026) | Verified | ESP32-S3 deauthentication tooling |
| Cayre, Cauquil, Francillon, WOOT'23 (2023) | Verified | ESP32 radio manipulation |
| Carbajal and Jodeiri Akbarfam, arXiv:2602.23513 (2026) | Verified | Link-layer deauth resilience |
| Burns and Davis, *Mixed Criticality Systems: A Review*, 14th edn (Feb 2026) | Verified | Mixed-criticality survey |
| Meszlényi et al., arXiv:2508.13652 (2025) | Verified | x86 PREEMPT-RT timing isolation |
| Hoornaert et al., *Real-Time Systems* 60(2) (2024) | Verified | Cortex-A53 + hypervisor isolation |
| Krichen, *Applied Sciences* 13(14):8122 (2023) | Verified | Formal verification for IoT; no TLA+ |
| Yun et al., *ACM Computing Surveys* (2022) | Verified, author list incomplete | Embedded fuzzing survey |
| Bley et al., ACM (2025), doi:10.1145/3719027.3765125 | Verified | Protocol-aware firmware rehosting |
| Tharindu, Jayasena, Mishra, arXiv:2602.02243 (2026) | Verified | System-level firmware fuzzing |
| Azhar, Azwar, Asroni (2026) | Verified | MQTT-over-TLS cost on ESP32-C3 |
| Ieropoulos et al., arXiv:2605.13159 (2026) | Verified | On-device IDS on ESP32 |
| Fischer et al., arXiv:2007.08885 (2020) | Verified | Linux-class industrial DoS timing |
| Lamport, *Specifying Systems* (2002) | Foundational | TLA+ method reference |

### 6.1 Found but not cited

| Item | Reason |
|---|---|
| "An Energy-Efficient ESP32 IoT System for Real-Time Detection of WiFi Deauthentication Attacks" (INTECOM, 2025) | Record surfaced but not retrieved from the publisher in this environment. Relevant: on-device deauth detection on ESP32 already exists, which is a further reason this project claims **no novelty** for its detector. Retrieve and cite before submission if the detector is discussed as a contribution |
| MDPI *BDCC* smart-home security review; a ScienceDirect lightweight-authentication paper | Publisher pages unreachable; excluded rather than cited from a snippet |
| ESP32 tutorials, vendor blogs, forum threads (bulk of S1 results) | Not peer-reviewed, no measurement protocol |

---

## 7. Effect of this search on the project

| Item | Before | After |
|---|---|---|
| Gap claim | "No prior work measures a safety deadline on a SoC whose own radio driver is the attacked resource" | Narrowed: core pinning as a deployable software-only mitigation is unevaluated; radio-layer load is unmeasured; no formal treatment exists |
| Expected result | Implicit null (invariance) | Mechanism-backed prediction with a prior effect size of 2-4% cycle loss |
| Novelty of deauth detection | Implicitly a feature of interest | **Explicitly not claimed as novel**; prior on-device detectors exist |
| References | 14 | 18 |
| Closest competitor | Fischer et al. (2020), Linux-class | **Behnke et al. (2020), same chip family** |

The engineering, the formal verification and the reproducible artifact are unaffected. What
changed is what may honestly be claimed about them.
