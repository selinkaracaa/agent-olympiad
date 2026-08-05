# Agent Olympiad — `data/base` (ALE-style task inputs)

Agent-facing task materials reshaped to match the
[Agents Last Exam task-input layout](https://huggingface.co/datasets/agents-last-exam/agents-last-exam-data)
(see e.g.
[`amber_three_stage_mmgbsa_workflow_instance_1/base`](https://huggingface.co/datasets/agents-last-exam/agents-last-exam-data/tree/main/tasks/life_sciences/amber_three_stage_mmgbsa_workflow_instance_1)).

This tree is **generated** from `data/benchmarks` (+ optional `pipeline/rules`
and `data/raw/*/runtime.json`). The original `benchmarks/`, `raw/`, `rubrics/`,
and `evaluators/` trees are unchanged.

## Layout

```
data/base/
  README.md
  task_cards.json              # catalog (ALE task-card analogue)
  tasks/
    <competition_id>/          # e.g. iol_team, ieo_business_case
      <problem_id>/
        base/                  # default variant (ALE naming)
          input/               # files the agent receives at run start
            task_sop.md
            input_environment_spec.md
            problem.md         # when text description exists
            <source assets>    # symlink, or *.path pointer on Windows
          software/            # only when a runtime.json exists
            README.txt
```

## What’s included vs excluded

| Included in `base/input` | Excluded (like ALE reference split) |
|---|---|
| Task SOP + environment spec | Official solution PDFs |
| Problem text (`problem.md`) | `gold_label.expected_answer` / parts |
| Agent-visible source packets | Rubric JSON bodies (path only in spec) |

Gold / solution pointers remain on each entry in `task_cards.json`
(`has_gold_answer`, `solution_file`, `evaluation`).

## Regenerate

```bash
python collectors/build_ale_base.py --clean
# smoke:
python collectors/build_ale_base.py --clean --competitions iol_team ieo_business_case --limit-per-competition 2
```

## Relation to existing data

| Path | Role |
|---|---|
| `data/benchmarks/` | Source of truth for extracted problem JSON |
| `data/raw/` | Original PDFs / upstream checkouts |
| `data/rubrics/`, `data/evaluators/` | Scoring assets (not staged into `input/`) |
| `data/base/` | ALE-shaped **input** packaging for agent runs |
