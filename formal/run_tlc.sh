#!/usr/bin/env bash
# Model-check the alarm specification with TLC. Downloads tla2tools.jar if it is not
# already present (pinned version), then checks every invariant and property in the .cfg.
set -euo pipefail
cd "$(dirname "$0")"

TLA_VERSION="v1.8.0"
JAR="${TLA_TOOLS_JAR:-tla2tools.jar}"
if [ ! -f "$JAR" ]; then
  echo "Downloading tla2tools ${TLA_VERSION}..."
  curl -sSL -o "$JAR" \
    "https://github.com/tlaplus/tlaplus/releases/download/${TLA_VERSION}/tla2tools.jar"
fi

fail=0
for m in AlarmFSM Isolation; do
  echo
  echo "=== TLC: $m ==="
  if java -XX:+UseParallelGC -cp "$JAR" tlc2.TLC -config "$m.cfg" "$m.tla"; then
    echo "PASS $m"
  else
    echo "FAIL $m"; fail=1
  fi
done
exit $fail
