# Task SOP

## Reference Environment
- Competition: DOE Science Bowl
- Competition id: `science_bowl`
- Problem id: `science_bowl_sample_set_16_set_10_hs_2021_toss_up_01`
- Task type: `science_bowl`
- Team size: 4
- Year / edition: 2021
- Source: https://science.osti.gov/wdts/nsb

## Goal
As a multi-agent team, solve the olympiad-style team task using only the materials under `base/input`. Produce the required deliverable (`team_submission`).

## Task directory
- Variant root: `base`
- Input directory: `base/input`

## Inputs
- `problem.md`
- `Set-10-HS-2021.pdf`

## Title
Physics / Short Answer / toss_up

## Deterministic Evaluation Rule
Gold answers and official solution booklets are not provided in `input/`. Scoring uses the evaluator declared on the task card (gold match, rubric LLM judge, slide judge, or deferred sandbox).

## Deliverables
Return the team `team_submission` expected by this competition.
