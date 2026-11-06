#!/usr/bin/env python3
"""Generate the publication diagrams as SVG, then PDF and PNG.

Editable source for the figures in docs/images/. Run from anywhere:

    python3 docs/figures/make_diagrams.py

Design rules enforced here, because journals and reviewers check them:

* Greyscale-safe. Nothing is distinguished by hue alone. Every distinction is
  carried by a line style (solid / dashed / dotted), a fill lightness that
  survives desaturation, or a text label.
* Consistent typography. One font stack, four sizes, used for the same roles
  in every figure.
* Legible at print size. Minimum 11 px type in a figure no wider than 1100
  units, which is about 8 pt at a 90 mm single-column width.
* Unambiguous arrows. Every arrowhead means "control or data flows this way";
  dashed means "optional or not implemented"; dotted means "observation only,
  no data path".
"""

import os
import subprocess
import sys

# ---------------------------------------------------------------- style ------
FONT = "DejaVu Sans, Arial, Helvetica, sans-serif"
INK = "#1B1F23"       # primary text
MUTED = "#4A5560"     # secondary text
LINE = "#2F3A45"      # connectors and borders

# Fills chosen so their greyscale luminance differs by at least ~12 %:
# light (#F4F6F8 ~ 96 %), mid (#DCE3EA ~ 88 %), dark (#B8C4D0 ~ 76 %).
LIGHT, MID, DARK = "#F4F6F8", "#DCE3EA", "#B8C4D0"
SAFETY, NETWORK = "#E9F7EF", "#E8F1FB"   # domain tints, both near-white in grey

SZ = {"title": 18, "head": 15, "body": 12.5, "small": 11}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Fig:
    """Minimal SVG builder. Coordinates are user units; 1 unit renders as 1 px."""

    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.p = []

    # -- primitives
    def box(self, x, y, w, h, fill=LIGHT, stroke=LINE, dash=None, rx=10, sw=1.6):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.p.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'
        )

    def text(self, x, y, s, size="body", anchor="middle", fill=INK, bold=False, mono=False):
        fam = '"DejaVu Sans Mono", monospace' if mono else FONT
        w = ' font-weight="bold"' if bold else ""
        self.p.append(
            f'<text x="{x}" y="{y}" font-size="{SZ[size]}" font-family=\'{fam}\' '
            f'text-anchor="{anchor}" fill="{fill}"{w}>{esc(s)}</text>'
        )

    def lines(self, x, y, rows, size="small", anchor="middle", fill=MUTED, lh=None):
        lh = lh or SZ[size] + 4
        for i, r in enumerate(rows):
            self.text(x, y + i * lh, r, size=size, anchor=anchor, fill=fill)

    def arrow(self, pts, dash=None, stroke=LINE, head=True, sw=1.8):
        d = "M" + " L".join(f"{a} {b}" for a, b in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        mk = ' marker-end="url(#arr)"' if head else ""
        self.p.append(
            f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}"{da}{mk}/>'
        )

    def label(self, x, y, rows, anchor="middle"):
        self.lines(x, y, rows, size="small", anchor=anchor)

    def render(self):
        defs = (
            '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M0 0 L10 5 L0 10 z" fill="{LINE}"/></marker></defs>'
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" font-family=\'{FONT}\'>'
            f"<title>{esc(self.title)}</title>"
            f'<rect width="100%" height="100%" fill="#FFFFFF"/>{defs}'
            + "".join(self.p)
            + "</svg>"
        )


