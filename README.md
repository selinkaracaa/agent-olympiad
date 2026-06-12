# Agent Olympiad — Economics Benchmark (IEO)

A curated dataset of **5 open-ended problems** from the **International Economics Olympiad (IEO)** selected for their agentic properties — multi-step modeling, dynamic systems, and strategic reasoning that goes beyond recall.

This is part of the broader **Agent Olympiad** research project at DAPLab, which aims to create the first benchmark suite focused exclusively on *agentic* tasks drawn from international academic competitions across diverse subjects (economics, geography, linguistics, physics lab sections, etc.).

## Why This Dataset

Existing AI benchmarks focus heavily on paper-based math and physics (AMC, IMO, etc.). This dataset targets tasks that require:

- **Multi-step strategic reasoning** (Game theory, Nash equilibria)
- **Dynamic/iterative environment interaction** (Time-lagged markets, bandwagon feedback loops)
- **Policy design under uncertainty** (Counterfactual analysis, LLM-as-judge scoring)
- **Path dependence and multiple equilibria** (Bandwagon effects, policy hysteresis)

## Repository Structure

```
agent-olympiad/
├── README.md
├── run_experiment.py          # Experiment runner (supports Perplexity Sonar + Agent APIs)
├── data/
│   ├── raw/                   # Original IEO exam PDFs (2018–2025)
│   └── processed/
│       ├── ieo_benchmark.json                    # Structured benchmark (5 open questions + business case)
│       ├── results_<model>.json                  # Raw single-agent results per model
│       ├── results_summary.md                    # Multi-model score comparison (open questions)
│       ├── results_multiagent_summary.md         # Business case multi-agent results summary
│       └── multiagent_<model>_judgedby_<judge>.json  # Full multi-agent discussion + report + score
```

## Dataset Summary

Questions were selected for **agentic properties**: iterative reasoning, dynamic systems, mechanism design, and counterintuitive results that require working through a model step by step.

| Problem ID | Year | Topic | Agentic Properties |
|---|---|---|---|
| econ_ieo_2019_q1 | 2019 | Mechanism Design | Sequential game theory, creative mechanism design |
| econ_ieo_2020_q2 | 2020 | Optimal Lockdown | Nash equilibrium vs social optimum, integer optimization |
| econ_ieo_2021_q1 | 2021 | Dynamic Equilibrium | Cobweb model, multi-period divergence |
| econ_ieo_2022_q5 | 2022 | Going Green (Bandwagon Effect) | Iterative equilibrium, multiple equilibria, path dependence |
| econ_ieo_2025_q1 | 2025 | Buying Cars | Prisoner's dilemma, policy design, repeated game theory |

## JSON Schema

Each entry in `ieo_benchmark.json` follows this structure:

```json
{
  "problem_id": "econ_ieo_YYYY_qN",
  "competition": "International Economics Olympiad",
  "year": 2025,
  "topic": "Topic Name",
  "source_file": "data/raw/YYYY.pdf",
  "task_type": "open_question",
  "problem_description": "Full problem text...",
  "gold_label": {
    "grading_rubric": ["Criterion 1 (X points)", "..."],
    "expected_answer": "Reference solution summary..."
  }
}
```

## Evaluation

Evaluation uses an **LLM-as-judge** approach: an agent attempts the problem, and a judge model scores the response against the `grading_rubric` criteria. This is a first-pass approach intended to establish baseline agent performance and identify evaluation challenges for future work.

## Sources

All problems are from official IEO Open Questions booklets (2018–2025). Raw PDFs are in `data/raw/`.

- IEO Official Site: [https://ieo.world](https://ieo.world)
