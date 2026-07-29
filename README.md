# Agent Olympiad — Multi-Agent Team Benchmark

Benchmark **multi-agent AI teams** on olympiad-style **team tasks**. Part of the **Agent Olympiad** research project at DAPLab.

**Current focus:** collecting and documenting team-competition data (PDFs + extracted benchmarks).

## Documentation

| Doc | Contents |
|-----|----------|
| [`docs/DATA_COLLECTION.md`](docs/DATA_COLLECTION.md) | Canonical tracker — 20 source-collected competitions + 33 external benchmark datasets |
| [`data/benchmarks/index.json`](data/benchmarks/index.json) | Primary session catalog (main) |
| [`data/benchmarks/index_new.json`](data/benchmarks/index_new.json) | Expanded primary session tracks (index.json + promotions) |
| [`data/benchmarks/index_aux.json`](data/benchmarks/index_aux.json) | Auxiliary question corpora (辅集) |
| [`initial_experiments/`](initial_experiments/) | Archived smoke tests and early multi-agent runs |

## Repository structure

```
├── docs/
│   └── DATA_COLLECTION.md       # Living data tracker
├── data/
│   ├── raw/                     # Source PDFs (committed to git)
│   │   ├── iol/, ioaa/, arml/, ijso/
│   │   ├── arml_national/, arml_local/
│   │   └── business_case/
│   └── benchmarks/              # Extracted problem JSON per competition
├── collectors/                  # PDF → benchmark.json scripts (run locally)
└── initial_experiments/         # Archived experiment code + results
    ├── src/run.py
    ├── docs/STATUS.md
    └── results/
```

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