# ------------------------------------------------- 1. command execution ------
def command_flow():
    """Command path, showing which core performs each stage."""
    f = Fig(1100, 760, "Command execution flow across the two cores")
    f.text(550, 34, "Command execution flow", size="title", bold=True)
    f.lines(550, 56, [
        "Parsing and HMAC verification run on core 0, so a command flood costs the safety core no time."
    ], size="small")

    # domain bands
    f.box(40, 80, 1020, 300, fill=NETWORK, dash="7 5", rx=14)
    f.text(60, 104, "CORE 0  —  network domain  (networkTask, priority 1, 8 KB stack)",
           size="head", anchor="start", bold=True)
    f.box(40, 430, 1020, 290, fill=SAFETY, dash="7 5", rx=14)
    f.text(60, 454, "CORE 1  —  safety domain  (Arduino loop)",
           size="head", anchor="start", bold=True)

    # core 0 stages
    st = [("MQTT\nmessage", 80), ("topic\nfilter", 250), ("parse\npayload", 420),
          ("verify\nHMAC tag", 590), ("enqueue\ncmdQ", 790)]
    for (lab, x) in st:
        w = 150 if "enqueue" not in lab else 170
        f.box(x, 150, w, 86, fill=MID)
        a, b = lab.split("\n")
        f.text(x + w / 2, 182, a, size="body", bold=True)
        f.text(x + w / 2, 202, b, size="body")
    for x0, x1 in [(230, 250), (400, 420), (570, 590), (740, 790)]:
        f.arrow([(x0, 193), (x1, 193)])

    # rejection paths out of core 0
    f.box(300, 282, 460, 72, fill=LIGHT, dash="4 3")
    f.text(530, 306, "rejected on core 0  —  never reaches the safety core", size="body", bold=True)
    f.lines(530, 328, [
        "malformed: dropped silently   ·   bad tag: cmd_badmac   ·   unsigned: cmd_unauth"
    ], size="small")
    f.arrow([(495, 236), (495, 282)], dash="4 3")
    f.arrow([(665, 236), (620, 282)], dash="4 3")

    # the queue crossing
    f.box(790, 386, 170, 58, fill=DARK, rx=8)
    f.text(875, 412, "cmdQ  depth 4", size="body", bold=True)
    f.text(875, 430, "bounded, non-blocking", size="small", fill=MUTED)
    f.arrow([(875, 236), (875, 386)], sw=2.4)

    # core 1 stages
    f.box(700, 470, 260, 86, fill=MID)
    f.text(830, 500, "dequeue, timeout 0", size="body", bold=True)
    f.text(830, 522, "xQueueReceive(cmdQ, &m, 0)", size="small", fill=MUTED, mono=True)
    f.text(830, 542, "the safety loop never waits", size="small", fill=MUTED)

    f.box(420, 470, 230, 86, fill=MID)
    f.text(535, 500, "freshness check", size="body", bold=True)
    f.text(535, 522, "m.ctr > cmdCounter", size="small", fill=MUTED, mono=True)
    f.text(535, 542, "else cmd_replay", size="small", fill=MUTED)

    f.box(150, 470, 220, 86, fill=MID)
    f.text(260, 496, "persist counter", size="body", bold=True)
    f.text(260, 518, "NVS write BEFORE acting:", size="small", fill=MUTED)
    f.text(260, 536, "a crash cannot replay", size="small", fill=MUTED)

    f.box(150, 600, 500, 92, fill=LIGHT)
    f.text(400, 626, "authorise and execute", size="body", bold=True)
    f.lines(400, 648, [
        "DISARM requires m.authed OR ALLOW_REMOTE_DISARM, else cmd_rejected",
        "ARM / ARM_AWAY only from DISARMED, else cmd_ignored   ·   STATUS publishes",
    ], size="small")

    f.arrow([(700, 513), (650, 513)])
    f.arrow([(420, 513), (370, 513)])
    f.arrow([(260, 556), (260, 600)])

    # response path back up
    f.box(700, 600, 260, 92, fill=LIGHT, dash="4 3")
    f.text(830, 626, "response", size="body", bold=True)
    f.lines(830, 648, [
        "retained state publish",
        "plus one outcome event",
        "no acknowledgement protocol",
    ], size="small")
    f.arrow([(650, 646), (700, 646)], dash="4 3")

    f.text(550, 738,
           "Dashed: rejection and reporting paths.  Solid: the accepted-command path.",
           size="small", fill=MUTED)
    return f


