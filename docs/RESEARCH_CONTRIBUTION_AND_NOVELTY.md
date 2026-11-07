# Research contribution and novelty

What is defensibly new in this work, what is not, and how the claim was validated against 2026
literature. Written after the evidence audit (`docs/EXPERIMENTAL_EVIDENCE_AUDIT.md`) and before
any manuscript revision, so that the positioning follows the evidence rather than the reverse.

---

## 1. What is explicitly **not** claimed as novel

Stated first, because the credibility of everything below depends on it.

| Technique | Status in this work |
|---|---|
| HMAC-SHA256 message authentication | standard primitive, used as specified |
| Monotonic counters for replay resistance | standard construction |
| MQTT over TLS with per-client ACLs | documented broker feature |
| TLA+ and TLC model checking | established tool, used as intended |
| FreeRTOS core pinning | documented platform facility |
| Coverage-guided fuzzing with ASan/UBSan | standard practice |
| Response-time decomposition | classical real-time analysis |
| **Vacuity detection in temporal model checking** | **established since 1999** — Beer et al.; Kupferman and Vardi; Kupferman's later sanity-check work. This work does **not** contribute a vacuity-detection technique |
| Mutation of checkers for property qualification | also established prior art |
| Arrival-curve / service-curve backlog analysis | network calculus, mature field |
| ESP32 deauthentication detection | demonstrated previously; no novelty claimed |

A reviewer who reads the contribution list as claiming any of the above would be right to reject
the paper. The contribution is not a technique.

---

## 2. The proposed central direction, and whether it survives

The direction put to test was:

> Systematic identification, falsification and formal analysis of configuration, specification
> and execution assumptions in resource-constrained embedded safety firmware.

### 2.1 The three dimensions, as actually instantiated

| Dimension | The assumption that was false | How it was falsified | Cost when false |
|---|---|---|---|
| **Configuration** | "A client authenticated to the broker over TLS is authorised to issue commands" — encoded in a preprocessor guard | 300-trial arm plus live-broker scenarios | alarm activation 300/300 → **50/300**; 246/300 disarms |
| **Specification** | "The firmware refuses unauthenticated remote disarm" — encoded as `UNCHANGED` in a TLA+ action, with the conclusion asserted in a comment | inverted model-checking configuration that **requires** a violation | the invariant was unfalsifiable; TLC reported success on every push |
| **Execution** | "The safety loop's own work is bounded" — encoded nowhere at all | writing the response-time decomposition, which required a bound that did not exist | no static bound on the loop whose timing the design exists to protect |

### 2.2 Is the connection between the three real, or rhetorical?

This is the question that decides whether the paper has one contribution or three anecdotes. Two
specific couplings were found in the artefacts, and they are what make the framing more than a
list.

**Coupling 1 — the specification inherited the configuration assumption.** This is the strongest
evidence for the framing. `NoUnauthRemoteDisarm` was vacuous *because the model hard-coded the
same build-time assumption the firmware got wrong*: the action asserted the refusal rather than
deriving it from a parameter. So dimension 2 did not independently fail to catch dimension 1 — it
failed *because it had imported dimension 1's assumption*. The repair was to make the build
switch a model parameter, which is precisely the act of moving the assumption from implicit to
checkable. A formal check cannot refute an assumption its own model asserts.

**Coupling 2 — the execution assumption was invisible to the other two instruments, by
construction.** The unbounded drain passed 9,600 adversarial trials, 3,000,000 fuzzing iterations,
exhaustive model checking and 129 host tests. It was undetectable by the formal model because
that model has no notion of duration, and undetectable by testing because the loop does terminate
in practice. The dimensions are therefore not merely three places to look; they have **disjoint
blind spots**, and that is a structural claim rather than an observation about this artefact.

