# Two versions, and which one to submit

Priority 4 asked for two honest framings. They are not two presentations of the same paper:
they make different claims, and only one of them can be made with the evidence that exists
today.

**Only Version B is submittable now.** Version A requires a measurement nobody has taken.

---

## Version A — the hardware-timing paper

**Title:** keep the current one, *Isolating the Safety Function on a Single-Chip Wi-Fi SoC*,
**only if conditions A–C are measured.** Otherwise the title names a property the paper does
not establish.

**Claim.** That pinning the safety task to the application core, combined with bounded
non-blocking queues and a zero-timeout status snapshot, keeps sensor-to-siren latency invariant
under 802.11 management-frame load — and that the invariance is measured, not argued.

**Evidence it would rest on.**

| | Status |
|---|---|
| Physical latency under conditions A, B, C | **Does not exist.** Protocol, instrument firmware, wiring, collection and analysis scripts and pre-registered statistics are written and committed |
| Response-time decomposition reducing four unknowns to one | Done |
| TLA+ isolation model, no fairness on the network task | Done |
| 9,600 adversarial trials, 3,000,000 fuzz iterations | Done |

**What it adds over Behnke et al. (IPCCC 2020).** Behnke measured 2.15–3.8 % cycle loss under
IP load with cross-core separation. Version A would differ on three points: management-frame
load is handled below the IP stack and may behave differently; this evaluates a *mitigation*
rather than characterising the problem; and the isolation argument is established formally as
well as empirically. The first of those is currently a hypothesis, and the measurement is what
would turn it into a finding.

**Limitations that would remain.** Single platform, single application, single vendor SDK. No
single-core variant, no ESP32-S3 or C3. No deployment data. The security results would stay as
they are.

**Scope fit.** Journal of Systems Architecture is a good fit for this version, and so are
*IEEE Embedded Systems Letters* (shorter) and *ACM Transactions on Embedded Computing Systems*.
This is the version whose readership is the one that measures things.

**Cost to produce.** Two ESP32 boards and a logic probe, and a few days of someone's time.
Nothing else is missing.

---

## Version B — the verification-assumptions paper

**Proposed title:** *Unverified Assumptions in Embedded Safety Firmware: Configuration
Defects, a Vacuous Invariant, and What Cheap Falsification Finds*. Several variants are
plausible; what matters is that the title names assumptions and falsification, not timing.

**Claim.** That a security property asserted in build configuration, and a timing property
asserted in design, are both unverified claims, and that each can be falsified by a method
costing far less than the system it checks. Three instances support it, all found in the
authors' own work:

1. A compile guard that accepted TLS plus a broker login as authority for unauthenticated
   remote disarm. Found by ablation. Cost: a safety property, with the alarm firing in 16.7 %
   of trials against 100 % for a matched control.
2. An unbounded drain in the safety path. Found by response-time decomposition, after 120 host
   checks, 3,000,000 fuzz iterations, 9,600 adversarial trials and exhaustive model checking
   had all passed.
3. A vacuous invariant in the shipped TLA+ specification: `NoUnauthRemoteDisarm` could not
   fail, because the specification *assumed* the refusal that the guard got wrong. A model
   embedding the assumption under test cannot test it.

**Evidence it rests on — all of which exists.**

| | Status |
|---|---|
| Twelve-configuration ablation, 3,600 trials, identical seeds | Done, reproduces byte-identically |
| Eight access-control scenarios against a real Mosquitto broker | Done, testbed measurement |
| Corpus study of 135 open-source projects | Done, and **negative**: the guard pattern was not found |
| Three TLC configurations, one required to fail | Done |
| Trace conformance, 19,529 transitions, none disallowed | Done |
| Metamorphic and differential harness tests | Done |
| RFC 4231 known-answer tests for the HMAC primitive | Done |

**What it adds.** Not a mechanism. The contribution is evidence and method: the controlled
separation of availability, integrity and the safety function across twelve configurations; the
compromise-indexed comparison showing that broker authorization and application-layer
authentication fail under *different* compromises and that layering does not close the set; the
owner-lockout result, in which the replay counter that defeats capture-and-replay denies the
legitimate owner service under key compromise; and a worked account of three self-inflicted
defects that every other technique applied here missed.

**Limitations that would remain, and must be stated.**

- The guard finding does **not** generalise on the evidence collected. Zero hits in 135
  projects. It is a single-system case study, and the corpus is cited for that restraint rather
  than against it.
- The corpus is biased: GitHub-only, English queries, a three-star floor that removes 437
  repositories and plausibly removes the least careful ones.
- The broker testbed is loopback with a private CA. It validates access-control policy, not
  networking, and does not cover wildcards, bridged brokers or client certificates.
- Trace conformance is one-directional and covers control state only. It is not a refinement
  proof.
- No physical timing measurement, and under this framing none is claimed.

**Scope fit.** The timing claim is gone, so JSA is a weaker fit than it is for Version A,
though not an impossible one: JSA publishes embedded software design and this is a paper about
how embedded firmware goes wrong. Better fits are venues that value method and negative
results: *Empirical Software Engineering*, *Journal of Systems and Software*, *IEEE Transactions
on Dependable and Secure Computing* (a stretch without a stronger security contribution), or a
software-engineering conference with an artifact track. A short-paper venue such as *IEEE
Embedded Systems Letters* suits instance 1 plus its ablation on its own.

**Cost to produce.** A retitle, a reframed introduction and abstract, and demotion of the
timing material to a section on what remains unverified. Days, not weeks. No new experiments.

---

## Recommendation

Submit **Version B** unless someone commits to the measurement.

The reason is not that Version B is better. Version A is the stronger paper, because a measured
timing-invariance result on this platform would be a real contribution and the security work
would ride along with it. The reason is that Version A cannot be submitted without the
measurement, and submitting the current framing — which is Version A minus its central
evidence — to a journal of this standing invites exactly the rejection two of three simulated
reviewers wrote.

A middle course is available and worth naming: produce Version B now, submit it, and keep the
hardware protocol published. If another laboratory performs conditions A–C using the committed
framework, that becomes Version A as a follow-up with a measured result, which is a cleaner
story than one paper carrying an unmeasured claim.

## On the quartile

**Unverified, and the repeated "Q2" assumption should be dropped until checked.** SCImago and
the ACM Digital Library are both behind bot verification, which was not circumvented, so no
quartile is asserted here for any venue. What is verified, from Elsevier's own pages, is that
the Journal of Systems Architecture reports CiteScore 9.1 and Impact Factor 5.3. Those figures
are more consistent with Q1 than Q2 in its categories, which would raise the bar rather than
lower it. Opening scimagojr.com in an ordinary browser, or checking Scopus or JCR through the
institution, settles it in about two minutes, and it should be settled before a venue is chosen
— it bears directly on whether Version B is submitted to JSA or elsewhere.
