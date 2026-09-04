# Benchmark design

Why this benchmark is shaped the way it is: what it measures, how contest
realism is enforced, what the baselines and metrics are, and where the design
is known to be weak.

For the data itself see [`DATA_COLLECTION.md`](DATA_COLLECTION.md); for the code
layout, [`SOFTWARE_DESIGN.md`](SOFTWARE_DESIGN.md); for evaluators,
[`EVALUATION.md`](EVALUATION.md).

---

## What is being measured

The question is **not** whether an unconstrained frontier model can solve
olympiad problems. Measured problem by problem with unlimited resources, strong
models already do well, and that number says little about the systems we care
about.

This benchmark scores **teams working a whole contest under that contest's
rules**: a fixed clock, a bounded number of model calls, a restricted tool set,
and many problems competing for the same budget. Under those constraints a
strong solo model can still lose to a coordinated team, and a team of capable
models can still lose to its own coordination overhead. Those are the outcomes
the benchmark is built to distinguish.

Design principles that follow from it:

- **Collaboration is not absolute ability.** The two are scored on separate
  axes and reported separately.
- **Evaluate at competition level**, not problem level. A session includes
  strategy, work division, and the decision of when to stop and submit.
- **Solo-versus-team comparisons must hold total resources equal.** Otherwise a
  team simply buys its advantage with more calls.
- **Encode real contest rules**, including penalties, so that behaviour like
  premature submission carries its real cost.
- **Prefer verifiable graders**, and treat rubric LLM judges as a fallback whose
  reliability is itself subject to review.
- **Guard against answer lookup** where search is permitted.

---

## Contest realism

### Time, cost, and tokens are three separate budgets

A **turn is the clock**. Each agent may make at most one model call per turn, or
`sleep`. Turn counts are not chosen by hand: `src/contest_budget.py` maps each
contest's official `duration_minutes` onto turns via `minutes_per_turn`
(default 5.0), and the environment tracks `simulated_minutes` against that.
A 60-minute contest is therefore a 12-turn run, not an arbitrary 50.

**API calls are a separate cost budget** (`CollabConfig.max_api_calls` /
`--max-api-calls`), and **output tokens a third** (`max_total_tokens`, with a
per-call cap). Runs record `tokens_by_turn` as `[{turn, tokens, api_calls}, …]`
alongside the run total, so cost can be traced to the point in the session where
it was spent. Token counts are estimated from output length at roughly four
characters per token; synthesis after the turn loop is attributed to the final
turn.

### Penalties consume the resource they would really consume

A wrong programming submission does not add an abstract 20-point penalty. It
**burns 20 minutes of the remaining contest clock**, so the team has less time
left to work — which is what a penalty costs a real team mid-contest. Ranking
penalties are a scoreboard artifact; time is the thing teams actually lose.

### Tools are per contest, and search is policed

Tool availability comes from the contest, not from a global default:
`use_calculator`, `execute_code`, `web_search`, `read_lab_equipment`,
`read_star_chart`, `submit_code`. Contests that ban a tool ban it in the
environment, not merely in the prompt.

Where search is allowed it runs live rather than against a stub, and queries
that look like answer-key lookups are blocked and recorded as rule violations.
Contests are labelled `forbidden`, `judge_only`, or `no_solution_lookup`, and
the environment enforces the label.

Lab and observation tools read fixtures attached to the problem record
(`assets` / `tool_fixtures`), so an instrument reading is reproducible rather
than invented by the model.

### Rules can be prompt-only or enforced

`rules_mode` selects whether a contest's rule card is merely described to agents
(`prompt_only`) or enforced by the environment (`enforced`) — role permissions,
who may submit, phase schedules, communication limits. Running the same contest
both ways separates "the model ignored the rules" from "the model was prevented
from breaking them".

---

## Baselines

Four collaboration schemas, held constant across contests:

| Schema | Shape |
|---|---|
| `single_agent` | One agent with the **whole team's** resource budget |
| `centralized` | A leader assigns work and synthesizes |
| `round_table` | All agents act each turn in sequence |
| `decentralized` | Agents work independently and reconcile |

Plus `open_table_coach`, in which a coach agent assigns work under an enforced
rule card, and several research schemas (`debate`, `self_consistency`,
`memory_solo`, `subagent`).

**The solo baseline is budget-matched, not seat-matched.** In `run_single_agent`
the lone agent may make up to `team_size` calls per turn — the same per-turn
call budget a full team has. Without this, "multi-agent wins" would only restate
that more calls beat fewer.

Team compositions run both **homogeneous** (every seat on one model) and
**heterogeneous** (models cycled across seats).

> **Reading the matrix:** a heterogeneous × `single_agent` cell is *not* a mixed
> team. `single_agent` has one seat, so the model cycle collapses to the first
> model and the cell duplicates that model's solo run. It is retained only for
> matrix completeness.

---

## Metrics

### Task score

Contest score from the appropriate evaluator: deterministic gold matching where
short answers extract cleanly (`gold_answer_v1`), a programming judge for code,
a rubric LLM for open-ended deliverables (`rubric_llm_v1`, `slide_deck_v1`).
Reported as score, max score, and accuracy.