# ------------------------------------------------- 2. command sequence -------
def command_sequence():
    """UML sequence diagram for an authenticated DISARM."""
    f = Fig(1060, 700, "Sequence diagram: authenticated remote DISARM")
    f.text(530, 34, "Sequence: authenticated remote DISARM", size="title", bold=True)

    actors = [("Operator", 90), ("MQTT broker", 270), ("networkTask\n(core 0)", 470),
              ("cmdQ", 650), ("safety loop\n(core 1)", 830), ("NVS", 990)]
    for lab, x in actors:
        rows = lab.split("\n")
        f.box(x - 78, 62, 156, 34 + 18 * (len(rows) - 1), fill=MID, rx=8)
        for i, r in enumerate(rows):
            f.text(x, 84 + i * 18, r, size="body", bold=(i == 0))
        # lifeline
        f.p.append(f'<path d="M{x} {100 + 18 * (len(rows) - 1)} L{x} 630" '
                   f'stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="5 5"/>')

    def msg(y, x0, x1, text, note=None, dash=None):
        f.arrow([(x0, y), (x1, y)], dash=dash)
        mid = (x0 + x1) / 2
        f.text(mid, y - 9, text, size="small", fill=INK)
        if note:
            f.text(mid, y + 15, note, size="small", fill=MUTED)

    msg(165, 90, 270, "publish DISARM:1001:<tag>", "tag = HMAC-SHA256(K, \"DISARM:1001\")[0:16]")
    msg(220, 270, 470, "deliver on command topic")
    f.box(392, 250, 156, 54, fill=LIGHT, rx=8)
    f.text(470, 272, "verifySigned()", size="small", bold=True)
    f.text(470, 290, "ct_equal, constant time", size="small", fill=MUTED)
    msg(340, 470, 650, "enqueue {DISARM, authed, 1001}")
    msg(385, 650, 830, "dequeue, timeout 0")
    f.box(752, 405, 156, 40, fill=LIGHT, rx=8)
    f.text(830, 430, "1001 > cmdCounter ?", size="small", bold=True)
    msg(480, 830, 990, "persistCounter(1001)", "before acting, so a crash cannot replay")
    msg(530, 990, 830, "ack", dash="4 3")
    f.box(752, 548, 156, 40, fill=LIGHT, rx=8)
    f.text(830, 573, "disarm(): state := DISARMED", size="small", bold=True)
    msg(620, 830, 470, "event: disarmed", dash="4 3")

    f.text(530, 668,
           "Dashed arrows are reporting, not control. The operator receives no direct "
           "acknowledgement:", size="small", fill=MUTED)
    f.text(530, 686,
           "the outcome is inferred from the retained state topic and the event stream.",
           size="small", fill=MUTED)
    return f


