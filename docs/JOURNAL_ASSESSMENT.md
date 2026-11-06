# Venue assessment and realistic reviewer outlook

Written after the corrected 3,300-trial campaign and the access-control arms. It supersedes the
venue discussion in `JOURNAL_TARGETS.md` where the two disagree.

The conclusion, stated first: **this manuscript is not ready to submit to the Journal of Systems
Architecture, and the reason is not formatting or polish.** It is that the paper's headline
claim is a physical timing property that no one has measured, and JSA's readership is precisely
the one that will notice. A realistic outcome at JSA today is reject or major revision with a
request for hardware. The software work is strong and honest; it is not a substitute for the
measurement.

---

## 1. What the target journal actually is

| Field | Value | Source |
|---|---|---|
| Title | Journal of Systems Architecture: Embedded Software Design | Elsevier journal page |
| Publisher | Elsevier | Elsevier journal page |
| ISSN | 1383-7621 (print), 1873-6165 (online) | Elsevier journal page |
| CiteScore | 9.1 | Elsevier "Insights" page |
| Impact Factor | 5.3 | Elsevier "Insights" page |
| Quartile | **Not verified.** See below | — |

**On the quartile.** This project has repeatedly described JSA as a "Q2 journal". That
assumption should be dropped until it is checked, and the evidence available points the other
way: an Impact Factor of 5.3 and a CiteScore of 9.1 are high for the Hardware and Architecture
and Software categories, and a journal with those metrics is more likely to sit in **Q1** than
Q2. The authoritative source is Scopus/SJR; both the SCImago page and the ACM Digital Library
were behind bot verification when this was checked, and that was not circumvented, so **the
quartile is recorded here as unverified rather than guessed**. It should be read directly from
Scopus or the JCR before any submission decision.

This matters practically. If JSA is Q1, the bar for a paper whose central claim is unmeasured is
higher than this project has been assuming, not lower.

## 2. Scope fit

JSA's stated scope covers embedded systems and software from microarchitecture through system
software, explicitly including real-time systems and operating systems, and explicitly
de-emphasising hardware design. That fits this work well: the subject is task isolation and
command authorization in embedded firmware, not circuit design.

Two scope statements cut against us, and both are quoted from the journal's own page:

- *"While JSA does not focus on hardware design"* — helpful, since our contribution is software
  structure, not silicon.
- *"Case studies are welcome, but they must contribute more than a design for a particular piece
  of software."* — **this is the sentence to worry about.** As assessed in
  `SECURITY_ANALYSIS.md` §7a, none of the five candidate contributions is a novel mechanism. The
  paper is a system-and-evidence paper about one artifact. The reviewer question will be
  precisely whether it contributes more than a design for a particular piece of software.

There is one favourable precedent: JSA published Behnke et al. (2023), whose headline mechanism
was simulated and never built. That establishes that JSA accepts simulation-based evaluation.
It does **not** establish that JSA accepts an unmeasured claim about physical timing, because
Behnke's simulated quantity *was* the paper's contribution, whereas our unmeasured quantity is
the one the title promises.

## 3. Reviewer assessment, written as a reviewer would

**Likely recommendation at JSA as the manuscript stands: major revision, trending reject.**

What a competent reviewer will credit:

- The evidence taxonomy and the refusal to report any unmeasured physical quantity. This is
  unusual and will be read as a sign of care.
- The TLA+ isolation model verified with no fairness assumption on the network task. This is a
  real formal result, not decoration.
- The response-time decomposition, and particularly that it exposed an unbounded drain that
  3,000,000 fuzz iterations, 7,800 adversarial trials and model checking all missed. That is the
  single most persuasive argument in the paper for doing the analysis at all.
- The eleven-arm ablation, including the arms that undercut the authors' own mechanism. The
  owner-lockout result especially: a paper that reports its own mechanism creating a
  denial-of-service channel is a paper being run honestly.
- The documented record of four harness defects, two of which flattered the intended conclusion.

What the same reviewer will object to, in order of severity:

1. **The headline claim is untested.** The title and abstract are about isolating a safety
   function on a single-chip Wi-Fi SoC; the property that matters is physical timing
   invariance; no physical measurement exists. Everything else in the paper is, from the
   reviewer's point of view, supporting material for a claim that has not been evaluated.
2. **No contribution is a new mechanism**, and the paper now says so itself. A reviewer who
   accepts the authors' own §7a assessment has to ask what the paper is *for*. The answer —
   careful evidence about one artifact, including negative results — is respectable but thin for
   a journal of this standing.
3. **The access-control arms are model-based.** No Mosquitto instance was used. This is a
   cheap gap to close and a reviewer will say so: validating against a real broker needs no
   special hardware, only a container.
4. **Single platform, single application, no deployment.** Honestly scoped in the paper, but it
   still bounds the contribution.
5. **Author-is-evaluator.** No blinding, and the harness and firmware share an author. The paper
   raises this itself, which helps, but does not remove it.

## 4. What would change the recommendation

In descending order of effect per unit of work:

| Action | Effect | Cost |
|---|---|---|
| Run hardware conditions A–C | Converts the central claim from asserted to measured. **This is the only change that addresses objection 1.** | Two ESP32 boards, a logic probe, a few days of someone's time |
| Validate the ACL arms against a real Mosquitto broker with per-client ACLs | Removes objection 3 entirely and upgrades gate Q7 | A container and a day; no hardware |
| Verify the Scopus quartile and read the Guide for Authors | Decides whether JSA is the right target at all | An hour |
| Enable flash encryption and secure boot, then re-run the compromise arms | Addresses the weakest assumption in the threat model | Hardware, and non-trivial |

Nothing on this list is cosmetic, and no amount of rewriting substitutes for the first row.

## 5. Alternative venues, if the hardware measurement will not happen

If the physical measurement will genuinely not be performed by anyone, JSA is the wrong target
and the honest move is to reframe rather than to submit and hope. Options, with the reframing
each would require:

- **Reframe as a security and methodology paper** and drop the timing claim from the title and
  abstract entirely. The paper then stands on the compile-guard defect, the eleven-arm
  compromise-indexed ablation, and the methodology. That is a coherent paper, and it is
  submittable without hardware. It is also a different paper from the one currently written.
- **A shorter letters venue** (for example IEEE Embedded Systems Letters, already assessed in
  `Q2_GATE.md` §3) suits a single sharp result such as the compile-guard finding plus its
  ablation, at a page count that does not invite the question of what else was measured.
- **An artifact or reproducibility track** would value the evidence taxonomy, the seeded
  reproduction and the defect record more than a general journal would.

The recommendation is the first option if the hardware will not happen, and JSA with the
hardware if it will. Submitting the current framing to JSA without the measurement is the one
course with a poor expected outcome.

## 6. Formatting status

Not yet done, and deliberately deferred until the venue is settled, because reformatting for the
wrong journal is wasted work.

- The manuscript compiles as a 25-page standalone article with no undefined references and no
  overfull boxes.
- Its header documents a one-line switch to `elsarticle` (JSA) or `IEEEtran`.
- **The JSA Guide for Authors has not been read.** Elsevier's journal page did not expose
  article-type definitions or length limits in the fetched content. Submission requirements —
  article types, structured abstract rules, reference style, declaration sections, data and
  code availability statements — must be read from the Guide for Authors before submission.
  This is recorded as outstanding rather than assumed satisfied.
