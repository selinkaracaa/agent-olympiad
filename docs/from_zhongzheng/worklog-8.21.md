# Work log — How Rule Cards Are Injected into Agents (2026-08-21)

> Author: Zhongzheng  
> Scope: shared design across `agent-team-features-main` / `agent-olympiad`  
> Last updated: 2026-08-26

## Summary of changes (Open Table + Coach, Aug 21–26)

New collaboration baseline **`open_table_coach`**: a Coach prepares the team before the contest, joins one opening discussion turn, then exits; remaining turns are contestant-only round-table.

| Stage | Where | What |
|-------|-------|------|
| **Prototype** (Aug 21) | `agent-olympiad/` | Cursor session [Open Table + Coach baseline](e4ac37bc-1f71-4b8f-8b24-6e05381c9fcb): `run_open_table_coach()`, action allowlists, runner wiring; Coach policy **hardcoded in Python** |
| **Production + experiment** (Aug 25–26) | **`agent-team-features-main`** (this repo) | Port + `_open_table_coach_policy()` reading `collaboration.json` → `simulation.open_table_coach`; ARML Local 2009 Tinker run → **§12** |

**Code touched (this repo):**

- `src/collaboration.py` — three-stage state machine, Coach prompts, rule-card policy loader
- `src/actions.py` — `allowed_actions` allowlist (Coach blocked from tools / submit)
- `src/run_phase_a.py`, `run_phase_b_matrix.py`, `run_competition_batch.py` — schema registration and Coach roster
- `src/evaluation/collaboration_score.py`, `src/llm.py` — scorer labels and mock Coach responses
- `data/rules/arml_local/collaboration.json` — Coach policy config (`rules_mode=enforced`)
- `tests/test_open_table_coach.py` — 6 focused tests

**Experiment result (§12):** `Qwen/Qwen3.6-35B-A3B` · Tinker · `rules_mode=enforced` · **35.6 / 40** · `results/open_table_coach_arml_local_2009_tinker.json/`

> **Repo note:** run all Coach experiments from **`agent-team-features-main`** only. The `agent-olympiad/` copy is an earlier prototype without rule-card enforcement.

---

## 1. TL;DR

A rule card is: 

1. A **human-curated rule package** loaded from `data/rules/{competition_id}/` by `competition_id`;
2. Attached to `env.rule_card` when `OlympiadEnvironment` initializes;
3. Used to drive both **runtime hard constraints** (tools, team size, communication budget, etc.) and **prompt text injection** (telling agents what the rules are);
4. Filtered through `agent_view()` to **hide** grading fields such as `scoring` and `evaluation_guidance`.

To run the bench, you only need `competition_id` + `problem_id`; no per-dataset-schema adapter is required.

---

## 2. End-to-end pipeline

```text
data/rules/{competition_id}/*.json
        │
        ▼
load_rule_card(competition_id)          ← env init; not chosen by the agent
        │
        ├─► configure runtime (tools, team size, communication budget, deliberation…)
        │
        └─► agent_view() filters visible fields
                │
                ├─► collaboration.py::_system_prompt()   (generic collaboration runner)
```

Entry point:

```python
env = OlympiadEnvironment(competition_id, problem_id, rules_mode="enforced")
```

- `competition_id` → selects the rule card (`data/rules/`)
- `problem_id` → selects the problem (`data/benchmarks/{competition_id}/benchmark.json`)

These are separate; there is no design where one rule card adapts to all datasets.

---

## 3. Where rules come from: storage and loading

### 3.1 File layout

One directory per competition, three component files (or a single flat JSON):

| File | Contents |
|------|----------|
| `competition.json` | profile, protocol, team, execution, resources, human_constraints, rules_text, allowed_tools |
| `collaboration.json` | agent_constraints, agent_roles, information_policy, rule_sections, deliberation, communication, simulation |
| `evaluation.json` | evaluation_guidance, scoring, submission (**not injected into agent prompts**) |

Code locations:

- `src/rules/storage.py` — merges the three JSON files
- `src/rules/loader.py` — `load_rule_card(competition_id)`
- `src/rules/models.py` — `RuleCard` dataclass

### 3.2 When loading happens

**agent-olympiad:**

```python
# src/env.py
self.rule_card = load_rule_card(competition_id)
```

**agent-team-features-main (this repo):**

