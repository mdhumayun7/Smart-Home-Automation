# Scientific consistency audit

Written in response to a request to verify the manuscript against the repository and the raw
experimental artefacts, on eleven specific points.

Every number below was recomputed from a committed artefact during this audit, not copied from
an earlier document. Where a check failed, the defect and its repair are recorded; three did.

Commands used are given so each check can be repeated.

---

## Summary

| # | Check | Result |
|---|---|---|
| 1 | Trial, iteration, corpus and scenario counts | **pass**, after correcting 3 stale counts in `docs/` |
| 2 | Corpus rule's eight controls and the zero-hit result | pass |
| 3 | Zero hits distinguished from zero prevalence | pass |
| 4 | Nine confirmed projects as an existence claim | pass |
| 5 | Nine credential-table cells | pass |
| 6 | Real Mosquitto experiment and its loopback limitation | **pass**, after adding a missing table row |
| 7 | 19,529 trace-conformance transitions and the negative control | pass |
| 8 | Metamorphic and differential tests | pass |
| 9 | Vacuous-invariant disclosure and the three TLC configurations | pass |
| 10 | No physical timing result claimed | pass |
| 11 | Statistics, intervals, tables, equations, citations, captions | **pass**, after the caption corrections in `FIGURE_VALIDATION.md` |

Three defects found and fixed: two stale counts in supporting documents, one missing row in
the broker table. None of them changed a scientific claim; all three would have been visible
to a careful reviewer.

---

## 1. Counts

```bash
wc -l < experiments/results/ablation.jsonl
python3 -c "import json;s=json.load(open('experiments/results/summary.json'));
print({k:sum(d['rates'][r]['n'] for r in d['rates']) for k,d in s.items()})"
python3 -c "import json;print(json.load(open('experiments/results/fuzz.json'))['iterations'])"
wc -l < experiments/results/sensitivity.jsonl
wc -l < experiments/results/broker_acl.jsonl
wc -l < experiments/corpus/commit_shas.tsv
```

| Claim | Artefact | Observed | Verdict |
|---|---|---|---|
| 3,600 ablation trials, 12 configurations, 300 each | `ablation.jsonl` | 3,600 records, 12 modes, every mode exactly 300 | pass |
| 6,000 campaign trials | `summary.json` | 3,000 baseline + 3,000 hardened, 6 rates each | pass |
| **9,600 adversarial trials** | sum of the two | 6,000 + 3,600 = 9,600 | pass |
| 3,000,000 fuzz iterations | `fuzz.json` | `iterations: 3000000` | pass |
| 180 sensitivity grid cells | `sensitivity.jsonl` | 180 | pass |
| 8 broker scenarios | `broker_acl.jsonl` | 8 | pass |
| 135-project corpus | `commit_shas.tsv`, `corpus.json` | 135 lines; `n_projects: 135`; 135 project entries | pass |

The manuscript's own reconciliation table (`tab:accounting`) names the artefact behind each
count and agrees with all of the above.

### Defect 1 — stale counts in supporting documents

`docs/CONTRIBUTIONS.md` said **9,300** adversarial trials in two places and **eleven
configurations** in one; `docs/SUBMISSION_CHECKLIST.md` said **6,000 + 3,300 = 9,300**. These
are the counts from before the twelfth ablation arm was added. The manuscript was already
correct at 9,600. Corrected.

Two further documents, `docs/Q2_GATE.md` and `docs/JOURNAL_ASSESSMENT.md`, were written
against the eleven-arm campaign and before the broker validation. Rather than silently edit a
dated assessment, each now carries a banner saying what has changed since and pointing at the
current position. `Q2_GATE.md`'s row 7 recorded a model-validity caveat — "no Mosquitto
instance was used" — which the broker experiment has since discharged, and the banner says so.

---

## 2. The corpus rule's eight controls, and the zero

```bash
python3 -I experiments/corpus/test_rule.py
```

All eight pass:

| Control | Expected | Got |
|---|---|---|
| `prefix_guard_real` — this project's own guard before the fix | flag | flag |
| `postfix_guard_real` — the repaired guard | clean | clean |
| `requires_appauth` — authentication required un-negated | clean | clean |
| `transport_only` — a capability gated on transport alone | flag | flag |
| `capability_only` — no transport identifier | clean | clean |
| `transport_no_capability` — transport config gating nothing privileged | clean | clean |
| `continuation` — condition spans a backslash continuation | flag | flag |
| `negated_hmac_elsewhere` — authentication named but negated | flag | flag |

