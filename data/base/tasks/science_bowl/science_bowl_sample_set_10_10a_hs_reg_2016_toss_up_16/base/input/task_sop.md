# Task SOP

## Reference Environment
- Competition: DOE Science Bowl
- Competition id: `science_bowl`
- Problem id: `science_bowl_sample_set_10_10a_hs_reg_2016_toss_up_16`
- Task type: `science_bowl`
- Team size: 4
- Year / edition: 2016
- Source: https://science.osti.gov/wdts/nsb

## Goal
As a multi-agent team, solve the olympiad-style team task using only the materials under `base/input`. Produce the required deliverable (`team_submission`).

## Task directory
- Variant root: `base`
- Input directory: `base/input`

## Inputs
- `problem.md`
- `10A_HS_Reg_2016.pdf`

## Title
Biology / Multiple Choice / toss_up

## Deterministic Evaluation Rule
Gold answers and official solution booklets are not provided in `input/`. Scoring uses the evaluator declared on the task card (gold match, rubric LLM judge, slide judge, or deferred sandbox).

## Deliverables
Return the team `team_submission` expected by this competition.
