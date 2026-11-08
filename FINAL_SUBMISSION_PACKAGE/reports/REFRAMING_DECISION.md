# Reframing decision (Part 9)

The revision brief asks whether the manuscript should be reframed away from a claim of physical
timing isolation and toward configuration, specification and execution-assumption analysis, and
requires that the title, abstract, research questions, contributions, results, discussion and
conclusion all tell the same evidence-supported story.

**Constraint accepted:** no new physical hardware experiments are performed for this revision, and
none are fabricated or simulated in their place.

---

## 1. Was the manuscript claiming physical timing isolation?

Checked rather than assumed. The audit searched the manuscript for timing and latency claims and
found **none that assert a physical result**. Specifically:

| Check | Result |
|---|---|
| Any reported latency value presented as a device measurement | **none** |
| "Complete isolation", "guaranteed real-time", "universally secure", "zero vulnerability", "production-ready", "proven for all devices" | **none present** |
| Host latency presented as physical ESP32 latency | **none** |
| Logical isolation presented as measured timing isolation | **none**; the manuscript decomposes invariance into logical and timing isolation and attributes different evidence to each |
| Analytical bound presented as an observed result | **none**; the response-time section produces no number for $R$ |
| Figure 6 panel B | already labelled as not yet measured |

**Finding: the manuscript was already framed around what the evidence supports.** The reframing
the brief anticipates had largely been done in earlier work, and the correct action is therefore
not to reframe but to verify, sharpen and say so. Rewriting a correctly-framed manuscript to
demonstrate activity would be the wrong response to the brief.

---

## 2. Decision on the title: **retain**

Current title:

> Unverified Assumptions in Embedded Safety Firmware: Configuration, Specification and
> Response-Time Defects in an MQTT Alarm System

Assessed against the brief's proposed direction, *"Configuration, specification and
execution-assumption analysis in embedded MQTT safety firmware"*:

| Requirement | Current title |
|---|---|
| Leads with assumptions rather than a mechanism claim | yes — "Unverified Assumptions" is the first phrase |
| Names all three dimensions | yes — configuration, specification, response-time |
| Avoids any isolation or timing-guarantee claim | yes — says "Response-Time **Defects**", which is what was found: an unbounded drain in the safety loop |
| Signals single-system scope | yes — "**an** MQTT Alarm System", singular |
| Matches the contribution list and the results | yes, and more closely after the restructuring in §4 |

"Response-Time Defects" is the precise and defensible phrase. The defect found *was* a
response-time defect: the safety loop had no static bound on its own execution time. The title
claims a defect was found, not that a timing property was measured.

**No scientific or editorial reason supports changing it**, and the earlier brief's instruction to
retain the title absent such a reason therefore applies. The one thing the title does not say is
"case study"; that is carried by the singular "an MQTT Alarm System" and stated explicitly in the
contributions and the scope subsection, which is the right place for it.

---

## 3. Decision on the abstract: **retain, already aligned**

249 words, within the publisher's limit. It states the problem, the gap, the method, the evidence
with its category, the quantitative findings, the contribution and the limitation — including that
physical timing invariance is unmeasured. No forbidden term appears. No change required.

---

## 4. Structural change made: one section per defect dimension

This is the one substantive misalignment the audit found between the claimed contribution and the
paper's architecture.

**Before.** The three dimensions were unequally placed. The execution dimension had its own section
(Response-Time Analysis, §5). The specification dimension had a subsection inside Formal
Verification, which is reasonable. But the **configuration dimension — the paper's strongest
finding, its first contribution, and the first dimension named in its title — was a *Discussion*
subsection**, roughly 240 lines from the end of the paper. The corpus study, which answers RQ5 in
full, was also a Discussion subsection.

A reader looking for the paper's main mechanism analysis would not have found it where the title
and contributions led them to look.

**After.** Both were promoted to numbered sections, placed immediately after Results so that the
analysis still follows the measurement it interprets and no forward references are created:

| § | Section |
|---|---|
| 9 | Results |
| **10** | **The Configuration Defect: a Guard that Encodes an Unsound Inference** |
| **11** | **Corpus Analysis and Generalizability** |
| 12 | Independent Hardware Validation Framework |
| 13 | Discussion |

Three cross-references that pointed readers to the Discussion for the guard analysis were
repointed to the new `sec:config` label, and the resolved section numbers were verified in the
rendered PDF. The manuscript rebuilds at 32 pages with 0 errors, 0 warnings and 0 undefined
references.

**Why not the brief's full suggested structure.** The brief proposes dimension sections *before*
the experimental evaluation. That ordering suits a paper whose dimension sections are purely
analytical, but here the guard analysis quotes and interprets measured arms, so placing it before
Results would create forward references into the evaluation and separate the interpretation from
the data it rests on. The brief permits changing its proposed structure where the argument becomes
clearer, and keeping interpretation adjacent to measurement is clearer. One section per dimension —
the brief's actual objective — is achieved either way.

---

## 5. Evidence-category separation, verified

The brief requires that six evidence classes stay distinct. Verified across the manuscript:

| Class | Where it appears | Kept distinct |
|---|---|---|
| Host-build testing | campaign, ablation, fuzzing, 129 host tests | yes, labelled "simulation result" |
| Software simulation | E1–E5 | yes |
| **Loopback broker testing** | E6 | yes — labelled the one "testbed measurement" in the paper, and the loopback limitation is stated |
| Formal model checking | E9, trace conformance | yes, with the bounded-abstraction caveat |
| Mathematical analysis | response-time decomposition, Theorem 1 | yes, and produces no number |
| **Physical hardware measurement** | **nowhere** | yes — there is none, and the paper says so |

The one empirical anchor from prior work (IP-layer interference on an ESP32) is attributed to that
work and identified as a different load class from the radio-layer question left open.

---

## 6. Coherence check: does everything tell the same story?

| Element | Story told |
|---|---|
| **Title** | assumptions in three dimensions; defects found; one system |
| **Abstract** | same three dimensions, with the timing limitation stated |
| **Research gap** | stated critically in §1, now with 2026 literature behind each dimension |
| **RQ1–RQ5** | one per dimension plus trade-offs and generalisation; RQ3 explicitly asks what analysis can establish *when measurement is unavailable* |
| **Contributions C1–C5** | one per dimension plus the trade-off measurement and the published protocol; each names what is *not* novel |
| **Results** | three metrics, per-rate breakdowns, paired tests, negative results reported |
| **§10, §11** | the configuration mechanism and the corpus null result, each in its own section |
| **§12** | the protocol for the open question, pre-registered and unexecuted |
| **Discussion** | synthesis, with the couplings between dimensions |
| **Threats to validity** | §1–§4 of `docs/THREATS_TO_VALIDITY.md`, including the two statistical errors corrected in this revision |
| **Conclusion** | five methodological findings; the open timing question restated as open |

**No element claims more than the evidence supports, and the timing limitation appears in the
abstract, the response-time section, the hardware section, the threats, the limitations and the
conclusion** — not hidden in a final paragraph.

---

## 7. Venue consequence, stated plainly

The absence of hardware data is **not** fatal to the configuration and specification dimensions,
which are the paper's strongest parts and rest on measurement (3,600 trials, 8 live-broker
scenarios) and exhaustive model checking respectively.

It **is** fatal to any venue that reads the execution dimension as the headline, because a
real-time or embedded-systems venue will expect a measured WCET and there is none.

The reframing that matters is therefore not of the manuscript but of the **venue choice**: the paper
should be submitted where an in-depth single-system case study with a methodological finding is an
accepted article type, and where the security and empirical-software-engineering contributions are
read as the contribution. That assessment is in `docs/JOURNAL_SELECTION_2026.md`.
