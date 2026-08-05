# Agent Olympiad — Multi-Agent Team Benchmark

Benchmark **multi-agent AI teams** on olympiad-style **team tasks**. Part of the **Agent Olympiad** research project at DAPLab.

**Current focus:** collecting and documenting team-competition data (PDFs + extracted benchmarks).

## Documentation

| Doc | Contents |
|-----|----------|
| [`docs/DATA_COLLECTION.md`](docs/DATA_COLLECTION.md) | Canonical tracker — 20 source-collected competitions + 33 external benchmark datasets |
| [`data/benchmarks/index.json`](data/benchmarks/index.json) | Unified mixed-unit catalog (32 session tracks + 5 question/challenge tracks) |
| [`initial_experiments/`](initial_experiments/) | Archived smoke tests and early multi-agent runs |

## Repository structure

```
├── docs/
│   └── DATA_COLLECTION.md       # Living data tracker
├── data/
│   ├── raw/                     # Source PDFs (committed to git)
│   ├── benchmarks/              # Extracted problem JSON per competition
│   └── base/                    # ALE-style agent inputs (generated)
│       └── tasks/<comp>/<id>/base/{input,software}
├── collectors/                  # PDF → benchmark.json (+ build_ale_base.py)
└── initial_experiments/         # Archived experiment code + results
```

`data/base/` follows the [Agents Last Exam](https://huggingface.co/datasets/agents-last-exam/agents-last-exam-data) per-task layout (`…/base/input`, optional `software/`). Regenerate with `python collectors/build_ale_base.py --clean`.

## Refresh benchmarks from PDFs

```bash
pip install -r requirements.txt
python3 collectors/iol_team.py
python3 collectors/arml_power.py
# … see collectors/ for each competition
```

## Olympiads tracked

See [`docs/DATA_COLLECTION.md`](docs/DATA_COLLECTION.md) for the unified catalog:
**20 source-collected competition types** plus **33 external benchmark
datasets** (17 rule-based, 16 rubric/open-ended). The inventories are reported
separately because they can overlap conceptually.
