# Software design (for Sean / integrators)

Short map of how contests, agents, and graders fit together.

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
 agents call LLM ≤1× per turn (or sleep)
        │
        ▼ actions.py → env.execute_action
 speak / scratchpad / tools / submit_final
        │
        ▼ evaluate_submission.py (or env.grade_submission)
 gold_answer_v1 | rubric_llm_v1 | slide_deck_v1 | programming_judge (deferred)
```

## Budgets (time / API / tokens)

Three knobs, all optional except the default **50-turn** clock:

| Budget | Meaning | Default |
|---|---|---|
| `max_turns` | Contest clock — one team time step per turn | **50** (all contests for now) |
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
| `env.py` | Contest rules, tools, shared state, **turn budget** (time) + **API budget** (cost) |
| `actions.py` | Parse `ACTION: … \| PAYLOAD: …` (includes `sleep`) |
| `collaboration.py` | Round table / centralized / decentralized loops |
| `llm.py` | Perplexity (and OpenAI) callers |
| `run_exam.py` | Live multi-schema runs + LLM judge |
| `evaluate_submission.py` | Unified grader entry |
| `artifacts/pdf_ingest.py` | PDF → text and/or page images |

## Budgets (Yusen 2026-08-05)

- **Turn** ≈ contest clock. Default trial size: `--rounds 50` (or smaller for smoke).
- **Per turn:** each eligible agent gets **at most one LLM call**, or chooses `sleep`.
- **API calls** ≈ money. Optional `--max-api-calls N`. Synthesis also counts.

```bash
# Offline sanity
python3 src/main.py

# Live baseline table (small model)
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_exam.py --all-schemas --rounds 2
# Later: --rounds 50 with a smaller agent model
```

## Adding Sean’s contest

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
