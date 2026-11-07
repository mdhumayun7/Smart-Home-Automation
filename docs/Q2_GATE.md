# Q2 reviewer gate, figure justification and journal compliance


> **Superseded.** This assessment was written against the 3,300-trial, eleven-arm campaign
> and before the real-broker validation. The campaign is now 3,600 trials over twelve
> configurations (9,600 adversarial trials in total), and the ACL arms were reproduced
> against a live Mosquitto 2.0.18 instance, so the model-validity caveat recorded in row 7
> is discharged. See [CONTRIBUTIONS.md](CONTRIBUTIONS.md) and
> [JOURNAL_ASSESSMENT.md](JOURNAL_ASSESSMENT.md) for the current position.

Parts E, F and G of the publication directives. Assessed 6 November 2026 at commit `a3ac427`.

**Headline verdict: the manuscript is NOT ready for submission.** One central claim remains
unverified for want of hardware. Sections 1 and 3 say exactly which, and what would unblock it.

---

## 1. Q2 reviewer gate

Fifteen questions, each with evidence, a status and a corrective action. A polished manuscript
does not turn a Fail into a Pass.

| # | Question | Status | Evidence | Corrective action |
|---|---|---|---|---|
| 1 | Is the problem important to the target readership? | **Pass** | Consumer alarms ship on this exact chip class; deauthentication tooling for it is published and cheap (Kremser 2026, Cayre 2023). Embedded-security readers care | — |
| 2 | Is the research gap current through 6 Nov 2026? | **Partial** | The original gap was **falsified** by Behnke 2020, found in this search. A narrower gap survives and was checked against the papers themselves: pinning-as-mitigation unevaluated, radio-layer load unused, no adversarial or formal treatment | Keep the narrowed claim. Re-run the search before submission |
| 3 | Is the primary contribution clear, specific and non-trivial? | **Partial** | Verified contributions are the ablation (E3) and the formal isolation model (E4 in the novelty matrix). Both are modest. The *intended* primary contribution needs hardware | Lead with the ablation until H1 is run |
| 4 | Is the contribution distinguishable from the closest prior work? | **Pass** | Novelty matrix in `RELATED_WORK.md`, each distinction verified against the source paper, not assumed | — |
| 5 | Are the assumptions realistic and stated? | **Pass** | Threat model enumerates 12 threats; E5's synthetic arrival model is labelled as an assumption wherever its numbers appear; formal abstraction boundary stated in the paper | — |
| 6 | Is the methodology technically correct and detailed enough? | **Pass** | `ARCHITECTURE.md` traces every element to source; `EXPERIMENTS.md` records seeds, runs, environment and reproduction commands per experiment | — |
| 7 | Are the baselines relevant and fairly configured? | **Pass** | E3 now compares eleven designs over 3,300 trials on identical seeds, including the strongest realistic broker configuration: per-client topic ACLs under three separate credential-compromise layouts (shared credential, controller credential, device credential), plus a key-compromise arm and a layered arm. The ACL is modelled as a competent operator would deploy it, and it *beats* this project's own mechanism in one arm — a per-client ACL contains a device-credential compromise that the MAC alone does not, because the key sits in the same flash image. A baseline that wins somewhere is not a straw man. **Caveat recorded rather than hidden:** the arms are model-based, with broker admission as a per-identity permission; no Mosquitto instance was used, and ACL pattern syntax, wildcards, bridged brokers, client-certificate identities and revocation are not modelled | Validate against a running Mosquitto instance with real per-client ACLs. Needs a container, no hardware. Tracked as model validity (Q6 and Threats to Validity), not baseline fairness |
| 8 | Are experiments sufficient to support every central claim? | **FAIL** | Logical isolation: yes (E1, E2). **Timing isolation: no experiment exists** | **Run H1 (conditions A-C)** |
| 9 | Are physical measurements required for any headline claim? | **Blocked** | Yes — the headline claim is physical by nature, and category 1 of the evidence taxonomy is empty | Two ESP32 boards and a logic probe |
| 10 | Are results statistically and scientifically interpreted correctly? | **Pass** | The vacuous Mann-Whitney result was removed from the results and re-stated as a pre-registered analysis for hardware. Zero variance is explained, not hidden | — |
| 11 | Are negative results, failure modes and limitations discussed? | **Pass** | E5 found a defect in a shipped parameter and the firmware changed; two harness bugs in E3 are documented; `PEER_REVIEW.md` is adversarial throughout | — |
| 12 | Can an independent researcher reproduce the work? | **Pass** | Seeded throughout; E2/E4 verified to regenerate byte-identically; CI re-runs formal and adversarial checks on every push | — |
| 13 | Are diagrams necessary, accurate, readable and compliant? | **Pass** | Section 2 justifies each figure; two stale diagrams were found and corrected; greyscale-safe conventions documented | — |
| 14 | Are citations accurate and current? | **Pass** | 22 references verified against publisher, preprint, institutional-repository or OpenAlex records. The three previously unverified fields are now resolved: the Yun author list is Yun, Rustamov, Kim and Shin (*ACM Computing Surveys* 55(7), OpenAlex record for doi:10.1145/3538644); the Bley venue is ACM CCS 2025 (CISPA's own repository names the published version's DOI 10.1145/3719027.3765125, and the OpenAlex record for it gives the venue); the MQTT-L author list is Yu, Qi, Luo, Tian and Lu, read from Springer's own `citation_author` metadata rather than the truncated display list. The ACM Digital Library itself is behind bot verification, which was not circumvented; each field was resolved from an independent authoritative source instead. No TODO markers remain in the manuscript | Re-check before submission, since venues and page numbers can change between acceptance and issue assignment |
| 15 | Does the paper comply with the target journal's scope and rules? | **Partial** | IEEE ESL scope fits; formatting does not yet (Section 3) | Reformat to IEEEtran; cut to the page limit |

