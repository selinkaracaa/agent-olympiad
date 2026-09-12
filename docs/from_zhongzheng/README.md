# Agent Olympiad current documentation

This directory is the maintained entry point for understanding and running the
current benchmark. The source of truth is the code under `src/`; these documents
describe protocol `contest_session_v6` and action set version 5.

## Start here

1. [Contest-session pipeline](current-status-20260910.md) — current
   implementation: settings, baselines, turn loop, actions, tools, and how
   memory is stored and injected into agents.
2. [Pipeline overview](pipeline-overview-20260910.md) — what the repository
   implements, architecture, data flow, baselines, judging, metrics, and outputs.
3. [Benchmark runbook](benchmark-runbook.md) — installation, manifests, single
   runs, matched baselines, structured-gold batches, ICPC/VJudge, resume, and
   troubleshooting.
4. [Actions reference](actions-reference.md) — all typed actions, arguments,
   visibility, capability packs, baseline surfaces, and runtime gates.
5. [Contest systems](../contest-systems.md) — the detailed v6 OTC and baseline
   contract.
6. [Run identity and reuse](../contest-run-reuse.md) — fingerprints, checkpoint
   compatibility, and safe resume behavior.

## What is current

- Current runtime: contest-session engine (`src/contest_engine.py`).
- Current CLI: `src/run_competition_batch.py --contest-manifest ...`.
- Current baselines: `single_agent`, `decentralized`, `centralized`, and `otc`.
- Current OTC: rule-card-driven v6, selected with `--system-variant otc`.
- Canonical action registry: `src/tool_registry.py`.
- Canonical experiment outputs: fresh directories containing `run_config.json`,
  `contest_checkpoint.json`, and `contest_session.json`.

Old spellings are accepted only as aliases:

- `vanilla` / `vanilla_team` → `decentralized`
- `strategic` / `strategic_team` / `open_table_coach` /
  `open_table_coach_memory` → `otc`

Do not use the legacy per-problem `--schema` path for new contest-session
experiments.

## Historical material

The `archive/` directory contains dated experiment reports, implementation
plans, weekly summaries, and retired protocol descriptions. They remain useful
for provenance but do not define current behavior. When an archived document
conflicts with the current pipeline, overview, runbook, action reference, or source code,
the current source code wins.
