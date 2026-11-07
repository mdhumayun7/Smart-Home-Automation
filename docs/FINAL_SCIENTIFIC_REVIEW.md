# Final scientific and technical review

Phase 6 of the finalization task. 7 November 2026.

Written as a reviewer would write it, against the manuscript as built, with every number
recomputed from the raw records rather than read from an earlier report. Two defects were
found and fixed during the review; both are recorded in §8.

---

## Verdict in one paragraph

The paper is scientifically sound and unusually disciplined about what its evidence does and
does not support. Its central claim — that assumptions encoded in build configuration, in
design and in a specification are unverified claims, and that each can be falsified cheaply —
is supported by three concrete defects the authors found in their own work, each by a
different method, each after other techniques had passed. Every statistic recomputes exactly.
The main weakness is unchanged and openly stated: the paper's own headline timing question is
unmeasured, and the attempt to generalise the central finding returned zero hits. Neither is
concealed. A reviewer's decision will turn on whether a rigorously executed single-artefact
case study, with a negative generalisation result, clears the venue's contribution bar — not
on whether the work is correct.

---

## A. Security claims

### A1. TLS versus application-layer authentication — **sound**

The claim is that broker credentials decide *admission* and only the command key decides
*authority*, because the broker terminates TLS and re-originates every message, so an arriving
command carries no evidence of its publisher.

This is correct as a matter of protocol, it is stated as a known principle rather than a
discovery, and the manuscript says so explicitly, citing Alsabbagh et al. (CSNet 2024). The
contribution claimed is narrower and defensible: that a *compile-time guard* can encode the
unsound inference, emit no diagnostic, survive review, and cost a **safety** property.

**No overclaim.** The paper nowhere says TLS is broken.

### A2. Broker ACL versus HMAC — **sound, and the strongest result**

Neither dominates. Measured, recomputed here:

| Control | Compromise | Alarm | Operator admitted |
|---|---|---|---|
| TLS + per-client ACL | device credential | 300/300 | 1250/1250 |
| HMAC + counter | any broker credential | 300/300 | 1250/1250 |
| TLS + per-client ACL | controller credential | 50/300 | 1250/1250 |
| HMAC + counter | controller credential + key | 50/300 | **0/1250** |

The ACL contains a compromised device credential that the MAC does not, because the key sits
in the same flash image; the MAC contains a compromised controller credential that the ACL
cannot, because the ACL must permit that identity to publish. The claim that neither dominates
is exactly what the data shows.

### A3–A6. The four compromise classes — **all verified against raw records**

All nine cells of the credential table were recomputed from `ablation.jsonl`, including the
disarm column that no figure plots: **0 mismatches**. The decisive pair in the real-broker run
reproduces too: E (device credential + key) is denied, E′ (controller credential + the *same*
valid signature) is delivered — establishing that what stops E is the access-control list, not
the signature.

### A7. Owner lockout under key compromise — **sound, and properly flagged as unanticipated**

Under key compromise the adversary signs with a counter far above the operator's; the device
persists it; every subsequent legitimate command is then rejected as a replay. Recomputed:
**0 of 1,250** operator commands admitted in both `hmac_keyleaked` and
`acl_hmac_controllerdump`.

This is a genuine negative result about a defence the authors themselves chose, it is reported
as unanticipated, and it is not buried.

### A8. Threat-model boundaries — **was defective, now fixed**

The primary model is adversary A, remote, radio range only, and the paper states that every
claim about the design is a claim against A unless said otherwise. That discipline is right.

**Defect found:** the table listed A–E, but **E′ — the compromised controller host — was
absent**, despite being the single most important failure in the paper and being discussed in
six places in the text. Worse, E (device flash dump) requires **physical** access while E′
requires **none**, and that distinction was not drawn where a reader would look for it. The
layered configuration survives the *physically expensive* scenario and falls to the *cheap*
one, which is the whole point, and the threat model did not say so.

**Fixed.** E′ is now a row with its access class marked remote, the caption states that the
*Access* column is load-bearing, and a paragraph before the table separates E from E′
explicitly.

---

## B. Formal verification

### B1–B2. TLA+ specification and isolation assumptions — **sound**

Two specifications. `Isolation` is checked with the network task granted **no fairness
assumption**, which is the right methodological choice: it means the result holds even if the
network task never runs, rather than relying on a scheduler guarantee. State counts
reproduced on a clean container: `AlarmFSM` 166 generated / **25 distinct**; `Isolation` 2,686
generated / **660 distinct**. Both match the manuscript.

The manuscript is careful that what is verified is *logical* isolation, and says so in the
abstract, in §4, in the results and in the conclusion.

### B3. Vacuous-invariant disclosure — **sound, and to the paper's credit**

`NoUnauthRemoteDisarm` was **vacuous in the specification that shipped and was checked in
CI**, because the specification assumed the refusal instead of deriving it — the same unsound
inference the compile guard made. The authors found this in their own work and disclosed it in
a section of its own, in the abstract, and in the title.

