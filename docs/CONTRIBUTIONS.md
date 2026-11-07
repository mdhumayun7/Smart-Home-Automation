# The eight stated contributions, assessed independently

Written in response to a request to classify each contribution and check it against the
literature rather than assert it. The conclusion is that **the manuscript should not claim
eight contributions**. Three survive as substantive, three are real but ordinary engineering or
reproducibility work, and two are findings rather than contributions. One central contribution
is identified and the abstract and introduction are restructured around it.

Classification scheme, as requested: **OSC** original scientific contribution, **ENG**
engineering contribution, **EXP** experimental finding, **FV** formal verification
contribution, **REP** reproducibility contribution.

---

## C1. A deployable isolation design, formally verified

**Class: ENG + FV. Not an original scientific contribution.**

Core pinning, bounded queues and zero-timeout locking are all standard real-time practice. The
TLA+ model is a genuine formal artifact, and verifying it with no fairness assumption on the
network task is the right methodological choice, but the property verified is logical
isolation, not the timing invariance the paper's title promises. Behnke et al. (IPCCC 2020)
already measured task lateness on an ESP32 under on-chip IP load with cross-core separation.

**What survives:** the combination is assembled and verified rather than asserted, and the
specification is mutation-tested so the verified properties are shown non-vacuous. That is
good practice, not novelty.

## C2. An ablation separating availability, integrity and the safety function

**Class: EXP. Strong.**

No individual mechanism in the ablation is new. What is new is the controlled separation: one
adversary, one system, one seed set, eleven configurations, showing that a rate limiter buys
integrity nothing while costing 41 % of operator commands, a static token does the reverse, and
only a counter-bound MAC does both. Practitioners conflate these routinely. Searched against
the MQTT security literature through 6 November 2026, we found no comparable controlled
separation on a single artifact.

## C3. A configuration-logic defect found by that ablation, and its removal

**Class: EXP. The strongest single result.**

The underlying principle is textbook and the attack class is published (Alsabbagh et al., CSNet
2024), so the *vulnerability* is not new and the manuscript says so. What is not in the
literature is the observation that a compile-time guard can encode an unsound security
inference, pass review without warning, emit no diagnostic, and convert that known principle
into the loss of a **safety** property. The defect is in a build condition, not a runtime check,
which is why no amount of testing the running system would find it — and it was found by
ablation, which is a reusable method rather than a one-off.

## C4. A compromise-indexed comparison of broker authorization against application-layer authentication

**Class: EXP, now partly testbed-validated. Strong.**

Shows that neither control dominates: an ACL contains a compromised device credential and fails
against a compromised controller; a MAC does the reverse; a shared credential collapses the ACL
entirely; only the layered configuration survives every case. Validated against a real
Mosquitto broker, which agreed with the model in all eight scenarios. The individual facts are
each unsurprising to a specialist; the indexed comparison, with measurements, is not something
we found stated elsewhere.

Includes the **owner-lockout** result, which is a genuine negative finding: under key
compromise the monotonic replay counter denies the legitimate owner service entirely (0 of
1250 operator commands admitted). We have not seen this trade-off reported for
counter-based replay protection in embedded command paths.

## C5. A parameter sensitivity analysis that corrected our own design

**Class: EXP. Modest but honest.**

The sweep found our own deauthentication threshold fired in 79.9 % of benign ten-minute runs
and we changed it. Valuable as evidence of method; the result itself is specific to this
detector and rests on a synthetic arrival model, which bounds how much it can claim.

## C6. A complete, reproducible artifact

**Class: REP. Real but crowded.**

Artifact evaluation is mature and seeded harnesses are common. Three things here are less
common and worth keeping: the evidence taxonomy that labels every number by category; the
refusal to report any physical quantity that was not measured; and the documented record of
four harness defects that produced plausible but wrong numbers, two of which flattered the
intended conclusion.

## C7. A response-time decomposition bounding three of four interference terms

**Class: ENG + EXP. Underrated in the current manuscript.**

Response-time analysis is classical and the decomposition itself is standard. But it **found a
real defect that nothing else did**: an unbounded drain that survived 120 host checks,
3,000,000 fuzz iterations, 9,300 adversarial trials and exhaustive model checking. That is the
single most persuasive argument in the paper for doing the analysis at all, and it is currently
buried.

## C8. A complete, independently executable validation framework

**Class: REP. Necessary, not a contribution.**

This exists because the central claim is unmeasured. A framework for an experiment nobody has
run is scaffolding, and presenting it as a contribution invites a reviewer to ask why the
experiment was not simply performed. It belongs in the paper — it is the honest response to the
gap — but not in a contributions list.

---

## Verdict

| | Keep as a contribution | Class |
|---|---|---|
| C1 | fold into C2/C3 as system description | ENG, FV |
| C2 | **yes** | EXP |
| C3 | **yes, lead with it** | EXP |
| C4 | **yes** | EXP |
| C5 | merge into C2 | EXP |
| C6 | **yes, reduced** | REP |
| C7 | **yes, promoted** | ENG, EXP |
| C8 | move out of the list into Limitations | REP |

**Eight becomes five.** There is no original scientific contribution in the strict sense, and
the manuscript should not imply otherwise. There is no new mechanism, no new attack, no new
protocol and no new formalism.

## The central contribution

> **Security properties asserted in build configuration, and timing properties asserted in
> design, are both unverified claims — and each can be falsified by a method that costs far
> less than the system it checks.**

Two independent instances support it, and they are the paper's two best results:

1. A compile-time guard encoded an unsound security inference. An **ablation with a fair
   baseline** falsified it, and the cost was a safety property, not merely a security one.
2. A command drain was assumed bounded. A **response-time decomposition** falsified it, after
   testing, fuzzing, model checking and 9,300 adversarial trials had all passed.

Neither method is novel. The claim is that applying them to the *assumptions* rather than to
the running system is what caught two defects that every other technique in the project missed,
and that this is a transferable practice for safety-critical embedded work.

This framing is also the honest one for the paper's weakest point: the headline timing claim is
itself an unverified assertion, and the paper says so and supplies the protocol to settle it.
A paper arguing that unverified assertions should be falsified cheaply is consistent when it
admits which of its own remain unverified.