The last two matter most. `continuation` exists because a rule that does not join continued
preprocessor lines silently under-reports. `negated_hmac_elsewhere` exists because the rule
was **wrong at first in exactly that way**: it treated any mention of an authentication
identifier as evidence that authentication was required, and so returned zero against this
project's own pre-repair guard, in which `AUTH_COMMANDS` appears negated. Until that was
found, the zero result was meaningless. The manuscript discloses this (Section `sec:corpus`).

`findings.json` records `rule1_projects: 0` and `rule1_total_hits: 0` over `n_projects: 135`.

---

## 3. Zero hits is not zero prevalence

The manuscript states it directly, in the same paragraph as the result:

> **The rule found nothing.** Zero hits in 135 projects. We therefore make no claim that the
> pattern is widespread, and the finding remains a single-system case study.

and gives the mechanism behind the zero rather than leaving it as a bare null: only 30 of the
135 projects both subscribe to MQTT and contain any authentication identifier at all, and
reading those shows most matches sit in vendored code rather than in the project's own command
path. The corpus is biased by construction — 22 fixed GitHub queries, minimum 3 stars, under
80 MB, archived repositories and forks excluded — and `corpus.json` records those criteria and
the rejection counts. **Pass.**

---

## 4. The nine confirmed projects are an existence claim

`experiments/corpus/manual_validation.json` records `corpus_size: 135`, `flagged_by_rule: 18`,
and a summary of `confirmed_true_positive: 9`, `false_positive: 9`. Its own `reading` field
states:

> These verdicts support an existence claim and not a prevalence claim. … The 18/135 figure is
> not a rate: the rule over-counts monitoring projects at about fifty per cent and
> under-counts non-GPIO actuation by an unknown amount.

The manuscript matches it, including the under-counting mechanism:

> We report this as an existence claim and not a rate: the rule over-counts by about half and
> under-counts by an unknown amount, since three confirmed cases actuate through Modbus, RF or
> serial frames and were caught only by an incidental GPIO write.

**Pass.** The 9/18 split, the ~50 % false-positive rate and the three non-GPIO cases all
appear in both.

---

## 5. The nine credential-table cells

Every cell of `tab:credential` recomputed from `ablation_summary.json`, including the disarm
column, which the table carries but no figure plots:

```
ok  TLS only, no secret                 alarm 300/300  admitted 1250/1250  disarm no
ok  TLS only, any broker credential     alarm  50/300  admitted 1250/1250  disarm yes
ok  TLS + ACL, the one shared credential alarm 50/300  admitted 1250/1250  disarm yes
ok  TLS + ACL, controller credential    alarm  50/300  admitted 1250/1250  disarm yes
ok  TLS + ACL, device credential        alarm 300/300  admitted 1250/1250  disarm no
ok  HMAC + counter, any broker credential alarm 300/300 admitted 1250/1250 disarm no
ok  HMAC + counter, controller cred + key alarm 50/300 admitted    0/1250  disarm yes
ok  TLS+ACL+HMAC, device cred + key     alarm 300/300  admitted 1250/1250  disarm no
ok  TLS+ACL+HMAC, controller cred + key alarm  50/300  admitted    0/1250  disarm yes

9 cells checked; 0 mismatches
```

The controller-credential-plus-command-key row is present, is not hedged, and carries the
owner-lockout result (0 of 1,250). `tab:withstands` states the same conclusion in prose, and
the manuscript says in the surrounding text that an earlier draft claimed the layered
configuration "survives every case" and that this was wrong. **Pass.**

---

## 6. The real Mosquitto experiment and its loopback limitation

```bash
cat experiments/results/broker_acl_summary.md
```

Eight scenarios against Mosquitto 2.0.18 over TLS 1.2 with a private certificate authority,
`password_file` authentication and a deny-by-default `acl_file`. Every verdict is decided by
whether a subscriber holding the device identity actually received the message, **not** by
PUBACK — MQTT 3.1.1 has no return code meaning "refused by policy", so the broker acknowledges
a QoS 1 publish and then silently discards it. The summary prints the PUBACK column precisely
to show it is uninformative.

