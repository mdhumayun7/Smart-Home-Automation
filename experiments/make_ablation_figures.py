#!/usr/bin/env python3
"""Produce the ablation figures from results/ablation_summary.json.

Reads only the committed aggregate written by analyse_ablation.py, so the figure cannot
disagree with the table in results/ablation_summary.md. Writes PDF and PNG into results/.

Every value plotted is a host-simulation result. Nothing here is a hardware measurement.

Usage: python3 make_ablation_figures.py
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

# Same validated categorical pair as make_figures.py, plus a neutral for the control arm.
C_FAIL = "#eb6834"   # orange - the design fails this property
C_PASS = "#2a78d6"   # blue   - the design holds this property
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#d9d8d4"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.8,
    "figure.dpi": 200,
})

# Figure 1 keeps the six command-path designs. The credential-compromise arms are a
# different question -- which secret the adversary holds -- and get their own figure, because
# eleven categories on one axis is unreadable at journal column width.
ORDER = ["none", "ratelimit", "token", "transport", "transport_leaked", "hmac"]

MATRIX = [
    ("transport",           "TLS only", "no secret"),
    ("transport_leaked",    "TLS only", "any broker\ncredential"),
    ("acl_shared_leaked",   "TLS + ACL", "shared\ncredential"),
    ("acl_operator_leaked", "TLS + ACL", "controller\ncredential"),
    ("acl_device_leaked",   "TLS + ACL", "device\ncredential"),
    ("hmac",                "HMAC", "any broker\ncredential"),
    ("hmac_keyleaked",      "HMAC", "controller cred.\n+ command key"),
    ("acl_hmac_devicedump", "TLS+ACL+HMAC", "device cred.\n+ key (flash dump)"),
]
LABEL = {
    "none": "No command\ndefence",
    "ratelimit": "Token-bucket\nrate limit",
    "token": "Static shared\ntoken",
    "transport": "TLS + broker\ncredentials",
    "transport_leaked": "TLS, credentials\nleaked",
    "hmac": "HMAC-SHA256\n+ counter",
}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, centre - margin), min(1.0, centre + margin)


def main():
    with open(os.path.join(RES, "ablation_summary.json")) as fh:
        ab = json.load(fh)["ablation"]
    modes = [m for m in ORDER if m in ab]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10.4, 3.4))
    x = range(len(modes))

    # ---- panel A: the safety outcome, with Wilson intervals
    pts = [wilson(ab[m]["reached_alarm"], ab[m]["intrusion_test_valid"]) for m in modes]
    vals = [100 * p for p, _, _ in pts]
    # The Wilson interval is not centred on p, so a naive p-lo can go slightly negative
    # at p = 1. Clamp: the bar marks the point estimate, the whisker the interval bound.
    lo = [max(0.0, 100 * (p - l)) for p, l, _ in pts]
    hi = [max(0.0, 100 * (h - p)) for p, _, h in pts]
    cols = [C_FAIL if v < 99.0 else C_PASS for v in vals]
    ax1.bar(x, vals, color=cols, width=0.68, zorder=3)
    ax1.errorbar(x, vals, yerr=[lo, hi], fmt="none", ecolor=INK,
                 elinewidth=0.9, capsize=2.5, zorder=4)
    ax1.set_ylabel("Alarm activation rate (%)")
    ax1.set_title("(a) Safety function under attack", loc="left")
    ax1.set_ylim(0, 108)
    for i, v in enumerate(vals):
        ax1.text(i, v + 3.0, f"{v:.0f}", ha="center", fontsize=7.5, color=INK)

    # ---- panel B: operator availability under flood
    av = [100 * ab[m]["legit_admitted_flooded"] / ab[m]["legit_attempts_flooded"]
          if ab[m]["legit_attempts_flooded"] else 0.0 for m in modes]
    ax2.bar(x, av, color=[C_FAIL if v < 99.0 else C_PASS for v in av], width=0.68, zorder=3)
    ax2.set_ylabel("Operator commands admitted (%)")
    ax2.set_title("(b) Availability under command flood", loc="left")
    ax2.set_ylim(0, 108)
    for i, v in enumerate(av):
        ax2.text(i, v + 3.0, f"{v:.0f}", ha="center", fontsize=7.5, color=INK)

    # ---- panel C: integrity, the ablation's discriminator
    rp = [100 * ab[m]["attacker_replay_armed"] / ab[m]["replay_test_valid"]
          if ab[m]["replay_test_valid"] else 0.0 for m in modes]
    ax3.bar(x, rp, color=[C_FAIL if v > 1.0 else C_PASS for v in rp], width=0.68, zorder=3)
    ax3.set_ylabel("Trials defeated by capture-and-replay (%)")
    ax3.set_title("(c) Integrity against replay", loc="left")
    ax3.set_ylim(0, 108)
    for i, v in enumerate(rp):
        ax3.text(i, v + 3.0, f"{v:.0f}", ha="center", fontsize=7.5, color=INK)

    for ax in (ax1, ax2, ax3):
        ax.set_xticks(list(x))
        ax.set_xticklabels([LABEL[m] for m in modes], rotation=38, ha="right")
        ax.yaxis.grid(True, color=GRID, linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(RES, f"ablation_results.{ext}"), bbox_inches="tight")
    print("wrote results/ablation_results.pdf and .png")
    credential_figure(ab)


def credential_figure(ab):
    """Which secret the adversary holds, against what the system still does."""
    rows = [(m, c, sec) for m, c, sec in MATRIX if m in ab]
    if not rows:
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.6), sharey=True)
    # Horizontal bars: the category labels are two-part (controls, secret held) and do not fit
    # legibly on a rotated x axis at journal column width.
    y = list(range(len(rows)))[::-1]

    alarm, avail = [], []
    for m, _, _ in rows:
        d = ab[m]
        alarm.append(100 * d["reached_alarm"] / d["intrusion_test_valid"]
                     if d["intrusion_test_valid"] else 0.0)
        avail.append(100 * d["legit_admitted_flooded"] / d["legit_attempts_flooded"]
                     if d["legit_attempts_flooded"] else 0.0)

    for ax, vals, lab, title in (
            (ax1, alarm, "Alarm activation rate (%)",
             "(a) Does the safety function still fire?"),
            (ax2, avail, "Operator commands admitted (%)",
             "(b) Can the owner still command the system?")):
        ax.barh(y, vals, color=[C_FAIL if v < 99.0 else C_PASS for v in vals],
                height=0.66, zorder=3)
        ax.set_xlabel(lab)
        ax.set_title(title, loc="left", fontsize=9)
        ax.set_xlim(0, 118)
        for yy, v in zip(y, vals):
            ax.text(v + 2.5, yy, f"{v:.0f}", va="center", fontsize=7.5, color=INK)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{c} — " + sec.replace("\n", " ") for _, c, sec in rows],
                           fontsize=7.4)
        ax.xaxis.grid(True, color=GRID, linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(RES, f"credential_matrix.{ext}"), bbox_inches="tight")
    print("wrote results/credential_matrix.pdf and .png")


if __name__ == "__main__":
    main()
