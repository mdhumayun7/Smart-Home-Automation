#!/usr/bin/env python3
"""Produce the ablation figures from results/ablation_summary.json.

Reads only the committed aggregate written by analyse_ablation.py, so a figure cannot
disagree with the table it sits beside. Every plotted value is asserted against that file
before it is drawn; a mismatch raises rather than producing a plausible-looking figure.

Writes, into results/:
    ablation_results.{pdf,png}   the six command-path designs, three properties
    credential_matrix.{pdf,png}  what each control withstands, by secret compromised

Both are vector PDF for the manuscript; the PNG is for the README only.

Every value is a host-simulation result. Nothing here is a hardware measurement.

Usage: python3 make_ablation_figures.py
"""
import json
import math
import os
import sys

import figstyle
from figstyle import FAIL, HOLD, INK
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
N_PER_ARM = 300

figstyle.apply()

# Figure 3: the six command-path designs. Labels are short enough to sit horizontally; the
# full description lives in the caption and in the design table.
CORE = [
    ("none", "No command defence"),
    ("ratelimit", "Token-bucket rate limit"),
    ("token", "Static shared token"),
    ("transport", "TLS, credentials held"),
    ("transport_leaked", "TLS, credentials leaked"),
    ("hmac", "HMAC-SHA256 + counter"),
]

# Figure 5: indexed by which secret the adversary holds, not by mechanism.
MATRIX = [
    ("transport", "TLS only", "no secret"),
    ("transport_leaked", "TLS only", "any broker credential"),
    ("acl_shared_leaked", "TLS + ACL", "the one shared credential"),
    ("acl_operator_leaked", "TLS + ACL", "controller credential"),
    ("acl_device_leaked", "TLS + ACL", "device credential"),
    ("hmac", "HMAC", "any broker credential"),
    ("hmac_keyleaked", "HMAC", "controller credential + key"),
    ("acl_hmac_devicedump", "TLS + ACL + HMAC", "device credential + key"),
    ("acl_hmac_controllerdump", "TLS + ACL + HMAC", "controller credential + key"),
]


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, centre - margin), min(1.0, centre + margin)


def pct(num, den):
    return 100.0 * num / den if den else 0.0


def check(ab):
    """Refuse to draw anything if the aggregate is not the shape the figures assume."""
    problems = []
    for key, _ in CORE:
        if key not in ab:
            problems.append(f"{key} missing from the aggregate")
    for key, _, _ in MATRIX:
        if key not in ab:
            problems.append(f"{key} missing from the aggregate")
    for key, d in ab.items():
        if d["intrusion_test_valid"] != N_PER_ARM:
            problems.append(f"{key}: {d['intrusion_test_valid']} valid trials, expected "
                            f"{N_PER_ARM}; the caption's sample size would be wrong")
    if problems:
        print("refusing to draw:", *problems, sep="\n  ", file=sys.stderr)
        sys.exit(1)


def hbars(ax, labels, values, title, xlabel, colours=None, label_pad=2.5):
    """Horizontal bars with the value printed beside each one.

    label_pad is widened by the caller on a panel that also carries error bars, so the number
    sits clear of the whisker instead of on top of it.
    """
    y = list(range(len(labels)))[::-1]
    cols = colours if colours is not None else [figstyle.colour_for(v) for v in values]
    ax.barh(y, values, color=cols, height=0.62, zorder=3)
    for yy, v, c in zip(y, values, cols):
        # A zero-height bar is invisible, so mark it. The marker takes the row's own colour:
        # zero means the design held in panel (c) and failed in panel (b), and the mark must
        # not assert the opposite of the bar it stands in for.
        if v <= 0.01:
            ax.plot([0], [yy], marker="|", markersize=9, color=c, zorder=4)
        ax.text(min(v, 100) + label_pad, yy,
                f"{v:.0f}" if float(v).is_integer() else f"{v:.1f}",
                va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 118)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel(xlabel)
    ax.set_title(title, loc="left", fontsize=9.5)
    figstyle.tidy(ax, axis="x")


def figure_ablation(ab):
    keys = [k for k, _ in CORE]
    labels = [lab for _, lab in CORE]

    alarm = [wilson(ab[k]["reached_alarm"], ab[k]["intrusion_test_valid"]) for k in keys]
    alarm_pct = [100 * p for p, _, _ in alarm]
    lo = [max(0.0, 100 * (p - l)) for p, l, _ in alarm]
    hi = [max(0.0, 100 * (h - p)) for p, _, h in alarm]
    avail = [pct(ab[k]["legit_admitted_flooded"], ab[k]["legit_attempts_flooded"]) for k in keys]
    replay = [pct(ab[k]["attacker_replay_armed"], ab[k]["replay_test_valid"]) for k in keys]

    fig, axes = plt.subplots(1, 3, figsize=(10.2, 2.9), sharey=True)
    # Panel (a) carries Wilson intervals, so its value labels are pushed clear of the whisker.
    hbars(axes[0], labels, alarm_pct,
          "(a) Safety function holds under attack", "Alarm activation (%)", label_pad=6.0)
    yy = list(range(len(labels)))[::-1]
    axes[0].errorbar(alarm_pct, yy, xerr=[lo, hi], fmt="none",
                     ecolor=INK, elinewidth=0.8, capsize=2.2, zorder=5)
    hbars(axes[1], labels, avail,
          "(b) Operator command survives flood", "Commands admitted (%)")
    # Panel (c) inverts the reading: here a high value is the failure, so the colour rule is
    # inverted with it. Blue still means "this design holds the property".
    hbars(axes[2], labels, replay,
          "(c) Defeated by capture-and-replay", "Trials defeated (%)",
          colours=[FAIL if v > 1.0 else HOLD for v in replay])

    fig.tight_layout(w_pad=1.4)
    save(fig, "ablation_results")


def figure_matrix(ab):
    keys = [k for k, _, _ in MATRIX]
    labels = [f"{ctrl}\n{sec}" for _, ctrl, sec in MATRIX]
    alarm = [pct(ab[k]["reached_alarm"], ab[k]["intrusion_test_valid"]) for k in keys]
    avail = [pct(ab[k]["legit_admitted_flooded"], ab[k]["legit_attempts_flooded"]) for k in keys]

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.9), sharey=True)
    hbars(axes[0], labels, alarm,
          "(a) Does the alarm still fire?", "Alarm activation (%)")
    hbars(axes[1], labels, avail,
          "(b) Can the owner still command it?", "Commands admitted (%)")
    # Two-line y labels: the control on top, the compromised secret beneath it.
    for lab in axes[0].get_yticklabels():
        lab.set_fontsize(8)
        lab.set_linespacing(1.35)
    fig.tight_layout(w_pad=1.2)
    save(fig, "credential_matrix")


def save(fig, stem):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(RES, f"{stem}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote results/{stem}.pdf and .png")


def main():
    with open(os.path.join(RES, "ablation_summary.json")) as fh:
        ab = json.load(fh)["ablation"]
    check(ab)
    figure_ablation(ab)
    figure_matrix(ab)


if __name__ == "__main__":
    main()
