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
g++ -O2 -std=c++17 -Wall -Wextra -o sensitivity sensitivity.cpp

echo "== E3: command-path ablation ($TRIALS trials per design) =="
{
  for m in none ratelimit token; do
    ./ablation_unauth --mode "$m" --trials "$TRIALS" --seed 2000
  done
  ./ablation_auth --mode hmac --trials "$TRIALS" --seed 2000
} > results/ablation.jsonl

echo "== E5: detector sensitivity sweep ($SENS_RUNS runs per cell) =="
./sensitivity --seed 11 --runs "$SENS_RUNS" > results/sensitivity.jsonl

echo "== analysing =="
python3 analyse_ablation.py > /dev/null

echo
echo "== done; see results/ablation_summary.md =="
