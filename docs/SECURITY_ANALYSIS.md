# Transport security, command authorization, and the remote-disarm compile guard

This document records a defect found by experiment in this project's own firmware, its exact
root cause, what the measured evidence does and does not establish, and an assessment of
whether the finding is a research contribution or a restatement of a known principle.

The short answer to the last question, established in section 7: **it is a known security
principle, and the attack class is already published.** This project does not claim a new
vulnerability. What the experiment contributes is a controlled, seed-matched measurement that
an unsound *compile-time configuration guard* in a safety-critical state machine converts that
known principle into loss of a **safety** property, and a negative control that makes the
command-path ablation fair.

**Evidence category of every quantitative result below: host simulation.** No physical
hardware, no real TLS handshake, no real broker. See `docs/EXPERIMENTS.md` for the taxonomy.

---

## 1. The guard

`firmware/smart_home/smart_home.ino`, lines 218–223:

```c
#ifndef ALLOW_REMOTE_DISARM
#  define ALLOW_REMOTE_DISARM 0
#endif
#if ALLOW_REMOTE_DISARM && !AUTH_COMMANDS && (!MQTT_USE_TLS || !MQTT_HAS_LOGIN)
#  error "ALLOW_REMOTE_DISARM needs AUTH_COMMANDS 1, or MQTT_USE_TLS 1 with broker credentials"
#endif
```

Read positively, the guard permits unauthenticated remote disarm when
`MQTT_USE_TLS && MQTT_HAS_LOGIN`. The dispatch site, line 664:

```c
case Cmd::DISARM:
  if (m.authed || ALLOW_REMOTE_DISARM) {
    if (state != SysState::DISARMED) disarm(src, now);
    else emitEvent("cmd_ignored", src);
  } else {
    emitEvent("cmd_rejected", src);
  }
  break;
```

`ALLOW_REMOTE_DISARM` is a compile-time constant. When it is 1, the `m.authed` test is
short-circuited: **every** syntactically valid `DISARM` that reaches `cmdQ` disarms the system,
whatever its origin, and `authed` is never consulted.

## 2. The unsound inference

The guard encodes this implication:

> TLS enabled ∧ the device supplies a broker username ⟹ every message delivered on the command
> topic originates from an authorized principal.

Each conjunct fails to support the conclusion, for a different reason.

**2.1 `MQTT_USE_TLS` authenticates the broker to the device, not the publisher to the device.**
Line 1069 is the whole of the TLS identity configuration:

```c
#if MQTT_USE_TLS
  netClient.setCACert(SECRET_MQTT_CA_CERT);
#endif
```

This sets a CA used to validate the *server* certificate. There is no client certificate, so
the device presents no TLS identity; its identity to the broker rests entirely on
username/password. More fundamentally, MQTT is a store-and-forward hub-and-spoke protocol and
**the broker terminates TLS**. Each publisher holds its own, separate TLS session to the broker.
A message arriving over the device's TLS session therefore carries *no cryptographic evidence
whatsoever* about who published it. TLS secures a hop; it does not convey end-to-end
provenance across a relay.

**2.2 `MQTT_HAS_LOGIN` describes this device, not any publisher.** Lines 117–123:

```c
#ifndef SECRET_MQTT_USER
#  define SECRET_MQTT_USER nullptr
#  define SECRET_MQTT_PASS nullptr
#  define MQTT_HAS_LOGIN 0
#else
#  define MQTT_HAS_LOGIN 1
#endif
```

`MQTT_HAS_LOGIN` is 1 if and only if a username macro is defined in `secrets.h`. It is a fact
about the *subscriber's* build configuration. It says nothing about whether the broker enforces
an access-control list, whether that list is correct, or what any *publisher* is permitted to
do. The guard uses the subscriber's own credential state as a proxy for every publisher's
authorization. That is a category error, and it is the core of the defect.

**2.3 Even a correctly configured broker moves the decision outside the device's trust
boundary.** With a correct ACL, authorization is enforced *at the broker*, and is only as
strong as credential secrecy. MQTT username/password credentials are bearer tokens: possession
is authority. In practice they are long-lived, frequently shared across every client in a
deployment, stored in plaintext in firmware or a `secrets.h`, and recoverable from an
unencrypted flash image. The device has no way to detect that a credential has been copied.

## 3. What the measurement shows

Six command-path designs, same adversary, same scenario, identical seed set, 300 trials each
(1,800 total). The two arms that isolate this defect differ in exactly one variable — whether
the adversary possesses valid broker credentials:

| Arm | Adversary holds credentials | Build |
|---|---|---|
| `transport` | no | `MQTT_USE_TLS=1`, `ALLOW_REMOTE_DISARM=1`, `AUTH_COMMANDS=0` |
| `transport_leaked` | yes | identical |

