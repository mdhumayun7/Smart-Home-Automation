# Simulated adversarial peer review

Three independent reviewers on the revised manuscript (33 pages, commit after the Part 9–11
restructuring), then an editor's consolidation.

**These reviews are a critical exercise, not a validation exercise.** They are written to find the
weakest points, and two of the three recommend major revision. They are a modelling aid and carry
no authority: **no real peer review has taken place, and nothing here constitutes acceptance by any
venue.**

---

# Reviewer 1 — Embedded and real-time systems

## Summary of the contribution

The authors study an ESP32 MQTT alarm firmware and report that three classes of assumption —
build-time security configuration, formal specification, and execution timing — were each false in
their own system, and that each was falsified by a method cheaper than the system it checks. For my
area the relevant content is §5, a response-time decomposition
$R = C_{\text{own}} + B + I_{\text{isr}} + I_{\text{mem}}$ with an argument that $B = 0$ from an
asymmetric mutex timeout, and §12, a pre-registered measurement protocol that has not been run.

## Major strengths

1. **The $B = 0$ argument is correct and cleanly made.** A zero-timeout `xSemaphoreTake` on the
   safety side with a 10 ms timeout on the network side does give an unconditional
   no-wait property, and pairing the source-level argument with an exhaustive check of
   `SafetyCanAlwaysStep` under a network task granted no fairness is better practice than I usually
   see. The authors do not overreach from it, which I checked specifically.
2. **The unbounded-drain finding is the most useful thing in the paper for a practitioner.** A
   `while (xQueueReceive(...))` loop in the safety task, with the other core able to enqueue
   concurrently, is a real defect, and the observation that it survived 9,600 adversarial trials,
   3,000,000 fuzz iterations and exhaustive model checking is a legitimate argument for doing the
   analysis. The `static_assert` tying $D_c$ to $N_c$ is the right fix.
3. **The logical/physical distinction is maintained consistently.** I went looking for a leaked
   timing claim and did not find one. The separation survives into the abstract, which is unusual.

## Major concerns

**M1. The paper's third dimension produces no number, and the title promises a defect in it.**
"Response-Time Defects" is in the title. What §5 delivers is a decomposition, an argument that one
of four terms is zero, and a theorem conditional on an assumption (T3) that bounds the very
quantity in question. There is no value for $\bar{C}$, no value for $\bar{I}$, no value for $R$,
and no deadline verdict. For my community this is an incomplete analysis. I accept that the defect
*found* is real and is a response-time defect, so the title is not false — but a reader from
real-time systems will arrive at §5 expecting an analysis and find a framework for one.

**M2. $\bar{C}$ is unquantified and that is not a hardware limitation.** The authors attribute
every missing number to the absence of an ESP32. But $C_{\text{own}}$ — in particular the I²C
display transaction $c_{\text{i2c}}$, which they identify as the largest term — could be bounded by
static analysis of the generated Xtensa code, or by a cycle-counting instruction on the target, or
estimated from the I²C clock rate and the transfer length, which is arithmetic requiring no device
at all. The authors' own §7 admits $\bar{C}$ is "the cheapest single measurement that would improve
this". So why was the arithmetic not done? A 128×64 SSD1306 page write at 400 kHz has a
calculable duration. This omission weakens the one part of §5 that did not need hardware.

**M3. The factor of 2 in $L \le T_{\text{conf}} + 2R$ is loose and the paper knows it.** The
authors note that under a uniform phase assumption the expectation is $T_{\text{conf}} + 1.5R$, then
proceed with the factor 2. Since $T_{\text{conf}} = 150$ ms dominates everything, the looseness
costs nothing — but then the authors should say that the bound's tightness is immaterial rather than
leaving a reader to wonder whether they tried to tighten it.

**M4. (T4) is asserted, not established.** "The safety task is the only task pinned to core 1" is
central to the no-preemption claim, and on an arduino-esp32 build it is not obviously true: the
framework creates its own tasks, the IDLE task exists per core, and timer and event tasks have
affinities set by the SDK. The authors should demonstrate this from the build — a task list dump, or
the relevant SDK configuration — rather than state it.

