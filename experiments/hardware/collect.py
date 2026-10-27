#!/usr/bin/env python3
"""Collect latency rows from the latency_probe board over serial into a tagged data file.

Each line from the probe is "index,latency_us". This appends them to a CSV with a condition
column so analyse_hw.py can compare conditions.

Usage:
    python3 collect.py --port /dev/ttyUSB1 --condition A --n 50 --out results_hw.csv

Requires: pip install pyserial
"""
import argparse
import csv
import os
import sys
import time

try:
    import serial
except ImportError:
    print("This tool needs pyserial:  pip install pyserial", file=sys.stderr)
    sys.exit(2)


def main():
    p = argparse.ArgumentParser(description="Collect latency samples from the probe board.")
    p.add_argument("--port", required=True, help="serial port of the probe board")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--condition", required=True, help="condition label, e.g. A, B, C, D")
    p.add_argument("--n", type=int, default=50, help="number of samples to collect")
    p.add_argument("--out", default="results_hw.csv")
    args = p.parse_args()

    new_file = not os.path.exists(args.out)
    ser = serial.Serial(args.port, args.baud, timeout=2)
    got = 0
    with open(args.out, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["condition", "index", "latency_us"])
        print(f"Collecting {args.n} samples for condition {args.condition}. "
              f"Trigger the PIR now; Ctrl-C to stop early.")
        try:
            while got < args.n:
                line = ser.readline().decode(errors="replace").strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(",")
                if len(parts) != 2:
                    continue
                try:
                    idx, us = int(parts[0]), int(parts[1])
                except ValueError:
                    continue
                w.writerow([args.condition, idx, us])
                f.flush()
                got += 1
                print(f"  [{got}/{args.n}] {us/1000.0:.2f} ms")
        except KeyboardInterrupt:
            pass
    print(f"wrote {got} samples for condition {args.condition} to {args.out}")


if __name__ == "__main__":
    main()
