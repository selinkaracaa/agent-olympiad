# Experiment Results — Multi-Model Comparison

**Benchmark:** IEO Agentic Questions (5 questions)  
**Judge:** same model as agent (LLM-as-judge)

## Score Summary

| Topic (Year) | gemini-2.5-flash-lite | sonar-pro |
|---|---|---|
| Mechanism Design (q1) | **25/30** | **10/30** |
| Dynamic Equilibrium (q1) | **30/30** | **10/30** |
| Going Green (q5) | **26/30** | **22/30** |
| Optimal Lockdown (q2) | **28/30** | **30/30** |
| Buying Cars (q1) | **30/30** | **30/30** |
| **TOTAL** | **139/150** | **102/150** |

## Key Observations

- High scores may reflect lenient self-judging (same model judges itself)
- sonar-pro scores vary widely (10–30/30), suggesting these questions do challenge some models
- Dynamic Equilibrium and Mechanism Design are the hardest questions for sonar-pro
- Future work: use a fixed strong judge (e.g. Claude) to remove self-judging bias