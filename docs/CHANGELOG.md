# Changelog

## Per-item workboard and shared-workspace actions

Adds per-item state to multi-item contests: agents pick up an item, record an
answer, see every answer already tried, and review each other's work. Full
reference in [`WORKBOARD_AND_TOOLS.md`](WORKBOARD_AND_TOOLS.md).

### New module — `src/workboard.py`

| Component | Purpose |
|---|---|
| `Attempt` | One recorded answer: turn, agent, text, normalised key. |
| `Review` | One `verify_problem` verdict against the answer it reviewed. |
| `BoardItem` | One contest item: statement, points, claim, attempts, reviews, triage flags. |
| `Workboard` | The board: item collection, reference resolution, mutations, metrics. |
| `_parse_labeled_spans()` | Splits a problem statement into `label → body` using the first of four patterns that finds ≥2 labels. |
| `_keep_ordered_run()` | Keeps only numeric labels reading `1, 2, 3, …`, so prose like `"…is 96. 2. Compute"` does not create an item 96. |
| `_normalize()` | Answer-equality key via `evaluation.gold.normalize_answer`, so repeat detection matches grading. |

`BoardItem`: `.answer` (latest attempt — the one graded) · `.answered` ·
`.status()` (`open`/`claimed`/`answered`/`reviewed`/`hopeless`) · `.holder()`
(claim holder, `None` once stale) · `.snapshot()`.

`Workboard`: `.from_problem()` (derives a board, or `None` for single-deliverable
tasks) · `.resolve()` (tolerant item lookup) · `.split_ref()` · `.overview()` ·
`.detail()` · `.answer_sheet()` · `.claim()` / `.release()` · `.record_answer()` ·
`.review()` · `.set_priority()` / `.mark_hopeless()` · `.metrics()` · `.snapshot()`.

### New actions

Registered in `CORE_WORKSPACE_ACTIONS` (`src/env.py`), which sits outside
`TOOL_ACTIONS` — so every contest, schema, and `rules_mode` can use them,
including the vanilla baseline, with no rule-card declaration.

**Board** (`BOARD_ACTIONS`)

| Action | Payload | Effect |
|---|---|---|
| `list_problems` | — | Whole board: status, points, holder, attempts, recorded answer. |
| `open_problem` | `<item>` | Statement plus complete answer history and reviews. |
| `claim_problem` | `<item>` | Take an item; one per agent, auto-releases the previous. |
| `release_problem` | `<item>` | Hand it back. |
| `submit_problem` | `<item> \| <answer>` | Record an answer. Latest recorded answer is what gets graded. |
| `verify_problem` | `<item> \| agree\|disagree\|unsure <comment>` | Review a teammate's recorded answer. Cannot review your own sole answer. |
| `mark_hopeless` | `<item> \| <reason>` or `\| undo` | Flag as not worth more time; item stays on the board. |
| `set_priority` | `<item> \| high\|normal\|low` | Triage marker. |

**Workspace** (`MEMORY_ACTIONS`, `TEAM_ACTIONS`)

| Action | Payload | Effect |
|---|---|---|
| `remember` | `[<item> \|] <note>` | Store a private note, optionally tagged to an item. Returns `M1`. |
| `recall` | `[<item> \|] <query>` | Search private notes plus team-published ones. |
| `publish_memory` | `M1, M2` | Share stored notes with the team as `S1`, `S2`. |
| `check_budget` | — | Turns, API calls, tokens, clock, and how much of the board is blank. |
| `message_group` | `<names> \| <message>` | Message named teammates only; recipients validated against the roster. |

Three rules make the board more than bookkeeping:

- **Repeats are rejected.** Recording an answer already recorded for that item
  returns a `Board error:` naming the earlier turn and author, and increments
  `repeat_attempts` without overwriting.
- **Different answers are unlimited.** Only the literal no-op is refused.
- **Claims are enforced**, and expire after 3 idle turns so the board cannot
  deadlock.

### New environment methods — `src/env.py`

| Method | Purpose |
|---|---|
| `register_agents()` | Records the roster so claims, reviews, and direct messages validate against real names. |
| `board_enabled()` / `board_overview()` / `board_answer_sheet()` | Board accessors for prompts and runners. |
| `_board_action()` | Dispatches the eight board actions. |
| `_memory_action()` | Dispatches `remember` / `recall` / `publish_memory`. |
| `_check_budget()` | Renders the budget report. |
| `_parse_recipients()` | Parses and validates `message_group` recipients. |
| `_broadcast_board_event()` | Posts a one-line `[board]` notice to `chat_history` on each mutation. |
| `_sync_answer_sheet()` | Mirrors recorded answers into `workspace["answer_sheet"]`. |
| `_resolve_final_payload()` | Backs `submit_final` with the board (see below). |
| `_board_submission_note()` | Appends unanswered items to the submission result. |

