# Agent Olympiad — Multi-Agent Team Benchmark

Benchmark **multi-agent AI teams** on olympiad-style **team tasks**. Part of the **Agent Olympiad** research project at DAPLab.

**Current focus:** collecting and documenting team-competition data (PDFs + extracted benchmarks).

## Documentation

| Doc | Contents |
|-----|----------|
| [`docs/DATA_COLLECTION.md`](docs/DATA_COLLECTION.md) | Canonical tracker — 20 source-collected competitions + 33 external benchmark datasets |
| [`data/benchmarks/index.json`](data/benchmarks/index.json) | Unified mixed-unit catalog (32 session tracks + 5 question/challenge tracks); each row also points at `data/base` |
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

## Programming leaderboards

`src/leaderboard.py` provides deterministic ICPC standings and the
LiveOIBench three-stage ranking pipeline (explicit oracle best-of-8 selection,
contest-local score totals, then normalized global aggregation). Human
baselines are read only from local JSON/CSV files under
`data/human_baselines/`; missing data is reported rather than downloaded.
Run `python src/leaderboard.py --help` for the JSON/CSV commands.

`src/liveoibench_adapter.py` exports `<model>_code.json`, validates a locally
mounted LiveOIBench problem tree, and imports local contestant JSON (or parquet
when pandas/pyarrow is installed). It has no network behavior and never runs
LiveOIBench's host judge or setup/evaluation scripts:

```bash
python src/liveoibench_adapter.py export --input candidates.json --model my_model --output predictions/
python src/liveoibench_adapter.py import-problem --problem-dir /mounted/IOI/2024/contest/task --output package-summary.json
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
