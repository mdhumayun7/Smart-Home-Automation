# Supervisor review notes

**For:** Dr. M. A. Zaveri
**From:** MD Humayun (P25IS016), M.Tech CSE — Information Security and Privacy, SVNIT Surat
**Date:** 7 November 2026
**Paper:** *Unverified Assumptions in Embedded Safety Firmware: Configuration, Specification
and Response-Time Defects in an MQTT Alarm System*
**Repository:** `github.com/mdhumayun7/Smart-Home-Automation`

**This package requests your approval. It does not assume it.** Four decisions are set out in
§11, and the work should not be submitted anywhere until you have ruled on them.

Reading order if time is short: §1–§6 (ten minutes), then §10 and §11.

---

## 1. Research problem

A domestic intrusion alarm has one obligation: make a loud noise within a bounded time of an
intrusion. Almost all such devices now run on single-chip Wi-Fi SoCs — on the ESP32, the Wi-Fi
driver, the TCP/IP stack, the MQTT client and the alarm application share one die, one
scheduler and one interrupt controller. An attacker outside the building who can delay or
suppress the siren with cheap equipment has defeated the device entirely.

Developers mitigate this with two pieces of standard advice:

1. **Pin the safety task to its own core**, and put everything network-facing on the other.
2. **Gate risky features behind build configuration.**

Both are *assertions*. The first asserts a timing property; the second a security property.
Neither is normally checked.

## 2. Research gap

Behnke et al. (IPCCC 2020) measured that network activity reaches a critical task on this
hardware despite cross-core separation — 2.15–3.8 % cycle loss on a listened port, 3.17–6.67 %
on an unused one. That establishes the *phenomenon*.

Three things it leaves open, which motivate this paper:

- it measures the phenomenon but does not evaluate the *mitigation*;
- it uses IP packet load, not load on the radio layer, which is what actually threatens a
  wireless alarm;
- there is no adversarial model and no formal treatment.

Their own proposed fixes need hardware that does not exist, or a platform an order of
magnitude larger — neither available to the installed base.

## 3. Main contributions

Originally eight. I reduced them to **five** after classifying each against the literature
(`docs/CONTRIBUTIONS.md`), because the evidence does not support eight and claiming it would
have been the easiest thing for a reviewer to attack.

**The central claim:**

> A security property asserted in build configuration, and a timing property asserted in
> design, are both unverified claims. Each can be falsified by a method that costs far less
> than the system it checks.

I claim **no new mechanism, attack, protocol or formalism**. The contribution is that applying
cheap falsification to a system's *assumptions*, rather than to its running behaviour, caught
three defects that testing, fuzzing, exhaustive model checking and 9,600 adversarial trials
all missed.

## 4. Experimental methodology

Five kinds of evidence, labelled separately throughout because they are not interchangeable:

| Kind | What | Scale |
|---|---|---|
| Formal | TLA+, exhaustive model checking, network task given no fairness | 25 and 660 distinct states |
| Simulation | unmodified firmware logic on host stubs, seeded | 9,600 adversarial trials, 3,000,000 fuzz iterations, 180 grid cells |
| Testbed measurement | live Mosquitto 2.0.18, TLS, per-client ACLs | 8 scenarios |
| Analytical | response-time decomposition, forgery probability | — |
| Corpus study | static analysis, commit-pinned | 135 projects |

Everything regenerates byte-identically from committed seeds. The broker experiment reproduces
its eight verdicts on a clean machine.

## 5. Key findings

**Three defects, in three kinds of assumption, each found by a different method — all three in
my own work.**

| Defect | Assumption lived in | Found by | Cost |
|---|---|---|---|
| Compile guard accepted TLS + broker login as publisher authority | build configuration | ablation over 12 configurations | alarm fires in 16.7 % of trials vs 100 % for the control |
| Command drain assumed bounded | design | response-time decomposition | no static bound on the safety loop's own execution time |
| `NoUnauthRemoteDisarm` assumed the refusal rather than deriving it | the TLA+ specification | mutating the specification | the invariant was **vacuous in CI** |

