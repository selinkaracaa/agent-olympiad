---
license: other
task_categories:
  - other
tags:
  - agent
  - multi-agent
  - olympiad
  - benchmark
  - evaluation
pretty_name: Agent Olympiad
size_categories:
  - 1K<n<10K
---

# Agent Olympiad — Data

Benchmark materials for **multi-agent AI teams** on olympiad-style team tasks (Agent Olympiad / DAPLab).

## Layout

| Path | Role |
|------|------|
| `base/` | ALE-style agent task inputs (`tasks/<competition>/<id>/base/{input,software}`) + `task_cards.json` |
| `benchmarks/` | Extracted problem JSON / unified catalog |
| `raw/` | Source PDFs and upstream checkouts |
| `rubrics/` | Scoring rubrics |
| `evaluators/` | Evaluator assets |
| `viz/` | Summary figures + `summary.json` |

`base/` follows the [Agents Last Exam](https://huggingface.co/datasets/agents-last-exam/agents-last-exam-data) per-task layout.

## Stats (snapshot)

See `viz/summary.json` for the latest catalog counts (competitions, records, domains, scoring modes).

## Citation / provenance

Source-collected competition PDFs and external benchmark corpora; regenerate `base/` from `benchmarks/` via the Agent Olympiad collectors (`build_ale_base.py`).
