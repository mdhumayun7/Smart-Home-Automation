#!/usr/bin/env python3
"""Detect build configurations that treat transport security as command authorization.

Two rules, defined before the corpus was inspected.

RULE 1 -- the guard pattern, a direct analogue of the defect found in this project's own
firmware. A preprocessor conditional whose controlling expression

    (a) names at least one TRANSPORT identifier (TLS, a broker username or password, a CA
        certificate), and
    (b) names at least one CAPABILITY identifier (a remote actuation or override the guard is
        gating), and
    (c) does not *require* application-layer authentication.

Condition (c) is polarity-aware, and getting this wrong was the first thing a positive control
caught. This project's own guard reads

    #if ALLOW_REMOTE_DISARM && !AUTH_COMMANDS && (!MQTT_USE_TLS || !MQTT_HAS_LOGIN)

and it names AUTH_COMMANDS -- but *negated*. The guard fires an error when application
authentication is off and the transport is weak, which is precisely to say that it permits the
capability when application authentication is off and the transport is strong. A rule that
treated any mention of an authentication identifier as "authentication is required" therefore
missed the very defect it was written to find. A negated application-auth identifier does not
suppress a hit; it is evidence for one. The reading is that the build treats "the transport is secured" as sufficient
authority to enable a privileged capability, which is the unsound inference. Rule 1 is narrow
on purpose: it looks for the specific shape, so every hit can be read by hand.

RULE 2 -- the weaker, more prevalent condition. A project that subscribes to MQTT, dispatches
on the received payload to a privileged action, and contains no application-layer message
authentication anywhere in its sources. Such a project's command authorization rests entirely
on broker credentials. Rule 2 is a heuristic over whole repositories and is expected to have
false positives; it is reported with a manual-validation sample, never as a precise count.

Neither rule is a vulnerability detector. Rule 1 finds a configuration shape; Rule 2 finds an
absence. Whether either is a defect in a given project depends on that project's threat model,
which only a human can judge. The output is input to manual review, not a verdict.

Usage: python3 -I analyse_guards.py --corpus DIR --shas DIR/_shas.tsv --out findings.json
"""
import argparse
import json
import os
import re

SRC_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".ino"}
MAX_BYTES = 2_000_000          # skip generated or vendored blobs

TRANSPORT = re.compile(
    r"\b\w*(?:USE_TLS|USE_SSL|ENABLE_TLS|ENABLE_SSL|MQTT_TLS|MQTT_SSL|MQTTS"
    r"|CA_CERT|CACERT|ROOT_CA|SERVER_CERT"
    r"|MQTT_USER|MQTT_PASS|MQTT_USERNAME|MQTT_PASSWORD"
    r"|BROKER_USER|BROKER_PASS|HAS_LOGIN|HAS_AUTH|USE_AUTH)\w*\b", re.I)

CAPABILITY = re.compile(
    r"\b\w*(?:REMOTE_DISARM|REMOTE_UNLOCK|REMOTE_OPEN|REMOTE_CONTROL|REMOTE_CMD"
    r"|ALLOW_REMOTE|ENABLE_REMOTE|REMOTE_ADMIN|REMOTE_OTA"
    r"|DISARM|UNLOCK|OVERRIDE|ACTUAT|ALLOW_OTA|ENABLE_OTA|OTA_UPDATE"
    r"|ADMIN_CMD|ALLOW_CMD|ENABLE_CMD|ALLOW_CONTROL|ENABLE_CONTROL)\w*\b", re.I)

APPAUTH = re.compile(
    r"\b\w*(?:HMAC|CMAC|POLY1305|ED25519|ECDSA|RSA_VERIFY|SIGNATURE|SIGNED_|SIGN_CMD"
    r"|AUTH_COMMAND|AUTH_CMD|CMD_AUTH|VERIFY_MAC|MAC_VERIFY|NONCE|REPLAY|JWT"
    r"|MESSAGE_AUTH|PAYLOAD_AUTH)\w*\b", re.I)

# Rule 2 evidence.
SUBSCRIBE = re.compile(
    r"\b(?:mqtt_?client_?subscribe|esp_mqtt_client_subscribe|mosquitto_subscribe"
    r"|\.subscribe\s*\(|->subscribe\s*\(|MQTTSubscribe|mqtt_subscribe)\b", re.I)
PAYLOAD_DISPATCH = re.compile(
    r"\b(?:strcmp|strncmp|strstr|strcasecmp|equalsIgnoreCase|indexOf)\s*\("
    r"[^;{]{0,80}(?:payload|message|msg|topic|data)\b", re.I)
ACTUATE = re.compile(
    r"\b(?:digitalWrite|ledcWrite|gpio_set_level|relay|servo|solenoid|unlock|open_?door"
    r"|lock_?open|setRelay|turnOn|turn_on)\b", re.I)

