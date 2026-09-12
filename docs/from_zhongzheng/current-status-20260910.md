<!-- markdownlint-disable MD060 -->

# Contest-session pipeline

> Protocol `contest_session_v6`, action set version 5. This is the
> implementation that `run_competition_batch.py --contest-manifest` runs.
> How to invoke it: [benchmark-runbook.md](benchmark-runbook.md).
> Action contract: [actions-reference.md](actions-reference.md).
> Baseline / OTC card contract: [../contest-systems.md](../contest-systems.md).

## 1. What a run is

One run is one **contest session**: several tasks, a fixed roster, one shared
clock, one shared API-call budget, one shared output-token budget, a typed
action surface, and an append-only event ledger.

The engine does not branch on the baseline name. It branches on
`BaselineFeatures` in `src/contest_config.py`. `--system-variant` only selects
a named row of those switches.

```text
source PDFs / archives
        |
        v
collectors/*  -->  data/benchmarks/<competition>/benchmark.json
                      + data/rules/<competition>/collaboration.json
                      + programming package / samples when present
        |
        v
data/contest_manifests/*.json
        |
        v
contest_manifest.load_contest_manifest()
        |   strips answer/solution leakage from prompts
        |   builds ordered ManifestTask values
        v
run_competition_batch.py
        |   resolve baseline, roster, clock, API/token limits
        |   load and validate the rule card when the baseline requires it
        |   resolve capability packs and action transport
        |   write run_config.json (fingerprint) before any model call
        v
contest_engine._ContestEngine
        |   optional turn-0 Coach or leader plan
        |   for each contest round:
        |       charge 1 turn + simulated minutes
        |       deliver any due delayed verdicts
        |       for each seat in roster order:
        |           resolve focus and legal actions
        |           optional private think call(s)
        |           one typed action
        |           validate, apply, append events, checkpoint
        |   deadline collection
        v
grade + process metrics
        |
        v
contest_session.json  +  contest_checkpoint.json  +  run_config.json
```

Authoritative modules:

| Piece | Module |
|---|---|
| CLI, provider, identity | `src/run_competition_batch.py` |
| Baseline presets and run config | `src/contest_config.py` |
| Manifest → tasks | `src/contest_manifest.py` |
| Clock, seats, think, action, deadline | `src/contest_engine.py` |
| Legal action surface | `src/contest_policy.py` |
| Action handlers | `src/contest_actions.py` |
| Prompts and projections | `src/contest_prompts.py` |
| Task / version / review / submission state | `src/contest_session.py` |
| Event ledger and working-memory view | `src/contest_memory.py` |
| Typed action contract | `src/tool_registry.py` |
| OTC card → runtime policy | `src/rulecard_policy.py`, `src/otc_runtime.py` |
| Verdict delivery, task grading | `src/contest_judging.py`, `src/contest_adapters.py` |
| Deadline collection, scoreboard, participation metrics | `src/contest_lifecycle.py` |
| Fingerprint | `src/contest_run_identity.py` |

Two stores sit side by side for the whole session:

- **`ContestSession`** — mutable contest state: tasks, immutable answer
  versions, reviews, submissions, locks, the shared budget ledger.
- **`ContestMemory`** — append-only events. Agents never see this archive
  whole. They see a visibility-filtered, size-bounded projection.

## 2. Settings

Settings come from three places, applied in this order: CLI defaults, the
competition's official duration / roster / card, then explicit CLI overrides.
The resolved object is `ContestRunConfig`. Its content hash, the card hash,
the manifest hash, and every `src/*.py` hash go into `run_config.json` before
the first model call.

### 2.1 The contest manifest

A manifest turns benchmark rows into one contest. Minimal form:

```json
{
  "session_id": "arml_local_2012",
  "competition_id": "arml_local",
  "problem_ids": ["arml_local_2012"],
  "split_parts": true,
  "question_ids": ["1", "2", "3"]
}
```

- Every `problem_id` must exist in
  `data/benchmarks/<competition_id>/benchmark.json`.
- `split_parts: true` splits one packet row into per-question tasks using its
  `gold_label.parts`; `question_ids` optionally selects a subset. Unknown ids
  fail loading.
- `contest_manifest.load_contest_manifest` strips trailing answer/solution
  sections from problem text before agents ever see it, and builds ordered
  `ManifestTask` values (`task_id`, `question_id`, `prompt`, `max_score`,
  `programming`).
- Any other key (for example `task_family`,
  `competition_description`) lands in `metadata` and is echoed into prompts.

