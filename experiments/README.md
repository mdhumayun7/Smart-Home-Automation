# Experiments and reproducibility artifact

Everything needed to reproduce the formal, simulation and fuzzing results in the paper. Each
result is produced by a seeded program; nothing is hand-entered. The one result that needs
physical hardware (latency invariance under on-chip radio stress) has its apparatus in
`hardware/` and is the single open step.

## Layout

```
campaign.cpp      randomised adversarial campaign against the real firmware logic
fuzz_cmd.cpp      command-parser fuzzer (AddressSanitizer + UBSan)
analyse.py        aggregates campaign JSONL -> summary tables + hypothesis test
make_figures.py   campaign figure (PDF/PNG), colourblind- and greyscale-safe
run.sh            builds and runs the whole simulation+fuzz pipeline end to end
results/          generated outputs (JSONL, summary.md/json, figures)
hardware/         measurement apparatus and protocol for the hardware latency campaign
../formal/        TLA+ models (AlarmFSM, Isolation) and run_tlc.sh
```

## Reproduce the simulation results

```bash
cd experiments
./run.sh            # ~5 min: 6000-trial campaign, 3M-iteration fuzz, analysis, figures
```

This writes `results/summary.md`, `results/summary.json`, `results/fig_campaign.pdf`, and the
raw per-trial JSONL. Fixed seeds make every run identical.

Individual steps:

```bash
g++ -O2 -std=c++17 -I ../tests/host/stubs -o campaign_baseline campaign.cpp
g++ -O2 -std=c++17 -DAUTH_COMMANDS=1 -I ../tests/host/stubs -o campaign_hardened campaign.cpp
./campaign_baseline --trials 3000 --seed 1000 > results/campaign_baseline.jsonl
./campaign_hardened --trials 3000 --seed 1000 > results/campaign_hardened.jsonl
python3 analyse.py && python3 make_figures.py

g++ -O2 -g -std=c++17 -fsanitize=address,undefined -DAUTH_COMMANDS=1 \
    -I ../tests/host/stubs -o fuzz_cmd fuzz_cmd.cpp
./fuzz_cmd --iters 3000000 --seed 7
```

## Reproduce the formal results

```bash
cd ../formal && ./run_tlc.sh     # checks AlarmFSM and Isolation with TLC
```

## Headline numbers (from the committed run)

- 6{,}000 campaign trials; attacker-caused disarms: 0; safety-invariant violations: 0.
- Baseline is attacker-armed in 2{,}500/2{,}500 flooded trials; hardened in 0.
- With authentication a legitimate command succeeds in 3{,}000/3{,}000 trials at every attack
  rate up to 20{,}000 msg/s; baseline loses it in every flooded trial.
- Fuzzer: 3{,}000{,}000 iterations, 0 memory errors, 0 accepted inputs.
- TLC: AlarmFSM 25 states, Isolation 660 states, all properties hold; both mutation-tested.

## Not included (the open step)

Physical sensor-to-siren latency under on-chip radio stress. Apparatus and protocol are in
`hardware/`; it requires two ESP32 boards, a logic probe and an authorized isolated RF
environment. The paper reports it as future work and does not claim a number.