**Score: 10 Pass, 3 Partial, 1 Fail, 1 Blocked.** The Fail and the Blocked are the same issue.

**Q7 has now moved to Pass, on the second attempt.** The first attempt added the transport arm
and the score did *not* move, because running the experiment the corrective action asked for is
not the same as satisfying the concern: a boolean broker is still configured more weakly than a
careful operator would configure one. What changed it was modelling per-client ACLs properly
and letting them win where they deserve to win. The ordering matters: the earlier refusal to
upgrade was correct then, and the upgrade is correct now, for a reason that can be pointed at
in the data rather than in the effort spent.

**For the record, the original reasoning when the transport arm alone was added:**
The experiment that Q7's corrective action asked for was performed, and it did what it was meant
to do: it removed the objection that the comparison rested on a straw-man baseline, and it
turned up a real defect in our own firmware. Neither of those makes the baseline *fairly
configured* in the sense Q7 asks about, because the broker is still modelled more weakly than a
careful operator would run one. Running the experiment is not the same as satisfying the
concern, and recording a Pass here because work was done would be the precise failure this gate
exists to prevent.

**Q8 and Q9 are untouched by any of this**, and no further simulation will touch them. It is
worth being equally blunt about what the new results are not. The literature search
recorded in `SECURITY_ANALYSIS.md` §7 establishes that the security principle is textbook, the
rogue-authenticated-client attack is published, and application-layer authentication for MQTT
has been implemented on this same SoC under this same threat model. The credential-compromise
finding therefore does **not** lift Q3, which asks whether the primary contribution is
non-trivial: it adds a well-executed negative control and a configuration-logic defect, not a
new mechanism. Q3 stays Partial, and Q8/Q9 are untouched, because no amount of simulation
substitutes for the physical timing measurement that the headline claim requires.

---

## 2. Figure justification

Part E requires each figure to earn its place. Figures are retained only if they answer all of:
does it support a specific claim, is a figure better than prose or a table here, and is it
non-duplicative?

