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
BAD_RED = "#C0392B"   # the one red used across the figure set
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

# Type scale, in SVG user units. These are chosen against the printed page, not the screen.
# A diagram placed at \textwidth on A4 with 1 in margins is 451 pt wide, so a 1,100-unit
# canvas renders one user unit as 0.41 pt. At the previous scale (small = 11) the smallest
# label printed at 4.2 pt, well under the 6 pt floor publishers set -- which no amount of
# inspection at screen resolution reveals. experiments/check_figure_type.py measures this and
# fails the build if any label drops below the floor; keep every canvas at or under 1,200
# units wide, or these values stop clearing it.
SZ = {"title": 22, "head": 19.5, "body": 17.5, "small": 16}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Fig:
    """Minimal SVG builder. Coordinates are user units; 1 unit renders as 1 px."""

    def __init__(self, w, h, title, crop_top=0):
        # crop_top removes dead space at the top of the canvas, which is what is left behind
        # when a figure's in-drawing title is deleted. The caption carries the title in the
        # manuscript, and repeating it inside the artwork is a style error in most journals.
        self.w, self.h, self.title, self.crop_top = w, h, title, crop_top
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
        h = self.h - self.crop_top
        body = "".join(self.p)
        if self.crop_top:
            body = f'<g transform="translate(0,{-self.crop_top})">{body}</g>'
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h}" '
            f'viewBox="0 0 {self.w} {h}" font-family=\'{FONT}\'>'
            f"<title>{esc(self.title)}</title>"
            f'<rect width="100%" height="100%" fill="#FFFFFF"/>{defs}'
            + body
            + "</svg>"
        )


