#!/usr/bin/env python3
"""Produce the paper figures from the campaign aggregates.

Reads results/summary.json (written by analyse.py) and writes PDF and PNG figures into
results/. Figures are built for print: a colourblind-safe pair (validated: CVD dE 24.7,
normal-vision dE 33.6), plus distinct markers and line styles so the two series remain
distinguishable in greyscale.

Usage: python3 make_figures.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

# Validated categorical pair (see dataviz palette validation).
C_BASE = "#eb6834"   # orange - baseline
C_HARD = "#2a78d6"   # blue   - hardened
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#d9d8d4"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.8,
    "figure.dpi": 200,
})


def pct(d, key, rates):
    return [100.0 * d["rates"][str(r)][key] / d["rates"][str(r)]["n"] for r in rates]


def main():
    with open(os.path.join(RES, "summary.json")) as f:
        s = json.load(f)
    base, hard = s["baseline"], s["hardened"]
    rates = sorted(int(r) for r in base["rates"])
    x = list(range(len(rates)))
    labels = ["0" if r == 0 else (f"{r//1000}k" if r >= 1000 else str(r)) for r in rates]

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.5), sharey=True)

    panels = [
        ("(a) Attacker-caused state change", "attacker_armed"),
        ("(b) Legitimate command succeeded", "legit_accepted"),
    ]
    for ax, (title, key) in zip(axes, panels):
        yb = pct(base, key, rates)
        yh = pct(hard, key, rates)
        ax.plot(x, yb, color=C_BASE, lw=2.0, marker="o", ms=5.5, ls="--",
                label="baseline (no authentication)", clip_on=False, zorder=3)
        ax.plot(x, yh, color=C_HARD, lw=2.0, marker="s", ms=5.0, ls="-",
                label="hardened (authenticated)", clip_on=False, zorder=4)
        ax.set_title(title, loc="left", color=INK)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_xlabel("injected commands per second")
        ax.set_ylim(-6, 106)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.grid(axis="y", color=GRID, lw=0.7)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    axes[0].set_ylabel("trials (%)")
    handles, labs = axes[0].get_legend_handles_labels()
    fig.legend(handles, labs, loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(RES, f"fig_campaign.{ext}"), bbox_inches="tight")
    plt.close(fig)
    n = base["trials"] + hard["trials"]
    print(f"wrote results/fig_campaign.pdf and .png  (from {n} trials)")


if __name__ == "__main__":
    main()