The decisive pair is E and E′: the same valid signature, carried by the device identity, is
not delivered; carried by the controller identity, it is. What stops E is therefore the
access-control list and not the signature.

**The loopback limitation is stated, twice:** at the end of the broker section ("the broker ran
on loopback with a private CA rather than in a deployed…") and again in Threats to Validity.

### Defect 2 — the table showed seven of eight scenarios

The text said "All eight scenarios were reproduced"; `tab:broker` listed seven rows, because
the two legitimate controls — one per ACL variant — had been collapsed into one. A reviewer
counting rows would have found a discrepancy. The second control is now shown, the two ACL
variants are separated by a rule, and the caption states what E′ establishes and why PUBACK is
not evidence. **Fixed.**

---

## 7. Trace conformance: 19,529 transitions

```bash
python3 -I experiments/test_conformance.py
```

```
ok   negative control: a forbidden Disarmed -> Alarm transition is rejected
ok   none       7044 states, 0 disallowed
ok   ratelimit  5282 states, 0 disallowed
ok   token      7206 states, 0 disallowed

19529 transitions checked
all observed transitions are permitted by the specification
```

7,044 + 5,282 + 7,206 = 19,529. The negative control matters: a conformance checker that
accepts everything would also report zero violations, so the suite asserts that a transition
the specification forbids is in fact rejected. The transition relation is parsed out of
`formal/AlarmFSM.tla` rather than restated, so the check cannot drift from the specification
it is checking. **Pass.**

---

## 8. Metamorphic and differential tests

```bash
python3 -I experiments/test_harness.py
```

All properties hold:

| | Property |
|---|---|
| M1 | determinism: the same seed gives the same record |
| M2 | seed sensitivity, probed on `ratelimit` — a saturated design cannot exhibit it, and the suite says so rather than passing vacuously |
| M3 | quiet trials carry no attacker activity, at rate 0 |
| M4 | a design defeated at a low attack rate stays defeated at a higher one |
| M5 | the mode switch actually reaches the command path: undefended and signed designs differ, the undefended one is in fact defeated by replay, the signed one is in fact not |
| D1 | the firmware's HMAC payload format agrees with an independent implementation, for three counter values including `4294967295` |

M5 is the one that would catch the worst class of harness bug — a mode switch that does
nothing, so every arm silently measures the same system.

---

## 9. The vacuous invariant, and three TLC configurations

```bash
bash formal/run_tlc.sh
```

```
=== TLC: AlarmFSM ===                                          PASS
=== TLC: Isolation ===                                         PASS
=== TLC: AlarmFSM, defective configuration (violation REQUIRED) ===
PASS AlarmFSM_unsafe: TLC reports the expected NoUnauthRemoteDisarm violation
```

State counts: `AlarmFSM` 166 generated / **25 distinct**; `Isolation` 2,686 generated / **660
distinct**. Both match the manuscript (Section 5) and the methodology figure.

The third configuration is the point. `NoUnauthRemoteDisarm` was **vacuous in the
specification that was shipped and checked in CI**, because the specification *assumed* the
refusal rather than deriving it — the same unsound inference the compile guard made.
`AllowUnauthDisarm` is now a CONSTANT, `AlarmFSM_unsafe.cfg` sets it TRUE, and `run_tlc.sh`
**requires TLC to fail** on that configuration. A run in which it passes means the invariant
has gone vacuous again, so the regression cannot recur silently.

The manuscript discloses this in a section of its own (`sec:vacuity`), and the disclosure is
named in the abstract and in the title. **Pass.**

---

## 10. No physical timing result is claimed

Searched for any measured latency, response time or timing figure presented as observed:

```bash
grep -nE "we measured [0-9]|latency of [0-9]|[0-9]+\.[0-9]+ *(ms|µs|us) (latency|response)" paper/manuscript.tex
```

No matches. What the paper does state, in the abstract, in Section 7 and in the conclusion, is
the opposite:

> These results establish *logical* isolation only. Physical timing invariance is a property of
> the silicon and a closed-source radio driver, and we report no latency figure we have not
> measured.

> We report no latency figure, because we have not measured one.

The response-time section contributes a *decomposition* that reduces four interference terms
to one composite hardware quantity and names what a measurement must isolate. That is an
analytical result and is labelled as one in the evidence taxonomy. Figure 6 panel B is drawn
dotted, headed "Not yet measured", and carries a red line saying no result in the paper comes
from it; its caption repeats this. The only timing numbers anywhere in the paper are
Behnke et al.'s (2.15–3.8 % and 3.17–6.67 % cycle loss), attributed to them in the
introduction and in related work. **Pass.**

---

## 11. Statistics, intervals, tables, equations, citations, captions

**Statistics, recomputed from the raw records.**

| Claim | Recomputed | Verdict |
|---|---|---|
| Rate limiter admits 59.0 % of operator attempts | 737 / 1250 = 59.0 % | pass |
| Fisher exact, one-sided, $p = 3.5\times10^{-184}$ (rate limiter vs others) | 3.53 × 10⁻¹⁸⁴ | pass |
| Leaked-credential arm: alarm in 16.7 % | 50 / 300 = 16.67 % | pass |
| 95 % Wilson CI [12.9 %, 21.3 %] | [12.9, 21.3] | pass |
| Fisher exact, one-sided, $p = 9.8\times10^{-119}$ (transport leaked vs held) | 9.83 × 10⁻¹¹⁹ | pass |
| Adversary disarms in 246 of 300 trials | 246 | pass |
| Owner lockout: 0 of 1,250 | 0 / 1250 | pass |
| Detector default fired in 79.9 % of benign ten-minute runs | `sensitivity.jsonl`, threshold 8 / window 2000 ms: 1597 / 2000 = 79.85 % | pass |

The 79.9 % figure is the **original** default; the firmware now ships `DEAUTH_THRESHOLD = 12`,
which is the correction the sweep produced. The manuscript describes it that way.

**Wilson intervals.** Computed with continuity-free Wilson score, clamped at 0 and 1, in both
`make_ablation_figures.py` and `validate_figures.py` independently; the two agree. The clamp
matters: at *p* = 1 an unclamped lower whisker renders below the axis.

**Tables.** All eleven are referenced in the text; no table is orphaned. `tab:accounting`
reconciles every count to a named artefact. `tab:credential` verified cell by cell in item 5;
`tab:broker` corrected in item 6.

**Citations.** 22 `\bibitem` entries, 22 cited, **0 uncited and 0 undefined**. Three entries
had previously been orphaned when a related-work paragraph was lost; that is not the case now.

**Cross-references.** `pdflatex` completes with **zero warnings** over three passes, so every
`\ref` and `\cite` resolves. No `Overfull \hbox` exceeds 20 pt. The document builds to **31 pages** as
of the Phase 6 corrections (30 when this audit was first written). (An earlier revision of this audit recorded 31; that figure was taken immediately
after the float-placement change, which briefly added a page, and before the caption and
evidence-taxonomy edits reflowed it. 30 is the count for the final document and is
reproducible from a clean build.)

**Figure captions.** Reviewed one by one against what each figure now draws; five were changed
and the reasoning is recorded in `docs/FIGURE_VALIDATION.md`. The two that mattered
scientifically: Figure 6's caption called the whole of panel A "the simulation harness", but
E6 ran against a live broker and is not a simulation, which the paper's own evidence taxonomy
depends on; and Figure 8's caption did not mention the compromised-controller row, which the
figure had also been missing.

**Figure placement.** All eight floats had been reaching the reader on pages 26–30 of a
30-page document. They now land on pages 8, 9, 16, 18, 18, 21, 23 and 24, beside the text that
refers to them.

---

## What this audit did not cover

- **Prose-level plagiarism or AI-detection screening.** Not performed, and no claim is made
  about either. These require tools this environment does not have and judgement that belongs
  with the author and supervisor.
- **The journal quartile.** Unverified. SCImago and the ACM Digital Library are behind bot
  verification, which was not circumvented, so no quartile is asserted for any venue. What is
  verified from Elsevier's own pages is CiteScore 9.1 and Impact Factor 5.3 for the Journal of
  Systems Architecture. See `docs/JOURNAL_ASSESSMENT.md`.
- **The target journal's current Guide for Authors.** Not retrieved. The manuscript is in a
  neutral `article` class with commented-out `elsarticle` and `IEEEtran` preambles, so the
  switch is one line when the venue is fixed.
- **Hardware conditions A–D.** Not run. This is the paper's declared open step, not an
  oversight.