def architecture():
    """System architecture: the two cores, the queues between them, and what is outside.

    Every pin number, timeout and queue depth is taken from
    firmware/smart_home/smart_home.ino and nothing is drawn that the firmware does not
    implement. This replaces a hand-authored SVG that carried its own six-size type scale and
    printed its smallest label at 4.9 pt. Core 0 is blue and core 1 green here exactly as in
    the command-flow figure, so the two read as one set.
    """
    OUTPUT = "#FFF4E0"   # amber, not the red that means "unsafe" elsewhere in the set
    f = Fig(1100, 1190, "System architecture: safety core, network core and the queues "
                        "between them")
    f.lines(550, 28, [
        "ESP32 firmware v2.2.0: the safety logic runs on core 1, all networking on core 0.",
        "They share only two bounded queues and one mutex-guarded status snapshot.",
    ], size="small")

    # ---------------- sensing
    f.box(36, 70, 1028, 140, fill=MID, dash="4 3")
    f.text(50, 94, "SENSING (inputs)", size="head", anchor="start", bold=True)
    for x, title, rows in (
        (60, "PIR motion sensor",
         ["HC-SR501, OUT on GPIO 13", "10 s warm-up, 150 ms confirm"]),
        (392, "Door / window switch",
         ["reed or slide switch, GPIO 14", "internal pull-up; HIGH = open"]),
        (724, "ARM / DISARM button",
         ["momentary, GPIO 27", "internal pull-up; LOW = pressed"]),
    ):
        f.box(x, 108, 316, 86, fill="#FFFFFF")
        f.text(x + 158, 134, title, size="body", bold=True)
        f.lines(x + 158, 156, rows, size="small")
    for x in (218, 550, 882):
        f.arrow([(x, 194), (x, 230)])

    # ---------------- the chip
    f.box(36, 230, 1028, 560, fill=LIGHT, sw=2.2)
    f.text(50, 256, "ESP32 DevKit  \u2014  dual core, FreeRTOS", size="head", anchor="start",
           bold=True)

    # core 1
    f.box(48, 270, 532, 512, fill=SAFETY, dash="7 5")
    f.text(62, 294, "Core 1: safety loop (Arduino loop task)", size="body", anchor="start",
           bold=True)
    f.text(62, 314, "never blocks, watchdog-supervised, works offline",
           size="small", anchor="start", fill=MUTED)
    f.box(60, 328, 508, 88, fill="#FFFFFF")
    f.text(314, 352, "1. Input conditioning", size="body", bold=True)
    f.lines(314, 374, ["debounce 40 ms on the door and the button",
                       "PIR: 10 s warm-up, 150 ms confirm"], size="small")
    f.box(60, 432, 508, 154, fill="#FFFFFF")
    f.text(314, 456, "2. State machine", size="body", bold=True)
    f.lines(314, 478, [
        "DISARMED \u2192 EXIT_DELAY 10 s \u2192 ARMED",
        "ARMED + motion or door \u2192 ENTRY_DELAY 10 s",
        "ENTRY_DELAY expires \u2192 ALARM 30 s \u2192 ARMED",
        "button arms and disarms; remote: ARM, DISARM, STATUS",
        "armed state kept in NVS across power cuts",
    ], size="small")
    f.box(60, 602, 508, 88, fill="#FFFFFF")
    f.text(314, 626, "3. Output driver", size="body", bold=True)
    f.lines(314, 648, ["buzzer tone 2.7 kHz, two LEDs,",
                       "OLED refresh every 250 ms (4 Hz)"], size="small")

    # the two queues: the only shared state
    f.box(594, 400, 152, 76, fill=SHARED)
    f.text(670, 424, "Command", size="body", bold=True)
    f.lines(670, 446, ["queue, 4 deep"], size="small")
    f.box(594, 520, 152, 96, fill=SHARED)
    f.text(670, 544, "Event", size="body", bold=True)
    f.lines(670, 566, ["queue, 16 deep", "drop oldest"], size="small")
    # The third shared object. The asymmetric mutex timeout is the isolation mechanism: the
    # safety loop takes it with timeout 0 and gives up rather than wait, so the network task
    # can never hold it long enough to delay the alarm.
    f.box(594, 652, 152, 96, fill=SHARED)
    f.text(670, 676, "Status", size="body", bold=True)
    f.lines(670, 698, ["snapshot 500 ms", "safety: 0 ms", "network: 10 ms"], size="small")
    f.arrow([(756, 438), (748, 438)], sw=2.2)
    f.arrow([(592, 438), (580, 438)], sw=2.2)
    f.arrow([(580, 568), (592, 568)], sw=2.2)
    f.arrow([(748, 568), (756, 568)], sw=2.2)
    f.arrow([(580, 700), (592, 700)], sw=2.2)
    f.arrow([(748, 700), (756, 700)], sw=2.2)

    # core 0
    f.box(756, 270, 296, 512, fill=NETWORK, dash="7 5")
    f.text(770, 294, "Core 0: network task", size="body", anchor="start", bold=True)
    f.lines(770, 314, ["slow DNS or TCP can never", "stall the alarm"],
            size="small", anchor="start")
    f.box(768, 346, 272, 86, fill="#FFFFFF")
    f.text(904, 370, "Wi-Fi manager", size="body", bold=True)
    f.lines(904, 392, ["retry every 15 s", "NTP clock (IST)"], size="small")
    f.box(768, 446, 272, 126, fill="#FFFFFF")
    f.text(904, 470, "MQTT client", size="body", bold=True)
    f.lines(904, 492, ["Last Will \u201coffline\u201d", "reconnect every 5 s",
                       "subscribes to .../cmd", "Home Assistant discovery"], size="small")
    f.box(768, 586, 272, 126, fill="#FFFFFF")
    f.text(904, 610, "Event publisher", size="body", bold=True)
    f.lines(904, 632, ["JSON events, sequence no.", "oldest first", "retained state,",
                       "heartbeat every 30 s"], size="small")

    # ---------------- local outputs
    f.arrow([(314, 690), (314, 822)], sw=2.2)
    f.box(36, 822, 596, 168, fill=OUTPUT, dash="4 3")
    f.text(50, 846, "LOCAL OUTPUTS", size="head", anchor="start", bold=True)
    for x, title, rows in (
        (48, "Buzzer", ["passive piezo", "GPIO 23", "2.7 kHz"]),
        (244, "Status LEDs", ["green GPIO 26", "red GPIO 25"]),
        (440, "OLED SSD1306", ["I2C 0x3C", "GPIO 21 / 22"]),
    ):
        f.box(x, 860, 184, 112, fill="#FFFFFF")
        f.text(x + 92, 886, title, size="body", bold=True)
        f.lines(x + 92, 908, rows, size="small")

    # ---------------- outside the device
    f.arrow([(904, 790), (904, 860)], sw=2.2)
    f.text(892, 812, "Wi-Fi, MQTT 1883 / 8883 TLS", size="small", anchor="end", fill=MUTED)
    f.box(652, 822, 412, 346, fill=EXTERNAL, dash="2 4")
    f.text(666, 846, "NETWORK AND USER SIDE", size="head", anchor="start", bold=True)
    f.box(664, 860, 388, 132, fill="#FFFFFF")
    f.text(858, 884, "MQTT broker", size="body", bold=True)
    f.lines(858, 906, [
        "default: public test broker",
        "evaluated against a private broker",
        "with TLS, per-client ACLs, credentials",
        "topics: availability, state, event, cmd",
    ], size="small")
    f.arrow([(820, 992), (820, 1032)])
    f.arrow([(896, 1032), (896, 992)])
    f.text(806, 1018, "state, events", size="small", anchor="end", fill=MUTED)
    f.text(910, 1018, "commands", size="small", anchor="start", fill=MUTED)
    f.box(664, 1032, 388, 124, fill="#FFFFFF")
    f.text(858, 1056, "Homeowner clients", size="body", bold=True)
    f.lines(858, 1078, [
        "Home Assistant / Node-RED / dashboard",
        "phone MQTT app: alert on an alarm event",
    ], size="small")

    # ---------------- legend
    f.box(36, 1002, 596, 166, fill="#FFFFFF", dash="4 3")
    f.text(50, 1026, "LEGEND", size="head", anchor="start", bold=True)
    # Each swatch repeats its band's border style as well as its fill: two of the tints are
    # close in greyscale, and the border is what actually separates them on the page.
    for i, (fill, label, dash) in enumerate((
        (MID, "Sensing", "4 3"),
        (SAFETY, "Safety core (core 1)", "7 5"),
        (NETWORK, "Network core (core 0)", "7 5"),
        (SHARED, "Shared queues", None),
        (OUTPUT, "Local outputs", "4 3"),
        (EXTERNAL, "Network and user side", "2 4"),
    )):
        y = 1040 + i * 21
        f.box(56, y, 28, 15, fill=fill, rx=3, dash=dash)
        f.text(94, y + 13, label, size="small", anchor="start")
    f.lines(316, 1052, [
        "Events raised while offline wait in",
        "the queue (up to 16) and are sent on",
        "reconnect. A remote DISARM needs a",
        "valid HMAC tag over a fresh,",
        "NVS-persisted counter.",
    ], size="small", anchor="start")
    return f