**Task family** routes the contest into a domain workflow (which prompt
workflow text and which tool packs apply). Values:
`programming`, `mathematics`, `short_answer`, `puzzle`, `general`, `mixed`.
The manifest's `task_family` overrides; otherwise the competition id decides
(ARML/HMMT/Purple Comet/WMTC → mathematics; Science Bowl/QANTA/History
Olympiad → short_answer; Mystery Hunt → puzzle), else it is inferred from the
tasks' types.

### 2.2 CLI (`--contest-manifest` path)

| Flag | What it sets |
|---|---|
| `--contest-manifest PATH` | The contest. Required for this pipeline. |
| `--system-variant` | `single_agent`, `decentralized`, `centralized`, `vallina_otc`, or `otc`. Default `otc`. |
| `--team-size N` | Roster size. `single_agent` is forced to 1. For `otc`, omit this and the card's default roster is used; an explicit value must sit in the card's min/max. |
| `--max-turns N` | Contest rounds. Default is official duration / 5 minutes, capped at 90 (ARML Local 45 min → 9). |
| `--max-api-calls N` | Shared orchestration-call ceiling. For the card baselines (`otc`, `vallina_otc`) the default is `turns × team × (1 + private_think_calls) + 1` (the extra 1 is the Coach). |
| `--max-total-tokens N` | Shared **output-token** ceiling. |
| `--max-simulated-minutes N` | Simulated clock. Default is `max_turns × minutes_per_turn` (5 min). |
| `--max-output-tokens N` | Per-call generation cap. Default from the contest registry, else 8192. |
| `--start-seat K` | Rotates who acts first. Order inside a round stays fixed. |
| `--action-calling` | `auto` / `native` / `emulated` / `prompt-json`. |
| `--live`, `--provider`, `--model`, `--temperature` | Model transport. |
| `--judge-task` / `--judge-collab` | Default on when `--live`. |
| `--judge-cce` | Off unless requested. Judge calls cost money but are **not** charged to `budget.api_calls_used`. |
| `--judge-provider`, `--judge-model` | Judge identity. |
| `--programming-deadline-submit` | At the end, submit one eligible recorded source per never-officially-submitted programming task. |
| `--require-review` / `--require-final-review` | Override the baseline's review switches. |
| `--rules-mode` | Default `enforced` for the card baselines (`otc`, `vallina_otc`), `off` otherwise; card baselines reject anything but `enforced`. |
| `--rules-root`, `--rules-strict` | Card location and fail-closed missing-card behavior. |
| `--output`, `--resume` | Fresh directory, or reuse an exactly matching fingerprint / checkpoint. |

`--resume` skips an identical finished result, continues an identical
checkpoint, and refuses a changed config, card, manifest, protocol, or source
tree.

### 2.3 `ContestRunConfig`

| Field | Default / rule |
|---|---|
| `system_variant` | Canonical baseline name |
| `team_size` | Positive integer; 1 for `single_agent`; ≥ 2 for `centralized` and `otc` |
| `max_turns` | Positive integer |
| `max_api_calls` | Optional shared cap |
| `max_tokens` | Optional shared output-token cap |
| `max_simulated_minutes` | Optional simulated clock |
| `minutes_per_turn` | `5.0` |
| `consecutive_non_ac_limit` | `3` |
| `cooldown_turns` | `2` |
| `stall_turns` | `3` |
| `require_review` | `None` → follow `features.review_workflow` |
| `require_final_review` | `None` → review baselines except `otc` (OTC has no extra whole-contest final-review pass) |
| `start_seat` | `0` |
| `rule_guidance` | Public rule text when a card is shown but not the OTC driver |
| `programming_deadline_submit` | `False` |
| `features` | The preset row, unless an ablation overrides switches |
| `rule_card` | Required when `features.rule_card != "off"` |
| `otc_policy` | Derived from the card when `coach == "card"`; callers never set it |

Budget accounting inside the engine:

- **Turn** — one outer contest round. Charged once per `_run_round`.
- **API call** in `budget.api_calls_used` — one orchestration request:
  Coach, leader plan, each private think, each seat action, each emulated
  correction. Post-run judges are not added here.
- **Tokens** — model output tokens, shared across the session.
- **Simulated minutes** — `minutes_per_turn` per round, plus programming
  penalties. Wall time is recorded and is not the contest clock.

### 2.4 The five baseline names, and what is actually shipped

`--system-variant` has **five** canonical presets. The five-way split maps
onto them one to one.