**A third coupling, found during this revision, strengthens the framing further.** The project's
own analysis code reported a Mann–Whitney test of latency as "indistinguishable" when every
observation in both samples was the same constant — a test incapable of rejecting, labelled as
having passed (audit §5.4). This is dimension 2's failure mode occurring in the *measurement
infrastructure* rather than in the specification. Five instances now exist, four of them in this
project's own artefacts.

### 2.3 Honest verdict on framing

**This is a case study with a methodological finding, not a general framework, and it must be
positioned as one.**

What the evidence supports:
- A single-system, in-depth account of three assumption classes failing in one firmware artefact,
  each falsified by a method that cost far less than the system it checked.
- A structural argument, supported by the couplings above, that the three instruments have
  disjoint blind spots, so applying any one of them in isolation is unsafe.
- Two reusable mechanisms: a model-checking configuration whose *required* outcome is a violation,
  and a `static_assert` tying a drain bound to a queue capacity.

What the evidence does **not** support:
- A validated framework. There is no second system, no inter-rater reliability, no cost model, and
  no demonstration that the method transfers.
- A prevalence claim. The corpus study returned **0/135** for the precise rule.

The word "framework" should not appear in the revised manuscript's contribution list. "Case
study", "field report" and "method" are defensible; "framework" is not, and a Q2 reviewer in
empirical software engineering will test that word specifically.

---

## 3. Novelty validated against 2026 literature

Each dimension checked against the closest recent work found. Full records in
`docs/LITERATURE_REVIEW_2026.md`.

### 3.1 Configuration dimension

**Closest work: Paixão et al., *Proc. ACM Softw. Eng.* 3, FSE, Art. FSE119 (July 2026)** —
*PatchLens*, static derivation of configuration conditions under which known vulnerabilities are
present, over 1,581 security patches across the Linux kernel, FFmpeg and PHP. It resolves
preprocessor presence conditions and build-system logic, so it addresses compile-time variability
rather than runtime config files.

**Gap.** PatchLens answers *which configurations contain code already known to be vulnerable*,
starting from patches and CVEs. It does **not** evaluate whether the security inference encoded in
a guard is itself sound, and it does not study embedded firmware. This work asks the complementary
question — is the guard's own reasoning valid — and measures the safety cost when it is not. The
two are not in competition; PatchLens needs a known vulnerability as input, and this work is about
the case where no CVE exists because nobody has questioned the inference.

**Closest MQTT work: Ghazi Asgar and Reddy, SDIoTSec 2025 (NDSS), DOI 10.14722/sdiotsec.2025.23010**
— measures *deployed* brokers accepting anonymous connections, via Shodan plus a 10-repository
popularity ranking, and **explicitly defers ACLs to future work**. No static analysis of firmware
or build configuration.

**Also close: Radwan and Sheldon, *Applied Sciences* 16(7):3583, 2026, DOI 10.3390/app16073583** —
experimental quantification of MQTT authentication enforcement and ACL misconfiguration impact on
Mosquitto. Of all work found, this is the nearest neighbour to experiment E6.

**Gap against Radwan and Sheldon.** Their study (method verified from the authors' preprint; see
the caveat in the literature review) measures authentication and authorisation success rates, FAR,
FRR and ACL granularity effects with two fixed roles. It does **not** compare broker ACLs against
application-layer message authentication as alternatives, does **not** model compromise indexed by
*which identity holds which secret*, does **not** touch firmware build configuration, and measures
**no safety or actuation outcome**. This work's E/E′ pair — the same valid signature refused from
the device identity and accepted from the controller identity — is exactly the comparison their
design cannot make, and the alarm-activation metric is the actuation outcome they do not have.

### 3.2 Specification dimension

**Prior art is strong and old.** Vacuity detection dates to Beer et al. and to Kupferman and
Vardi's work on vacuity in temporal model checking, with later sanity-check and
mutation-of-checkers literature. **No technical novelty is available here, and none is claimed.**

**What remains defensible** is an empirical report: a specification of a real embedded artefact,
checked in continuous integration on every push, was vacuous as shipped, and its vacuity masked a
firmware defect that other methods did find. Published accounts of vacuity are largely
technique-and-benchmark papers; a field instance tied to a specific configuration assumption and a
specific firmware defect is a different kind of evidence and is worth reporting as such.