New constants: `BOARD_ACTIONS`, `MEMORY_ACTIONS`, `TEAM_ACTIONS`,
`CORE_WORKSPACE_ACTIONS`, `PRIVATE_WORKSPACE_ACTIONS`,
`OPERATIONAL_ERROR_PREFIXES`.

### New metrics

`Workboard.metrics()` → run result `workboard` → batch row → TSV.

| Metric | Row / sheet column | Meaning |
|---|---|---|
| `board_source` | — | Which of the three item sources was used. |
| `items_total` | `board_items` | Items on the board. |
| `items_answered` | `board_items_answered` / `board_answered` | Items with a recorded answer. |
| `items_unanswered` | — | Items scoring zero by default. |
| `items_reviewed` | `board_items_reviewed` / `board_reviewed` | Items with at least one review. |
| `items_hopeless` | — | Items flagged via `mark_hopeless`. |
| `attempts_recorded` | `board_attempts` | Distinct answers recorded. |
| `repeat_attempts_rejected` | `board_repeat_attempts` / `board_repeats` | Attempts refused as already recorded. |
| `repeat_rate` | `board_repeat_rate` | `repeats / (attempts + repeats)`. |
| `distinct_claimers` | — | Agents that held a claim; work-division proxy. |

Batch aggregates (`_aggregate_metrics`, `src/run_competition_batch.py`):
`board_runs`, `mean_board_repeat_rate`, `total_board_repeat_attempts`,
`mean_board_answered_fraction`.

New helper `_board_row_fields()` flattens board metrics onto each row; columns
added to `competition_batch.tsv`, `competition_summary.tsv`,
`sheet1_summary.tsv`, and `sheet2_detail.tsv`.

### Changed behaviour

**`submit_final` is backed by the board** (`env._resolve_final_payload`). The
submitter's own answers win; recorded items they dropped are appended under
`Recorded on the board and not covered above:`; a submission that parses to no
numbered answers falls back to the board sheet. Without this a synthesizer that
returned commentary or a stray `ACTION:` line discarded the team's recorded
work — a run with five correct answers on the board scored zero. The merge lives
in the environment, so every submission path benefits, including
`single_agent`, `memory_solo`, `subagent`, and `debate`, which never call
synthesis.

**The 10-character minimum on `submit_final` exempts answer sheets.** That floor
rejects `"ok"`; `"1. 268"` is a complete submission on a one-item board.

**Phase allowlists implicitly permit reads** (`rules/phases.py`,
`IMPLICITLY_ALLOWED_ACTIONS`). Rule cards that list `allowed_actions` predate
these actions and would ban them by omission; reads and personal bookkeeping are
now exempt, while actions that change shared state stay gated.

**Refused board and memory calls are no-ops, not rule violations.** They stay
out of `rule_violations` and consume no communication budget.

**`MemoryStore` gained per-item scoping and auto-registration**
(`src/memory.py`): `MemoryItem.problem_ref`, `add(problem_ref=…)`,
`recall(problem_ref=…)` ranking item-tagged memories first, and agents
registering on first write.

**Prompts carry board state** (`src/collaboration.py`,`src/actions.py`): the
board overview and group messages appear in the agent prompt, the recorded
answer sheet appears in the synthesis prompt, and `build_action_instructions()`
takes `board_item_count` / `workspace_actions` to render
`WORKBOARD_INSTRUCTIONS` and `WORKSPACE_INSTRUCTIONS`.

### Tests

`tests/test_workboard.py` — 32 tests across board construction (including
gold-answer leak protection), behaviour, environment integration, and phase
gating.

---

## Documentation and repository hygiene

- **New:** [`BENCHMARK_DESIGN.md`](BENCHMARK_DESIGN.md) — what the benchmark
  measures, contest realism, baselines, CS/IHS metric definitions, the two
  reporting layers, and known limitations.
  [`WORKBOARD_AND_TOOLS.md`](WORKBOARD_AND_TOOLS.md) — workboard reference.
- **Removed from the repository:** meeting notes, weekly status updates, and
  dated plans. They were internal working documents; their technical substance
  was folded into `BENCHMARK_DESIGN.md`. Contributor documentation under
  `docs/from_zhongzheng/` is unaffected.
- **Renamed:** `scripts/export_shawn_sheet.py` → `scripts/export_results_sheet.py`,
  generated `shawn_sheet/` output directories → `results_sheet/`, and
  `results/demo_yusen/` → `results/demo_submission/`, so that generated paths
  and filenames describe their contents rather than a person.
- **Fixed:** the per-problem block of `sheet1_summary.tsv` now derives its header
  and body from the same keys, so they cannot drift apart as columns are added.
