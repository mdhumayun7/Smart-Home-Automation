#!/usr/bin/env python3
"""Validate the access-control scenarios against a real Mosquitto broker.

The ablation in experiments/ablation.cpp models broker admission as a per-identity permission
on the command topic. This script checks that model against an actual broker with real TLS,
real password authentication and real per-client ACLs, and records what the broker actually
did, including its own log lines.

Method note, which matters for reading the results. MQTT 3.1.1 has no return code for "your
publish was refused by policy": the broker acknowledges a QoS 1 publish and then silently
discards it. A PUBACK is therefore *not* evidence of delivery. Every scenario below is decided
by whether a subscriber holding the device's identity actually receives the message, which is
also exactly how the real firmware would learn of it -- that is, it would not.

Scenarios map to the threat-model cases in the manuscript:

    A  remote adversary with no credentials
    B  adversary holding the single shared credential
    C  adversary holding the controller credential
    D  adversary holding the device credential
    E  adversary holding the device credential and the command key (flash dump)

Writes results/broker_acl.jsonl and results/broker_acl_summary.md.

Usage: python3 validate_acl.py [--run-dir DIR]
"""
import argparse
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
import uuid

import paho.mqtt.client as mqtt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
PORT = 18883
HOST = "127.0.0.1"
CMD_TOPIC = "home/alarm/esp32-1/cmd"
STAT_TOPIC = "home/alarm/esp32-1/stat"

CREDS = {
    "operator": ("operator", "operator-secret"),
    "device": ("device", "device-secret"),
    "shared": ("alarm", "alarm-secret"),
    "none": ("intruder", "no-such-password"),
}

# The command key as the firmware would hold it. In the flash-dump scenario the adversary has
# this, because it sits in the same image as the broker credentials.
CMD_KEY = b"test-key-not-the-demo-key"
TAG_BYTES = 16


def sign(verb, ctr, key=CMD_KEY):
    """Reproduce the firmware's payload format exactly.

    firmware/smart_home/smart_home.ino builds "<VERB>:<ctr>" and appends a colon and the first
    AUTH_TAG_BYTES of HMAC-SHA256 over that string, hex encoded.
    """
    base = f"{verb}:{ctr}"
    tag = hmac.new(key, base.encode(), hashlib.sha256).digest()[:TAG_BYTES]
    return f"{base}:{tag.hex()}"


class Broker:
    def __init__(self, run_dir, variant):
        self.run_dir, self.variant = run_dir, variant
        self.log = os.path.join(run_dir, f"broker_{variant}.log")
        self.proc = None

    def __enter__(self):
        if os.path.exists(self.log):
            os.remove(self.log)
        conf = os.path.join(self.run_dir, f"mosquitto_{self.variant}.conf")
        self.proc = subprocess.Popen(["mosquitto", "-c", conf],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Wait for the listener rather than sleeping a fixed amount.
        for _ in range(100):
            time.sleep(0.05)
            if _connect("operator", self.run_dir, probe=True):
                return self
        raise RuntimeError(f"broker did not come up for variant {self.variant}")

    def __exit__(self, *exc):
        self.proc.terminate()
        self.proc.wait(timeout=10)
        return False

    def denials(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, errors="replace") as fh:
            return [l.strip() for l in fh if "Denied PUBLISH" in l]


def _client(identity, run_dir):
    user, password = CREDS[identity]
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                    client_id=f"{identity}-{uuid.uuid4().hex[:8]}")
    c.username_pw_set(user, password)
    c.tls_set(ca_certs=os.path.join(run_dir, "ca.crt"))
    c.tls_insecure_set(False)       # the hostname must match the certificate
    return c


def _connect(identity, run_dir, probe=False):
    """Return the connected client, or None if the broker refused the connection."""
    c = _client(identity, run_dir)
    state = {}

    def on_connect(client, userdata, flags, rc, props=None):
        state["rc"] = rc

    c.on_connect = on_connect
    try:
        c.connect(HOST, PORT, keepalive=20)
    except Exception:
        return None
    c.loop_start()
    for _ in range(100):
        if "rc" in state:
            break
        time.sleep(0.05)
    rc = state.get("rc")
    ok = rc is not None and getattr(rc, "value", rc) == 0
    if probe or not ok:
        c.loop_stop()
        try:
            c.disconnect()
        except Exception:
            pass
        return True if (probe and ok) else None
    return c