A model checker reports no violation for a vacuous specification exactly as readily as for a
sound one. Most papers would have quietly fixed this. Disclosing it is the correct scientific
behaviour and is, in a paper about unverified assumptions, the most on-point result in it.

### B4–B6. Mutation testing, negative controls, TLC configurations — **sound**

Three configurations, re-run here:

```
PASS AlarmFSM
PASS Isolation
PASS AlarmFSM_unsafe: TLC reports the expected NoUnauthRemoteDisarm violation
```

The third is the important one: `AllowUnauthDisarm` is a CONSTANT, the defective configuration
sets it TRUE, and the runner **requires TLC to fail**. A run in which it passes means the
invariant has gone vacuous again, so the regression cannot recur silently.

Trace conformance: **19,529 transitions** across three modes, 0 disallowed, with a negative
control asserting that a forbidden `Disarmed → Alarm` transition *is* rejected. The transition
relation is parsed out of `AlarmFSM.tla` rather than restated, so the checker cannot drift
from the specification it checks. Without the negative control the 19,529 would be worthless;
with it, it is evidence.

---

## C. Response-time analysis

### C1–C4. Decomposition, the unbounded drain, blocking term — **sound, and under-sold**

The decomposition reduces four interference terms to one composite hardware quantity and names
what a measurement must isolate. The blocking term is identically zero by construction because
the safety loop takes the status mutex with timeout 0 and gives up rather than wait — verified
in the firmware at `xSemaphoreTake(statusMutex, 0)`, against the network task's
`pdMS_TO_TICKS(10)`.

**The analysis found a real defect nothing else did.** The command drain was an unbounded
`while`, giving the safety loop no static bound on its own execution time: core 0 can enqueue
while core 1 dequeues, and in the default build enqueueing costs only a parse. The loop would
still terminate, but by a probabilistic argument about relative costs — not acceptable in the
one path the whole design exists to protect. This survived 120 host checks, 3,000,000 fuzz
iterations, 9,600 adversarial trials and exhaustive model checking.

The repair is bounded and the bound is asserted at compile time:

```c
static constexpr int CMD_DRAIN_PER_PASS = CMD_Q_LEN;
static_assert(CMD_DRAIN_PER_PASS == CMD_Q_LEN, …);
```

**Reviewer note:** this is the second-strongest result in the paper and it is still the least
prominent. It is the cleanest possible demonstration of the central claim — every empirical
technique passed, and an analytical one found the defect. Consider promoting it in the
abstract.

### C5–C6. Residual interference and physical limits — **correctly scoped**

One composite hardware term remains, and the paper declines to put a number on it. **No
measured latency appears anywhere**: a targeted search for measured-timing language found
nothing, and the only timing numbers in the paper are Behnke et al.'s, attributed to them in
the introduction and related work.

---

## D. Experimental evidence — every count recomputed

Run against the raw artefacts during this review:

```
E1/E2 campaign trials   : 6000          (3,000 baseline + 3,000 hardened, 6 rates)
E3 ablation trials      : 3600 in 12 configurations   (300 per mode, exactly)
total adversarial       : 9600
E4 fuzz iterations      : 3000000
E5 sensitivity cells    : 180
E6 broker scenarios     : 8
corpus projects         : 135
corpus rule-1 hits      : 0        | rule-2 flagged: 18
manual verdicts         : 9 confirmed / 9 false positive
trace transitions       : 19529, 0 disallowed, negative control rejects
```

Statistics:

| Claim | Recomputed | Verdict |
|---|---|---|
| Leaked-credential alarm activation 16.7 % | 50/300 = 16.67 % | exact |
| 95 % Wilson CI [12.9 %, 21.3 %] | [12.9, 21.3] | exact |
| Rate limiter admits 59.0 % | 737/1250 = 59.0 % | exact |
| Fisher exact, one-sided, p = 3.5×10⁻¹⁸⁴ | 3.53×10⁻¹⁸⁴ | exact |
| Fisher exact, one-sided, p = 9.8×10⁻¹¹⁹ | 9.83×10⁻¹¹⁹ | exact |
| Adversary disarms 246/300 | 246 | exact |
| Owner lockout 0/1250 | 0/1250 | exact |
| Detector default fired in 79.9 % of benign runs | 1597/2000 = 79.85 % | exact |
| TLC states 25 and 660 | 25 and 660 | exact |

**Nothing required correction.** The Wilson implementation is independently duplicated in
`make_ablation_figures.py` and `validate_figures.py` and the two agree.

---

## E. Research limitations — each requirement checked

