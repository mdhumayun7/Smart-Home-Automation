#!/usr/bin/env bash
# Build and run the ablation (E3) and the detector sensitivity sweep (E5), then analyse.
# Deterministic: fixed seeds make every run identical.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results
STUBS=../tests/host/stubs

TRIALS="${TRIALS:-300}"
SENS_RUNS="${SENS_RUNS:-2000}"

echo "== building =="
g++ -O2 -std=c++17 -Wall -Wextra -Wno-unused-parameter -I "$STUBS" \
    -o ablation_unauth ablation.cpp
g++ -O2 -std=c++17 -Wall -Wextra -Wno-unused-parameter -DAUTH_COMMANDS=1 -I "$STUBS" \
    -o ablation_auth ablation.cpp
# Transport-security variant. MQTT_USE_TLS with broker credentials is the only configuration
# in which the firmware's compile guard permits ALLOW_REMOTE_DISARM without application-layer
# authentication, so this build is what the leaked-credential mode must be tested against.
g++ -O2 -std=c++17 -Wall -Wextra -Wno-unused-parameter \
    -DMQTT_USE_TLS=1 -DSECRET_MQTT_USER='"alarm"' -DSECRET_MQTT_PASS='"pw"' \
    -DSECRET_MQTT_CA_CERT='"-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----\n"' \
    -DALLOW_REMOTE_DISARM=1 -I "$STUBS" -o ablation_tls ablation.cpp
g++ -O2 -std=c++17 -Wall -Wextra -o sensitivity sensitivity.cpp

echo "== E3: command-path ablation, 6 designs ($TRIALS trials each) =="
{
  for m in none ratelimit token transport; do
    ./ablation_unauth --mode "$m" --trials "$TRIALS" --seed 2000
  done
  ./ablation_tls  --mode transport_leaked --trials "$TRIALS" --seed 2000
  ./ablation_auth --mode hmac             --trials "$TRIALS" --seed 2000
} > results/ablation.jsonl

echo "== E5: detector sensitivity sweep ($SENS_RUNS runs per cell) =="
./sensitivity --seed 11 --runs "$SENS_RUNS" > results/sensitivity.jsonl

echo "== analysing =="
python3 analyse_ablation.py > /dev/null

echo
echo "== done; see results/ablation_summary.md =="
