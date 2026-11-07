#!/usr/bin/env python3
"""Coarse trace conformance between the host harness and the TLA+ specification.

The TLA+ model is hand-written and nothing mechanically relates it to the firmware, so the
correspondence between the two has until now been an argument rather than a check. This closes
part of that gap: it extracts the state-transition relation *from the specification source*,
extracts the state sequence the real firmware actually produces under the ablation harness, and
checks that every observed transition is one the specification permits.

What this does and does not establish.

  It does establish that the firmware's reachable state sequences are a subset of those the
  specification allows, for the scenarios the harness exercises. A transition the firmware can
  make and the model cannot would be found here, and that is the direction that matters: it is
  how a model comes to prove something about a system that does not behave that way.

  It does not establish the converse. The harness does not exercise every behaviour the model
  permits, so this is not a refinement proof and no claim of one is made. It is also limited
  to the control state: the counter, the authentication flag and timing are not checked.

  The transition relation is parsed from AlarmFSM.tla rather than written out again here, so
  the check cannot silently drift from the specification it is checking against.

Usage: python3 -I test_conformance.py
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "..", "formal", "AlarmFSM.tla")
STUBS = os.path.join(HERE, "..", "tests", "host", "stubs")

# The firmware emits a state-change event named for the state it has entered; the TLA+ model
# names the same five states in camel case. This mapping is the only hand-written
# correspondence in the check, and it is one line per state.
EVENT_TO_STATE = {
    "disarmed": "Disarmed",
    "exit_delay": "ExitDelay",
    "armed": "Armed",
    "entry_delay": "EntryDelay",
    "alarm": "Alarm",
}

ACTION = re.compile(r"^([A-Z][A-Za-z0-9_]*)\s*==\s*$", re.M)


def parse_spec_transitions(path):
    """Extract {(from, to)} from the specification's actions.

    Each action is a block of /\\ conjuncts; a block that constrains both `state` and `state'`
    is a transition. A block that assigns `state'` without constraining `state` can fire from
    any state, which is represented by a wildcard source.
    """
    text = open(path).read()
    blocks, names = [], [(m.group(1), m.start()) for m in ACTION.finditer(text)]
    for i, (name, start) in enumerate(names):
        end = names[i + 1][1] if i + 1 < len(names) else len(text)
        blocks.append((name, text[start:end]))

    transitions, wildcard = set(), set()
    for name, body in blocks:
        if "state' =" not in body and "state' \\in" not in body:
            continue
        srcs = re.findall(r"state\s*=\s*\"(\w+)\"", body)
        srcs += re.findall(r"state\s*\\in\s*ArmedLike", body) and ["ExitDelay", "Armed",
                                                                   "EntryDelay", "Alarm"] or []
        dsts = re.findall(r"state'\s*=\s*\"(\w+)\"", body)
        if not dsts:
            continue
        if srcs:
            for a in srcs:
                for b in dsts:
                    transitions.add((a, b))
        else:
            for b in dsts:
                wildcard.add(b)
    return transitions, wildcard


def collect_traces(binary, modes, seed=2000, trials=6):
    """Run the harness and return the sequence of control states it entered, per mode."""
    out = {}
    for mode, extra_env in modes:
        env = dict(os.environ, ABLATION_TRACE="1", **extra_env)
        # The adversary injects random bytes, which reach the event source field, so the
        # trace is not valid UTF-8. Read it as bytes and replace what will not decode.
        r = subprocess.run([binary, "--mode", mode, "--trials", str(trials),
                            "--seed", str(seed)],
                           capture_output=True, env=env)
        states = []
        for line in r.stderr.decode("utf-8", errors="replace").splitlines():
            if not line.startswith("TRACE "):
                continue
            ev = line[6:].split(":", 1)[0]
            if ev in EVENT_TO_STATE:
                states.append(EVENT_TO_STATE[ev])
        out[mode] = states
    return out


def main():
    transitions, wildcard = parse_spec_transitions(SPEC)
    print(f"transitions parsed from {os.path.basename(SPEC)}: {len(transitions)}")
    for a, b in sorted(transitions):
        print(f"    {a:11} -> {b}")
    if wildcard:
        print(f"  reachable from any state: {sorted(wildcard)}")

    if not transitions:
        print("FAIL: no transitions parsed; the checker cannot be trusted")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        binary = os.path.join(tmp, "abl")
        subprocess.run(["g++", "-O2", "-std=c++17", "-w", "-I", STUBS, "-o", binary,
                        os.path.join(HERE, "ablation.cpp")], check=True, capture_output=True)
        traces = collect_traces(binary, [("none", {}), ("ratelimit", {}), ("token", {})])

    # Negative control. A checker that cannot fail proves nothing, which is the lesson of the
    # vacuous invariant in formal/AlarmFSM.tla. Inject a transition the specification forbids
    # and confirm the check rejects it before trusting any pass below.
    forbidden = ("Disarmed", "Alarm")
    assert forbidden not in transitions and forbidden[1] not in wildcard, \
        "the control transition is in fact allowed; pick another"
    synthetic = ["Disarmed", "Alarm"]
    caught = any((a, b) not in transitions and b not in wildcard
                 for a, b in zip(synthetic, synthetic[1:]))
    print(f"\n  {'ok  ' if caught else 'FAIL'} negative control: a forbidden "
          f"{forbidden[0]} -> {forbidden[1]} transition is rejected")
    if not caught:
        print("FAIL: the checker cannot detect a violation, so its passes mean nothing")
        return 1

    failures, total = [], 0
    print()
    for mode, states in traces.items():
        bad = []
        for a, b in zip(states, states[1:]):
            total += 1
            if a == b:
                continue                      # a repeated entry event, not a transition
            if (a, b) in transitions or b in wildcard:
                continue
            bad.append((a, b))
        uniq = sorted(set(bad))
        print(f"  {'ok  ' if not bad else 'FAIL'} {mode:10} "
              f"{len(states):4} states, {len(bad)} disallowed"
              f"{'' if not bad else '  ' + str(uniq[:4])}")
        if bad:
            failures.append(mode)

    print(f"\n{total} transitions checked")
    if failures:
        print(f"FAIL: the firmware made transitions the specification forbids: {failures}")
        print("Either the firmware is wrong or the model does not describe it. Both matter.")
        return 1
    print("all observed transitions are permitted by the specification")
    return 0


if __name__ == "__main__":
    sys.exit(main())
