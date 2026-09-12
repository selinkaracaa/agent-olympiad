# Weekly summary, 2026-09-05 to 2026-09-09

Zhongzheng. All live runs: Perplexity `openai/gpt-5.4-mini`, native actions, 3 agents, 50 turns.
Picks up where [otc-protocol-fixes-20260906.md](otc-protocol-fixes-20260906.md) stops.

## What happened

Spent the week on one question: why do full ICPC contests score 2/12, and is Vanilla a fair
baseline? Audited the low score down to five named defects, fixed three, re-ran fresh pairs. Score
didn't move. The reason it didn't move is the useful part.

Also gave ARML Power / National Power machine-derived rubrics so they can enter the sweep, and built
a resumable all-years ICPC pair batch.

## ICPC: the ceiling is wrong algorithms, not plumbing

The audit (`results/icpc_2012_v3_gap_audit_20260908/remaining_gaps.md`) started from a run where all
12 tasks had source, all 12 got an official verdict, and all 136 applicable prompts had full source
and the right task-family tag. So missing submissions and prompt bugs are ruled out. Five defects:

1. **P1** Sample checker token-compared Infiltration, rejecting a valid reordered optimal set.
2. **P1** Sample success is too weak a progress signal — provably wrong code that passes two samples
   keeps counting as progress.
3. **P2** One hard task ate the contest: Takeover took 56/150 actions, 30/101 executions, ended TLE.
4. **P2** 10 of 101 executions re-ran already-executed source.
5. **P2** Deadline submission handles task *coverage*, not candidate *selection* — it skipped any
   task that ever had a valid submission, including a WA one.

Defect 2 was shown with tiny counterexamples against the run's own saved code, not prose. Takeover's
turn-50 source decides by `sum(a) < sum(b)` and its comments admit the rule was guessed from the two
samples; it answers `Buyout` on `1 1 / 2 / 1` where Takeover wins. Infiltration solves source SCCs,
so a 3-cycle returns 1 where the answer is 2.

Fixed 1, 4, 5 → `programming_workflow_v4` (`fix_validation_v4.md`): semantic Infiltration checker,
failed-execution reuse keyed by source + language + task + judge fingerprint, and deadline candidate
selection that prefers sample-AC then approval then recency and never resends the same program.

Fresh full 2012 pairs under v4:

| | OTC v3 | OTC v4 | Vanilla v4 |
|---|---:|---:|---:|
| Official AC | 2/12 | **2/12** | **2/12** |
| Tasks with a verdict | 12/12 | 12/12 | **2/12** |
| Output tokens | 93,593 | 102,432 | 34,607 |
| Sample executions | 101 | 98 (13 reused) | 10 |
| Action errors | 0 | 0 | **62** |

The tie means little — one stochastic run each, 3× the tokens on the OTC side, and a Vanilla run
dominated by invalid actions. What's clean is coverage: OTC put all 12 problems in front of the
judge, Vanilla reached it on 2 and left 9 unseen. 9.4% more tokens bought the same two ACs, so
raising the turn budget is not the next lever.

Still open after v4, each with evidence in the run notes: Minflow's sample-AC source hardcodes two
case outputs and its own comments call it incomplete, was rejected at review, submitted anyway, WA.
A turn-44 review approved a hash claiming Kosaraju/SCC when the source at that hash is
branch-and-bound with an unused bound — the saved prompt contains that exact source, so it's a
grounding failure, not the old truncation bug. And 96 distinct sources collapse to 86 distinct ASTs,
so exact-source dedup misses formatting variants.

## Remote-judge failures look exactly like agent failures

Two ICPC 2014 pairs, identical config, hours apart:

| Run | Terminal verdicts | AC |
|---|---|---:|
| 2014 OTC, first try | **12× PENDING** | 0/12 |
| 2014 OTC, gateway healthy | 1 AC, **10× SUBMIT_FAILED** | 1/12 |

In the first, verdicts never resolved, so a run that submitted all 12 grades as a clean zero. In the
second, all ten failures carry Kattis's `out of submission tokens` — a quota ceiling, not ten wrong
programs. Neither zero says anything about the agents. **Any ICPC table needs the verdict
distribution next to the score.**

