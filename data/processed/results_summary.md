# Experiment Results — Multi-Model Comparison

**Benchmark:** IEO Agentic Questions (5 questions, 30 pts each)  

## Table 1: Self-Judging (each model judges itself)

| Topic | Gemini 2.5 Flash Lite | sonar-pro | Claude Sonnet 4.6 | GPT-5.5 |
|---|---|---|---|---|
| Mechanism Design | 25/30 | 10/30 | 20/30 | 30/30 |
| Dynamic Equilibrium | 30/30 | 10/30 | 30/30 | 30/30 |
| Going Green | 26/30 | 22/30 | 28/30 | 30/30 |
| Optimal Lockdown | 28/30 | 30/30 | 30/30 | 28/30 |
| Buying Cars | 30/30 | 30/30 | 30/30 | 30/30 |
| **TOTAL** | **139/150** | **102/150** | **138/150** | **148/150** |

## Table 2: External Judge (GPT-5.5 judges all)

| Topic | Gemini 3.1 Flash Lite | sonar-pro | Claude Sonnet 4.6 |
|---|---|---|---|
| Mechanism Design | 12/30 | 12/30 | 12/30 |
| Dynamic Equilibrium | 20/30 | 25/30 | 30/30 |
| Going Green | 19/30 | 23/30 | 27/30 |
| Optimal Lockdown | 30/30 | 24/30 | 30/30 |
| Buying Cars | 30/30 | 29/30 | 30/30 |
| **TOTAL** | **111/150** | **113/150** | **129/150** |

## Key Observations

- Self-judging is **inconsistent**: sonar-pro scores higher with external judge (+11), Claude scores lower (-9)
- With a fixed external judge, **Mechanism Design** is the hardest question across all models (12/30)
- **Optimal Lockdown** and **Buying Cars** are consistently well-solved (≥24/30)
- These results suggest the benchmark differentiates models, supporting the case for a fixed external judge in all future runs