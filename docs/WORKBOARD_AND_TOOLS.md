# Workboard and shared-workspace actions

Most contests in this benchmark are one environment over many items: an ARML
answer sheet has ten problems, an IOAA group task has a dozen labelled
sub-questions. The **workboard** gives a team per-item state for those contests —
a shared sheet where agents pick up an item, record an answer, see every answer
already tried, and review each other's work.

Alongside it, a small set of **workspace actions** covers structured recall,
budget checks, and messaging a subgroup rather than the whole team.

| | |
|---|---|
| Action registry (single source of truth) | [`src/tool_registry.py`](../src/tool_registry.py) |
| Wire parsing (`ACTION \| PAYLOAD` and typed dicts) | [`src/action_wire.py`](../src/action_wire.py) |
| Board | [`src/workboard.py`](../src/workboard.py) |
| Recall | [`src/memory.py`](../src/memory.py) |
| Action dispatch (legacy env runtime) | [`src/env.py`](../src/env.py) |
| Action dispatch (contest-session runtime) | [`src/contest_actions.py`](../src/contest_actions.py) |
| Prompt text | [`src/actions.py`](../src/actions.py) |
| Tests | [`tests/test_workboard.py`](../tests/test_workboard.py), [`tests/test_tool_registry.py`](../tests/test_tool_registry.py) |

---

## One registry, two runtimes

Every action an agent can take is a frozen `ActionSpec` in
`tool_registry.ACTION_REGISTRY` (`ACTION_SET_VERSION = 5`). The same registry
drives both execution paths:

- the **legacy env runtime** (`env.OlympiadEnvironment.execute_action`), used by
  `collaboration.py` schemas and the vanilla baseline, and
- the **contest-session runtime** (`contest_actions.SESSION_HANDLERS`), used by
  `contest_engine` / OTC runs.

Each spec carries a `runtimes` tag. `actions_for_runtime("env")` and
`actions_for_runtime("session")` return the surface each path implements; the
prompt text, the handler tables, and the visibility rules are all derived from
the registry rather than hand-written lists.

| Pack | Actions | Runtimes |
|---|---|---|
| `common` (16) | `speak`, `direct_message`, `work`, `rest`, `submit`, `select_problem`, `skip_problem`, `inspect_problem`, `triage_problem`, `review_answer`, `remember`, `recall`, `share_note`, `assign_problem`, `request_review`, `finish_contest` | both, except `assign_problem` / `request_review` / `finish_contest` (session only) |
| `deliberation` (5) | `propose`, `challenge`, `provide_evidence`, `revise`, `decide` | both |
| `math` (1) | `use_calculator` | both |
| `programming` (2) | `execute_code`, `submit_code` | both |
| `research` (1) | `web_search` | both |
| `resources` (2) | `read_lab_equipment`, `read_star_chart` | both |
| `workboard` (1) | `verify_problem` | env only |
| `workspace` (3) | `check_budget`, `query_rules`, `write_private_notes` | env only |

31 canonical actions in total; 28 reachable from the env runtime, 27 from the
session runtime, 24 shared.

### Legacy names

The pre-unification wire names still parse. `tool_registry.LEGACY_ALIASES` maps
each one onto a canonical action and its argument fields, so old transcripts,
old rule cards, and mock LLM outputs keep working. The action log records the
canonical `action` and, when an alias was used, the original name under
`invoked_as`.

| Old name | Canonical | Notes |
|---|---|---|
| `sleep` | `rest` | |
| `submit_final` | `submit` | |
| `write_scratchpad` | `work` | no `problem_id`; always writes the shared scratchpad |
| `submit_problem` | `work` | `<item> \| <answer>` |
| `claim_problem` | `select_problem` | |
| `release_problem` | `skip_problem` | |
| `list_problems` | `inspect_problem` | no `problem_id` → whole board |
| `open_problem` | `inspect_problem` | |
| `verify` | `inspect_problem` | programming: latest code + run history |
| `set_priority` | `triage_problem` | `<item> \| high\|normal\|low` |
| `mark_hopeless` | `triage_problem` | `<item> \| <reason>` → `hopeless`; `<item> \| undo` → `normal` |
| `publish_memory` | `share_note` | |
| `message_group` | `direct_message` | |

## Availability

Board and workspace actions are not contest tools. They live in the `common`,
`workboard`, and `workspace` packs, outside `TOOL_PACKS`, so `allowed_tools` and
`COMPETITION_TOOL_REGISTRY` do not gate them: every contest, every schema, and
every `rules_mode` can use them, including the vanilla baseline. They model the
desk and the answer sheet, not instruments like `use_calculator` or
`read_star_chart`, which remain per-contest.

