# Supplementary material

Nothing is copied into this directory. Everything the paper rests on already lives in this
repository, at the paths below, and duplicating it here would create a second copy that goes
stale the moment anything changes — which is exactly the defect this revision cycle removed
from `paper/` (see commit `31576ec`).

If the publisher requires a self-contained supplementary archive, build it from these paths at
submission time and record the commit hash alongside it.

---

## Experimental results

| Path | Contents |
|---|---|
| `experiments/results/summary.json`, `summary.md` | E1/E2 adversarial campaign, 6,000 trials |
| `experiments/results/ablation.jsonl` | E3, **raw per-trial records**, 3,600 rows in 12 modes |
| `experiments/results/ablation_summary.json`, `.md` | E3 aggregate, derived from the above |
| `experiments/results/fuzz.json` | E4, 3,000,000 iterations |
| `experiments/results/sensitivity.jsonl` | E5, 180 grid cells |
| `experiments/results/broker_acl.jsonl`, `broker_acl_summary.md` | E6, 8 scenarios against a live Mosquitto 2.0.18 |
| `experiments/corpus/corpus.json`, `commit_shas.tsv` | 135 commit-pinned projects and the selection criteria |
| `experiments/corpus/findings.json` | rule results: 0 hits for rule 1, 18 flagged by rule 2 |
| `experiments/corpus/manual_validation.json` | per-project verdicts, 9 confirmed / 9 false positive, and the bias analysis |

Every count in the manuscript's trial-accounting table resolves to one of these files.

## Formal verification

| Path | Contents |
|---|---|
| `formal/AlarmFSM.tla`, `AlarmFSM.cfg` | state machine specification, 25 distinct states |
| `formal/AlarmFSM_unsafe.cfg` | the defective configuration TLC **must** report a violation for |
| `formal/Isolation.tla`, `Isolation.cfg` | isolation model, 660 distinct states, no fairness on the network task |
| `formal/run_tlc.sh` | runs all three; fails if the third one passes |

## Firmware

| Path | Contents |
|---|---|
| `firmware/smart_home/smart_home.ino` | v2.2.0, the unmodified artefact under test |
| `firmware/smart_home/secrets.example.h` | **demo keys are public**; the build refuses `AUTH_COMMANDS=1` with them |
| `tests/host/` | 129 host tests, including the three negative build-guard checks |

## Analysis scripts

| Path | Purpose |
|---|---|
| `experiments/analyse.py`, `analyse_ablation.py` | aggregation and statistics, standard library only |
| `experiments/test_harness.py` | metamorphic and differential properties of the harness itself |
| `experiments/test_conformance.py` | 19,529 trace transitions against the TLA+ relation, with a negative control |
| `experiments/corpus/test_rule.py` | 8 controls for the static rule |
| `experiments/check_figure_type.py` | printed point size of every figure label |
| `experiments/check_figure_fit.py` | clipped or overflowing labels, measured in the real font |
| `experiments/validate_figures.py` | every plotted value, recomputed from the raw records |
| `experiments/hardware/analyse_hw.py` | the pre-registered Mann–Whitney *U* analysis, **awaiting data** |

## Reproducibility

| Path | Contents |
|---|---|
| `REPRODUCTION.md` | the canonical guide: three evidence levels, software reproduction in about an hour, and the full hardware procedure |
| `.github/workflows/ci.yml` | every check above, run on each push |
| `docs/HARDWARE_VALIDATION_PLAN.md` | what conditions A–D require, and what is blocking |

## What is not here, and will not be

- **Attack tooling.** Deliberately not published. `experiments/hardware/README.md` covers
  instrumentation and measurement only.
- **Physical measurements.** None exist. See `docs/HARDWARE_VALIDATION_PLAN.md`.
- **Real credentials or keys.** The repository ships demo keys that are public by design, and
  the firmware refuses to build an authenticated configuration that uses them.
