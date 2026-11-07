# Title evaluation and final selection

Written in response to a request to decide whether the working title represents the evidence
available at commit `87dcba5`, to assess four candidates, and to select one.

Every title below is scored on the six criteria requested: scientific accuracy, alignment with
the contributions that survived the reduction from eight to five (`docs/CONTRIBUTIONS.md`),
clarity, searchability, journal suitability, and whether it overstates novelty, generality or
physical measurement.

---

## What the evidence actually supports

The paper's central claim, as stated in `docs/CONTRIBUTIONS.md` and in Section 1 of the
manuscript, is:

> A security property asserted in build configuration, and a timing property asserted in
> design, are both unverified claims. Each can be falsified by a method that costs far less
> than the system it checks.

Three concrete defects support it, and each sits in a different kind of assumption:

| Defect | Where the assumption lived | What falsified it |
|---|---|---|
| Compile guard accepted TLS + broker login as publisher authority | build configuration | ablation over 12 configurations |
| Command drain assumed bounded | design | response-time decomposition |
| `NoUnauthRemoteDisarm` assumed the refusal rather than deriving it | the TLA+ specification | mutation of the specification |

What the paper does **not** have:

- any measured physical timing quantity (the hardware rig is specified and not run);
- any new mechanism, attack, protocol or formalism;
- any prevalence claim (the 135-project corpus returned zero hits for the guard rule, and the
  nine manually confirmed projects support an existence claim only).

A title must therefore avoid implying measured timing, novelty, or generality beyond one
system.

---

## The working title

> **Isolating the Safety Function on a Single-Chip Wi-Fi SoC: Formal Verification,
> Response-Time Analysis, and a Reproducible Measurement Protocol**

**Verdict: replace.** Three independent problems, the first serious.

1. **"Isolating" asserts the paper's least-supported claim.** As a present participle it
   states that the work achieves isolation. The paper establishes *logical* isolation (a TLA+
   model, bounded queues, a zero-timeout lock) and explicitly declines to claim timing
   invariance, which is a property of the silicon and a closed-source radio driver. A reader
   of a real-time or embedded-systems journal will read "isolating the safety function" as a
   timing claim, because that is what isolation means in that literature.

2. **The paper's own best result contradicts it.** The response-time decomposition found an
   *unbounded* drain in the safety path. The isolation the title asserts was, at the point the
   analysis was done, defective. A title claiming isolation while the body reports that the
   isolation argument had a hole in it is not a presentational problem; it is an accuracy
   problem.

3. **It describes methods, not findings.** "Formal Verification, Response-Time Analysis, and a
   Reproducible Measurement Protocol" is a list of things done. Two of the three were
   *instruments*, and the third is scaffolding for an experiment that has not been run —
   `docs/CONTRIBUTIONS.md` moved it out of the contributions list for exactly that reason.
   Promoting it to the title invites the reviewer question the document anticipates: why was
   the measurement not simply performed?

Secondary: "single-chip Wi-Fi SoC" is not a term anyone searches; "ESP32" and "MQTT" are, and
neither appears. The title also omits security entirely, although the two strongest results are
security findings.

---

## The four candidates

### 1. "When Verification Assumptions Fail: Security and Timing Defects in Embedded Safety Firmware"

| Criterion | Assessment |
|---|---|
| Accuracy | Mostly good. "Verification assumptions" fits the vacuous invariant exactly, but the compile guard was a *configuration* assumption and the drain a *design* assumption; neither is a verification assumption. The noun undersells two of the three findings. |
| Contribution alignment | Partial. Names the findings, not the method claim that unifies them. |
| Clarity | Clear. |
| Searchability | Weak. No MQTT, no ESP32, no IoT. |
| Journal suitability | The "When X Fails:" construction is common enough to read as a conference-talk title, and several journals' author guidance discourages rhetorical openings. |
| Overstatement | "Timing Defects" risks being read as measured timing. No novelty or generality overclaim. |

**Not selected:** the governing noun misclassifies two of the three defects.

### 2. "Falsifying Design Assumptions in Embedded Safety Firmware: A Case Study of Security and Timing Defects"

| Criterion | Assessment |
|---|---|
| Accuracy | Good. "Falsifying … assumptions" is the central claim almost verbatim. Same category problem as candidate 1, inverted: the compile guard is a configuration assumption and the vacuous invariant a specification assumption, so "design assumptions" covers one of three precisely. |
| Contribution alignment | Strong. Leads with the method claim. |
| Clarity | Clear. |
| Searchability | Weak, as above. |
| Journal suitability | Good. "A Case Study" correctly scopes the generality, which matters given the corpus result. |
| Overstatement | None, beyond "Timing Defects". |

**Not selected, but closest of the four.** The scoping and the method-first framing are both
right; only the category noun is imprecise.

### 3. "Unverified Security and Timing Assumptions in Embedded IoT Firmware: An Empirical Case Study"

| Criterion | Assessment |
|---|---|
| Accuracy | Mixed. "Unverified assumptions" is right. "Empirical" is wrong for a third of the work: the response-time decomposition is analytical and the vacuous-invariant finding is formal, and the manuscript is at pains to separate measured, simulated, formal, analytical and corpus evidence. A title calling the whole thing empirical undoes that distinction on the cover. |
| Contribution alignment | Weak. Names the problem but neither the method nor the findings. |
| Clarity | Clear. |
| Searchability | Best of the four — "IoT" is a high-traffic term. |
| Journal suitability | Acceptable but generic; it would fit several hundred papers. |
| Overstatement | None. |

**Not selected:** "Empirical" misdescribes the formal and analytical contributions.

### 4. "Unverified Assumptions in Embedded Safety Firmware: Configuration Defects, a Vacuous Invariant, and What Cheap Falsification Finds"

