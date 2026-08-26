# Task SOP

## Reference Environment
- Competition: ARML National Meet — Team Round
- Competition id: `arml_national_team`
- Problem id: `arml_national_team_2009`
- Task type: `team_contest`
- Team size: 15
- Year / edition: 2009
- Source: https://www.arml.com/ARML/arml_2019/public_contest_files/2009_2014_book/ARML_2009_2014.pdf

## Goal
As a multi-agent team, solve the olympiad-style team task using only the materials under `base/input`. Produce the required deliverable (`answer_sheet`).

## Task directory
- Variant root: `base`
- Input directory: `base/input`

## Inputs
- `problem.md`
- `ARML_2009_2014.pdf`

## Title
Team Round — 2009

## Deterministic Evaluation Rule
Gold answers and official solution booklets are not provided in `input/`. Scoring uses the evaluator declared on the task card (gold match, rubric LLM judge, slide judge, or deferred sandbox).

## Deliverables
Return the team `answer_sheet` expected by this competition.
