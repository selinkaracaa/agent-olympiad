# Changelog

## Per-item workboard and shared-workspace actions

Most contests here are one environment over many items — an ARML answer sheet
has ten problems, an IOAA group task has a dozen sub-questions. Previously a
team held a single `final_answer` string for the whole contest. The workboard
replaces that with a shared answer sheet the agents can actually work: pick up
an item, record an answer against it, read what has already been tried, and
check a teammate's work.

The closest familiar thing is an online quiz. You open a question, type an
answer, move to another, come back later and your previous answer is still
sitting there. That is what the board gives a team.

**Three problems it solves:**

- **Agents could not see what they had already tried.** With one answer string
  and no history, resubmitting the same wrong answer cost nothing and taught
  nothing, so runs could spend their whole turn budget cycling on one item.
- **Nothing recorded who was working on what.** A transcript could not answer
  "what happened on question 4?", which made collaboration failures impossible
  to diagnose.
- **There was no review step.** An answer went from one agent straight into the
  final submission with nothing in between.

Full reference: [`WORKBOARD_AND_TOOLS.md`](WORKBOARD_AND_TOOLS.md).

---

### The board

A board is built automatically for any contest whose items can be identified —
from `gold_label.parts`, from labelled sub-questions in the problem statement,
or from an explicit `board_items` field. Contests graded as one deliverable get
no board and are unaffected.

Eight actions, grouped by what they are for.

**Finding work.** `list_problems` shows every item at once: status, points, who
is on it, how many attempts it has taken, and the answer currently recorded.
`open_problem <item>` opens one item — its statement plus the **complete answer
history**, every attempt with its turn and author. This is the action that
makes stubbornness visible: an agent about to retry can first see the four
answers already tried.

**Taking work.** `claim_problem <item>` takes an item, one per agent, and
`release_problem` hands it back. This turns "divide up the questions" from an
instruction in a prompt into something the environment actually enforces —
another agent cannot answer an item you hold. Claims expire after three idle
turns, so an agent that claims an item and then stops acting cannot lock it for
the rest of the run.

**Recording answers.** `submit_problem <item> | <answer>` records an answer.
Three rules apply, each for a reason:

- *Only the latest recorded answer is graded, and an item with nothing recorded
  scores zero.* This matches how the contests actually score, and means a
  considered guess always beats leaving a blank.
- *Recording an answer already recorded for that item is refused.* It changes
  nothing, so the environment says so — naming the turn and agent that recorded
  it first, and how many items are still blank. Retrying with a **different**
  answer stays unlimited: persistence on a hard problem is reasonable, and only
  the literal no-op is blocked.
- *No correctness feedback is returned.* These contests do not give teams
  per-item feedback, and the board is built from the gold record — returning a
  verdict would hand over the answer key.

**Checking work.** `verify_problem <item> | agree|disagree|unsure <comment>`
reviews whatever answer is currently recorded. You cannot review your own sole
answer, which is the point: since the board gives no correctness feedback, a
teammate's review is the only check a team has. A review does not change the
recorded answer — it flags it for someone to replace.

**Triage.** `mark_hopeless <item> | <reason>` and `set_priority <item> |
high|normal|low` let a team say what it has given up on and what matters most.
A hopeless item stays on the board, because a recorded guess still beats a
blank.

### Workspace actions

Five actions that are not about any single item. They are available in every
contest and every rules mode — including the vanilla baseline — because they
represent the desk rather than contest-specific equipment like a calculator or
a star chart.

**`remember` / `recall` / `publish_memory`** give an agent notes that survive
outside the chat log. A note can be tagged to a board item, so `recall` scoped
to item 4 returns what was worked out about item 4 earlier in the run.
`publish_memory` promotes a private note to the whole team.

**`check_budget`** reports turns, API calls, tokens, the contest clock, and how
much of the board is still blank. Deciding whether to keep working a hard item
or move on is only a real decision if an agent can see both the clock and the
remaining work; without this it is guesswork.

**`message_group <names> | <message>`** sends to named teammates instead of
broadcasting. This is what makes sub-teams possible — two groups working
separate halves of a paper and then checking each other — without every message
going to every seat.

### Metrics

Each answers a specific question about a run.

| Metric | The question it answers |
|---|---|
| `repeat_rate` | Did the team cycle on answers it had already tried? `repeats / (attempts + repeats)`. |
| `items_answered` / `items_unanswered` | How much of the paper did they actually attempt? Blank items score zero. |
| `items_reviewed` | Did anyone check anyone else's work? |
| `attempts_recorded` | How much answering happened, independent of coverage. |
| `distinct_claimers` | Did the team divide the work, or did one agent do everything? |
| `items_hopeless` | What did the team consciously give up on? |
| `board_source` | Where the items came from, for debugging a bad board. |

Aggregated across a batch as `board_runs`, `mean_board_repeat_rate`,
`total_board_repeat_attempts`, and `mean_board_answered_fraction`. All reach
`competition_batch.tsv`, `competition_summary.tsv`, `sheet1_summary.tsv`, and
`sheet2_detail.tsv`.

`repeat_rate` is the headline. Because the board refuses a repeat rather than
absorbing it, the count is a direct measure of the behaviour rather than a
proxy for it.

### Changed behaviour

**`submit_final` is now backed by the board.** Whoever submits keeps authorship
of their answers, but any item recorded on the board and missing from their
submission gets appended, and a submission that contains no numbered answers at
all falls back to the board sheet. Without this the feature was worse than
useless: a run with five correct answers on the board scored zero, because the
synthesis step wrote its own answer and discarded everything the team had
recorded. The merge lives in the environment rather than in the synthesis code,
so every submission path gets it — including the schemas that never call
synthesis.

**The 10-character minimum on `submit_final` no longer rejects short answer
sheets.** That floor exists to reject `"ok"`; `"1. 268"` is a complete
submission on a one-item board.

**Contest phase rules no longer block reads.** Rule cards that list permitted
actions per phase were written before these actions existed and would have
banned them by omission. Reading the board, checking the budget, and rereading
your own notes are now always permitted; actions that change shared state are
still gated by the phase.

**A refused board or memory call is a no-op, not a rule violation.** Asking for
an item that does not exist is a mistake, not cheating, and should not pollute
the rule-violation count.

### Code

New module `src/workboard.py` holds the board: `Workboard` with its
`BoardItem`s, each owning its `Attempt`s, `Review`s, claim, and triage flags.
The actions are dispatched from `src/env.py`; `src/memory.py` gained per-item
tagging; `src/actions.py` and `src/collaboration.py` put the board into the
prompts agents actually read. `tests/test_workboard.py` covers it in 32 tests,
including one asserting that no gold answer can leak through the board.

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
