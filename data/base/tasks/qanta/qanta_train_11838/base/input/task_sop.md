# Task SOP

## Reference Environment
- Competition: QANTA Quiz Bowl
- Competition id: `qanta`
- Problem id: `qanta_train_11838`
- Task type: `quizbowl`
- Team size: 4
- Year / edition: 2001
- Source: https://www.qanta.org/

## Goal
As a multi-agent team, solve the olympiad-style team task using only the materials under `base/input`. Produce the required deliverable (`team_submission`).

## Task directory
- Variant root: `base`
- Input directory: `base/input`

## Inputs
- `problem.md`

## Title
Science

## Deterministic Evaluation Rule
Gold answers and official solution booklets are not provided in `input/`. Scoring uses the evaluator declared on the task card (gold match, rubric LLM judge, slide judge, or deferred sandbox).

## Deliverables
Return the team `team_submission` expected by this competition.
