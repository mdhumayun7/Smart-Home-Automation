# Does the compile-guard pattern occur elsewhere? A corpus study

Written to answer a reviewer objection: the configuration-logic defect reported in this work
is one defect in one codebase, and a single self-reported finding is an anecdote until it is
shown to generalise.

**The answer is that it does not generalise, on this evidence.** The guard pattern was not
found in any of 135 open-source embedded MQTT projects. The finding stays a single-system case
study, and the manuscript says so. What the corpus did show is something different and, we
think, more useful: the reason the pattern is absent is that most of these projects never
implement application-layer authentication at all, so they have no guard to get wrong.

Everything below is reproducible from `experiments/corpus/`.

---

## 1. Corpus

Built by `build_corpus.py`, which applies fixed criteria mechanically. The selection is
recorded in `corpus.json` together with the queries that produced it.

| Criterion | Value |
|---|---|
| Source | GitHub repository search, 22 fixed queries listed in `corpus.json` |
| Language | C or C++ |
| Minimum stars | 3 |
| Maximum repository size | 80,000 KB, to exclude vendor SDK mirrors |
| Archived repositories | excluded |
| Forks | excluded, since a fork duplicates its parent and would inflate any rate |
| De-duplication | by full name across queries |

**Result: 135 projects.** Rejected: 437 below the star threshold, 36 duplicates, 9 oversized,
6 archived. Every project was shallow-cloned and its exact commit recorded in
`commit_shas.tsv`; all 135 clones succeeded.

### Bias, stated plainly

This corpus is **not** a random sample of embedded MQTT firmware, and no claim here should be
read as if it were.

- GitHub search ranks by relevance and we sorted by stars, so the corpus skews toward visible,
  popular projects. Firmware in products, in private repositories, or on other forges is
  absent entirely.
- The queries are in English and name ESP32, ESP8266, Arduino and Zephyr. Other platforms and
  other languages of project description are underrepresented.
- A three-star floor excludes 437 repositories. That filter removes abandoned scratch work, but
  it also removes exactly the unpolished projects most likely to contain the defects we are
  looking for. The direction of that bias is against finding problems.
- 135 is a small corpus for any rate.

## 2. Rule 1: the guard pattern

A preprocessor conditional whose controlling expression (a) names a transport-security
identifier, (b) names a privileged-capability identifier, and (c) does not *require*
application-layer authentication. Defined in full, with its identifier sets, in
`analyse_guards.py`.

### The rule was wrong the first time, and the corpus result was meaningless until it was fixed

The first version returned **zero hits across all 135 projects**, which looked like a clean
negative result. It was not. Run against this project's own firmware before the repair, it also
returned zero: it could not detect the very defect it was written to find.

The cause is polarity. This project's guard reads

```c
#if ALLOW_REMOTE_DISARM && !AUTH_COMMANDS && (!MQTT_USE_TLS || !MQTT_HAS_LOGIN)
```

and it does name `AUTH_COMMANDS` — but negated. Condition (c) treated any mention of an
authentication identifier as evidence that authentication was required, so the guard excluded
itself. A negated authentication identifier is evidence *for* the pattern, not against it.

`test_rule.py` now holds eight controls, including the real pre-repair guard as a positive
control and the repaired guard as a negative control. All eight pass. **A detector that reports
nothing is indistinguishable from a detector that is broken, and this one was broken.**

### Result, with the validated rule

**0 hits in 135 projects.**

The honest reading is that the specific guard shape is not present in this corpus, so this
work provides no evidence that it is a widespread pattern. The finding is a single-system case
study and is reported as one.

### Why zero, which is the interesting part

The Rule 1 pattern can only occur in a project that implements application-layer
authentication *as an option* and then writes a build condition choosing between it and
transport security. Of the 135 projects:

| | Projects |
|---|---|
| Subscribe to MQTT | 87 |
| Actuate something | 98 |
| Contain any application-auth identifier | 39 |
| Subscribe **and** contain an application-auth identifier | 30 |

Thirty is the largest population in which the pattern could exist, and reading those thirty
shows most of the matches are in vendored code — FreeRTOS `queue.c`, ArduinoJson's test suite,
a bundled `catch.hpp`, the PubSubClient library — rather than in the project's own command
path. The population of projects that genuinely implement authenticated commands and could
therefore write an unsound guard about them is very small.

That is worth stating directly: **the defect reported in this paper is a defect of a
comparatively sophisticated project.** A simpler project cannot make this mistake, because it
never had application-layer authentication to weigh transport security against. It is simply
unauthenticated.

## 3. Rule 2: command authorization resting entirely on broker credentials

The weaker condition the corpus can speak to. A project that subscribes to MQTT, dispatches on
the received payload, drives an actuator, and contains no application-layer message
authentication anywhere in its own sources.

**18 of 135 projects flagged. All 18 were read by hand**; the procedure and per-project verdicts
are in `manual_validation.json`.

| Verdict | Projects |
|---|---|
| Confirmed: an unauthenticated MQTT payload moves something physical | **9** |
| False positive | 9 |
| Uncertain | 0 |

The confirmed cases include a garage door opener in which a payload of `"trigger"` reaches
`digitalWrite(RELAY_PIN, HIGH)`, an alarm keypad, a heating relay, a spa heater and pump, a
boiler's setpoints, and Modbus register writes. The false positives are monitoring and display
projects, plus one whose only actuation match was inside a bundled WiFiManager example sketch.

### Why 18/135 is not a rate

The automated figure is wrong in both directions and should not be quoted as prevalence.

- It **over-counts** by about fifty per cent: nine of eighteen flagged projects only display or
  publish. The rule cannot distinguish a write to a status LED from a write to a relay.
- It **under-counts** by an unknown amount: three of the nine confirmed cases actuate through
  Modbus, RF or a serial command frame, and were flagged only because an unrelated GPIO write
  happened to be present elsewhere. A project that actuates solely through those channels is
  missed entirely. The automated count is therefore not even a lower bound.

What the manual validation supports is an **existence** claim: projects that open garage doors
and drive heating relays from unauthenticated MQTT payloads demonstrably exist in the
open-source corpus, at this commit, and can be named. It does not support a rate.

## 4. What this changes in the manuscript

- The compile-guard finding is **not** claimed to be prevalent. It is a single-system case
  study, and the corpus is cited as the evidence for that restraint rather than for a
  generalisation.
- The broader observation it motivates — that command authorization in this device class
  commonly rests entirely on broker credentials — is supported by named, manually validated
  examples, and is stated as existence rather than as a rate.
- The rule's own failure is reported. It is a third instance of this paper's central claim: a
  detector that asserts a property without a control is itself an unverified assertion, and the
  cheap check that falsified it was a single positive control.

## 5. Reproducing

```bash
cd experiments/corpus
python3 build_corpus.py                      # rebuilds corpus.json from GitHub search
./fetch_corpus.sh /some/scratch/dir          # shallow clones, records commit SHAs
python3 -I test_rule.py                      # 8 controls; must pass before trusting results
python3 -I analyse_guards.py --corpus /some/scratch/dir \
    --shas /some/scratch/dir/_shas.tsv --out findings.json
```

Repository contents change, so `build_corpus.py` will not return the same 135 projects at a
later date. `commit_shas.tsv` pins what was actually analysed. The analysis scripts are run
with `python3 -I` and the cloned corpus is kept outside the script directory, because cloned
third-party code is untrusted input.