```python
# src/env.py
self.rules_baseline = RulesBaseline.resolve(competition_id, mode=rules_mode, ...)
self.rule_card = self.rules_baseline.card
```

This repo adds a three-level `rules_mode` (`src/rules/baseline.py`):

| Mode | Behavior |
|------|----------|
| `off` | no rule card; legacy registry defaults |
| `prompt_only` | rules go into the prompt; runtime does not enforce |
| `enforced` | prompt + runtime dual enforcement (communication budget, tool allowlist, structured deliberation, etc.) |

Transcript metadata records `rules_mode`, `rule_card_content_hash`, `rule_capabilities`, etc., for reproducibility.

---

## 4. Two-layer injection: runtime config + prompt text

### 4.1 Layer A: environment hard constraints (not relying on prompt compliance)

Rule card fields → env behavior:

| Field | Effect |
|-------|--------|
| `allowed_tools` | actions available to agents (`enforced` mode filters unknown tools) |
| `team.active_*` | team size bounds |
| `simulation.max_turns` | turn budget |
| `communication` | message quota (`CommunicationBudget`) |
| `deliberation.mode` | whether structured debate actions are enabled |
| `agent_roles` | role names, duties, who may submit |

Under `enforced` mode, violating actions are blocked by the env and logged in `rule_violations`.

### 4.2 Layer B: prompt injection (telling agents “what the rules are”)

Core filter `agent_view()` (`src/rules/views.py`):

```python
def agent_view(card, *, team_size=None) -> dict:
    """Contestant-visible: official input + collaboration method."""
    return {
        "rules_text": card.rules_text,
        "human_constraints": list(card.human_constraints),
        "agent_constraints": list(card.agent_constraints),
        "allowed_tools": list(card.allowed_tools),
        "agent_roles": [...],
        # excludes scoring / evaluation_guidance
    }
```

`grader_view()` includes the full evaluation configuration.

---

## 5. Generic collaboration runner prompt assembly

Code: `src/collaboration.py` → `_system_prompt()` + `_agent_user_prompt()`

### 5.1 System prompt structure (ICPC Agent_2 example, ~13k characters)

```text
① Identity
   You are Agent_2, title: contestant.
   Runtime tools: ['query_rules', 'execute_code']

② Rule summary
   Competition rule profile: proxy (human_team_shared_workstation_programming).
   {full rules_text prose}

③ CONTESTANT-VISIBLE COMPETITION RULES
   {human_constraints as bullets}
   {describe_resources(resources)}

④ COLLABORATION AND RESOURCE RULES
   {agent_constraints as bullets}
   Declared tools: [...]
   Communication policy: {...}
   Deliberation policy: {...}

⑤ YOUR ROLE DUTIES
   {assigned.duties}
   May submit final answer: yes/no

⑥ Action interface (build_action_instructions)
   ACTION: speak | PAYLOAD: ...
   - submit_code (for programming tasks)
   - query_rules / execute_code
```

JSON field → prompt location mapping:

| JSON field | File | Prompt location |
|------------|------|-----------------|
| `resources` | competition.json | `describe_resources()` sentence |
| `rules_text` | competition.json | rule summary section |
| `human_constraints` | competition.json | CONTESTANT-VISIBLE COMPETITION RULES |
| `agent_constraints` | collaboration.json | COLLABORATION AND RESOURCE RULES |
| `agent_roles[].duties` | collaboration.json | YOUR ROLE DUTIES |
| `allowed_tools` | competition.json | Runtime tools + action list |
| `rule_sections` | collaboration.json | **not in generic path** (see §7) |
| `scoring` | evaluation.json | **hidden** |

### 5.2 User prompt template (standard turn)

```text
=== SCHEMA ===
{schema_note}

=== PROBLEM ===
{full problem statement}

=== TEAM DISCUSSION ===
{chat_history}

=== SHARED SCRATCHPAD ===
{scratchpad}

=== YOUR PRIVATE NOTES ===
{private_notes}

=== YOUR TURN ===
Turn budget / API budget / Communication budget
{extra}
```

**Rules are given once in the system prompt**; the user prompt repeats the problem + dynamic state each turn and does not repeat the full rule card.

### 5.3 Optional: `query_rules` action

If the rule card includes `query_rules` in `allowed_tools`, agents can query JSON at runtime (`env.query_rules()`). This is on-demand lookup, not the primary injection path.

---

## 6. Prompt trace: ICPC + Centralized schema