### Coordination Score (CS)

From `src/evaluation/collaboration_score.py`, following MultiAgentBench:

```
Communication (Cscore) ∈ {0, 1..5}   — 0 when there is no communication at all
Planning      (Pscore) ∈ {1..5}
CS = mean(Cscore, Pscore)
```

CS is judged by an LLM reading the run, deliberately **not** computed from
hand-coded proxies like message count — a team can exchange many messages
without coordinating. The communication judge sees the task, roster, schema,
outcome, and full chat log. The planning judge sees the roster and the **action
log** (speak / scratchpad / sleep / submit / tool calls), scoring whether work
was assigned clearly and whether plans advanced the task.

> **Reading CS:** a solo agent can score CS > 0 despite `Cscore = 0`, because
> planning is still scored from its own actions — `mean(0, 2) = 1.0`. A high
> task score with low CS is the expected signature of a strong solo, and is
> part of the result rather than a bug in the metric.

### Interaction Helpfulness Score (IHS)

CS measures process quality; a team can talk well and never improve its answer.
IHS scores the same run for effect: each interaction is labelled

- **helpful** — advanced a correct answer, fixed an error, or usefully divided work
- **neutral** — filler, repetition, or no clear effect on the final sheet
- **hurt** — pushed a wrong answer, wasted budget, or blocked progress

and the run gets a 0–5 score plus per-label counts and a helpful fraction.
`src/rescore_interaction_collab.py` applies it to already-completed runs, so
IHS can be added to past results without re-running them.

### Board metrics

Contests with a per-item workboard also report coverage and repeat behaviour.
See [`WORKBOARD_AND_TOOLS.md`](WORKBOARD_AND_TOOLS.md).

---

## Two reporting layers

The benchmark deliberately keeps two experiment shapes, because they answer
different questions and neither subsumes the other.

| | Per-problem batch | Model × schema matrix |
|---|---|---|
| Unit | 1 problem = 1 row | 1 cell = contest × team × schema |
| Varies | The problem | The system |
| Holds fixed | One run configuration | One problem |
| Answers | How accurate is this system? | Does collaboration structure matter? |
| Output | `competition_batch.tsv`, `competition_summary.tsv` | `phase_b_matrix.json` |
| Runner | `src/run_competition_batch.py` | `src/run_phase_b_matrix.py` |

The batch sweep is the honest accuracy headline: one configuration across many
problems gives a number with a denominator. The matrix is the collaboration
experiment: many configurations on the same problem isolates the effect of
structure. Reporting only the matrix overstates accuracy from a small sample;
reporting only the batch cannot say whether collaboration helped.

Export either to spreadsheet TSVs with `scripts/export_results_sheet.py`.

---

## Known limitations

Recorded so results are read with the right caveats. See also
[`TOOLING_GAPS.md`](TOOLING_GAPS.md), [`CAPABILITY_MATRIX.md`](CAPABILITY_MATRIX.md),
and [`HUMAN_VS_AGENT_SETTING.md`](HUMAN_VS_AGENT_SETTING.md).

**Grading.** Only mathematics has broad reliable gold. Linguistics, astronomy,
business-case, and writing contests are rubric-LLM graded, and the reliability
of those judges is itself an open question — a judge that scores plausibly is
not the same as a judge that scores correctly.

**Programming.** Submissions are judged against *sample* tests built from the
problem package. Secret/full test sets require a remote judge; a VJudge gateway
path exists (see [`VJUDGE_INTEGRATION_FEASIBILITY.md`](VJUDGE_INTEGRATION_FEASIBILITY.md))
but is not the default. Sample AC is a weaker claim than accepted.

**Practical and oral contests** are scored from written reports as a proxy.
Physical lab work and oral defence are not simulated, so scores for those
families measure the report, not the performance.

**Multi-modal problems** that depend on a diagram may be underspecified when
only the extracted text reaches the agents.

**Contest-rule transfer.** Human rules do not always have a clean agent
analogue — "no internet" and "one shared computer" mean something different for
a language model. `HUMAN_VS_AGENT_SETTING.md` tracks which mappings are faithful
and which are approximations.

**Turn budgets** are derived from official durations through a single
`minutes_per_turn` constant. That constant is a modelling choice, and results
are sensitive to it.

---

## Adding a contest

1. Add the benchmark record under `data/benchmarks/<contest_id>/benchmark.json`
   with `problem_id`, statement, `task_type`, `team_size`, and a `gold_label`
   or rubric reference.
2. Register the budget in `src/contest_budget.py` from the official duration.
3. Register allowed tools in `COMPETITION_TOOL_REGISTRY` (`src/env.py`), and a
   rule card under `data/rules/<contest_id>/` if it should run enforced.
4. Point `evaluation.evaluator_id` at the right evaluator, adding a rubric under
   `data/rubrics/` if needed.
5. If the contest has distinct sub-items, give it a board — see
   [`WORKBOARD_AND_TOOLS.md`](WORKBOARD_AND_TOOLS.md).
