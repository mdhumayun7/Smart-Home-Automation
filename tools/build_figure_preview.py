#!/usr/bin/env python3
"""Build ALL_FIGURES_PREVIEW.pdf: every figure, one per page, at its printed width.

A reviewer or supervisor opening one PDF should be able to see every figure in the paper
without opening the paper, at the size it will actually print. Manuscript figures come first,
each with the caption summary and the page it appears on; the repository documentation
figures follow, clearly separated.

Usage: python3 tools/build_figure_preview.py [--out DIR]
Requires pdflatex.
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
IMAGES = os.path.join(ROOT, "docs", "images")
RESULTS = os.path.join(ROOT, "experiments", "results")

MANUSCRIPT = [
    ("architecture", IMAGES, 8, "System architecture",
     "The safety domain on core~1 and the network domain on core~0, the two bounded queues and "
     "the mutex-guarded status snapshot between them. Every pin, timeout and queue depth is "
     "transcribed from \\texttt{smart\\_home.ino}."),
    ("command_flow", IMAGES, 9, "Command execution flow",
     "Parsing and HMAC verification complete on core~0; the replay counter is committed to NVS "
     "before the command is acted on. Rejected and accepted paths are distinguished."),
    ("ablation_results", RESULTS, 16, "Command-path ablation results",
     "Six designs over three properties. 300 trials per bar in (a) and (c), 1{,}250 operator "
     "attempts per bar in (b); whiskers in (a) are 95\\,\\% Wilson intervals."),
    ("acl_architecture", IMAGES, 18, "Broker access control architecture",
     "Per-client topic permissions, and which compromise each control contains. The matrix is "
     "both the one the ablation models and the Mosquitto \\texttt{acl\\_file} used in the "
     "broker experiment."),
    ("credential_matrix", RESULTS, 18, "Security compromise comparison",
     "Alarm activation and operator availability for nine combinations of control and "
     "compromised secret. The bottom row is the layered build under a compromised controller "
     "host: it fails, and is drawn at the same weight as every other row."),
    ("experimental_setup", IMAGES, 22, "Experimental setup",
     "Panel~A is everything that has been run. Panel~B is the hardware rig: specified, not "
     "run, drawn dotted, and labelled in red that no result in the paper comes from it."),
    ("guard_decision", IMAGES, 24, "Compile-guard comparison",
     "The defective guard and its repair, transcribed from the preprocessor conditions. Both "
     "branches of the original reach the same outcome, which is the defect."),
    ("security_paths", IMAGES, 25, "Transport security versus command authorization",
     "The third row of the upper panel is the compromised controller host, holding both a "
     "permitted credential and the key: neither layer refuses it, and the alarm fires in only "
     "50 of 300 trials."),
]
ADDITIONAL = [
    ("command_sequence", "Command sequence (UML)"),
    ("deployment", "Deployment"),
    ("methodology", "Methodology"),
    ("state_machine", "Alarm state machine"),
    ("event_sequence", "Event sequence"),
    ("circuit_wiring", "Circuit wiring"),
    ("hardware_rig", "Hardware measurement rig --- NOT BUILT, NOT RUN"),
]

PRE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=0.8in]{geometry}
\usepackage{graphicx,hyperref}
\hypersetup{colorlinks=true,linkcolor=black,pdftitle={All figures preview}}
\setlength{\parindent}{0pt}
\begin{document}
\begin{center}
{\LARGE\bfseries All Figures Preview}\\[6pt]
{\large Unverified Assumptions in Embedded Safety Firmware:}\\
{\large Configuration, Specification and Response-Time Defects in an MQTT Alarm System}\\[6pt]
MD Humayun \quad\textbullet\quad SVNIT Surat \quad\textbullet\quad commit \texttt{%(head)s}
\end{center}
\vspace{6pt}
Every figure is the exact file the manuscript embeds, shown at the width it occupies there
(\verb|\textwidth|). Figures 1--8 are the manuscript's; the figures after them document the
repository and are not part of the submission.
\vspace{8pt}\hrule\vspace{8pt}
\tableofcontents
\newpage
\section{Manuscript figures}
%(man)s
\newpage
\section{Additional repository figures}
Not part of the manuscript.
%(add)s
\end{document}
"""


def block(path, label, title, caption):
    return (f"\\subsection*{{{label} --- {title}}}\n"
            f"\\addcontentsline{{toc}}{{subsection}}{{{label} --- {title}}}\n"
            f"\\begin{{center}}\\includegraphics[width=\\textwidth,height=0.70\\textheight,"
            f"keepaspectratio]{{{path}}}\\end{{center}}\n"
            f"\\vspace{{-2pt}}\\small {caption}\\normalsize\n\\newpage\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "build"))
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    work = os.path.join(out, "_preview")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work, exist_ok=True)

    head = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip() or "unknown"

    man = "".join(
        block(os.path.join(src, stem + ".pdf"), f"Figure {i}", title,
              f"{cap} \\textit{{Manuscript page {page}.}}")
        for i, (stem, src, page, title, cap) in enumerate(MANUSCRIPT, 1))
    add = "".join(
        block(os.path.join(IMAGES, stem + ".pdf"), "Repository figure", title,
              "Documentation figure; not part of the manuscript.")
        for stem, title in ADDITIONAL)

    tex = os.path.join(work, "preview.tex")
    with open(tex, "w") as fh:
        fh.write(PRE % {"head": head, "man": man, "add": add})

    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "preview.tex"],
                       cwd=work, capture_output=True)

    built = os.path.join(work, "preview.pdf")
    if not os.path.exists(built):
        raise SystemExit("pdflatex did not produce preview.pdf")
    dest = os.path.join(out, "ALL_FIGURES_PREVIEW.pdf")
    shutil.copy2(built, dest)
    pages = subprocess.run(["pdfinfo", dest], capture_output=True, text=True).stdout
    n = [l.split()[1] for l in pages.splitlines() if l.startswith("Pages")]
    print(f"wrote {dest}  ({os.path.getsize(dest)/1e3:.0f} kB, {n[0] if n else '?'} pages, "
          f"{len(MANUSCRIPT) + len(ADDITIONAL)} figures)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
