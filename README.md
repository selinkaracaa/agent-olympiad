# Agent Olympiad — Multi-Agent Team Benchmark

Benchmark **multi-agent AI teams** on olympiad-style **team tasks**. Part of the **Agent Olympiad** research project at DAPLab.

**Current focus:** collecting and documenting team-competition data (PDFs + extracted benchmarks).

## Documentation

| Doc | Contents |
|-----|----------|
| [`docs/DATA_COLLECTION.md`](docs/DATA_COLLECTION.md) | What we collected — summary table + format per contest |
| [`docs/EVALUATION.md`](docs/EVALUATION.md) | PDF-first artifact evaluators, human calibration, and readiness |
| [`data/benchmarks/index.json`](data/benchmarks/index.json) | Olympiad catalog and collection status |
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

## Programming leaderboards

`src/leaderboard.py` provides deterministic ICPC standings and the
LiveOIBench three-stage ranking pipeline: explicit oracle best-of-8 selection,
contest-local score totals, then normalized global aggregation. Human
baselines are read only from local JSON/CSV files; missing data is reported
rather than downloaded.

`src/liveoibench_adapter.py` exports code predictions, validates a locally
mounted LiveOIBench problem tree, and imports local contestant data. It has no
network behavior and never runs LiveOIBench host-judge or setup scripts.

## Rule-aware baseline

Competition runs accept `--rules-mode off|prompt_only|enforced` (default:
`off`). `off` preserves the current-main collaboration and tool behavior.
`prompt_only` loads a canonical card from `data/rules/` and gives contestants
the public competition, resource, collaboration, roster, and role-duty rules
without enforcing them. `enforced` additionally applies card communication
budgets, submission authority, tool allowlists, private notes, and structured
deliberation invariants.

Use `--rules-root PATH` to select another canonical card root and
`--rules-strict` to raise a typed resolution error when a competition has no
card. Without strict mode, such runs return `rules_baseline_unavailable`; no
fallback card is fabricated. Run summaries and transcripts record card
coverage, schema/rule identifiers, a deterministic SHA-256 content hash, and
the status of each baseline capability. Analysis groups include `rules_mode`,
so baseline conditions are never pooled.

## Refresh benchmarks from PDFs

```bash
pip install -r requirements.txt
python3 collectors/iol_team.py
python3 collectors/arml_power.py
# … see collectors/ for each competition
```

## Olympiads tracked

See [`docs/DATA_COLLECTION.md`](docs/DATA_COLLECTION.md) for counts. **20 competition types** across mathematics, physics, science, linguistics, economics, informatics, international law, and humanities.
