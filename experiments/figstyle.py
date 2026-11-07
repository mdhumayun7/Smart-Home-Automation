"""Shared plot style, so every generated figure in this paper looks like the same paper.

Imported by make_ablation_figures.py and make_figures.py. Nothing here decides what is
plotted; it decides only how. Keeping it in one module is what stops typography, colour and
line weight drifting between figures that sit on facing pages.

Colour carries one meaning throughout and never carries it alone: a value that fails a
property is drawn in the fail colour *and* labelled with its number, and every axis is
labelled in words. The two hues are distinguishable in greyscale (the fail colour is
noticeably darker when desaturated) and pass a deuteranopia check, because blue against
orange is the safest of the common pairs.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Semantic colours. HOLD: the property under test holds. FAIL: it does not.
HOLD = "#2a6fb5"
FAIL = "#d2601a"
INK = "#1a1a1a"
MUTED = "#5c5c5c"
GRID = "#dcdcdc"

# Sizes are chosen so that the smallest text in a figure placed at \textwidth is about 8 pt on
# the printed A4 page, which is the floor most publishers set for legibility.
RC = {
    # The six hand-drawn diagrams are set in DejaVu Sans, so the plots are too: eight figures
    # in one typeface rather than six in one and two in another. Sans-serif figures against a
    # serif body are conventional and keep small axis text legible at column width.
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "Liberation Sans"],
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": INK,
    "axes.labelcolor": INK,
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "pdf.fonttype": 42,          # embed TrueType, not Type 3: required by most publishers
    "ps.fonttype": 42,
}


def apply():
    plt.rcParams.update(RC)


def tidy(ax, axis="x"):
    """Grid on the value axis only, spines reduced to the two that carry information."""
    (ax.xaxis if axis == "x" else ax.yaxis).grid(
        True, color=GRID, linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def colour_for(value, threshold=99.0):
    return HOLD if value >= threshold else FAIL
