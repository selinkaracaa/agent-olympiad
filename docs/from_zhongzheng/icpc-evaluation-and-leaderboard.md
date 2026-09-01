# ICPC Evaluation and Leaderboard (2026-08-26)

> Author: Zhongzheng  
> Scope: `agent-team-features-main` — programming contests (ICPC pilot)  
> Last updated: 2026-08-26

## Summary of changes (Aug 26)

ICPC problems now materialize **`ao.icpc-package/v1`** bundles (same path as Codeforces) instead of relying only on flat Kattis `.in/.ans` folders.

**Code touched:**

- `src/problem_package_writer.py` — shared package materialization for ICPC and Codeforces
- `src/codeforces_adapter.py` — refactored to use the shared writer
- `collectors/fetch_icpc_samples.py` — writes `official_bundle_path` after sample collection
- `data/benchmarks/icpc/packages/icpc_wf_2012_bottles/` — first ICPC official bundle
- `tests/test_icpc_package_materialize.py` — package + judge integration tests

**Experiment result:** `Qwen/Qwen3.6-35B-A3B` · Tinker · `rules_mode=enforced` · **sample AC** · `results/icpc_tinker_qwen_8turns_v2/`

> **Repo note:** run ICPC experiments from **`agent-team-features-main`** only. Judging, rule cards, and batch runners live here.

---

## 1. TL;DR

ICPC evaluation is **three separate axes**, not one blended score:

| Axis | Question | Implementation | Status |
|------|----------|----------------|--------|
| **Task performance** | Is the code correct? What is the time penalty? | `programming_judge` + `env.grade_submission()` | Sample tests work |
| **Rule compliance** | Did the team violate contest rules? | `env.rule_violations` + rule-card enforcement | Partially enforced |
| **Collaboration quality** | Did the team coordinate well? | `evaluation/collaboration_score.py` (MultiAgentBench CS) | Optional LLM judge |

**Leaderboard** (`src/leaderboard.py`) is a **deterministic offline utility** for multi-team, multi-problem ICPC standings. It is **not** wired into the live agent simulation loop.

---

## 2. End-to-end pipeline

```text
data/benchmarks/icpc/benchmark.json
data/benchmarks/icpc/packages/{problem_id}/package.json
data/rules/icpc/evaluation.json
        │
        ▼
OlympiadEnvironment(competition_id="icpc", problem_id=...)
        │
        ├─► load rule card (team size, tools, penalties, prompts)
        │
        ▼
run_collaboration(schema, env, query_fn)     ← centralized / round_table / …
        │
        ├─► submit_code   → programming_judge (sample scope only)
        ├─► submit_final  → grade_submission() → programming_judge
        │
        ▼
transcript JSON  +  competition_batch.json
        │
        ├─► analyze_runs.py          (experiment analysis)
        └─► leaderboard.py icpc      (offline standings, needs submission log)
```

Entry point for a single-problem live run:

```bash
export TINKER_API_KEY=...
python src/run_competition_batch.py \
  --live --provider tinker \
  --competitions icpc --problem-id icpc_wf_2012_bottles \
  --max-turns 8 --schema centralized --rules-mode enforced \
  --no-judge-task --no-judge-collab \
  --output results/icpc_tinker_qwen_8turns_v2
```

`--no-judge-task` / `--no-judge-collab` skip Perplexity-backed post-hoc judges. Programming verdicts are produced inline by `programming_judge` during the run.

---

## 3. Data layer: benchmarks and test packages

### 3.1 Benchmark record

Each ICPC problem is listed in `data/benchmarks/icpc/benchmark.json`:

```json
{
  "problem_id": "icpc_wf_2012_bottles",
  "task_type": "algorithmic_programming",
  "kattis_id": "bottles",
  "evaluation": {
    "evaluator_id": "programming_judge",
    "status": "sample_tests_ready",
    "official_bundle_path": "data/benchmarks/icpc/packages/icpc_wf_2012_bottles",
    "sample_tests_path": "data/benchmarks/icpc/samples/icpc_wf_2012_bottles"
  }
}
```

`evaluator_id: programming_judge` tells the env and finalize layer to route submissions through the local OJ, not gold answers or LLM rubrics.

### 3.2 `ao.icpc-package/v1` layout

```
data/benchmarks/icpc/packages/icpc_wf_2012_bottles/
  package.json
  tests/sample/
    bottle-sample.in
    bottle-sample.ans
  tests/secret/          # optional; add manually for authorized hidden tests
```

`package.json` declares limits, checker mode, test groups (`sample` / `secret`), and subtasks.

### 3.3 Collection workflow

```bash
python collectors/fetch_icpc_samples.py --problem icpc_wf_2012_bottles
```

This script:

1. Downloads Kattis `samples.zip` (or reuses existing flat samples)
2. Writes `data/benchmarks/icpc/samples/{problem_id}/`
3. Calls `materialize_package_from_directory()` via `src/problem_package_writer.py`
4. Updates `benchmark.json` with `official_bundle_path`