## Minor concerns

- §4.3 claims the detector cooldown is "load-bearing for the arrival bound". I agree, and it is a
  nice observation, but it belongs in the design section where an engineer tuning the detector will
  see it, not buried in a queueing appendix.
- The event-queue priority weakness (an alarm event droppable while rejection events are delivered)
  is correctly identified as a notification rather than safety issue. It is still a defect and
  should appear in the abstract's limitation sentence, not only in §14.
- "151 ms" appears as the constant simulated latency. Given the paper's own insistence that this is
  an artefact of the logical clock, I would drop the number entirely from the results and keep only
  the statement that variance is identically zero.

## Unsupported claims

I found none in my area. The `delay(2)` giving $P \ge 2$ ms is correctly used as a lower bound
only. The Proposition 5 overload condition ($P < 25$ ms) follows from the stated constants and I
verified the arithmetic.

## Missing evidence

A bound on $C_{\text{own}}$ (M2). A demonstration of core-1 exclusivity (M4).

## Mathematical weaknesses

Theorem 1 is valid but nearly vacuous as a theorem: with $B = 0$ established and $C_{\text{own}}$
and interference each assumed bounded, "$R \le \bar{C} + \bar{I}$" is a restatement of the
assumptions, and the rearrangement into a feasibility condition is algebra. The authors are honest
about this in §3.3 — they call it a conditional statement and say it yields no number — so I do not
regard it as overclaiming. But it should be presented as a *budget decomposition* rather than
dignified as a theorem with a proof environment. The genuinely non-trivial results are
Propositions 3–6, especially the sustained-overflow condition, which are given less prominence.

## Recommendation

**Major revision.** The paper is honest and the defect findings are real, but M2 and M4 are fixable
without hardware and should be fixed before this is published in an embedded venue. If the authors
cannot bound $C_{\text{own}}$, they should say explicitly why arithmetic from the I²C clock rate is
insufficient.

---

# Reviewer 2 — IoT security and MQTT

## Summary of the contribution

An ESP32 alarm firmware is shown to contain a compile-time guard that treats TLS plus a broker
login as evidence of publisher authorisation; the paper measures what that costs, then compares
broker ACLs against application-layer HMAC under compromises indexed by which secret the adversary
holds, with eight scenarios reproduced against a real Mosquitto broker.

## Major strengths

1. **The capability-indexed design is the right design and I have not seen it done this way.**
   Indexing arms by which secret the adversary holds, rather than by which mechanism is deployed, is
   what makes the non-domination result visible. The E/E′ pair — the same valid signature refused
   from the device identity and accepted from the controller identity — is a genuinely clarifying
   result, and it cannot be obtained from a mechanism-indexed design.
2. **Running it against a real broker was worth doing and the authors understood why.** The
   observation that MQTT 3.1.1 has no return code meaning "refused by policy", and that every
   denied publish was nonetheless PUBACKed, is the kind of detail that invalidates simulation-only
   studies of broker authorisation. Deciding each scenario by what a device-identity subscriber
   actually received is correct.
3. **The negative results are reported properly.** The layered configuration falling to a
   compromised controller, the authors' retraction of an earlier "survives every case" claim, and
   the owner lockout are all stated plainly and in the contributions, not buried. The observation
   that the configuration survives the *expensive* attack (physical flash dump) and falls to the
   *cheap* one (controller compromise) is the most important security insight in the paper.

## Major concerns

**M1. The loopback testbed is doing more work than the paper admits.** Eight scenarios on
localhost with one client at a time establishes that Mosquitto's ACL enforcement behaves as
modelled. It establishes nothing about a deployment: no concurrent clients, no retained-message
interactions, no session takeover via duplicate client IDs, no QoS 2 flows, no bridge, no
`$SYS` exposure. Several of those are the usual ways real MQTT deployments are broken. §3.4 of the
threats document mentions loopback; the manuscript should be equally explicit that the broker
result is a *conformance* check of one mechanism rather than a security evaluation of a deployment.