Plus, from the ablation: availability, integrity and the safety function fail *independently*.
A rate limiter costs 41 % of operator commands and buys integrity nothing; a static token does
the reverse; only a counter-bound MAC does both.

## 6. Formal verification results

- Two specifications, model-checked exhaustively. The network task is granted **no fairness
  assumption**, so the result holds even if it never runs.
- Trace conformance: **19,529** firmware transitions checked against the specification's
  transition relation, 0 disallowed, with a negative control confirming a forbidden transition
  *is* rejected.
- **The vacuous invariant.** The property stating that unauthenticated remote disarm never
  takes effect was unfalsifiable in the specification I shipped and checked in CI, because it
  assumed the refusal instead of deriving it — the same unsound inference the compile guard
  made. I have disclosed this in a section of its own, in the abstract, and in the title. The
  runner now **requires** TLC to fail on a deliberately defective configuration, so it cannot
  recur silently.

I would value your view on whether disclosing this strengthens the paper, as I believe, or
whether a reviewer will read it as carelessness.

## 7. Security findings

Broker-side authorisation and application-layer authentication fail under **different**
compromises; neither dominates:

| Control | Compromise | Alarm fires | Operator admitted |
|---|---|---|---|
| TLS + per-client ACL | device credential | 300/300 | 1250/1250 |
| HMAC + counter | any broker credential | 300/300 | 1250/1250 |
| TLS + per-client ACL | controller credential | 50/300 | 1250/1250 |
| HMAC + counter | controller credential + key | 50/300 | **0/1250** |
| **TLS + ACL + HMAC** | device credential + key (flash dump) | **300/300** | **1250/1250** |
| **TLS + ACL + HMAC** | controller credential + key | 50/300 | **0/1250** |

Two things I want to flag:

- **An earlier draft claimed the layered configuration "survives every case". That was wrong**,
  and I found it by measuring the arm I had not run. It survives every single-secret
  compromise and a device flash dump; it falls to a compromised controller host, which needs
  *no physical access at all*. The paper now says this in the threat model, the tables, two
  figures and the abstract.
- **An unanticipated negative result:** under key compromise the monotonic replay counter that
  defeats capture-and-replay becomes a lockout against the legitimate owner — 0 of 1,250
  commands admitted. I did not expect this and have not seen it reported for counter-based
  replay protection in embedded command paths.

The underlying principle is textbook and the attack class is published (Alsabbagh et al.,
CSNet 2024), so **I claim no new vulnerability** and the paper says so plainly.

## 8. Response-time findings

The decomposition removes three of four interference terms by construction — the blocking term
is identically zero because the safety loop takes the status mutex with timeout 0 and gives up
rather than wait — and names the single composite hardware quantity that remains.

**It found a defect nothing else did.** The command drain was an unbounded `while` loop,
leaving the safety loop with no static bound on its own execution time. It had survived 120
host checks, 3,000,000 fuzz iterations, 9,600 adversarial trials and exhaustive model
checking. It is now bounded, and the bound is asserted at compile time.

My own review (`docs/FINAL_SCIENTIFIC_REVIEW.md`) argues this is the second-strongest result in
the paper and still the least prominent. **Decision 3 in §11 asks whether to promote it.**

## 9. Research limitations

Stated plainly, because they are the paper's honest edge:

1. **No physical timing measurement.** Everything about isolation is *logical*. The simulation
   advances a logical clock, so it says nothing about timing. Construct validity names this
   "the most serious threat" to the work.
2. **The generalisation attempt returned nothing.** 135 open-source embedded MQTT projects,
   zero hits for the guard pattern. I report it as a zero and explicitly decline to claim
   prevalence. A weaker rule flagged 18, of which 9 were confirmed on reading — reported as an
   **existence claim, not a rate**, with the over- and under-counting both quantified.
3. **The broker testbed ran on loopback**, not in a deployed wireless network.
4. **Fuzzing was on the host build**, not on the device binary, so it says nothing about
   toolchain or radio-driver faults.
5. **One chip, two framework versions, one application, no deployment.** I do not generalise
   to single-chip Wi-Fi SoCs as a class.

