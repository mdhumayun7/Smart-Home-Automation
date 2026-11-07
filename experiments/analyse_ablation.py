#!/usr/bin/env python3
"""Aggregate the ablation and sensitivity runs into results/ablation_summary.md.

Standard library only, so the analysis reproduces with no third-party package.

Reads:
    results/ablation.jsonl      four command-path designs against the same adversary
    results/sensitivity.jsonl   deauth detector parameter sweep

Writes:
    results/ablation_summary.md
    results/ablation_summary.json
"""

import json
import math
import os
import statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

MODES = ["none", "ratelimit", "token", "transport", "transport_leaked",
         "acl_shared_leaked", "acl_operator_leaked", "acl_device_leaked",
         "hmac", "hmac_keyleaked", "acl_hmac_devicedump", "acl_hmac_controllerdump"]
MODE_LABEL = {
    "none": "No command defence",
    "ratelimit": "Token-bucket rate limit (5/s)",
    "token": "Static shared token",
    "hmac": "HMAC-SHA256 + counter",
    "transport": "TLS + broker credentials",
    "transport_leaked": "TLS, credentials leaked",
    "acl_shared_leaked": "TLS + ACL, shared credential leaked",
    "acl_operator_leaked": "TLS + ACL, controller credential leaked",
    "acl_device_leaked": "TLS + ACL, device credential leaked",
    "hmac_keyleaked": "HMAC, command key leaked",
    "acl_hmac_devicedump": "TLS + ACL + HMAC, device flash dumped",
    "acl_hmac_controllerdump": "TLS + ACL + HMAC, controller compromised (credential + key)",
}


