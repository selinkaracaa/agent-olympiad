# Unified API and Action Contract

Status: repository contract for the unified contest-session engine.

This document defines the unified contest-session contract (`ACTION_SET_VERSION = 5`). It unifies the action vocabulary, collaboration schemas, rule-card configuration, tools, budgets, resource conditions, and run commands. The spreadsheet action vocabulary is the public vocabulary. Older runtime spellings are compatibility mappings only; they are not a second conceptual API.

## Source of truth

| Area | Source |
|---|---|
| Canonical action registry and legacy normalization | `src/env.py` |
| Action syntax and generated instructions | `src/actions.py` |
| Collaboration schemas and per-run budgets | `src/collaboration.py` |
| Contest budgets | `src/contest_budget.py` |
| Rule-card schema | `data/rules/schema.json` |
| Competition-specific versions, roles, resources, and conditions | `data/rules/<competition>/competition.json` |
| Workboard, claims, release, answers, and reviews | `src/workboard.py` |

Rule cards use schema version `1.0`. A rule card's `rule_id` identifies the source/version of that competition configuration. Use `rules_mode=enforced` when the rule card should control runtime behavior.

## Collaboration schemas

The spreadsheet's common/specific action table and the collaboration schema list are different dimensions. Actions describe what an agent does inside a run. Schemas describe how agents are organized for an experiment. Therefore `debate`, `self_consistency`, `memory_solo`, `subagent`, and `liveoi_best_of_8` do not belong in the common-action table, even though they are implemented run modes.

| Schema | Runtime meaning | Use when |
|---|---|---|
| `single_agent` | One logical solver with the team's budget-matched call allowance | Solo baseline |
| `centralized` | Leader coordinates, workers act, leader synthesizes/submits | Central coordinator experiment |
| `round_table` | Agents act in sequence with shared history | Standard team baseline |
| `decentralized` | Peers work independently and reconcile | No-leader comparison |
| `open_table_coach` | Coach gives a pre-contest brief and opening discussion, then exits | Enforced coach rule card only |
| `debate` | Independent proposers, challenge/revision rounds, and decision | Optional deliberation experiment; implemented in `run_debate` |
| `self_consistency` | Multiple isolated solo samples with per-part aggregation | Optional sampling experiment; implemented in `run_self_consistency` |
| `memory_solo` | Solo solver with bounded private memory | Optional memory experiment; implemented in `run_memory_solo` |
| `subagent` | Orchestrator delegates to isolated workers and aggregates returns | Optional delegation experiment; retained for division/cohesion analysis |
| `liveoi_best_of_8` | Eight isolated candidates, selected only when a judge is supplied | Optional research experiment; implemented in `run_liveoi_best_of_8` |

For `single_agent`, `solo_calls_per_turn` can match the team API budget. For ordinary team schemas, each eligible agent may make at most one model call per turn or sleep.

## Common actions

The names in the first column are the public workflow names from the registry and spreadsheet. New callers and generated prompts use only these names. The implementation normalizes them to existing handlers internally. Older spellings are accepted only for existing transcripts, tests, and callers; they are not public names.

| Public action | Internal handler | Payload / condition |
|---|---|---|
| `select_problem` | `claim_problem` | Board item id; requires a workboard |
| `assign_problem` | `claim_problem` | Board item id; requires a workboard |
| `inspect_problem` | `open_problem` | Board item id |
| `triage_problem` | `list_problems` | No payload |
| `direct_message` | `message_group` | `Agent_2,Agent_3 \| message` |
| `work` | `write_scratchpad` | Shared scratchpad text |
| `remember` | `remember` | Private note, optionally item-scoped |
| `recall` | `recall` | Search private/team-visible memory |
| `share_note` | `publish_memory` | Memory ids such as `M1, M2` |
| `request_review` | `verify_problem` | `<item> \| agree|disagree|unsure comment` |
| `review_answer` | `verify_problem` | Same payload; review may agree or disagree |
| `submit` | `submit_final` | Complete final answer; only authorized submitters |
| `finish_contest` | `submit_final` | Same as `submit` |
| `skip_problem` | `mark_hopeless` | Board item and reason |
| `rest` | `sleep` | Optional reason; passes the turn |
| `release_problem` | `release_problem` | Legacy board compatibility action; ordinary public workflow does not require release |

Core common actions are the spreadsheet actions above. The runtime also exposes optional infrastructure actions: `speak` (team broadcast), `check_budget` (budget/board report), `query_rules` (rule-card view), `write_private_notes` (enforced private notes), and `set_priority` (board priority). These are implementation support actions, not additional spreadsheet concepts.

Review policy is neutral: a reviewer may `agree`, `disagree`, or use `unsure`. There is no restriction requiring agreement. A review records evidence/comments and does not change the recorded answer by itself.

## Specific actions and tools

| Category | Canonical actions |
|---|---|
| Math / computation | `use_calculator` |
| Programming | `execute_code`, `submit_code` |
| Research | `web_search` |
| Resources | `read_lab_equipment`, `read_star_chart` |
| Deliberation | `propose`, `challenge`, `provide_evidence`, `revise`, `decide` |
| Board | `list_problems`, `open_problem`, `claim_problem`, `release_problem`, `submit_problem`, `verify_problem`, `mark_hopeless`, `set_priority` |
| Memory/team workspace | `remember`, `recall`, `publish_memory`, `message_group`, `check_budget` |

`submit_code` is enabled by the competition action registry for `icpc`, `iiot`, and `codeforces`. It is separate from `execute_code`: use local execution first, then submit code when the contest permits it.

### Competition tool registry

This is the default registry when no enforced rule card overrides it:

