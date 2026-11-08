# Response to reviewers

Point-by-point response to the three simulated reviews in `docs/SIMULATED_PEER_REVIEW.md`.

**Every addressable concern has been resolved.** None required new experiments or hardware. Two
produced substantive new results, and one revealed a design weakness we had not seen.

Status key: **RESOLVED** — changed in the manuscript or artefact. **RESOLVED (declined)** — we
disagree and say why. **DEFERRED** — not addressable without hardware, and recorded as such.

---

## Reviewer 1 — Embedded and real-time systems

### M1. The third dimension produces no number, and the title promises a defect in it

**RESOLVED (partly declined).** The reviewer accepts the title is not false, and we retain it: the
defect found *is* a response-time defect, and the paper claims a defect was found rather than a
property measured. But the substance of the concern was right, and M2 is where we acted on it — §5
now produces a number for $C_{\mathrm{own}}$ and a concrete latency bound, so a reader arriving
from real-time systems no longer finds only a framework.

### M2. $\bar{C}$ is unquantified and that is not a hardware limitation

**RESOLVED, and this is the most valuable comment in the review.** The reviewer was right that the
I²C transaction can be bounded by arithmetic, and we had wrongly attributed its absence to the
missing device. Derived from the bus clock and transfer length, both read from source
(`Wire.setClock(400000)`, l.1079; `Adafruit_SSD1306 display(128, 64, ...)`, l.338):

> 1,024 framebuffer bytes + 32 chunks × (address byte + data-mode byte) = 1,088 bytes
> × 9 bit-times = 9,792 bit-times ÷ 400 kHz = **$c_{\mathrm{i2c}} = 24.48$ ms**

Three consequences, now in §5 and in `docs/MATHEMATICAL_MODEL_AND_PROOFS.md` §2.3.1:

1. **$c_{\mathrm{i2c}}$ is essentially the whole of $C_{\mathrm{own}}$**, exceeding every other
   stage by more than an order of magnitude.
2. **A 160 ms deadline is infeasible for this firmware before any interference is considered**, and
   at 200 ms the design has roughly half a millisecond of interference budget. Core pinning cannot
   protect a budget already spent on a display refresh. This is the most consequential number the
   analysis produces, and we would not have derived it without this comment.
3. **A design weakness we had not seen:** the refresh runs on the safety task and should be moved
   off it or chunked across passes. We state it and have not fixed it.

$c_0$ and $c_{\mathrm{cmd}}$ remain symbolic. Both are microsecond-scale against a 24.48 ms term,
so they change no conclusion, and we say so rather than leaving the reader to wonder.

### M3. The factor of 2 in $L \le T_{\mathrm{conf}} + 2R$ is loose

**RESOLVED, and the looseness is now removed rather than excused.** Pursuing it produced a result:
because `driveOutputs` precedes `updateDisplay` in program order, only the *interrupted* pass can
contain a display transaction, giving

$$L \le T_{\mathrm{conf}} + R_{\mathrm{full}} + R_{\mathrm{pre}}
     \;\lesssim\; 175\ \text{ms} + \text{interference},$$

tighter than $T_{\mathrm{conf}} + 2R$ by a whole display transaction. **The stage order is
therefore load-bearing for the deadline**: swapping two adjacent calls, an edit with no visible
effect, costs about 24.5 ms. Nothing in the code recorded this, which makes it an instance of
precisely the undocumented assumption the paper is about. Added as Proposition 1′.

### M4. (T4) is asserted, not established

**RESOLVED by correcting the claim rather than by asserting it harder.** The reviewer is right, and
checking it showed the assumption as written is too strong. The firmware creates exactly one task
of its own and pins it to core 0, and `loop()` runs in the framework's `loopTask` on core 1 — so no
*application* task preempts the safety task. But core 1 is not empty: the SDK maintains a per-core
idle task (lowest priority, cannot preempt) and an inter-processor-call task (high priority, runs
only during a cross-core call, which this firmware never issues directly), and framework timer and
event task affinities come from SDK configuration we did not audit.

