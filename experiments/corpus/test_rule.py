#!/usr/bin/env python3
"""Controls for the Rule 1 guard detector.

A detector that reports nothing is indistinguishable from a detector that is broken, and the
first version of this rule was broken: it missed this project's own guard, because the guard
names AUTH_COMMANDS under a negation and the rule treated any mention of an authentication
identifier as evidence that authentication was required. The corpus run returned zero hits and
that zero meant nothing until this file existed.

Every case below is a small synthetic source file with a known verdict. Run before trusting
any corpus result.

Usage: python3 -I test_rule.py
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

CASES = [
    # (name, source, should_be_flagged, why)
    ("prefix_guard_real",
     '#if ALLOW_REMOTE_DISARM && !AUTH_COMMANDS && (!MQTT_USE_TLS || !MQTT_HAS_LOGIN)\n'
     '#  error "needs TLS"\n#endif\n',
     True, "this project's own guard before the fix; the positive control"),

    ("postfix_guard_real",
     '#if ALLOW_REMOTE_DISARM && !AUTH_COMMANDS && !defined(ACKNOWLEDGE_UNAUTHENTICATED_DISARM)\n'
     '#  error "needs AUTH_COMMANDS"\n#endif\n',
     False, "the repaired guard: no transport identifier remains, so nothing to flag"),

    ("requires_appauth",
     '#if ALLOW_REMOTE_DISARM && AUTH_COMMANDS && MQTT_USE_TLS\n#  define OK 1\n#endif\n',
     False, "application authentication is required un-negated, so the guard is sound"),

    ("transport_only",
     '#if defined(ENABLE_REMOTE_UNLOCK) && defined(MQTT_USE_TLS)\n'
     '#  define UNLOCK_OK 1\n#endif\n',
     True, "a capability gated on transport alone"),

    ("capability_only",
     '#if ALLOW_REMOTE_DISARM\n#  define X 1\n#endif\n',
     False, "no transport identifier: not the pattern this rule describes"),

    ("transport_no_capability",
     '#if MQTT_USE_TLS && defined(MQTT_USER)\n#  define Y 1\n#endif\n',
     False, "transport configuration with no privileged capability being gated"),

    ("continuation",
     '#if defined(ALLOW_REMOTE_OTA) && \\\n    defined(MQTT_USE_TLS)\n#  define Z 1\n#endif\n',
     True, "the condition spans a backslash continuation and must still be parsed"),

    ("negated_hmac_elsewhere",
     '#if ENABLE_REMOTE_CONTROL && MQTT_TLS && !USE_HMAC\n#  define W 1\n#endif\n',
     True, "authentication is named but negated, which is evidence for the defect, not against"),
]


def main():
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        corpus = os.path.join(tmp, "corpus")
        for name, src, _, _ in CASES:
            d = os.path.join(corpus, f"ctrl__{name}")
            os.makedirs(d)
            with open(os.path.join(d, "main.c"), "w") as fh:
                fh.write(src)
        shas = os.path.join(tmp, "shas.tsv")
        with open(shas, "w") as fh:
            for name, _, _, _ in CASES:
                fh.write(f"ctrl/{name}\tSYNTHETIC\n")
        out = os.path.join(tmp, "out.json")
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "analyse_guards.py"),
                        "--corpus", corpus, "--shas", shas, "--out", out],
                       check=True, capture_output=True)
        import json
        res = {r["project"].split("/", 1)[1]: r for r in json.load(open(out))["results"]}

    for name, _, expect, why in CASES:
        got = bool(res[name]["rule1_hits"])
        mark = "ok " if got == expect else "FAIL"
        if got != expect:
            failures.append(name)
        print(f"  {mark} {name:26} expected={'flag' if expect else 'clean':5} "
              f"got={'flag' if got else 'clean':5}  {why}")

    print()
    if failures:
        print(f"{len(failures)} control(s) failed: {failures}")
        print("Corpus results from this rule are not trustworthy until these pass.")
        return 1
    print(f"all {len(CASES)} controls pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
