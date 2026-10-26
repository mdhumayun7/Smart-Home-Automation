#!/usr/bin/env python3
"""Evaluate the command-authentication defences against your OWN alarm device.

This is a verification tool, not an attack tool. It publishes to the command topic of a
device you control, on a broker you control, and checks that the firmware responds the way
the threat model requires: forged commands are rejected, replays are rejected, and only a
correctly signed command with a fresh counter is accepted. Run it on your own test setup.

It observes the device's reaction on the event topic, so you see the exact event the device
emitted (cmd_badmac, cmd_replay, cmd_rejected, exit_delay, disarmed, ...).

Requires: pip install paho-mqtt

Example:
    python3 tools/eval_commands.py \\
        --host test.mosquitto.org --device esp32-112233445566 \\
        --key "my-shared-key" --start-counter 1000
"""
import argparse
import hashlib
import hmac
import sys
import time

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("This tool needs paho-mqtt:  pip install paho-mqtt", file=sys.stderr)
    sys.exit(2)

TAG_BYTES = 16


def sign(verb, counter, key):
    base = f"{verb}:{counter}".encode()
    tag = hmac.new(key, base, hashlib.sha256).digest()[:TAG_BYTES]
    return f"{verb}:{counter}:{tag.hex()}"


class Watcher:
    def __init__(self):
        self.events = []

    def on_message(self, client, userdata, msg):
        self.events.append((time.time(), msg.payload.decode(errors="replace")))

    def wait_event(self, substr, timeout=4.0):
        """Return the first event containing substr seen within timeout, else None."""
        deadline = time.time() + timeout
        seen = 0
        while time.time() < deadline:
            while seen < len(self.events):
                _, payload = self.events[seen]
                seen += 1
                if substr in payload:
                    return payload
            time.sleep(0.05)
        return None


def main():
    p = argparse.ArgumentParser(description="Verify command-authentication defences on your device.")
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--device", required=True, help="device id, e.g. esp32-112233445566")
    p.add_argument("--root", default="svnit/smarthome")
    p.add_argument("--key", required=True, help="shared command key (same as the device's)")
    p.add_argument("--start-counter", type=int, default=1,
                   help="must exceed the device's stored counter")
    args = p.parse_args()

    key = args.key.encode()
    cmd_topic = f"{args.root}/{args.device}/cmd"
    evt_topic = f"{args.root}/{args.device}/event"

    w = Watcher()
    c = mqtt.Client()
    c.on_message = w.on_message
    c.connect(args.host, args.port, 30)
    c.subscribe(evt_topic)
    c.loop_start()
    time.sleep(1.0)

    results = []

    def check(name, payload, expect_substr, must_not=False):
        c.publish(cmd_topic, payload)
        got = w.wait_event(expect_substr)
        ok = (got is not None) != must_not
        results.append((name, ok, got or "(no matching event)"))

    n = args.start_counter

    # 1. A forged tag (right shape, wrong key) must be rejected.
    forged = sign("DISARM", n, b"wrong-key-" + key)
    check("forged DISARM rejected", forged, "cmd_badmac")

    # 2. An unsigned DISARM must be rejected.
    check("unsigned DISARM rejected", "DISARM", "cmd_rejected")

    # 3. A correctly signed ARM must be accepted.
    check("signed ARM accepted", sign("ARM", n), "exit_delay")

    # 4. Replaying that exact ARM must be rejected.
    check("replayed ARM rejected", sign("ARM", n), "cmd_replay")

    # 5. A signed DISARM at a higher counter must be accepted.
    check("signed DISARM accepted", sign("DISARM", n + 1), "disarmed")

    c.loop_stop()
    c.disconnect()

    print(f"\n{'result':6}  check")
    allok = True
    for name, ok, got in results:
        allok &= ok
        print(f"{'PASS' if ok else 'FAIL':6}  {name:28}  <- {got}")
    print()
    print("All command-authentication defences held." if allok
          else "Some checks FAILED - see above.")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