| Requirement | Status | Where |
|---|---|---|
| Zero corpus hits not presented as zero prevalence | **met** | "We therefore make no claim that the pattern is widespread, and the finding remains a single-system case study." The paper also explains *why* the zero occurred: only 30 of 135 projects contain any authentication identifier, mostly in vendored code. |
| Nine confirmed projects remain an existence claim | **met** | "We report this as an existence claim and not a rate", with the over- and under-counting mechanisms given. Matches `manual_validation.json` exactly. |
| Corpus sampling bias disclosed | **met** | 22 fixed queries, ≥3 stars, <80 MB, archived and forks excluded; criteria and rejection counts in `corpus.json`. |
| Loopback Mosquitto not presented as a wireless deployment | **met** | Stated twice — in the broker section and in Threats to Validity. |
| Host fuzzing not presented as hardware fuzzing | **was a gap, now fixed** | See §8.2. |
| Logical isolation not presented as physical timing isolation | **met** | Abstract, §4, results, conclusion, title, and H2 marked "Requires hardware; not tested here". Construct validity names this "the most serious threat". |
| No new vulnerability or mechanism claimed | **met** | "We claim no new mechanism, attack, protocol or formalism." The attack class is cited as published. |

The evidence taxonomy now names five categories — formal, simulation, testbed measurement,
analytical, corpus study — with what each does and does not transfer to.

---

## 6. Major strengths

1. **It reports defects in its own work, three times.** A configuration defect, a vacuous
   invariant in its own shipped specification, and an unbounded drain. Papers that find their
   own mistakes and lead with them are rare.
2. **The negative results are not buried.** The owner lockout, the zero-hit corpus, the
   detector threshold that was wrong by a wide margin, and four documented harness defects —
   two of which flattered the intended conclusion.
3. **Reproducibility is exceptional.** Byte-identical figure regeneration from source;
   byte-identical simulation from committed seeds; a live-broker experiment whose eight
   verdicts reproduce on a fresh container; a commit-pinned corpus; checks that gate the build.
4. **The negative control discipline.** The corpus rule has eight controls including the real
   pre-repair guard; trace conformance has a forbidden-transition control; the TLA+ runner
   requires a configuration to fail. Each exists because a check that always passes is
   worthless.
5. **Evidence is labelled by kind** and the labels are respected throughout.

## 7. Weaknesses and remaining risks

| # | Weakness | Severity | Can it be fixed before submission? |
|---|---|---|---|
| 1 | The headline timing question is unmeasured | **high** | Yes for A–C: about £25 and an afternoon. D needs institutional resources. See `HARDWARE_VALIDATION_PLAN.md`. |
| 2 | Single-artefact case study, and the attempt to generalise returned zero | **high** | No. It is reported honestly; fabricating prevalence would be worse. The defence is the transferable *method*, which must be prominent in the abstract. |
| 3 | The response-time finding is under-sold | medium | Yes, editorially. It is the cleanest demonstration of the central claim. |
| 4 | Abstract is ~430 words, likely over a typical limit | medium | Yes, once the Guide for Authors is read. |
| 5 | No competing-interest or funding declaration | medium | Yes, trivially. |
| 6 | Five references lack DOIs | low | Yes. |
| 7 | Broker testbed on loopback, not a wireless deployment | low | No, but it is disclosed twice. |
| 8 | Simulation uses a logical clock | low | Disclosed as "the most serious threat" to construct validity. This is correct, not evasive. |

## 8. Defects found by this review, and fixed

### 8.1 E′ missing from the threat model — **fixed**

See §A8. The paper's decisive failure case was not in the threat-model table, and the
physical-versus-remote distinction between E and E′ — which is the reason the result matters —
was not drawn there.

### 8.2 Fuzzing scope not stated in the fuzzing section — **fixed**

§Fuzzing reported 3,000,000 iterations under ASan and UBSan without saying the parser was
**compiled for the host**. The evidence taxonomy covers it, but a reader of that section alone
could take it for on-device fuzzing. Added:

> "The fuzzer exercises the parser *compiled for the host*, not the binary running on the
> device. … This is host fuzzing, not firmware rehosting, and the two are not interchangeable."

---

## 9. Exact sections requiring attention before submission

| Section | Action | Who |
|---|---|---|
| Abstract | Likely needs cutting to the venue's limit. Cut the access-control paragraph's detail, not the three defects. | author |
| Abstract | Consider naming the response-time finding more prominently (weakness 3). | author |
| Front matter | **Add a competing-interest declaration and a funding statement.** Both are absent. | author |
| Front matter | Add Highlights (3–5 bullets) if Elsevier requires them. | author, after reading the Guide |
| Bibliography | Add DOIs to `mcreview2026`, `espwn2023`, `mqtttls2026`, `zeghida2024`; ISBN for `lamport2002`. | author |
| §Hardware validation | Unchanged unless A–C are run. If they are, this becomes a results section and Figure 6 panel B becomes a results figure. | author |
| Whole document | Reformat to `elsarticle` once the venue is fixed; the preamble already carries the alternative. | author |

**Nothing in the Results, Discussion, Formal Verification or Threats to Validity sections
requires scientific change.** The remaining work is editorial, administrative and the
measurement.

---

## 10. Recommendation

**Technically complete and scientifically defensible.** As a reviewer I would recommend
*minor revision* on the science and would press hard on two things: the absent physical
measurement, and whether a single-artefact case study with a null generalisation result meets
the venue's contribution bar. Neither is a correctness objection.

**The single highest-value action remaining is running hardware conditions A, B and C.** They
cost about £25, need no institutional permission, and would convert the paper's most
predictable objection into a result.