**A live 2026 parallel to position against:** Canedo, *arXiv:2608.17214* (preprint, 17 Aug 2026),
"Oracles That Cannot Fail", introduces *oracle anchoring* — an oracle whose expected value derives
from the system it judges cannot detect faults that move measurement and expectation together,
with specification-anchored versus state-anchored as the distinction. The vacuous invariant here is
an assumption-anchored oracle in exactly that sense. Canedo's domain is property-based testing of a
TypeScript simulator evaluated by mutation testing; this work's is formal specification and build
configuration in embedded firmware. Complementary, and citing it places this work in a current
conversation rather than in isolation. It is a preprint and must be labelled as one.

### 3.3 Execution dimension

Response-time decomposition is classical. The defensible points are narrow and should be stated
narrowly:

1. **Response-time analysis used as a defect-finding instrument rather than a certification
   instrument.** The analysis was not completed — no number for $R$ is produced — and it still
   found a real defect, because the derivation required a quantity the code did not possess. That
   is a methodological observation about when the analysis pays for itself.
2. **An explicit $B = 0$ argument from an asymmetric mutex timeout**, verified formally as
   `SafetyCanAlwaysStep`, with the logical/physical boundary stated precisely. The construction is
   not new; the pairing of the source-level argument with an exhaustive check of its logical
   consequence, and the refusal to extend it to a timing claim, is the contribution.
3. **A pre-registered falsification protocol published without being executed.** Committed before
   any data existed, with the test, sample sizes and acceptance criteria fixed.

Prior ESP32 interference measurement (IP-layer load, single-digit percent cycle loss) remains the
one empirical anchor, and it is a *different* load class from the radio-layer question left open.

### 3.4 Generalisation dimension

The corpus study must be reported as what it is: **rule 1 returned 0 hits across 135 projects.**
Rule 2 flagged 18, of which 9 were confirmed by hand and 9 were false positives, with known
under-counting of non-GPIO actuation.

This supports an **existence claim** and nothing more. The sample is 22 fixed GitHub queries with
a 3-star minimum and an 80 MB cap, excluding archived repositories and forks, with 437 rejections
on stars alone — a convenience sample of public hobby and educational code, not a population.
Compare Ghazi Asgar and Reddy, who use a 900-star threshold and Shodan counts and still make only
exposure-share claims.

**The honest position: the corpus supports a limited case-study observation, not a broader
finding.** The zero is reported as a zero and explained (only 30 of 135 projects both subscribe to
MQTT and contain any application-authentication identifier), and no prevalence is asserted.

---

## 4. Research questions, refined

Each with its objective, checkable outcome, required evidence and limitation. **Hypotheses are
stated only where the available evidence can test them.**

### RQ1 — Configuration assumptions

*How can build-time security configuration assumptions create exploitable authorisation failures
in embedded MQTT alarm firmware?*

- **Objective.** Identify the unsound inference, explain why it is unsound from protocol
  semantics, and measure its cost on the safety function.
- **Checkable outcome.** Alarm activation and unauthorised-disarm counts under a single leaked
  credential, against an identically-built control.
- **Evidence.** 300-trial arms (50/300 vs 300/300; 246 disarms; Fisher *p* = 9.83 × 10⁻¹¹⁹) plus
  live-broker scenarios B and C.
- **H1 (testable, tested, supported).** Under a single leaked broker credential, a build whose
  guard treats transport authentication as publisher authority admits adversary disarm at a rate
  indistinguishable from a build with no command authentication at all.
- **Limitation.** One protocol version, one broker, our adversary model, simulation for the
  trial counts.

### RQ2 — Specification assumptions

*How can vacuous formal safety properties allow defective embedded firmware configurations to
pass verification?*

