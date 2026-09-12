# Software design

Map of how contests, agents, and graders fit together.

## Data flow

```
data/raw/{contest}/*.pdf
        │
        ▼ collectors/*.py
data/benchmarks/{contest}/benchmark.json   ← problem text, team_size, gold, evaluation.*
        │
        ▼ OlympiadEnvironment (env.py)
 shared chat + scratchpad + tools + turn/API budgets
        │
        ▼ collaboration.py (3 schemas)
 agents call LLM ≤1× per turn (or rest)
        │
        ▼ actions.py → action_wire.normalize_invocation → env.execute_action
 speak / work / board & desk actions / tools / submit   (tool_registry.ACTION_REGISTRY)
        │
        ▼ evaluate_submission.py (or env.grade_submission)
 gold_answer_v1 | rubric_llm_v1 | slide_deck_v1 | programming_judge (deferred)
```

## Budgets (time / API / tokens)

Three knobs, all optional except the turn clock, which follows the official
contest duration:

| Budget | Meaning | Default |
|---|---|---|
| `max_turns` | Contest clock — one turn = `minutes_per_turn` (5 min) of official time | `duration / 5 min`, clamped to **[1, 90]** (ARML 1h → 12, ICPC 5h → 60, MCM 99h at 60 min/turn → 90) |
| `max_api_calls` | Total LLM calls (discussion + synthesis) | unlimited |
| `max_output_tokens_per_call` | Cap one agent’s output in a single call | unlimited (ICPC/IIOT: **4096** placeholder) |
| `max_total_tokens` | Team-wide output token cap for the run | unlimited |

Registry: `src/contest_budget.py` → `COMPETITION_BUDGET_REGISTRY`. Override at run time via `CollabConfig` or `run_exam.py` flags.

```bash
python3 src/run_exam.py --rounds 50 --max-output-tokens-per-call 4096
python3 src/run_exam.py --competition icpc --problem icpc_wf_2012_bottles  # uses ICPC cap from registry
```

## Key modules under `src/`

| File | Role |
|---|---|
| `tool_registry.py` | Single registry of all 31 canonical actions (`ACTION_SET_VERSION = 5`), runtime tags, legacy-name aliases; shared with the contest-session runtime |
| `action_wire.py` | Turns typed dicts or `a \| b \| c` text payloads into one canonical `Invocation` |
| `env.py` | Contest rules, tools, shared state, **turn budget** (time) + **API budget** (cost); handler table keyed by canonical action |
| `actions.py` | Parse `ACTION: … \| PAYLOAD: …` (accepts `rest`/`sleep`, `submit`/`submit_final`, …); prompt text rendered from the registry |
| `collaboration.py` | Round table / centralized / decentralized loops |
| `llm.py` | Perplexity (and OpenAI) callers |
| `run_exam.py` | Live multi-schema runs + LLM judge |
| `evaluate_submission.py` | Unified grader entry |
| `artifacts/pdf_ingest.py` | PDF → text and/or page images |
| `run_smoke_batch.py` | One sample per contest family (all 20) |

**Turn rules:** each eligible agent gets at most one LLM call per turn, or chooses `rest` (legacy `sleep`). Optional `--max-api-calls N`. Synthesis counts toward the API budget.

```bash
python3 src/main.py
python3 src/run_smoke_batch.py --rounds 1
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_exam.py --all-schemas --rounds 2
```

## Adding a new contest

1. Put PDFs under `data/raw/<your_contest>/`.
2. Add/extend a collector → `data/benchmarks/<your_contest>/benchmark.json`.
3. Register in `env.py`:
   - `TEAM_SIZE_MATRIX["your_contest"] = N`
   - `COMPETITION_TOOL_REGISTRY["your_contest"] = [...]` (e.g. `["execute_code"]`)
4. Set `evaluation.evaluator_id` via `collectors/enrich_evaluation_metadata.py` or by hand.
5. Run with `OlympiadEnvironment("your_contest", "problem_id")` + `run_collaboration(...)`.

## Collaboration baselines (keep all three)

- **Round table** — full history, strict order within each turn.
- **Centralized** — leader plans on turn 1; workers act on later turns; leader submits.
- **Decentralized** — no leader; peers coordinate via chat/scratchpad.

More baselines later (e.g. “discuss more then execute”) are welcome; these three stay.

## Eval notes

- Short math sheets → curated gold (`gold_answer_v1`).
- Writing / proofs / slides → LLM rubric.
- ICPC/IIOT → need an online/sandbox judge (Codeforces-style submit→verdict); not done yet.
- Lab practicals → report proxy only; environment-agent sim is lower priority.
