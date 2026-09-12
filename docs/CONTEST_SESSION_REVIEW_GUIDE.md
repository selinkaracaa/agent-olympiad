# Contest-session unification review guide

## 1. Executive summary

This branch uses the canonical contest-session engine as the primary implementation and treats the legacy runtime as a compatibility layer rather than as the source of truth.

The key outcome is a unified benchmark runtime in which:

- canonical action definitions live in `src/tool_registry.py`
- typed and legacy invocation parsing live in `src/action_wire.py`
- contest state, budgets, answer versions, and task scheduling live in `src/contest_session.py`
- runner orchestration lives in `src/contest_runner.py`
- policy, competition bundles, and rule-card rules are handled in `src/contest_policy.py`, `src/contest_actions.py`, and `src/contest_rules.py`
- older local files like `src/env.py`, `src/actions.py`, and `src/collaboration.py` remain only where compatibility or benchmark-specific adapters are still required

This is the architecture to preserve for the benchmark: one canonical action vocabulary, one schema, one session engine, and a compatibility boundary for older spellings.

## 2. Source-of-truth mapping

| Area | Authoritative implementation | Notes |
|---|---|---|
| Canonical action registry | `src/tool_registry.py` | Single registry and action-set versioning |
| Action parsing and alias normalization | `src/action_wire.py` | Handles typed JSON actions and legacy text names |
| Session state and task ledger | `src/contest_session.py` | Tracks task states, submissions, reviews, and budgets |
| Run orchestration | `src/contest_runner.py` | Builds the session, resolves legal actions, executes a run |
| Action execution and policy checks | `src/contest_actions.py`, `src/contest_policy.py` | Main execution and gate logic |
| Rule-card support | `src/contest_rules.py`, `src/rulecard_policy.py` | Card-driven constraints and role permissions |
| Legacy compatibility runtime | `src/env.py` | Kept for older per-problem compatibility paths |
| Prompt generation | `src/actions.py` | Uses registry-backed specs to render agent instructions |
| Board and workspace compatibility | `src/workboard.py` | Work-item semantics used by legacy runtime |
| Budget conversion | `src/contest_budget.py` | Turn and token accounting for contest sessions |

## 3. Unified format families

The benchmark is organized around a small set of format families, each defining how the team coordinates and how agent actions are surfaced.

### 3.1 Single-agent

- One solver acts as the entire team.
- Team size is effectively pinned to one.
- Best for baseline comparison when the question is whether communication or coordination itself helps.
- Usually the simplest configuration for debugging action validation and tool routing.

### 3.2 Decentralized

- No centralized leader.
- Agents coordinate through the shared contest state and public event log.
- Supports open-table problem selection and peer interaction.
- This is the default open-table comparison for non-leader baselines.

### 3.3 Centralized

- One agent acts as the leader or orchestrator.
- The leader may have higher submission authority and can assign or re-prioritize work.
- Worker agents do not necessarily see the same submission or high-level assignment privileges.
- Useful for measuring whether recentering agency improves performance in structured tasks.

### 3.4 Round-table

- Agents act in sequence with shared history.
- The team sees a common public state and rotates through the active seat sequence.
- This is the standard collaborative baseline when a team needs explicit turn taking without a formal leader.

### 3.5 Open-table coach

- A coach is present only in the precontest or opening phase.
- The coach may shape the team brief or initial framing without participating as a solver.
- Controlled by the rule-card or baseline configuration.
- Useful when benchmarking “structured guidance with no direct solving burden.”

## 4. Action families and tools

The registry exposes one canonical action set and then dynamically resolves which actions are legal per runtime, competition, task type, and rule-card state.

### 4.1 Common contest actions

| Action | Purpose | Visibility |
|---|---|---|
| `select_problem` | Switch or claim the active task | contest |
| `inspect_problem` | Read problem history and current state | private |
| `triage_problem` | Prioritize or re-sort the problem queue | contest |
| `work` | Record durable draft or answer | team |
| `speak` | Public broadcast to the team | team |
| `direct_message` | Private message to specific teammates | private |
| `remember` | Store private note | private |
| `recall` | Search notes and shared memory | private |
| `share_note` | Publish a note to the team | team |
| `request_review` | Ask for review without approving | team |
| `review_answer` | Approve or reject a version | team |
| `submit` | Submit a non-programming answer | team |
| `skip_problem` | Release or abandon the current task | contest |
| `rest` | Pass the turn without action | private |
| `finish_contest` | End a contest when gates permit | contest |

### 4.2 Tool packs