- **Objective.** Document a vacuity instance in a shipped, CI-checked specification; identify its
  cause; demonstrate a mechanism that prevents recurrence.
- **Checkable outcome.** The invariant's falsifiability — a configuration under which TLC
  *must* report a violation of the named invariant.
- **Evidence.** `AlarmFSM_unsafe.cfg`; the runner requires the string
  `Invariant NoUnauthRemoteDisarm is violated`, so a parse error cannot pass as the expected
  violation. Verified on every run.
- **No statistical hypothesis.** Vacuity is a logical property; a *p*-value here would be
  decoration. Stated explicitly because Part 3 of the task warns against inventing one.
- **Limitation.** No technique novelty; one specification; bounded abstraction (`MaxCtr = 4`).

### RQ3 — Execution assumptions

*What can analytical response-time modelling establish about network-related execution
interference on an embedded safety task when physical timing measurements are unavailable?*

- **Objective.** Decompose $R$, establish which terms are settled by construction, and state the
  residual as a function of named hardware parameters.
- **Checkable outcome.** $R = C_{\text{own}} + B + I_{\text{isr}} + I_{\text{mem}}$ with $B = 0$
  from source and $C_{\text{own}} = O(1)$ per stage; conditional deadline theorem; backlog bound
  from actual capacities.
- **Evidence.** Source-level argument; `SafetyCanAlwaysStep` over 660 distinct states;
  `docs/MATHEMATICAL_MODEL_AND_PROOFS.md`.
- **H2 (not testable here).** Physical timing invariance. **Requires hardware; not tested.** The
  pre-registered protocol exists and was not executed.
- **Limitation.** No value for $R$. $I_{\text{isr}} + I_{\text{mem}}$ are unmeasured, and the
  Wi-Fi driver is closed-source, so they are not statically analysable.

### RQ4 — Security trade-offs

*How do broker access control, application-layer message authentication and layered protection
behave under different attacker capabilities?*

- **Objective.** Establish whether either control dominates, indexed by which secret the adversary
  holds rather than by mechanism.
- **Checkable outcome.** A 9-cell matrix over three metrics, with the decisive pair confirmed
  against real broker software.
- **Evidence.** 3,600 ablation trials; 8 live-broker scenarios; the E/E′ pair.
- **Finding, stated as a negative result.** Neither dominates. The ACL contains a device
  compromise the MAC cannot; the MAC contains a broker-credential compromise the ACL cannot; the
  layered build falls to a compromised controller host, which is the **cheaper** attack than the
  flash dump it survives.
- **Limitation.** One broker, one version, one ACL; loopback.

### RQ5 — Methodological generalisation

*To what extent can the identified defect patterns be detected in a corpus of open-source embedded
MQTT projects?*

- **Objective.** Attempt generalisation and report the outcome whichever way it falls.
- **Checkable outcome.** Hits for a precise rule and a loose rule, with manual adjudication and a
  labelled control set.
- **Evidence.** 0/135 (rule 1); 18/135 flagged, 9 confirmed (rule 2); 8 controls including this
  project's own pre-repair and repaired guards.
- **No hypothesis.** A prevalence hypothesis would require a sampling frame this corpus does not
  provide.
- **Answer.** *To a very limited extent.* The precise pattern was not found at all. This is
  reported as a **null result**, and the attempt's value is the labelled control set and the
  documented rule-polarity defect, not the count.

---

## 5. Contributions, as they should appear

Five, each verifiable against a named section and artefact, and each stated at the strength the
evidence supports.

**C1 — A configuration defect that costs a safety property, with its cost measured.** A
compile-time guard accepted TLS plus a broker login as evidence of publisher authority; the
inference is unsound because the MQTT 3.1.1 broker re-originates messages. Under one leaked
credential, alarm activation fell to 50/300 against 300/300 for the control. The guard emitted no
diagnostic and survived review. *Not novel:* the protocol semantics. *Novel:* the measured safety
cost of the unsound inference, and the build-time rejection with a named acknowledgement escape.