Example: `icpc_wf_2012_bottles` + `run_centralized()` (default schema in `run_competition_batch.py`).

### 6.1 Call chain

```text
run_centralized()
  │
  ├─ Turn 1: Group_Leader plans
  │     system = _system_prompt(env, "Group_Leader")
  │     user   = problem + "Assign sub-tasks to Agent_2 .. Agent_3"
  │     → speak broadcasts plan into chat_history
  │
  └─ Turn 2+: Agent_2 / Agent_3 ... execute
        system = _system_prompt(env, "Agent_2")
        user   = _agent_user_prompt(..., extra=Leader's plan)
        submitters=∅  (workers cannot submit)
        │
        └─ then Group_Leader synthesis → submit_final
```

Turn 1 **does not** use `_agent_user_prompt()`; the user message is only the problem + assignment instructions—no discussion history / scratchpad / budget block.

### 6.2 Key values after ICPC initialization

| Field | Value | Source |
|-------|-------|--------|
| `allowed_tools` | `["query_rules", "execute_code"]` | competition.json |
| `team_size` | 3 | benchmark |
| `max_turns` | 60 | collaboration.json → simulation.max_turns |
| `communication.mode` | unlimited | collaboration.json |
| `deliberation.mode` | unstructured | no propose/challenge actions injected |

### 6.3 Known quirk: Group_Leader vs ICPC rule card

Centralized uses `"Group_Leader"` as leader, but the ICPC rule card only defines `Agent_1/2/3`:

```python
# collaboration.py::_role_lookup fallback
AgentRole(agent_name, agent_name, (), False)
```

On Turn 1, Group_Leader sees:

- `title: Group_Leader` (not the rule card’s `contestant`)
- `YOUR ROLE DUTIES: (none listed)`
- `May submit final answer: no`

But synthesis still assigns `Group_Leader` to submit → **schema-layer roles misalign with rule-card roles**.

**Recommendation:** for ICPC team collaboration, use `round_table` or `icpcrun`, not centralized.

---

## 7. Three prompt injection paths compared

### 7.1 Round Table (equal three-person team; closer to ICPC)

- Each turn: `Agent_1 → Agent_2 → Agent_3` in rotation
- All agents use `Agent_*` roles from the rule card
- system / user templates as in §5
- synthesis defaults to `Agent_1` submitting

### 7.2 Open Table + Coach (second-pass rule injection)

Code: `run_open_table_coach()` + `_open_table_coach_policy()`

This repo’s Coach flow is stricter than agent-olympiad:

- Turn 1 (precontest): Coach **cannot see the problem**; user prompt contains full `agent_view()` JSON
- Turn 2 (opening): Coach joins opening discussion, then exits
- Turn 3+: contestant-only; `extra` carries rule JSON

Triple injection: system prompt summary + full user JSON + optional `query_rules`.

Reference transcript: `results/open_table_coach_arml_local_2009_tinker.json/transcripts/arml_local__arml_local_2009__open_table_coach__enforced.json`

**Naming note:** the new function is `run_open_table_coach()` (schema name `"open_table_coach"`). There is **no** separate `run_open_table()`.  
“Open table” means shared-history collaboration (already implemented by `run_round_table()`); the Coach baseline adds a three-stage Coach flow on top.

#### 7.2.1 Implementation changelog (2026-08-21)

Prototype drafted in `agent-olympiad/` (Cursor session, [Open Table + Coach baseline](e4ac37bc-1f71-4b8f-8b24-6e05381c9fcb)); Coach turns and action allowlists were **hardcoded in Python**, with no rule-card policy loader.

**This repo** (`agent-team-features-main`) ported that prototype, added rule-card-driven `_open_table_coach_policy()`, and **ran the ARML Local 2009 experiment here** (§12). Results: `results/open_table_coach_arml_local_2009_tinker.json/`. Do not run Coach experiments from `agent-olympiad/`.

**Three-stage state machine (`run_open_table_coach()`)**

```text
Turn 1  precontest brief    Coach sees agent_view rules only; no problem access
Turn 2  opening discussion  All contestants speak in turn → Coach summarizes → exits
Turn 3+ contestant-only     Agent_* round-table only; synthesis submits
```

All stages share the turn / API / token ledger from `_budgeted_query()`; Coach is not a free resource.

**New files**

