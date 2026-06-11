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
## Table 3: Human Students vs LLM Models (External GPT-5.5 Judge)

*Human stats sourced from official IEO Final Reports (publicly available on ecolymp.org):*
- *2019: https://files.ecolymp.org/2019/IEO_Final_Report_2019.pdf*
- *2020: https://files.ecolymp.org/2020/IEO_Final_Report_2020.pdf*
- *2021: https://files.ecolymp.org/2021/IEO_Final_Report_2021.pdf*
- *2022 & 2025: Final Reports not yet accessible (server error / not yet published)*

| Question | Human Avg | Human Max | # Who Got Max | GPT-5.5 | Claude | sonar-pro | Gemini |
|---|---|---|---|---|---|---|---|
| Mechanism Design (2019) | 13.4/30 | 30/30 | 8 students | 30/30 | 12/30 | 12/30 | 15/30 |
| Optimal Lockdown (2020) | 15.1/30 | 30/30 | 5 students | 28/30 | 30/30 | 24/30 | 30/30 |
| Dynamic Equilibrium (2021) | 14.5/30 | 30/30 | 17 students | 30/30 | 30/30 | 25/30 | 20/30 |
| Going Green (2022) | N/A | N/A | N/A | 30/30 | 27/30 | 23/30 | 14/30 |
| Buying Cars (2025) | N/A | N/A | N/A | 30/30 | 30/30 | 29/30 | 30/30 |

### What this shows
- **Average human student scores 13–15/30** on these questions; LLMs score 24–30/30
- Only **5–17 students out of 50–171 attempted** achieved a perfect score — yet GPT-5.5 scores perfect on every question
- This suggests either (a) LLM judge is still too lenient, or (b) these questions are within LLMs' training distribution and don't challenge them as agentic tasks should
- **This is the core argument for why a new, truly agentic benchmark is needed**
