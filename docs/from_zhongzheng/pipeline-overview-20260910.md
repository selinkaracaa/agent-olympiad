<!-- markdownlint-disable MD060 -->

# Agent Olympiad benchmark pipeline

> Current as of 2026-09-10. This document describes the contest-session engine,
> protocol `contest_session_v6`, and action set version 5.

## 1. What this repository does

Agent Olympiad evaluates AI teams on real or reconstructed team competitions.
A run gives several model-controlled contestants:

- one contest containing multiple tasks;
- one shared clock, API-call budget, and output-token budget;
- a typed action surface determined by the competition and baseline;
- shared and private state with auditable visibility;
- deterministic or remote judging;
- outcome, cost, participation, and coordination metrics.

The repository now provides five connected layers:

1. **Data** — source files, normalized benchmark rows, rule cards, rubrics,
   programming packages, and explicit contest manifests.
2. **Contest runtime** — one stateful engine for all current baselines.
3. **Model transport** — native function calling or validated emulation.
4. **Judging** — deterministic gold, rubric judging, local samples, and remote OJ.
5. **Experiment tooling** — resumable batches, identity fingerprints, summaries,
   result sheets, and leaderboards.

## 2. Current stack versus legacy stack

There are two execution paths in the repository:

| Path | Current use | Entry | Core modules |
|---|---|---|---|
| Contest session | All new benchmark experiments | `run_competition_batch.py --contest-manifest ... --system-variant ...` | `contest_engine.py`, `contest_session.py`, `contest_memory.py`, `contest_actions.py`, `contest_policy.py` |
| Legacy per-problem | Historical schemas and compatibility tests | `run_competition_batch.py --schema ...` and older scripts | `env.py`, `collaboration.py`, `actions.py` |

The two paths share the canonical action definitions in `tool_registry.py`, but
they do not have the same lifecycle or result format. A legacy `decentralized`
run is not interchangeable with a contest-session `decentralized` run.

Use the contest-session path for new work.

## 3. End-to-end data flow

```text
source PDFs / archives / APIs
        |
        v
collectors/*  ---------------------------> data/raw/*
        |
        v
data/benchmarks/<competition>/benchmark.json
        |                     |
        |                     +----------> data/rubrics/*
        |                     +----------> data/rules/<competition>/collaboration.json
        |                     +----------> programming package / sample assets
        v
data/contest_manifests/*.json
        |
        v
contest_manifest.load_contest_manifest()
        |
        v
run_competition_batch.py
        |
        +--> resolve baseline, rule card, roster, clock, API/token limits
        +--> resolve task-family capability packs and provider transport
        +--> build and fingerprint run_config.json
        v
contest_engine._ContestEngine
        |
        +--> optional turn-0 Coach or leader plan
        +--> rounds x seats x private-think/action phases
        +--> action validation and state transitions
        +--> checkpoint after accepted state changes
        +--> deadline settlement
        v
grade + collaboration/process metrics
        |
        v
contest_session.json + summaries + exported TSV
```

## 4. Data contracts

### 4.1 Benchmark rows

The primary processed data lives at:

```text
data/benchmarks/<competition_id>/benchmark.json
```

A row normally contains:

- `problem_id`, competition, year, title, task type, and source metadata;
- `problem_description`;
- team-size and competition metadata;
- `gold_label.parts[]` with expected values, points, aliases, and match mode;
- an `evaluation` block naming the evaluator and readiness status;
- programming metadata when remote judging is available.

Rows have mixed granularity. Some are complete published packets; others are
individual questions. Row count is therefore not contest count.

### 4.2 Contest manifests

A manifest converts benchmark rows into one actual contest session:

```json
{
  "session_id": "mystery_hunt_1999",
  "competition_id": "mystery_hunt",
  "problem_ids": ["mystery_hunt_00002", "mystery_hunt_00003"],
  "split_parts": false,
  "task_family": "puzzle"
}
```

`src/contest_manifest.py` resolves every id against the benchmark, removes
answer/solution leakage from prompts, and creates ordered `ManifestTask` values.

`scripts/run_otc_gold_suite.py` generates natural contest units:

- ARML Local / National Team: one published packet per session, split into its
  numbered questions;
- Science Bowl: group sampled questions by official `parent_session_id`;
- QANTA: group by year and tournament;
- Mystery Hunt: group puzzles by year;
- packet competitions: preserve one benchmark packet per session.

### 4.3 Rule cards

