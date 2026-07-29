# Agent pipeline (`src/`)

Multi-agent olympiad simulator: load a real team problem, run agents under competition rules, compare coordination schemas, and grade the result.

```
benchmark JSON  →  env.py  →  collaboration.py  →  actions.py
                      ↑              ↑
                   llm.py      run_exam.py / main.py
```

## Quick start

```bash
# Offline smoke test (no API key)
python3 src/main.py

# Live run on ARML Local 2009, all three schemas
export PERPLEXITY_API_KEY="..."
python3 src/run_exam.py --all-schemas
```

Results land in [`../results/`](../results/). See [`../results/ARML_LOCAL_2009.md`](../results/ARML_LOCAL_2009.md) for the first evaluation write-up.

---

## `env.py` — environment, tool gatekeeper, grading

**What it is:** The shared “exam room” every agent team works inside. One class (`OlympiadEnvironment`) handles all competitions; rules come from config, not hardcoded logic.

**How you use it:**

```python
env = OlympiadEnvironment(competition_id="arml_local", problem_id="arml_local_2009")
env.execute_action("Agent_1", "speak", "I'll take problem 3.")
env.grade_submission()
```

**Key pieces:**

| Piece | Purpose |
|-------|---------|
| `TEAM_SIZE_MATRIX` | Default team size per competition (ARML Local = 6, ICPC = 3, …). Overridden if `team_size` is set on the problem in benchmark JSON. |
| `COMPETITION_TOOL_REGISTRY` | Which tools each contest allows. ARML = paper only (`[]`); ICPC/IIOT = `execute_code`; Purple Comet = `use_calculator`. |
| `chat_history` | Full team discussion — every `speak` action appends here. All schemas read this. |
| `workspace` | Shared `scratchpad` (working notes) and `final_answer` (official submission). |
| `action_log` | Audit trail of every action, turn number, and env response. Saved in experiment JSONs. |
| `max_turns` | Hard cap (default 50) to prevent runaway loops. |

**Tool gatekeeper:** Before any tool runs, `validate_action()` checks whether that action is allowed for this competition. If an agent tries `use_calculator` on ARML, the env returns a rule violation — it does not silently run the tool.

**Implemented tools:**
- `use_calculator` — safe AST evaluator (basic arithmetic only)
- `execute_code` — runs `python3 -c <payload>` with a 5s timeout
- `web_search`, `read_lab_equipment`, `read_star_chart` — stubs for v1

**Grading (`grade_submission()`):**
1. If a gold `expected_answer` exists → normalized substring match (coarse, good for smoke tests)
2. If task is programming (ICPC/IIOT) → flags `judge_sandbox_required`
3. Otherwise → flags `llm_judge_required` (used by `run_exam.py` for partial credit)

Problems load from `data/benchmarks/{competition_id}/benchmark.json`.

---

## `actions.py` — agent action protocol

**What it is:** The bridge between raw LLM text and env actions. Agents don't call Python functions directly — they output text, and this module parses and executes it.

**Two response formats:**

1. **Plain text** → treated as `speak` (broadcast to team)
2. **Structured:**
   ```
   ACTION: write_scratchpad | PAYLOAD: Problem 3 answer: 946/27
   ACTION: speak | PAYLOAD: I agree with Agent_2 on P3.
   ```

**Key functions:**

| Function | Role |
|----------|------|
| `build_action_instructions()` | Injected into every agent system prompt — tells the model what actions exist and which tools are allowed. |
| `parse_agent_response()` | Regex parser; supports multi-line `PAYLOAD` (important for full answer sheets). |
| `apply_agent_response()` | Parses + calls `env.execute_action()` for each action. Stops early if `submit_final` succeeds. |
| `submitters` kwarg | In centralized schema, only `Group_Leader` may submit; other agents' `submit_final` gets redirected to scratchpad. |

**Design choice:** Plain-text fallback keeps the protocol forgiving — agents can discuss naturally without always using `ACTION:` syntax. Structured actions are used when agents need to update scratchpad, run code, or submit.

---

## `collaboration.py` — three coordination schemas + synthesis

**What it is:** Defines *how* agents talk to each other, on top of the same env. Swap schema → same problem, same model, different team structure.