**C2 — A vacuous invariant, disclosed, with a regression test for vacuity.** The property stating
that unauthenticated remote disarm never takes effect was unfalsifiable in the specification that
was shipped and checked in CI, because the model asserted the refusal rather than deriving it from
the build parameter. The runner now *requires* a deliberately defective configuration to fail.
*Not novel:* vacuity detection. *Novel:* the field instance, and the demonstrated coupling — the
specification was vacuous because it had imported the configuration assumption the firmware got
wrong.

**C3 — A response-time decomposition that exposed an unbounded drain, plus a conditional
deadline theorem.** Three of four interference terms are removed or bounded by construction, with
$B = 0$ from an asymmetric mutex timeout and verified formally as a logical property. Deriving the
bound revealed that the safety loop had no static bound on its own execution time, a defect that
had passed 9,600 adversarial trials, 3,000,000 fuzzing iterations, exhaustive model checking and
129 host tests. *Not novel:* response-time analysis. *Novel:* its use as a defect-finding
instrument, and the precise statement of the logical/physical boundary.

**C4 — A measurement of defence independence under capability-indexed compromise.** A
twelve-configuration ablation over 3,600 trials shows availability, integrity and the safety
function failing independently, and shows broker authorisation and message authentication failing
under *different* compromises with neither dominating — reproduced against a live broker, where
the E/E′ pair isolates the ACL rather than the signature as what refuses a flash-dump adversary.
Includes two results that cut against this project's own design: the layered build's failure to a
compromised controller, and the counter-induced owner lockout.

**C5 — A published, pre-registered falsification protocol for the claim that remains open.**
Committed before any data existed, with the test, sample sizes and acceptance criteria fixed, and
published unexecuted so the timing question is falsifiable by someone else.

### Contributions deliberately **not** claimed

- Any new cryptographic, verification, scheduling or analysis technique.
- A validated methodology or framework.
- Any prevalence finding.
- Any physical timing result.
- Novelty for the counter-lockout *mechanism*: it is stated as background in prior ZigBee work.
  Only its measurement and the resulting coupling are contributed. **An earlier draft of the
  report claimed the mechanism had not been reported; that claim was wrong and is withdrawn.**

---

## 6. What a researcher can reuse

Asked directly by the task, and worth answering concretely rather than in the abstract.

1. **The inverted-configuration pattern.** A model-checking run whose *required* outcome is a
   violation of a named invariant, with the invariant's name matched in the output so that a parse
   error cannot pass as the expected failure. Applicable to any specification whose properties
   could become vacuous.
2. **The capability-indexed ablation design.** Indexing arms by *which secret the adversary holds*
   rather than by *which mechanism is deployed* is what made the non-domination result visible. A
   mechanism-indexed design cannot express the E/E′ distinction.
3. **Three metrics, not one.** Alarm activation alone would have ranked "no command defence" equal
   to a MAC. Reporting availability, integrity and the safety function separately is what exposed
   the independence.
4. **The labelled control set for the static rule**, including a known-defective guard and its
   repair. Reusable for validating any similar rule, and the reason the rule's polarity defect was
   caught.
5. **The `static_assert` tying a drain bound to a queue capacity**, so the response-time argument
   cannot silently drift from the code it describes.

---

## 7. Verdict on Q2 viability

**The contribution is defensible at Q2 level if, and only if, it is positioned as an in-depth
single-system case study with a methodological finding, in a venue that accepts that article
type.** The three couplings in §2.2 give it a thesis rather than a list, the live-broker E/E′ pair
and the 12-arm ablation give it real evidence, and the negative results give it credibility.

**It is not defensible if positioned as a framework, as a prevalence study, or in a venue that
expects physical measurement.** The absence of hardware data is not fatal to the configuration and
specification dimensions, which are the strongest parts; it is fatal to any venue that reads the
execution dimension as the headline. That is the reframing decision taken up in Part 9 and in
`docs/JOURNAL_SELECTION_2026.md`.