| File | Contents |
|------|----------|
| `tests/test_open_table_coach.py` | 6 focused tests (~130 lines) |
| `data/rules/arml_local/collaboration.json` → `simulation.open_table_coach` | Coach policy config (enabled, turn, allowed_actions, advice_scope, etc.) |

**Additions in `src/collaboration.py`**

| Symbol | Responsibility |
|--------|----------------|
| `SchemaName` includes `"open_table_coach"` | type + `SCHEMAS` registration |
| `_open_table_coach_policy(env)` | load and validate Coach policy from rule card (this repo only; requires `rules_mode=enforced`) |
| `_coach_system_prompt(env, phase, policy)` | Coach-specific system prompt (precontest / opening) |
| `_precontest_coach_prompt(env, policy)` | Turn 1 user prompt (full `agent_view()` JSON, no problem) |
| `run_open_table_coach()` | three-stage main loop (~130 lines) |

**Changes in `src/collaboration.py`**

- `_run_agent_once()` gains optional `allowed_actions` and `system_prompt` (Coach overrides prompt / restricts actions)

**Changes in `src/actions.py`**

- `apply_agent_response()` gains `allowed_actions: Optional[set[str]]`
- if an action is not in the allowlist → force `sleep` and log `blocked prohibited action`

Coach calls pass `allowed_actions={"speak", "sleep"}`, blocking `execute_code`, `submit_final`, etc. at the code layer.

**Runner / scoring / mock integration**

| File | Change |
|------|--------|
| `src/run_phase_a.py` | add `"open_table_coach"` to `DEFAULT_SCHEMAS` |
| `src/run_phase_b_matrix.py` | `agent_roster()` returns `[Agent_1..N, Coach]`; hetero mode reuses `Agent_1`’s model for Coach |
| `src/run_competition_batch.py` | `_agent_names()` appends `"Coach"` for open_table_coach |
| `src/evaluation/collaboration_score.py` | `format_agent_profiles()` labels Coach as pre-contest/opening coordinator who cannot submit |
| `src/llm.py` | `mock_agent_llm` adds two deterministic Coach responses (precontest / opening) |

**Rule card config (`data/rules/arml_local/collaboration.json`)**

```json
"simulation": {
  "open_table_coach": {
    "enabled": true,
    "status": "counterfactual_synthetic_baseline_not_official_arml_rule",
    "may_submit": false,
    "allowed_tools": [],
    "counts_toward_shared_api_and_token_budget": true,
    "precontest_brief": { "turn": 1, "problem_access": false, "allowed_actions": ["speak", "sleep"], ... },
    "opening_discussion": { "turn": 2, "problem_access": true, "allowed_actions": ["speak", "sleep"], ... },
    "after_opening_access": false
  }
}
```

**Test coverage (`tests/test_open_table_coach.py`)**

1. Turn 1 has no problem leakage; Coach appears only on turns 1–2  
2. Coach attempts `execute_code` / `submit_final` → blocked as `sleep`  
3. Pre-contest brief counts toward shared API budget  
4. Final synthesis submitted by `Agent_1` (not Coach)  
5. Result metadata includes `coach_policy_status`, `coach_problem_access`  
6. roster / hetero models / scorer correctly identify Coach role  

**Differences between the two repos**

| Dimension | `agent-olympiad` initial version | `agent-team-features-main` (this repo) |
|-----------|-----------------------------------|----------------------------------------|
| Rule source | `load_rule_card()` + metadata fallback | requires enforced rule card + `_open_table_coach_policy()` |
| Coach policy | hardcoded in Python | read from `collaboration.json` → `simulation.open_table_coach` |
| Submitter | fixed `Agent_1` | determined by `may_submit` on rule-card roster |
| Result metadata | none | `coach_policy_status`, `coach_exit_after_turn`, etc. |

**How to run**

```powershell
# Phase A smoke
python src/run_phase_a.py --schemas open_table_coach

# Phase B matrix (requires enforced)
python src/run_phase_b_matrix.py --schemas open_table_coach --rules-mode enforced

# Single-problem batch
python src/run_competition_batch.py --competition arml_local --problem arml_local_2009 --schema open_table_coach
```

### 7.3 ICPC-specific runner (`icpcrun.py`)

Does not use generic `_system_prompt`; uses `RuleSession`:

- system = full `CONTEST RULE PACKET` (all `rule_sections`)
- action interface = JSON objects (not `ACTION: ... | PAYLOAD: ...`)
- **no** `query_rules` tool
- extra enforcement: workstation lease, memory_publish, structured debate

