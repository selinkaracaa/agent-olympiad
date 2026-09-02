# Phase B — combined meeting summary

### How to read a cell

Each cell is **task · CS · IHS** (when scored).

| Symbol | Meaning |
|---|---|
| **task** | Correctness vs gold (scale in section title) |
| **CS** | MultiAgentBench coordination (0–5): communication/planning *process* |
| **IHS** | Interaction helpfulness (0–5): whether chat helped the *final answers* |

`—` = cell not run yet. **Hetero × single_agent** uses GPT mini only (one Solo seat).

# Wave 1 — Math & programming (rules off)
_55/80 cells complete · rules=off_

## arml_local (arml_local_2009) task/40

ARML Local Team Round — short-answer math sheet for a six-person school team (10 problems, gold **/40**); no calculators or outside help.

| Team | single | centr. | round | decen. |
|---|---:|---:|---:|---:|
| gpt | 4.44444/40 · CS 1.0 | 26.6667/40 · CS 4.0 | 22.2222/40 · CS 3.0 | 17.7778/40 · CS 3.5 |
| claude | 35.5556/40 · CS 0.5 | 22.2222/40 · CS 4.0 | 35.5556/40 · CS 3.0 | 26.6667/40 · CS 3.5 |
| gemini | 40/40 · CS 1.0 | 35.5556/40 · CS 3.5 | 35.5556/40 · CS 3.5 | 40/40 · CS 3.0 |
| hetero | 13.3333/40 · CS 0.5 | 35.5556/40 · CS 3.5 | 40/40 · CS 3.0 | 40/40 · CS 3.5 |

**Solo → best multi:** gpt: 4.44444 → 26.6667 (Δ +22.2); claude: 35.5556 → 35.5556 (Δ +0.0); gemini: 40 → 40 (Δ +0.0); hetero: 13.3333 → 40 (Δ +26.7)

## arml_national_team (arml_national_team_2009) task/50

ARML National Team Round — harder national-meet short answers (team **/50**); denser olympiad-style problems under time pressure.

| Team | single | centr. | round | decen. |
|---|---:|---:|---:|---:|
| gpt | 37.5/50 · CS 0.5 | 37.5/50 · CS 4.0 | 43.75/50 · CS 3.5 | 43.75/50 · CS 3.5 |
| claude | 43.75/50 · CS 0.5 | 43.75/50 · CS 4.0 | 43.75/50 · CS 1.0 | 43.75/50 · CS 0.5 |
| gemini | 37.5/50 · CS 2.0 | 37.5/50 · CS 4.0 | 37.5/50 · CS 0.5 | 37.5/50 · CS 1.0 |
| hetero | 37.5/50 · CS 0.5 | 43.75/50 · CS 4.0 | 37.5/50 · CS 3.5 | 43.75/50 · CS 4.0 |

**Solo → best multi:** gpt: 37.5 → 43.75 (Δ +6.2); claude: 43.75 → 43.75 (Δ +0.0); gemini: 37.5 → 37.5 (Δ +0.0); hetero: 37.5 → 43.75 (Δ +6.2)

## purple_comet (purple_comet_hs_2024) task/30

Purple Comet HS — online team math packet (**30** short numeric answers, **/30**); broad HS contest math suited to splitting work.

| Team | single | centr. | round | decen. |
|---|---:|---:|---:|---:|
| gpt | 5/30 · CS 3.5 | 7/30 · CS 3.5 | 4/30 · CS 3.0 | 7/30 · CS 3.0 |
| claude | 26/30 · CS 0.5 | 27/30 · CS 3.0 | 20/30 · CS 3.5 | 18/30 · CS 3.0 |
| gemini | 26/30 · CS 2.5 | 0/30 · CS 2.0 | 27/30 · CS 2.0 | 28/30 · CS 2.5 |
| hetero | 1/30 · CS 3.0 | 3/30 · CS 3.0 | 1/30 · CS 2.5 | 13/30 · CS 2.5 |

**Solo → best multi:** gpt: 5 → 7 (Δ +2.0); claude: 26 → 27 (Δ +1.0); gemini: 26 → 28 (Δ +2.0); hetero: 1 → 13 (Δ +12.0)

## hmmt_guts (hmmt_guts_2024) task/50

HMMT Guts — among the hardest US HS team contests; timed guts short answers (**/50**), team of 8.

| Team | single | centr. | round | decen. |
|---|---:|---:|---:|---:|
| gpt | 8.33333/50 · CS 3.5 | 5.55556/50 · CS 3.5 | 1.38889/50 · CS 3.5 | 4.16667/50 · CS 3.0 |
| claude | 23.6111/50 · CS 1.5 | 30.5556/50 · CS 3.5 | 25/50 · CS 3.0 | — |
| gemini | — | — | — | — |
| hetero | — | — | — | — |

