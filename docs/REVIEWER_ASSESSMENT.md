# Three-reviewer assessment and editorial decision

Simulated peer review of the 29-page manuscript at commit `b70f93b`, written against the
standards of the Journal of Systems Architecture. Each reviewer is written as an adversarial
specialist, not a friendly one, because a review that only finds what the authors already
admit is worthless.

**Consolidated decision is in section 4. It is major revision, and the required revision is an
experiment, not an edit.**

---

## Reviewer 1 — embedded and real-time systems

### Major concerns

**R1.1 The central timing claim is unmeasured, and it is in the title.** The paper is called
*Isolating the Safety Function on a Single-Chip Wi-Fi SoC*. The property that word "isolating"
denotes, for this readership, is timing invariance under radio load. The authors establish
logical isolation and are explicit that they have not measured timing. I credit the honesty,
but the title and framing still promise what the evidence does not deliver. For this journal
that is the whole question, not a caveat.

**R1.2 Behnke et al. (IPCCC 2020) already measured what this paper asserts.** Prior work
measured 2.15–3.8\% cycle loss on an ESP32 under IP load with cross-core separation. The
authors distinguish their work on three grounds: management-frame load rather than IP load,
mitigation rather than characterisation, and formal rather than empirical argument. The first
two are real but narrow, and the third is a different kind of claim, not a stronger one. The
paper does not show that management-frame load behaves differently; it hypothesises it.

**R1.3 The response-time decomposition proves less than its presentation suggests.** $B = 0$
follows from a zero-timeout acquisition, which is correct but close to definitional: a task
that never waits cannot be blocked. The genuinely hard terms, $I_{\mathrm{isr}}$ and
$I_{\mathrm{mem}}$, are precisely the ones collapsed into an unmeasured composite. The
contribution is reducing four unknowns to one, which is useful, but the remaining unknown is
the entire research question.

### Minor concerns

- Single platform, single application, single vendor SDK. No single-core variant, no ESP32-S3
  or C3, no alternative RTOS configuration.
- The 151 ms host latency figure is an artifact of a logical clock and should be labelled even
  more loudly than it is; a hurried reader may mistake it for a measurement.
- The drain fix (`CMD_DRAIN_PER_PASS = 4`) is tied to the queue capacity by a comment rather
  than by a static assertion.

### Unsupported claims

- That pinning plus queue discipline is an *adequate* mitigation. Adequacy is a timing claim.
- That management-frame load is the interesting case. Plausible, untested.

### Missing experiments

Hardware conditions A–C. Two boards and a logic probe. The protocol is already written.

### Required revisions

1. Perform conditions A–C, or retitle and reframe the paper so the timing claim is not the
   headline.
2. Add a static assertion binding the drain bound to the queue capacity.

### Recommendation: **major revision**, bordering reject if the measurement will not be done.

---

## Reviewer 2 — IoT security and MQTT authentication

### Major concerns

**R2.1 Nothing here is a new security mechanism, and the paper says so.** HMAC-authenticated
MQTT commands on an ESP32 are published prior art (Amirkhanova et al., 2026), the
rogue-authenticated-client attack is published (Alsabbagh et al., 2024), and end-to-end payload
authentication above an untrusted broker is an established class. I agree with the authors'
own assessment in §7a of their security analysis. The question this raises for the editor is
whether what remains is enough for this journal.

**R2.2 The compile-guard finding is the real contribution, and it is a finding about one
codebase.** The defect is in the authors' own firmware. It is a good finding, honestly
reported, and the generalisation offered — that build conditions encode unverified security
arguments — is believable. But it rests on $n = 1$. No survey of other embedded projects for
similar guards, no static-analysis rule that would catch the class, no evidence that the
pattern occurs elsewhere. A single self-reported defect is an anecdote until it is shown to
generalise.

**R2.3 The threat model boundary around scenario E is stated but strains.** The authors
correctly separate remote adversaries (A–D) from the physical-access adversary (E). Yet the
headline claim for the layered configuration — that it survives a flash dump — lives entirely
in E. The paper is careful about this, but the strongest positive result for the proposed
design sits outside the primary threat model, and that should be said more plainly than it is.

### Minor concerns

- The owner-lockout result is excellent and underplayed. It deserves more than a subsection; it
  is a genuine design trade-off for counter-based replay protection in embedded command paths,
  and I have not seen it reported.
- The broker validation is loopback-only with a private CA. Adequate for ACL semantics, and the
  authors say so, but it is not a network evaluation.
- The key is symmetric and unrotatable, and flash encryption is not enabled. The authors
  document this; a deployed product could not.

### Unsupported claims

None found. The security claims are scoped more carefully than is usual, and the paper
repeatedly declines to claim things the evidence would not carry. I checked the four claims I
expected to be overstated and all four were already qualified.

### Missing experiments