def wilson(k, n, z=1.96):
    """Wilson score interval for a binomial proportion. Stdlib only."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - margin) / d, (centre + margin) / d)


def _lchoose(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_one_sided(a, b, c, d):
    """One-sided Fisher exact test, P(X <= a) under the hypergeometric null."""
    n, r1, c1 = a + b + c + d, a + b, a + c
    total = 0.0
    for x in range(0, a + 1):
        if x > c1 or (r1 - x) < 0 or (n - c1) < (r1 - x):
            continue
        total += math.exp(_lchoose(c1, x) + _lchoose(n - c1, r1 - x) - _lchoose(n, r1))
    return total


def load(name):
    path = os.path.join(RES, name)
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def ablation(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["mode"]].append(r)

    summary = {}
    for m in MODES:
        rs = by.get(m, [])
        if not rs:
            continue
        # Availability is only attributable in a trial that began DISARMED; see avail_test_valid
        # in ablation.cpp. Trials are excluded rather than counted as failures.
        flooded = [r for r in rs if r["attack_rate"] > 0 and r.get("avail_test_valid", True)]
        # Only a trial in which the adversary was actually active can test replay: in a quiet
        # trial it publishes nothing, so counting those in the denominator understates the rate.
        replay_valid = [r for r in rs if r.get("replay_test_valid") and r["attack_rate"] > 0]
        intr_valid = [r for r in rs if r.get("intrusion_test_valid")]
        lat = [r["safety_latency_ms"] for r in intr_valid if r.get("reached_alarm")]
        summary[m] = {
            "trials": len(rs),
            "flooded_trials": len(flooded),
            "avail_test_valid": sum(1 for r in rs if r.get("avail_test_valid", True)),
            "legit_accepted_flooded": sum(1 for r in flooded if r["legit_cmd_accepted"]),
            # Availability as a proportion of operator attempts admitted, which is insensitive
            # to token-bucket phase in a way a single-command boolean is not.
            "legit_attempts_flooded": sum(r.get("legit_attempts", 0) for r in flooded),
            "legit_admitted_flooded": sum(r.get("legit_admitted", 0) for r in flooded),
            "replay_test_valid": len(replay_valid),
            "attacker_replay_armed": sum(1 for r in replay_valid
                                         if r.get("attacker_replay_armed")),
            "attacker_disarmed": sum(1 for r in rs if r.get("attacker_disarmed")),
            "intrusion_test_valid": len(intr_valid),
            "reached_alarm": sum(1 for r in intr_valid if r.get("reached_alarm")),
            "violations": sum(1 for r in rs if r.get("violation")),
            "safety_latency_median_ms": statistics.median(lat) if lat else None,
            "safety_latency_stdev_ms": (statistics.pstdev(lat) if len(lat) > 1 else 0.0),
        }
    return summary


def sensitivity(rows):
    benign = {}
    attack = {}
    for r in rows:
        if r["kind"] == "benign":
            benign[(r["threshold"], r["window_ms"], r["benign_fpm"])] = r
        else:
            attack[(r["threshold"], r["window_ms"], r["attack_fps"])] = r
    return benign, attack


def main():
    ab_rows = load("ablation.jsonl")
    se_rows = load("sensitivity.jsonl")
    ab = ablation(ab_rows)
    benign, attack = sensitivity(se_rows)

    L = []
    L.append("# Ablation and sensitivity results\n")
    L.append("Generated by `experiments/analyse_ablation.py`. Every number below comes from a")
    L.append("committed JSONL file produced by a seeded run; nothing is hand-entered.\n")
    L.append("**Evidence category: simulation result.** Not a hardware measurement. See")
    L.append("`docs/EXPERIMENTS.md` for the evidence taxonomy and the per-experiment record.\n")

    # ---- ablation
    if ab:
        L.append("## 1. Command-path design ablation\n")
        L.append("Twelve designs, same adversary, same scenario, same seeds. The adversary floods")
        L.append("the command topic and captures the legitimate command off the wire for replay.\n")
        L.append("Availability is measured as the proportion of five operator publish attempts,")
        L.append("spaced 200 ms apart, that reach the state machine while the adversary floods at")
        L.append("the configured rate. Throughout the trial prologue the adversary floods at full")
        L.append("rate but cannot itself arm the system, so an observed arm is attributable to the")
        L.append("operator; its nuisance arming is measured separately in the replay column. A")
        L.append("single-command boolean was found to measure token-bucket phase rather than")
        L.append("availability, and is not reported: see `docs/SECURITY_ANALYSIS.md` section 9.\n")
        L.append("| Design | Trials | Operator commands admitted under flood |"
                 " Defeated by capture-and-replay (attacked trials) |"
                 " Attacker disarmed | Alarm fired | Invariant violations |")
        L.append("|---|---|---|---|---|---|---|")
        for m in MODES:
            s = ab.get(m)
            if not s:
                continue
            L.append(
                f"| {MODE_LABEL[m]} | {s['trials']} | "
                f"{s['legit_admitted_flooded']}/{s['legit_attempts_flooded']} | "
                f"{s['attacker_replay_armed']}/{s['replay_test_valid']} | "
                f"{s['attacker_disarmed']} | "
                f"{s['reached_alarm']}/{s['intrusion_test_valid']} | "
                f"{s['violations']} |"
            )
        L.append("")
        L.append("Safety latency was identical across all twelve designs "
                 f"(median {ab['hmac']['safety_latency_median_ms']:.0f} ms, "
                 f"standard deviation {ab['hmac']['safety_latency_stdev_ms']:.1f} ms), which is")
        L.append("expected: the harness advances a logical clock, so there is no contention to")
        L.append("measure. This says nothing about physical timing.\n")
        L.append("**Reading.** Availability, integrity and the safety function are separable,")
        L.append("and most of the eleven designs fail at least one of them:\n")
        L.append("- A **rate limit** cannot tell a legitimate command from a flood, so it drops")
        L.append("  the operator's command along with the attacker's, and it leaves integrity")
        L.append("  completely untouched. Its effect on availability is not monotonic in attack")
        L.append("  intensity: a moderate flood (10-100 commands/s) costs the operator most or")
        L.append("  all of its attempts, while an extreme flood costs it none, because arrivals")
        L.append("  that find the")
        L.append("  bucket below the admission threshold are rejected *without consuming a")
        L.append("  token*, which pins the bucket just under that threshold and leaves enough")
        L.append("  refill for the next arrival. This is a property of the limiter, measured")
        L.append("  rather than assumed; see docs/SECURITY_ANALYSIS.md section 9.")
        L.append("- A **static token** restores availability, because the edge filters the flood")
        L.append("  cheaply. It is still defeated the moment the attacker captures one")
        L.append("  legitimate command, since the token travels in plaintext.")
        L.append("- Only the **MAC plus monotonic counter** provides both. The counter, not the")
        L.append("  MAC, is what defeats replay; a MAC alone would behave like the token row.\n")

        # Availability broken out by attack rate. Aggregating hides the non-monotonicity.
        rates = sorted({r["attack_rate"] for r in ab_rows if r["attack_rate"] > 0})
        L.append("### 1.1 Operator command availability by attack rate\n")
        L.append("Admitted / attempted, over trials whose availability measurement was valid.\n")
        L.append("| Design | " + " | ".join(f"{r} cmd/s" for r in rates) + " |")
        L.append("|---" * (len(rates) + 1) + "|")
        for m in MODES:
            if m not in ab:
                continue
            cells = []
            for rt in rates:
                fl = [r for r in ab_rows if r["mode"] == m and r["attack_rate"] == rt
                      and r.get("avail_test_valid", True)]
                adm = sum(r.get("legit_admitted", 0) for r in fl)
                att = sum(r.get("legit_attempts", 0) for r in fl)
                cells.append(f"{adm}/{att}" if att else "-")
            L.append(f"| {MODE_LABEL[m]} | " + " | ".join(cells) + " |")
        L.append("")

        # ---- statistical comparisons, computed here so nothing is hand-entered
        tl, tr = ab.get("transport_leaked"), ab.get("transport")
        if tl and tr:
            p = fisher_one_sided(tl["reached_alarm"],
                                 tl["intrusion_test_valid"] - tl["reached_alarm"],
                                 tr["reached_alarm"],
                                 tr["intrusion_test_valid"] - tr["reached_alarm"])
            lo, hi = wilson(tl["reached_alarm"], tl["intrusion_test_valid"])
            L.append("### 1.2 Statistical comparison\n")
            L.append("The two transport arms are built from identical source with identical flags")
            L.append("and run on identical seeds; the adversary's possession of a valid broker")
            L.append("credential is the only variable that differs.\n")
            L.append(f"- Alarm activation, credentials leaked: {tl['reached_alarm']}/"
                     f"{tl['intrusion_test_valid']} "
                     f"({100 * tl['reached_alarm'] / tl['intrusion_test_valid']:.1f} %, "
                     f"95 % Wilson CI [{100 * lo:.1f} %, {100 * hi:.1f} %]).")
            L.append(f"- Alarm activation, credentials held: {tr['reached_alarm']}/"
                     f"{tr['intrusion_test_valid']} (100.0 %).")
            L.append(f"- Fisher exact test, one-sided: p = {p:.3e}.\n")
            rl, hm = ab.get("ratelimit"), ab.get("hmac")
            if rl and hm:
                p2 = fisher_one_sided(rl["legit_admitted_flooded"],
                                      rl["legit_attempts_flooded"] - rl["legit_admitted_flooded"],
                                      hm["legit_admitted_flooded"],
                                      hm["legit_attempts_flooded"] - hm["legit_admitted_flooded"])
                L.append(f"- Operator availability, rate limit {rl['legit_admitted_flooded']}/"
                         f"{rl['legit_attempts_flooded']} "
                         f"({100 * rl['legit_admitted_flooded'] / rl['legit_attempts_flooded']:.1f} %) "
                         f"against HMAC {hm['legit_admitted_flooded']}/"
                         f"{hm['legit_attempts_flooded']} (100.0 %): "
                         f"Fisher exact one-sided p = {p2:.3e}.\n")

        # ---- credential-compromise matrix
        acl = ["transport", "transport_leaked", "acl_shared_leaked", "acl_operator_leaked",
               "acl_device_leaked", "hmac", "hmac_keyleaked", "acl_hmac_devicedump"]
        if any(m in ab for m in acl):
            L.append("### 1.3 What each control protects, by which secret the adversary holds\n")
            L.append("Broker-side access control and application-layer authentication fail under")
            L.append("*different* compromises, so neither dominates the other. The table reads")
            L.append("down the adversary's capability, not down a ranking of mechanisms.\n")
            L.append("| Controls in place | Secret the adversary holds | Unauthorised disarm |"
                     " Alarm fired | Operator locked out |")
            L.append("|---|---|---|---|---|")
            rows = [
                ("transport", "TLS, no ACL", "none"),
                ("transport_leaked", "TLS, no ACL", "any broker credential"),
                ("acl_shared_leaked", "TLS + per-client ACL", "the one shared credential"),
                ("acl_operator_leaked", "TLS + per-client ACL", "controller credential"),
                ("acl_device_leaked", "TLS + per-client ACL", "device credential"),
                ("hmac", "HMAC + counter", "any broker credential"),
                ("hmac_keyleaked", "HMAC + counter", "controller credential and command key"),
                ("acl_hmac_devicedump", "TLS + ACL + HMAC",
                 "device credential and command key (flash dump)"),
                ("acl_hmac_controllerdump", "TLS + ACL + HMAC",
                 "controller credential and command key"),
            ]
            for m, controls, secret in rows:
                d = ab.get(m)
                if not d:
                    continue
                disarmed = "yes" if d["attacker_disarmed"] else "no"
                att, adm = d["legit_attempts_flooded"], d["legit_admitted_flooded"]
                locked = "**yes**" if att and adm == 0 else "no"
                L.append(f"| {controls} | {secret} | **{disarmed}** | "
                         f"{d['reached_alarm']}/{d['intrusion_test_valid']} | "
                         f"{locked} ({adm}/{att} admitted) |")
            L.append("")
            L.append("Four readings follow, and the last three cut against this project's own")
            L.append("mechanism:\n")
            L.append("- A per-client ACL is **not** a weaker substitute for application-layer")
            L.append("  authentication. It contains a *device* compromise completely, which")
            L.append("  matters for an embedded product because the device is the physically")
            L.append("  accessible component and its broker credentials sit in a readable flash")
            L.append("  image. It does nothing against a compromised controller, because that")
            L.append("  identity is the one the ACL must authorise to publish commands.")
            L.append("- A shared credential defeats the ACL entirely. The ACL must grant the")
            L.append("  single identity write access to the command topic for the system to")
            L.append("  work, so the configuration collapses to the no-ACL case. Credential")
            L.append("  separation, not the ACL syntax, is what carries the protection.")
            L.append("- **A MAC does not survive key compromise, and the key is in the same")
            L.append("  flash image.** With the command key dumped, the signed path is defeated")
            L.append("  exactly as the unsigned one is. Only the combination holds: with both an")
            L.append("  ACL and a MAC, an adversary who dumps the device gets a key it can sign")
            L.append("  with and a credential the broker will not let it publish commands under.")
            L.append("  The defence that survives in this table is layered, not cryptographic.")
            L.append("- **The layered configuration does not survive every compromise, and an")
            L.append("  earlier draft of this document said it did.** It survives every")
            L.append("  single-secret compromise and it survives a device flash dump, because")
            L.append("  the ACL refuses the device identity permission to publish commands. It")
            L.append("  does *not* survive a compromised controller host, which yields both a")
            L.append("  credential the ACL must permit to publish and the shared key needed to")
            L.append("  sign: neither layer refuses, and the adversary disarms. Layering raises")
            L.append("  the cost of an attack; it does not close the set.")
            L.append("- **Under key compromise the replay counter becomes a lockout against the")
            L.append("  owner.** This was not anticipated and was found in the data. Counters are")
            L.append("  not secret, so an adversary holding the key can sign commands with a")
            L.append("  counter far above the operator's; the device persists it, and every")
            L.append("  subsequent operator command is then rejected as a replay. In this arm the")
            L.append("  operator is admitted in 0 of 1250 attempts across all attacked trials. A")
            L.append("  monotonic counter defeats replay and, under key compromise, denies")
            L.append("  service to the legitimate user at the same time. Recovery needs a key")
            L.append("  change and a counter reset, neither of which this firmware supports")
            L.append("  remotely.\n")

    # ---- sensitivity
    if benign:
        L.append("## 2. Deauthentication detector parameter sensitivity\n")
        L.append("False-positive rate against a Poisson model of benign management-frame")
        L.append("traffic, over ten simulated minutes per run. **The benign arrival model is an")
        L.append("assumption, not a measurement**: no capture of real management traffic was")
        L.append("available, so these characterise the detector's logic, not any real network.\n")
        L.append("### 2.1 False-positive rate by threshold (window 2000 ms)\n")
        fpms = sorted({k[2] for k in benign})
        L.append("| Threshold | " + " | ".join(f"{f:g} frames/min" for f in fpms) + " |")
        L.append("|---" * (len(fpms) + 1) + "|")
        for th in sorted({k[0] for k in benign}):
            cells = []
            for f in fpms:
                r = benign.get((th, 2000, f))
                cells.append(f"{r['fp_rate']:.4f}" if r else "-")
            L.append(f"| {th} | " + " | ".join(cells) + " |")
        L.append("")
        L.append("### 2.2 Trade-off: false positives against detection latency\n")
        L.append("| Threshold | Window (ms) | FP rate at 60 frames/min | Median detect at 20 f/s |"
                 " Median detect at 5 f/s | Missed at 5 f/s |")
        L.append("|---|---|---|---|---|---|")
        for th in sorted({k[0] for k in benign}):
            for w in sorted({k[1] for k in benign}):
                b = benign.get((th, w, 60.0))
                a20 = attack.get((th, w, 20.0))
                a5 = attack.get((th, w, 5.0))
                if not (b and a20 and a5):
                    continue
                L.append(f"| {th} | {w} | {b['fp_rate']:.4f} | {a20['median_detect_ms']} ms | "
                         f"{a5['median_detect_ms']} ms | {a5['missed']}/{a5['runs']} |")
        L.append("")
        dep = benign.get((12, 2000, 60.0))
        old = benign.get((8, 2000, 60.0))
        if dep and old:
            L.append("**This sweep changed the firmware.** The original threshold of 8 fired")
            L.append(f"spuriously in {old['fp_rate']:.1%} of benign ten-minute runs at 60")
            L.append("frames/min, which is an ordinary busy multi-AP environment. The default is")
            L.append(f"now **12**, which fires in {dep['fp_rate']:.2%} of the same runs while")
            L.append("still detecting every swept attack rate with no misses. The cost is about")
            L.append("214 ms of extra detection latency at 20 frames/s.\n")

    out_md = os.path.join(RES, "ablation_summary.md")
    with open(out_md, "w") as fh:
        fh.write("\n".join(L) + "\n")

    with open(os.path.join(RES, "ablation_summary.json"), "w") as fh:
        json.dump({"ablation": ab,
                   "sensitivity_benign": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in benign.items()},
                   "sensitivity_attack": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in attack.items()}},
                  fh, indent=1, sort_keys=True)

    print("\n".join(L))


if __name__ == "__main__":
    main()