**Solo → best multi:** gpt: 8.33333 → 5.55556 (Δ -2.8); claude: 23.6111 → 30.5556 (Δ +6.9)

---

# Wave 2 — Non-math domains (rules enforced)
_43/64 cells complete · rules=enforced_

## ieo_business_case (ieo_business_case_2021) task/50

International Economics Olympiad — **Business Case** (2021 RAF2021). Team of 5 recommends what vehicle/strategy a revived Latvian automaker should pursue and defends it as a slide deck; web search allowed; graded by slide rubric.

| Team | single | centr. | round | decen. |
|---|---:|---:|---:|---:|
| gpt | 34/50 · CS 1.0 · IHS 3.0 | 32/50 · CS 4.0 · IHS 4.0 | 31.5/50 · CS 4.0 · IHS 4.0 | 33/50 · CS 4.0 · IHS 5.0 |
| claude | 41.5/50 · CS 1.0 · IHS 3.0 | 40/50 · CS 4.0 · IHS 4.0 | 43/50 · CS 2.0 · IHS 4.0 | 40/50 · CS 2.0 · IHS 4.0 |
| gemini | 32.5/50 · CS 0.5 · IHS 3.0 | 36/50 · CS 3.0 · IHS 4.0 | 33.5/50 · CS 1.0 · IHS 3.0 | 31.5/50 · CS 2.5 · IHS 3.0 |
| hetero | 31/50 · CS 0.5 · IHS 0.0 | 32/50 · CS 4.0 · IHS 5.0 | 30.5/50 · CS 4.0 · IHS 4.0 | 35/50 · CS 4.0 · IHS 4.0 |

**Solo → best multi:** gpt: 34 → 33 (Δ -1.0); claude: 41.5 → 43 (Δ +1.5); gemini: 32.5 → 36 (Δ +3.5); hetero: 31 → 35 (Δ +4.0)

## iol_team (iol_team_2005) task/100

International Linguistics Olympiad — **Team Contest** (Figuig 2005). Team of 4 reverse-engineers a Berber language from sentence translations: orthography, transcriptions, and translations; graded by rubric LLM on worked answers.

| Team | single | centr. | round | decen. |
|---|---:|---:|---:|---:|
| gpt | 5/100 · CS 0.5 · IHS 1.0 | 0/100 · CS 2.5 · IHS 0.0 | 0/100 · CS 1.5 · IHS 1.0 | 0/100 · CS 2.0 · IHS 0.0 |
| claude | 57/100 · CS 0.5 · IHS 2.0 | 5/100 · CS 2.0 · IHS 1.0 | 55/100 · CS 1.5 · IHS 2.0 | 55/100 · CS 2.5 · IHS 3.0 |
| gemini | 48/100 · CS 1.0 · IHS 2.0 | 42/100 · CS 3.0 · IHS 3.0 | 54/100 · CS 2.5 · IHS 3.0 | 50/100 · CS 2.5 · IHS 3.0 |
| hetero | 1/100 · CS 0.5 · IHS 0.0 | 0/100 · CS 2.5 · IHS 0.0 | 37/100 · CS 2.0 · IHS 2.0 | 0/100 · CS 3.0 · IHS 0.0 |

**Solo → best multi:** gpt: 5 → 0 (Δ -5.0); claude: 57 → 55 (Δ -2.0); gemini: 48 → 54 (Δ +6.0); hetero: 1 → 37 (Δ +36.0)

## ioaa_group (ioaa_group_2025) task/1

International Olympiad on Astronomy and Astrophysics — **Group round** (2025). Team of 5 runs a radio-telescope HI-line lab to estimate Galactic rotation and dark matter; real contest needs instrument CSVs (text-only proxy here).

| Team | single | centr. | round | decen. |
|---|---:|---:|---:|---:|
| gpt | 0/1 · CS 0.5 · IHS 0.0 | 0/1 · CS 2.5 · IHS 1.0 | 0/1 · CS 3.5 · IHS 2.0 | 0/1 · CS 2.0 · IHS 0.0 |
| claude | 0/1 · CS 1.0 · IHS 1.0 | 0/1 · CS 4.0 · IHS 1.0 | 0/1 · CS 1.5 · IHS 2.0 | 0/1 · CS 1.5 · IHS 2.0 |
| gemini | 0/1 · CS 1.0 · IHS 0.0 | 0/1 · CS 2.5 · IHS 2.0 | 0/1 · CS 3.0 · IHS 2.0 | — |
| hetero | — | — | — | — |

**Solo → best multi:** gpt: 0 → 0 (Δ +0.0); claude: 0 → 0 (Δ +0.0); gemini: 0 → 0 (Δ +0.0)
