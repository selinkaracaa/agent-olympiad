# Agent Olympiad — Economics Benchmark (IEO)

A curated dataset of 10 open-ended problems from the **International Economics Olympiad (IEO)** designed to benchmark agentic AI systems on multi-step economic reasoning tasks.

This is part of the broader **Agent Olympiad** research project at DAPLab, which aims to create the first benchmark suite focused exclusively on *agentic* tasks drawn from international academic competitions across diverse subjects (economics, geography, linguistics, physics lab sections, etc.).

## Why This Dataset

Existing AI benchmarks focus heavily on paper-based math and physics (AMC, IMO, etc.). This dataset targets tasks that require:

- **Multi-step strategic reasoning** (Game theory, Nash equilibria)
- **Dynamic/iterative environment interaction** (Time-lagged markets, bandwagon feedback loops)
- **Policy design under uncertainty** (Counterfactual analysis, LLM-as-judge scoring)
- **Data interpretation with blind spots** (Inequality measurement, securitization paradoxes)

## Repository Structure

```
agent-olympiad-econ/
├── README.md
├── data/
│   ├── raw/               # Original IEO exam PDFs (2018–2025)
│   └── processed/
│       └── ieo_benchmark.json   # Structured benchmark dataset
```

## Dataset Summary

| Problem ID | Year | Topic |
|---|---|---|
| econ_ieo_2019_q1 | 2019 | Mechanism Design (Cake Cutting) |
| econ_ieo_2019_q5 | 2019 | Short Run vs Long Run / Adverse Selection |
| econ_ieo_2020_q2 | 2020 | Optimal Lockdown / Nash Equilibrium vs Social Optimum |
| econ_ieo_2021_q1 | 2021 | Dynamic Equilibrium (Oil & Gas Markets) |
| econ_ieo_2021_q3 | 2021 | Pandemic Possibility Frontier |
| econ_ieo_2021_q5 | 2021 | Vaccination Dilemmas / Crowding Out |
| econ_ieo_2022_q1 | 2022 | Measuring Inequality / Data Bias |
| econ_ieo_2022_q5 | 2022 | Bandwagon Effect / Solar Panels |
| econ_ieo_2024_q1 | 2024 | Mortgage Securitization / Adverse Selection |
| econ_ieo_2025_q1 | 2025 | Conspicuous Consumption / Signaling Game |

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