# ------------------------------------------------- 1. command execution ------
def command_flow():
    """Command path, showing which core performs each stage."""
    f = Fig(1100, 760, "Command execution flow across the two cores")
    f.text(550, 34, "Command execution flow", size="title", bold=True)
    f.lines(550, 56, [
        "Parsing and HMAC verification run on core 0, so a command flood costs the safety core no time."
    ], size="small")

    # domain bands
    f.box(40, 80, 1020, 290, fill=NETWORK, dash="7 5", rx=14)
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
    f.box(250, 282, 580, 80, fill=LIGHT, dash="4 3")
    f.text(540, 306, "rejected on core 0  —  never reaches the safety core",
           size="body", bold=True)
    f.lines(540, 328, [
        "malformed: dropped silently   ·   bad tag: cmd_badmac",
        "unsigned: cmd_unauth",
    ], size="small")
    f.arrow([(495, 236), (495, 282)], dash="4 3")
    f.arrow([(665, 236), (620, 282)], dash="4 3")

    # the queue crossing
    # The badge sits in the gap between the two domain bands: it is the only object that
    # crosses the boundary, which is the point the figure makes.
    f.box(762, 374, 226, 52, fill=DARK, rx=8)
    f.text(875, 396, "cmdQ  depth 4", size="body", bold=True)
    f.text(875, 416, "bounded, non-blocking", size="small", fill=MUTED)
    f.arrow([(875, 236), (875, 374)], sw=2.4)
    f.arrow([(875, 426), (875, 470)], sw=2.4)

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

    f.box(150, 600, 560, 100, fill=LIGHT)
    f.text(430, 628, "authorise and execute", size="body", bold=True)
    f.lines(430, 652, [
        "DISARM requires m.authed or ALLOW_REMOTE_DISARM,",
        "else cmd_rejected   ·   STATUS always publishes",
        "ARM / ARM_AWAY only from DISARMED, else cmd_ignored",
    ], size="small")

    f.arrow([(700, 513), (650, 513)])
    f.arrow([(420, 513), (370, 513)])
    f.arrow([(260, 556), (260, 600)])

    # response path back up
    f.box(740, 600, 300, 100, fill=LIGHT, dash="4 3")
    f.text(890, 628, "response", size="body", bold=True)
    f.lines(890, 652, [
        "retained state publish",
        "plus one outcome event",
        "no acknowledgement protocol",
    ], size="small")
    f.arrow([(710, 650), (740, 650)], dash="4 3")

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

    selfnote(xs["networkTask"], 318, 76, "verify on core 0",
             ["parse VERB:ctr:tag",
              "recompute tag, ct_equal"], "network")

    selfnote(xs["networkTask"], 410, 76, "rejected, not enqueued",
             ["bad tag -> cmd_badmac", "unsigned -> cmd_unauth",
              "malformed -> dropped silently"], "output", dash="5 4")

    step(3, 515, "networkTask", "cmdQ", "enqueue  {DISARM, authed, 1001}",
         "a flood cannot displace it")
    step(4, 575, "cmdQ", "safety loop", "xQueueReceive(cmdQ, &m, 0)",
         "zero timeout: never waits")

    selfnote(xs["safety loop"], 600, 58, "fresh: ctr > counter",
             ["else cmd_replay"], "safety")

    step(5, 695, "safety loop", "NVS", "persistCounter(1001)",
         "committed BEFORE acting")
    step(6, 756, "NVS", "safety loop", "committed", dash="4 3")

    selfnote(xs["safety loop"], 778, 76, "authorise and execute",
             ["m.authed -> disarm()",
              "DISARMED, 150 ms beep"], "safety")

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
        "PIR HC-SR501 (GPIO 13)  ·  door reed (GPIO 14)",
        "button (GPIO 27)  ·  buzzer (GPIO 23)",
        "LEDs (GPIO 25, 26)  ·  OLED (I2C 21/22)",
        "LD2410 radar (GPIO 33): optional, fusion only",
    ], size="small")

    # broker + HA
    f.box(540, 90, 250, 120, fill=NETWORK)
    f.text(665, 118, "MQTT broker", size="head", bold=True)
    f.lines(665, 140, [
        "events, commands,", "Last Will, retained state", "alarm works offline",
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
        "Does core pinning isolate", "the safety function if the",
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
        ("Fuzzing", ["3,000,000 runs", "ASan + UBSan", "0 accepted"], "COMPLETE", MID),
        ("Hardware", ["Conditions A-D", "latency spread", "apparatus built"], "NOT RUN", LIGHT),
    ]
    for i, (name, rows, status, fill) in enumerate(routes):
        x = 346 + i * 185
        dash = "6 4" if status == "NOT RUN" else None
        f.box(x, 150, 175, 140, fill=fill, dash=dash)
        f.text(x + 87, 178, name, size="head", bold=True)
        f.lines(x + 87, 200, rows, size="small")
        f.text(x + 87, 268, status, size="small", bold=True)
        # The four routes are INDEPENDENT, not sequential: the gap fans out to each
        # via a shared bus, so no arrow ever runs from one route to the next.
        f.arrow([(315, 240), (315, 120), (x + 87, 120), (x + 87, 150)], dash=dash)
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

    f.box(350, 450, 710, 100, fill=LIGHT, dash="6 4")
    f.text(705, 478, "What remains open", size="head", bold=True)
    f.lines(705, 500, [
        "TIMING isolation: a property of the silicon, the interrupt",
        "controller and the closed-source radio driver. It cannot be",
        "simulated, and no latency number is claimed anywhere.",
    ], size="small")
    f.arrow([(987, 290), (987, 450)], dash="6 4")
    return f


# ------------------------------------------------- 5. experimental setup -----
def experimental_setup():
    """What has been run, and what has only been specified.

    Panel A lists every experiment whose results appear in the paper, with the counts taken
    from the committed artefacts in experiments/results/ and experiments/corpus/. Panel B is
    the hardware rig: it is specified and its analysis script exists, but it has not been
    run, and no number in the paper comes from it. The two panels are drawn differently
    (solid against dotted) so that distinction survives greyscale printing.
    """
    f = Fig(1100, 660, "Experimental setup: completed evidence against the hardware rig",
            crop_top=46)

    # ---------------- A: what has actually been run
    f.box(50, 70, 500, 570, fill=LIGHT, sw=2.2)
    f.text(300, 96, "A.  Completed evidence", size="head", bold=True)
    f.text(300, 116, "every result reported in this paper", size="small", fill=MUTED)

    f.box(80, 134, 440, 104, fill=MID)
    f.text(300, 158, "Unmodified firmware logic", size="body", bold=True)
    f.lines(300, 180, [
        "smart_home.ino compiled against host stubs",
        "for Arduino, FreeRTOS, WiFi, MQTT, NVS, OLED.",
        "Not altered for testing.",
    ], size="small")

    for x, title, rows in (
        (80, "Campaign (E1, E2)",
         ["6,000 trials, seed 1000", "rates 0 to 20,000 msg/s", "fork() per trial"]),
        (308, "Ablation (E3)",
         ["3,600 trials, seed 2000", "12 configurations", "300 trials each"]),
    ):
        f.box(x, 252, 212, 96, fill=MID)
        f.text(x + 106, 276, title, size="body", bold=True)
        f.lines(x + 106, 296, rows, size="small")

    for x, title, rows in (
        (80, "Fuzzer (E4)",
         ["3,000,000 runs", "seed 7, 6 input classes", "ASan + UBSan"]),
        (308, "Broker testbed (E6)",
         ["real Mosquitto 2.0.18", "TLS, per-client ACLs", "8 scenarios"]),
    ):
        f.box(x, 364, 212, 96, fill=MID)
        f.text(x + 106, 388, title, size="body", bold=True)
        f.lines(x + 106, 408, rows, size="small")

    f.box(80, 476, 440, 66, fill=MID)
    f.text(300, 500, "Sensitivity sweep (E5) and corpus study", size="body", bold=True)
    f.lines(300, 520, [
        "180 grid cells; 135 projects, commit-pinned,",
        "guard rule with 8 controls, 0 hits",
    ], size="small")

    f.box(80, 556, 440, 78, fill=LIGHT, dash="4 3")
    f.text(300, 578, "Limitation that defines the open step", size="body", bold=True)
    f.lines(300, 598, [
        "The harness advances a logical clock. No radio,",
        "no parallelism, no contention: zero variance.",
    ], size="small")

    # ---------------- B: specified, not run
    f.box(570, 70, 480, 570, fill=LIGHT, dash="2 4", sw=2.2)
    f.text(810, 96, "B.  Not yet measured", size="head", bold=True)
    f.text(810, 116, "rig specified; no result in this paper comes from it",
           size="small", fill=BAD_RED)

    # A 60-unit gap, so the GPIO label sits clear of both borders rather than touching them.
    f.box(598, 134, 188, 96, fill=MID, dash="2 4")
    f.text(692, 160, "Device under test", size="body", bold=True)
    f.lines(692, 180, ["ESP32 DevKit", "running v2.2.0", "unmodified"], size="small")

    f.box(834, 134, 188, 96, fill=MID, dash="2 4")
    f.text(928, 160, "Measuring board", size="body", bold=True)
    f.lines(928, 180, ["second ESP32,", "independent clock,", "logic probe"], size="small")
    f.arrow([(788, 186), (832, 186)], dash="2 4")
    f.text(810, 172, "GPIO", size="small", fill=MUTED)

    f.box(600, 256, 420, 132, fill=LIGHT, dash="2 4")
    f.text(810, 280, "Four conditions", size="body", bold=True)
    for i, (c, d) in enumerate([
        ("A", "idle (control)"),
        ("B", "legitimate network load"),
        ("C", "command-interface stress"),
        ("D", "radio-layer stress"),
    ]):
        y = 306 + i * 22
        f.text(620, y, f"{c}.", size="small", anchor="start", bold=True, fill=INK)
        f.text(648, y, d, size="small", anchor="start", fill=INK)
    # The RF caveat is a footnote rather than a per-row column: at this type size the two
    # would collide on the longest row.
    f.lines(810, 408, [
        "A to C need no RF isolation.",
        "D: authorised, isolated RF environment only.",
    ], size="small")

    f.box(600, 444, 420, 84, fill=MID, dash="2 4")
    f.text(810, 468, "Dependent variable", size="body", bold=True)
    f.lines(810, 490, [
        "Physical sensor-to-siren latency distribution,",
        "compared across conditions with analyse_hw.py.",
    ], size="small")

    f.box(600, 546, 420, 66, fill=LIGHT, dash="4 3")
    f.lines(810, 572, [
        "Conditions A to C need two boards and a probe.",
        "No attack tooling is published.",
    ], size="small", fill=INK)
    return f


# ------------------------------------------- 6. transport vs application auth -
def security_paths():
    """Where broker credentials decide admission and where the command key decides authority.

    Every relationship drawn is taken from the implementation: broker admission is modelled by
    deliverGuarded/admit in experiments/ablation.cpp; the device-side checks are handleCommands
    in firmware/smart_home/smart_home.ino. The counts are measured, from
    experiments/results/ablation.jsonl (300 trials per arm).

    The canvas is 1,160 units because the type scale only clears the 6 pt print floor at or
    below about 1,200; see experiments/check_figure_type.py.
    """
    OK, BAD = "#2E7D32", "#C0392B"
    OKF, BADF = "#E9F7EF", "#FDECEC"
    f = Fig(1160, 866, "Transport-layer admission against application-layer authorization",
            crop_top=10)
    f.lines(580, 38, [
        "The broker terminates TLS and re-originates every message, so an arriving command "
        "carries no evidence of who published it.",
        "Broker credentials decide admission. Only the command key decides authority.",
    ], size="small")

    XP, WP = 48, 228          # publisher
    XB, WB = 296, 132         # broker
    XC, WC = 448, 238         # device-side check
    XO, WO = 706, 398         # outcome

    def header(y):
        for x, w, t in ((XP, WP, "Publisher"), (XB, WB, "Broker"),
                        (XC, WC, "Device check"), (XO, WO, "Outcome")):
            f.text(x + w / 2, y, t, size="small", bold=True, fill=MUTED)

    def row(y, who, sub, admit, check, chk_ok, outcome, out_ok, h=62):
        col = OK if out_ok else BAD
        f.box(XP, y, WP, h, fill="#FFFFFF")
        f.text(XP + WP / 2, y + 26, who, size="body", bold=True)
        f.text(XP + WP / 2, y + 46, sub, size="small", fill=MUTED)

        # Only the Outcome column is coloured. An intermediate step that blocks an attack and
        # an outcome in which the attack succeeds are opposite things, and colouring both red
        # (because both are "a failure" in some sense) is what made the earlier version of
        # this figure unreadable. The intermediate columns say what happened in words.
        f.arrow([(XP + WP, y + h / 2), (XB - 6, y + h / 2)], stroke=col)
        f.box(XB, y, WB, h, fill=LIGHT)
        f.text(XB + WB / 2, y + h / 2 + 5, "admits" if admit else "refuses",
               size="small", bold=True, fill=INK)

        if not admit:
            f.text(XC + WC / 2, y + h / 2 + 5, "never reached", size="small", fill=MUTED)
            f.box(XO, y, WO, h, fill=OKF, stroke=OK)
            f.text(XO + WO / 2, y + h / 2 + 5, outcome, size="small", bold=True, fill=OK)
            return
        f.arrow([(XB + WB, y + h / 2), (XC - 6, y + h / 2)], stroke=col)
        f.box(XC, y, WC, h, fill=LIGHT)
        f.lines(XC + WC / 2, y + 24, check, size="small", fill=INK)
        f.arrow([(XC + WC, y + h / 2), (XO - 6, y + h / 2)], stroke=col)
        f.box(XO, y, WO, h, fill=OKF if out_ok else BADF, stroke=OK if out_ok else BAD)
        f.text(XO + WO / 2, y + h / 2 + 5, outcome, size="small", bold=True, fill=col)

    # ---------------- panel 1: the default build
    f.box(36, 70, 1088, 340, fill=SAFETY, dash="7 5", rx=14)
    f.text(48, 96, "AUTH_COMMANDS = 1    \u2014  application-layer authentication required",
           size="head", anchor="start", bold=True)
    f.text(48, 118, "Acted on only if the HMAC-SHA256 tag verifies under SECRET_CMD_KEY "
                    "and the counter exceeds the value in NVS.",
           size="small", anchor="start", fill=MUTED)
    header(146)
    row(156, "Operator", "credential + key", True,
        ["tag verifies,", "counter advances"], True, "DISARM executes", True)
    row(236, "Adversary", "credential, no key", True,
        ["tag fails:", "cmd_badmac"], False, "rejected; alarm fires 300/300", True)
    # The row that stops this figure from implying the layered build is unconditional. The
    # adversary who has taken the controller host holds a credential the ACL must permit and
    # the key the device trusts, so both layers pass it. Measured, not asserted.
    row(316, "Adversary", "controller cred + key", True,
        ["tag verifies,", "counter advances"], True,
        "DISARM executes; alarm fires 50/300", False)
    f.text(580, 396, "Row 3 is a compromised controller host: a credential the ACL must "
                     "permit plus the key. Neither layer refuses it.",
           size="small", fill=BAD)

    # ---------------- panel 2: the unsound guard
    f.box(36, 432, 1088, 250, fill="#FDF3F2", dash="7 5", rx=14)
    f.text(48, 458, "ALLOW_REMOTE_DISARM = 1 without AUTH_COMMANDS   "
                    "\u2014  the guard this work removed",
           size="head", anchor="start", bold=True)
    f.text(48, 480, "The guard treated TLS plus a broker login as sufficient: the HMAC test "
                    "is skipped, so any admitted DISARM is acted on.",
           size="small", anchor="start", fill=MUTED)
    header(508)
    row(518, "Operator", "credential, no key", True,
        ["no check:", "ALLOW_REMOTE_DISARM"], False, "DISARM executes", True)
    row(598, "Adversary", "credential, no key", True,
        ["no check:", "ALLOW_REMOTE_DISARM"], False,
        "DISARM executes; alarm fires 50/300", False)

    # ---------------- the control, shared by both builds
    f.box(36, 704, 1088, 100, fill=MID, dash="7 5", rx=14)
    f.text(48, 728, "Control, identical in both builds", size="head", anchor="start", bold=True)
    row(736, "Adversary", "no credential", False, [], True,
        "connection refused; alarm fires 300/300", True, h=56)

    f.lines(580, 824, [
        "Outcome colour is the only colour that carries meaning: green, the alarm still "
        "protects the house;",
        "red, an unauthorised DISARM succeeded. Every outcome also states its measured count.",
    ], size="small")
    return f


# ------------------------------------------ 7. compile guard decision flow --
def guard_decision():
    """The guard's decision flow, before and after, with the unsound edge marked.

    Transcribed from the #if conditions in firmware/smart_home/smart_home.ino and the
    dispatch in handleCommands. No relationship is drawn that is not in the source.
    """
    OK, BAD = "#2E7D32", "#C0392B"
    OKF, BADF = "#E9F7EF", "#FDECEC"
    f = Fig(1180, 706, "Compile-time guard for unauthenticated remote disarm", crop_top=14)
    f.lines(590, 34, [
        "A build condition is a security argument. This one asserted that transport security "
        "plus a broker login",
        "implies publisher authority.",
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
    f.box(153, 150, 320, 46, fill="#FFFFFF")
    f.text(313, 178, "ALLOW_REMOTE_DISARM = 1", size="small", bold=True, mono=True)
    f.arrow([(313, 196), (313, 222)])
    diamond(313, 258, 300, 72, "AUTH_COMMANDS = 1 ?", [])
    f.arrow([(463, 258), (548, 258), (548, 440)], stroke=OK)
    f.text(506, 250, "yes", size="small", fill=OK)
    f.arrow([(313, 294), (313, 322)], stroke=BAD)
    f.text(325, 312, "no", size="small", anchor="start", fill=BAD)
    diamond(313, 372, 330, 86, "MQTT_USE_TLS = 1", ["and MQTT_HAS_LOGIN = 1 ?"],
            fill="#FFFFFF", stroke=BAD)
    f.arrow([(313, 415), (313, 446)], stroke=BAD)
    # Both branches land in the same outcome box: that is the defect. A signed build reaches
    # it legitimately, an unsigned one reaches it through the unsound transport test.
    f.box(60, 446, 506, 60, fill=BADF, stroke=BAD)
    f.text(313, 470, "compiles: any admitted DISARM is acted on", size="small", bold=True,
           fill=BAD)
    f.text(313, 490, "the m.authed test is short-circuited", size="small", fill=BAD)
    f.box(44, 526, 538, 110, fill="#FFFFFF", stroke=BAD, dash="4 3")
    f.text(313, 550, "Why the predicate cannot support the conclusion",
           size="small", bold=True, fill=BAD)
    f.lines(313, 572, [
        "The broker terminates TLS and re-originates every message,",
        "so an arriving command carries no evidence of its publisher.",
        "MQTT_HAS_LOGIN describes this device's own build, not any",
        "publisher's authority. One leaked credential is sufficient.",
    ], size="small")

    # ---------------- after
    f.box(626, 100, 518, 560, fill=SAFETY, dash="7 5", rx=14)
    f.text(646, 126, "After", size="head", anchor="start", bold=True)
    f.box(715, 150, 320, 46, fill="#FFFFFF")
    f.text(875, 178, "ALLOW_REMOTE_DISARM = 1", size="small", bold=True, mono=True)
    f.arrow([(875, 196), (875, 222)])
    diamond(875, 258, 300, 72, "AUTH_COMMANDS = 1 ?", [])
    f.arrow([(1025, 258), (1120, 258), (1120, 420)], stroke=OK, head=False)
    f.text(1070, 250, "yes", size="small", fill=OK)
    f.arrow([(875, 294), (875, 322)])
    f.text(887, 312, "no", size="small", anchor="start", fill=MUTED)
    diamond(875, 374, 430, 104, "ACKNOWLEDGE_", ["UNAUTHENTICATED_DISARM", "defined ?"],
            fill="#FFFFFF")
    # Refusing the build is the protective outcome, so it is green. An earlier version drew
    # #error in red, which read as "this is the bad branch" -- the opposite of what it is.
    f.arrow([(875, 426), (875, 446)], stroke=OK)
    f.box(650, 446, 450, 52, fill=OKF, stroke=OK)
    f.text(875, 468, "no: #error, the build is refused", size="small", bold=True, fill=OK)
    f.text(875, 487, "transport security is no longer accepted as authority",
           size="small", fill=OK)
    f.arrow([(1090, 374), (1120, 374), (1120, 420)], head=False)
    f.text(1114, 366, "yes", size="small", anchor="end", fill=MUTED)
    f.box(650, 528, 450, 52, fill=OKF, stroke=OK)
    f.text(875, 550, "compiles: signed DISARM, or acknowledged risk",
           size="small", bold=True, fill=OK)
    f.text(875, 569, "the research baseline takes the second path", size="small")
    f.arrow([(1120, 420), (1120, 554), (1104, 554)], stroke=OK)

    f.text(590, 684, "Red marks a build in which an unauthenticated DISARM can be acted on; "
                     "green marks one in which it cannot.", size="small", fill=MUTED)
    return f


# ------------------------------------------- 8. broker ACL trust boundaries --
def acl_architecture():
    """Topic permissions per identity, and which compromise each control contains.

    The permissions shown are the configuration the ablation's ACL arms model, and the same
    matrix was then written as a Mosquitto acl_file and exercised against a real broker; see
    docs/SECURITY_ANALYSIS.md section 3a and experiments/broker/.

    The canvas is 1,160 units so the type scale clears the 6 pt print floor; see
    experiments/check_figure_type.py.
    """
    OK, BAD = "#2E7D32", "#C0392B"
    f = Fig(1160, 700, "Per-client topic permissions and trust boundaries", crop_top=14)
    f.lines(580, 38, [
        "Some identity must hold write on the command topic, or the alarm cannot be "
        "commanded at all.",
        "Which identity the adversary steals is what decides the outcome.",
    ], size="small")

    # topic permission table
    f.box(36, 72, 1088, 214, fill=MID, dash="7 5", rx=14)
    f.text(48, 98, "PER-CLIENT ACL  —  modelled, and reproduced on Mosquitto 2.0.18",
           size="head", anchor="start", bold=True)
    cols = [(340, "cmd topic: publish"), (620, "cmd topic: subscribe"),
            (900, "stat topic: publish")]
    for x, t in cols:
        f.text(x, 130, t, size="small", bold=True, fill=MUTED)
    f.text(146, 130, "identity", size="small", bold=True, fill=MUTED)
    rows = [(180, "controller", True, False, False), (228, "device", False, True, True)]
    for y, name, pub, sub, stat in rows:
        f.box(56, y - 20, 180, 40, fill="#FFFFFF")
        f.text(146, y + 5, name, size="small", bold=True)
        for (x, _), val in zip(cols, (pub, sub, stat)):
            f.box(x - 60, y - 20, 120, 40, fill="#E9F7EF" if val else LIGHT)
            f.text(x, y + 5, "allow" if val else "deny", size="small", bold=val,
                   fill=OK if val else MUTED)
    f.text(580, 268, "Only the controller may publish commands; the device may only read "
                     "them.   (Broker usernames: operator, device.)",
           size="small", fill=MUTED)

    # outcomes
    f.text(580, 322, "Which compromise each control contains", size="head", bold=True)
    cards = [
        (40, "Device credential\nstolen", "ACL holds", "the device identity has no write on "
         "the command topic, so the broker refuses the publish", OK),
        (420, "Controller credential\nstolen", "ACL fails", "that identity is the one the ACL "
         "must authorise to publish commands", BAD),
        (800, "One shared credential\nstolen", "ACL fails", "it must carry write on the "
         "command topic, so the configuration collapses to no ACL", BAD),
    ]
    for x, title, verdict, why, col in cards:
        f.box(x, 350, 320, 176, fill="#FFFFFF", stroke=col)
        a, b = title.split("\n")
        f.text(x + 160, 378, a, size="body", bold=True)
        f.text(x + 160, 398, b, size="body", bold=True)
        f.text(x + 160, 426, verdict, size="small", bold=True, fill=col)
        f.lines(x + 160, 450, textwrap.wrap(why, 33)[:4], size="small")

    # The ACL and the MAC fail under different compromises, and the figure has to say so in
    # both directions. Stating only the device-dump case would imply the layered build is
    # unconditional, which experiments/results/ablation.jsonl contradicts.
    f.box(56, 548, 1048, 124, fill=SHARED, dash="4 3")
    f.text(580, 574, "The ACL and the MAC fail under different compromises",
           size="body", bold=True)
    f.lines(580, 598, textwrap.wrap(
        "The command key and the device's broker credentials share one flash image, so a "
        "flash dump yields both; the ACL still refuses that identity, and the layered build "
        "holds. A compromised controller host is the opposite case: it yields a credential "
        "the ACL must permit and the key to sign with, so neither layer refuses it.",
        114)[:4], size="small")
    return f


def hardware_rig():
    """The measurement rig for conditions A-D. Nothing here has been built or run.

    This is a plan diagram, not a result. It exists so that an independent laboratory can
    wire the rig from one picture, and so the manuscript's Figure 6 panel B has a detailed
    counterpart in the repository. Pin assignments come from REPRODUCTION.md section 3.2 and
    from experiments/hardware/latency_probe.
    """
    PLAN = "#F4F6F8"
    f = Fig(1100, 782, "Hardware measurement rig for conditions A to D (not yet built)",
            crop_top=10)
    f.lines(550, 34, [
        "NOT YET BUILT AND NOT YET RUN. No number in the manuscript comes from this rig.",
    ], size="small", fill=BAD_RED)
    f.lines(550, 58, [
        "The device under test never times itself: the hypothesis concerns its own clock "
        "under load, so a second board with an",
        "independent clock timestamps both edges.",
    ], size="small")

    # device under test
    f.box(60, 104, 400, 196, fill=PLAN, dash="2 4", sw=2.2)
    f.text(260, 132, "Device under test", size="head", bold=True)
    f.lines(260, 154, [
        "ESP32-WROOM-32 DevKit (dual core)",
        "smart_home v2.2.0, AUTH_COMMANDS=1",
        "unmodified, not reflashed between conditions",
    ], size="small")
    f.box(84, 216, 160, 72, fill="#FFFFFF")
    f.text(164, 240, "GPIO 13", size="body", bold=True, mono=True)
    f.lines(164, 260, ["PIR input", "(or push button)"], size="small")
    f.box(276, 216, 160, 72, fill="#FFFFFF")
    f.text(356, 240, "GPIO 23", size="body", bold=True, mono=True)
    f.lines(356, 260, ["buzzer output", "siren line"], size="small")

    # probe
    f.box(640, 104, 400, 196, fill=PLAN, dash="2 4", sw=2.2)
    f.text(840, 132, "Measuring instrument", size="head", bold=True)
    f.lines(840, 154, [
        "second ESP32, independent clock",
        "experiments/hardware/latency_probe",
        "rising-edge ISR, its own hardware timer",
    ], size="small")
    f.box(664, 216, 160, 72, fill="#FFFFFF")
    f.text(744, 240, "GPIO 34", size="body", bold=True, mono=True)
    f.lines(744, 260, ["PIN_PIR_SENSE", "input only"], size="small")
    f.box(856, 216, 160, 72, fill="#FFFFFF")
    f.text(936, 240, "GPIO 35", size="body", bold=True, mono=True)
    f.lines(936, 260, ["PIN_BUZZ_SENSE", "input only"], size="small")

    # The three wires are routed below both boards: a straight run from GPIO 13 to GPIO 34
    # would pass through the GPIO 23 box, which reads as a connection that does not exist.
    f.arrow([(164, 288), (164, 326), (744, 326), (744, 288)], sw=2.2)
    f.text(454, 318, "sensor edge  (t0)", size="small", fill=MUTED)
    f.arrow([(356, 288), (356, 358), (936, 358), (936, 288)], sw=2.2)
    f.text(646, 350, "siren edge  (t1)", size="small", fill=MUTED)
    f.box(386, 384, 328, 44, fill=SHARED)
    f.text(550, 412, "common ground  \u2014  required", size="body", bold=True)
    f.arrow([(100, 288), (100, 406), (386, 406)], head=False)
    f.arrow([(1000, 288), (1000, 406), (714, 406)], head=False)

    # what is measured
    f.box(60, 448, 980, 76, fill=MID)
    f.text(550, 474, "Measured quantity:  L = t1 \u2212 t0,  the confirmed sensor edge to the "
                     "siren line going active",
           size="body", bold=True)
    f.text(550, 498, "One value per trial, in microseconds, timed entirely on the probe's "
                     "clock. Written to results_hw.csv by collect.py.",
           size="small", fill=MUTED)

    # conditions
    f.box(60, 544, 980, 140, fill=PLAN, dash="4 3")
    f.text(550, 570, "Four conditions, same firmware throughout",
           size="head", bold=True)
    for i, (c, what, iso) in enumerate([
        ("A", "idle, broker reachable, no other traffic \u2014 the control", "none"),
        ("B", "legitimate MQTT load: frequent STATUS, large retained payloads", "none"),
        ("C", "high-rate publication on the device's own command topic", "none"),
        ("D", "802.11 deauthentication and disassociation frames at the device",
         "shielded enclosure + permission"),
    ]):
        y = 600 + i * 22
        f.text(84, y, f"{c}.", size="small", anchor="start", bold=True)
        f.text(112, y, what, size="small", anchor="start")
        f.text(1016, y, iso, size="small", anchor="end",
               fill=BAD_RED if c == "D" else MUTED)

    f.lines(550, 714, [
        "At least 50 samples per condition, 200 preferred: 200 detects a shift of about "
        "0.29 standard deviations",
        "at the pre-registered two-sided Mann\u2013Whitney U test, \u03b1 = 0.05, power = 0.80.",
    ], size="small")
    return f


# ---------------------------------------------------------------- driver -----
FIGS = {
    "architecture": architecture,
    "command_flow": command_flow,
    "command_sequence": command_sequence,
    "deployment": deployment,
    "methodology": methodology,
    "experimental_setup": experimental_setup,
    "security_paths": security_paths,
    "guard_decision": guard_decision,
    "acl_architecture": acl_architecture,
    "hardware_rig": hardware_rig,
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

    # Re-export the remaining hand-authored diagrams. BOTH pdf and png: the README embeds
    # the png, so exporting only the pdf leaves an edited svg invisible on GitHub. That
    # happened once -- a correction to state_machine.svg never reached its png, and the
    # repository kept showing the old text.
    #
    # architecture is no longer in this list: it is generated above, because the hand-drawn
    # version had its own type scale and printed its smallest label at 4.9 pt.
    for name in ("state_machine", "event_sequence", "circuit_wiring"):
        sp = os.path.join(out, name + ".svg")
        if os.path.exists(sp):
            cairosvg.svg2pdf(url=sp, write_to=os.path.join(out, name + ".pdf"))
            cairosvg.svg2png(url=sp, write_to=os.path.join(out, name + ".png"), scale=2.0)
            print(f"  {name}: pdf + png re-exported from svg")


if __name__ == "__main__":
    sys.exit(main())
