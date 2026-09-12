# Contest sessions: four baselines on one engine

Use an explicit manifest so unrelated benchmark years are never mixed into one
contest:

```powershell
python src/run_competition_batch.py `
  --live `
  --contest-manifest data/contest_manifests/icpc_wf_2012_5.json `
  --system-variant otc `
  --max-api-calls 300 `
  --max-total-tokens 80000 `
  --output results/icpc_otc
```

Run a matched baseline with the same model, manifest, team size, API limit,
token limit, turn limit, and starting seat; change only `--system-variant`.
Use `--start-seat` for repeated runs with a different first agent.

## Baselines (2026-09-10)

`--system-variant` names one of four baselines. Each is a named preset of
orthogonal switches (`contest_config.BaselineFeatures`); the engine never
branches on the baseline's name, only on these switches, so adding a baseline
is one table row, not a new set of `if` statements.

| baseline | coach | review workflow | memory (`remember/recall/share_note`) | desk (`inspect/triage`) | `direct_message` | structured context | cooldown | mechanical switch | leader submits | rule card |
|---|---|---|---|---|---|---|---|---|---|---|
| `single_agent` (team_size pinned to 1) | none | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | off |
| `decentralized` (open table, rotating seats) | none | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | off |
| `centralized` (`Agent_1` is the leader) | leader | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | off |
| `otc` (rule-card Open Table Coach) | card (turn 0 only) | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | enforced |

### `otc`: the rule card drives the session

`otc` is the Open Table Coach method as written in
`data/rules/<competition>/collaboration.json`, run on the contest-session
engine. It is the only baseline with `rule_card="enforced"`; the card is
loaded by `run_competition_batch.py` (missing card fails closed; see
[reuse and settings](contest-run-reuse.md)), validated by `src/rulecard_policy.py`, and its `rule_id` / SHA-256 / mode are recorded in
`contest_session.json["rule_card"]`. What the card decides:

| card block | runtime behaviour |
|---|---|
| `team_size_min/default/max`, `agent_roles[].may_submit` | roster defaults to the card's (`--team-size` outside the range is an error); only `may_submit` roles see `submit` / `submit_code` / `finish_contest` |
| `simulation.open_table_coach.precontest_brief` (`turn=0`, `problem_access=false`) | Exactly one blind Coach brief before the clock: one API call, zero contestant turns/minutes. Resume restores that event, never calls Coach again |
| `opening_discussion.enabled=false` | No second Coach call, summary, or problem assignment |
| `contestant_turn_policy.private_think_calls_per_turn` | each seat makes N private think calls (text, event `think`, private ledger of `memory_entries.private_think_per_agent` entries shown back) then exactly one typed action; API budget default = `turns × team × (1+N) + 1` |
| `max_chars_by_action` | `work/speak/direct_message/rest/deliberation` content is clipped at the card limit (event `card_content_clipped`); `think` likewise |
| `memory_entries` | `strategic_projection(max_current_events=shared_work, max_direct_messages=group_messages, max_team_messages=public_messages)` |
| `discussion_policy` | `report_after_work` / `conflicts_require_targeted_speak` in the prompt; `silent_work_turn_requires_discussion`: after 2 consecutive work-only turns only discussion actions (+ desk read-only) remain for that turn |
| `communication` (`limited`: team / per-agent budget, `max_message_chars`) | `speak` / `direct_message` / `share_note` (+ deliberation actions) are counted; a message longer than `max_message_chars` is clipped (the effective limit is `min(card max_chars, max_message_chars)`); once the message *count* is exhausted → action error, turn spent |
| `deliberation.mode == "structured"` (`min_challenges`, `decision_maker`) | adds the competition-specific **deliberation pack** `propose / challenge / provide_evidence / revise / decide` (ledger replayed from events; `decide` only for the decision maker); the four follow-up actions are offered only while a proposal is open and their `proposal_id` is pinned to the open ids; the protocol line lists the open proposals; the answer sheet cannot be submitted before `min_challenges` challenges |
| `min_turns` | contest-ending actions (`submit` on an answer sheet, `finish_contest`) are withheld before that turn |
| `exclusive_workstation_lease: enforced` (ICPC) | One team-global keyboard; the last executor/submitter holds it for 2 turns across all problems. Other seats can analyse/review but cannot execute/submit by switching problems |
| `run_judging_latency_turns` | The actual verdict is controller-private; all contestant surfaces see only PENDING until delivery. No early score/lock/penalty/reopen. Pending source is frozen. Queue and exactly-once delivery survive checkpoints; final collection flushes pending verdicts |
| `repair_budget_after_rejected_run` (default 2) | after an official rejection, N executions without a sample-AC on *new* source lower the problem to `low` priority (event `programming_repair_budget_exhausted`) |

