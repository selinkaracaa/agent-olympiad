# Task SOP

## Reference Environment
- Competition: DebateBench (WUDC / BP)
- Competition id: `debatebench`
- Problem id: `debatebench_doxbridge_worlds_2021_west_round_5`
- Task type: `bp_debate_transcript`
- Team size: 8
- Year / edition: 2021

## Goal
As a multi-agent team, solve the olympiad-style team task using only the materials under `base/input`. Produce the required deliverable (`team_submission`).

## Task directory
- Variant root: `base`
- Input directory: `base/input`

## Inputs
- `problem.md`
- `doxbridge_worlds_2021_west_round_5.txt`

## Title
doxbridge_worlds_2021_west_round_5

## Deterministic Evaluation Rule
Gold answers and official solution booklets are not provided in `input/`. Scoring uses the evaluator declared on the task card (gold match, rubric LLM judge, slide judge, or deferred sandbox).

## Deliverables
Return the team `team_submission` expected by this competition.
