ARML 2009 paired protocol check — 2026-09-06

> Prior contest-session gold + National/History routing results:
> [contest-session-gold-suite-20260903.md](contest-session-gold-suite-20260903.md) §3.1,
> [contest-session-followups-20260904.md](contest-session-followups-20260904.md).

Scope: current `agent-team-features-main` working tree. Existing user changes
remain in place. OTC means the manifest-based `strategic_team`, not the older
`--schema open_table_coach` lifecycle. This change does not claim native support
for every competition or add missing rubric/physical contest environments.

**Implemented corrections**

- Python execution, Python sample judging, and failing-sample output diagnostics
  now run in Docker. Only source code is mounted and input is streamed. Gold,
  repository files, host credentials, and network access are unavailable to the
  agent process. There is no automatic host fallback. The pinned image was
  downloaded and arithmetic, host-file isolation, timeout, output limit, and
  backend-unavailable tests were executed locally.
- Answer-section stripping occurs before either split or packet prompts.
  Numbered parts accept both `1.` and `1)`; explicit split failure and unknown
  requested IDs raise errors instead of silently returning an unsplit packet.
- Known contests use the environment's tool allowlist. ARML no longer advertises
  a calculator that execution rejects. MCM receives code computation without
  being reclassified as a programming submission task.
- A review-only assignment can now schedule non-programming work. Reviewers get
  the full target prompt and exact answer version, including final review,
  rather than relying on a truncated preview of another active task.
- Unsupported/missing non-programming gold is reported as unavailable with null
  task scores. It is excluded from supported-score denominators. Results expose
  evaluation coverage; a session with no gradable tasks has null utility.
- Deadline collection is shared by vanilla and OTC. Both retain their final
  model action for useful work; the environment then submits pending drafts.
  Missing answers remain blank. The baseline retains no Coach, enforced coach
  assignment, strategic memory, or mandatory review.
- The first live check exposed repeated baseline attempts to submit an
  incomplete sheet. That action is now hidden for both variants until the base
  submission contract permits it. This is environment validation, not a new
  baseline planning policy.

**Verification**

296 tests passed across the repository, including new regressions for the
vanilla action surface, duplicate-answer identity, next-unseen progression,
shared stall recovery, and complete-sheet submission. The original seven audit
checks also passed after correction (six reproduced defects plus one check of
the documented output-only budget).

The first paired live run is retained at
`results/arml_local_2009_protocol_v2_20260906/` as a diagnostic run. It used the
shared deadline policy but preceded the additional incomplete-sheet action
filter. Vanilla answered 1/9 and OTC 7/9. These are not the final paired results.

The earlier final v2 run is retained at
`results/arml_local_2009_protocol_v2_final_20260906/`. It exposed the main
baseline defect: vanilla could see review actions, every `work` call created
another immutable version even when content was identical, and only the
strategic branch had automatic stalled-task switching. The active-task prompt
therefore kept returning vanilla to the first problem. This was a
runtime/protocol defect rather than evidence that the base model inherently
prefers the first problem.

Protocol v3 separates the baseline from the OTC review workflow:

- vanilla never receives `request_review` or `review_answer`;
- an identical draft is a no-op, preserving its version and existing reviews;
- after vanilla records an answer-sheet draft, contest control advances to the
  first unseen task;
- the stall guard applies to both variants, while vanilla control moves are
  counted separately as `baseline_mechanical_switches`; and
- after every required vanilla draft exists, only `submit` is exposed, avoiding
  a new rewrite loop on the final task.

The final v3 paired run is at
`results/arml_local_2009_protocol_v3_final_20260906/`.
Its `paired_config.json` records input/source hashes and identical model,
team-size, task IDs, and budget limits. Each variant has its own command,
checkpoint, log, and final result. `paired_summary.json` contains scores,
submission coverage, action errors, API/output-token usage, and metrics.

| v3 final run | Correct | Score / 40 | Submitted | Turns | API calls | Output tokens | Session seconds | Action errors |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Vanilla | 4/9 (44.44%) | 17.78 | 9/9 | 4 | 11 | 3,767 | 39.77 | 0 |
| OTC | 5/9 (55.56%) | 22.22 | 9/9 | 16 | 49 | 14,730 | 172.56 | 1 |

Vanilla's final action trace is one selection, nine draft writes, and one
submission. Every problem has exactly one answer version; its eight cursor
moves are all recorded as baseline mechanical switches. OTC completes per-task
and final review, with 100% review and final-review coverage. Its one action
error is a model response with no native function call; the run recovered and
had zero transport failures. Both variants explicitly submitted the complete
sheet and have 100% grading coverage.

Vanilla answered Q1, Q2, Q4, and Q9 correctly. OTC answered Q2, Q4, Q6, Q7,
and Q8 correctly. This single paired sample shows that the repaired baseline
now covers the contest and that OTC achieved one additional correct answer; it
does not estimate a stable treatment effect.

Collaboration judge CS was 1.0 for Vanilla and 4.0 for OTC. Report CS alongside
outcomes; do not treat it as a substitute for solved-task coverage or proof
correctness.

All recorded source/input hashes match the working files after completion, and
the live source snapshot was saved in `source_snapshot/`. Both result files and
the paired configuration record `contest_session_v3`. These runs used
`--no-judge-cce`.

**Experimental boundaries**

The selected manifest contains the nine deterministically graded ARML Local
2009 tasks. The repository rescales their points to a total of 40. This is a
single 3-agent paired pilot, using Perplexity `openai/gpt-5.4-mini`, native action
calling, 50 turns, 151 shared API calls, and a 220,000 output-token cap per team.
The Coach consumes the OTC shared API budget. These are equal limits, not equal
actual compute consumption. Input tokens are not included in the existing
output-token cap. The clock is the standardized 250 simulated minutes, not an
official-duration reproduction. Collaboration grading calls are external to
the contestant action budget. Live model sampling is stochastic, so repeated
runs are needed for comparative claims.

Run a fresh pair without overwriting earlier artifacts:

```powershell
../.venv/Scripts/python.exe -u scripts/run_arml_2009_protocol_check.py --output results/arml_2009_new_pair
```

Run from `agent-team-features-main`. Use a fresh output directory, not a
checkpoint from the previous protocol. The runner records
`protocol_version=contest_session_v3` and the shared deadline policy.