Docs: `agent-olympiad/docs/ICPCRUN_ON_DEMAND_RULES_SUMMARY.md`

---

## 8. Per-turn data flow summary

```text
data/rules/{competition_id}/*.json
        │
        ├─ runtime constraints ──→ env.allowed_tools, team_size, max_turns, communication
        │
        └─ agent_view() filter
                │
                ▼
        _system_prompt()  ──→ large fixed block (ICPC ~13k chars)
                │              sent every agent every turn; content nearly unchanged
                │
        _agent_user_prompt() ──→ dynamic: problem + discussion + scratchpad + budget + extra
                │
                ▼
              LLM call
                │
                ▼
        apply_agent_response() ──→ env.execute_action(speak/tool/submit...)
```

---

## 9. Implications for bench design

1. **Competition-first, not dataset-first**  
   Change `competition_id` to swap the entire rule card; pick `problem_id` from the matching `benchmark.json`.

2. **Generic runner uses “summary injection”**  
   `rules_text` + constraint lists go into the system prompt; full `rule_sections` are only packed wholesale in icpcrun.

3. **Wrong schema changes role semantics**  
   Centralized’s Group_Leader does not match ICPC’s equal-contestant design.

4. **Prompt size is mostly constraints**  
   ICPC single-agent system prompt ~13k characters, repeated every turn. If cost-sensitive, consider:
   - only `rules_text` summary + `query_rules` tool (already allowed in ICPC competition.json);
   - or icpcrun’s one-shot full packet + no repeated queries.

5. **`rules_mode` controls enforcement depth**  
   - `prompt_only`: ablation for rule text alone  
   - `enforced`: communication budget, tool allowlist, structured deliberation, etc. at runtime  
   transcripts should always record `rules_mode` and `rule_card_content_hash`.

6. **`contest_rules.py` is a gap tracker, not an injection layer**  
   Human-maintained audit of “official rules vs what the env encodes”; does not participate in prompts.

---

## 10. Key code index

| Module | Path | Responsibility |
|--------|------|----------------|
| Rule loading | `src/rules/loader.py` | `load_rule_card(competition_id)` |
| Rule storage | `src/rules/storage.py` | three-file merge |
| Visibility filter | `src/rules/views.py` | `agent_view()` / `grader_view()` |
| Rules mode | `src/rules/baseline.py` | `RulesBaseline.resolve()` |
| Environment | `src/env.py` | init, runtime enforce, `query_rules()` |
| Prompt assembly | `src/collaboration.py` | `_system_prompt()`, `_agent_user_prompt()` |
| Open Table + Coach | `src/collaboration.py` | `run_open_table_coach()`, `_open_table_coach_policy()` |
| Coach action allowlist | `src/actions.py` | `apply_agent_response(allowed_actions=...)` |
| Coach tests | `tests/test_open_table_coach.py` | three stages, permissions, budget, roster |
| Coach rule card | `data/rules/arml_local/collaboration.json` | `simulation.open_table_coach` |
| ICPC runner | `src/icpcrun.py` | `RuleSession`, `_render_contest_rules()` |
| Action instructions | `src/actions.py` | `build_action_instructions()` |
| Resource description | `src/rules/describe.py` | `describe_resources()` |

---

## 11. Follow-ups (optional)

- [ ] Standardize ICPC bench on `round_table` or `icpcrun` to avoid centralized role mismatch
- [ ] Evaluate “slim rule injection”: `rules_text` + `query_rules` only vs full constraints
- [ ] Log system prompt character counts / token estimates per competition for cost analysis
- [ ] Compare `prompt_only` vs `enforced` impact on coordination score (Phase B matrix)

---

## 12. Qwen3.6-35B · ARML Local 2009 · open_table_coach (2026-08-26)

`Qwen/Qwen3.6-35B-A3B` · Tinker · `rules_mode=enforced` · `results/open_table_coach_arml_local_2009_tinker.json/`

### Task score (/40)

| | open_table_coach |
|---|---:|
| **qwen** | **35.6** |

### Coordination score CS (0–5)

| | open_table_coach |
|---|---:|
| **qwen** | — (`judge_collab` not run) |

### Effort used (turns / API calls)

| qwen · open_table_coach | Turns | API | Note |
|---|---:|---:|---|
| | 5/8 | 26 | Q4 wrong; 24 speaks blocked over 1200-char limit |