Two limits apply:

- **Single-deliverable contests get no board.** When a task has no derivable
  items, board actions return `Board unavailable: ...` and the workspace actions
  continue to work. IOL team and IEO business case fall here by default; see
  [Enabling a board](#enabling-a-board-on-a-new-contest).
- **Phase allowlists still bind board mutations.** A rule card with
  `simulation.phases[].allowed_actions` rejects `work`, `select_problem`,
  `direct_message` and similar during that phase (allowlists may name either
  the canonical or the legacy spelling). Reads and
  personal bookkeeping are exempt — see
  [Submissions and phase rules](#submissions-and-phase-rules).

---

## The board does not grade

`work <item> | <answer>` returns an item's answer history and never reports
whether an answer is correct. Two reasons:

**Fidelity.** ARML, IOL, and IOAA give contestants no per-item feedback during
the contest. Programming contests do, and those already have `submit_code`
backed by a real judge.

**Leak safety.** Board items are derived from `gold_label.parts`, which also
carries `expected` and `reference` — the latter holding the full worked
solution. Only `id` and `points` cross that boundary.
`test_gold_parts_become_items_without_leaking_answers` asserts that neither
value appears in any rendered board text.

The only check available to a team is a teammate reviewing a recorded answer:
`review_answer` (pinned to a version hash, shared with the session runtime) or
the lighter env-only `verify_problem`.

---

## Where board items come from

`Workboard.from_problem()` tries three sources in order and requires at least
two items. If none yields two, the contest runs without a board.

| Priority | Source | `board_source` | Example |
|---|---|---|---|
| 1 | `problem_data["board_items"]` — ids, or `{id, statement, points}` dicts | `board_items` | opt-in per record |
| 2 | `gold_label["parts"]` — id and points only | `gold_parts` | `arml_local` → 10 items |
| 3 | Labels parsed from the problem statement | `statement_labels` | `ioaa_group` → 9 items (`G01`, `G01.1`, …) |

Statement parsing tries four patterns and takes the first yielding two or more
labels: `Problem N` / `Question N` / `Task N` / `Part N` headings; parenthesised
codes such as `(G01.1)`; line-initial `N.` or `N)`; and finally an unanchored
`N.`, since answer-sheet contests ship the whole set as a single paragraph
(`"Team Problems 1. Compute ... 2. Compute ..."`).

Numeric labels must read `1, 2, 3, …` in order. Without that constraint, prose
such as `"the product of its digits is 96. 2. Compute"` contributes a spurious
item 96. Boards are capped at 40 items.

Statements found by the parser attach to gold-part items when the labels match,
so `inspect_problem 3` shows the actual question text rather than a bare id.

---

## Action reference

Payloads take the form `<item> | <rest>`. Item references resolve tolerantly:
`3`, `P3`, `p3`, `Problem 3`, `Q3`, and `(3)` all reach item `3`. The forms
`<item> rest` and `<item>: rest` also parse when the leading token resolves.

### Board actions

| Action | Payload | Visibility | Effect |
|---|---|---|---|
| `inspect_problem` | `[<item>] [\| <focus>]` | private | With an item: statement plus the complete answer history — every attempt with turn and author — along with reviews, the recorded version hash, and the count of rejected repeats. Without one: the whole board (status, points, holder, attempt count, recorded answer per item). In a programming contest with no board: the latest code and run history. |
| `select_problem` | `<item>` | team | Take an item. One per agent: selecting a second releases the first. Refused if another agent holds it. |
| `skip_problem` | `[<reason>]` | team | Hand your current item back (or name one). |
| `work` | `[<item> \|] <answer>` | team | Record an answer for an item (and claim it). Without an item: the answer for the item you hold, or the shared scratchpad when you hold none. The latest recorded answer is the one that gets graded. |
| `triage_problem` | `<item> \| high\|normal\|low\|hopeless [\| <reason>]` | team | Set the team's working priority, or mark the item hopeless. Hopeless items stay on the board — a recorded guess still beats a blank. `normal` clears a hopeless flag. |
| `review_answer` | `<item> \| <version_hash> \| approve\|reject \| <comment>` | team | Approve or reject the recorded answer version shown by `inspect_problem` (`Recorded version: …`). A stale hash is refused with the current one. |
| `verify_problem` | `<item> \| agree\|disagree\|unsure <comment>` | team | Env-only lighter review with no version pin. Refused on your own sole answer. Free text without a verdict keyword stores as `unsure` with the payload as the comment. Does not change the recorded answer. |

`work` on a board item enforces three rules:

- **Repeats are rejected.** Recording an answer already recorded for that item —
  normalised through `evaluation.gold.normalize_answer`, so `(-6, 13)` and
  `(-6,13)` are the same answer — returns a `Board error:` naming the earlier
  turn and author, along with how many items remain blank. It neither
  overwrites nor appends an attempt; it increments `repeat_attempts`.
- **Different answers are unlimited.** Retrying an item with a *new* answer is
  always allowed. Only the literal no-op is refused: persistence on a hard
  problem is rational, and the board does not penalise it.
- **Claims are enforced.** Answering an item another agent holds is refused.

A rejection reads:

```
Board error: '(-6,13)' is already the recorded answer for 3 (turn 4, Agent_1).
Recording it again changes nothing. Try a different approach or move to another
item — 6 item(s) still have no answer.
```

### Workspace actions

| Action | Payload | Visibility | Effect |
|---|---|---|---|
| `remember` | `[<item> \|] <note>` | private | Store a note only you can read, optionally tagged to a board item. Returns its id, e.g. `M1`. |
| `recall` | `[<item> \|] <query>` | private | Search your private notes plus everything published to the team. Item-tagged memories rank first when the query is scoped to an item. |
| `share_note` | `M1, M2` | team | Share stored notes with the team, where they become `S1`, `S2`. |
| `check_budget` | *(none)* | private | Turns, API calls, tokens, contest clock, wrong submissions, and how much of the board is still blank. Env only. |
| `direct_message` | `<names> \| <message>` | group | Message named teammates only. Recipients are validated against the roster; unknown names are refused. Readable by sender and recipients through `format_group_memory`. |

`check_budget` exists so that triage is an informed choice: deciding whether to
keep working an item or move on requires seeing both the clock and the board.

```
=== BUDGET ===
Turns (time): 12/30
API calls (cost): 47/∞
Team output tokens: 18432/∞
Clock: 60/60 min
Board: 4/10 answered, 6 blank, 3 repeat attempt(s) rejected
18 turn(s) left for 6 unanswered item(s) across the whole team. A blank item
scores zero.
```

### Claim expiry

A claim goes stale after `DEFAULT_CLAIM_TTL_TURNS` (3) turns in which its holder
does not touch the item. Without expiry, an agent that claims an item and then
stops acting would hold it for the rest of the run.

### Visibility and observations

Private results — `inspect_problem`, `check_budget`, `query_rules`, `remember`,
`recall` (`env.PRIVATE_WORKSPACE_ACTIONS`) — return to the acting agent only.

Team-visible board mutations also return their full result to the actor, since
a rejection notice is only useful to the agent that triggered it, and append a
one-line notice to `chat_history`:

```
[board] Agent_2 recorded an answer for 3: (-6, 13) (attempt 1).
```

A board that only its author can see coordinates nothing, but broadcasting every
full result to every seat would flood the prompt on a fifteen-agent team.

A refused board or memory call is a no-op rather than a rule violation: it does
not enter `rule_violations` and does not consume communication budget.

---

## Metrics

`Workboard.metrics()` flows into the run result under `workboard`, onto each
batch row, and into the TSV exports.

### Per run

| Metric | Batch row | Sheet column | Meaning |
|---|---|---|---|
| `board_source` | — | — | Which item source was used. |
| `items_total` | `board_items` | `board_items` | Items on the board. |
| `items_answered` | `board_items_answered` | `board_answered` | Items with a recorded answer. |
| `items_unanswered` | — | — | Items scoring zero by default. |
| `items_reviewed` | `board_items_reviewed` | `board_reviewed` | Items with at least one review. |
| `items_hopeless` | — | — | Items flagged through `triage_problem … hopeless`. |
| `attempts_recorded` | `board_attempts` | — | Distinct answers recorded across all items. |
| `repeat_attempts_rejected` | `board_repeat_attempts` | `board_repeats` | Attempts refused as already recorded. |
| `repeat_rate` | `board_repeat_rate` | `board_repeat_rate` | `repeats / (attempts + repeats)`. |
| `distinct_claimers` | — | — | Agents that held a claim; a division-of-labour proxy. |

### Per batch

Computed in `_aggregate_metrics`, both overall and per competition:

| Metric | Meaning | Appears in |
|---|---|---|
| `board_runs` | Runs in the batch that had a board. | `competition_summary.tsv` |
| `mean_board_repeat_rate` | Mean `repeat_rate` across those runs. | `competition_summary.tsv`; as `board_repeat_rate` in `sheet1_summary.tsv` |
| `total_board_repeat_attempts` | Absolute count of refused repeats. | `competition_summary.tsv` |
| `mean_board_answered_fraction` | Mean `items_answered / items_total`; board coverage. | `competition_summary.tsv`; as `board_answered_frac` in `sheet1_summary.tsv` |

**Reading `repeat_rate`.** It counts refused repeats only — attempts to record
an answer the team already held for that item. A high rate indicates a team
cycling on answers it has already tried rather than exploring new ones. It
cannot exceed 1, and is `0.0` for a run without a board. Because the board
refuses a repeat rather than absorbing it, the metric measures the behaviour
directly rather than approximating it.

Complete board state — every attempt, review, and claim with turn and author —
is written to the transcript under `workboard`, and memory under `memory`.

---

## Submissions and phase rules

**`submit` is backed by the board.** `env._resolve_final_payload` merges
the submitted text with recorded board answers:

1. The submitter's own text wins, since synthesis is instructed to recompute
   rather than copy.
2. Recorded items the submitter omitted are appended under
   `Recorded on the board and not covered above:`.
3. If the submission parses to no numbered answers at all — commentary, a stray
   `ACTION:` line, or a bare `submit` / `done` — the board sheet is used.

The merge lives in the environment rather than in
`collaboration._run_synthesis`, so every submission path benefits, including
`single_agent`, `memory_solo`, `subagent`, and `debate`, which never call
synthesis. Contests without a board pass through untouched.

**The 10-character minimum on `submit` exempts answer sheets.** That floor
rejects `"ok"` and `"done"`; `"1. 268"` is a complete submission on a one-item
board.

**Phase allowlists implicitly permit reads.** `rules/phases.py` exempts
`IMPLICITLY_ALLOWED_ACTIONS` — `inspect_problem`, `check_budget`, `remember`,
`recall`, `share_note` — from `allowed_actions` checks. Those allowlists
constrain what a team may *do* during a phase, not whether a contestant may
check the clock or reread their own notes. Actions that change shared state stay
gated, so an enforced IEO run returns:

```
RULE VIOLATION: Preparation day — action 'direct_message' is not permitted
during this phase.
```

To allow it, add `direct_message` (or the legacy `message_group`; matching is
alias-aware) to the relevant phase in
`data/rules/ieo_business_case/collaboration.json`.

---

## Enabling a board on a new contest

Add `board_items` to the benchmark record. Entries may be bare ids or dicts:

```json
{
  "problem_id": "iol_team_2003",
  "board_items": [
    {"id": "1", "statement": "Assign the Tocharian subscripts.", "points": 20},
    {"id": "2", "statement": "Translate the verb forms.", "points": 20}
  ]
}
```

This is the intended route for rubric-graded contests that have distinct
sub-tasks but no `gold_label.parts`. Check the result with:

```bash
PYTHONPATH=src python3 -c "
from env import OlympiadEnvironment
env = OlympiadEnvironment('iol_team', 'iol_team_2003')
print(env.workboard.source if env.workboard else 'NO BOARD')
print(env.board_overview())
"
```

---

## Extending

Board state is a plain `Workboard` holding `BoardItem` objects; each item owns
its `attempts`, `reviews`, claim, and triage flags. To add an action:

1. Declare it once in `src/tool_registry.py` with `_action(...)`: name, pack,
   typed arguments, description, and `runtimes` (`ALL_RUNTIMES`, `ENV_ONLY`,
   or `SESSION_ONLY`). Putting it in `common`, `workboard`, or `workspace`
   keeps it outside `TOOL_PACKS`, so no rule card needs to declare it. Bump
   `ACTION_SET_VERSION`.
2. Implement it: add an `_act_<name>` method and a row in
   `OlympiadEnvironment._HANDLERS` (`src/env.py`) for the env runtime, and/or a
   `_session_<name>` handler in `SESSION_HANDLERS` (`src/contest_actions.py`)
   for the session runtime. `OlympiadEnvironment.unimplemented_actions()`
   returns env-tagged specs that have no handler yet (it should stay empty);
   `validate_registry()` checks pack names, runtime tags, legacy field names,
   and alias targets.
3. Decide visibility. Add read-only actions to `PRIVATE_WORKSPACE_ACTIONS` in
   `src/env.py`; give mutations a summary line in `_broadcast_board_event`.
4. If an old wire name should keep working, add a `LegacyAlias` to
   `LEGACY_ALIASES`. The prompt text is rendered from the spec's description
   and arguments (`actions.build_action_instructions`), so there is no separate
   string to edit.

Run the suite with:

```bash
PYTHONPATH=src python3 -m pytest tests/test_workboard.py tests/test_tool_registry.py -q
```