The benchmark identifies bundled tool capabilities per task type and competition.

| Pack | Typical actions |
|---|---|
| Math | `use_calculator` |
| Programming | `execute_code`, `submit_code` |
| Research | `web_search` |
| Resources | `read_lab_equipment`, `read_star_chart` |

Tool visibility is still controlled by competition allowlists, rule cards, and runtime gating. An action may be registered without being visible in a given run.

### 4.3 Competition-specific action gating

- ICPC and programming-heavy competitions primarily surface programming tools.
- Math-oriented competitions surface calculators and math tasks.
- Research-heavy competitions can expose web research or lab/resource tools.
- Board-style and non-programming competitions keep a lightweight action surface centered on work, review, memory, and messages.

## 5. What to review on the branch

The branch to inspect is `unify-contest-engine`.

The important files to read are:

- `README.md` — top-level project overview and current benchmark framing
- `docs/contest-systems.md` — baseline and format-family contract
- `docs/from_zhongzheng/actions-reference.md` — canonical action surface and rules
- `src/tool_registry.py` — source of truth for the action registry
- `src/action_wire.py` — invocation normalization and compatibility mapping
- `src/contest_session.py` — contest state and task lifecycle
- `src/contest_runner.py` — run orchestration and session startup
- `src/contest_actions.py` and `src/contest_policy.py` — execution and gating logic
- `src/env.py` and `src/actions.py` — compatibility layers only, not the canonical source

If someone is reviewing the branch for correctness, this is the order to read: README → contest-systems → actions reference → registry → session engine → runner → compatibility adapter files.

## 6. How to run experiments by format

The project should be benchmarked by choosing a format family, then modifying only the controls that matter for that family.

### 8.1 Single-agent experiments

```bash
PYTHONPATH=src python3 src/run_competition_batch.py \
  --live \
  --schema single_agent \
  --competitions icpc \
  --max-turns 10 \
  --limit 1
```

Use this to isolate the performance of one solver without coordination costs.

### 8.2 Decentralized experiments

```bash
PYTHONPATH=src python3 src/run_competition_batch.py \
  --live \
  --schema decentralized \
  --competitions arml_local \
  --max-turns 10 \
  --limit 1
```

Use this for open-table coordination without a designated leader.

### 8.3 Centralized experiments

```bash
PYTHONPATH=src python3 src/run_competition_batch.py \
  --live \
  --schema centralized \
  --competitions icpc \
  --max-turns 10 \
  --limit 1
```

Use this to measure whether leader-driven routing and authority improve results versus open coordination.

### 8.4 Round-table experiments

```bash
PYTHONPATH=src python3 src/run_competition_batch.py \
  --live \
  --schema round_table \
  --competitions arml_power \
  --max-turns 10 \
  --limit 1
```

Use this when the team should rotate through shared history and task context without a formal leader or coach.

### 8.5 Open-table coach experiments

```bash
PYTHONPATH=src python3 src/run_competition_batch.py \
  --live \
  --schema open_table_coach \
  --rules-mode enforced \
  --competitions icpc \
  --max-turns 10 \
  --limit 1
```

Use this when the benchmark should include guidance at the beginning while keeping the actual contest task solving by the team.

### 8.6 Deliberation experiments

```bash
PYTHONPATH=src python3 src/run_competition_batch.py \
  --live \
  --schema decentralized \
  --rules-mode enforced \
  --competitions ioaa_group \
  --max-turns 12 \
  --limit 1
```

Use this when the benchmark explicitly tests challenge, evidence, and structured revision behavior.

### 8.7 Memory-focused experiments

- Use the same format family as the comparison baseline.
- Change only the memory settings or the presence of note-sharing and recall actions.
- Compare against the same format without memory to isolate the value of durable recall.

### 8.8 Best-practice experiment protocol

For each format family, the comparison should hold constant:

- same competition or manifest
- same model provider and model version
- same token budget and turn limit
- same rules mode
- same output directory or run metadata
- same task set and evaluation rubric

Only the format family and the feature toggles under test should differ.

## 7. Verification evidence

Validated with the focused regression suite:

```bash
cd /Users/selinkaraca/Desktop/agent_olympiad_econ && PYTHONPATH=src:tests python3 -m unittest tests.test_tool_registry tests.test_typed_actions tests.test_scoped_actions tests.test_contest_session tests.test_contest_runner
```

Result:

- 80 tests ran
- all passed
- exit status was successful

This confirms that the canonical contest-session engine and its typed registry remain consistent while the format-family and compatibility layers are layered on top.

