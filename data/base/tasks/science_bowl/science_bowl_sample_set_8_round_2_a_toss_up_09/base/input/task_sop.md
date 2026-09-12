# Task SOP

## Reference Environment
- Competition: DOE Science Bowl
- Competition id: `science_bowl`
- Problem id: `science_bowl_sample_set_8_round_2_a_toss_up_09`
- Task type: `science_bowl`
- Team size: 4
- Source: https://science.osti.gov/wdts/nsb

## Goal
As a multi-agent team, solve the olympiad-style team task using only the materials under `base/input`. Produce the required deliverable (`team_submission`).

## Task directory
- Variant root: `base`
- Input directory: `base/input`

## Inputs
- `problem.md`
- `Round-2-A.pdf`

## Title
EARTH AND SPACE / Short Answer / toss_up

## Deterministic Evaluation Rule
Gold answers and official solution booklets are not provided in `input/`. Scoring uses the evaluator declared on the task card (gold match, rubric LLM judge, slide judge, or deferred sandbox).

## Deliverables
Return the team `team_submission` expected by this competition.