# An application-auth identifier under a negation: "!AUTH_COMMANDS", "! defined(HMAC_CMD)",
# "ifndef USE_HMAC". These do not establish that authentication is required.
NEGATED_APPAUTH = re.compile(
    r"!\s*(?:defined\s*\(\s*)?\w*(?:HMAC|CMAC|POLY1305|ED25519|ECDSA|RSA_VERIFY|SIGNATURE"
    r"|SIGNED_|SIGN_CMD|AUTH_COMMAND|AUTH_CMD|CMD_AUTH|VERIFY_MAC|MAC_VERIFY|NONCE|REPLAY|JWT"
    r"|MESSAGE_AUTH|PAYLOAD_AUTH)\w*", re.I)

COND = re.compile(r"^\s*#\s*(if|elif|ifdef|ifndef)\b(.*)$")


def sources(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in {".git", "node_modules", "build", ".pio", "managed_components"}]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in SRC_EXT:
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(p) > MAX_BYTES:
                        continue
                    with open(p, errors="replace") as fh:
                        yield p, fh.read()
                except OSError:
                    continue


def logical_conditions(text):
    """Yield (line_number, full_condition) with backslash continuations joined."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = COND.match(lines[i])
        if m:
            start, cond = i + 1, m.group(2)
            while cond.rstrip().endswith("\\") and i + 1 < len(lines):
                i += 1
                cond = cond.rstrip()[:-1] + " " + lines[i]
            yield start, cond.strip()
        i += 1


def analyse_project(name, root):
    r1, files_scanned = [], 0
    has_sub = has_dispatch = has_actuate = has_appauth = False
    appauth_files = []

    for path, text in sources(root):
        files_scanned += 1
        rel = os.path.relpath(path, root)
        if SUBSCRIBE.search(text):
            has_sub = True
        if PAYLOAD_DISPATCH.search(text):
            has_dispatch = True
        if ACTUATE.search(text):
            has_actuate = True
        if APPAUTH.search(text):
            has_appauth = True
            if len(appauth_files) < 5:
                appauth_files.append(rel)

        for lineno, cond in logical_conditions(text):
            if not cond:
                continue
            t, c = TRANSPORT.search(cond), CAPABILITY.search(cond)
            if not (t and c):
                continue
            # Polarity: an app-auth identifier only means "authentication is required" when it
            # appears un-negated. Strip negated occurrences before testing for a requirement.
            stripped = NEGATED_APPAUTH.sub(" ", cond)
            requires_appauth = APPAUTH.search(stripped)
            if requires_appauth:
                continue
            r1.append({"file": rel, "line": lineno, "condition": cond[:300],
                       "transport_token": t.group(0), "capability_token": c.group(0),
                       "negated_appauth": bool(NEGATED_APPAUTH.search(cond))})

    return {
        "project": name,
        "files_scanned": files_scanned,
        "rule1_hits": r1,
        "rule2": {
            "subscribes": has_sub,
            "dispatches_on_payload": has_dispatch,
            "actuates": has_actuate,
            "has_application_auth": has_appauth,
            "appauth_evidence": appauth_files,
            # The condition: commands arrive and drive an actuator, and nothing in the
            # repository authenticates the message itself.
            "flagged": bool(has_sub and has_dispatch and has_actuate and not has_appauth),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--shas", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    shas = {}
    with open(args.shas) as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 2:
                shas[parts[0]] = parts[1]

    results = []
    for safe in sorted(os.listdir(args.corpus)):
        root = os.path.join(args.corpus, safe)
        if not os.path.isdir(root):
            continue
        name = safe.replace("__", "/", 1)
        r = analyse_project(name, root)
        r["commit"] = shas.get(name, "UNKNOWN")
        results.append(r)

    r1_projects = [r for r in results if r["rule1_hits"]]
    r2_projects = [r for r in results if r["rule2"]["flagged"]]
    doc = {
        "n_projects": len(results),
        "rule1_projects": len(r1_projects),
        "rule1_total_hits": sum(len(r["rule1_hits"]) for r in results),
        "rule2_projects": len(r2_projects),
        "results": results,
    }
    with open(args.out, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)

    print(f"projects analysed      : {len(results)}")
    print(f"Rule 1 (guard pattern) : {len(r1_projects)} projects, "
          f"{doc['rule1_total_hits']} hits")
    for r in r1_projects:
        for h in r["rule1_hits"]:
            print(f"   {r['project']}  {h['file']}:{h['line']}  {h['condition'][:90]}")
    print(f"Rule 2 (no app auth)   : {len(r2_projects)} projects flagged, "
          f"before manual validation")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