| Requested baseline | Shipped? | `--system-variant` | What you get |
|---|---|---|---|
| single agent | yes | `single_agent` | Same no-coach environment as decentralized; `team_size` pinned to 1; no review, desk, memory, or private channel |
| decentralized | yes | `decentralized` | Flat rotating open table; same feature switches as single-agent, roster ≥ 1 |
| centralized | yes | `centralized` | `Agent_1` plans, reassigns, and alone submits; desk + private channel; **no** `remember` / `recall` / `share_note` |
| open table coach + rule card | yes | `vallina_otc` (alias `vanilla_otc`) | Basic OTC ablation: turn-0 blind Coach, enforced rule card, desk; **no** review, memory actions, private channel, or deliberation; only the current turn's private thought is kept |
| open table coach + rule card + memory | yes | `otc` | Full OTC: enforced rule card, turn-0 Coach, independent review, desk, private channel, **and** `remember` / `recall` / `share_note` |

`open_table_coach` and `open_table_coach_memory` are CLI aliases for the full
`otc`; `vanilla_otc` is the alias for `vallina_otc`. `vallina_otc` is a fixed
baseline: `ContestRunConfig` rejects any feature override or forced review on
it. Details: [../vallina-otc.md](../vallina-otc.md).

`BaselineFeatures` is the switchboard the engine actually reads:

| Switch | `single_agent` | `decentralized` | `centralized` | `vallina_otc` | `otc` |
|---|---|---|---|---|---|
| `coach` | none | none | leader (`Agent_1`) | card (turn-0 Coach) | card (turn-0 Coach) |
| `review_workflow` | no | no | no | no | yes |
| `memory_actions` | no | no | no | no | yes (`remember` / `recall` / `share_note`) |
| `desk_actions` | no | no | yes | yes | yes |
| `private_channel` | no | no | yes | no | yes |
| `structured_context` | no | no | yes | no | yes |
| `submission_cooldown` | no | no | yes | no | no |
| `mechanical_switch` | yes | yes | no | no | no |
| `leader_submits` | no | no | yes | no | no |
| `rule_card` | off | off | off | enforced | enforced |

`single_agent` and `decentralized` use the same switches. The only difference
is team size. `coach="card"` with review and memory both off is what the code
calls `basic_open_table` (`BaselineFeatures.basic_open_table`); the engine
uses that property, not the name, to select the basic-OTC behaviour below.

What those switches mean in the engine:

- **`coach=none`** — no opening plan. Seats rotate. After `work`, a
  mechanical cursor can advance to the next blank task. Stall after
  `stall_turns` also advances the cursor.
- **`coach=leader`** — before the clock, `Agent_1` writes a plan. Each
  worker's work list is enforced. Only `Agent_1` may `submit` /
  `submit_code` / `finish_contest` / `assign_problem`. `Agent_1` opens every
  later round.
- **`coach=card`** — one problem-blind Coach brief at turn 0 (one API call,
  zero contest turns). No later Coach call and no enforced assignment. Each
  seat keeps its own focus. Under `otc`, independent review of the current
  hash is mandatory and deadline collection does not bypass that gate.
- **`basic_open_table`** (`vallina_otc`) — same card-driven world, minus the
  collaboration machinery. A pure overlay (`src/basic_otc.py`) is applied on
  top of the competition's card without mutating it: discussion policy
  cleared, `deliberation` forced to `none`, `min_challenges=0`, private think
  history cut to the current turn, review requirement off, action bundles
  fixed to `common` + `desk` + `competition_tools`. The prompt card is marked
  `basic_otc_ablation_not_official_competition_rule`. Review actions,
  memory actions, `direct_message`, and the deliberation pack are all hidden;
  deadline collection takes current drafts without an approval gate.

### 2.5 OTC card settings that become runtime

Both card baselines read `data/rules/<competition>/collaboration.json`
through `rulecard_policy.open_table_policy`; `vallina_otc` then applies the
`basic_otc` overlay described in §2.4. The card, not the engine, decides:

| Card field | Runtime effect |
|---|---|
| `team_size_min/default/max`, `agent_roles[].may_submit` | Roster and who may submit |
| `simulation.open_table_coach.precontest_brief` (`turn=0`, `problem_access=false`) | One blind Coach brief |
| `opening_discussion.enabled=false` | No second Coach call |
| `contestant_turn_policy.private_think_calls_per_turn` | Private think API calls before the public action (ARML Local: 1) |
| `max_chars_by_action` | Clip `think` / `work` / `speak` / `rest` (and mapped message actions) |
| `memory_entries` | Projection windows (see §6) |
| `discussion_policy` | Prompt rules; after `silent_work_turns` consecutive work-only turns, only discussion (+ desk read-only) remains |
| `communication` (`limited`) | Team and per-agent message counts; `max_message_chars` |
| `deliberation.mode == "structured"` | Adds `propose` / `challenge` / `provide_evidence` / `revise` / `decide` |
| `min_turns` | Hide contest-ending actions until that turn |
| `exclusive_workstation_lease` | One team-global keyboard for `execute_code` / `submit_code` |
| `run_judging_latency_turns` | Official verdict stays controller-private until that round |
| `repair_budget_after_rejected_run` | After an official rejection, N sample-failing new sources drop priority |

