#!/usr/bin/env bash
# Builds the firmware against host-side stubs and runs every scenario at three
# millis() start values (0, 2^31 and just before the 2^32 wrap), for both
# arduino-esp32 2.x and 3.x LEDC APIs.
set -euo pipefail
cd "$(dirname "$0")"
SCENARIOS="basic arm_alarm disarm_in_entry door_left_open pir_edge pir_glitch remote display_fail oled network persist restore restore_door diag hmac_vectors auth wifiguard linklost alert fusion"
STARTS="0 2147483000 4294950000"
fail=0
# Every MQTT payload that looks like JSON must parse (state, events, Home Assistant discovery).
check_json() {
  { grep '^PUB ' /tmp/fw_test_out.txt || true; } | cut -d' ' -f3- | python3 -c '
import json, sys
for line in sys.stdin:
    line = line.strip()
    if line.startswith("{"):
        json.loads(line)
'
}
for core in 3 2; do
  g++ -std=c++17 -Wall -Wextra -Werror -Wno-unused-parameter -DESP_ARDUINO_VERSION_MAJOR=$core \
      -I stubs -o "/tmp/fw_test_core$core" test_firmware.cpp
  for s in $SCENARIOS; do
    for st in $STARTS; do
      if "/tmp/fw_test_core$core" "$s" "$st" > /tmp/fw_test_out.txt 2>&1 && check_json; then
        echo "PASS core$core $s start=$st"
      else
        echo "FAIL core$core $s start=$st"; grep FAIL /tmp/fw_test_out.txt || true; fail=1
      fi
    done
  done
done

# Build-only checks of the optional configurations.
buildcheck() {  # <label> <flags...>
  local label="$1"; shift
  if g++ -std=c++17 -Wall -Wextra -Werror -Wno-unused-parameter -fsyntax-only -I stubs "$@" test_firmware.cpp; then
    echo "PASS build $label"
  else
    echo "FAIL build $label"; fail=1
  fi
}
buildcheck "TLS + remote disarm config" \
    -DMQTT_USE_TLS=1 -DSECRET_MQTT_CA_CERT='"-----BEGIN CERTIFICATE-----"' \
    -DSECRET_MQTT_USER='"user"' -DSECRET_MQTT_PASS='"pass"' -DALLOW_REMOTE_DISARM=1 \
    -DACKNOWLEDGE_UNAUTHENTICATED_DISARM
buildcheck "authenticated commands required" -DAUTH_COMMANDS=1 -DSECRET_CMD_KEY='"test-key-not-the-demo-key"'
buildcheck "PIR + radar fusion (AND)"        -DFUSION_MODE=FUSION_AND

# Negative build checks: these configurations must be REFUSED by the compile guards. A guard
# that stops rejecting them is a silent regression, so failure to fail is a test failure.
# See docs/SECURITY_ANALYSIS.md for why each combination is unsafe.
buildfails() {  # <label> <flags...>
  local label="$1"; shift
  if g++ -std=c++17 -fsyntax-only -I stubs "$@" test_firmware.cpp >/dev/null 2>&1; then
    echo "FAIL guard did not reject: $label"; fail=1
  else
    echo "PASS guard rejects $label"
  fi
}
# TLS plus a broker login does not authorize a publisher, so it must not be enough on its own.
buildfails "unauthenticated remote disarm behind TLS + login" \
    -DMQTT_USE_TLS=1 -DSECRET_MQTT_CA_CERT='"-----BEGIN CERTIFICATE-----"' \
    -DSECRET_MQTT_USER='"user"' -DSECRET_MQTT_PASS='"pass"' -DALLOW_REMOTE_DISARM=1
buildfails "unauthenticated remote disarm with no transport security" -DALLOW_REMOTE_DISARM=1
# Signing with the repository's published demo key is not authentication.
buildfails "AUTH_COMMANDS with the published demo key" -DAUTH_COMMANDS=1
buildcheck "Wi-Fi guard disabled"            -DENABLE_WIFI_GUARD=0

# The shared headers in the ESP-NOW receiver must be byte-identical to the alarm's.
for h in authmac.h alertmsg.h; do
  if diff -q "../../firmware/smart_home/$h" "../../firmware/espnow_receiver/$h" >/dev/null; then
    echo "PASS shared header in sync: $h"
  else
    echo "FAIL shared header drift: $h"; fail=1
  fi
done
exit $fail
