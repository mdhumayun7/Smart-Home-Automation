#!/usr/bin/env python3
"""Measure the printed size of the smallest text in every figure the manuscript includes.

A diagram is authored in SVG user units and then scaled to a fraction of the text block.
Inspecting it on screen says nothing about how large its labels are on paper: a 1,100-unit
canvas placed at 0.92\\textwidth renders one user unit as 0.38 pt, so an 11-unit label prints
at 4.2 pt. Most publishers set a 6 pt floor, and a reviewer reading a printout simply cannot
make out anything smaller.

This script reads each \\includegraphics line out of the manuscript, finds the matching SVG,
takes the smallest font-size in it, and reports the size that label will actually print at.
Matplotlib figures are reported separately: their sizes are set in points already, through
figstyle, so they are scaled by the ratio of the requested width to the figure's own width.

Exit status is non-zero if any figure prints below the floor.

Usage: python3 -I check_figure_type.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
TEX = os.path.join(ROOT, "paper", "manuscript.tex")
IMAGES = os.path.join(ROOT, "docs", "images")

# a4paper with 1 in margins: 210 mm - 2 in, in TeX points.
TEXTWIDTH_PT = 595.276 - 2 * 72.27
FLOOR_PT = 6.0


def main():
    tex = open(TEX, errors="replace").read()
    incs = re.findall(r"\\includegraphics\[width=([0-9.]*)\\textwidth\]\{([^}]+)\}", tex)

    worst = []
    print(f"text block: {TEXTWIDTH_PT:.1f} pt;  floor: {FLOOR_PT} pt\n")
    print(f"{'figure':<26}{'frac':>6}{'canvas':>9}{'min unit':>10}{'prints at':>11}")
    print("-" * 62)

    for frac_s, pdf in incs:
        frac = float(frac_s) if frac_s else 1.0
        svg = os.path.join(IMAGES, pdf.replace(".pdf", ".svg"))
        if not os.path.exists(svg):
            print(f"{pdf:<26}{frac:>6.2f}{'(matplotlib - sized in pt by figstyle)':>45}")
            continue
        text = open(svg, errors="replace").read()
        m = re.search(r'width="([0-9.]+)"', text)
        canvas = float(m.group(1))
        sizes = [float(s) for s in re.findall(r'font-size="([0-9.]+)"', text)]
        if not sizes:
            continue
        smallest = min(sizes)
        printed = smallest * (TEXTWIDTH_PT * frac / canvas)
        flag = "" if printed >= FLOOR_PT else "   BELOW FLOOR"
        print(f"{pdf:<26}{frac:>6.2f}{canvas:>9.0f}{smallest:>10.1f}"
              f"{printed:>9.2f} pt{flag}")
        if printed < FLOOR_PT:
            worst.append((pdf, round(printed, 2)))

    print()
    if worst:
        print("below the 6 pt floor:", worst)
        return 1
    print("every diagram label clears the 6 pt floor at its printed size")
    return 0


if __name__ == "__main__":
    sys.exit(main())
