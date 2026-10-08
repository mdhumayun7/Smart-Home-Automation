#!/usr/bin/env bash
# Builds the firmware against host-side stubs and runs every scenario at three
# millis() start values (0, 2^31 and just before the 2^32 wrap), for both
# arduino-esp32 2.x and 3.x LEDC APIs.
set -euo pipefail
cd "$(dirname "$0")"
SCENARIOS="basic arm_alarm disarm_in_entry door_left_open pir_edge pir_glitch remote display_fail oled network"
STARTS="0 2147483000 4294950000"
fail=0
for core in 3 2; do
  g++ -std=c++17 -Wall -Wextra -Wno-unused-parameter -DESP_ARDUINO_VERSION_MAJOR=$core \
      -I stubs -o "/tmp/fw_test_core$core" test_firmware.cpp
  for s in $SCENARIOS; do
    for st in $STARTS; do
      if "/tmp/fw_test_core$core" "$s" "$st" > /tmp/fw_test_out.txt 2>&1; then
        echo "PASS core$core $s start=$st"
      else
        echo "FAIL core$core $s start=$st"; grep FAIL /tmp/fw_test_out.txt || true; fail=1
      fi
    done
  done
done
exit $fail
