# Related work comparison

One table per research dimension, then the gap statement that follows from them. Every row cites a
work whose record was verified against a publisher or repository page actually retrieved; full
records and verification caveats are in `docs/LITERATURE_REVIEW_2026.md`.

---

## 1. Configuration-level security assumptions

| Study | Platform / system | Problem addressed | Method | Evidence | Limitation | Difference from this work |
|---|---|---|---|---|---|---|
| Paixão et al., *Proc. ACM Softw. Eng.* 3, FSE, Art. FSE119, 2026 | Linux kernel, FFmpeg, PHP | Which compile-time configurations contain a known vulnerability | Static: patch hunks → ASTs → preprocessor presence conditions → Boolean impact condition, simplified with SMT | 1,581 patches; 88.7 / 96.9 / 68% analysis success; 500 conditions manually reviewed, 0 incorrect, 5.4% over-approximate | Needs an existing patch or CVE as input; no embedded firmware; does not judge whether a guard's reasoning is sound | This work asks whether the security *inference* in the guard is valid, for a defect with no CVE and no patch, and measures its safety cost |
| Ghazi Asgar and Reddy, SDIoTSec 2025 (NDSS), doi:10.14722/sdiotsec.2025.23010 | Deployed MQTT brokers, internet-wide | Brokers accepting anonymous connections | Shodan exposure counts + GitHub popularity ranking (≥ 900 stars) + ESP32 detector prototype | ~500,000 open-1883 devices returning code 0; 10 repositories; tracking exposure 6.85% vs home automation 2.91% | **ACLs and rate limits explicitly deferred**; no static analysis of firmware or build config; detector validated on one broker | This work studies the ACL behaviour they defer, at source level in one artefact, with an actuation outcome |
| Radwan and Sheldon, *Appl. Sci.* 16(7):3583, 2026, doi:10.3390/app16073583 | Mosquitto on Ubuntu, two PCs, LAN | Authentication enforcement correctness and ACL misconfiguration impact | Six scenarios × 10–100 runs; Paho C++ and Mosquitto CLI clients | 95/100 password success; certificate 88% then 0/100; FAR ≈ 0; ACL-restricted 97/100 vs default policy 78/100 | **No HMAC or any application-layer MAC**; no compromise model; two fixed roles; no firmware; **no safety or actuation outcome** | This work's E/E′ pair needs a MAC *and* a compromise indexed by which identity holds which secret — unavailable to that design |
| **This work** | ESP32-WROOM-32 alarm firmware + Mosquitto 2.0.18 over TLS 1.2 | Is the security inference encoded in a build guard sound, and what does it cost the safety function | 12-arm ablation indexed by held secret, 3,600 trials; 8 live-broker scenarios; build-time rejection | 50/300 vs 300/300 alarm activation; 246/300 disarms; Fisher *p* = 9.83 × 10⁻¹¹⁹; 8/8 broker verdicts reproduced | One artefact, one broker, one protocol version; loopback; simulation for trial counts | — |

---

## 2. Specification-level assumptions

| Study | Platform / system | Problem addressed | Method | Evidence | Limitation | Difference from this work |
|---|---|---|---|---|---|---|
| Kupferman and Vardi, *STTT* 4(2):224–233, 2003, doi:10.1007/s100090100062 | General CTL\* specifications | Vacuous satisfaction: a specification holds but a subformula never affects the result | Detection method plus generation of interesting witnesses; strengthens Beer et al. | Theory: definitions, witness generation, complexity analysis | Not tied to any deployed artefact or configuration mechanism | **This work contributes no technique and claims none.** It reports a field instance whose cause was an imported build-time assumption |
| Beer et al.; Kupferman (sanity checks); vacuity by mutation of checkers | Hardware and protocol specifications | Vacuity detection and property qualification | ACTL-fragment detection; mutation of checkers | Established prior art | — | Establishes that the *technique space* is occupied; this work's regression mechanism is an engineering instance of it, not a new method |
| Canedo, arXiv:2608.17214 **(preprint, Aug 2026)** | Deployed air-traffic-control simulator, TypeScript | Oracles whose expected value moves with the fault | Property-based temporal testing evaluated by mutation testing (Stryker); specification- vs state-anchored oracles | 4 modules, 366 mutants, 12 suites; re-anchoring recovers 8 mutants; state-anchoring loses 4 | One system, one author; preprint, no peer review; application software, not embedded or formal | Same underlying idea in a different domain and instrument: this work's vacuous invariant is an assumption-anchored oracle in a TLA+ specification of firmware |
| **This work** | TLA+ specification of ESP32 alarm firmware, model-checked in CI | A shipped, continuously-checked invariant that was unfalsifiable, and why | Build switch promoted to model parameter; inverted configuration whose **required** outcome is a violation of the named invariant | 25 and 660 distinct states, exhaustive; third configuration reports the required violation on every run; 19,529-transition conformance check with a negative control | One specification; bounded abstraction (`MaxCtr = 4`); no technique novelty | — |

---

## 3. Execution-level assumptions

