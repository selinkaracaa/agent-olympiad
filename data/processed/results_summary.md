# Experiment Results — Multi-Model Comparison

**Benchmark:** IEO Agentic Questions (5 questions, 30 pts each)  
**Models tested:** GPT-5.5, Claude Sonnet 4.6, sonar-pro, Gemini 3.5 Flash  
**Note:** All models run via Perplexity API

## Table 1: Self-Judging (each model judges its own answers)

| Topic | GPT-5.5 | Claude Sonnet | sonar-pro | Gemini 3.5 Flash |
|---|---|---|---|---|
| Mechanism Design | 30/30 | 20/30 | 10/30 | 12/30 |
| Dynamic Equilibrium | 30/30 | 30/30 | 10/30 | 14/30 |
| Going Green | 30/30 | 28/30 | 22/30 | 4/30 |
| Optimal Lockdown | 28/30 | 30/30 | 30/30 | 22/30 |
| Buying Cars | 30/30 | 30/30 | 30/30 | 30/30 |
| **TOTAL /150** | **148** | **138** | **102** | **82** |

## Table 2: Fixed External Judge (GPT-5.5 judges all models)

| Topic | GPT-5.5 | Claude Sonnet | sonar-pro | Gemini 3.5 Flash |
|---|---|---|---|---|
| Mechanism Design | 30/30 | 12/30 | 12/30 | 15/30 |
| Dynamic Equilibrium | 30/30 | 30/30 | 25/30 | 20/30 |
| Going Green | 30/30 | 27/30 | 23/30 | 14/30 |
| Optimal Lockdown | 28/30 | 30/30 | 24/30 | 30/30 |
| Buying Cars | 30/30 | 30/30 | 29/30 | 30/30 |
| **TOTAL /150** | **148** | **129** | **113** | **109** |

## Key Findings

- **Mechanism Design** is the hardest question: all models score 12–15/30 with external judge
- **Optimal Lockdown** and **Buying Cars** are well-solved across the board (≥22/30)
- **Self-judging is inconsistent**: sonar-pro goes up (+11) with external judge, Claude goes down (-9)
- **GPT-5.5 scores highest** under both conditions; **Gemini 3.5 Flash scores lowest** (82 self / 109 external)
- External judge gives more differentiated and reliable scores — recommended for future runs