# ------------------------------------------------- 3. deployment -------------
def deployment():
    """Hardware and software deployment, marking what is optional and what is unbuilt."""
    f = Fig(1100, 700, "Deployment architecture")
    f.text(550, 34, "Deployment architecture", size="title", bold=True)
    f.lines(550, 56, [
        "Solid: required. Dashed: optional, compiles in CI, never run on hardware. "
        "Dotted: experiment apparatus, never run."
    ], size="small")

    # required device
    f.box(60, 90, 400, 250, fill=SAFETY, sw=2.2)
    f.text(260, 118, "ESP32 DevKit  —  alarm device", size="head", bold=True)
    f.text(260, 140, "firmware/smart_home  (v2.2.0)", size="small", fill=MUTED, mono=True)
    for i, (lab, sub) in enumerate([
        ("Core 1: FSM, siren, OLED", "safety domain"),
        ("Core 0: Wi-Fi, MQTT, HMAC", "network domain"),
        ("NVS: armed flag, cmd counter", "survives power cut"),
    ]):
        y = 162 + i * 56
        f.box(80, y, 360, 46, fill=LIGHT, rx=8)
        f.text(260, y + 21, lab, size="body", bold=True)
        f.text(260, y + 38, sub, size="small", fill=MUTED)

    # sensors
    f.box(60, 370, 400, 110, fill=MID)
    f.text(260, 396, "Peripherals", size="head", bold=True)
    f.lines(260, 418, [
        "PIR HC-SR501 (GPIO 13)  ·  door reed switch (GPIO 14)  ·  button (GPIO 27)",
        "buzzer (GPIO 23)  ·  LEDs (GPIO 25, 26)  ·  SSD1306 OLED (I2C 21/22)",
        "LD2410 mmWave radar (GPIO 33) — optional, fusion modes only",
    ], size="small")

    # broker + HA
    f.box(540, 90, 250, 120, fill=NETWORK)
    f.text(665, 118, "MQTT broker", size="head", bold=True)
    f.lines(665, 140, [
        "events, commands,", "Last Will, retained state", "OPTIONAL: alarm works offline",
    ], size="small")

    f.box(540, 240, 250, 110, fill=NETWORK)
    f.text(665, 266, "Home Assistant", size="head", bold=True)
    f.lines(665, 288, [
        "auto-configured by", "retained discovery", "OPTIONAL consumer",
    ], size="small")

    f.box(540, 380, 250, 100, fill=LIGHT, dash="6 4")
    f.text(665, 406, "Second ESP32", size="head", bold=True)
    f.lines(665, 428, [
        "espnow_receiver", "signed fallback alerts", "when MQTT is unreachable",
    ], size="small")

    # experiment apparatus
    f.box(850, 90, 210, 390, fill=LIGHT, dash="2 4")
    f.text(955, 118, "Experiment rig", size="head", bold=True)
    f.text(955, 138, "NOT YET RUN", size="small", bold=True, fill=INK)
    f.box(870, 160, 170, 120, fill=MID, dash="2 4", rx=8)
    f.text(955, 186, "Third ESP32", size="body", bold=True)
    f.lines(955, 208, [
        "latency_probe:", "independent clock,", "measures sensor to", "siren by logic probe",
    ], size="small")
    f.box(870, 300, 170, 100, fill=MID, dash="2 4", rx=8)
    f.text(955, 326, "Host PC", size="body", bold=True)
    f.lines(955, 348, [
        "collect.py (serial)", "analyse_hw.py", "Mann-Whitney U",
    ], size="small")
    f.text(955, 440, "Condition D also needs", size="small", fill=MUTED)
    f.text(955, 456, "an authorised isolated", size="small", fill=MUTED)
    f.text(955, 472, "RF environment", size="small", fill=MUTED)

    # connectors
    f.arrow([(460, 150), (540, 150)], sw=2.2); f.label(500, 140, ["MQTT"])
    f.arrow([(665, 210), (665, 240)])
    f.arrow([(460, 420), (540, 420)], dash="6 4"); f.label(500, 410, ["ESP-NOW"])
    f.arrow([(460, 250), (870, 250)], dash="2 4")
    f.label(690, 236, ["GPIO probe lines"])

    # software env
    f.box(60, 510, 1000, 150, fill=LIGHT)
    f.text(560, 536, "Software environment used for the committed results", size="head", bold=True)
    f.lines(560, 560, [
        "Device: arduino-esp32 2.0.17 and 3.3.12  ·  Adafruit SSD1306, Adafruit GFX, PubSubClient",
        "Host: Linux 6.18.44  ·  g++ 13 (C++17)  ·  Python 3.13.16  ·  OpenJDK 21 (CI uses 17)",
        "Verification: TLA+ tla2tools v1.8.0 (pinned)  ·  AddressSanitizer + UndefinedBehaviorSanitizer",
        "CI: ubuntu-24.04, 5 jobs, re-runs formal and adversarial checks on every push",
    ], size="small")
    return f


