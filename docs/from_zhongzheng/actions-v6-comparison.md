<!-- markdownlint-disable MD060 -->

# Action set v6: full surface and v5 → v6 comparison

> Source: `src/tool_registry.py` in the working tree (`ACTION_SET_VERSION = 6`)
> compared against `git HEAD` (`4239c5bc`, `ACTION_SET_VERSION = 5`).
> Every count below comes from importing both registries directly, not from
> copying other documents.

## 0. Summary

| | v5 (HEAD) | v6 (working tree) |
|---|---:|---:|
| Registered canonical actions | 31 | **29** |
| Packs | 8 (incl. `workboard`, `workspace`) | **6** |
| Implemented by the `env` runtime | 28 | **29** |
| Implemented by the `session` runtime | 27 | **29** |
| env-only | 4 (`verify_problem`, `check_budget`, `query_rules`, `write_private_notes`) | **0** |
| session-only | 3 (`assign_problem`, `request_review`, `finish_contest`) | **0** |
| Legacy aliases | 13 | **15** |
| `review_answer.version_hash` | required | **optional** |
| New `validate_registry()` rule | — | a spec tagged for only one runtime is an error |

v6 does one thing: **one vocabulary, implemented on both execution paths**. To
get there it removed two env-only actions (folded into aliases), promoted two
env-only actions into `common`, and gave the env handlers for the three
session-only actions.

## 1. What v6 contains (29 actions)

### 1.1 `common` (18, loaded unconditionally by both runtimes)

| Action | Arguments (`?` = optional) | Visibility | Budget | Effect |
|---|---|---|---|---|
| `select_problem` | `problem_id` | contest | 1 turn | Select (claim) a problem |
| `skip_problem` | `reason?` | contest | 1 turn | Release the current problem |
| `work` | `content`, `problem_id?` | team | 1 turn | Record a candidate answer/draft version; with `problem_id` it switches problem atomically |
| `speak` | `content` | team | 1 turn | Team broadcast |
| `direct_message` | `recipients[]`, `content` | private | 1 turn | Message one teammate or a named sub-group |
| `inspect_problem` | `problem_id?`, `focus?` | private | 1 turn | Read-only: statement + full version/review/submission history; does not change focus, does not count as a review |
| `triage_problem` | `problem_id`, `priority{high,normal,low,hopeless}`, `reason?` | team | 1 turn | Set team priority / mark hopeless |
| `remember` | `content`, `problem_id?` | private | 1 turn | Durable private note |
| `recall` | `query?`, `problem_id?` | private | 1 turn | Search own notes + notes teammates shared |
| `share_note` | `note_id` | team | 1 turn | Publish a note to the team |
| `assign_problem` | `agent`, `problem_ids[]`, `reason?` | team | 1 turn | Leader only: replace a teammate's work list |
| `request_review` | `content`, `reviewer?` | team | 1 turn | Ask for a review; never approves |
| `review_answer` | `problem_id`, `version_hash?`, `decision{approve,reject}`, `content` | team | 1 turn | Independently review another author's current version; without a hash it binds to the current version |
| `submit` | `answer` | team | 1 turn + 1 submission | Final non-programming submission (evaluator: `task_evaluator`) |
| `finish_contest` | `reason?` | contest | 1 turn, terminal | Allowed only when every task has a valid submission and required review; answer-sheet contests end through `submit` |
| `rest` | `reason?` | private | 1 turn | Pass the turn |
| `check_budget` | — | private | 1 turn | Turns / API calls / tokens / clock / penalties / problems with nothing recorded |
| `query_rules` | — | private | 1 turn | Rules and rule card as visible to the role |

### 1.2 `deliberation` (5, only for OTC with a rule card whose `deliberation.mode == "structured"`)

| Action | Arguments | Effect |
|---|---|---|
| `propose` | `content`, `problem_id?` | Open a numbered proposal |
| `challenge` | `proposal_id`, `content` | Concrete objection to someone else's open proposal |
| `provide_evidence` | `proposal_id`, `content` | Attach a check, derivation, or counterexample |
| `revise` | `proposal_id`, `content` | Author only: replace the proposal's current claim |
| `decide` | `proposal_id`, `outcome{accept,reject,defer}`, `reason` | Card-designated decision maker only |

### 1.3 Tool packs (`TOOL_PACKS`, resolved per competition/capability, 6 actions)