| Fig | Claim it supports | Why a figure | First cited | Verdict |
|---|---|---|---|---|
| 1 Architecture | The safety and network domains are separated by specific mechanisms | Spatial relationships and three concurrent paths; prose would need a paragraph per edge | §Design | **Keep** |
| 2 State machine | The alarm's behaviour is a small, enumerable FSM amenable to model checking | Standard UML notation; the transition table alone does not show reachability structure | §Design | **Keep** |
| 3 Event sequence | Events are bounded, counted and best-effort | Shows ordering and the overflow/retry path over time | §Design | **Keep in repo**, cut from a 4-page paper |
| 4 Circuit wiring | Reproducibility of the physical build | Needed by anyone rebuilding the device | §Implementation | **Repo only.** Not a journal figure |
| 5 Command flow | Verification happens on core 0, so a flood costs the safety core nothing — the core mechanism of the paper | This is the paper's central mechanism, and the core split is inherently spatial | §Design | **Keep** |
| 6 Command sequence | The counter is committed before acting; there is no ack protocol | Temporal ordering with a trust boundary; a table cannot show "before" | §Design | **Keep in repo**, cut if space is tight |
| 7 Deployment | What is required vs optional vs unbuilt | Distinguishes three states of completeness at a glance | §Implementation | **Repo only** |
| 8 Methodology | Three evidence routes are complete, one is not | Makes the open step unmissable, which is an honesty requirement | §Introduction | **Keep** |
| 9 Experimental setup | What the simulation can and cannot show | Separates the harness from the unbuilt rig | §Evaluation | **Keep** |
| 10 Campaign results | Hardened is flat across five orders of magnitude of attack rate | A plot shows the flatness; a table does not | §Evaluation | **Keep** |

**Not created, deliberately:** latency distributions, CDFs, ablation bar charts and sensitivity
surfaces. The first two need hardware. The ablation and sensitivity results are small enough to
read as tables, and a chart of four rows would be decoration. **No figure shows data that does
not exist.**

For a 4-page IEEE ESL submission the figure budget is roughly three: Figures 5, 8 and 10, with
the rest referenced in the repository.

---

## 3. IEEE Embedded Systems Letters compliance checklist

Target chosen on scope fit, not quartile (`JOURNAL_TARGETS.md` §3.1). Verified against the
official author instructions on the IEEE CEDA site, 6 November 2026.

| Requirement | Status | Action |
|---|---|---|
| Scope: early-stage embedded systems research | **Met** | The one venue whose stated remit matches work with a specified-but-unrun experiment |
| Article type: research paper | **Met** | — |
| **Length: 4 pages including everything**; US$125/page over; 8-page hard limit | **NOT met — currently 5 pages** | Declarations move to the submission system (≈0.5 page); cut Figures 3, 6, 7 references and tighten §Design |
| Format: IEEEtran two-column | **Not done** | `\documentclass[journal]{IEEEtran}` |
| Open access optional, US$2,800; traditional free | **Met** | Choose traditional; no APC |
| Student discount on OA | **Not applicable** | Students are excluded from the OA discount; irrelevant on the free route |
| Submission via IEEE Author Portal | **Not done** | Account needed |
| Figures legible at single-column width | **Met** | Vector PDF, minimum 8 pt effective type |
| Ethics / AI-use disclosure | **Met** | In the manuscript; confirm IEEE's exact current wording |
| Data and code availability | **Met** | Public MIT repository, CI-verified |
| Quartile verified | **Not verified** | SCImago and Scopus Sources unreachable here; check Scopus Sources directly |

---

## 4. What is blocked, and exactly what unblocks it

| Blocked item | Needs | Who |
|---|---|---|
| Gate Q8/Q9, experiment H1 | 2× ESP32 DevKit, logic probe, USB cables | You. No permission or RF isolation needed |
| Experiment H2 (condition D) | Authorised isolated or shielded RF environment, institutional permission | You and Dr. Zaveri |
| Gate Q15, quartile claim | Scopus Sources lookup | You, ten minutes |
| Gate Q14, two citation fields | IEEE Xplore / ACM DL access | You, via institution |
| Gate Q7 validation against a real broker | A Mosquitto container; no hardware | Anyone, about a day |
| Scopus quartile and JSA Guide for Authors | Institutional access to Scopus or JCR | Dr. Zaveri, or the library |
| Venue decision and MDPI acceptability | Supervisor judgement | Dr. Zaveri |

---

## 5. Honest statement of readiness

The repository is a complete, reproducible research artifact. The formal verification, the
adversarial campaign, the ablation, the fuzzing and the sensitivity sweep are all real, all
seeded, all re-runnable, and all reported with their limitations.

**The manuscript is not submission-ready**, for one reason: it asks whether core pinning holds a
safety deadline under radio-layer load, and that question has not been answered by any
experiment in this repository. Simulation establishes logical isolation only, and the
literature search found prior measurement suggesting the physical answer may well be "not
entirely".

Running conditions A-C would change this assessment more than any further writing.