# ------------------------------------------------- 4. methodology ------------
def methodology():
    """End-to-end research methodology, with the open step marked."""
    f = Fig(1100, 560, "Research methodology workflow")
    f.text(550, 34, "Research methodology", size="title", bold=True)
    f.lines(550, 56, [
        "Four evidence routes. Three are complete; the fourth is specified and unrun, "
        "and it is the one the headline claim needs."
    ], size="small")

    f.box(60, 90, 220, 90, fill=MID)
    f.text(170, 118, "Research question", size="head", bold=True)
    f.lines(170, 138, [
        "Does core pinning isolate", "the safety function when the",
        "on-die radio is attacked?",
    ], size="small")

    f.box(60, 210, 220, 90, fill=LIGHT)
    f.text(170, 236, "Literature gap", size="head", bold=True)
    f.lines(170, 256, [
        "14 works verified against", "publisher records.",
        "No prior work measures it.",
    ], size="small")
    f.arrow([(170, 180), (170, 210)])

    # four routes
    routes = [
        ("Formal", ["2 TLA+ models, TLC", "25 and 660 states", "mutation-tested"], "COMPLETE", MID),
        ("Simulation", ["6,000 seeded trials", "0 attacker disarms", "0 violations"], "COMPLETE", MID),
        ("Fuzzing", ["3,000,000 iterations", "ASan + UBSan", "0 accepted inputs"], "COMPLETE", MID),
        ("Hardware", ["Conditions A-D", "latency distributions", "apparatus built"], "NOT RUN", LIGHT),
    ]
    for i, (name, rows, status, fill) in enumerate(routes):
        x = 350 + i * 185
        dash = "6 4" if status == "NOT RUN" else None
        f.box(x, 150, 165, 140, fill=fill, dash=dash)
        f.text(x + 82, 178, name, size="head", bold=True)
        f.lines(x + 82, 200, rows, size="small")
        f.text(x + 82, 268, status, size="small", bold=True)
        # The four routes are INDEPENDENT, not sequential: the gap fans out to each
        # via a shared bus, so no arrow ever runs from one route to the next.
        f.arrow([(315, 240), (315, 120), (x + 82, 120), (x + 82, 150)], dash=dash)
    f.arrow([(280, 240), (315, 240)], head=False)

    f.box(350, 330, 710, 90, fill=LIGHT)
    f.text(705, 358, "What the three complete routes establish", size="head", bold=True)
    f.lines(705, 380, [
        "LOGICAL isolation: no code path makes the safety response depend on network input,",
        "and the authenticated command path rejects every forged, stale and malformed input.",
    ], size="small")
    f.arrow([(432, 290), (432, 330)])
    f.arrow([(617, 290), (617, 330)])
    f.arrow([(802, 290), (802, 330)])

    f.box(350, 450, 710, 80, fill=LIGHT, dash="6 4")
    f.text(705, 478, "What remains open", size="head", bold=True)
    f.lines(705, 500, [
        "TIMING isolation: a property of the silicon, the interrupt controller and the closed-source",
        "radio driver. It cannot be simulated, and no latency number is claimed anywhere.",
    ], size="small")
    f.arrow([(987, 290), (987, 450)], dash="6 4")
    return f