Codeforces problems use the same package schema via `src/codeforces_adapter.py`, which now delegates to the shared writer.

---

## 4. Simulation layer: env and actions

### 4.1 Rule card

`data/rules/icpc/` provides:

- `competition.json` — team size (3), duration, allowed languages, workstation rules
- `collaboration.json` — agent constraints, roles, pending-run policy (prompt-level)
- `evaluation.json` — scoring contract and reporting guidance (**not shown to agents**)

With `--rules-mode enforced`, the env enforces tool allowlists, submission authority, communication budgets, and private notes.

### 4.2 Programming-specific actions

| Action | When | Test scope | Finalizes? |
|--------|------|------------|------------|
| `submit_code` | During contest | `sample` only | No |
| `submit_final` | End of attempt | `secret` if present, else `sample` | Yes |

`submit_code` feedback is returned as JSON (verdict, per-case results, penalty state). Under enforced ICPC rules it is **team-visible** and recorded in `code_submissions`.

### 4.3 Wrong-submission penalty

ICPC uses a 20-minute penalty per penalized rejection (WA, TLE, RE, etc.). The simulator models this by **burning contest clock**:

```python
# env.record_wrong_submission()
simulated_minutes += 20
current_turn += ceil(20 / minutes_per_turn)
```

Compilation Error (CE) is **not** penalized, matching official ICPC rules.

---

## 5. Programming judge

### 5.1 Entry point

`src/evaluation/programming_judge.py` → `judge_programming_submission()`:

1. Resolve `official_bundle_path` from the benchmark record (preferred)
2. Fall back to flat samples or Kattis download if no bundle exists
3. Extract source from markdown code fences (default `python3`, also `cpp17`)
4. Call `judge.run_submission(package, source, language, test_scope)`

### 5.2 Execution backends

| Language | Backend | Isolation |
|----------|---------|-----------|
| Python 3 | `NativePythonRunner` | Host CPython (trusted smoke) |
| C++17 | `DockerProgrammingJudge` | Docker: `--network none`, `--read-only`, `--cap-drop ALL`, … |

### 5.3 Checkers and verdicts

`src/judge/checkers.py` supports `exact`, `token` (default), `float`, and `custom`.

Verdicts: `AC`, `WA`, `TLE`, `RE`, `MLE`, `OLE`, `CE`, `JUDGE_ERROR`.

Secret test details are redacted in returned case objects (generic messages only).

### 5.4 Grade dict written to transcript

After `submit_final`, `env.grade_submission()` returns:

```json
{
  "evaluator_id": "programming_judge",
  "verdict": "AC",
  "test_scope": "sample",
  "grading_scope_label": "sample-only",
  "method": "programming_sample_judge",
  "cases": [...],
  "penalty_minutes": 0,
  "simulated_minutes": 20.0,
  "icpc_time_score": 20,
  "clock_burned_by_wa": false
}
```

`icpc_time_score` equals `simulated_minutes` at first AC (including any prior WA burns).

---

## 6. Post-run scoring and collaboration axis

### 6.1 Inline grading (default for ICPC)

`collaboration._result()` calls `env.grade_submission()` at the end of every run. No extra step is required for programming verdicts.

### 6.2 `apply_registered_judge` (optional)

`src/evaluation/finalize.py` can re-run registered judges after the collaboration loop. For ICPC this is redundant when `programming_judge` already graded inline. It matters more for `rubric_llm_v1` and `slide_deck_v1`.

### 6.3 Coordination score (CS)

`src/evaluation/collaboration_score.py` implements MultiAgentBench-style:

- **Cscore** (communication, 0–5)
- **Pscore** (planning, 1–5)
- **CS** = mean(C, P)

Enabled with `--judge-collab` (requires `PERPLEXITY_API_KEY`). Solo baselines naturally get Cscore = 0.

---

## 7. Leaderboard (`src/leaderboard.py`)

Leaderboard utilities are **pure functions** with a thin CLI. They do not run inside the agent loop.

### 7.1 ICPC standings: `compute_icpc_standings()`

Input: chronological submission records:

```json
[
  {"team": "alpha", "problem": "A", "minute": 10, "verdict": "WA"},
  {"team": "alpha", "problem": "A", "minute": 30, "verdict": "AC"}
]
```

Algorithm (official ICPC rules):

1. Count wrong attempts only **before** first AC per problem
2. Ignore submissions after AC on that problem
3. Penalty per solved problem = `AC_minute + 20 × wrong_before_ac`
4. Rank by: **solved ↓ → total penalty ↑ → last AC time ↑**

CLI:

```bash
python src/leaderboard.py icpc submissions.json standings.json
```

**Gap:** a single `run_competition_batch` cell produces one transcript for one problem. Building a full packet standings table requires aggregating `{team, problem, minute, verdict}` rows from multiple runs into a submissions JSON file first.