| Study | Platform / system | Problem addressed | Method | Evidence | Limitation | Difference from this work |
|---|---|---|---|---|---|---|
| Prior ESP32 interference measurement (existing bibliography) | ESP32, network task already on the other core | Critical-task cycle loss under IP-layer load | Physical measurement | Single-digit-percent cycle loss | **IP-layer** load only; does not identify the responsible mechanism; different load class from the radio-layer question | This work decomposes which terms a design eliminates and states the residual symbolically; it adds **no** measurement |
| Network calculus / Real-Time Calculus (mature field; recent activity in TSN and time-triggered Ethernet) | Networks and time-triggered systems | Deterministic backlog and delay bounds from arrival and service curves | Arrival-curve / service-curve algebra | Extensive theory | Not addressed to single-chip Wi-Fi SoCs or to adversarial command floods | **No contribution to the theory is claimed.** It is applied to verified queue capacities and drain bounds to derive a concrete overload condition and backlog bound |
| **This work** | ESP32-WROOM-32, FreeRTOS, two cores | Which interference terms a design removes by construction, when no hardware is available | $R = C_{\text{own}} + B + I_{\text{isr}} + I_{\text{mem}}$; $B = 0$ from an asymmetric mutex timeout; conditional deadline theorem; deterministic bounded-work analysis | $B = 0$ derived and verified as a logical property over 660 states; $\partial R/\partial\lambda_{\text{cmd}} = 0$ after repair; overload condition $P < 25$ ms from verified constants | **No numerical value for $R$, $\bar{C}$ or $\bar{I}$. Physical timing invariance not established.** (T3) is assumed | — |

---

## 4. Generalisation over corpora

| Study | Platform / system | Problem addressed | Method | Evidence | Limitation | Difference from this work |
|---|---|---|---|---|---|---|
| Shen et al., *Proc. ACM Softw. Eng.* 2, ISSTA, Art. ISSTA048, 2025, doi:10.1145/3728923 | 258 open-source C/C++ embedded projects | How well a commercial-grade static analyser performs on embedded code | CodeQL over star-ranked GitHub + 32 RTOSes; 123 repositories sampled; two analysts, ~1 month | 709 defects; **34% false-positive rate** (538/1,577); 10% false-negative rate in the SAST-usage measurement | Authors state: may not transfer to commercial tools or commercial embedded software; GitHub only; **measurement study, no causal claims** | **Does not study preprocessor guards or security configuration.** This work's rule targets one specific unsound inference and reports a null result for it |
| Ghazi Asgar and Reddy, 2025 (as above) | Deployed devices | Exposure share by application category | Shodan + popularity ranking | Exposure percentages | Makes exposure-share claims only, not prevalence of a code defect | This work makes an existence claim only, from a smaller sample |
| **This work** | 135 open-source C/C++ MQTT projects | Does the specific guard pattern occur elsewhere | Precise rule + loose heuristic; 8 labelled controls including this project's own pre-repair and repaired guard; all 18 flags adjudicated by hand | **Rule 1: 0/135.** Rule 2: 18/135 flagged, 9 confirmed, 9 false positive (**50%**) | 22 fixed queries, ≥ 3 stars, ≤ 80 MB, no forks or archived; 437 rejected on stars alone; convenience sample | — |

**Calibration point worth stating in the manuscript.** This work's loose rule is ~50% wrong
(9/18); Shen et al.'s mature commercial-grade analyser is 34% wrong on comparable code. A roughly
half-wrong heuristic is therefore in the expected range rather than anomalous — which is an
argument for the manual adjudication, not an excuse for the rule.

---

## 5. The gap, stated after the comparison

Five specific absences, each traceable to a row above:

1. **No work assesses whether the security inference encoded in a build-time guard is sound.**
   Paixão et al. map configurations to *known* vulnerabilities and need a patch as input; a guard
   that grants a property on unsound grounds produces no patch until someone questions it.
2. **No MQTT study compares broker authorisation against application-layer message authentication
   as alternatives under compromise indexed by which identity holds which secret.** Radwan and
   Sheldon come closest and have no MAC and no compromise model; Ghazi Asgar and Reddy defer ACLs
   entirely.
3. **No MQTT security study reports a safety or actuation outcome.** Every comparator measures
   authentication or authorisation success; none measures whether the alarm fired.
4. **Vacuity is documented as a technique, not as a field instance with an identified cause.** No
   prior account was found of a continuously-checked specification of a deployed embedded artefact
   that was vacuous *because it had imported the configuration assumption the firmware got wrong*.
5. **Response-time analysis is treated as a certification instrument, not a defect-finding one.**
   No work was found that reports an incomplete decomposition — one that produces no WCET —
   exposing a real defect because the derivation required a bound the code lacked.

### What the gap does **not** license

- No claim of a validated framework. One artefact, no transfer demonstration, no cost model.
- No prevalence claim. The best comparator uses a larger corpus and declines population claims;
  this work's precise rule found nothing.
- No physical timing claim. Nothing in any row above supplies hardware data, and this work adds
  none.
- No "first to" claim anywhere. The searches behind this comparison were targeted, not exhaustive,
  and §6 of the literature review records what could not be retrieved.