`scripts/run_all_icpc_full_pairs.py` now batches every `remote_judge_ready` year (24 jobs), is
resumable per session+variant, health-gates the gateway before every job and stops with
`status: blocked` instead of producing more `PENDING`, and paces jobs 15s apart. First pair through
it (2013) is the first clean one: OTC 1/11 (1 AC, 9 WA, 1 RE), Vanilla 0/11. Still running.

`src/judge/kattis.py:130` maps the quota rejection to a generic `SUBMIT_FAILED` — it needs its own
classification plus bounded backoff, distinct from an ambiguous network failure.

## Vanilla is finally a real baseline

The v3 protocol split (last week's doc) shows up here. ARML National Team, Vanilla arm: **6/11 years
nonzero, 35.56/550**, using 4–8 turns per year. Last week's clean rerun was 0/11 nonzero burning all
50 turns. Comparisons made before the split were measuring a broken action surface, not the model.

Vanilla still has three gaps, reproduced offline with intentionally-failing probes in
`results/icpc_2012_full_vanilla_v4_50turn_20260909/`: `finish_contest` stays exposed even though the
handler always rejects it (31 of the 62 action errors), an AC doesn't advance the cursor (Bottles
stayed active from its turn-2 AC to a manual skip at turn 19), and identical-source resubmission
reaches the executor before the AC lock check — which sent a real repeat request to Kattis at
turn 32. All three are shared preconditions, not "give Vanilla OTC's strategy".

OTC still leads where the contest is gradeable. Five ARML Local years finished in both arms:
**97.78/200 (48.9%) vs 23.33/200 (11.7%)**, at roughly 10× the API calls. 2011 was a clean 40/40.

## ARML Power: data ready, evaluation blocked

Power packets are proof rounds with no answer key, but they carry their own weights inline as
`[4]` / `[3 pts.]` markers. `scripts/build_arml_power_rubrics.py` turns every marker into one rubric
criterion — the statement text up to the marker, worth the marker's points, under the packet's own
numbering. 26 rubrics written and linked (15 `arml_power` + 11 `arml_national_power`).

The faithfulness check is that recovered weights sum to the official total, true for 13 of 15
`arml_power` contests. It matters because `apply_registered_judge` rescales to `total_points`, so a
packet with markers lost in PDF extraction would silently inflate its surviving criteria; anything
under `--min-coverage` is written but left unlinked.

All 26 sessions ran and all 26 grade as `unavailable`. Structural, not a bad rubric: the
contest-manifest branch of `run_competition_batch.py` grades only through `grade_contest_result`,
which has no path to `rubric_llm_v1`, and `regrade_contest_sessions.py` calls the same grader.
Nothing consumes the rubrics yet.

## One failing test to decide on

338 tests, 337 pass. `test_reference_only_gold_is_unavailable` fails because
`grade_contest_result` now returns `graded: all_supported or all_unsupported` — a fully unsupported
session reports `graded: True` with coverage 0 and null score, meaning "grading reached a
determinate conclusion" rather than "a score exists". The test asserts the old meaning. Either move
it to the coverage contract or give the determinate-but-unscorable case its own field. This is
exactly the shape the power rows take, so decide before scoring them.

## Next

1. Classify + back off the Kattis quota rejection; persist retry state.
2. Wire rubric judging into the contest-session path so the 26 power sessions can be scored (settle
   the `graded` semantics first).
3. Finish the 24-job ICPC sweep and the OTC arm of the 43-session ARML sweep (6/43 done).
4. Audit gap 2: separate candidate from tests, retain per-task counterexamples, require rejected
   counterexamples to be addressed. Not an unconditional reviewer veto.
5. Audit gap 3: task-wide attempt budget or cooldown after repeated official failure.
6. Fix the three Vanilla preconditions above.

Budgets are equal *limits*, not equal consumption — OTC's Coach draws on the shared API budget and
OTC always spends more tokens. Every paired result is one stochastic run per variant.
