---
license: other
task_categories:
  - text-generation
  - question-answering
language:
  - en
tags:
  - multi-agent
  - olympiad
  - team-competition
  - benchmark
pretty_name: Agent Olympiad Benchmarks
size_categories:
  - 1K<n<10K
---

# Agent Olympiad — Processed Team Competition Benchmarks

Extracted multi-agent team competition problems for the **Agent Olympiad** research project (DAPLab).

## Contents

- Per-competition folders with `benchmark.json` (primary eval set)
- Catalog: `index.json` — each olympiad lists `benchmark_path` (extracted JSON)
  and `base_path` (ALE-style inputs under `data/base/tasks/<id>/`)

The catalog is intentionally mixed-unit. Tracks without an explicit `eval_unit`
are session-level by default (one full published team task per row). Tracks
marked `eval_unit: "question"` contain independently evaluated questions,
puzzles, or challenges. Their row counts must not be interpreted as numbers of
full contest sessions.

Each problem typically includes:

- `problem_id`, `competition`, `year`, `task_type`, `team_size`
- `problem_description`
- `gold_label` (`expected_answer` and/or `grading_rubric` when available)
- source metadata (`source_url`, `source_file`, `solution_file`)

Subsampled question-level tracks (for example Science Bowl, QANTA, Cybench)
retain only the promoted `benchmark.json`; full pre-subsample inventories are
not kept in-tree. Raw source packets, where available, remain under `data/raw/`.

## Intended use

Benchmarking **multi-agent AI teams** on olympiad-style team tasks (paper contests, programming, debate, mystery hunt, science bowl, etc.).

## Notes

- Source materials remain subject to their original competition licenses/terms.
- This dataset is for research evaluation; do not redistribute restricted contest materials beyond the terms of the original sources.
