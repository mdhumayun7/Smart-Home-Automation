#!/usr/bin/env python3
"""Check every value plotted in the generated figures against the raw per-trial records.

The figures are drawn from results/ablation_summary.json. That file is itself produced by
analyse_ablation.py, so checking a figure against it would only prove that one derived file
agrees with another. This script goes back to results/ablation.jsonl, recomputes each
quantity from the per-trial records, and compares it with what the figure code would draw.

It also re-reads the numbers that appear as text inside the hand-drawn diagrams, which have
no data pipeline at all and are the easiest place for a stale figure to survive a change.

Exit status is non-zero on any mismatch, so this can gate a build.

Usage: python3 -I validate_figures.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
IMAGES = os.path.join(HERE, "..", "docs", "images")
N_PER_ARM = 300

problems = []


def ok(cond, what, got=None):
    print(f"  {'ok  ' if cond else 'FAIL'} {what}" + ("" if cond else f"   got: {got}"))
    if not cond:
        problems.append(what)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - m), min(1.0, c + m)


def main():
    rows = [json.loads(l) for l in open(os.path.join(RES, "ablation.jsonl")) if l.strip()]
    summary = json.load(open(os.path.join(RES, "ablation_summary.json")))["ablation"]

    print(f"raw records: {len(rows)}")
    by = {}
    for r in rows:
        by.setdefault(r["mode"], []).append(r)

    print("\n1. the aggregate the figures read agrees with the raw records")
    for mode, rs in sorted(by.items()):
        s = summary[mode]
        iv = [r for r in rs if r["intrusion_test_valid"]]
        fl = [r for r in rs if r["attack_rate"] > 0 and r["avail_test_valid"]]
        rv = [r for r in rs if r["replay_test_valid"] and r["attack_rate"] > 0]
        checks = [
            (len(rs) == N_PER_ARM, "trials"),
            (s["intrusion_test_valid"] == len(iv), "intrusion_test_valid"),
            (s["reached_alarm"] == sum(1 for r in iv if r["reached_alarm"]), "reached_alarm"),
            (s["legit_admitted_flooded"] == sum(r["legit_admitted"] for r in fl),
             "legit_admitted_flooded"),
            (s["legit_attempts_flooded"] == sum(r["legit_attempts"] for r in fl),
             "legit_attempts_flooded"),
            (s["replay_test_valid"] == len(rv), "replay_test_valid"),
            (s["attacker_replay_armed"] == sum(1 for r in rv if r["attacker_replay_armed"]),
             "attacker_replay_armed"),
            (s["attacker_disarmed"] == sum(1 for r in rs if r["attacker_disarmed"]),
             "attacker_disarmed"),
        ]
        bad = [name for good, name in checks if not good]
        ok(not bad, f"{mode}", bad)

    print("\n2. values the figures plot, recomputed from the raw records")
    want = {
        "none": (100.0, 100.0, 100.0),
        "ratelimit": (100.0, 59.0, 100.0),
        "token": (100.0, 100.0, 100.0),
        "transport": (100.0, 100.0, 0.0),
        "transport_leaked": (16.7, 100.0, 100.0),
        "hmac": (100.0, 100.0, 0.0),
        "hmac_keyleaked": (16.7, 0.0, None),
        "acl_device_leaked": (100.0, 100.0, None),
        "acl_hmac_devicedump": (100.0, 100.0, None),
        "acl_hmac_controllerdump": (16.7, 0.0, None),
        "acl_shared_leaked": (16.7, 100.0, None),
        "acl_operator_leaked": (16.7, 100.0, None),
    }
    for mode, (w_alarm, w_avail, w_replay) in sorted(want.items()):
        rs = by[mode]
        iv = [r for r in rs if r["intrusion_test_valid"]]
        fl = [r for r in rs if r["attack_rate"] > 0 and r["avail_test_valid"]]
        rv = [r for r in rs if r["replay_test_valid"] and r["attack_rate"] > 0]
        alarm = 100 * sum(1 for r in iv if r["reached_alarm"]) / len(iv)
        avail = 100 * sum(r["legit_admitted"] for r in fl) / sum(r["legit_attempts"] for r in fl)
        ok(abs(alarm - w_alarm) < 0.05, f"{mode}: alarm {w_alarm}%", round(alarm, 2))
        ok(abs(avail - w_avail) < 0.05, f"{mode}: availability {w_avail}%", round(avail, 2))
        if w_replay is not None:
            rep = 100 * sum(1 for r in rv if r["attacker_replay_armed"]) / len(rv)
            ok(abs(rep - w_replay) < 0.05, f"{mode}: replay {w_replay}%", round(rep, 2))

    print("\n3. the Wilson interval drawn on Figure 3, panel (a)")
    s = summary["transport_leaked"]
    lo, hi = wilson(s["reached_alarm"], s["intrusion_test_valid"])
    ok((round(lo * 100, 1), round(hi * 100, 1)) == (12.9, 21.3),
       "transport_leaked 95% Wilson [12.9, 21.3]", (round(lo * 100, 1), round(hi * 100, 1)))

    print("\n4. numbers hard-coded inside the hand-drawn diagrams")
    # These SVGs carry counts as literal text. A figure that quotes a stale count is the
    # failure mode this section exists to catch.
    expect_in = {
        "security_paths.svg": [
            ("300/300", summary["hmac"]["reached_alarm"] == 300),
            ("50/300", summary["transport_leaked"]["reached_alarm"] == 50),
        ],
    }
    for fname, pairs in expect_in.items():
        path = os.path.join(IMAGES, fname)
        if not os.path.exists(path):
            ok(False, f"{fname} exists", "missing")
            continue
        text = open(path, errors="replace").read()
        for literal, data_agrees in pairs:
            ok(literal in text and data_agrees,
               f"{fname} quotes {literal} and the data agrees")

    print("\n5. no diagram hard-codes a table or figure number")
    # A cross-reference baked into artwork goes stale the moment a table is inserted above
    # it, and LaTeX cannot catch it. Numbering belongs in the caption, via \\ref.
    import re
    for fname in sorted(os.listdir(IMAGES)):
        if not fname.endswith(".svg"):
            continue
        text = open(os.path.join(IMAGES, fname), errors="replace").read()
        hits = re.findall(r"(?:Table|Figure|Fig\.)\s*\d+", text)
        ok(not hits, f"{fname} carries no baked-in cross-reference", hits)

    print("\n6. generated figure files are present and non-trivial")
    for stem in ("ablation_results", "credential_matrix"):
        p = os.path.join(RES, f"{stem}.pdf")
        ok(os.path.exists(p) and os.path.getsize(p) > 5000, f"{stem}.pdf written")

    print()
    if problems:
        print(f"{len(problems)} mismatch(es): {problems}")
        return 1
    print("every plotted and quoted value matches the raw records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