# ------------------------------------------------- 5. experimental setup -----
def experimental_setup():
    """Experimental setup: the simulation harness and the hardware rig."""
    f = Fig(1100, 620, "Experimental setup")
    f.text(550, 34, "Experimental setup", size="title", bold=True)

    # simulation side
    f.box(50, 70, 500, 500, fill=LIGHT, sw=2.2)
    f.text(300, 98, "A.  Simulation harness  —  USED FOR ALL COMMITTED RESULTS",
           size="head", bold=True)

    f.box(80, 120, 440, 100, fill=MID)
    f.text(300, 146, "Unmodified firmware logic", size="body", bold=True)
    f.lines(300, 168, [
        "smart_home.ino compiled against host stubs for Arduino,",
        "FreeRTOS, WiFi, MQTT, NVS and the OLED. The firmware",
        "source is not altered for testing.",
    ], size="small")

    f.box(80, 240, 205, 120, fill=MID)
    f.text(182, 266, "Campaign", size="body", bold=True)
    f.lines(182, 288, [
        "6,000 trials", "seed base 1000",
        "rates 0 to 20,000", "msg/s", "fork() per trial",
    ], size="small")

    f.box(315, 240, 205, 120, fill=MID)
    f.text(417, 266, "Fuzzer", size="body", bold=True)
    f.lines(417, 288, [
        "3,000,000 iters", "seed 7, 6 classes",
        "ASan + UBSan", "oracle: no state", "change, no counter",
    ], size="small")

    f.box(80, 380, 440, 80, fill=LIGHT, dash="4 3")
    f.text(300, 406, "Limitation that defines the open step", size="body", bold=True)
    f.lines(300, 428, [
        "The harness advances a logical clock. There is no radio, no true",
        "parallel execution and no CPU contention, so latency variance is zero.",
    ], size="small")

    f.box(80, 480, 440, 70, fill=MID)
    f.text(300, 506, "Analysis", size="body", bold=True)
    f.lines(300, 526, [
        "analyse.py: aggregation, Mann-Whitney U with tie correction,",
        "standard library only. make_figures.py: validated palette.",
    ], size="small")

    # hardware side
    f.box(570, 70, 480, 500, fill=LIGHT, dash="2 4", sw=2.2)
    f.text(810, 98, "B.  Hardware rig  —  SPECIFIED, NOT YET RUN", size="head", bold=True)

    f.box(600, 120, 190, 90, fill=MID, dash="2 4")
    f.text(695, 148, "Device under test", size="body", bold=True)
    f.lines(695, 168, ["ESP32 DevKit", "running v2.2.0", "unmodified"], size="small")

    f.box(830, 120, 190, 90, fill=MID, dash="2 4")
    f.text(925, 148, "Measuring board", size="body", bold=True)
    f.lines(925, 168, ["second ESP32,", "independent clock,", "logic probe"], size="small")
    f.arrow([(790, 150), (830, 150)], dash="2 4")
    f.label(810, 136, ["GPIO"])

    f.box(600, 240, 420, 150, fill=LIGHT, dash="2 4")
    f.text(810, 266, "Four conditions", size="body", bold=True)
    for i, (c, d, rf) in enumerate([
        ("A", "idle (control)", "no RF isolation"),
        ("B", "legitimate network load", "no RF isolation"),
        ("C", "command-interface stress", "no RF isolation"),
        ("D", "radio-layer stress", "AUTHORISED ISOLATED RF ONLY"),
    ]):
        y = 290 + i * 24
        f.text(620, y, f"{c}.", size="small", anchor="start", bold=True, fill=INK)
        f.text(645, y, d, size="small", anchor="start", fill=INK)
        f.text(1000, y, rf, size="small", anchor="end", fill=MUTED)

    f.box(600, 410, 420, 80, fill=MID, dash="2 4")
    f.text(810, 436, "Dependent variable", size="body", bold=True)
    f.lines(810, 458, [
        "Physical sensor-to-siren latency distribution, compared across",
        "conditions with the same non-parametric test (analyse_hw.py).",
    ], size="small")

    f.box(600, 510, 420, 40, fill=LIGHT, dash="4 3")
    f.text(810, 535, "A to C need two boards and a probe. No attack tooling is published.",
           size="small", bold=True)
    return f


# ---------------------------------------------------------------- driver -----
FIGS = {
    "command_flow": command_flow,
    "command_sequence": command_sequence,
    "deployment": deployment,
    "methodology": methodology,
    "experimental_setup": experimental_setup,
}


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(here, "..", "images"))
    os.makedirs(out, exist_ok=True)

    import cairosvg

    for name, fn in FIGS.items():
        svg = fn().render()
        sp = os.path.join(out, name + ".svg")
        with open(sp, "w") as fh:
            fh.write(svg)
        cairosvg.svg2pdf(url=sp, write_to=os.path.join(out, name + ".pdf"))
        cairosvg.svg2png(url=sp, write_to=os.path.join(out, name + ".png"), scale=2.5)
        print(f"  {name}: svg + pdf + png")

    # Re-export the hand-written diagrams to PDF so every figure has a vector
    # form suitable for LaTeX submission.
    for name in ("architecture", "state_machine", "event_sequence", "circuit_wiring"):
        sp = os.path.join(out, name + ".svg")
        if os.path.exists(sp):
            cairosvg.svg2pdf(url=sp, write_to=os.path.join(out, name + ".pdf"))
            print(f"  {name}: pdf re-exported")


if __name__ == "__main__":
    sys.exit(main())