## 10. Pending hardware experiments

The paper's own open question needs two ESP32 boards and a probe.

| Condition | What | Blocked by |
|---|---|---|
| A — idle (control) | establishes F₀ and the instrument noise floor | ~£25 of hardware |
| B — legitimate MQTT load | whether ordinary operation perturbs the safety path | ~£25 of hardware |
| C — command-interface stress | the hardware counterpart of the simulated flood | ~£25 of hardware |
| D — radio-layer stress | the central open question | **RF-shielded enclosure + institutional permission** |

**A, B and C need about £25 and an afternoon, and no permission.** D needs departmental
resources, and in many jurisdictions transmitting deauthentication frames outside a shielded
environment is a criminal offence — I will not attempt it without written permission.

Full protocol, bill of materials, wiring diagram, data template and a sample-size analysis are
in `docs/HARDWARE_VALIDATION_PLAN.md`. The analysis script is written, committed and verified
end to end on synthetic input; only the data is missing.

## 11. Decisions I need from you

### Decision 1 — Submit now, or run conditions A–C first?

`docs/VERSION_STRATEGY.md` sets out two honest framings. Version B (the current manuscript)
is submittable today. Version A would need the measurement.

My assessment: A–C cost about £25 and an afternoon, and would convert the objection most
likely to cost an acceptance into a result. **I recommend running them first**, but this is
your call on timing against my other commitments.

### Decision 2 — Journal

Recommendation: **Journal of Systems Architecture** (Elsevier). Its scope is verified to cover
embedded systems and software and real-time systems, and it states that "case studies are
welcome but must contribute more than just a design for a particular piece of software" —
which is the bar this paper has to clear and I believe it does.

**But:** Empirical Software Engineering (Springer) may be the better home, because what this
paper actually argues is methodological, and EMSE explicitly prefers work that can be
replicated. It would need reframing, not just reformatting.

Two things I could not verify and have not claimed: **JSA's quartile** (SCImago was
unreachable; Scopus and JCR need library access — earlier drafts of mine assumed Q2 and I have
removed that assumption), and the **Guide for Authors** (the page would not load). CiteScore
9.1 and Impact Factor 5.3 *are* verified from Elsevier's own pages, and are more Q1-shaped than
Q2, which raises the bar rather than lowering it.

### Decision 3 — Promote the response-time finding?

It is the cleanest demonstration of the paper's central claim: every empirical technique
passed, and an analytical one found the defect. It is currently buried in §7.

### Decision 4 — Dissertation overlap

Does any of this work appear, or will it appear, in my M.Tech dissertation? If so it must be
declared on submission. I need your ruling before I complete the declarations.

---

## 12. What is in this package

| Item | Path |
|---|---|
| Final manuscript PDF (31 pages) | `FINAL_SUBMISSION_PACKAGE/manuscript/FINAL_MANUSCRIPT.pdf` |
| LaTeX source (bibliography is embedded, no separate `.bib`) | `FINAL_SUBMISSION_PACKAGE/manuscript/manuscript.tex` |
| All figures, PDF + SVG + 600 DPI PNG | `FINAL_SUBMISSION_PACKAGE/figures/COMPLETE_FIGURE_COLLECTION.zip` |
| All figures in one PDF, at printed size | `FINAL_SUBMISSION_PACKAGE/figures/ALL_FIGURES_PREVIEW.pdf` |
| Supplementary material index | `FINAL_SUBMISSION_PACKAGE/supplementary_material/README.md` |
| Ten reports | `FINAL_SUBMISSION_PACKAGE/reports/` |
| Submission checklist with per-item status | `FINAL_SUBMISSION_PACKAGE/SUBMISSION_CHECKLIST.md` |
| How to reproduce everything | `REPRODUCTION.md` |

**Outstanding and not resolvable by me:** the hardware measurement, the institutional
similarity report, JSA's Guide for Authors and quartile, and your approval.

I have not claimed the paper is submission-ready. It is **technically** complete; the
administrative and external items in `SUBMISSION_CHECKLIST.md` are not.