`data/rules/<competition>/collaboration.json` records the public competition
contract and the enforced OTC policy. `src/rulecard_policy.py` validates and
projects it into runtime policy.

For OTC, the card can control:

- roster minimum/default/maximum and submission roles;
- official duration, rounds, and minimum finishing turn;
- blind turn-0 Coach;
- private think calls and memory window sizes;
- message and character budgets;
- structured deliberation requirements;
- enabled capability bundles;
- ICPC workstation lease and delayed verdict delivery;
- programming repair budget.

The exact card content and SHA-256 are stored in each run identity.

## 5. Baselines

All current baselines use the same contest engine. Their behavior is defined by
`BaselineFeatures` in `src/contest_config.py`.

| Baseline | Core behavior |
|---|---|
| `single_agent` | Same no-coach environment as decentralized, with team size fixed to one |
| `decentralized` | Flat open table; no Coach, review workflow, private channel, desk, or memory actions |
| `centralized` | `Agent_1` creates the plan, acts first, can reassign work, and alone can submit |
| `otc` | Rule-card Open Table Coach: one blind Coach brief, private thinking, memory/desk/private communication, independent review, and card enforcement |

Aliases exist for old command lines, but results store the canonical name.

### 5.1 OTC v6

Current OTC is not the retired `collaboration.py` implementation.

1. Before the clock, a problem-blind Coach produces one brief. It costs one API
   call but no contest turn.
2. There is no later Coach call and no Coach-generated enforced assignment.
3. Each seat keeps its own problem focus. `work(problem_id=..., content=...)`
   can switch and record a draft in one action.
4. The card may require private think calls before the seat's public action.
5. Current-version approval by another contestant is mandatory. Self-review is
   invalid, a rejection vetoes submission, and revision stales earlier reviews.
6. Deadline collection does not bypass review or programming sample evidence.
7. ICPC cards may enforce one team-global workstation lease and delayed,
   controller-private judge verdicts.

## 6. One contest run

### 6.1 Setup

`run_competition_batch.py`:

1. parses the manifest;
2. canonicalizes the requested baseline;
3. loads and validates the rule card when required;
4. resolves team size and official contest budget;
5. resolves the action transport and frozen action registry;
6. builds a run identity covering configuration, content, rule card, protocol,
   action set, and all `src/*.py` files;
7. writes `run_config.json` before model calls.

### 6.2 Turn loop

The engine then runs:

```text
for contest round:
    charge one contest turn / simulated time
    for each seat in fixed order:
        resolve that seat's focus and legal actions
        run card-required private think calls
        charge one API call and query the model
        validate exactly one typed action
        apply card rules and state prerequisites
        append visibility-tagged events
        update ContestSession
        persist checkpoint
deliver due delayed verdicts
```

`--start-seat` rotates the first seat for repeated matched experiments; it does
not rotate the order every round.

### 6.3 API calls, turns, and tokens

- **Turn**: one outer contest round.
- **API call** in `budget.api_calls_used`: one contest-orchestration request to
  the model. Every seat action, private think, Coach call, leader plan, or
  emulated correction may add calls. Post-run collaboration/CCE judge calls
  incur provider cost but are not added to this contest budget field.
- **Tokens**: the shared contest limit counts model output tokens.
- **Wall time**: recorded, not used as the simulated contest clock.

For a simple three-seat decentralized run, the upper pattern is approximately
`turns × 3` calls. An OTC card with one private think and one action per seat is
approximately `turns × team_size × 2 + one Coach call`.

## 7. State and memory

### 7.1 ContestSession

`src/contest_session.py` is authoritative state:

- tasks and per-seat focus;
- immutable answer/source versions and hashes;
- current and stale reviews;
- local evidence and official submissions;
- task state, priority, locks, and cooldown;
- shared budget ledger.

### 7.2 ContestMemory

`src/contest_memory.py` is an append-only event ledger. Events include actor,
task, turn, kind, payload, visibility, and recipients.

Visibility is enforced:

- public/team events are visible to contestants;
- private events are visible only to the actor and named recipients;
- controller/judge state remains hidden where the protocol requires it.

Agents receive bounded projections, not the complete archive. OTC memory actions
write into the same ledger:

- `remember` creates a private note;
- `recall` searches own and shared notes;
- `share_note` publishes a selected note.

## 8. Action resolution

`src/tool_registry.py` is the single action contract. It defines names,
arguments, JSON schema, visibility, capability pack, budget semantics, runtime
support, and handler marker.

