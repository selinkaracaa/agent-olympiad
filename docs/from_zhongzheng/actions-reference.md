<!-- markdownlint-disable MD060 -->

# Contest-session actions reference

> Current contract: `src/tool_registry.py`, `ACTION_SET_VERSION = 5`.

The registry contains 31 canonical actions shared across the current
contest-session runtime and the legacy environment. The contest-session runtime
implements 27 of them. Four workspace/workboard actions are legacy-only.

An action being registered does not mean every agent sees it. The final surface
is resolved from:

1. runtime (`session` or legacy `env`);
2. competition/task capability packs;
3. baseline feature switches;
4. OTC rule-card bundles and role permissions;
5. current task, review, submission, lease, message-budget, and deliberation
   state.

## 1. Visibility

| Registry value | Meaning |
|---|---|
| `private` | Result/event is visible to the actor and explicit recipients |
| `team` | Shared with the team |
| `contest` | Contest-control state visible across the session |

The archival event ledger preserves the visibility and recipients. Agent
prompts receive only their permitted projection.

## 2. Common contest-session actions

### Work and navigation

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `select_problem` | `problem_id` | contest | Change the acting seat's focus/current problem |
| `work` | `content`, optional `problem_id` | team | Record an immutable candidate answer/draft; optional problem id switches and writes atomically |
| `skip_problem` | optional `reason` | contest | Leave/release current focus according to runtime policy |
| `rest` | optional `reason` | private | Spend the seat's action without changing work |
| `finish_contest` | optional `reason` | contest | End only when the contest completion gates permit it |

`work` is the durable candidate-answer operation. Intermediate reminders belong
in `remember`, and public discussion belongs in `speak`.

### Communication

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `speak` | `content` | team | Public team broadcast |
| `direct_message` | `recipients[]`, `content` | private | Message one teammate or named subgroup |

OTC cards can limit message count and characters. Exceeding the count produces
an action error and still spends the turn. Text can be clipped to card limits.

### Review and submission

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `request_review` | `content`, optional `reviewer` | team | Ask for review; does not approve any version |
| `review_answer` | `problem_id`, `version_hash`, `decision`, `content` | team | Approve or reject another author's exact current version |
| `submit` | `answer` in registry; may become argument-free by policy | team | Submit a non-programming answer or complete answer sheet |

In current OTC:

- candidates enter the review queue automatically, so `request_review` is
  removed from the offered surface;
- an author cannot review their own version;
- the hash must identify the current version;
- revision makes earlier reviews stale;
- a current independent approval is mandatory;
- a current rejection blocks submission;
- answer-sheet `submit` is exposed only when all required gates pass and is
  transformed to an argument-free atomic submission.

### Desk and memory

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `inspect_problem` | optional `problem_id`, optional `focus` | private | Read statement, versions, reviews, and submissions without changing focus |
| `triage_problem` | `problem_id`, `priority`, optional `reason` | team | Set `high`, `normal`, `low`, or `hopeless` priority |
| `remember` | `content`, optional `problem_id` | private | Store a private durable note |
| `recall` | optional `query`, optional `problem_id` | private | Search own notes and team-shared notes |
| `share_note` | `note_id` | team | Publish one of the actor's notes |

`inspect_problem` is self-verification context, not an independent review.
`hopeless` changes priority but does not erase a draft or automatically omit it
from deadline handling.

### Centralized-only control

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `assign_problem` | `agent`, `problem_ids[]`, optional `reason` | team | `Agent_1` replaces a worker's enforced work list |

Only the centralized leader sees this action.

## 3. Structured deliberation pack

These actions appear only for OTC cards whose deliberation mode is structured.

| Action | Arguments | Effect |
|---|---|---|
| `propose` | `content`, optional `problem_id` | Open a numbered candidate proposal |
| `challenge` | `proposal_id`, `content` | Raise a concrete objection to another author's open proposal |
| `provide_evidence` | `proposal_id`, `content` | Attach a derivation, check, source, or counterexample |
| `revise` | `proposal_id`, `content` | Proposal author replaces its current claim |
| `decide` | `proposal_id`, `outcome`, `reason` | Card-designated decision maker accepts, rejects, or defers |

Runtime restrictions include:

- follow-up ids are pinned to open proposals;
- a proposal author cannot challenge their own proposal;
- only the author may revise;
- only the configured decision maker may decide;
- the card can require a minimum number of challenges before answer-sheet
  submission.

## 4. Competition capability packs

