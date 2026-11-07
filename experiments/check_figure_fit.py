#!/usr/bin/env python3
"""Find text that spills out of its box, or off the canvas, in the generated diagrams.

Reading a figure on screen does not reliably catch this. A label one or two characters too
long for its box looks like a label that touches its border, and at the size these are
inspected the difference is invisible -- but in print it is a clipped word.

The check is mechanical. For every <text> in an SVG it measures the string in the real font
at the real size, works out the drawn extent from the anchor, and then asks whether that
extent fits inside the tightest <rect> that encloses the anchor point. Text that sits on a
background band rather than in a box is checked against the canvas instead.

Measurement uses Pillow with the actual DejaVu Sans face, so it is the renderer's metrics
rather than an average-character-width guess.

Exit status is non-zero if anything overflows.

Usage: python3 -I check_figure_fit.py [name ...]
"""
import os
import re
import sys

from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.normpath(os.path.join(HERE, "..", "docs", "images"))

# Text is allowed to come this close to a border before it counts as overflowing. Below about
# 3 units a label is touching the stroke, which reads as a mistake even when it technically
# fits.
PAD = 3.0

FACES = {
    (False, False): "DejaVuSans.ttf",
    (True, False): "DejaVuSans-Bold.ttf",
    (False, True): "DejaVuSansMono.ttf",
    (True, True): "DejaVuSansMono-Bold.ttf",
}
SEARCH = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "/usr/share/fonts/TTF",
]
_cache = {}


def font(size, bold, mono):
    key = (round(size, 1), bold, mono)
    if key in _cache:
        return _cache[key]
    name = FACES[(bold, mono)]
    for d in SEARCH:
        p = os.path.join(d, name)
        if os.path.exists(p):
            _cache[key] = ImageFont.truetype(p, int(round(size)))
            return _cache[key]
    raise SystemExit(f"cannot find {name}; install fonts-dejavu to run this check")


def unescape(s):
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))


RECT = re.compile(r'<rect x="([-0-9.]+)" y="([-0-9.]+)" width="([0-9.]+)" height="([0-9.]+)"')
TEXT = re.compile(
    r'<text x="([-0-9.]+)" y="([-0-9.]+)" font-size="([0-9.]+)" font-family=\'([^\']*)\' '
    r'text-anchor="([a-z]+)"[^>]*?>(.*?)</text>')


def check(path):
    svg = open(path, errors="replace").read()
    m = re.search(r'width="([0-9.]+)" height="([0-9.]+)"', svg)
    cw, ch = float(m.group(1)), float(m.group(2))

    rects = [(float(a), float(b), float(c), float(d)) for a, b, c, d in RECT.findall(svg)
             # the full-canvas background rect is not a container
             if not (float(c) >= cw and float(d) >= ch)]

    bad = []
    for xs, ys, size_s, family, anchor, body in TEXT.findall(svg):
        x, y, size = float(xs), float(ys), float(size_s)
        s = unescape(body)
        if not s.strip():
            continue
        bold = 'font-weight="bold"' in svg[svg.index(f'<text x="{xs}" y="{ys}"'):][:400]
        mono = "Mono" in family
        w = font(size, bold, mono).getlength(s)
        if anchor == "middle":
            x0, x1 = x - w / 2, x + w / 2
        elif anchor == "end":
            x0, x1 = x - w, x
        else:
            x0, x1 = x, x + w

        if x0 < PAD or x1 > cw - PAD:
            bad.append((s, "runs off the canvas", round(x0, 1), round(x1, 1), f"0..{cw:.0f}"))
            continue

        # The tightest rect containing the anchor. A text baseline sits above the glyph
        # bottom, so the vertical test uses the baseline alone.
        holders = [r for r in rects
                   if r[0] <= x <= r[0] + r[2] and r[1] <= y <= r[1] + r[3]]
        if not holders:
            continue
        hx, hy, hw, hh = min(holders, key=lambda r: r[2] * r[3])
        if x0 < hx + PAD or x1 > hx + hw - PAD:
            bad.append((s, "overflows its box", round(x0, 1), round(x1, 1),
                        f"{hx:.0f}..{hx + hw:.0f}"))
    return bad


def main():
    want = sys.argv[1:]
    names = sorted(f for f in os.listdir(IMAGES) if f.endswith(".svg"))
    if want:
        names = [f for f in names if any(w in f for w in want)]
    total = 0
    for name in names:
        bad = check(os.path.join(IMAGES, name))
        total += len(bad)
        print(f"{name}: {'ok' if not bad else str(len(bad)) + ' overflowing'}")
        for s, why, x0, x1, box in bad:
            short = s if len(s) <= 58 else s[:55] + "..."
            print(f"    {why}: [{x0} .. {x1}] vs {box}   {short!r}")
    print()
    if total:
        print(f"{total} overflowing label(s)")
        return 1
    print("every label fits inside its box and inside the canvas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