ARML Local card values, as an example: 6 contestants, 9 turns, 1 private think
per seat, think/work 2400 chars, speak 320, rest 80, memory windows
`private_think_per_agent=3`, `shared_work=18`, `group_messages=12`,
`public_messages=24`, team message budget 60 / 10 per agent / 1200 chars.

Thirteen competitions ship `otc_turn0_review_v1`: `arml_local`,
`arml_national_team`, `science_bowl`, `qanta`, `history_olympiad`,
`purple_comet`, `hmmt_guts`, `wmtc`, `mystery_hunt`, `icpc`, `codeforces`,
`nyu_ctf_bench`, `cfa_research_challenge`.

## 3. One contest, seat by seat

`_ContestEngine.run()`:

```text
_prepare_coach()                          # OTC brief or centralized plan
for round in 1..max_turns:
    charge 1 turn + minutes_per_turn
    deliver due delayed verdicts
    write a public scoreboard event
    for agent in roster (start_seat rotation; leader first if centralized):
        _prepare_agent     # focus, legal actions
        _build_agent_prompts
        _request_action    # exactly one typed call
        _apply_agent_action
    optional stall / mechanical switch
    persist checkpoint
deadline collection
build result
```

### 3.1 Focus

- **OTC / `vallina_otc`:** each seat's last `select_problem` (or
  `work(problem_id=...)`) stands. Otherwise the seat considers the
  scheduler's next blank problem.
- **Centralized:** the engine moves the shared cursor onto the scheduled work
  or review task for that seat.
- **Decentralized / single-agent:** shared cursor; `work` can advance it
  mechanically; stall after `stall_turns` with no new version or submission
  also advances it.

### 3.2 A seat turn

1. Resolve the legal `ActionSpec` set (`contest_policy._actions_for_agent`).
2. If a card baseline and the card asks for private think: charge one API
   call per think, build a think-only system prompt, write a private `think`
   event, clip to the card limit. Think is **not** an action and is not a
   function call. Under `vallina_otc` no think history is carried between
   turns; only the current turn's thought reaches the action prompt.
3. Charge one API call for the public action.
4. Build system + user prompts. Offer only the remaining legal functions.
5. Transport (`auto` / `native` / `emulated` / `prompt-json`) must return
   exactly one validated `{action, arguments}`. Extra tool calls are logged
   and dropped. Emulated retries are charged to the shared budget.
6. Card rules may clip text or reject the action (message budget, lease,
   deliberation ids). A rejected action still spends the turn and writes
   `action_error`.
7. The handler mutates `ContestSession` and appends events. A checkpoint is
   written after accepted state changes.

### 3.3 Deadline

When the loop ends:

- Answer-sheet contests collect current drafts that pass the baseline's
  gates. Full OTC collects only independently approved current versions;
  `vallina_otc` and the non-review baselines collect the current draft as-is.
  Missing or ineligible answers stay blank. No extra model call.
- Programming: `--programming-deadline-submit` may send one recorded source
  per never-officially-submitted task. OTC still requires current approval
  and sample evidence. Candidate order is sample-AC, then approval, then
  recency; the same program is not resent.
- Delayed ICPC verdicts are flushed.

## 4. Actions

`src/tool_registry.py` is the single contract: name, JSON schema, visibility,
capability pack, budget semantics, which runtime implements it. The
contest-session runtime implements the actions below. An action being
registered does not mean a seat sees it this turn.

Resolution order:

1. session runtime (not the environment runtime);
2. common pack, plus inferred or declared task packs;
3. baseline feature switches;
4. OTC card bundles and role permissions;
5. current focus, review, submission, lease, message budget, deliberation
   state, and remaining budget.

The model receives that narrowed function list. If it still violates a
precondition, the engine records `action_error` and spends the turn.

### 4.1 Visibility on the wire

| Registry value | Meaning |
|---|---|
| `private` | Event visible to the actor and named recipients |
| `team` | Shared with the team (stored as public on the ledger) |
| `contest` | Contest-control state |