### Math

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `use_calculator` | `expression` | private | Evaluate a permitted arithmetic expression |

The resolver infers a math family but still respects the contest tool allowlist.
For example, an ARML task being mathematical does not by itself grant a
calculator when the contest rules forbid it.

### Programming

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `execute_code` | `code`, optional `language` | private | Run source in the sandbox and, for programming tasks, evaluate official samples |
| `submit_code` | `code`, optional `language`; may be transformed by policy | team | Submit source to the programming evaluator/remote judge |

For reviewed OTC programming:

- source needs local sample evidence;
- another contestant must approve the exact current hash;
- policy can submit the frozen reviewed version without asking the model to
  reproduce source;
- ICPC cards can enforce a team-global workstation lease;
- official verdicts can remain controller-private until a later round;
- pending source is frozen and exactly-once delivery is checkpointed.

`SAMPLE_WA`/`SAMPLE_RE` are local results and are not remote attempts.

### Research

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `web_search` | `query` | private | Use the installed permitted search handler |

### Declared physical resources

| Action | Arguments | Visibility | Effect |
|---|---|---|---|
| `read_lab_equipment` | optional `resource` | private | Read an explicitly declared laboratory resource |
| `read_star_chart` | optional `resource` | private | Read an explicitly declared astronomy resource |

Physical-resource actions are never inferred broadly. The benchmark/card must
declare the capability and a handler must exist.

## 5. Baseline surfaces

| Capability | single-agent | decentralized | centralized | OTC |
|---|---:|---:|---:|---:|
| Public `speak` / `work` / navigation | yes | yes | yes | yes |
| Private messages | no | no | yes | yes |
| Desk inspection/triage | no | no | yes | yes |
| Memory actions | no | no | no | yes |
| Independent review | no | no | no | yes |
| Leader assignment | no | no | leader only | no |
| Structured deliberation | no | no | no | card-dependent |
| Competition tools | task-dependent | task-dependent | task-dependent | task/card-dependent |
| Submission authority | actor/policy | actor/policy | leader only | rule-card role |

`single_agent` and `decentralized` have the same feature switches; single-agent
only pins team size to one.

## 6. Dynamic gates

`src/contest_policy.py`, `src/contest_actions.py`, and the OTC runtime can hide
or reject actions for these reasons:

- wrong runtime or unavailable handler;
- capability not granted or forbidden by contest rules;
- baseline bundle disabled;
- role lacks submission or decision authority;
- invalid teammate/problem/proposal enum;
- action targets the wrong task/focus;
- no current draft/source/version;
- self-review, stale hash, or duplicate review;
- incomplete answer sheet or missing independent approval;
- current rejection;
- missing sample evidence;
- task already solved/locked or source already pending;
- workstation lease held by another seat;
- message/character budget exhausted;
- minimum turn or deliberation challenge requirement not met;
- shared API/token/clock budget exhausted.

The model receives the dynamically narrowed JSON function schemas each call.
If it still violates a runtime precondition, an `action_error` event records the
failure.

## 7. Action transport

The same `ActionSpec` schemas drive every transport:

- `auto`: native for providers that support tools, validated emulation otherwise;
- `native`: provider function calling with required tool choice;
- `emulated`: schemas rendered into the prompt, parsed and validated, with
  bounded correction attempts;
- `prompt-json`: compatibility mode for strict action JSON.

Only the first validated function call is executed. Extra calls are logged and
ignored. API calls and output tokens used by emulated correction attempts are
charged to the shared budget.

## 8. Legacy-only actions and aliases

These canonical registry actions run only in the old `env` path:

| Action | Purpose |
|---|---|
| `verify_problem` | Workboard opinion without immutable version hashes |
| `check_budget` | Show old environment budget/workboard state |
| `query_rules` | Show role-visible old environment rule card |
| `write_private_notes` | Replace the old private-notes block |

Legacy wire names normalize at the boundary:

| Legacy name | Canonical action |
|---|---|
| `submit_final` | `submit` |
| `sleep` | `rest` |
| `write_scratchpad`, `submit_problem` | `work` |
| `verify`, `list_problems`, `open_problem` | `inspect_problem` |
| `claim_problem` | `select_problem` |
| `release_problem` | `skip_problem` |
| `set_priority`, `mark_hopeless` | `triage_problem` |
| `publish_memory` | `share_note` |
| `message_group` | `direct_message` |

New contest-session code and rule cards should use canonical names.
