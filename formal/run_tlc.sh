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
# Negative check: the defective build configuration must be REJECTED.
#
# AlarmFSM_unsafe.cfg sets AllowUnauthDisarm = TRUE, which models the ALLOW_REMOTE_DISARM
# build with no application-layer authentication. TLC must report a violation of
# NoUnauthRemoteDisarm. A run that *passes* means the specification has stopped modelling the
# defect, which is the regression this check exists to catch -- and it is exactly the state
# the specification was in before: badDisarm could never be set, so the invariant was
# unfalsifiable and the model checker could not have caught the real firmware defect.
echo
echo "=== TLC: AlarmFSM, defective configuration (a violation is REQUIRED) ==="
if java -XX:+UseParallelGC -cp "$JAR" tlc2.TLC \
     -config AlarmFSM_unsafe.cfg AlarmFSM.tla > /tmp/tlc_unsafe.out 2>&1; then
  echo "FAIL AlarmFSM_unsafe: TLC found no violation, so the invariant is vacuous again"
  fail=1
elif grep -q "Invariant NoUnauthRemoteDisarm is violated" /tmp/tlc_unsafe.out; then
  echo "PASS AlarmFSM_unsafe: TLC reports the expected NoUnauthRemoteDisarm violation"
  grep -A2 "The behavior up to this point" /tmp/tlc_unsafe.out | head -3
else
  echo "FAIL AlarmFSM_unsafe: TLC failed, but not with the expected invariant violation"
  tail -20 /tmp/tlc_unsafe.out
  fail=1
fi

exit $fail