(T4) now reads **"no application task preempts $\tau_s$"**, which is established, rather than
"nothing preempts $\tau_s$", which is not. Confirming the stronger form needs a `vTaskList` dump
from a running device; that is a two-line firmware addition and a serial capture, and it is listed
in the hardware runbook as a prerequisite measurement rather than claimed as done.

### Minor points

- **Cooldown placement.** RESOLVED (declined, with a change). It stays in §5 where the timing
  argument needs it, because that is where its role in the arrival bound is load-bearing; we added
  the cross-reference so an engineer tuning the detector reaches it.
- **Event-queue priority in the abstract.** RESOLVED (declined). The abstract's limitation sentence
  is reserved for the physical-timing limitation, which is the paper's principal one. The queue
  weakness is a notification rather than safety issue and is stated in §5, §14 and the threats
  document. Promoting it would displace a more important caveat from a 249-word abstract.
- **Drop the "151 ms" constant.** RESOLVED (declined). We keep it with the statement that variance
  is identically zero, because removing the number would make the zero-variance claim unverifiable
  against the committed records, where `safety_latency_ms ∈ {0, 151}`.

### On Theorem 1

**RESOLVED.** Agreed, and demoted. It is now **Proposition 7**, introduced as a *budget
decomposition* with an explicit note that it follows immediately from its own hypotheses and that
its value is organisational rather than mathematical. Propositions 3–6 are promoted in prominence,
with Proposition 5 — sustained event-queue overflow whenever the loop period is under 25 ms —
identified as the substantive result. Reviewer 3 raised the same point independently.

---

## Reviewer 2 — IoT security and MQTT

### M1. The loopback testbed is doing more work than the paper admits

**RESOLVED.** The manuscript now states that the broker result is a **conformance check of one
mechanism**, not a security evaluation of a deployment, and names what loopback with one client at
a time excludes: concurrent clients, retained-message interactions, session takeover by duplicate
client ID, QoS 2 flows, bridging and `$SYS` exposure — several of which are the usual ways real
deployments are broken.

### M2. The threat model omits a compromised broker

**RESOLVED, and the reviewer identified a real gap.** The entire access-control argument rests on
the broker enforcing its own policy faithfully, and we had not said so. Table 2 is now preceded by
an explicit statement of what is trusted: the broker, the controller host, and the vendor radio
stack. We state plainly that **no result in this paper survives a malicious or compromised
broker**, and that in a home deployment the broker is often a third-party service or an unpatched
single-board computer, so the omission is realistic rather than theoretical.

### M3. No key management, and the strongest finding depends on its absence

**RESOLVED with a new subsection**, because the reviewer is right that a reader could take the
counter-bound MAC as a sound design. §13 now says: this firmware has no rotation, no revocation and
no counter resynchronisation; **those absences are the direct cause of both negative results** —
the owner lockout because no authenticated path can reset an advanced counter, and E′ because a
compromised key cannot be retired. The defensible claim is narrowed explicitly to *"under the
assumption that the key remains secret and the controller host is intact"*. We also state that
designing that machinery for a device with no secure element, no clock and 1,024 bytes of usable
non-volatile storage is the open problem our results point at, and that we do not solve it.

### M4. The 128-bit tag needs a justification

**RESOLVED.** The RFC 2104 §5 permission and the $2^{-128}$ per-attempt figure were already there;
the rate-based reasoning the reviewer wanted was not. Added: at a sustained $10^3$ attempts/s for a
decade ($\approx 2^{38}$ trials) the forgery probability is near $2^{-90}$; an 8-octet tag would
leave $\approx 2^{-26}$ over the same period, too close for a safety function; 32 octets would
double the tag on a wire format that must fit an MQTT payload for no reachable gain. We note the
reasoning is analytical and that the fuzzing campaign cannot corroborate it, since zero forgeries
is the expected outcome at any of these lengths.

