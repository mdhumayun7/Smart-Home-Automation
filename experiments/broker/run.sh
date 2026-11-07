#!/usr/bin/env bash
# E6: validate the access-control scenarios against a real Mosquitto broker.
#
# Unlike every other experiment in this repository, this one is a testbed measurement rather
# than a simulation: it starts an actual broker with TLS, password authentication and
# per-client ACLs, and observes what it does. Results go to
# experiments/results/broker_acl.jsonl and broker_acl_summary.md.
#
# Requires: mosquitto, mosquitto_passwd, openssl, python3 with paho-mqtt.
#   Debian or Ubuntu:  apt-get install -y mosquitto mosquitto-clients
#                      pip3 install paho-mqtt
set -euo pipefail
cd "$(dirname "$0")"

for tool in mosquitto mosquitto_passwd openssl; do
  command -v "$tool" >/dev/null || { echo "missing $tool; see the header of this script" >&2; exit 2; }
done
python3 -c "import paho.mqtt.client" 2>/dev/null \
  || { echo "missing paho-mqtt; pip3 install paho-mqtt" >&2; exit 2; }

# The run directory holds throwaway keys and a password file. It is regenerated on every run
# and is deliberately not committed.
RUN="${BROKER_RUN_DIR:-$PWD/run}"

echo "== generating broker material in $RUN =="
./setup.sh "$RUN" >/dev/null

echo "== running the access-control scenarios against mosquitto $(mosquitto -h | head -1 | awk '{print $3}') =="
python3 validate_acl.py --run-dir "$RUN"

echo
echo "== done; see ../results/broker_acl_summary.md =="