**M2. The threat model omits the most common real attack on this device class.** Scenarios A–E′ are
all about credentials and keys. Missing: a malicious or compromised *broker*, which in a home
deployment is frequently a third-party cloud service or a Raspberry Pi that the user does not
patch. The paper treats the broker as trusted infrastructure and never says so in the threat model,
although the controller is explicitly discussed. Since the whole ACL argument rests on the broker
enforcing policy faithfully, this assumption deserves a row in Table 2 and a sentence saying no
result survives a compromised broker.

**M3. There is no key management at all, and the paper's own strongest finding depends on that
absence.** No rotation, no revocation, no provisioning story. The owner-lockout result is a
*consequence* of having no counter-resynchronisation path, and scenario E′ is unrecoverable because
a compromised key cannot be retired. The paper lists these as scope exclusions, which is honest, but
a reader could conclude that a counter-bound MAC is a sound design for this problem. It is not,
without key management, and the paper should say so in the discussion rather than only in a
limitations table.

**M4. The 128-bit truncated tag needs a justification the paper does not give.** `AUTH_TAG_BYTES =
16` truncates HMAC-SHA256. That is defensible, but on a constrained command path the authors should
state the reasoning — forgery probability against the command rate, and why 16 rather than 8 or 32
— rather than leaving it as a constant in a table. The fuzzing section correctly notes that zero
forgeries in 3,000,000 attempts is expected either way, which makes the absence of an analytical
justification more conspicuous, not less.

## Minor concerns

- The corpus rule targets a guard pattern, but the paper's own strongest finding is about an
  *inference*, not a syntactic pattern. A rule that matches syntax cannot find the same class of
  defect expressed differently. This limits the generalisation attempt more than corpus bias does,
  and it is not discussed.
- "Credential separation, not the ACL syntax, is what carries the protection" is an excellent
  sentence that appears in a generated results document but, as far as I can see, not in the paper.
- Scenario B's shared-credential collapse is the single most likely real-world configuration and
  gets one row. It deserves more emphasis than E, which requires physical access.

## Unsupported claims

The manuscript previously said shared credentials are common in deployed fleets; the authors have
removed it and now state that no deployment data exists. Correct. I found no remaining prevalence
or deployment claim.

## Missing evidence

A compromised-broker row in the threat model (M2). Tag-length justification (M4).

## Reproducibility

Strong — among the best I have reviewed. Fixed seeds, committed raw records, byte-identical figure
regeneration, broker verdicts reproduced on a clean install. One gap: the raw campaign JSONL is not
committed, only `summary.json`, so the 6,000-trial campaign cannot be re-analysed without
re-running it. Given everything else is committed, that looks like an oversight.

## Recommendation

**Minor revision.** The security contribution is sound, correctly bounded and genuinely novel in
its comparison design. M1–M4 are presentation and framing fixes rather than new experiments, and
M2 in particular is a single table row plus a sentence.

---

# Reviewer 3 — Formal verification, empirical methodology and mathematical analysis

## Summary of the contribution

The authors report that a TLA+ invariant stating unauthenticated remote disarm never takes effect
was vacuous in the specification they shipped and model-checked in CI, because the model asserted
the refusal rather than deriving it from a build parameter. They add a configuration whose required
outcome is a violation. They also report an attempted corpus generalisation that returned a null
result, and a set of defects in their own measurement infrastructure.

## Major strengths

1. **The vacuity instance is a real contribution and the causal account is what makes it one.**
   Vacuity detection is prior art of twenty-five years' standing and the authors say so explicitly,
   which I verified. What they add is the *cause*: the specification was unfalsifiable because it
   had imported the same build-time assumption the firmware got wrong. That coupling between the
   configuration and specification dimensions is the paper's best idea, and it is what turns three
   anecdotes into a thesis. I would like it stated even more prominently than it is.
