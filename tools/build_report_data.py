#!/usr/bin/env python3
"""Regenerate report/generated/*.tex directly from the repository.

The report cites file counts, lines of code, the commit hash, the experiment catalogue and the
figure index. Each of those can drift from the artefacts it describes if it is maintained by
hand, so each is generated here instead:

  meta.tex            commit hash, source file count, lines of code
  appA_tree.tex       directory listing with per-directory file counts
  appB_inventory.tex  every source file with its language, lines and lines of code
  appG_experiments.tex  the experiment catalogue
  appH_figures.tex    the figure index, with each figure's generator

The directory descriptions in appendix A, and the titles in appendices G and H, are editorial
and live in the tables below. Everything countable -- file counts, line counts, which figure
files exist and which generator produces each -- is read from disk, and the script FAILS if a
curated entry names a file that is not there. That way an editorial label cannot outlive the
thing it labels.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report" / "generated"

# ---------------------------------------------------------------------------------------
# Which files count as source, and how to classify them.
# ---------------------------------------------------------------------------------------
LANG_BY_SUFFIX = {
    ".ino": "Arduino/C++",
    ".cpp": "C++",
    ".h": "C/C++ header",
    ".py": "Python",
    ".sh": "Shell",
    ".tla": "TLA+",
    ".cfg": "TLC config",
}
# Line-comment prefixes per language, for the lines-of-code count.
COMMENT_PREFIX = {
    "Arduino/C++": ("//",),
    "C++": ("//",),
    "C/C++ header": ("//",),
    "Python": ("#",),
    "Shell": ("#",),
    "TLA+": ("\\*",),
    "TLC config": ("\\*",),
}
SKIP_DIR_PARTS = {
    ".git", "__pycache__", ".pytest_cache", "node_modules", "build",
    "corpus_repos", "states", "FINAL_SUBMISSION_PACKAGE",
}
SKIP_NAMES = {"secrets.h"}
# Run artefacts and build output. These are excluded from the appendix A directory counts as
# well as from the inventory: without the exclusion, formal/ counts 21 files rather than 7
# because TLC writes a .tla and a .bin trace file per failing run, and report/ counts its own
# .aux, .log and .pdf. The appendix would then describe the last build rather than the source.
SKIP_SUFFIXES = {
    ".pyc", ".o", ".so", ".bin", ".aux", ".log", ".out", ".toc", ".lof", ".lot",
    ".blg", ".bbl", ".pdf", ".synctex.gz",
}
SKIP_PATTERNS = ["AlarmFSM_TTrace_*", "*_TTrace_*"]

# Directory descriptions for appendix A. A directory with no entry here prints with an empty
# description rather than an invented one.
DIR_NOTES = {
    "(root)": "Licence, citation metadata, top-level README, reproduction guide, changelog",
    ".github/workflows": "Continuous integration",
    "docs": "Analysis documents and the figure sources",
    "docs/figures": "The diagram generator",
    "docs/images": "Generated SVG, PDF and PNG figures",
    "experiments": "Harnesses, analysis scripts, figure generators, verification checks",
    "experiments/broker": "Real Mosquitto testbed: setup, ACL variants, scenario runner",
    "experiments/corpus": "Corpus builder, static rule, controls, commit pins, findings",
    "experiments/hardware":
        "Probe firmware, collection and pre-registered analysis (not yet run)",
    "experiments/results": "Committed raw and aggregate experimental records",
    "firmware/espnow_receiver": "Companion receiver sketch (not part of the evaluation)",
    "firmware/smart_home": "The artefact under study: v2.2.0 sketch and its headers",
    "formal": "TLA+ specifications, three TLC configurations, runner, tla2tools.jar",
    "paper": "Manuscript source and build products",
    "paper/submission": "Highlights, declaration document, similarity-screening file",
    "report": "This report: chapter sources, front matter, generated data",
    "tests/host": "Host test suite and the stub headers it compiles against",
    "tools": "Command signer, evaluator, figure and archive builders",
    "wokwi": "Simulator circuit definition",
}

# Appendix G. 'artefact' is checked to exist under experiments/ (or formal/) where it names one.
EXPERIMENTS = [
    ("E1", "Adversarial campaign, baseline build", "Simulation",
     "summary.json", "3{,}000 trials"),
    ("E2", "Adversarial campaign, hardened build", "Simulation",
     "summary.json", "3{,}000 trials"),
    ("E3", "Command-path ablation", "Simulation",
     "ablation.jsonl", "3{,}600 trials, 12 configurations"),
    ("E4", "Host-build fuzzing under ASan/UBSan", "Simulation",
     "fuzz.json", "3{,}000{,}000 iterations"),
    ("E5", "Detector parameter sensitivity sweep", "Simulation",
     "sensitivity.jsonl", "180 grid cells"),
    ("E6", "Access control against a live broker", "Testbed measurement",
     "broker_acl.jsonl", "8 scenarios"),
    ("E7", "Open-source corpus study", "Corpus study",
     "corpus/corpus.json", "135 projects"),
    ("E8", "Trace conformance against the TLA+ relation", "Formal + simulation",
     "test_conformance.py", "19{,}529 transitions"),
    ("E9", "Model checking, three configurations", "Formal",
     "formal/", "25 and 660 distinct states"),
]

# Appendix H. Each entry's file must exist, and its generator must exist.
DIAGRAM_GEN = "docs/figures/make_diagrams.py"
PLOT_GEN = "experiments/make_ablation_figures.py"
MANUSCRIPT_FIGURES = [
    (1, "System architecture", "architecture.pdf", DIAGRAM_GEN),
    (2, "Command execution flow", "command_flow.pdf", DIAGRAM_GEN),
    (3, "Command-path ablation results", "ablation_results.pdf", PLOT_GEN),
    (4, "Broker access control architecture", "acl_architecture.pdf", DIAGRAM_GEN),
    (5, "Security compromise comparison", "credential_matrix.pdf", PLOT_GEN),
    (6, "Experimental setup", "experimental_setup.pdf", DIAGRAM_GEN),
    (7, "Compile-guard comparison", "guard_decision.pdf", DIAGRAM_GEN),
    (8, "Transport security versus command authorisation", "security_paths.pdf", DIAGRAM_GEN),
]
DOC_FIGURES = [
    ("Command sequence (UML)", "command_sequence.pdf", DIAGRAM_GEN),
    ("Deployment view", "deployment.pdf", DIAGRAM_GEN),
    ("Methodology overview", "methodology.pdf", DIAGRAM_GEN),
    ("Alarm state machine", "state_machine.pdf", DIAGRAM_GEN),
    ("Event sequence", "event_sequence.pdf", DIAGRAM_GEN),
    ("Circuit wiring", "circuit_wiring.pdf", DIAGRAM_GEN),
    ("Hardware measurement rig (not built)", "hardware_rig.pdf", DIAGRAM_GEN),
]
FIGURE_SEARCH = ["docs/images", "experiments/results"]


def tex(s: str) -> str:
    """Escape the characters that matter in these tables."""
    return s.replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("&", r"\&") \
            .replace("%", r"\%").replace("#", r"\#")


# Languages whose files may contain /* ... */ block comments. Without handling these, a file
# with a long block-comment header counts every one of those lines as code: ablation.cpp
# reports 384 rather than 369, a 4% overstatement concentrated in the most heavily commented
# files, which are exactly the harnesses.
BLOCK_COMMENT_LANGS = {"Arduino/C++", "C++", "C/C++ header"}


def count_lines(path: Path, lang: str) -> tuple[int, int]:
    """Total lines, and lines that are neither blank nor comment.

    A line counts as code if, after removing block comments and a trailing line comment,
    anything is left. The count is therefore of lines carrying at least one token, not of
    statements.
    """
    prefixes = COMMENT_PREFIX.get(lang, ())
    blocks = lang in BLOCK_COMMENT_LANGS
    total = code = 0
    in_block = False
    for raw in path.read_text(errors="replace").splitlines():
        total += 1
        line = raw
        if blocks:
            out = []
            i = 0
            while i < len(line):
                if in_block:
                    end = line.find("*/", i)
                    if end == -1:
                        i = len(line)
                    else:
                        in_block = False
                        i = end + 2
                else:
                    start = line.find("/*", i)
                    if start == -1:
                        out.append(line[i:])
                        break
                    out.append(line[i:start])
                    in_block = True
                    i = start + 2
            line = "".join(out)
        stripped = line.strip()
        if not stripped:
            continue
        if prefixes and stripped.startswith(prefixes):
            continue
        code += 1
    return total, code


def walk_files() -> list[Path]:
    out = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(ROOT)
        if SKIP_DIR_PARTS & set(rel.parts[:-1]):
            continue
        if path.name in SKIP_NAMES:
            continue
        if any(path.name.endswith(s) for s in SKIP_SUFFIXES):
            continue
        if any(path.match(p) for p in SKIP_PATTERNS):
            continue
        out.append(path)
    return out


def write_meta(sources: list[tuple[Path, str, int, int]]) -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()
    loc = sum(c for _, _, _, c in sources)
    (OUT / "meta.tex").write_text(
        f"\\newcommand{{\\repohead}}{{{head[:7]}}}\n"
        f"\\newcommand{{\\repohashfull}}{{{head}}}\n"
        f"\\newcommand{{\\srcfiles}}{{{len(sources)}}}\n"
        f"\\newcommand{{\\srccode}}{{{loc}}}\n"
    )
    print(f"meta.tex: {head[:7]}, {len(sources)} source files, {loc} lines of code")


def write_tree(files: list[Path]) -> None:
    counts: dict[str, int] = {}
    for path in files:
        rel = path.relative_to(ROOT)
        d = str(rel.parent) if str(rel.parent) != "." else "(root)"
        counts[d] = counts.get(d, 0) + 1

    rows = []
    for d in sorted(counts, key=lambda x: (x != "(root)", x)):
        note = DIR_NOTES.get(d, "")
        rows.append(f"\\texttt{{{tex(d)}}} & {counts[d]} & {note} \\\\")

    (OUT / "appA_tree.tex").write_text(
        "\\begin{longtable}{p{0.40\\textwidth} r p{0.42\\textwidth}}\n"
        "\\toprule\n"
        "\\textbf{Directory} & \\textbf{Files} & \\textbf{Contents} \\\\\n"
        "\\midrule\n\\endhead\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n\\end{longtable}\n"
    )
    print(f"appA_tree.tex: {len(counts)} directories")


def write_inventory(sources: list[tuple[Path, str, int, int]]) -> None:
    rows = []
    for path, lang, total, code in sources:
        rel = tex(str(path.relative_to(ROOT)))
        rows.append(f"\\texttt{{\\footnotesize {rel}}} & {lang} & {total} & {code} \\\\")
    tot = sum(t for _, _, t, _ in sources)
    loc = sum(c for _, _, _, c in sources)

    (OUT / "appB_inventory.tex").write_text(
        "\\begin{longtable}{p{0.50\\textwidth} l r r}\n"
        "\\toprule\n"
        "\\textbf{File} & \\textbf{Language} & \\textbf{Lines} & \\textbf{Code} \\\\\n"
        "\\midrule\n\\endhead\n"
        + "\n".join(rows) + "\n"
        "\\midrule\n"
        f"\\textbf{{{len(sources)} files}} & & \\textbf{{{tot}}} & \\textbf{{{loc}}} \\\\\n"
        "\\bottomrule\n\\end{longtable}\n"
    )
    print(f"appB_inventory.tex: {len(sources)} files, {tot} lines, {loc} code")


def write_experiments() -> list[str]:
    problems = []
    rows = []
    for eid, title, cls, artefact, scale in EXPERIMENTS:
        if artefact.endswith("/"):
            if not (ROOT / artefact).is_dir():
                problems.append(f"appendix G: {eid} names missing directory {artefact}")
        else:
            # Artefacts live under experiments/ or experiments/results/.
            candidates = [ROOT / "experiments" / artefact,
                          ROOT / "experiments" / "results" / artefact]
            if not any(c.exists() for c in candidates):
                problems.append(f"appendix G: {eid} names missing artefact {artefact}")
        rows.append(
            f"\\texttt{{{eid}}} & {title} & {cls} & "
            f"\\texttt{{\\footnotesize {tex(artefact)}}} & {scale} \\\\"
        )
    rows.append(
        "\\texttt{---} & Hardware conditions A--D & \\emph{not executed} & "
        "\\texttt{\\footnotesize ---} & \\emph{no data exists} \\\\"
    )

    (OUT / "appG_experiments.tex").write_text(
        "\\begin{longtable}{l p{0.30\\textwidth} p{0.15\\textwidth} p{0.17\\textwidth} "
        "p{0.20\\textwidth}}\n"
        "\\toprule\n"
        "\\textbf{ID} & \\textbf{Experiment} & \\textbf{Evidence class} & "
        "\\textbf{Artefact} & \\textbf{Scale} \\\\\n"
        "\\midrule\n\\endhead\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n\\end{longtable}\n"
    )
    print(f"appG_experiments.tex: {len(EXPERIMENTS)} experiments + the unexecuted conditions")
    return problems


def find_figure(name: str) -> Path | None:
    for d in FIGURE_SEARCH:
        p = ROOT / d / name
        if p.exists():
            return p
    return None


def write_figures() -> list[str]:
    problems = []
    rows = []

    def row(label: str, title: str, name: str, gen: str) -> str:
        if find_figure(name) is None:
            problems.append(f"appendix H: missing figure file {name}")
        if not (ROOT / gen).exists():
            problems.append(f"appendix H: missing generator {gen}")
        return (f"{label} & {title} & \\texttt{{\\footnotesize {tex(name)}}} & "
                f"\\texttt{{\\footnotesize {tex(gen)}}} \\\\")

    for num, title, name, gen in MANUSCRIPT_FIGURES:
        rows.append(row(str(num), title, name, gen))
    rows.append("\\midrule")
    rows.append("\\multicolumn{4}{l}{\\textit{Repository documentation figures, not part of "
                "the manuscript}}\\\\")
    rows.append("\\midrule")
    for title, name, gen in DOC_FIGURES:
        rows.append(row("---", title, name, gen))

    (OUT / "appH_figures.tex").write_text(
        "\\begin{longtable}{l p{0.30\\textwidth} p{0.26\\textwidth} p{0.26\\textwidth}}\n"
        "\\toprule\n"
        "\\textbf{No.} & \\textbf{Title} & \\textbf{File} & \\textbf{Generator} \\\\\n"
        "\\midrule\n\\endhead\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n\\end{longtable}\n"
    )
    print(f"appH_figures.tex: {len(MANUSCRIPT_FIGURES)} manuscript + {len(DOC_FIGURES)} "
          "documentation figures")
    return problems


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = walk_files()

    sources: list[tuple[Path, str, int, int]] = []
    for path in files:
        lang = LANG_BY_SUFFIX.get(path.suffix)
        if lang is None:
            continue
        total, code = count_lines(path, lang)
        sources.append((path, lang, total, code))
    sources.sort(key=lambda t: str(t[0].relative_to(ROOT)))

    write_meta(sources)
    write_tree(files)
    write_inventory(sources)
    problems = write_experiments() + write_figures()

    if problems:
        print("\nFAIL: a curated entry names something that is not in the repository:",
              file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("\nall curated entries resolve to files that exist")
    return 0


if __name__ == "__main__":
    sys.exit(main())
