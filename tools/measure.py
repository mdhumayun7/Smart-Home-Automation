#!/usr/bin/env python3
"""Measure command-path latency and reconnect behaviour of your own alarm device.

Run against a device and broker you control. It reports:
  - command latency: time from publishing a signed STATUS to the state message arriving;
  - reconnect time: subscribe to availability and time how long "offline" -> "online" takes
    after you power-cycle the router (you trigger the outage; the script times the recovery).

For detection latency (sensor trigger -> event published), use the manual procedure in
docs/EVALUATION.md with a logic analyser, since the sensor must be triggered physically.

Requires: pip install paho-mqtt
"""
import argparse
import hashlib
import hmac
import statistics
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


def cmd_latency(args):
    state_topic = f"{args.root}/{args.device}/state"
    cmd_topic = f"{args.root}/{args.device}/cmd"
    got = {"t": None}

    def on_message(cl, u, msg):
        got["t"] = time.time()

    c = mqtt.Client()
    c.on_message = on_message
    c.connect(args.host, args.port, 30)
    c.subscribe(state_topic)
    c.loop_start()
    time.sleep(1.0)

    samples = []
    n = args.start_counter
    for _ in range(args.runs):
        got["t"] = None
        payload = sign("STATUS", n) if args.key else "STATUS"
        n += 1
        t0 = time.time()
        c.publish(cmd_topic, payload)
        while got["t"] is None and time.time() - t0 < 5:
            time.sleep(0.005)
        if got["t"] is not None:
            samples.append((got["t"] - t0) * 1000.0)
        time.sleep(0.5)

    c.loop_stop(); c.disconnect()
    if not samples:
        print("no responses - check device id, key and broker")
        return 1
    print(f"command latency over {len(samples)} runs (ms): "
          f"min {min(samples):.1f}  median {statistics.median(samples):.1f}  "
          f"max {max(samples):.1f}")
    return 0


def reconnect(args):
    avail_topic = f"{args.root}/{args.device}/availability"
    history = []

    def on_message(cl, u, msg):
        history.append((time.time(), msg.payload.decode(errors="replace")))

    c = mqtt.Client()
    c.on_message = on_message
    c.connect(args.host, args.port, 30)
    c.subscribe(avail_topic)
    c.loop_start()
    print("Watching availability. Now power-cycle the router or disable Wi-Fi.")
    print("Press Ctrl-C when you have seen one full offline -> online cycle.\n")
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    c.loop_stop(); c.disconnect()

    off_t = None
    for t, payload in history:
        print(f"  {time.strftime('%H:%M:%S', time.localtime(t))}  {payload}")
        if payload == "offline":
            off_t = t
        elif payload == "online" and off_t is not None:
            print(f"\nrecovery time: {t - off_t:.1f} s")
            off_t = None
    return 0


def main():
    p = argparse.ArgumentParser(description="Measure latency and reconnect time of your device.")
    p.add_argument("mode", choices=["latency", "reconnect"])
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--device", required=True)
    p.add_argument("--root", default="svnit/smarthome")
    p.add_argument("--key", default="", help="command key (needed if AUTH_COMMANDS is on)")
    p.add_argument("--start-counter", type=int, default=1)
    p.add_argument("--runs", type=int, default=20)
    args = p.parse_args()
    return cmd_latency(args) if args.mode == "latency" else reconnect(args)


if __name__ == "__main__":
    raise SystemExit(main())
