# Task SOP

## Reference Environment
- Competition: ARML National Meet — Team Round
- Competition id: `arml_national_team`
- Problem id: `arml_national_team_2019`
- Task type: `team_contest`
- Team size: 15
- Year / edition: 2019
- Source: https://www.arml.com/ARML/arml_2019/public_contest_files/2019_contest_file/2019_Contest_Final_Version.pdf

## Goal
As a multi-agent team, solve the olympiad-style team task using only the materials under `base/input`. Produce the required deliverable (`answer_sheet`).

## Task directory
- Variant root: `base`
- Input directory: `base/input`

## Inputs
- `problem.md`
- `2019_Contest_Final_Version.pdf`

## Title
Team Round — 2019

## Deterministic Evaluation Rule
Gold answers and official solution booklets are not provided in `input/`. Scoring uses the evaluator declared on the task card (gold match, rubric LLM judge, slide judge, or deferred sandbox).

## Deliverables
Return the team `answer_sheet` expected by this competition.