| Competition | Tools |
|---|---|
| `purple_comet` | `use_calculator` |
| `fyziklani` | `use_calculator`, `web_search` |
| `iiot` | `execute_code` |
| `icpc` | `execute_code` |
| `codeforces` | `execute_code` |
| `mcm`, `icm` | `execute_code`, `web_search` |
| `ieo_business_case`, `jessup` | `web_search` |
| `iypt` | `web_search`, `execute_code`, `use_calculator` |
| `ijso_practical` | `use_calculator`, `read_lab_equipment` |
| `ioaa_group` | `use_calculator`, `read_star_chart` |
| `iol_team`, `arml_power`, `arml_national_team`, `arml_national_power`, `arml_local`, `hmmt_team`, `hmmt_guts`, `wsc_writing` | No tools |

With `rules_mode=enforced`, `allowed_tools` in the rule card is authoritative. A tool not listed there is a rule violation.

## Computers and `k`

`k` is the number of computers that may be occupied simultaneously in the current environment.

Resolution order:

1. Explicit `computer_capacity=k` passed to `OlympiadEnvironment`.
2. Rule-card resource field: `shared_workstation_count`, `contest_machine_capacity`, or `computer_capacity`.
3. Legacy contest rule text such as `1 shared workstation` or `2 VMs`.
4. Default `k=1`.

`use_calculator` and `execute_code` are computer actions. Each consumes one slot for the current turn. If all `k` slots are occupied, the action returns a resource error and can be retried on the next turn. There is intentionally no required release action: the per-turn occupancy resets when `begin_turn()` starts the next turn.

Current rule-card examples:

| Competition | Rule-card resource | `k` |
|---|---|---:|
| `icpc` | `shared_workstation_count: 1` | 1 |
| `iiot` | `contest_machine_capacity: 2` | 2 |

This is a simulator capacity model. It does not model physical keyboard ownership, queueing, or partial execution within a turn.

## Turns, API calls, and tokens

- Standard experimental budget: `30` turns.
- Recommended minimum for substantive runs: `10` turns (`MIN_RECOMMENDED_TURNS`).
- Explicit `max_turns`, `rounds`, or `decentralized_events` may intentionally use fewer turns for smoke tests.
- One turn is a contest-clock step, not one API call.
- Each eligible team agent gets at most one model call per turn, or may sleep.
- `max_api_calls` limits total model requests across the run.
- `max_output_tokens_per_call` limits one response.
- `max_total_tokens` limits team-wide output.
- Contest durations are converted to simulated minutes; they do not replace an explicit turn override.

ICPC and IIOT default to a `4096` output-token cap per call in the contest budget registry. Other budgets are defined in `src/contest_budget.py` and may be overridden at run time.

## Conditions by mode

| Mode | Problem access | Tools | Submission |
|---|---|---|---|
| `decentralized` | Team problem state | Competition/rule-card allowlist | Final synthesis/authorized submitter |
| `centralized` | Leader and workers according to schema | Competition/rule-card allowlist | Leader/authorized submitter |
| `round_table` | Shared history | Competition/rule-card allowlist | Synthesis/authorized submitter |
| `open_table_coach` | Coach has no problem access in turn 1, opening access in turn 2, then exits | Coach has no tools | Contestants continue; final submission is synthesis-only |
| `single_agent` | Whole task | Team budget matched through solo call allowance | Single logical solver |
| Enforced rule card | Agent-visible rule view | `allowed_tools` and role permissions enforced | `may_submit` role flag enforced |

Structured deliberation actions require an enforced rule card with `deliberation.mode = "structured"`. `write_private_notes` and structured deliberation are unavailable in rules-off mode.

## Run commands

From the repository root:

### Offline smoke run

```bash
PYTHONPATH=src python3 src/run_smoke_batch.py
```

### One live competition with a 10-turn minimum

```bash
export PERPLEXITY_API_KEY=...
PYTHONPATH=src python3 src/run_competition_batch.py \
  --live \
  --provider perplexity \
  --competitions icpc \
  --max-turns 10 \
  --limit 1
```

### Centralized run with enforced rule card

```bash
PYTHONPATH=src python3 src/run_competition_batch.py \
  --live \
  --schema centralized \
  --rules-mode enforced \
  --competitions icpc \
  --max-turns 10 \
  --limit 1
```

### Compare schemas

```bash
PYTHONPATH=src python3 src/run_competition_batch.py \
  --live \
  --schema decentralized \
  --competitions arml_local,ioaa_group \
  --max-turns 10
```

Use `--schema` with the schema names in the table above. Use `--max-turns` for a controlled experiment; omit it to use the contest budget registry.

### Direct environment check

```bash
PYTHONPATH=src python3 - <<'PY'
from env import OlympiadEnvironment

env = OlympiadEnvironment(
    "iiot",
    "iiot_2017_01",
    rules_mode="enforced",
    computer_capacity=2,
)
print(env.get_metadata()["computer_capacity"])
print(env.get_state()["computers_available_this_turn"])
PY
```

### Rules audit

```bash
PYTHONPATH=src python3 src/contest_rules.py --report
```

## Known limits and unresolved items

The unified names are now accepted by the environment, but action logs retain canonical names for compatibility. The following remain partial or deferred in the simulator:

- Physical workstation ownership and keyboard/UI contention are not modeled; `k` is a per-turn occupancy cap.
- Programming judge behavior, hidden tests, pending verdict latency, and full multi-problem packets vary by adapter and rule card.
- Some rule cards describe official resources more precisely than the general registry; enforced cards should be preferred for evaluation.
- `MIN_RECOMMENDED_TURNS` documents the requested floor but does not reject explicit short smoke-test overrides.
- The repository still contains unrelated local changes and one pre-existing structured-gold test failure; this document does not alter those datasets.
