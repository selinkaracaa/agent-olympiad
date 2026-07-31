# Initial experiments (archived)

Early **multi-agent** smoke tests on IOL, IOAA, ARML Power, IJSO (and later
presentation-style pilots). Solo / single-agent IEO open-question experiments
were removed.

## Contents

| Path | What |
|------|------|
| `src/run.py` | Multi-agent pipeline (Perplexity Agent API) |
| `src/score_teamwork.py` | Teamwork scorer on saved discussion logs |
| `docs/STATUS.md` | Experiment results (smoke tests, gold batch, GPT runs) |
| `docs/FORMAT.md` | Per-olympiad format and scoring notes from that phase |
| `results/` | Multi-agent run outputs (`gold-batch-2025-06-19/`, `iol-gpt55/`, …) |

## Re-run (optional)

From repo root:

```bash
export PERPLEXITY_API_KEY="pplx-..."
python3 initial_experiments/src/run.py agent:openai/gpt-5.4-mini --olympiad iol_team --smoke --limit 1
```

Benchmark problems live in `data/benchmarks/` at the repo root.
