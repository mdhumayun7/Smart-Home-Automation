#!/usr/bin/env python3
"""Build COMPLETE_FIGURE_COLLECTION.zip and ALL_FIGURES_PREVIEW.pdf.

The archive is a deliverable, but it is entirely derived from files already in this
repository, so it is built by this script rather than committed as a binary blob that would
go stale the moment a figure changed.

For each of the eight manuscript figures it writes a publication-quality vector PDF (the exact
file the manuscript embeds), the editable SVG where one exists, and a PNG rendered at 600 DPI
*measured at the width the figure occupies in the manuscript* -- not 600 DPI of some arbitrary
canvas, which would mean something different for every figure. The six repository
documentation figures are included separately.

Also written: a manifest with per-file SHA-256, the validation output, and SHA256SUMS.txt.

Usage:
    python3 tools/build_figure_collection.py [--out DIR]

Requires cairosvg, Pillow, pdftoppm (poppler-utils) and pdflatex.
"""
import argparse
import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
IMAGES = os.path.join(ROOT, "docs", "images")
RESULTS = os.path.join(ROOT, "experiments", "results")

# A4 with 1 in margins: the text block a figure at \textwidth occupies.
TEXTWIDTH_IN = (595.276 - 2 * 72.27) / 72.27
DPI = 600

MANUSCRIPT = [
    ("figure_01_architecture", "architecture", IMAGES,
     "System Architecture", 8),
    ("figure_02_command_flow", "command_flow", IMAGES,
     "Command Execution Flow", 9),
    ("figure_03_ablation_results", "ablation_results", RESULTS,
     "Command-Path Ablation Results", 16),
    ("figure_04_acl_architecture", "acl_architecture", IMAGES,
     "Broker Access Control Architecture", 18),
    ("figure_05_credential_matrix", "credential_matrix", RESULTS,
     "Security Compromise Comparison", 18),
    ("figure_06_experimental_setup", "experimental_setup", IMAGES,
     "Experimental Setup", 22),
    ("figure_07_guard_decision", "guard_decision", IMAGES,
     "Compile-Guard Comparison", 24),
    ("figure_08_security_paths", "security_paths", IMAGES,
     "Transport Security vs Command Authorization", 25),
]
ADDITIONAL = ["command_sequence", "deployment", "methodology",
              "state_machine", "event_sequence", "circuit_wiring", "hardware_rig"]

SOURCES = [
    ("docs/figures/make_diagrams.py", "make_diagrams.py"),
    ("experiments/make_ablation_figures.py", "make_ablation_figures.py"),
    ("experiments/figstyle.py", "figstyle.py"),
    ("experiments/check_figure_type.py", "check_figure_type.py"),
    ("experiments/check_figure_fit.py", "check_figure_fit.py"),
    ("experiments/validate_figures.py", "validate_figures.py"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def render_png(svg_path, dest):
    """600 DPI at the printed width, so every figure is comparable."""
    import cairosvg
    text = open(svg_path, errors="replace").read()
    canvas = float(re.search(r'width="([0-9.]+)"', text).group(1))
    cairosvg.svg2png(url=svg_path, write_to=dest, scale=DPI * TEXTWIDTH_IN / canvas)


def png_from_pdf(pdf_path, stem_dest):
    subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-singlefile",
                    pdf_path, stem_dest], check=True)


def collect(out, rows, group, folder, stem, src_dir, title, page=None):
    from PIL import Image
    d = os.path.join(out, group, folder)
    os.makedirs(d, exist_ok=True)
    svg = os.path.join(src_dir, stem + ".svg")
    pdf = os.path.join(src_dir, stem + ".pdf")
    if not os.path.exists(pdf):
        raise SystemExit(f"missing {pdf}; run the figure generators first")

    shutil.copy2(pdf, os.path.join(d, stem + ".pdf"))
    if os.path.exists(svg):
        shutil.copy2(svg, os.path.join(d, stem + ".svg"))
        render_png(svg, os.path.join(d, stem + ".png"))
        generator = "docs/figures/make_diagrams.py"
    else:
        png_from_pdf(pdf, os.path.join(d, stem))
        generator = "experiments/make_ablation_figures.py"

    im = Image.open(os.path.join(d, stem + ".png"))
    for ext in ("pdf", "svg", "png"):
        f = os.path.join(d, stem + "." + ext)
        if not os.path.exists(f):
            continue
        rows.append({
            "group": group, "folder": folder, "title": title,
            "manuscript_page": page if page else "",
            "file": os.path.relpath(f, out), "format": ext.upper(),
            "bytes": os.path.getsize(f),
            "png_pixels": f"{im.width}x{im.height}" if ext == "png" else "",
            "png_dpi_at_textwidth": DPI if ext == "png" else "",
            "generator": generator, "sha256": sha256(f),
        })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "build"))
    args = ap.parse_args()

    out_root = os.path.abspath(args.out)
    out = os.path.join(out_root, "COMPLETE_FIGURE_COLLECTION")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)

    rows = []
    for folder, stem, src, title, page in MANUSCRIPT:
        collect(out, rows, "manuscript_figures", folder, stem, src, title, page)
    for stem in ADDITIONAL:
        collect(out, rows, "additional_readme_figures", stem, stem, IMAGES,
                stem.replace("_", " ").title())

    os.makedirs(os.path.join(out, "source_files"), exist_ok=True)
    for src, dst in SOURCES:
        shutil.copy2(os.path.join(ROOT, src), os.path.join(out, "source_files", dst))

    # validation: run the three checks and capture their output verbatim
    vdir = os.path.join(out, "validation")
    os.makedirs(vdir, exist_ok=True)
    shutil.copy2(os.path.join(ROOT, "docs", "FIGURE_VALIDATION.md"), vdir)
    with open(os.path.join(vdir, "validation_results.txt"), "w") as fh:
        for script in ("check_figure_type.py", "check_figure_fit.py", "validate_figures.py"):
            fh.write(f"=== {script} ===\n")
            r = subprocess.run([sys.executable, "-I",
                                os.path.join(ROOT, "experiments", script)],
                               capture_output=True, text=True, cwd=ROOT)
            fh.write(r.stdout + r.stderr + f"exit={r.returncode}\n\n")

    with open(os.path.join(out, "manifest.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    readme = os.path.join(ROOT, "docs", "FIGURE_COLLECTION_README.md")
    if os.path.exists(readme):
        shutil.copy2(readme, os.path.join(out, "README.md"))

    # checksums last, over everything else
    sums = os.path.join(vdir, "SHA256SUMS.txt")
    with open(sums, "w") as fh:
        for base, _, files in sorted(os.walk(out)):
            for f in sorted(files):
                p = os.path.join(base, f)
                if os.path.abspath(p) == os.path.abspath(sums):
                    continue
                fh.write(f"{sha256(p)}  {os.path.relpath(p, out)}\n")

    zip_path = os.path.join(out_root, "COMPLETE_FIGURE_COLLECTION")
    if os.path.exists(zip_path + ".zip"):
        os.remove(zip_path + ".zip")
    shutil.make_archive(zip_path, "zip", out_root, "COMPLETE_FIGURE_COLLECTION")

    n_files = sum(len(f) for _, _, f in os.walk(out))
    print(f"wrote {zip_path}.zip  ({os.path.getsize(zip_path + '.zip')/1e6:.1f} MB, "
          f"{n_files} files)")
    print(f"  {len(MANUSCRIPT)} manuscript figures, {len(ADDITIONAL)} additional, "
          f"{len(rows)} figure files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
