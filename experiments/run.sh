#!/usr/bin/env bash
# Build and run the whole simulation + fuzzing pipeline, then analyse and plot.
# Deterministic: fixed seeds make every run identical.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results
STUBS=../tests/host/stubs

TRIALS="${TRIALS:-3000}"
FUZZ_ITERS="${FUZZ_ITERS:-3000000}"

echo "== building campaign =="
g++ -O2 -std=c++17 -Wall -Wextra -Wno-unused-parameter -I "$STUBS" -o campaign_baseline campaign.cpp
g++ -O2 -std=c++17 -Wall -Wextra -Wno-unused-parameter -DAUTH_COMMANDS=1 -I "$STUBS" -o campaign_hardened campaign.cpp

echo "== running campaign ($TRIALS trials per build) =="
./campaign_baseline --trials "$TRIALS" --seed 1000 > results/campaign_baseline.jsonl
./campaign_hardened --trials "$TRIALS" --seed 1000 > results/campaign_hardened.jsonl

echo "== analysing =="
python3 analyse.py > /dev/null
python3 make_figures.py

echo "== fuzzing command parser ($FUZZ_ITERS iters) =="
g++ -O2 -g -std=c++17 -Wall -Wextra -Wno-unused-parameter -fsanitize=address,undefined \
    -DAUTH_COMMANDS=1 -I "$STUBS" -o fuzz_cmd fuzz_cmd.cpp
./fuzz_cmd --iters "$FUZZ_ITERS" --seed 7 | tee results/fuzz.json

echo
echo "== done; see results/summary.md =="