### 4.2 Common contest actions

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `select_problem` | `problem_id` | contest | Change this seat's focus |
| `work` | `content`, optional `problem_id` | team | Write an immutable answer version; optional id switches and writes in one step |
| `skip_problem` | optional `reason` | contest | Leave current focus |
| `rest` | optional `reason` | private | Spend the action without changing work |
| `finish_contest` | optional `reason` | contest | End only when completion gates pass |
| `speak` | `content` | team | Public broadcast |
| `direct_message` | `recipients[]`, `content` | private | Message named teammates |
| `request_review` | `content`, optional `reviewer` | team | Ask for review; does not approve. OTC hides this because new versions enter the queue automatically |
| `review_answer` | `problem_id`, `version_hash`, `decision`, `content` | team | Approve or reject another author's **current** hash |
| `submit` | `answer` in the registry; OTC/answer-sheet often becomes argument-free | team | Hand in a non-programming answer or the whole sheet |
| `inspect_problem` | optional `problem_id`, optional `focus` | private | Read statement, versions, reviews, submissions; does not move focus |
| `triage_problem` | `problem_id`, `priority`, optional `reason` | team | `high` / `normal` / `low` / `hopeless` |
| `remember` | `content`, optional `problem_id` | private | Append a private note |
| `recall` | optional `query`, optional `problem_id` | private | Search own notes and shared notes |
| `share_note` | `note_id` | team | Publish one of the actor's notes |
| `assign_problem` | `agent`, `problem_ids[]`, optional `reason` | team | Centralized leader only: replace a worker's work list |

`work` is the durable candidate. Notes go to `remember`. Talk goes to `speak`
or `direct_message`.

OTC review rules: no self-review; hash must be current; revision stales older
reviews; a current rejection blocks submission; `submit` appears only when
gates pass.

### 4.3 Structured deliberation (card-only)

Offered only when the OTC card sets `deliberation.mode == "structured"`.

| Action | Arguments | Effect |
|---|---|---|
| `propose` | `content`, optional `problem_id` | Open a numbered proposal |
| `challenge` | `proposal_id`, `content` | Object to another author's open proposal |
| `provide_evidence` | `proposal_id`, `content` | Attach a check, derivation, or counterexample |
| `revise` | `proposal_id`, `content` | Author replaces the claim |
| `decide` | `proposal_id`, `outcome`, `reason` | Card-designated decision maker accepts, rejects, or defers |

Follow-up ids are pinned to open proposals. The author cannot challenge their
own proposal. Only the author revises. Only the decision maker decides. The
card can require `min_challenges` before answer-sheet `submit`.

### 4.4 Who sees which bundle

| Bundle | single-agent | decentralized | centralized | `vallina_otc` | OTC |
|---|---|---|---|---|---|
| Navigation, `speak`, `work`, `rest` | yes | yes | yes | yes | yes |
| `direct_message` | no | no | yes | no | yes |
| `inspect_problem`, `triage_problem` | no | no | yes | yes | yes |
| `remember`, `recall`, `share_note` | no | no | no | no | yes |
| `review_answer`, `request_review` | no | no | no | no | yes |
| `assign_problem` | no | no | leader only | no | no |
| Deliberation pack | no | no | no | no | card |
| Competition tools (§5) | task | task | task | task + card | task + card |
| Who may submit | acting seat | acting seat | `Agent_1` only | card `may_submit` roles | card `may_submit` roles |

### 4.5 Transport and legacy names

The same `ActionSpec` schemas drive every transport. `--action-calling auto`
uses native provider function calling where available and schema-validated
emulation otherwise; `emulated` renders the schemas into the prompt, parses,
validates, and retries within a bounded correction budget (charged to the
shared budget); `prompt-json` is the strict-JSON compatibility mode. Only the
first validated call executes.

