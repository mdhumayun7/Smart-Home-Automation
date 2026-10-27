#!/usr/bin/env python3
"""Analyse the hardware latency samples and test safety-latency invariance.

Reads the CSV written by collect.py (columns: condition, index, latency_us), reports median
and tail latency per condition, applies the same Mann-Whitney U test as the simulation
analysis comparing each loaded condition against condition A, and writes a box-plot figure.

Usage: python3 analyse_hw.py --in results_hw.csv

Requires matplotlib for the figure; the table prints without it.
"""
import argparse
import csv
import math
import os
import statistics
from collections import defaultdict

# Reuse the same test implemented in experiments/analyse.py (kept standalone to avoid imports).
def mann_whitney_u(a, b):
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return None, None, None
    combined = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks = [0.0] * len(combined)
    i = 0
    tie_term = 0.0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        t = j - i + 1
        tie_term += t ** 3 - t
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    r1 = sum(r for r, (_, g) in zip(ranks, combined) if g == 0)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    u = min(u1, n1 * n2 - u1)
    mu = n1 * n2 / 2.0
    n = n1 + n2
    var = (n1 * n2 / 12.0) * ((n + 1) - tie_term / (n * (n - 1))) if n > 1 else 0.0
    if var <= 0:
        return u, 0.0, 1.0
    z = (u - mu) / math.sqrt(var)
    p = math.erfc(abs(z) / math.sqrt(2))
    return u, z, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="results_hw.csv")
    ap.add_argument("--control", default="A")
    args = ap.parse_args()

    if not os.path.exists(args.inp):
        print(f"no data file yet: {args.inp}\n"
              f"Collect samples with collect.py first (see hardware/README.md).")
        return

    data = defaultdict(list)
    with open(args.inp) as f:
        for row in csv.DictReader(f):
            data[row["condition"]].append(int(row["latency_us"]) / 1000.0)  # ms

    conds = sorted(data)
    print(f"{'cond':5} {'n':>4} {'median':>9} {'p95':>9} {'max':>9}")
    for c in conds:
        xs = sorted(data[c])
        p95 = xs[min(len(xs) - 1, int(0.95 * len(xs)))]
        print(f"{c:5} {len(xs):>4} {statistics.median(xs):>8.3f} {p95:>8.3f} {max(xs):>8.3f}")

    if args.control in data:
        print(f"\nMann-Whitney U vs condition {args.control}:")
        for c in conds:
            if c == args.control:
                continue
            u, z, p = mann_whitney_u(data[c], data[args.control])
            verdict = "indistinguishable" if (p is None or p > 0.05) else "DIFFERENT"
            print(f"  {c}: U={u} z={None if z is None else round(z,3)} "
                  f"p={None if p is None else round(p,4)} -> {verdict}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams.update({"font.family": "serif", "font.size": 9})
        fig, ax = plt.subplots(figsize=(4.0, 2.6))
        ax.boxplot([data[c] for c in conds], labels=conds, showfliers=True)
        ax.set_ylabel("sensor-to-siren latency (ms)")
        ax.set_xlabel("condition")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        fig.tight_layout()
        fig.savefig("fig_hw_latency.pdf", bbox_inches="tight")
        fig.savefig("fig_hw_latency.png", dpi=200, bbox_inches="tight")
        print("\nwrote fig_hw_latency.pdf / .png")
    except ImportError:
        print("\n(matplotlib not available; skipped the figure)")


if __name__ == "__main__":
    main()