**Entry point:**

```python
from collaboration import run_collaboration, CollabConfig

result = run_collaboration("round_table", env, query_llm_fn, CollabConfig(rounds=2))
```

### Schema A — Round Table (`run_round_table`)

- All agents see the full chat history.
- Strict turn order: Agent_1 → Agent_2 → … → Agent_N, repeated for `config.rounds`.
- After discussion, **Agent_1 synthesizes** the final numbered answer sheet.

Best for: peer debate, self-assignment of sub-problems, cross-checking (what we saw on ARML 2009).

### Schema B — Centralized (`run_centralized`)

- **Group_Leader** plans first: assigns sub-tasks to Agent_2 … Agent_N.
- Workers solve their slice (cannot `submit_final` — redirected to scratchpad).
- Leader synthesizes and submits the official answer.

Best for: fewer turns, clearer division of labor (scored 20/40 on ARML with only 7 turns).

### Schema C — Decentralized (`run_decentralized`)

- No leader. Agents coordinate by updating scratchpad and speaking directly.
- Runs `config.decentralized_events` rounds of all agents acting.
- **Agent_1 synthesizes** at the end.

Best for: modeling flat teams with no designated coordinator.

### Synthesis phase (`_run_synthesis`)

Separate from discussion. After all rounds, one agent is prompted to write the **complete** numbered answer sheet (1. through 10. for team rounds). Features:

- Dedicated system prompt: output plain text only, no `ACTION:` lines
- Retries up to 2× if fewer than 5 numbered parts detected
- Prefers full response text over truncated `ACTION: submit_final` payloads (this fix took scores from 4/40 → 17–20/40)

**`CollabConfig`:** `rounds`, `decentralized_events`, `synthesize` (bool), `progress` (callback for logging).

---

## `run_exam.py` — batch runner + LLM judge

**What it is:** End-to-end experiment script. Runs one or more schemas on a real problem with live LLMs, scores with an LLM judge, saves full traces.

```bash
python3 src/run_exam.py --all-schemas              # round_table + centralized + decentralized
python3 src/run_exam.py --schema centralized --rounds 3
python3 src/run_exam.py --problem arml_local_2010
```

**Defaults:** ARML Local 2009, 2 rounds, agents = `openai/gpt-5.4-mini`, judge = `anthropic/claude-sonnet-4-6` (both via Perplexity).

**What each run produces** (`results/{problem_id}_{schema}_{timestamp}.json`):

- Final answer, submission metadata, auto-grade from env
- Full `chat_history` and `action_log`
- `judge_feedback` — per-problem partial credit (e.g. `TOTAL: 20/40`)
- Model names, round count, numbered-parts count

**Why an LLM judge?** Team rounds have 10 sub-problems with partial credit. Env gold matching is binary substring check — too coarse. The judge compares each numbered answer to the official solution and awards 0–4 points per problem.

---

## `main.py` — quick diagnostics

**What it is:** Fast sanity check that the whole stack works. No real exam, no saved results.

```bash
python3 src/main.py          # mock LLM, no API key
python3 src/main.py --live   # real Perplexity calls
```

**What it tests:**

1. Load ARML problem + metadata
2. Tool gatekeeper (calculator blocked on ARML, code allowed on ICPC)
3. Submission validation (reject too-short answers)
4. All three schemas with 1 round each (mock or live)
5. Error handling (`ProblemNotFoundError`)

Use this after changing env, actions, or collaboration logic — before spending API credits on `run_exam.py`.

---

## `llm.py` — LLM callers

- `mock_agent_llm` — deterministic responses for offline tests
- `make_perplexity_caller(model=...)` — live Perplexity Agent API
- `resolve_query_fn(use_mock=True/False)` — picks mock vs live

All collaboration code takes a `query_llm_fn(system, user) -> str` callback, so the orchestration layer stays model-agnostic.

---

## Data flow (one agent turn)

```
1. collaboration.py builds system + user prompt
      (problem, chat history, scratchpad, schema rules, action instructions)
2. query_llm_fn() returns raw text
3. actions.py parses → list of (action_type, payload)
4. env.execute_action() runs each action, updates state
5. Repeat until rounds done → synthesis → grade
```