Evidence that the compile-guard pattern occurs outside this codebase: a survey of open-source
embedded MQTT projects, or a static-analysis rule run over a corpus. This would convert the
strongest contribution from an anecdote into a result.

### Required revisions

1. Generalise the compile-guard finding beyond $n = 1$, or restate its scope as a case study.
2. Promote the owner-lockout result.
3. State plainly that the layered configuration's advantage is demonstrated only under E.

### Recommendation: **major revision.** The security content is sound and honest; its weight is the issue.

---

## Reviewer 3 — formal verification and experimental methodology

### Major concerns

**R3.1 The authors shipped a vacuous invariant, and I am inclined to treat this as a point in
their favour.** §VI reports that `NoUnauthRemoteDisarm` could not fail in the specification
that ran in CI, because `badDisarm` was never assigned. The mutation test for that property had
been performed on a hand-edited local copy. This is a serious methodological failure, disclosed
by the authors, diagnosed correctly, and fixed with a parameterised configuration in which the
defective build is *required* to produce a counterexample. I have reviewed many papers claiming
mutation testing; this is the first I recall that found its own mutation testing had not been
applied to the artefact it shipped. The disclosure strengthens the paper's thesis rather than
undermining it.

**R3.2 The abstraction gap is the usual one and is not closed.** The TLA+ model is
hand-written, and nothing mechanically relates it to the firmware. There is no refinement
proof, no trace conformance, no extraction. The state names match and the transitions
correspond by inspection, which is what most papers do, but it means the verification applies
to the model and the correspondence remains an argument.

**R3.3 Four harness defects is a lot, and the authors are right that three produced plausible
numbers.** I want to be clear that reporting them is correct and unusual. The concern is what
it implies about defects not yet found. Two of the four were caught only because results were
broken out by attack rate rather than aggregated; that is luck as much as method. No systematic
validation of the harness exists — no metamorphic tests, no differential testing against an
independent implementation.

### Minor concerns

- The ablation's zero-variance latency is correctly reported as meaningless; good.
- Wilson intervals and Fisher exact tests are appropriate and correctly computed. I recomputed
  the headline interval and it matches.
- Byte-identical reproduction from committed seeds is verified, which is more than most
  artifacts offer.
- 180 sensitivity grid cells rest on a synthetic Poisson arrival model, acknowledged as an
  assumption. Fine, but it bounds the detector result tightly.

### Unsupported claims

- "Mutation-tested" in the abstract and contributions, as a blanket statement, is now
  defensible only because the paper corrects it in §VI. Ensure no remaining sentence implies
  all properties were non-vacuous in the shipped artefact before the fix.

### Missing experiments

Trace conformance between the TLA+ model and the firmware, even at a coarse level: generate
traces from the host harness and check them against the specification.

### Required revisions

1. Add metamorphic or differential validation of the ablation harness, or state explicitly that
   harness correctness rests on inspection and the four documented corrections.
2. Audit every "mutation-tested" phrase for consistency with §VI.

### Recommendation: **minor revision.** The methodology is the strongest part of this paper.

---

## 4. Consolidated editorial decision

### **Major revision.**

Two reviewers of three require an experiment rather than an edit, and they require different
experiments. The decision is not close.

**What the reviewers agree on.** The work is honest to an unusual degree; the methodology is
strong; the security analysis is correctly scoped; nothing material is overstated. Reviewer 2
looked for overstatement specifically and found none. The paper's weaknesses are structural,
not presentational, and no amount of rewriting addresses them.

**The two blocking items.**

1. **The timing measurement (R1.1, R1.2).** The headline claim is unverified and this is a
   journal whose readers measure things. Either perform hardware conditions A–C, or retitle and
   reframe so that the paper's claim is what it actually establishes.
2. **Generalising the compile-guard finding (R2.2).** The strongest contribution rests on one
   self-reported defect. A survey of open-source embedded projects, or a static-analysis rule
   over a corpus, would convert it into a result. This needs no hardware and is the better
   investment if the boards will not be bought.

**The non-blocking but valuable items.** Promote the owner-lockout result (R2.1 minor);
harness validation beyond inspection (R3.1); trace conformance (R3.2); a static assertion on
the drain bound (R1.3 minor).

**An observation for the editor.** This paper has an unusual property: three of its findings
are defects in its own work, disclosed by the authors — a compile guard that was unsound, a
vacuous invariant in the shipped specification, and four harness defects of which two flattered
the intended conclusion. A reviewer's instinct is to read self-reported defects as weakness.
Here they are the evidence for the paper's thesis, which is that asserted properties go
unchecked and can be falsified cheaply. The paper would be weaker, not stronger, without them.

That thesis is also the paper's best route forward. If the hardware will not be bought, the
honest move is not to submit the current framing and hope, but to retitle around the thesis the
evidence supports and pursue R2.2. That is a publishable paper. The current framing, submitted
to this journal without the measurement, is not.