Actions are organised as one **common set** every competition gets
(`select_problem / speak / direct_message / work / rest / skip_problem /
finish_contest / submit` + desk `inspect_problem / triage_problem / remember /
recall / share_note`) plus **competition-specific bundles** switched on by the
manifest and the card: `programming` (`execute_code / submit_code`, ICPC-style
lease and latency), `math` (`use_calculator`), `research` / `resources`, and
the card-only `deliberation` pack. Cards declare `action_surface=registry_bundles_v1`
and the exact bundle list; `allowed_actions` names the core work/talk/rest bundle,
not the complete registry surface. `review_answer` is enabled; candidate versions
automatically enter the shared review queue, so no separate `request_review` action
is needed. `assign_problem` is unavailable. Approval must be by a different author
and match the current hash; a current rejection vetoes submission. Revision stales
previous reviews. Deadline collection does not bypass this gate (or programming
sample evidence). There is no extra whole-contest final-review pass by default.

Focus under `otc` is per seat, not the shared cursor: a seat's own latest
`select_problem` stands until it switches; otherwise it considers the scheduler's
next blank problem and its own recent focus. There are no Coach-generated assignments. Because the card allows exactly one action per turn,
`work` carries an optional `problem_id`: `work(problem_id=X, content=...)`
switches to X and records the draft in the same move (logged as a
`select_problem` event with `via: "work"` so the focus follows on later turns).

The protocol is now `contest_session_v6` (`otc_turn0_review_v1` in the cards).
This is the user-maintained OTC, not a restoration of Selin\'s old OTC engine.
Do not resume v5/older results under v6; identity validation rejects that mismatch.
ARML Local defaults to its competition card\'s 45 minutes / 9 rounds; national team
is 20 minutes / 4 rounds, with `min_turns <= max_turns`. Explicit experimental
budget overrides remain possible and are recorded, not relabeled as official runs.

Old spellings `OTC`, `open_table_coach`, `open_table_coach_memory`,
`strategic`, and `strategic_team` all resolve to `otc`.
`vanilla` / `vanilla_team` still resolve to `decentralized`.
Results store the canonical name in `system_variant` and the requested spelling
in `run.requested_variant`. Legacy `--schema open_table_coach` is retired:
use `--contest-manifest ... --system-variant otc`.
Historical outputs retain their original names and protocol metadata.

Configuration lives in `src/contest_config.py`; action effects and card gates
live in `src/contest_actions.py`; lifecycle orchestration now lives in
`src/contest_engine.py`. `src/contest_runner.py` is a compatibility facade:
the old runner imports remain compatible re-exports,
not duplicate implementations. The ICPC batch now uses the official CLI for both
fresh and resumed runs, not a script inside a historical result directory.

`single_agent` and `decentralized` share every switch; the only difference is
the one-seat constraint. Both are the v3 vanilla environment: no desk or memory
tools, raw 12-event context, answer-sheet drafts auto-advance to the next unseen
problem.