def run_scenario(run_dir, variant, scenario, adversary_identity, payload, note):
    """Publish as the adversary and record whether a device-identity subscriber receives it."""
    sub_identity = "shared" if variant == "shared" else "device"
    sub = _connect(sub_identity, run_dir)
    if sub is None:
        raise RuntimeError(f"the subscriber ({sub_identity}) could not connect")
    received = []
    sub.on_message = lambda c, u, m: received.append(m.payload.decode(errors="replace"))
    sub.subscribe(CMD_TOPIC, qos=1)
    time.sleep(0.4)

    pub = _connect(adversary_identity, run_dir)
    connected = pub is not None
    puback = None
    if connected:
        info = pub.publish(CMD_TOPIC, payload, qos=1)
        try:
            info.wait_for_publish(timeout=5)
            puback = info.is_published()
        except Exception:
            puback = False
        time.sleep(0.8)
        pub.loop_stop()
        pub.disconnect()

    time.sleep(0.3)
    sub.loop_stop()
    sub.disconnect()

    delivered = any(r == payload for r in received)
    # The command is only acted on if it both reaches the device and verifies, so record the
    # application-layer check separately from the broker's decision.
    hmac_valid = None
    if payload.count(":") == 2:
        verb, ctr, tag = payload.split(":")
        hmac_valid = hmac.compare_digest(sign(verb, ctr), payload)

    return {
        "scenario": scenario,
        "acl_variant": variant,
        "adversary_identity": adversary_identity,
        "payload_kind": "signed" if hmac_valid is not None else "bare",
        "broker_accepted_connection": connected,
        "puback_received": puback,
        "delivered_to_device": delivered,
        "hmac_verifies": hmac_valid,
        "command_would_execute": bool(delivered and (hmac_valid is not False)),
        "note": note,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    run_dir = os.path.abspath(args.run_dir)
    rows, denials = [], {}

    # --- per-client ACL variant
    with Broker(run_dir, "perclient") as b:
        rows.append(run_scenario(
            run_dir, "perclient", "control-operator", "operator", "ARM",
            "the legitimate controller; must be delivered or the system does not work"))
        rows.append(run_scenario(
            run_dir, "perclient", "A", "none", "DISARM",
            "remote adversary with no credentials"))
        rows.append(run_scenario(
            run_dir, "perclient", "C", "operator", "DISARM",
            "adversary holding the controller credential"))
        rows.append(run_scenario(
            run_dir, "perclient", "D", "device", "DISARM",
            "adversary holding the device credential"))
        rows.append(run_scenario(
            run_dir, "perclient", "E", "device", sign("DISARM", 2000000),
            "flash dump: device credential and the command key"))
        rows.append(run_scenario(
            run_dir, "perclient", "E-control", "operator", sign("DISARM", 2000001),
            "the same signed command from an identity the ACL permits, to show the "
            "signature itself is valid and the ACL is what stops scenario E"))
        denials["perclient"] = b.denials()

    # --- shared-credential variant
    with Broker(run_dir, "shared") as b:
        rows.append(run_scenario(
            run_dir, "shared", "control-operator", "shared", "ARM",
            "the legitimate controller, using the shared account"))
        rows.append(run_scenario(
            run_dir, "shared", "B", "shared", "DISARM",
            "adversary holding the single shared credential"))
        denials["shared"] = b.denials()

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "broker_acl.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    write_summary(rows, denials)
    bad = [r for r in rows if r["scenario"].startswith("control") and not r["delivered_to_device"]]
    if bad:
        print("CONTROL FAILED: the legitimate controller was not delivered", file=sys.stderr)
        return 1
    print(f"wrote results/broker_acl.jsonl ({len(rows)} scenarios)")
    return 0


def write_summary(rows, denials):
    L = ["# Access-control validation against a real Mosquitto broker\n",
         "Generated by `experiments/broker/validate_acl.py`. **Evidence category: testbed "
         "measurement.** Unlike the arms in `ablation_summary.md`, these are observations of a "
         "real broker: Mosquitto 2.0.18 over TLS 1.2 with a private CA, password "
         "authentication, and per-client ACLs.\n",
         "A note on method. MQTT 3.1.1 has no return code meaning \"refused by policy\": the "
         "broker acknowledges a QoS 1 publish and then silently discards it. A PUBACK is "
         "therefore not evidence of delivery, and the `puback` column below shows that "
         "directly. Every scenario is decided by whether a subscriber holding the device's "
         "identity actually received the message.\n",
         "| Scenario | ACL | Adversary uses | Connected | PUBACK | Delivered | HMAC verifies |"
         " Command executes |", "|---|---|---|---|---|---|---|---|"]
    def y(v):
        return "-" if v is None else ("yes" if v else "**no**")
    for r in rows:
        L.append(f"| {r['scenario']} | {r['acl_variant']} | {r['adversary_identity']} | "
                 f"{y(r['broker_accepted_connection'])} | {y(r['puback_received'])} | "
                 f"{y(r['delivered_to_device'])} | {y(r['hmac_verifies'])} | "
                 f"**{'yes' if r['command_would_execute'] else 'no'}** |")
    L.append("")
    L.append("Scenario letters match the threat model in the manuscript: A no credentials, "
             "B shared credential, C controller credential, D device credential, E device "
             "credential and command key from a flash dump.\n")
    L.append("## What the broker itself logged\n")
    for variant, lines in denials.items():
        L.append(f"`{variant}` variant, {len(lines)} denied publishes:\n")
        L.append("```")
        L.extend(lines or ["(none)"])
        L.append("```\n")
    with open(os.path.join(RESULTS, "broker_acl_summary.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
