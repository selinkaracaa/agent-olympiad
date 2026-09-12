# Agent Olympiad — Multi-Agent Team Benchmark

Benchmark **multi-agent AI teams** on olympiad-style **team tasks**. Part of the **Agent Olympiad** research project at DAPLab.

**Current focus:** a manifest-driven contest-session benchmark with five selectable
baselines, rule-card Open Table Coach, typed actions, resumable runs, and
deterministic or remote judging.

## Documentation

| Doc | Contents |
|-----|----------|
| [Vallina OTC](docs/vallina-otc.md) | Basic Coach + rule-card baseline, isolated from full OTC enhancements |
| [OTC artifact pipeline](docs/otc-artifact-pipeline.md) | Shared OTC engine, reviewed PDF delivery, rubric grading, and per-competition readiness |
| [`docs/from_zhongzheng/README.md`](docs/from_zhongzheng/README.md) | Current documentation index |
| [`docs/from_zhongzheng/current-status-20260910.md`](docs/from_zhongzheng/current-status-20260910.md) | Current contest-session pipeline: settings, actions, tools, memory |
| [`docs/from_zhongzheng/pipeline-overview-20260910.md`](docs/from_zhongzheng/pipeline-overview-20260910.md) | End-to-end current architecture and benchmark pipeline |
| [`docs/from_zhongzheng/benchmark-runbook.md`](docs/from_zhongzheng/benchmark-runbook.md) | How to run single contests, matched baselines, gold batches, and ICPC |
| [`docs/from_zhongzheng/actions-reference.md`](docs/from_zhongzheng/actions-reference.md) | All current typed actions, packs, baseline surfaces, and gates |
| [`docs/contest-systems.md`](docs/contest-systems.md) | Current baseline and OTC v6 contract |
| [`docs/contest-run-reuse.md`](docs/contest-run-reuse.md) | Run fingerprints, checkpoint reuse, and resume safety |
| [`docs/BENCHMARK_DESIGN.md`](docs/BENCHMARK_DESIGN.md) | What the benchmark measures, contest realism, baselines, the CS / IHS metrics, limitations |
| [`docs/DATA_COLLECTION.md`](docs/DATA_COLLECTION.md) | What we collected — summary table + format per contest |
| [`docs/EVALUATION.md`](docs/EVALUATION.md) | PDF-first artifact evaluators, human calibration, and readiness |
| [`docs/WORKBOARD_AND_TOOLS.md`](docs/WORKBOARD_AND_TOOLS.md) | Per-item workboard and shared-workspace actions — reference and metrics |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | What changed — new actions, methods, and metrics |
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

## OTC and contest sessions

OTC is the sole current Open Table Coach implementation (protocol v6). Run it
with `--contest-manifest ... --system-variant otc`; old variant spellings are
aliases, not separate baselines. Legacy per-problem `--schema open_table_coach`
is removed. Use fresh output directories when migrating from older protocols.
See [contest systems](docs/contest-systems.md) for presets and matched budgets.

## Rule-aware baseline

For the contest-session path (`--contest-manifest`), see
[`docs/contest-run-reuse.md`](docs/contest-run-reuse.md#effective-contest-settings):
`prompt_only` loads the selected card into prompts, while `enforced` is supported
by the `otc` baseline only. The rules-mode description below covers the legacy
per-problem path.

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

### Tinker live ICPC run

Install dependencies, set `TINKER_API_KEY`, then run:

```bash
python src/run_competition_batch.py --live --provider tinker --model Qwen/Qwen3.6-35B-A3B --max-output-tokens 8192 --temperature 0.2 --competitions icpc --problem-id icpc_wf_2012_bottles --schema centralized --max-turns 2 --rules-mode enforced --no-judge-task --no-judge-collab --output results/icpc_tinker_qwen
```

This uses three agents because the enforced ICPC rule-card roster has three
members. The complete atomic transcript is written under
`results/icpc_tinker_qwen/transcripts/`; the batch summary and final result are
in `results/icpc_tinker_qwen/competition_batch.json`.

## Refresh benchmarks from PDFs

```bash
pip install -r requirements.txt
python3 collectors/iol_team.py
python3 collectors/arml_power.py
# … see collectors/ for each competition
```

## Olympiads tracked

See [`docs/DATA_COLLECTION.md`](docs/DATA_COLLECTION.md) for counts. **20 competition types** across mathematics, physics, science, linguistics, economics, informatics, international law, and humanities.