`centralized` is the contest-session form of the legacy `--schema centralized`:
`Agent_1` writes the opening plan itself (same JSON schema as the Coach, event
`precontest_coach_guidance` with `author=Agent_1`), stays in the contest as an
ordinary contestant who may work on any problem, acts first every round, and is
the **only** seat that can `submit` / `submit_code` / `finish_contest` (workers
never see those actions; the leader's `submit_code` takes no arguments and
sends the active problem's latest recorded source). The leader-only
`assign_problem(agent, problem_ids, reason?)` replaces one worker's enforced work
list live; it is a public event replayed on resume. There is no review
workflow, so review routes are cleared from the plan.

Ablations pass `features=BaselineFeatures(...)` (or `--require-review` /
`--no-require-review`) on top of a preset; the label stays the preset name.

Module interfaces:

- `src/vanilla_contest_runner.py` runs the no-coach presets. Its interface
  intentionally has no `coach_query_fn`, so Coach behavior cannot be enabled
  accidentally.
- `src/strategic_contest_runner.py` runs the coach and leader presets,
  including the Coach dependency (the leader plan uses the contestant model).
- `src/contest_runner.py` retains the compatibility dispatcher and helper imports.
- `src/contest_engine.py` owns one run's private state and orders setup, Coach,
  rounds, seat phases, deadline collection, and result construction. Per-seat
  state is isolated in `_AgentTurn`, not leaked across seats.
- `src/contest_prompts.py` owns agent-visible prompts and review projections;
  `src/contest_policy.py` owns action gating and routing;
  `src/contest_lifecycle.py` owns environment defaults and deadline helpers.
  These modules do not import the facade. All presets still use the same
  mechanics, budgets, checkpoint representation, and result representation.

The structural refactor originally kept protocol v5 behavior unchanged; the
current contract is v6. Twelve fixed-clock replays compare complete
prompt/event/checkpoint/result fingerprints for
decentralized, centralized, and OTC runs, covering math/programming and
fresh/resumed execution. As usual, source fingerprints change after edits,
so previously written experiment identities cannot be resumed as current code.
See [the original six-item repair checklist](pipeline-repair-checklist.md).

Contest actions use one provider-neutral `LLMRequest(tools=...)` /
`LLMResponse(tool_calls=...)` interface. With `--action-calling auto`,
Perplexity uses provider-native function calling and Tinker uses
schema-validated emulated function calling because the current Tinker sampling
SDK does not expose native custom functions or constrained JSON output. The
Tinker adapter renders the same function schemas into the prompt, validates the
sampled name, argument types, required fields, and enums, and performs at most
two bounded correction attempts. Those additional API calls and output tokens
are charged to the shared budget. Use `--action-calling prompt-json` only for
compatibility experiments.

The selected transport is recorded as `native`, `emulated`, or `prompt_json`
in the `action_calling` field of `contest_session.json`. Calls are also
preserved in `action_transport_log` with turn, agent, provider `call_id`,
function name, and validated arguments. Diagnostics include transport API
calls, retries, and terminal transport failures.

## Canonical tools: common versus specialized

`src/tool_registry.py` contains one canonical registry of 31 typed actions
(`ACTION_SET_VERSION = 5`). Every action has a name, description,
JSON-compatible argument schema, visibility, capability pack, budget semantics,
runtime handler marker, and a `runtimes` tag (`session`, `env`, or both). The
same definitions are used for provider function schemas, prompt instructions,
validation, and dispatch in **both** execution paths: the contest-session
runtime described in this document and the legacy per-problem
`OlympiadEnvironment` used by the `--schema` stack (see
*action_set_version=5* below and `docs/WORKBOARD_AND_TOOLS.md`).

All task families initially receive the **common** collaboration pack:

- `select_problem(problem_id)` selects or switches the shared active problem.
- `speak(content)` broadcasts a message to the team.
- `direct_message(recipients, content)` privately sends a message to one
  teammate or a named sub-group of teammates.
- `work(content, problem_id?)` records a durable answer or code draft; the
  optional `problem_id` switches to that task first when the agent may work it.
- `request_review(content, reviewer?)` asks for review but does not approve a
  version.
- `review_answer(problem_id, version_hash, decision, content)` independently
  approves or rejects an immutable answer version.
- `submit(answer)` submits a non-programming answer.
- `skip_problem(reason?)` leaves the current problem.
- `finish_contest(reason?)` ends a contest only when completion gates permit it.
- `rest(reason?)` passes the current agent action.

and the **desk** subset of the common pack (see *contest_session_v4* below):

- `inspect_problem(problem_id?, focus?)` reads any problem's statement and full
  version/review/submission history without moving the shared cursor.
- `triage_problem(problem_id, priority, reason?)` sets the team priority
  (`high | normal | low | hopeless`) used by the scheduler.
- `remember(content, problem_id?)` stores a private note.
- `recall(query?, problem_id?)` ranks the agent's notes and team-shared notes.
- `share_note(note_id)` publishes one of the agent's notes to the team.

Specialized actions are grouped into capability packs:

- **Math:** `use_calculator(expression)`.
- **Programming:** `execute_code(code, language?)` and
  `submit_code(code, language?)`. The former `verify(focus?)` is no longer a
  registered action; it is a legacy alias of `inspect_problem`, which covers
  self-verification for every family in both runtimes.
- **Research:** `web_search(query)`.
- **Physical resources:** `read_lab_equipment(resource?)` and
  `read_star_chart(resource?)`.

The initial specialized surface is resolved from competition, task type,
benchmark requirements, declared capabilities, and installed handlers:

- ICPC, IIOT, Codeforces, or programming/coding/algorithmic task types receive
  the programming pack.
- Purple Comet, Fyziklani, IJSO Practical, IOAA Group, IYPT, or
  math/proof/numeric task types receive the math pack.
- Fyziklani, MCM, ICM, IEO Business Case, Jessup, IYPT, or
  research/case-study/legal task types receive the research pack.
- A benchmark may explicitly request a known pack or individual action through
  its tool requirements or capabilities.
- Physical resource actions are never inferred from a broad task family. They
  require the exact declared capability and an installed handler.
- An action whose runtime handler is unavailable is omitted rather than shown
  to the model.

“Common” means shared across task families, not unconditionally visible on
every turn. The contest runner narrows the function list dynamically:

- `select_problem` is restricted to the acting agent's coach assignment and
  excludes the already-active problem.
- `direct_message` is available to multi-agent strategic teams, with the
  `recipients` item enum restricted to actual teammates other than the sender.
  Every named recipient receives it in the `direct_messages` inbox of their
  next prompt; `speak` remains the public broadcast channel.
- `review_answer` is exposed only for eligible non-author versions routed to
  that reviewer.
- Strategic programming removes `request_review`; authors must report a
  sample-AC run with `speak` before another agent reviews the exact version.
- Strategic `submit_code` appears only after local evidence and independent
  approval, and submits the frozen reviewed source without asking the model to
  reproduce it.
- `finish_contest` is hidden for both variants while any task lacks a valid
  submission (its handler would reject it anyway).
- Answer-sheet `submit` is gated until required drafts and reviews exist.
  Deadline collection is done by the environment after the loop, never by an
  in-loop model action.
- Desk actions (when the baseline includes them) stay available whenever the
  agent may act at all, including off-assignment turns in coach runs; only the
  two forced phases hide them (answer-sheet *submit-only* and programming
  *source-required*).

The no-coach presets (`single_agent`, `decentralized`) have no Coach, private
deliberation, review workflow, review gate, desk or memory tools, or
cross-problem strategic summary. They make one model call and execute at most
one public action per scheduled agent. `request_review` and `review_answer` are
hidden. After a new answer-sheet draft is recorded, contest control advances the
shared cursor to the first unseen task. The common stall guard also moves every
baseline away from an unchanged task; the no-coach presets' automatic moves are
reported separately as `baseline_mechanical_switches`.

All baselines receive the same contest rules and competition-specific base tool
packs; they differ only by the optional bundles in the table above. Actions
invalid under the contest's submission contract are hidden for everyone,
including incomplete answer-sheet submissions.

The structured presets add bounded contest memory, immutable answer versions,
stalled-task switching, and later revisits. OTC adds mandatory different-agent
review and evidence-bound code review. Centralized, but not OTC, enables the
three-non-AC cooldown; OTC instead uses its card's repair-demotion policy.
These are experimental system policies, not official ARML or ICPC rules.

Every task family can resolve `inspect_problem(problem_id?, focus?)`, but only
baselines with desk actions (`centralized` and `otc`) expose it. It returns the
statement, version chain (with sample reports for programming), review history
and submissions of the requested problem (default: the active one) as a private
tool event. It is self-verification context only, never satisfies the
independent-review gate, and never moves the shared cursor.

Every run writes `contest_session.json` and `contest_checkpoint.json`. The
result includes the frozen action set, shared budget ledger, task timeline,
latest valid per-task submissions, answer/review versions, visibility-tagged
memory, switch reasons, TaskUtility, AAR, AB, review coverage, attempts-to-AC,
stalled turns, and switch count. Live runs evaluate Communication, Planning,
and coordination score (CS) by default; `--no-judge-collab` disables this.
`--judge-cce` adds CCE for live runs.

Multi-problem non-programming contests use answer-sheet semantics: `work`
updates a per-problem draft and one argument-free `submit` atomically submits
the sheet and terminates the contest. Individual math problems are never
submitted mid-contest. OTC requires independent approval of every current
submitted version but no redundant whole-sheet final-review pass by default.
At session end, eligible pending non-programming drafts are collected without
another model call; OTC's approval gate is not bypassed and missing tasks remain
blank. Programming contests retain per-problem `submit_code` semantics.

Results record `protocol_version=contest_session_v6`,
`action_set_version=5`, and the effective deadline policy. Re-run old
experiments from fresh output directories when comparing protocols; do not mix
old checkpoints or scores with current results.
`run_competition_batch.py --resume` refuses a `contest_checkpoint.json` whose
`protocol_version` differs from the running code.

## Historical implementation notes (v2–v5)

The dated sections below document earlier implementations, not the current OTC
contract. For v6, the table above takes precedence: one turn-0 Coach, mandatory
current-version approval, and no review bypass at deadline or after rejection.
Vanilla and explicitly selected review-only ablations retain their own behavior.

### OTC programming workflow v2 (2026-09-08)

Reviewed strategic programming sessions additionally record
`programming_workflow_version=programming_workflow_v2`. Math, short-answer,
Vanilla, and explicitly review-disabled sessions retain their existing answer
semantics. Use fresh output directories for v2 comparisons; old ICPC runs
without this marker used the prior programming workflow.

In this programming workflow, `work` records discussion/analysis in memory and
never replaces candidate source. `execute_code` records complete source and
its sample evidence. After sample AC, the scheduler prioritizes the author
until the exact version is reported with `speak`, then routes independent
review and frozen-source submission. A review rejection still permits an
official submission; reviewers do not decide the official verdict.

`src/programming_workflow.py` tracks unproductive work actions per agent/task.
After `stall_turns` such actions (default 3), the task moves behind the worker's
other assigned tasks and remains eligible for later revisiting. Fresh failing
code versions and ordinary active-cursor changes do not reset this budget.
A newly sample-passing candidate, a local-run report, or a valid formal
submission resets it. Report/review/submission-ready code retains pipeline
priority. Infrastructure errors such as `JUDGE_ERROR` are not sample failures.
The counter and rotation order are persisted in memory and restored on resume.

`diagnostics.programming_repair_yields` counts these repair-budget yields
separately from the legacy round-based `stalled_turns` metric. Local sample
failures never increment the official non-AC submission counter or add penalty
minutes. Ordinary progress-accounting events are excluded from the limited
working-memory projection so they do not crowd out source and judge feedback.

An explicit `split_parts` request now fails if numbered prompts cannot be
matched to the requested part IDs. Appended numbered answer sections are
removed before either packet or split prompts are delivered. Deterministic
grading reports unavailable tasks separately, excludes them from score and
utility denominators, and records `evaluation_coverage`. A completely ungradable
session has `task_utility=null`, not an accuracy of zero.

Agent Python, local Python judging, and sample-output diagnostics use Docker
isolation. Only the submitted source is mounted; test input is streamed on stdin
and expected answers remain in the host evaluator. Containers have no network,
host environment, repository mount, or write access to the image. Time, memory,
process, and output limits apply. There is no automatic host fallback when
Docker is unavailable. The judge's `trusted_python=True` option is exclusively
for explicitly trusted fixtures; benchmark adapters do not use it.

### Docker isolation prerequisites

Code-enabled contests require a running Docker daemon and the pinned image
defined as `PYTHON_IMAGE` in `src/isolated_python.py`. Isolated runs invoke
`docker run --pull=never`, so the image must already be present on the host;
contest scripts do not start Docker Desktop and do not pull images at runtime.

Install the pinned image once per machine (or after the local image cache is
cleared):

```powershell
docker pull python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534
```

Confirm the daemon and image before a live run:

```powershell
docker info
docker image inspect python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534
e:\agent_olympiad\.venv\Scripts\python.exe -c "from isolated_python import run_python_isolated; print(run_python_isolated('print(42)').stdout)"
```

The smoke check must print `42`. If the digest in `PYTHON_IMAGE` changes, pull
that revision instead; do not substitute an unpinned `python:3.11-slim` tag.
Operational notes for the monorepo interpreter and remote-judge gateway live in
`docs/PYTHON_ENV.md`.

`--max-total-tokens` continues to mean a shared **output-token** budget, as its
CLI help states. It does not match total input-plus-output cost across systems.

Every answer version also has shared review history keyed by its immutable
`version_hash`. Agents can see the answer author, review decisions and comments,
and whether each review became stale after a revision. The complete untruncated
history is persisted as `shared_review_history` in `contest_session.json`.

The team keeps one global active-task cursor, but it is not an ownership lock.
Before a strategic live run, the pre-contest coach receives the task set, rules,
team size, and shared budget, then produces a persisted structured operational
brief with work assignments, review routes, task order, switch conditions, and
the final checklist. The coach may assign one problem per agent, group several
agents on one problem, or focus the whole team together. Each assignment is
copied into that agent's private memory. Before each call, the scheduler moves
the shared active-task cursor to the agent's next assigned work or review target;
task actions outside the assignment are rejected. The coach call consumes the
same API/token budget and is not repeated after checkpoint resume.
`request_review` creates a shared request when that action is enabled, while a
different agent uses `review_answer` with the exact problem and version hash.

Use `--resume` with the same explicit `--output` directory to resume its
checkpoint. A checkpoint is scoped to its session and system variant, so
vanilla and strategic memory cannot be reused across matched runs.

### Optional programming deadline submission

`--programming-deadline-submit` (default: off) enables controller-side code
collection after the last normal turn, or earlier budget exhaustion. It uses
no additional model calls or turns. For each unsolved programming task, it
selects one recorded nonempty source not previously attempted officially:
sample-AC candidates first, independently approved candidates as a tiebreaker,
then recency. This preserves a sample-AC candidate over a later sample failure.
An earlier WA/TLE does not exclude a genuinely new candidate. Analysis notes
are not code; blank tasks, accepted tasks, and active cooldowns are skipped.
Code identity ignores version-parent hashes, fences and outer whitespace, so
recreating an old failed source does not authorize another submission. Pending
or otherwise uncertain normal attempts also exclude their source; explicitly
local-only `SAMPLE_*` rejections do not. Sample AC is not proof of correctness.
Normal actions retain their sample and independent-review gates. Only this
controller-only deadline path waives those gates; official WA still incurs the
normal penalty. Pending, human-verification, sample-only, and failed responses
are not official acceptance.

This option does not alter mathematics or short-answer collection, and is
available to either variant as an explicit environment policy. Use the same
setting in matched comparisons. Results record
`deadline_policy=collect_pending_non_programming_drafts_and_unsubmitted_candidates_v2`,
`programming_deadline` before/after task lists, source hashes and judge results
in `programming_deadline_*` memory events, and separate deadline attempt/AC
counts. Write fresh experiment outputs: finalized checkpoints cannot be used
to retroactively enable submissions. Intent is checkpointed before each remote
call; interrupted or uncertain attempts are not automatically retried on resume
because the judge may already have received the code.

Regression coverage: `tests/test_programming_deadline.py`. This is a submission
safety net, not a remedy for agents failing to generate or repair source.

### OTC programming workflow v3 (2026-09-08)

Reviewed strategic programming runs now record
`programming_workflow_version=programming_workflow_v3`. Use fresh experiment
outputs instead of appending to v2 runs. Mathematics, short-answer, Vanilla,
and explicitly review-disabled flows retain their action rules.

- Ordinary sample/official-WA repair candidates and uncoded tasks follow the
  same worker rotation order. Uncoded tasks no longer override that order and
  indefinitely starve repairs. Ready sample-AC reporting, review, and submission
  retain their existing priority. The three-unproductive-action rotation still
  provides time for other assigned tasks.
- The active programming source is pinned in full, with its exact hash,
  matching sample report, reviews, and latest valid official submission.
  This block is outside the eight-event / 6,000-character general-memory
  projection. Shared history previews remain bounded.
- During implementation or failed-source repair, two own-task actions without
  a code execution/progress exhaust the analysis allowance. The next action on
  that task exposes only `execute_code` and explicitly asks for a complete
  stdin/stdout solver. Notes, rest, messages, verification, and manual switches
  cannot indefinitely replace source production. Counters are worker/task-local,
  persist across automatic rotation and checkpoint resume, and reset on a
  non-infrastructure code attempt (even sample WA) or real workflow progress.
  Empty source is rejected before execution. Sample-AC reporting, independent
  review, and submission are not subject to this source-production gate.
- `diagnostics.programming_source_required_actions` counts forced-source
  prompts; their controller events do not consume general working-memory slots.

These are execution-policy guarantees, not correctness guarantees. Nonempty
placeholder programs, hardcoded sample harnesses, and algorithmic mistakes can
still pass syntax checks or fail hidden tests. The independent-review override
and optional deadline submission policy have not been changed in v3.

Regression coverage: `tests/test_programming_productivity.py`, plus the existing
programming pipeline, family separation, and deadline-submission tests.

### Programming gap repairs v4 (2026-09-08)

Reviewed strategic programming runs now record `programming_workflow_v4`.
Use fresh outputs instead of resuming old experiments across this policy change.
Only the requested checker, duplicate-execution and deadline-selection gaps
are changed; task-wide budget limits and counterexample tools are not added.

- The ICPC 2012 Infiltration legacy sample adapter uses a semantic checker:
  optimal cardinality from the trusted answer, unique in-range cells, correct
  case labels, and direct domination of every input vertex. It accepts different
  valid optimal sets and arbitrary identifier order, not merely reordered text.
  Other legacy problems retain token checking; configured official packages
  keep their own checkers. This public judging correction applies equally to
  both variants, not to mathematics or short-answer grading.
- Reviewed OTC programming reuses a known failed result when source, language,
  task metadata, local samples and judge-code identity match. The saved public
  sample results support reuse across agents and checkpoint restoration without
  re-executing code or creating a version. It does not overwrite the active
  source, grant evidence, or reset source/progress counters. Failures of the
  infrastructure, unknown results and successful runs are not cached. Bundled
  judges with untracked dependencies opt out; source/test changes cause real
  execution. Vanilla, non-programming and review-disabled flows do not receive
  this strategic deduplication policy. Injected custom executors should expose
  `execution_context_key(task)` (return `None` to opt out); otherwise their
  benchmark metadata is assumed stable for the run.
- Results separately count `programming_duplicate_executions_avoided`; cached
  execute attempts still use their ordinary agent turn and model budget. They
  save sandbox work and make the required repair explicit, not refund tokens.
- The explicit deadline policy above records both the selected historical hash
  and the final submitted hash, source identity and selection reason. It keeps
  one checkpointed deadline intent per task and never retries an interrupted
  deadline call. Both variants receive this policy only when explicitly enabled.

Regression coverage: `tests/test_programming_gap_repairs.py` and the existing
deadline, productivity, contest-family and variant suites.

### contest_session_v4: desk actions (2026-09-10)

Results now record `protocol_version=contest_session_v4` and
`action_set_version=2`; the on-disk `contest_checkpoint.json` carries the same
stamps and `--resume` refuses a mismatch. Start fresh output directories.

This revision ports the useful interface ideas of the legacy workboard /
workspace actions (`open_problem`, `mark_hopeless` + `set_priority`,
`remember` / `recall` / `publish_memory`, `message_group`, the duplicate
`submit_problem` rejection) into the contest session as typed actions. State
stays in `ContestSession` (immutable versions, reviews, submissions, now also
per-task triage) and `ContestMemory` (event ledger); no `Workboard` or
`MemoryStore` object is introduced, and the legacy `--schema` stack is
unchanged.

- **Desk actions** `inspect_problem`, `triage_problem`, `remember`, `recall`,
  `share_note` are in the common pack. Which baseline sees which bundle is
  decided by the preset table in *Baselines* above (initially v4 gave all of
  them to both variants; the five-baseline revision the same day split them
  into the `desk` and `memory` switches and removed them from the no-coach
  presets). They are not gated by the Coach's work/review assignment; only the
  answer-sheet submit-only phase and the programming source-required phase hide
  them. Every desk call uses one seat action and one API call inside the already
  charged global contest round; turns are charged once per round, not per seat.
- `inspect_problem(problem_id?, focus?)` replaces the programming-only
  `verify`: a private `inspect_problem_result` event with statement, versions
  (content clipped to 2 000 chars, sample and author reports), reviews and
  submissions. It never moves the shared cursor, so agents can look at a
  teammate's problem without `select_problem`.
- `triage_problem(problem_id, priority, reason?)` writes `TaskUnit.priority /
  triage_reason / triaged_by / triaged_turn` and a public `task_triaged` event.
  `_scheduled_agent_task` stable-sorts the agent's work list by priority
  (high → normal → low → hopeless) inside the Coach's `task_order`; `_next_task`
  and the vanilla next-unseen pick use the same order. Hopeless problems are
  never removed: their latest draft is still collected at the deadline.
- `remember(content, problem_id?)` is the note itself (private `note` event
  tagged with the problem). `recall(query?, problem_id?)` returns a private
  `recall_result` ranked exactly like the legacy `MemoryStore.recall`: problem
  tag → query-term hits → recency, deduplicated by content. `share_note(note_id)`
  copies one of the caller's notes to a public `note_shared` event
  (`source_event_id` kept); sharing someone else's note or sharing twice is an
  `action_error`. The strategic projection gains `recent_notes` (≤ 4, notes not
  already shown under the current task), problem digests include notes, and
  vanilla sees notes through its ordinary 12-event window.
- `direct_message(recipients: [Agent_N, …], content)` accepts one or more
  teammates (deduplicated, sender excluded); the projection field is now
  `direct_messages[].recipients`.
- A `work` whose content equals **any** earlier version of the task no longer
  silently no-ops: no version is created and the author gets a private
  `work_duplicate` event naming the existing version, its author, the turn it
  was recorded and the still-blank task ids. `BUDGET` in the prompt also lists
  `blank_tasks`; `TASK STATUS` rows add `versions`, `priority`, `hopeless`,
  `triaged_by`.
- Housekeeping: `finish_contest` is hidden for both variants until every task
  is complete (previously vanilla exposed it and the handler rejected it), and
  the dead in-loop `deadline_submit` branch is removed; deadline collection
  remains the environment's job after the loop.
- Diagnostics add `inspect_count`, `notes_recorded`, `notes_shared`,
  `recall_count`, `triage_changes`, `items_hopeless`, `repeat_draft_attempts`;
  `scripts/_export_paste_tabs_3_6.py` (per-session tabs) and
  `scripts/posthoc_icpc_metrics.py` export them as
  `protocol, inspect, notes, notes_shared, recalls, triage, hopeless,
  repeat_drafts`.

Not ported, by design: `list_problems` (TASK STATUS already injected),
`claim_problem` / `release_problem` (Coach assignment + runtime enforcement),
legacy `verify_problem` (`review_answer` binds a `version_hash`),
`check_budget` (BUDGET injected), and the deliberation actions.

Regression coverage: `tests/test_tool_registry.py`, `tests/test_contest_memory.py`
(recall, recent notes, multi-recipient inbox) and `tests/test_contest_runner.py`
(inspect without cursor move, note round trip, triage scheduling and deadline,
duplicate-draft feedback, desk availability per baseline/phase, shared core
action set, centralized leader/worker gating, live reassignment and its resume
replay, alias canonicalisation and team-size rules). `src/run_contest_smoke.py`
produces the same deterministic matched-pair outcomes as v3 and as the
pre-refactor v4.

### action_set_version=5: one registry for both runtimes (2026-09-10)

Results now record `action_set_version=5`. The contest-session protocol itself
is unchanged (replay fingerprints in `tests/test_contest_engine_replay.py` were
recaptured only because `work` gained an optional `problem_id` argument in
every variant); the revision unifies the legacy `OlympiadEnvironment` action
set with this registry so that the `--schema` stack and the contest-session
stack share one action vocabulary.

- **Runtime tags.** Each `ActionSpec` carries `runtimes`; `actions_for_runtime`
  yields 27 actions for `session` and 28 for `env`, 24 shared. Session-only:
  `assign_problem`, `request_review`, `finish_contest`. Env-only packs
  `workboard` (`verify_problem`) and `workspace` (`check_budget`,
  `query_rules`, `write_private_notes`) exist because the session runtime
  injects TASK STATUS / BUDGET and pins reviews to a version hash instead.
- **Legacy names are aliases, not actions.** `LEGACY_ALIASES` maps
  `sleep→rest`, `submit_final→submit`, `write_scratchpad`/`submit_problem→work`,
  `claim_problem→select_problem`, `release_problem→skip_problem`,
  `list_problems`/`open_problem`/`verify→inspect_problem`,
  `set_priority`/`mark_hopeless→triage_problem`, `publish_memory→share_note`,
  `message_group→direct_message`, including positional field mapping for the
  `a | b | c` text payload. Old rule cards, transcripts and mock outputs still
  parse; logs record the canonical `action` plus `invoked_as`.
- **One wire parser.** `src/action_wire.normalize_invocation` turns a typed
  dict or a text payload into the same `Invocation`; `env.execute_action`
  accepts both.
- **Handler tables replace the if-chains.** `OlympiadEnvironment._HANDLERS`
  and `contest_actions.SESSION_HANDLERS` are keyed by canonical name;
  `env.unimplemented_actions()` must stay empty.
- **Env gains session semantics.** `review_answer` is implemented against
  `Workboard.answer_hash` (`inspect_problem` prints `Recorded version:`);
  `inspect_problem` without a `problem_id` returns the board overview, or the
  code / run history in a programming contest.
- **Prompts are rendered from the registry** (`actions.build_action_instructions`),
  so the legacy prompt now advertises `work`, `rest`, `submit` and the desk
  actions under their canonical names.

## Verification and retired coverage

The removed per-problem OTC tests targeted a retired protocol (including its
turn-2 exit and legacy synthesis). Current stage/access/action/lease/latency
coverage lives in `tests/test_otc_rulecard.py`; canonical aliases, fail-closed
migration, and module boundaries are covered by `tests/test_otc_migration.py`.
Shared review/cooldown/source-gate tests remain as explicit feature ablations
in `tests/contest_feature_fixtures.py`, using the centralized planner where an
opening plan is needed. They are not OTC or Vanilla benchmark presets.

`grade.graded` means every task was evaluable. Partial or wholly unsupported
grading reports `graded=false`; unavailable tasks do not enter the score
denominator, and wholly unsupported sessions keep `task_utility=null`.
