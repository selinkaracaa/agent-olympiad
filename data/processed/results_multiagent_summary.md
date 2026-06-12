# Multi-Agent Business Case Results

**Case:** IEO 2025 — The Caspian Connector (`econ_ieo_2025_bc`)  
**Setup:** 5 agents, 3 discussion rounds, no pre-assigned roles, emergent collaboration  
**Format:** Written report (substitutes for oral presentation + slides)

## Scores (GPT-5.5 external judge, /50)

| Agents | Judge | Analytical | Conceptual | Quantitative | Communication | **Total** |
|---|---|---|---|---|---|---|
| GPT-5.5 (5 agents) | GPT-5.5 | 14/15 | 14/15 | 9/10 | 9/10 | **46/50** |

## Human baseline (2025 IEO, same case)

From [2025 IEO results](https://2025.ieo-official.org/results):

| Team | Raw score | Notes |
|---|---|---|
| Canada (1st place) | 92.5 | Only winner's raw score published |
| Other finalists | N/A | Full ranking not published |

Human teams are scored by a professional jury using the official 4-dimension rubric. Raw scores are normalized to final /50 points via Z-scores. Direct comparison to our LLM judge scores is approximate.

## Key finding from discussion

Agents self-organized without assigned roles — Agent 1 took a leadership/framework role in Round 1, and by Round 3 agents explicitly volunteered to draft specific report sections. All agents opened with "I agree" (sycophancy pattern), but coverage diversified across geopolitics, financing, legal/environmental, and alternatives.

## Recommendation

GPT-5.5 team recommended **deferring the fixed link** and pursuing modular ferry/port upgrades ("Caspian Crossing 2.0") rather than a bilateral tariff-funded JV.

## Files

- Raw results: `multiagent_openai_gpt-5_5_judgedby_openai_gpt-5_5.json`
- Case source: `data/raw/business_case/2025.pdf`
- Script: `run_multiagent_experiment.py`