| Criterion | Assessment |
|---|---|
| Accuracy | Highest of the four. It is the only candidate that names the vacuous invariant, which is a genuine and unusual disclosure, and the only one that does not misclassify a defect. |
| Contribution alignment | Strongest. Problem, findings and method all present. |
| Clarity | Good until the last clause. "What Cheap Falsification Finds" is coy where the rest of the title is precise, and "cheap" is an argument the paper makes rather than a fact a title should assert. |
| Searchability | Weak. No MQTT, no IoT, no ESP32. |
| Journal suitability | The trailing rhetorical clause reads as a workshop title. |
| Overstatement | None. It also drops the third defect (the drain), listing two of three. |

**Not selected:** right content, wrong register in the final clause, and incomplete.

---

## Alternatives considered

| Candidate | Why not |
|---|---|
| "Unverified Assumptions in Embedded Safety Firmware: A Compile-Time Guard, a Vacuous Invariant, and an Unbounded Queue Drain" | Accurate and complete, but reads as a list of three bugs in one system rather than a transferable result. Sells the paper short. |
| "Falsifying Configuration and Design Assumptions in Embedded Safety Firmware: An MQTT Alarm Case Study" | Good scope and keywords, but names no finding, so the title promises a method paper and the body delivers findings. |
| "Three Unverified Assumptions in an Embedded Alarm, and the Cheap Methods That Falsified Them" | Readable, but "cheap" as a title claim again, and no field keyword. |
| "Cheap Falsification of Security and Timing Assumptions in Embedded Safety Firmware" | Compact and method-first, but asserts cheapness and omits the findings and the artifact. |

---

## Selected title

> **Unverified Assumptions in Embedded Safety Firmware: Configuration, Specification and
> Response-Time Defects in an MQTT Alarm System**

129 characters.

### Justification against the six criteria

**Scientific accuracy.** Each of the three nouns in the subtitle names one defect and the kind
of assumption it lived in, with no residue:

- *Configuration* — the compile-time guard (Section 6, `docs/SECURITY_ANALYSIS.md`);
- *Specification* — the vacuous `NoUnauthRemoteDisarm` invariant (Section `sec:vacuity`);
- *Response-time* — the unbounded command drain (Section `sec:timing`).

"Response-time defect" is an analytical statement about a bound, not a measurement, and so
carries no implication that latency was measured. This matters: it is the exact failure of the
working title.

**Alignment with the contributions.** "Unverified Assumptions" is the head noun of the central
claim as `docs/CONTRIBUTIONS.md` states it. The three defects are contributions 1, 2 and part
of 4 in the reduced list. Nothing in the title corresponds to a contribution that was demoted.

**Clarity and academic professionalism.** Declarative, no rhetorical opening, no colon-joke, no
superlative. The subtitle is a parallel three-item list, which is a conventional and readable
form for a findings paper.

**Searchability.** Carries *embedded*, *safety*, *firmware*, *MQTT*, *configuration*,
*specification* and *response-time*. "MQTT" is the highest-value term the working title was
missing. *ESP32* is deliberately left to the keywords and abstract: putting a part number in
the title narrows the readership more than it helps retrieval, and the paper's claim is about a
practice rather than about one chip.

**Journal suitability.** Fits a systems, embedded-software or security-engineering venue. It
promises a case study with transferable method, which is what the paper is, rather than a new
mechanism, which it is not.

**Overstatement check.**

| Risk | Status |
|---|---|
| Implies measured physical timing | No. "Response-time defect" is analytical, and the abstract's closing paragraph states no latency figure is reported. |
| Implies a new vulnerability | No. No mention of a vulnerability, attack or exploit. |
| Implies prevalence or generality | No. "in an MQTT Alarm System", singular and indefinite, scopes it to one artifact, which is what the zero-hit corpus result requires. |
| Implies novelty of method | No. The methods are not named in the title at all. |
| Implies isolation was achieved | No. The word is gone. |

---

## Title–abstract–contribution alignment

Checked after the change was applied. "Supports" means the element states or follows from the
title; "changed" means it had to be edited to do so.

| Element | Status | Note |
|---|---|---|
| Title | changed | as above |
| Abstract, opening | supports | already framed as "Both are *assertions* … neither is checked … what happens when each is falsified cheaply" |
| Abstract, middle | supports | names the configuration defect and the response-time defect with their measured consequences |
| Abstract, vacuous invariant | changed | the abstract named two of the three defects; the specification defect is now stated there too, so the three nouns in the subtitle each have a referent in the abstract |
| Abstract, closing | supports | "These results establish *logical* isolation only … we report no latency figure we have not measured" |
| Keywords | changed | "real-time task isolation" removed, since the title no longer claims isolation; MQTT, configuration defects, specification mutation and response-time analysis added |
| Introduction, central claim | supports | quoted verbatim at line 140 |
| Introduction, contribution 1 | supports | configuration defect |
| Introduction, contribution 2 | supports | response-time defect |
| Introduction, third instance | supports | vacuous invariant, named in the paragraph before the list |
| Section headings | supports | `sec:vacuity`, `sec:timing`, `sec:results` already named for the three defects; no heading claimed isolation |
| Conclusion | changed | closing paragraph reworded so it does not reprise "isolating the safety function" |
| Figure captions | supports | no caption claims isolation or measured timing; Figure 6's caption states that no number comes from the hardware panel |

### What was *not* changed, and why

The paper keeps the response-time analysis as a contribution and keeps the measurement
protocol as a section. The title no longer advertises either, which is the point: the protocol
is the honest response to an open question, not a result, and `docs/CONTRIBUTIONS.md` already
moved it out of the contributions list. Demoting it from the title completes that decision.
