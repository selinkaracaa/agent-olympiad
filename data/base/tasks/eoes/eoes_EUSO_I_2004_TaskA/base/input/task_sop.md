# Task SOP

## Reference Environment
- Competition: EOES / EUSO
- Competition id: `eoes`
- Problem id: `eoes_EUSO_I_2004_TaskA`
- Task type: `lab_experiment`
- Team size: 3
- Year / edition: 2004
- Source: https://www.eoes.science/Previous%20olympiads/previous.html

## Goal
As a multi-agent team, solve the olympiad-style team task using only the materials under `base/input`. Produce the required deliverable (`team_submission`).

## Task directory
- Variant root: `base`
- Input directory: `base/input`
- Software fixtures: `base/software`

## Inputs
- `problem.md`
- `EUSO_I_2004_TaskA.pdf`

## Title
EUSO_I_2004_TaskA

## Deterministic Evaluation Rule
Gold answers and official solution booklets are not provided in `input/`. Scoring uses the evaluator declared on the task card (gold match, rubric LLM judge, slide judge, or deferred sandbox).

## Deliverables
Return the team `team_submission` expected by this competition.
