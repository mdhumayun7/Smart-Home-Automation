#!/usr/bin/env python3
"""Sign an alarm command so the device will accept it.

The firmware trusts a command on the MQTT command topic only when it carries a valid
HMAC-SHA256 tag over a strictly increasing counter (see firmware/smart_home/authmac.h).
This tool builds that signed string. The counter must be higher than any the device has
already accepted; it is stored in NVS, so it also has to beat the last value across reboots.

Usage:
    python3 tools/sign_command.py DISARM 42 --key "my-shared-key"
    python3 tools/sign_command.py DISARM 42 --key-file key.txt

Then publish the printed string, for example:
    mosquitto_pub -h HOST -t "svnit/smarthome/<deviceId>/cmd" -m "DISARM:42:<tag>"

The key and the counter are secrets of your deployment; do not commit real ones.
"""
import argparse
import hashlib
import hmac
import sys

TAG_BYTES = 16  # must match AUTH_TAG_BYTES in authmac usage


def sign(verb: str, counter: int, key: bytes) -> str:
    verb = verb.upper()
    if verb not in ("ARM", "ARM_AWAY", "DISARM", "STATUS"):
        raise ValueError(f"unknown command: {verb}")
    if counter < 0:
        raise ValueError("counter must be non-negative")
    base = f"{verb}:{counter}".encode()
    tag = hmac.new(key, base, hashlib.sha256).digest()[:TAG_BYTES]
    return f"{verb}:{counter}:{tag.hex()}"


def main() -> int:
    p = argparse.ArgumentParser(description="Sign an alarm command with HMAC-SHA256.")
    p.add_argument("command", help="ARM, DISARM or STATUS")
    p.add_argument("counter", type=int, help="strictly increasing counter")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--key", help="shared key as text")
    g.add_argument("--key-file", help="file containing the shared key")
    args = p.parse_args()

    if args.key is not None:
        key = args.key.encode()
    else:
        with open(args.key_file, "rb") as f:
            key = f.read().strip()

    try:
        print(sign(args.command, args.counter, key))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
