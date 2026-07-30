# Experiment results

Outputs from `src/run.py`. New runs default to `results/multiagent_*.json` at this level.

## Grouped runs

| Folder | Agents | Rounds | Judge | Olympiads |
|--------|--------|--------|-------|-----------|
| `gold-batch-2025-06-19/` | GPT-5.4-mini | 2 | Claude Sonnet 4.6 | IOL, IOAA, ARML, IJSO |
| `iol-gpt55/` | GPT-5.5 | 3 | GPT-5.5 | IOL Team |
| `iol-gpt54-mini-2r/` | GPT-5.4-mini | 2 | GPT-5.4-mini | IOL Team (smoke) |

Each olympiad subfolder contains `answer.json` (full logs) and `answer.md` (readable summary).

## Other

- `summaries/` — cross-run score tables for multi-agent runs
- `logs/` — run logs (gitignored)

Solo / single-agent IEO open-question results were deleted.
