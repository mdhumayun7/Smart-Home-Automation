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
import textwrap
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
EXTERNAL, SHARED = "#F2F4F7", "#F1EAFB"  # outside the device; internal shared state

# House palette, shared with the hand-authored diagrams (architecture.svg and
# state_machine.svg) so every figure in the paper reads as one set. Each pair is
# (fill, stroke); all fills stay near-white so greyscale printing survives.
PAL = {
    "external":  ("#F2F4F7", "#475467"),   # operator, broker: outside the device
    "sensing":   ("#E8F1FB", "#2B6CB0"),
    "network":   ("#FFF4E0", "#B26A00"),   # core 0
    "safety":    ("#E9F7EF", "#2E7D32"),   # core 1
    "shared":    ("#F1EAFB", "#6B46C1"),   # queues and NVS: internal shared resources
    "output":    ("#FDECEC", "#C0392B"),
}

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

    def vline(self, x, y0, y1, stroke=MUTED, dash="5 5", sw=1.2):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.p.append(f'<path d="M{x} {y0} L{x} {y1}" stroke="{stroke}" '
                      f'stroke-width="{sw}" fill="none"{d}/>')

    def actbar(self, x, y0, y1, stroke, w=11):
        """UML activation bar: the participant is executing over this interval."""
        self.p.append(f'<rect x="{x - w / 2}" y="{y0}" width="{w}" height="{y1 - y0}" '
                      f'fill="#FFFFFF" stroke="{stroke}" stroke-width="1.5"/>')

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
    """UML sequence diagram for an authenticated remote DISARM.

    Styled to match the hand-authored diagrams: title and subtitle, participants
    coloured by the domain they belong to, UML activation bars, a trust boundary,
    the rejection paths, and a legend.
    """
    W, H = 1500, 1250
    f = Fig(W, H, "Command execution sequence: authenticated remote DISARM")
    f.text(W / 2, 40, "Smart Home Surveillance System v2 - Command Execution Sequence",
           size="title", bold=True)
    f.text(W / 2, 64, "Authenticated remote DISARM: HMAC-SHA256 over a reboot-persistent "
                      "counter, verified on core 0", size="body", fill=MUTED)

    BOT = 975
    NOTE_W = 220          # clears the narrowest lifeline gap (safety->NVS = 250)
    parts = [
        ("Operator",     "external", 110,  ["MQTT client"]),
        ("MQTT broker",  "external", 350,  ["untrusted"]),
        ("networkTask",  "network",  610,  ["core 0"]),
        ("cmdQ",         "shared",   880,  ["depth 4"]),
        ("safety loop",  "safety",   1120, ["core 1"]),
        ("NVS",          "shared",   1370, ["flash"]),
    ]
    xs = {n: x for n, _, x, _ in parts}
    col = {n: PAL[k] for n, k, _, _ in parts}

    # trust boundary between the broker and the device
    f.vline(480, 108, BOT + 30, stroke="#C0392B", dash="9 6", sw=2)
    f.text(480, 100, "TRUST BOUNDARY", size="small", bold=True, fill="#C0392B")
    f.text(470, BOT + 46, "untrusted", size="small", fill="#C0392B", anchor="end")
    f.text(490, BOT + 46, "device", size="small", fill="#C0392B", anchor="start")

    for name, kind, x, sub in parts:
        fill, stroke = PAL[kind]
        f.box(x - 98, 112, 196, 48, fill=fill, stroke=stroke, rx=10, sw=2)
        f.text(x, 134, name, size="head", bold=True)
        f.text(x, 152, sub[0], size="small", fill=MUTED)
        f.vline(x, 160, BOT + 20)

    # activation bars
    f.actbar(xs["Operator"], 205, 228, col["Operator"][1])
    f.actbar(xs["MQTT broker"], 208, 300, col["MQTT broker"][1])
    f.actbar(xs["networkTask"], 283, 515, col["networkTask"][1])
    f.actbar(xs["cmdQ"], 498, 575, col["cmdQ"][1])
    f.actbar(xs["safety loop"], 556, 876, col["safety loop"][1])
    f.actbar(xs["NVS"], 682, 756, col["NVS"][1])
    f.actbar(xs["networkTask"], 856, 916, col["networkTask"][1])
    f.actbar(xs["MQTT broker"], 896, 956, col["MQTT broker"][1])
    f.actbar(xs["Operator"], 936, 958, col["Operator"][1])

    def step(n, y, a, b, text, note=None, dash=None):
        """One message. The badge sits at the arrow's origin and the label is
        aligned away from it, so a number can never land on top of its own text."""
        x0, x1 = xs[a], xs[b]
        right = x1 > x0
        f.arrow([(x0, y), (x1, y)], dash=dash)
        bx = x0 + (16 if right else -16)
        f.p.append(f'<circle cx="{bx}" cy="{y - 15}" r="10" fill="{INK}"/>')
        f.text(bx, y - 11, str(n), size="small", fill="#FFFFFF", bold=True)
        tx = x0 + (32 if right else -32)
        anchor = "start" if right else "end"
        f.text(tx, y - 11, text, size="body", fill=INK, anchor=anchor)
        if note:
            f.text(tx, y + 17, note, size="small", fill=MUTED, anchor=anchor)

    def selfnote(x, y, h, title, rows, kind, dash=None):
        """A processing note, kept inside the gap to the next lifeline."""
        fill, stroke = PAL[kind]
        f.box(x + 20, y, NOTE_W, h, fill=fill, stroke=stroke, rx=8, dash=dash)
        cx = x + 20 + NOTE_W / 2
        f.text(cx, y + 21, title, size="small", bold=True)
        f.lines(cx, y + 39, rows, size="small")

    step(1, 215, "Operator", "MQTT broker", "publish  DISARM:1001:<tag>",
         'tag = HMAC-SHA256(K, msg)[0:16]')
    step(2, 300, "MQTT broker", "networkTask", "deliver on  .../cmd")

    selfnote(xs["networkTask"], 318, 76, "parse and verify   (core 0)",
             ["parse <VERB>:<ctr>:<hex-tag>",
              "recompute tag, compare ct_equal"], "network")

    selfnote(xs["networkTask"], 410, 76, "rejected here, never enqueued",
             ["bad tag -> cmd_badmac", "unsigned -> cmd_unauth",
              "malformed -> dropped silently"], "output", dash="5 4")

    step(3, 515, "networkTask", "cmdQ", "enqueue  {DISARM, authed, 1001}",
         "a flood cannot displace it")
    step(4, 575, "cmdQ", "safety loop", "xQueueReceive(cmdQ, &m, 0)",
         "zero timeout: never waits")

    selfnote(xs["safety loop"], 600, 58, "freshness:  1001 > cmdCounter ?",
             ["else cmd_replay, no state change"], "safety")

    step(5, 695, "safety loop", "NVS", "persistCounter(1001)",
         "committed BEFORE acting")
    step(6, 756, "NVS", "safety loop", "committed", dash="4 3")

    selfnote(xs["safety loop"], 778, 76, "authorise and execute",
             ["m.authed is true -> disarm()",
              "state := DISARMED, 150 ms beep"], "safety")

    step(7, 876, "safety loop", "networkTask", "event: disarmed  (via eventQ)", dash="4 3")
    step(8, 916, "networkTask", "MQTT broker", "publish event + retained state", dash="4 3")
    step(9, 956, "MQTT broker", "Operator", "retained state", dash="4 3")

    # legend
    f.box(50, 1035, W - 100, 182, fill="#FBFBFC", stroke=LINE, rx=12)
    f.text(74, 1061, "LEGEND", size="body", anchor="start", bold=True)
    leg = [
        ("external", "Outside the device (untrusted)"),
        ("network", "Core 0: network domain"),
        ("safety", "Core 1: safety domain"),
        ("shared", "Internal shared resource"),
        ("output", "Rejection path"),
    ]
    for i, (k, lab) in enumerate(leg):
        x = 74 + (i % 3) * 330
        y = 1083 + (i // 3) * 30
        fill, stroke = PAL[k]
        f.box(x, y, 26, 18, fill=fill, stroke=stroke, rx=4, sw=1.6)
        f.text(x + 36, y + 14, lab, size="small", anchor="start", fill=INK)

    f.p.append(f'<path d="M1070 1092 L1130 1092" stroke="{LINE}" stroke-width="1.8" '
               f'marker-end="url(#arr)"/>')
    f.text(1140, 1096, "control flow", size="small", anchor="start")
    f.p.append(f'<path d="M1070 1122 L1130 1122" stroke="{LINE}" stroke-width="1.8" '
               f'stroke-dasharray="4 3" marker-end="url(#arr)"/>')
    f.text(1140, 1126, "reporting, not control", size="small", anchor="start")

    f.lines(74, 1163, [
        "Step 5 commits the counter to flash before the command is acted on, so an interruption "
        "can at worst burn a counter value: it cannot leave the command replayable.",
    ], size="small", anchor="start")
    f.text(74, 1181, "The operator gets no direct acknowledgement: there is no command-ack "
                     "protocol, so the outcome is inferred from the retained state topic and the "
                     "event stream.", size="small", anchor="start", fill=MUTED)
    f.text(74, 1199, "Steps 7 to 9 are therefore best-effort reporting at MQTT QoS 0 "
                     "(at-most-once delivery).", size="small", anchor="start", fill=MUTED)
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


# ------------------------------------------- 6. transport vs application auth -
def security_paths():
    """Where broker credentials decide admission and where the command key decides authority.

    Every relationship drawn is taken from the implementation: broker admission is modelled by
    deliverGuarded/admit in experiments/ablation.cpp; the device-side checks are handleCommands
    in firmware/smart_home/smart_home.ino. The counts are measured, from
    experiments/results/ablation.jsonl (300 trials per arm).
    """
    OK, BAD = "#2E7D32", "#C0392B"
    OKF, BADF = "#E9F7EF", "#FDECEC"
    f = Fig(1280, 820, "Transport-layer admission against application-layer authorization")
    f.text(640, 36, "Transport security does not supply command authorization",
           size="title", bold=True)
    f.lines(640, 60, [
        "The broker terminates TLS and re-originates every message, so an arriving command "
        "carries no evidence of who published it.",
        "Broker credentials decide admission. Only the command key decides authority.",
    ], size="small")

    XP, WP = 56, 250          # publisher
    XB, WB = 346, 150         # broker
    XC, WC = 536, 250         # device-side check
    XO, WO = 836, 388         # outcome

    def header(y):
        for x, w, t in ((XP, WP, "Publisher"), (XB, WB, "Broker"),
                        (XC, WC, "Device check"), (XO, WO, "Outcome")):
            f.text(x + w / 2, y, t, size="small", bold=True, fill=MUTED)

    def row(y, who, sub, admit, check, chk_ok, outcome, out_ok, h=62):
        col = OK if out_ok else BAD
        f.box(XP, y, WP, h, fill="#FFFFFF")
        f.text(XP + WP / 2, y + 26, who, size="body", bold=True)
        f.text(XP + WP / 2, y + 46, sub, size="small", fill=MUTED)

        f.arrow([(XP + WP, y + h / 2), (XB - 6, y + h / 2)], stroke=col)
        f.box(XB, y, WB, h, fill=OKF if admit else BADF,
              stroke=LINE if admit else BAD)
        f.text(XB + WB / 2, y + h / 2 + 5, "admits" if admit else "refuses",
               size="small", bold=True, fill=INK if admit else BAD)

        if not admit:
            f.text(XC + WC / 2, y + h / 2 + 5, "never reached", size="small", fill=MUTED)
            f.box(XO, y, WO, h, fill=OKF, stroke=OK)
            f.text(XO + WO / 2, y + h / 2 + 5, outcome, size="small", bold=True, fill=OK)
            return
        f.arrow([(XB + WB, y + h / 2), (XC - 6, y + h / 2)], stroke=col)
        f.box(XC, y, WC, h, fill=OKF if chk_ok else BADF,
              stroke=LINE if chk_ok else BAD)
        f.lines(XC + WC / 2, y + 24, check, size="small",
                fill=INK if chk_ok else BAD)
        f.arrow([(XC + WC, y + h / 2), (XO - 6, y + h / 2)], stroke=col)
        f.box(XO, y, WO, h, fill=OKF if out_ok else BADF, stroke=OK if out_ok else BAD)
        f.text(XO + WO / 2, y + h / 2 + 5, outcome, size="small", bold=True, fill=col)

    # ---------------- panel 1: the default build
    f.box(36, 110, 1208, 268, fill=SAFETY, dash="7 5", rx=14)
    f.text(56, 136, "AUTH_COMMANDS = 1    —  application-layer authentication required",
           size="head", anchor="start", bold=True)
    f.text(56, 158, "A command is acted on only if its HMAC-SHA256 tag verifies under "
                    "SECRET_CMD_KEY and its counter exceeds the value in NVS.",
           size="small", anchor="start", fill=MUTED)
    header(186)
    row(196, "Operator", "holds credentials and key", True,
        ["tag verifies,", "counter advances"], True, "DISARM executes", True)
    row(276, "Adversary", "leaked credentials, no key", True,
        ["tag fails:", "cmd_badmac"], False, "rejected — alarm fires, 300/300 trials", True)

    # ---------------- panel 2: the unsound guard
    f.box(36, 400, 1208, 268, fill="#FDF3F2", dash="7 5", rx=14)
    f.text(56, 426, "ALLOW_REMOTE_DISARM = 1 without AUTH_COMMANDS   "
                    "—  the guard this work removed",
           size="head", anchor="start", bold=True)
    f.text(56, 448, "The guard accepted TLS plus a broker login as sufficient. "
                    "The HMAC test is short-circuited, so any admitted DISARM is acted on.",
           size="small", anchor="start", fill=MUTED)
    header(476)
    row(486, "Operator", "holds credentials, no key", True,
        ["no check:", "ALLOW_REMOTE_DISARM"], False, "DISARM executes", True)
    row(566, "Adversary", "leaked credentials, no key", True,
        ["no check:", "ALLOW_REMOTE_DISARM"], False,
        "DISARM executes — alarm fires in only 50/300", False)

    # ---------------- the control, shared by both builds
    f.box(36, 690, 1208, 100, fill=MID, dash="7 5", rx=14)
    f.text(56, 714, "Control, identical in both builds", size="head", anchor="start", bold=True)
    row(722, "Adversary", "no credentials", False, [], True,
        "connection refused — alarm fires, 300/300", True, h=56)
    return f

# ------------------------------------------ 7. compile guard decision flow --
def guard_decision():
    """The guard's decision flow, before and after, with the unsound edge marked.

    Transcribed from the #if conditions in firmware/smart_home/smart_home.ino and the
    dispatch in handleCommands. No relationship is drawn that is not in the source.
    """
    OK, BAD = "#2E7D32", "#C0392B"
    OKF, BADF = "#E9F7EF", "#FDECEC"
    f = Fig(1180, 700, "Compile-time guard for unauthenticated remote disarm")
    f.text(590, 36, "The compile guard, before and after", size="title", bold=True)
    f.lines(590, 60, [
        "A build condition is a security argument. This one asserted that transport security "
        "plus a broker login implies publisher authority.",
    ], size="small")

    def diamond(cx, cy, w, h, label, rows, fill=LIGHT, stroke=LINE):
        f.p.append(f'<path d="M{cx} {cy-h/2} L{cx+w/2} {cy} L{cx} {cy+h/2} L{cx-w/2} {cy} z" '
                   f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
        f.text(cx, cy - 4, label, size="small", bold=True)
        f.lines(cx, cy + 14, rows, size="small")

    # ---------------- before
    f.box(36, 100, 554, 560, fill=BADF, dash="7 5", rx=14)
    f.text(56, 126, "Before: the guard this work removed", size="head", anchor="start",
           bold=True)
    f.box(150, 150, 320, 46, fill="#FFFFFF")
    f.text(310, 178, "ALLOW_REMOTE_DISARM = 1", size="small", bold=True, mono=True)
    f.arrow([(310, 196), (310, 222)])
    diamond(310, 258, 300, 72, "AUTH_COMMANDS = 1 ?", [])
    f.arrow([(460, 258), (548, 258), (548, 440)], stroke=OK)
    f.text(505, 250, "yes", size="small", fill=OK)
    f.arrow([(310, 294), (310, 322)], stroke=BAD)
    f.text(322, 312, "no", size="small", anchor="start", fill=BAD)
    diamond(310, 372, 330, 86, "MQTT_USE_TLS = 1", ["and MQTT_HAS_LOGIN = 1 ?"], fill="#FFFFFF",
            stroke=BAD)
    f.arrow([(310, 415), (310, 446)], stroke=BAD)
    # Both branches land in the same outcome box: that is the defect. A signed build reaches it
    # legitimately, an unsigned one reaches it through the unsound transport test.
    f.box(96, 446, 428, 60, fill=BADF, stroke=BAD)
    f.text(310, 470, "compiles: any admitted DISARM is acted on", size="small", bold=True,
           fill=BAD)
    f.text(310, 490, "the m.authed test is short-circuited", size="small", fill=BAD)
    f.box(96, 526, 428, 110, fill="#FFFFFF", stroke=BAD, dash="4 3")
    f.text(310, 550, "Why the predicate cannot support the conclusion",
           size="small", bold=True, fill=BAD)
    f.lines(310, 572, [
        "The broker terminates TLS and re-originates every message,",
        "so an arriving command carries no evidence of its publisher.",
        "MQTT_HAS_LOGIN describes this device's own build, not any",
        "publisher's authority. One leaked credential is sufficient.",
    ], size="small")

    # ---------------- after
    f.box(626, 100, 518, 560, fill=SAFETY, dash="7 5", rx=14)
    f.text(646, 126, "After", size="head", anchor="start", bold=True)
    f.box(725, 150, 320, 46, fill="#FFFFFF")
    f.text(885, 178, "ALLOW_REMOTE_DISARM = 1", size="small", bold=True, mono=True)
    f.arrow([(885, 196), (885, 222)])
    diamond(885, 258, 300, 72, "AUTH_COMMANDS = 1 ?", [])
    f.arrow([(1035, 258), (1105, 258), (1105, 420)], stroke=OK)
    f.text(1068, 250, "yes", size="small", fill=OK)
    f.arrow([(885, 294), (885, 322)])
    f.text(897, 312, "no", size="small", anchor="start", fill=MUTED)
    diamond(885, 374, 350, 90, "ACKNOWLEDGE_", ["UNAUTHENTICATED_DISARM", "defined ?"],
            fill="#FFFFFF")
    f.arrow([(885, 419), (885, 446)], stroke=BAD)
    f.box(680, 446, 410, 52, fill=BADF, stroke=BAD)
    f.text(885, 468, "no: #error, the build is refused", size="small", bold=True, fill=BAD)
    f.text(885, 487, "transport security is no longer accepted as authority",
           size="small", fill=BAD)
    f.arrow([(1060, 374), (1105, 374), (1105, 420)])
    f.text(1115, 400, "yes", size="small", anchor="start", fill=MUTED)
    f.box(680, 528, 410, 52, fill=OKF, stroke=OK)
    f.text(885, 550, "compiles: signed DISARM, or acknowledged risk",
           size="small", bold=True, fill=OK)
    f.text(885, 569, "the research baseline takes the second path", size="small")
    f.arrow([(1105, 420), (1105, 554), (1094, 554)], stroke=OK)
    return f


# ------------------------------------------- 8. broker ACL trust boundaries --
def acl_architecture():
    """Topic permissions per identity, and which compromise each control contains.

    The permissions shown are the configuration the ablation's ACL arms model; see
    docs/SECURITY_ANALYSIS.md section 3a for what is and is not modelled.
    """
    OK, BAD = "#2E7D32", "#C0392B"
    f = Fig(1200, 660, "Per-client topic permissions and trust boundaries")
    f.text(600, 36, "Broker access control and where each compromise stops",
           size="title", bold=True)
    f.lines(600, 60, [
        "Some identity must hold write on the command topic, or the alarm cannot be commanded. "
        "Which identity the adversary steals is what decides the outcome.",
    ], size="small")

    # topic permission table
    f.box(40, 100, 1120, 214, fill=MID, dash="7 5", rx=14)
    f.text(60, 126, "PER-CLIENT ACL, as modelled", size="head", anchor="start", bold=True)
    cols = [(330, "cmd topic: publish"), (610, "cmd topic: subscribe"), (900, "stat topic: publish")]
    for x, t in cols:
        f.text(x, 158, t, size="small", bold=True, fill=MUTED)
    f.text(150, 158, "identity", size="small", bold=True, fill=MUTED)
    rows = [(192, "controller", True, False, False), (240, "device", False, True, True)]
    for y, name, pub, sub, stat in rows:
        f.box(60, y - 20, 180, 40, fill="#FFFFFF")
        f.text(150, y + 5, name, size="small", bold=True)
        for (x, _), val in zip(cols, (pub, sub, stat)):
            f.box(x - 60, y - 20, 120, 40, fill="#E9F7EF" if val else LIGHT)
            f.text(x, y + 5, "allow" if val else "deny", size="small", bold=val,
                   fill=OK if val else MUTED)
    f.text(600, 292, "Only the controller may publish commands. The device may only read them.",
           size="small", fill=MUTED)

    # outcomes
    f.text(600, 352, "Which compromise each control contains", size="head", bold=True)
    cards = [
        (60, "Device credential\nstolen", "ACL holds", "the device identity has no write on "
         "the command topic, so the broker refuses the publish", OK),
        (400, "Controller credential\nstolen", "ACL fails", "that identity is the one the ACL "
         "must authorise to publish commands", BAD),
        (740, "One shared credential\nstolen", "ACL fails", "it must carry write on the command "
         "topic, so the configuration collapses to no ACL", BAD),
    ]
    for x, title, verdict, why, col in cards:
        f.box(x, 380, 320, 150, fill="#FFFFFF", stroke=col)
        a, b = title.split("\n")
        f.text(x + 160, 408, a, size="body", bold=True)
        f.text(x + 160, 428, b, size="body", bold=True)
        f.text(x + 160, 456, verdict, size="small", bold=True, fill=col)
        f.lines(x + 160, 480, textwrap.wrap(why, 40)[:3], size="small")

    f.box(60, 554, 1000, 76, fill=SHARED, dash="4 3")
    f.text(560, 580, "A MAC fails under the one compromise the ACL survives",
           size="body", bold=True)
    f.lines(560, 602, [
        "The command key lives in the same flash image as the device's broker credentials, so a "
        "flash dump yields both.",
        "With an ACL as well, that adversary holds a key it can sign with and a credential the "
        "broker will not let it publish commands under.",
    ], size="small")
    return f


# ---------------------------------------------------------------- driver -----
FIGS = {
    "command_flow": command_flow,
    "command_sequence": command_sequence,
    "deployment": deployment,
    "methodology": methodology,
    "experimental_setup": experimental_setup,
    "security_paths": security_paths,
    "guard_decision": guard_decision,
    "acl_architecture": acl_architecture,
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

    # Re-export the hand-authored diagrams. BOTH pdf and png: the README embeds the
    # png, so exporting only the pdf leaves an edited svg invisible on GitHub. That
    # happened once -- a correction to state_machine.svg never reached its png, and
    # the repository kept showing the old text.
    for name in ("architecture", "state_machine", "event_sequence", "circuit_wiring"):
        sp = os.path.join(out, name + ".svg")
        if os.path.exists(sp):
            cairosvg.svg2pdf(url=sp, write_to=os.path.join(out, name + ".pdf"))
            cairosvg.svg2png(url=sp, write_to=os.path.join(out, name + ".png"), scale=2.0)
            print(f"  {name}: pdf + png re-exported from svg")


if __name__ == "__main__":
    sys.exit(main())