2. **Requiring the invariant's name in the model-checker output is a detail that shows care.**
   Inverting the exit code alone would accept a syntax error as the expected violation. Matching
   `Invariant NoUnauthRemoteDisarm is violated` does not. The same reasoning applied to the
   conformance checker's negative control is consistent and correct.
3. **The authors found and corrected two statistical errors in their own reported tests during this
   revision, and documented both.** The design is matched pairs — all arms on one seed set — and was
   analysed with Fisher's exact test; and the availability metric is clustered, with 231 of 250
   trials all-or-nothing, ICC 0.669. Correcting 3.53 × 10⁻¹⁸⁴ to 1.93 × 10⁻³⁴ and stating that the
   error was anti-conservative is exactly right, and reporting it rather than silently fixing it is
   rarer than it should be.

## Major concerns

**M1. Theorem 1 should not be a theorem.** With $B = 0$ proved and both remaining terms assumed
bounded, the statement $R \le \bar{C} + \bar{I}$ is immediate from its hypotheses. Dressing it in a
theorem-and-proof environment overstates its mathematical content, and Part 15's own gate —
"mathematical analysis adds genuine value" — invites exactly this challenge. Demote it to a
proposition or present it as a budget decomposition. The substantive results are Propositions 3–6;
Proposition 5 in particular, which derives that the event queue is in sustained overflow whenever
the loop period is under 25 ms, is a real and non-obvious finding about the artefact and is
currently under-sold.

**M2. The corpus study does not support its own place in the paper.** Rule 1: 0/135. Rule 2: 18
flagged, 9 confirmed, 50% false-positive. The authors report this honestly as a null result and
decline prevalence claims, and they cite a comparable 34% false-positive rate from a 258-project
study. But an honest null result is not automatically a publishable component: as it stands, §11
tells the reader that the authors looked for their defect elsewhere and did not find it. The
defensible contribution is the **labelled control set** and the **documented rule-polarity defect**
— the rule initially returned zero against the authors' own pre-repair guard — not the counts. I
would restructure §11 around the instrument and its validation, and relegate the counts.

**M3. Model coverage is thin relative to the firmware, and the ratio should be stated.** Two
specifications abstract a five-state machine, a counter and a seven-variable task model, from
1,166 lines of firmware. Not modelled: the HMAC computation, the parser, NVS persistence and its
failure modes, detector arithmetic, and — decisively — execution time. §6.4 lists these, and the
authors correctly say that selected properties of a bounded abstraction were checked exhaustively
rather than that the firmware was verified. I want the coverage stated quantitatively in the paper,
as it is in the authors' internal audit, so a reader can calibrate without reconstructing it.

**M4. `MaxCtr = 4` deserves a sentence on why it suffices.** The counter is the mechanism behind
both the replay resistance and the owner lockout, and the model bounds it at 4. A reader will ask
whether a monotonicity property established over a four-element counter space transfers to a
32-bit one. I believe it does, by a straightforward data-independence argument, but the authors
should make that argument rather than leave the bound unexplained.

**M5. Five instances of one pattern, four of them self-inflicted, raises a question the paper does
not confront.** The authors found a vacuous invariant, a degenerate statistical test, two
flattering harness defects and a wrong-polarity corpus rule — all in their own work. They present
this as evidence for their thesis, and it is. But it also bears on how much the *remaining*
unchecked parts of this artefact should be trusted, and the paper does not address that. The
mitigation offered is that each repair has a control; the honest extension is to say which parts of
the infrastructure still have no control.

## Minor concerns

- The hypotheses H1 and H2 are stated, but H2 ("physical timing invariance") is not testable with
  the available evidence and the authors say so. Then it should not be labelled a hypothesis of
  *this* study; it is the hypothesis of the pre-registered future study.
- The paper reports no multiplicity correction and justifies it by the arms being pre-declared.
  That is acceptable, but with twelve arms and two reported tests the authors should state which
  comparisons were planned before the data was seen. "Pre-declared" is asserted, not evidenced.