The session starts from:

1. common collaboration actions;
2. inferred or declared task packs (`math`, `programming`, `research`,
   `resources`);
3. the OTC card's optional `deliberation` pack.

Then `src/contest_policy.py` narrows the list for the baseline, role, task,
review state, submission state, card budget, workstation lease, and current
phase. Therefore a registered action is not necessarily visible on every turn.

See [Actions reference](actions-reference.md).

## 9. Submission and judging

### 9.1 Answer-sheet contests

`work` records per-task drafts. When submission gates are satisfied, argument-free
`submit` sends the current sheet atomically. At the deadline, eligible pending
drafts are collected without another model call. Missing or review-ineligible
answers stay blank.

### 9.2 Programming contests

The normal path is:

1. `execute_code` runs source against official samples in the isolated runner;
2. another contestant reviews the exact source hash;
3. `submit_code` sends the frozen reviewed source;
4. the VJudge/Kattis adapter returns or schedules the official verdict;
5. rejected code is revised and the cycle repeats.

The OTC ICPC card can enforce a global keyboard lease and verdict latency.
`--programming-deadline-submit` controls end-of-contest candidate submission;
the result records whether it was used.

### 9.3 Graders

- `gold_answer_v1`: normalized exact/alias matching with weighted parts;
- programming: solved state from authoritative official verdicts;
- `rubric_llm_v1`: criterion-based grading where connected;
- collaboration judge: Communication and Planning, with
  `CS = (Communication + Planning) / 2`;
- CCE: optional causal action-graph analysis.

An execution can complete while grading is unavailable. Check
`evaluation_coverage`, not only `grade.graded`.

## 10. Metrics

Core reported values include:

- task score, max score, accuracy/TaskUtility;
- turns, API calls, output tokens, wall time, and programming penalty;
- Communication, Planning, and CS;
- AAR: fraction of contestants taking substantive actions, macro-averaged by
  task;
- AB: Gini-normalized balance of substantive action counts;
- review coverage, attempts to AC, repair yield, switch/stall counts;
- action transport retries/failures;
- desk, memory, triage, deliberation, and deadline diagnostics.

These process metrics describe observed behavior; they do not prove that
collaboration caused a score increase. Causal claims require matched baselines.

## 11. Outputs and safe reuse

A fresh output directory contains:

```text
run_config.json             resolved settings + fingerprint
contest_checkpoint.json     resumable session/memory state
contest_session.json        final result and archival event ledger
run.log                     batch-launch log when a scheduler creates it
```

The fingerprint includes model settings, canonical baseline, manifest content,
rule-card content, budgets, judges, action transport, protocol/action versions,
and source hashes. It excludes credentials and output paths.

`--resume`:

- skips an exactly matching final result;
- resumes an exactly matching checkpoint;
- rejects changed code/config/data/protocol instead of silently mixing runs.

Never add identities to old results manually. Use a fresh directory when the
experiment definition changes.

## 12. Main modules

| Module | Responsibility |
|---|---|
| `run_competition_batch.py` | CLI, provider/judge setup, settings resolution, run identity |
| `contest_config.py` | protocol version, baseline presets, validated run config |
| `contest_manifest.py` | benchmark-to-contest task extraction |
| `contest_engine.py` | Coach, rounds, seat phases, deadlines, result construction |
| `contest_policy.py` | legal action surface and scheduling/focus policy |
| `contest_actions.py` | action handlers and state transitions |
| `contest_prompts.py` | contestant-visible prompts and projections |
| `contest_session.py` | authoritative task/version/review/submission state |
| `contest_memory.py` | visibility-aware append-only event ledger |
| `tool_registry.py` | canonical typed action definitions and capability resolver |
| `rulecard_policy.py` | validated OTC policy derived from cards |
| `contest_run_identity.py` | fingerprint and reuse checks |
| `contest_batch_summary.py` | provenance-checked batch summaries |
| `judge/*`, `vjudge_gateway.py` | local and remote programming judge integration |

## 13. Known limits

- Some collected benchmark families still lack a contest-session artifact
  workflow or connected rubric grader.
- Question-level datasets are sampled; grouping recreates natural sessions from
  available rows, not necessarily complete historical packets.
- Remote OJ availability, credentials, quotas, and external state are not
  captured by the local fingerprint.
- LLM-judged coordination and rubric scores are model-dependent diagnostics.
- Historical results from older protocol versions remain valid only for their
  recorded protocol and cannot be resumed under v6.