### Minor points

- **A syntactic rule cannot find an inference.** RESOLVED — incorporated into the reframed §11,
  which now leads with what the section contributes (the instrument and its validation) rather than
  the counts, and states that a rule matching syntax cannot find the same class of defect expressed
  differently.
- **"Credential separation, not the ACL syntax, carries the protection."** RESOLVED — the reviewer
  is right that this sentence existed only in a generated results document. It is now in the paper.
- **Scenario B deserves more emphasis than E.** RESOLVED (partly declined). We agree it is the most
  likely real configuration and have said so in §10, but we keep E's separate treatment because it
  is the one scenario requiring physical access and conflating the two would weaken the cost
  asymmetry that is the section's point.

### Raw campaign records not committed

**RESOLVED.** The reviewer called it an oversight and it was: the records were gitignored on the
grounds that they regenerate identically from committed seeds — true, and verified again in this
revision — but "regenerates" is not "available", and the ablation and sensitivity raw records were
committed for exactly the opposite reason. Both campaign JSONL files (1.4 MB) are now tracked, and
the `.gitignore` comment records why the earlier reasoning was wrong.

---

## Reviewer 3 — Formal verification, empirical methodology and mathematical analysis

### M1. Theorem 1 should not be a theorem

**RESOLVED.** See the response to Reviewer 1 above — demoted to Proposition 7 and presented as a
budget decomposition, with Propositions 3–6 promoted. Two reviewers reaching this independently
settled it.

### M2. The corpus study does not support its own place in the paper

**RESOLVED.** §11 is restructured as the reviewer suggested. It now opens by stating that the
generalisation attempt returned a null result and that **the counts are not the contribution**; the
reusable contribution is the instrument and its validation — the labelled control set including our
own pre-repair guard and its repair, and the documented polarity defect that made the rule's first
zero meaningless. The section is explicit that a reader looking for a prevalence finding will not
find one, and that a reader building such a rule will find what it takes to know whether theirs
works.

### M3. Model coverage is thin and the ratio should be stated

**RESOLVED.** §6 now states coverage quantitatively: two specifications abstracting a five-state
machine with a counter and a seven-variable two-task model, out of 1,166 firmware lines, with
explicit lists of what is modelled and what is not — the HMAC computation (checked differentially
instead), the parser (fuzzed), non-volatile storage, detector arithmetic, sensor fusion, display,
MQTT client, ESP-NOW, and **execution time, which neither model represents at all**.

### M4. `MaxCtr = 4` deserves a sentence on why it suffices

**RESOLVED.** Added a data-independence argument: no action in the specification inspects the
counter's *value*, only the predicate $c > c_{\text{stored}}$ and the successor relation, so the
reachable control structure is identical for any bound $\ge 2$ and enlarging the bound adds states
isomorphic to those already explored. We also state the weaker thing we actually did — verified the
state count at the chosen bound rather than proving the isomorphism mechanically.

### M5. Five instances raises a question the paper does not confront

**RESOLVED, and this was the sharpest comment in the review.** §14 now says which parts of the
infrastructure still have **no** control, which is the honest extension of our own argument:

1. The **host stub models** have no differential check against real Arduino or FreeRTOS behaviour,
   so a shared misconception between the stubs and the firmware — which have the same author —
   would be invisible to both.
2. The **broker scenarios** are adjudicated by a script reading Mosquitto's log, and nothing
   independently verifies that the script's parse matches the broker's intent.
3. The **corpus adjudication** of eighteen flagged projects was done by one person with no second
   rater, so no inter-rater agreement can be reported.

We draw no conclusion depending on those three beyond what is stated.

### Minor points

