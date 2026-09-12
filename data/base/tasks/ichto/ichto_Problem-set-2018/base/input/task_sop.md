# Task SOP

## Reference Environment
- Competition: International Chemistry Tournament
- Competition id: `ichto`
- Problem id: `ichto_Problem-set-2018`
- Task type: `chemistry_tournament_problem_set`
- Team size: 3
- Year / edition: 2018
- Source: http://ichto.org/en/problems/

## Goal
As a multi-agent team, solve the olympiad-style team task using only the materials under `base/input`. Produce the required deliverable (`team_submission`).

## Task directory
- Variant root: `base`
- Input directory: `base/input`

## Inputs
- `problem.md`
- `Problem-set-2018.pdf`

## Title
Problem-set-2018

## Deterministic Evaluation Rule
Gold answers and official solution booklets are not provided in `input/`. Scoring uses the evaluator declared on the task card (gold match, rubric LLM judge, slide judge, or deferred sandbox).

## Deliverables
Return the team `team_submission` expected by this competition.
