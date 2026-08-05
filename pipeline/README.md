# Dataset pipeline

Config-driven multi-agent competition runner. It loads benchmark questions, applies a
competition rule card, lets agents form a team and collaborate, scores the final answer, and
updates a simulated or read-only Codeforces leaderboard.

## Offline smoke test

```bash
python -m pipeline.run --competition iol_team --problems all --limit 1 --rounds 1 --mock
```

## OpenAI-compatible run

```bash
set OPENAI_API_KEY=...
set OPENAI_BASE_URL=https://your-provider.example/v1
python -m pipeline.run --competition iol_team --problems all \
  --provider openai --model your-model --judge-model your-judge --media both
```

`OPENAI_BASE_URL` is optional for the standard OpenAI endpoint. The default roster uses the
official `problem.team_size` (IOL = 4). A different `--team-size` is rejected unless
`--allow-noncomparable-team-size` is supplied; such results are marked non-comparable.

The runner attaches agent-visible source PDFs/page images according to `--media`. Solution
files and judge-only assets are never exposed to solving agents. Scoring follows each
problem's `evaluation.evaluator_id` through `data/evaluators/registry.json`; deferred or
unsupported evaluators fail closed instead of receiving a generic score.

Each run writes one full trace per problem and `summary.json` under `pipeline/results/<run_id>/`.
Codeforces integration is read-only:

```bash
python -m pipeline.run --competition iol_team --limit 1 --mock --codeforces-contest 2044
```

The pipeline never submits to Codeforces. Codeforces standings are shown as an external,
read-only reference only: raw contest points are not ranked against the pipeline's normalized
0–100 evaluator score.
