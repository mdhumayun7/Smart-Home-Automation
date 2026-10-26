# Threat Model

This document states what the Smart Home Surveillance System protects, who it defends
against, and how each threat is handled. It follows the structure of a standard security
analysis (assets, adversary, attack surface, threats and mitigations) and is the reference
for the evaluation in [EVALUATION.md](EVALUATION.md) and the deployment steps in
[HARDENING.md](HARDENING.md).

## 1. Assets

| Asset | Why it matters |
|---|---|
| Availability of detection and the local siren | The core function. If it stops, an intrusion goes unannounced. |
| Integrity of the armed/disarmed state | Only the legitimate occupant may disarm. |
| Authenticity of alerts | A consumer must be able to trust that an alert came from the real device. |
| Confidentiality of events | Event traffic reveals occupancy patterns (when the house is empty). |
| The shared keys and credentials | Compromise defeats command authentication and encryption. |

## 2. Adversary model

Three adversaries of increasing capability are considered.

- **A1 - Network eavesdropper / spoofer.** On the same LAN or able to reach the broker.
  Can read unencrypted MQTT, publish to topics, and replay captured messages. Cannot break
  modern cryptography.
- **A2 - Radio attacker.** Within Wi-Fi range. Can transmit 802.11 management frames
  (deauthentication / disassociation floods) and can jam the 2.4 GHz band. Does not have the
  Wi-Fi password.
- **A3 - Opportunistic physical attacker.** Brief physical access near the device: can cut
  mains power or attempt to cover a sensor. Not a well-resourced attacker who can desolder
  flash and extract secrets at leisure (that is out of scope and noted as a limitation).

Out of scope: supply-chain compromise, a nation-state attacker with unlimited physical
access, and side-channel key extraction.

## 3. Attack surface

1. The MQTT command topic (`.../cmd`) - anyone who can publish to the broker.
2. The MQTT event/state topics - anyone who can subscribe.
3. The Wi-Fi link between the device and the access point.
4. The ESP-NOW fallback channel.
5. The mains supply and the physical sensors.
6. The firmware image and the stored secrets (NVS, flash).

## 4. Threats and mitigations

The mitigations marked "v2.2" are implemented in this repository; those marked "deploy" are
configuration steps in [HARDENING.md](HARDENING.md); those marked "future" are on the roadmap.

| # | Threat (STRIDE) | Adversary | Mitigation | Status |
|---|---|---|---|---|
| T1 | Spoofing: forge a `DISARM` command | A1 | HMAC-SHA256 tag over the command; a forged tag is rejected (`cmd_badmac`) | v2.2 |
| T2 | Tampering/Replay: resend a captured signed `DISARM` | A1 | Strictly increasing per-command counter, persisted in NVS (`cmd_replay`) | v2.2 |
| T3 | Information disclosure: read events to learn occupancy | A1 | TLS to a private broker; topic ACLs | deploy |
| T4 | Denial of service: deauth/disassoc flood to drop the link | A2 | Passive flood detection (`wifi_deauth`); alarm runs offline; ESP-NOW fallback alert | v2.2 |
| T5 | Denial of service: knock the device offline silently | A2 | `link_lost` event while armed; broker Last Will; "silence is itself an alarm" at the consumer | v2.2 |
| T6 | Denial of service: wideband 2.4 GHz jamming | A2 | Local siren is fully independent of radio; honest limitation: a wideband jammer also blocks ESP-NOW | partial |
| T7 | Tampering: cut mains power while armed to disarm | A3 | Armed state restored from NVS on reboot; door-open at power-up triggers entry delay | v2.2 |
| T8 | Spoofing: inject fake ESP-NOW alerts to cause alarm fatigue | A1/A2 | ESP-NOW alerts are HMAC-authenticated and counter-checked | v2.2 |
| T9 | Tampering: firmware hang | - | Task watchdog resets and reports the reset reason | v2.1 |
| T10 | Elevation: extract keys from the firmware image | A3 | No secrets in source (`secrets.h` git-ignored); flash encryption and secure boot | future |
| T11 | Tampering: malicious firmware update | A3 | Signed OTA with image verification | future |
| T12 | Tampering: cover or blind the PIR | A3 | PIR + mmWave radar fusion raises the bar; a true anti-mask sensor is future work | partial |

## 5. Security properties verified

Two of the safety/security claims are machine-checked, not only tested:

- The alarm state machine and the authenticated-command path are modelled in TLA+
  ([formal/AlarmFSM.tla](../formal/AlarmFSM.tla)) and TLC proves, over the whole state space,
  that an unauthenticated remote command never disarms the system, that the replay counter
  never decreases, and that the entry delay and the alarm always resolve.
- The command and alert authentication logic is unit-tested against RFC 4231 / FIPS 180-4
  known-answer vectors and cross-checked between the Python signer and the firmware verifier.

The quantitative evaluation of each threat under attack is in [EVALUATION.md](EVALUATION.md).