Legacy wire names (`sleep`, `submit_final`, `write_scratchpad`,
`submit_problem`, `message_group`, `mark_hopeless`, …) normalize to canonical
actions at the boundary; the ledger stores the canonical name plus
`invoked_as`. Full table:
[actions-reference.md](actions-reference.md#8-legacy-only-actions-and-aliases).

## 5. Tools

In this codebase **tools** are the contest-instrument packs, not the whole
action list. `TOOL_PACKS = {math, programming, research, resources}`. Desk
actions (`inspect` / `triage` / memory) are the contestant's desk, not
instruments.

Packs are inferred from the task family or declared on the manifest / card.
A pack being inferred still respects the contest allowlist: an ARML math
packet does not get `use_calculator` when the card forbids electronics.

Handlers live in `contest_actions._session_task_tool`. The tool runs, then a
`{action}_result` event is appended (`private` for execute/calculator/search,
`public` for `submit_code`). Agents see that result only through the next
projection, not as a hidden side channel.

### 5.1 Math — `use_calculator`

| Argument | Effect |
|---|---|
| `expression` | Safe AST arithmetic. Private result. |

### 5.2 Programming — `execute_code` / `submit_code`

| Action | Arguments | Effect |
|---|---|---|
| `execute_code` | `code`, optional `language` | Isolated runner. On a programming task, official samples are executed and compared. Only sample-AC is local evidence. |
| `submit_code` | `code`, optional `language`; review/leader paths often take no source | Send frozen source to the local/remote judge |

Programming path under review (OTC and any `review_workflow` programming
session):

1. `execute_code` records an immutable source version and sample evidence.
2. Failed executions are reused when source + language + task + judge
   fingerprint match, so the same failing program is not re-run.
3. Another seat reviews that exact hash.
4. `submit_code` sends the frozen reviewed source. The model is not asked to
   paste it again.
5. The adapter returns or queues the official verdict. OTC ICPC cards can
   hold the verdict controller-private for `run_judging_latency_turns`.
6. `SAMPLE_WA` / `SAMPLE_RE` are local and are not remote attempts.

The workstation lease, when the card enables it, is team-global: the last
seat that executed or submitted holds `execute_code` / `submit_code` for two
turns, including across problem switches. Other seats can still inspect,
review, and talk.

Remote judging uses the localhost VJudge gateway and/or a direct Kattis
client. Cookies and `.kattisrc` never enter prompts.

### 5.3 Research — `web_search`

| Argument | Effect |
|---|---|
| `query` | Installed permitted search handler. Private result. |

Only contests whose card / allowlist grant research see this.

### 5.4 Declared resources

| Action | Effect |
|---|---|
| `read_lab_equipment` | Read an explicitly declared lab fixture |
| `read_star_chart` | Read an explicitly declared astronomy fixture |

These are never inferred from “the task looks scientific.” The benchmark or
card must declare the capability and a handler must exist.

## 6. Memory

Memory is not a vector store and not a separate `MemoryStore` object. It is
the same append-only ledger that records every speak, work, think, note, and
tool result.

### 6.1 Event record

`ContestEvent` fields:

```text
event_id          event-000001, event-000002, ...
run_id, session_id, competition_id
task_id, question_id
actor             seat name, Contest_Control, Contest_Scheduler, Tool, Coach
visibility        public | private | group | judge
recipients        extra viewers (required for group; used for private fan-out)
kind              speak, work, note, think, recall_result, ...
payload           JSON object
turn              current contest turn
```

Visibility rules (`ContestMemory._can_view`):

| Visibility | Who can see it |
|---|---|
| `public` | Every contestant |
| `private` | Actor and named `recipients` |
| `group` | Actor and anyone in a matching recipient group |
| `judge` | Judge viewers only |

Forbidden payload keys (`answer_key`, `gold`, `hidden_test`, `oracle`,
`secret`, …) are stripped on digest / sanitise. Forbidden event kinds
(`gold_answer`, `hidden_tests`, `judge_feedback`, …) never enter a digest.

### 6.2 How notes are written

| Agent action | Ledger kind | Visibility | Payload |
|---|---|---|---|
| `remember` | `note` | private, recipients = the actor | `{content, problem_id}` |
| `recall` | request event `recall`, then `recall_result` from actor `Tool` | private | Ranked notes, or empty |
| `share_note` | `note_shared` | public | `{content, problem_id, author, source_event_id}` |
| private think (not an action) | `think` | private | `{content, compacted}` |

`remember` **is** the note: the handler is a no-op after the event is
appended (`_session_noop`). `share_note` looks up `note_id` among the actor's
own `note` events, refuses a second share of the same id, and copies the
content into a public `note_shared`. `recall` ranks the viewer's own notes
and team-shared notes: exact `problem_id` first, then query-term hits, then
recency; identical content is collapsed. Default `top_k` is 8. The result is
a private `recall_result` the actor will see on the next projection.

Think events are excluded from `strategic_projection`'s current-task window.
They come back only through the dedicated think ledger (newest last, length
`memory_entries.private_think_per_agent`).

### 6.3 How the ledger is stored

In process: `ContestMemory._events` and `_digests` on the engine object.

On disk, after every accepted state change and at the end of a round:

| File | Contents |
|---|---|
| `contest_checkpoint.json` | `ContestSession` checkpoint plus `memory.to_checkpoint_json()` |
| `contest_session.json` | Final result; includes `memory: archival_snapshot()` |

`archival_snapshot()` is the complete unfiltered archive:

```json
{
  "version": 1,
  "scope": {"run_id": "...", "session_id": "...", "competition_id": "..."},
  "events": [ /* every ContestEvent */ ],
  "digests": [ /* compact per-task summaries created on switches */ ]
}
```

Checkpoint restore requires matching `run_id` / `session_id` /
`competition_id` and a contiguous `event-00000N` sequence. Resume never
replays Coach if the brief event is already in the ledger.

Digests (`create_problem_digest`) are compact, sanitised slices of one task
for one viewer. They are created when the engine switches away from a task
so later prompts can keep a short “what happened there” without replaying
the full task window.

### 6.4 How memory is projected (what the agent is allowed to remember)

Agents do **not** receive `archival_snapshot()`. `_user_prompt` builds a
`VISIBLE MEMORY` JSON blob in one of four ways.

**Full OTC** (`config.otc_policy` present, not basic, there is an active
task):

```text
memory.strategic_projection(
    viewer=agent,
    current_task_id=active.task_id,
    max_current_events = card.memory_entries.shared_work,      # ARML: 18
    max_direct_messages = card.memory_entries.group_messages,  # ARML: 12
    max_team_messages   = card.memory_entries.public_messages, # ARML: 24
    max_chars           = max(6000, 300 × (shared_work + public_messages)),
)
```

**Centralized** (`structured_context=True`, no OTC policy):

```text
memory.strategic_projection(viewer=agent, current_task_id=..., max_chars=6000)
```

using the function defaults: 8 current-task events, 4 digests, 6 procedural
lessons, 8 direct messages, 4 recent notes, 0 team-message slice.

**Decentralized / single-agent** (`structured_context=False`):

```text
memory.view(agent)[-12:]     # last 12 visible events, raw
```

**`vallina_otc`** (`basic_open_table`): no strategic projection. The raw
visible view is used, with `think` / `note` / `note_shared` events filtered
out, and the block is labelled `VISIBLE CONVERSATION` instead of
`VISIBLE MEMORY`. The review-history block is replaced by
`CURRENT SHARED DRAFTS` (the latest version and author per task), and the
think ledger by `CURRENT PRIVATE THOUGHT (this turn only)`.

`strategic_projection` always includes:

| Slice | Source |
|---|---|
| `contest_capsule` | Latest visible `contest_capsule` event |
| `scoreboard` | Latest visible `scoreboard` event |
| `current_task_events` | Visible events on the active task, excluding capsule, scoreboard, lessons, DMs, think, and some programming-progress kinds |
| `recent_digests` | Digests this viewer created for **other** tasks |
| `recent_notes` | This viewer's `note` / `note_shared` that are not already in `current_task_events` |
| `procedural_lessons` | Visible `procedural_lesson` events |
| `direct_messages` | Visible `direct_message` events |
| `team_messages` | Only when `max_team_messages > 0`: latest public `speak` / `note_shared` / deliberation / coach-summary across **all** tasks |

If the JSON exceeds `max_chars`, the oldest item of the currently largest
list is dropped until it fits. If that is still too large, capsule and
scoreboard collapse to `{"truncated": true}`.

`view()` is applied first, so a private note from Agent_2 never appears in
Agent_1's projection. Judge-only verdicts stay out until
`deliver_verdicts` writes the public/delayed form the card allows.

### 6.5 How that projection is stuffed into the model

Two prompts, rebuilt every seat action (and again for each OTC think call).

**System prompt** (`contest_prompts._system_prompt`):

- identity: `You are Agent_K, one contestant in an N-agent team`;
- transport instruction: native “call exactly one function” or JSON
  `action` / `arguments`;
- desk paragraph when those actions are offered (what `remember` /
  `recall` / `share_note` / `inspect_problem` are for);
- baseline protocol (leader rules, or the OTC `card_protocol` from
  `otc_runtime.protocol_text`);
- family workflow (answer sheet / programming / mathematics /
  short-answer / puzzle);
- `PRE-CONTEST COACH BRIEF` or `OPENING LEADER PLAN`;
- the public card block (roster, duration, communication limits).

The system prompt does **not** contain the event ledger.

**User prompt** (`contest_prompts._user_prompt`), in order:

```text
CONTEST <session_id>
TASK FAMILY <family>
COMPETITION FORMAT <description>
TASK STATUS   JSON of every task: state, drafts, reviews, priority, ...
BUDGET        turns/api/tokens/clock used and remaining, plus blank_tasks
DEADLINE POLICY
[COACH OPENING SUGGESTION FOR YOU]          # advice under OTC, enforced list under centralized
[YOUR PRIVATE THINK LEDGER]                 # OTC; newest last; nobody else sees this
                                            # vallina_otc: CURRENT PRIVATE THOUGHT (this turn only)
ANSWER-SHEET / PROGRAMMING GATE text
ACTIVE TASK <id> + full problem prompt      # or "NO ACTIVE TASK"
[ACTIVE PROGRAMMING SOURCE]                 # full latest source + sample report + reviews
SHARED ANSWER REVIEW HISTORY                # versions truncated to 800 chars
                                            # vallina_otc: CURRENT SHARED DRAFTS instead
YOUR ELIGIBLE PENDING REVIEWS               # full source for versions this seat may review
VISIBLE MEMORY                              # the projection from §6.4
                                            # vallina_otc: VISIBLE CONVERSATION (raw filtered view)
```

So an OTC contestant, each action call, sees:

1. bounded **shared work** on the current task;
2. bounded **team messages** across tasks;
3. bounded **direct messages**;
4. a few **cross-task notes** without calling `recall`;
5. the last N **private thoughts** (`private_think_per_agent`);
6. the live **task table** and **budget** from `ContestSession` (this is
   state, not ledger memory);
7. and, if they call `recall` this turn, a private `recall_result` that
   appears in the **next** projection.

They never see another seat's `think` or `note`. They never see gold,
hidden tests, or undelivered official verdicts.

Think-call user prompts use the same `_user_prompt` (so the same
`VISIBLE MEMORY`) plus `think_system_prompt` + `card_protocol` + the Coach
brief. The think response is stored, then the action call is built with
the updated think ledger.

## 7. Grading and judging

Grading runs after the deadline, on the final `ContestSession` state. It
never reaches the agents: gold text is not in prompts, and official verdicts
pass through the delayed-delivery path in §5.2.

### 7.1 Task grade (`grade_contest_result`)

| Task kind | Score |
|---|---|
| Programming | `1/1` when the task state is `solved` by an authoritative official verdict, else `0/1` |
| Everything else | Deterministic gold matching (`gold_answer_v1` machinery): the latest valid submission is parsed per `question_id` against the shared answer sheet; parts are weighted by their gold points, with alias and normalization rules (numbered lines, bare single-part answers, scientific-notation forms) |

A task whose gold record cannot support deterministic grading is marked
`{"graded": false, "status": "unavailable"}` and excluded from the totals.
The result therefore carries:

- `graded` — true only when **every** task was gradeable;
- `evaluation_coverage` — graded tasks / all tasks. Read this, not just
  `graded`: a run can complete while grading is partly unavailable;
- `score` / `max_score` / `task_utility` (mean per-task utility).

`rubric_llm_v1` (rubric-based LLM grading) exists in `src/evaluation/` but is
**not wired into this path**: contests whose only gold is a rubric grade as
`unavailable` here.

### 7.2 Judges (post-run, optional)

| Judge | Flag | What it produces |
|---|---|---|
| Task judge | `--judge-task` (default on with `--live`) | Registered evaluator output where gold alone is insufficient |
| Collaboration judge | `--judge-collab` (default on with `--live`) | MultiAgentBench-style Communication and Planning, `CS = (Communication + Planning) / 2` |
| CCE | `--judge-cce` (opt-in) | AgentWorld-style causal action graph over the event ledger; may add up to one judge call per turn |

Judge calls use `--judge-provider` / `--judge-model` (recorded in the
result). They cost provider money but are **not** charged to the contest's
`budget.api_calls_used`, so matched pairs stay budget-comparable. All judge
scores are model-dependent diagnostics; the task grade is the outcome
metric.

## 8. Outputs

A finished directory contains:

| File | Role |
|---|---|
| `run_config.json` | Resolved settings + fingerprint |
| `contest_checkpoint.json` | Resumable session + memory |
| `contest_session.json` | Final grade, budgets, process metrics, archival ledger |

Headline metrics in the result (reported separately, never averaged into
one score): TaskUtility / official score; turns, API calls, output tokens,
wall time, programming penalty; Communication, Planning, CS; AAR; AB;
review coverage; attempts-to-AC; repair / switch / stall counts; desk,
memory, deliberation, and deadline diagnostics.

A collaboration-gain claim needs matched `--system-variant` runs that
share model, manifest, team size, and budget caps. Process metrics
describe what the team did; they do not prove the score moved because of
collaboration.
