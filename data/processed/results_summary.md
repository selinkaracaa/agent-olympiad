# Experiment Results — Multi-Model Comparison

**Benchmark:** IEO Agentic Questions (5 questions, 30 pts each)  
**Judge:** same model as agent (self-judging — see observations)

## Score Summary

| Topic | gemini-2.5-flash-lite | sonar-pro | anthropic/claude-sonnet-4-6 | openai/gpt-5.5 |
|---|---|---|---|---|
| Mechanism Design (2019) | **25/30** | **10/30** | **20/30** | **30/30** |
| Dynamic Equilibrium (2021) | **30/30** | **10/30** | **30/30** | **30/30** |
| Going Green (2022) | **26/30** | **22/30** | **28/30** | **30/30** |
| Optimal Lockdown (2020) | **28/30** | **30/30** | **30/30** | **28/30** |
| Buying Cars (2025) | **30/30** | **30/30** | **30/30** | **30/30** |
| **TOTAL /150** | **139/150** | **102/150** | **138/150** | **148/150** |

## Key Observations

- **Self-judging bias**: each model judges its own answers, inflating scores for stronger models
- **sonar-pro** is the most honest signal: 102/150, struggling on Mechanism Design and Dynamic Equilibrium
- **Claude Sonnet** loses 10 pts on Mechanism Design (part b) — cannot fully design the mechanism
- **Next step**: use a fixed external judge for all models to remove bias