| Pack | Action | Arguments | Visibility | Budget |
|---|---|---|---|---|
| `math` | `use_calculator` | `expression` | private | 1 turn + 1 tool_call |
| `programming` | `execute_code` | `code`, `language?` | private | 1 turn + 1 tool_call |
| `programming` | `submit_code` | `code`, `language?` | team | 1 turn + 1 tool_call + 1 submission (evaluator: `programming_judge`) |
| `research` | `web_search` | `query` | private | 1 turn + 1 tool_call |
| `resources` | `read_lab_equipment` | `resource?` | private | 1 turn + 1 tool_call |
| `resources` | `read_star_chart` | `resource?` | private | 1 turn + 1 tool_call |

`resources` is never inferred from competition or task type; the benchmark/card
must declare the capability and a handler must exist.

### 1.4 Named subsets in the registry (what policies switch on and off)

| Constant | Members | Consumer |
|---|---|---|
| `DESK_ACTION_NAMES` | `inspect_problem`, `triage_problem`, `remember`, `recall`, `share_note` | contest runners keep these whenever the agent may act at all |
| `DESK_READONLY_ACTION_NAMES` | `inspect_problem`, `triage_problem` | `features.desk_actions` |
| `MEMORY_ACTION_NAMES` | `remember`, `recall`, `share_note` | `features.memory_actions` |
| `DESK_BOOKKEEPING_ACTION_NAMES` **(new in v6)** | `check_budget`, `query_rules` | hidden from session prompts unless the card's `allowed_actions` lists them |
| `LEADER_ACTION_NAMES` | `assign_problem` | `features.leader_submits` |
| `DELIBERATION_ACTION_NAMES` | the 5 deliberation actions | `otc_policy.structured_deliberation` |

## 2. v5 → v6, item by item

### 2.1 Merged (removed from the registry, kept as aliases)

| v5 action | v5 pack / runtime | v6 target | Semantics |
|---|---|---|---|
| `verify_problem` | `workboard` / env-only | alias → `review_answer` | `<item> \| agree\|disagree\|unsure <comment>`; `agree→approve`, `disagree→reject`, `unsure→reject` with `[unsure]` prefixed to the comment (the board still shows the verdict as `unsure`); no version pin, binds to the current version. Transform: `_verify_transform` |
| `write_private_notes` | `workspace` / env-only | alias → `remember` | whole payload is the note; the env still refreshes the private-notes prompt block from it |

### 2.2 Kept, promoted (moved from an env-only pack into `common`)

| Action | v5 | v6 |
|---|---|---|
| `check_budget` | `workspace` pack, env-only | `common`, implemented by both runtimes; the session appends a private `budget_result` event. The prompt already injects the BUDGET block, so the session does not advertise it unless the card lists it |
| `query_rules` | `workspace` pack, env-only | `common`; the session appends a private `rules_result` event (`rule_guidance` + baseline features + card allowed actions); same advertising rule |

### 2.3 Added to the env (previously session-only; v6 drops `runtimes=SESSION_ONLY`)

| Action | v6 env behaviour (`src/env.py`) |
|---|---|
| `assign_problem` | leader (rule-card submitter, else the first registered agent) sets a teammate's work list and claims the first item for them; `inspect_problem` shows `Assigned to:` |
| `request_review` | records a review request on the item (`REVIEW REQUESTS` in `inspect_problem`), broadcasts, and DMs the named reviewer; `legacy_payload` grew from `("content",)` to `("content", "reviewer")` |
| `finish_contest` | programming contests: finalize the latest `submit_code` that passed judging; answer-sheet contests: refused with a pointer to `submit` |

### 2.4 Argument / description changes

| Item | v5 | v6 |
|---|---|---|
| `review_answer.version_hash` | required | optional; default = the version currently recorded; a stale hash is refused and the current one is reported |
| `review_answer` description | one sentence | explains that the hash comes from `inspect_problem` and what omitting it means |
| `finish_contest` description | one sentence | adds "answer-sheet contests end through `submit`" |
| `check_budget` description | mentions blank board items | mentions penalties and problems with nothing recorded |

### 2.5 Structural removals

| Removed | Reason |
|---|---|
| packs `workboard`, `workspace` | all members merged or promoted; `PACK_NAMES` shrinks to 6 |
| `ENV_DESK_PACKS` | no pack is loaded unconditionally for one runtime only; `_requested_names` looks at `ALWAYS_ON_PACKS = {common}` alone |
| the `runtime == "env"` branch in `_requested_names` | both runtimes resolve identically |

### 2.6 Unchanged (v5 == v6)