The builds are byte-for-byte the same; only the adversary's credential possession changes.
Results are in `experiments/results/ablation_summary.md`, regenerated from the committed
`ablation.jsonl` by `experiments/analyse_ablation.py`.

The adversary cannot forge TLS, cannot break the cipher, and cannot read the device's flash.
It is modelled only as a party that has obtained a working credential and can connect to the
broker as a legitimate client would. This matters for section 7: the attack requires no
cryptographic break at all.

## 4. What TLS does and does not protect

Stated explicitly, because it would be wrong to conclude from section 3 that TLS is broken.
**TLS is not broken here, and nothing in this project's evidence bears on the security of
TLS.** The defect is in what the firmware *infers* from TLS being enabled.

TLS, as configured here, does protect:

- confidentiality and integrity of the device↔broker hop against a passive eavesdropper or an
  on-path attacker;
- broker identity, via CA validation — the device will not accept an impostor broker;
- against injection or modification of messages *on that hop*.

TLS, as configured here, does not protect:

- publisher authenticity end to end, because the broker terminates TLS and re-originates the
  message;
- the *semantics* of a command — TLS carries bytes and has no notion of "disarm";
- anything at all once a valid credential is in an adversary's possession, because at that
  point the adversary *is* a legitimate TLS client.

The last point is the one the guard missed. Transport security and application-layer
authorization are orthogonal properties, and no amount of the former supplies the latter.

## 5. Why application-layer authentication helps, and its exact assumption boundary

With `AUTH_COMMANDS=1`, a command is accepted only if it carries a valid HMAC-SHA256 tag
(128-bit, truncated) over the payload under `SECRET_CMD_KEY`, with a counter strictly greater
than the value persisted in NVS. Broker credentials are irrelevant to that check, and the key
never travels on the wire. An adversary holding only broker credentials therefore cannot
produce an accepted `DISARM`: it would need the key.

**This project does not claim that HMAC is secure under broker compromise in general.** The
following assumptions are load-bearing, and three of them are weaknesses of this
implementation rather than of the mechanism:

1. **The key must actually have been changed.** Line 210 ships a default:
   ```c
   #ifndef SECRET_CMD_KEY
   #  define SECRET_CMD_KEY "demo-shared-key-change-me"   // public demo key; override in secrets.h
   #endif
   ```
   This string is in a public repository. A deployment that enables `AUTH_COMMANDS` without
   overriding it obtains **no protection whatsoever**, while appearing in every log and every
   code review to be authenticated. Section 6 implements a compile-time refusal for this case.
2. **The key is symmetric and shared.** Verification and signing use the same secret, so every
   authorized publisher holds a key that can also forge. The key therefore exists in at least
   two places (device and controller), and compromise of either is total. There is no per-device
   key derivation.
3. **The key is readable from flash unless the SoC's protections are enabled.** This project
   does not enable ESP32 flash encryption or secure boot. With physical access, JTAG, or a
   flash dump, `SECRET_CMD_KEY` is recoverable, after which HMAC provides nothing. This is a
   documented limitation, not a measured result.
4. **There is no rotation and no revocation.** The NVS counter defeats replay, but a key
   compromise is unrecoverable without reflashing every holder.

The honest statement of what HMAC buys, therefore, is scoped: *against an adversary who holds
broker credentials and arbitrary network position, but not the command key, and who cannot read
device flash, application-layer authentication prevents unauthorized disarm; the monotonic NVS
counter additionally prevents replay of a captured legitimate command.* Outside that boundary
it provides correspondingly less, and under key compromise it provides nothing.

## 6. Guard strengthening: what was changed and what was deliberately not

The guard's permissive branch tests a condition that cannot establish what it needs to
establish (section 2). The minimal correct fix is to remove that branch from the default build
rather than to add a mechanism. Two changes were made:

1. **`ALLOW_REMOTE_DISARM` without `AUTH_COMMANDS` no longer compiles by default.** The
   TLS-plus-login escape now requires an explicit acknowledgement macro,
   `ACKNOWLEDGE_UNAUTHENTICATED_DISARM`, whose name states what the builder is accepting. The
   research baseline remains reproducible by defining it, so the `transport` and
   `transport_leaked` arms still build and the original behaviour is preserved for comparison.
2. **`AUTH_COMMANDS=1` with the default demo key no longer compiles.** This closes the
   failure mode in section 5.1, where a build appears authenticated but uses a published key.

The following were evaluated and **not** implemented, with reasons, because adding them would
inflate the contribution count without evidence to support them:

| Candidate | Assessment |
|---|---|
| Timestamp / freshness window | Needs a trusted clock. The device has no RTC and no NTP in this build; the monotonic counter already defeats replay without requiring time sync. Not justified. |
| Nonce-based challenge–response | Requires a round trip on a QoS 0, at-most-once path, so a lost challenge becomes a lost command. Would weaken availability to restate a property the counter already provides. |
| Credential rotation / revocation | A broker-side and fleet-management concern, outside this firmware's scope. Recommended in deployment guidance, not implemented. |
| Secure key storage (flash encryption, secure boot) | The correct mitigation for section 5.3 and an ESP-IDF platform feature, but it cannot be validated without physical hardware, which this project does not have. Documented as a requirement for any real deployment and listed in the hardware-validation framework. |
| Separate broker-auth from command-auth | Already the structure after change 1: `m.authed` is the only path to disarm in a default build. |

## 7. Is this a research contribution?

Assessed against the literature, searched through 6 November 2026. The conclusion is
deliberately deflationary.

**The principle is textbook.** That transport-layer security does not provide application-layer
authorization, and that a broker which terminates TLS cannot vouch for a publisher, is standard
guidance in MQTT security practice and is stated in vendor and practitioner literature.

**The attack class is published.** Alsabbagh, Amogbonjaye, Kim and Langendörfer, *Pirates of
the MQTT: Raiding IIoT Systems with a Rogue Client* (IEEE CSNet 2024,
doi:10.1109/CSNET64211.2024.10851733) demonstrates precisely this: an adversary that connects
to an MQTT broker as a legitimate client and issues unauthorized commands to an industrial
system. Zeghida, Boulaiche and Chikh, *Security of MQTT Protocol: A Brief Overview* (TACC
2024, CEUR) likewise treats weak and leaked credentials as a cause of unauthorized access.

**The mitigation class is published, on this SoC, with this threat model.** Amirkhanova,
Ismailov, Amirkhanov, Adilzhanova, Zhasuzakova and Chen, *A Lightweight, End-to-End Encrypted
Data Pipeline for IIoT: An AES-GCM Implementation for ESP32, MQTT, and Raspberry Pi*
(*Information* 17(1):33, 2026, doi:10.3390/info17010033) implements application-layer
authenticated encryption on an ESP32 MQTT client explicitly so that the broker relays only
ciphertext it cannot read or alter undetected. Yu, Qi, Luo, Tian et al., *MQTT-L: a lightweight
end-to-end secure protocol with renewable hash chains for IoT environments* (*Journal of King
Saud University Computer and Information Sciences* 38(6):539, 2026,
doi:10.1007/s44443-026-00972-4) treats the broker as honest-but-curious and adds freshness and
hash-chain anchoring. *(The Springer landing page truncates the MQTT-L author list; the full
list is unverified and must be completed from the PDF before submission.)*

**Therefore this project claims none of the following:** a new vulnerability, a new attack, a
new mechanism, or novelty for HMAC-authenticated MQTT commands on an ESP32. Any such claim
would be false.

What survives as a contribution, stated at the size it deserves:

1. **A configuration-logic defect class, found by experiment, in a safety-critical FSM.** The
   published work above concerns adversaries attacking a *correctly understood* threat model.
   The defect here is different in kind: a compile-time guard that *appears* to enforce a
   security precondition, passes code review, produces no warning, and silently authorizes
   unauthenticated disarm. The finding is not "credentials can leak" but "this guard's
   predicate cannot support its conclusion, and the resulting build is one credential away from
   a disabled alarm." That is a defect in security *reasoning encoded as a build condition*,
   and it is the kind of thing a formal or systematic treatment is supposed to catch.
2. **A quantified link from a transport-security misconfiguration to loss of a safety
   property.** This paper's thesis is that the safety function stays live under adversarial
   network load. The credential-compromise arm is the **only** configuration among the six in
   which the alarm fails to fire at all. Every other attack — flooding at up to 20,000
   commands/s, forgery, replay — leaves the safety path intact. The contribution is the
   *contrast*: it locates the one place where the isolation argument does not hold, and shows
   that the breach is an authorization defect rather than a timing or resource failure.
3. **A fair baseline for the ablation.** This was the original reason for the arm. Without it,
   the comparison "HMAC beats the alternatives" was open to the objection that a realistic
   deployment would use TLS with broker credentials and need no application-layer
   authentication. The `transport` arm (0 successful disarms, alarm fires in every trial)
   shows that objection is *correct as long as credentials hold*, and the `transport_leaked`
   arm shows exactly where it stops being correct. The ablation is stronger for including a
   baseline that beats the weaker designs.

**Reviewer concern Q7 is therefore not simply resolved.** The added experiment removes the
baseline-fairness objection, which was Q7's substance, and that part is genuinely addressed.
But the experiment also establishes that the headline mechanism is not novel, which was never
Q7's claim and is not fixed by running more trials. Q7 is reassessed in `docs/Q2_GATE.md` on
that basis rather than marked resolved.