- **H2 should not be a hypothesis of this study.** RESOLVED. Reclassified as the pre-registered
  hypothesis of the future experiment, retained in the methodology only because the design was
  built to satisfy it and a reader should know what it was aiming at.
- **"Pre-declared" is asserted, not evidenced.** RESOLVED (partly). The twelve arms are fixed in
  `ablation.cpp` and the two comparisons are computed in `analyse_ablation.py`, both committed
  before the reported analysis, so the claim is checkable from history rather than taken on trust;
  we say so. We cannot produce a pre-registration document, because none exists for the simulation
  work — only for the hardware protocol — and we do not pretend otherwise.
- **79.8% vs 79.9%.** RESOLVED by removing the ambiguity rather than picking a side. 1597/2000 =
  0.7985 is an exact tie at one decimal, which round-half-even renders 79.8% and round-half-up
  renders 79.9% — the two documents disagreed for that reason alone. All of them now report
  **1,597 of 2,000 (79.85%)**.

### Literature weaknesses

**RESOLVED (partly).** Agreed that a preprint should not carry positioning weight: the oracle-
anchoring preprint is cited as a secondary observation and labelled a preprint, while the
positioning rests on the peer-reviewed vacuity literature. On the unresolvable venue: we made two
further search attempts and two publisher-page fetches and still could not establish it, so the
entry states "venue not independently verifiable" and asserts no venue, volume or page range. We
share the reviewer's dislike of this, and we prefer a visible gap to an invented citation.

---

## Editor's required items

| # | Item | Status |
|---|---|---|
| 1 | Demote Theorem 1; promote Propositions 3–6 | **RESOLVED** |
| 2 | Bound $C_{\mathrm{own}}$ by arithmetic, or say why not | **RESOLVED** — $c_{\mathrm{i2c}} = 24.48$ ms |
| 3 | Demonstrate core-1 exclusivity or weaken the claim | **RESOLVED** — claim weakened to application tasks; verification deferred to hardware |
| 4 | Compromised-broker row and trust assumptions | **RESOLVED** |
| 5 | State the broker result is a conformance check | **RESOLVED** |
| 6 | Counter-bound MAC unsound without key management | **RESOLVED** — new subsection |
| 7 | Justify the tag length analytically | **RESOLVED** |
| 8 | Restructure §11 around the instrument | **RESOLVED** |
| 9 | State formal coverage quantitatively | **RESOLVED** |
| 10 | Justify `MaxCtr = 4` | **RESOLVED** |
| 11 | Say which infrastructure has no control | **RESOLVED** |
| 12 | Commit the raw campaign records | **RESOLVED** |
| 13 | Reclassify H2 | **RESOLVED** |
| 14 | Fix the 79.8/79.9 inconsistency | **RESOLVED** |

### Editor's note on positioning

Accepted. The review split along the embedded/security line exactly as the editor observed, and we
agree the paper is a security-and-methodology contribution: the measured results concern
authorisation, the formal results concern specification quality, and the timing dimension
contributes a decomposition and an unexecuted protocol. `docs/JOURNAL_SELECTION_2026.md` reached
the same conclusion independently and identifies the timing objection as the likeliest cause of
rejection at the first-choice venue, with a cover-letter strategy to pre-empt it.

---

## What this review round changed in the science, not just the prose

Recorded separately because three items are substantive:

1. **A real number where there had been a symbol.** $c_{\mathrm{i2c}} = 24.48$ ms, and with it a
   latency bound of roughly 175 ms plus interference, derived from constants in the source.
2. **A feasibility verdict we did not have.** A 160 ms deadline is infeasible for this firmware
   before interference is considered, and a 200 ms deadline leaves about half a millisecond of
   interference budget.
3. **A design weakness and an undocumented dependency.** The display refresh belongs off the safety
   task, and the order of two adjacent calls is load-bearing for the deadline with nothing in the
   code to say so.

All three came from one reviewer comment pointing out that a term we had called unmeasurable needed
only arithmetic.