`select_problem`, `skip_problem`, `work`, `speak`, `direct_message`,
`inspect_problem`, `triage_problem`, `remember`, `recall`, `share_note`,
`submit`, `rest`; the 5 `deliberation` actions; the 6 tool actions in
`math`/`programming`/`research`/`resources`; the competition allowlists in
`COMPETITION_TOOL_REGISTRY` / `COMPETITION_ACTION_REGISTRY`; the 13 aliases
already present in v5.

## 3. Legacy aliases (v6, 15)

| Old name | Canonical | Notes | New in v6 |
|---|---|---|:-:|
| `submit_final` | `submit` | | |
| `sleep` | `rest` | | |
| `write_scratchpad` | `work` | no `problem_id`; writes the shared scratchpad | |
| `submit_problem` | `work` | `<item> \| <answer>` | |
| `verify` | `inspect_problem` | programming: latest code + run history | |
| `list_problems` | `inspect_problem` | no arguments → whole board | |
| `open_problem` | `inspect_problem` | | |
| `claim_problem` | `select_problem` | | |
| `release_problem` | `skip_problem` | | |
| `set_priority` | `triage_problem` | `<item> \| high\|normal\|low` | |
| `mark_hopeless` | `triage_problem` | `<item> \| <reason>` → hopeless; `<item> \| undo` → normal | |
| `publish_memory` | `share_note` | | |
| `message_group` | `direct_message` | | |
| `verify_problem` | `review_answer` | three-state verdict folded onto two states, see §2.1 | ✔ |
| `write_private_notes` | `remember` | | ✔ |

The action log records the canonical `action`; when an alias was used the
original name goes under `invoked_as`. Name matching in rule cards and phase
allowlists is alias-aware (`action_matches`).

## 4. Runtime matrix: v5 vs v6

| Action | v5 env | v5 session | v6 env | v6 session |
|---|:-:|:-:|:-:|:-:|
| the 13 `common` actions not listed below | ✔ | ✔ | ✔ | ✔ |
| `assign_problem` | ✘ | ✔ | ✔ | ✔ |
| `request_review` | ✘ | ✔ | ✔ | ✔ |
| `finish_contest` | ✘ | ✔ | ✔ | ✔ |
| `check_budget` | ✔ (workspace) | ✘ | ✔ (common) | ✔ (common) |
| `query_rules` | ✔ (workspace) | ✘ | ✔ (common) | ✔ (common) |
| `verify_problem` | ✔ (workboard) | ✘ | alias | alias |
| `write_private_notes` | ✔ (workspace) | ✘ | alias | alias |
| `deliberation` ×5 | ✔ | ✔ | ✔ | ✔ |
| tools ×6 | ✔ | ✔ | ✔ | ✔ |
| **Total** | **28** | **27** | **29** | **29** |

## 5. Registered ≠ advertised: per-baseline surface (v6, `contest_policy._trim_to_baseline`)

| Capability | single_agent | decentralized | centralized | OTC |
|---|:-:|:-:|:-:|:-:|
| `speak` / `work` / navigation / `rest` / `submit` | ✔ | ✔ | ✔ | ✔ |
| `direct_message` | ✘ | ✘ | ✔ | ✔ |
| `inspect_problem` / `triage_problem` | ✘ | ✘ | ✔ | ✔ |
| `remember` / `recall` / `share_note` | ✘ | ✘ | ✘ | ✔ |
| `review_answer` / `request_review` | ✘ | ✘ | ✘ | ✔ (OTC then drops `request_review`: candidates enter the review queue automatically) |
| `assign_problem` | ✘ | ✘ | leader only | ✘ (also hidden when coach=card) |
| `deliberation` ×5 | ✘ | ✘ | ✘ | card-dependent |
| `check_budget` / `query_rules` | only if card lists them | only if card lists them | only if card lists them | only if card lists them |
| tools | per competition | per competition | per competition | per competition + card |

`basic_open_table` additionally hides deliberation + `review_answer` +
`request_review`; `team_size < 2` hides `direct_message`. Dynamic gates (no
current draft, stale hash, self-review, lease held elsewhere, message budget
exhausted, …) are listed in `actions-reference.md` §6.

## 6. Related files

| | |
|---|---|
| Registry (single source of truth) | `src/tool_registry.py` |
| Session handlers | `src/contest_actions.py` (`SESSION_HANDLERS`) |
| Env handlers | `src/env.py` (`OlympiadEnvironment._HANDLERS`) |
| Baseline trimming | `src/contest_policy.py` (`_trim_to_baseline`) |
| Tests | `tests/test_tool_registry.py` (asserts `ACTION_SET_VERSION == 6`, 29 actions, env == session), `tests/test_workboard.py` |
| Longer prose | `actions-reference.md`, `../WORKBOARD_AND_TOOLS.md` |