## 8. Threats to the validity of this section

- Every quantitative result is a **host simulation**. The TLS path in the host harness is a
  no-op shim (`WiFiClientSecure` is real in firmware, stubbed on the host), so no handshake,
  encryption overhead, latency, or throughput figure is or can be reported from it. The only
  TLS cost this project reports is **static flash and RAM measured by the real compiler** in CI.
- The credential-leak scenario is modelled as a boolean (`g_hasBrokerCreds`), i.e. broker
  admission succeeds or fails. It does not model how credentials leak, broker ACL topologies,
  per-client ACLs that might restrict a compromised client to a different topic, or detection
  and revocation. A deployment with correct per-client ACLs that forbid the compromised client
  from publishing to the command topic would not be vulnerable; that configuration is not
  modelled and the finding should not be read as applying to it.
- The adversary model excludes key compromise and flash readout by construction. Section 5
  states what that leaves unproven.
- `legit_cmd_accepted` was found to be unattributable in four of the six arms and the harness
  was corrected; see section 9.

## 9. A harness defect found while verifying this result

Verifying the first completed 1,800-trial dataset surfaced a measurement defect that had
nothing to do with the security finding, and it is recorded here because it affected published
numbers in an earlier revision of the ablation summary.

`legit_cmd_accepted` was inferred from an `exit_delay` event appearing in a 50 ms window after
the operator publishes `ARM` while the adversary floods. In every arm where the adversary's
commands are *admitted* — `none`, `ratelimit`, `token` after capture, and `transport_leaked` —
the adversary can itself publish a bare `ARM`. The metric therefore measured "someone armed the
system", not "the operator's command survived", and was only sound in the `transport` and
`hmac` arms. The symptom that exposed it was non-monotonic: apparent availability *rose* with
attack rate, because a denser adversary stream made a spurious `exit_delay` more likely inside
the window.

A second, related defect: the adversary could arm the system during the warmup window, after
which the operator's `ARM` was correctly ignored as redundant, which again had nothing to do
with availability.

The first correction suppressed the adversary's arm-capable commands during the attribution
window and returned the system quietly to `DISARMED` beforehand. **That fix introduced a second
artifact of its own, which is recorded here because the first re-run was discarded because of
it.** The quiet settle gave the token bucket 160 ms with no arrivals, which refilled it, and the
rate-limit design consequently admitted the operator's command in every trial — making the
limiter look better than it is. The symptom was that availability became 100 % in all six arms,
including the one design expected to harm it.

The final harness therefore holds the adversary's arm-capable commands for the whole trial
prologue instead of a single window. The adversary still floods at the full configured rate
throughout, draining the bucket and saturating the queues, but cannot itself arm, so the system
is `DISARMED` by construction and no quiet settle is needed.

A third problem survived both fixes: a single-command boolean is not an availability
measurement on this path. Instrumenting the token bucket at the instant of the operator's
publish showed its residue was 0.5 at 10 commands/s, 0.9 at 100, and 0.995 at 1,000 and above.
The explanation is that an arrival finding the bucket below the admission threshold is rejected
*without consuming a token*, so an extreme flood pins the bucket just under the threshold and
leaves it one millisecond of refill short of admitting; a moderate flood consumes tokens
whenever it finds them and leaves a lower residue. Whether one particular command is admitted
is therefore a function of bucket phase, and is not monotonic in attack intensity.

Availability is now measured as the proportion of **five** operator attempts, spaced 200 ms
apart, that reach the state machine, which is insensitive to that phase. The resulting
non-monotonicity is systematic and reproducible rather than a coin flip — 0 of 5 admitted at 10
and 100 commands/s, 5 of 5 at 1,000 and above — and is reported as a measured property of the
token-bucket design rather than smoothed away.

A fourth, purely mechanical defect was found while validating the retry loop: the inter-attempt
button reset initially held the pin for 40 ms, below the firmware's debounce window, so the
reset silently never happened and attempts 2–5 were evaluated from the wrong state, yielding
1 of 5 in every arm including the undefended one. The hold is now 80 ms.

The full campaign was re-run from scratch after the final harness revision, and only that
dataset is reported. **The headline results of section 3 are unaffected by all four defects**,
because they rest on `attacker_disarmed` and `reached_alarm`, which are read from directly
observed events carrying explicit source tags and were never inferred. Every defect above
affected the availability column only.

The sequence is recorded in this much detail deliberately. Three of the four defects produced
*plausible* numbers, and two of them produced numbers that flattered the conclusion the
experiment was built to support. The non-monotonicity that exposed the first defect was visible
only because the results were broken out by attack rate rather than aggregated.