### 7.2 LiveOIBench pipeline (same module, different contest family)

Three stages for informatics olympiad-style contests:

| Stage | Function | Role |
|-------|----------|------|
| 1 | `select_best_solutions()` | Oracle best-of-N per problem |
| 2 | `aggregate_contest_scores()` | Sum scores within one contest |
| 3 | `build_global_table()` | Normalized cross-contest ranking |

Also includes `human_percentile()`, `medal_from_cutoffs()`, and `codeforces_equivalent_rating()` for human baseline comparison.

### 7.3 Run analysis: `analyze_runs.py`

Reads `competition_batch.json` or transcripts and writes `analysis.json` with normalized task scores, solo-vs-team decompositions, team metrics, and error taxonomy. This is experiment analysis, not a live scoreboard.

---

## 8. Evaluation contract vs implementation

From `data/rules/icpc/evaluation.json`:

| Requirement | Status |
|-------------|--------|
| `programming_judge` for source submissions | **Implemented** (sample scope) |
| Rank by solved count, then penalty | **`compute_icpc_standings()`** implemented; single-run records `icpc_time_score` |
| 20-minute penalty per penalized rejection | **`record_wrong_submission()`** implemented |
| CE not penalized | **Implemented** |
| Secret / official hidden tests | **Deferred** — only Kattis public samples unless `tests/secret/` is mounted manually |
| One-turn pending verdict wait | **Documented, not enforced** in runtime |
| Live scoreboard during contest | **Not implemented** |
| Multi-problem packet standings auto-aggregation | **Manual** — feed submission log to `leaderboard.py` |
| Collaboration quality (CS) | **Optional** — off by default in ICPC runs |
| Rule violations (pending assume, resubmit while pending) | **Partial** — tool/submit authority enforced; pending policy not tracked |

---

## 9. Live experiment: `icpc_tinker_qwen_8turns_v2`

| Field | Value |
|-------|-------|
| Model | `Qwen/Qwen3.6-35B-A3B` (Tinker) |
| Schema | `centralized`, `rules_mode=enforced` |
| Budget | 8 turns; used **4** |
| Submitted by | Agent_3 |
| Verdict | **AC** on `bottle-sample` (1/1) |
| `grade_score` | `0/0` — new package sets `sample` subtask points to 0; only `secret` subtask carries official weight |
| `icpc_time_score` | 20 min |
| Penalty / violations | 0 / none recorded |
| Path | `results/icpc_tinker_qwen_8turns_v2/` |

**Trace notes:**

- Turn 1: Agent_1 delegated and drafted full solution in `speak`
- Turns 2–3: Agent_2 / Agent_3 confirmed logic
- Turn 4: Agent_3 `submit_final` with raw Python (no intermediate `submit_code`)
- Judging used `official_bundle_path` (Path A package)
- No collaboration score (`--no-judge-collab`)

Earlier run `icpc_tinker_qwen_8turns/` (pre-package refactor) showed `grade_score 1.0/1.0` because the legacy flat-sample adapter assigned 1 point to the sample subtask.

---

## 10. Key files (quick reference)

| File | Role |
|------|------|
| `src/env.py` | `submit_code`, `grade_submission`, penalty clock |
| `src/evaluation/programming_judge.py` | Benchmark → judge adapter |
| `src/judge/core.py` | Package orchestration, verdict aggregation |
| `src/judge/runners.py` | Python native + C++ Docker backends |
| `src/problem_package_writer.py` | Shared `ao.icpc-package/v1` writer |
| `collectors/fetch_icpc_samples.py` | Kattis samples + package materialization |
| `src/leaderboard.py` | ICPC standings + LiveOIBench ranking |
| `src/run_competition_batch.py` | Batch runner, transcript output |
| `data/rules/icpc/evaluation.json` | Evaluation contract (human-facing spec) |

---

## 11. Known limitations and next steps

1. **Sample-only judging** — sample AC does not imply hidden-test AC; mount `tests/secret/` for authorized reproduction.
2. **Score display** — with `sample_points=0.0`, batch summary shows `0/0` even on AC; consider reporting `verdict` prominently or assigning informational sample points for demos.
3. **Pending-run enforcement** — rule card describes one-turn wait; env returns verdicts immediately on `submit_code`.
4. **Leaderboard wiring** — add a post-batch step to extract submission rows from transcripts and call `compute_icpc_standings()`.
5. **Multi-problem ICPC packets** — current pilot is single-problem (`icpc_wf_2012_bottles`); packet-level simulation and standings remain future work.

---

## 12. One-sentence summary for slides

> ICPC is modeled as a **rule-constrained multi-agent simulation** plus a **local `ao.icpc-package/v1` judge** plus an **optional MultiAgentBench collaboration score**; per-problem verdicts are automatic at run end, while official multi-team standings are computed offline by `leaderboard.compute_icpc_standings()`.