- `analyse_ablation.py` prints the detector false-positive rate as 79.8% in prose and 0.7985 in a
  table. Trivial, but it is the kind of thing this paper's own standards should catch.

## Literature weaknesses

The vacuity prior art is now correctly acknowledged. One gap: the authors cite a 2026 arXiv
preprint on oracle anchoring as a conceptual sibling, which is apt, but a preprint should not carry
positioning weight — the argument should stand on the peer-reviewed vacuity literature with the
preprint as a secondary observation. Also, one reference has its venue marked unverifiable. I accept
that this is more honest than inventing one, but the authors should make a further attempt to
resolve it; an unresolvable venue in a bibliography is a reviewer irritant.

## Reproducibility

Exemplary, with one real gap: the raw campaign records are not committed.

## Recommendation

**Major revision.** The core contribution — the vacuity instance with its causal account, and the
coupling it demonstrates — is worth publishing. M1 and M2 are presentational but they are what a
reviewer will seize on, and M3–M5 are short additions. None requires new experiments.

---

# Editor's consolidation

## Consensus

All three reviewers accept that the paper is honest, that its negative results are real and
properly reported, and that it does not overclaim. All three independently confirm that no physical
timing claim leaks into the text — which, given the brief's concern, is the most important
verification in this review.

The strongest parts, by agreement:
- the capability-indexed security comparison and the E/E′ pair (R2, and R3 by implication);
- the vacuity instance with its causal account (R3, and R1 on the formal pairing of $B = 0$);
- the unbounded-drain finding (R1 calls it the most useful result for a practitioner);
- reproducibility (R2 and R3 both call it among the best they have reviewed).

## The decisive disagreement

**R1 and R3 both say the paper's mathematics is presented above its weight, and R3 says the corpus
study does not justify its place.** R2, from security, sees no such problem. This is a venue
question as much as a content one: the response-time dimension is the paper's weakest and is
precisely what an embedded venue will review hardest. That matches the authors' own
`docs/JOURNAL_SELECTION_2026.md` assessment, which identifies this as the single likeliest cause of
rejection at their first-choice venue.

## Decision

**Major revision.** Two reviewers recommend it; the third's minor-revision verdict concerns a
different part of the paper. No reviewer requests new experiments, and nothing in the consolidated
review requires hardware — which means every concern raised is addressable.

## Required for acceptance

| # | Concern | From | Addressable without new experiments |
|---|---|---|---|
| 1 | Demote Theorem 1; promote Propositions 3–6, especially the overflow condition | R1, R3 | yes |
| 2 | Bound $C_{\text{own}}$ by arithmetic from the I²C clock rate, or say why not | R1 | yes |
| 3 | Demonstrate core-1 exclusivity from the build rather than asserting it | R1 | yes |
| 4 | Add a compromised-broker row to the threat model and state the trust assumption | R2 | yes |
| 5 | State in the manuscript that the broker result is a conformance check, not a deployment evaluation | R2 | yes |
| 6 | Say in the discussion that a counter-bound MAC is unsound without key management | R2 | yes |
| 7 | Justify the 128-bit tag length analytically | R2 | yes |
| 8 | Restructure §11 around the instrument and its validation rather than the counts | R3 | yes |
| 9 | State formal coverage quantitatively | R3 | yes |
| 10 | Justify `MaxCtr = 4` by data independence | R3 | yes |
| 11 | Say which parts of the infrastructure still have no control | R3 | yes |
| 12 | Commit the raw campaign records | R2, R3 | yes |
| 13 | Reclassify H2 as the hypothesis of the future study | R3 | yes |
| 14 | Fix the 79.8/79.9 inconsistency | R3 | yes |

## Editor's note on positioning

The authors should decide whether this is an embedded-systems paper or a security-and-methodology
paper, because the review above splits cleanly along that line. On the evidence presented it is the
latter: the measured results are about authorisation and the formal results are about specification
quality, while the timing dimension contributes a decomposition and an unexecuted protocol. If
submitted to an embedded venue, the authors should expect R1's review and should pre-empt it.
