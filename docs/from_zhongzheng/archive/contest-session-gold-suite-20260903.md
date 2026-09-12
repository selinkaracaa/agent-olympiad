# Contest-session gold suite — OTC vs Vanilla (2026-09-03/04)

> Scope: deterministic structured-gold competitions on the **contest-session** path  
> Model: Perplexity `openai/gpt-5.4-mini`, native function calling, team size 3  
> Status: structured-gold **complete** (771 OTC + 771 Vanilla); ICPC OTC+vanilla **complete** (WF 2012 + WF 2014)  
> Protocol follow-ups **complete** — National clean + low-accuracy OTC rerun: session-weighted OTC Acc **~25.9%** (was 18.6%); History **64.4%**; MH still **0.4%**. Details: [contest-session-followups-20260904.md](contest-session-followups-20260904.md)  
> Last updated: 2026-09-07

## Setup

| Variant | System | Coach |
|---|---|---|
| **OTC** | `strategic_team` | Yes (scheduler / review / open-table coach lineage) |
| **Vanilla** | `vanilla_team` | No (same tools & rules) |

**Included:** ARML Local, Science Bowl, ARML National Team, Qanta, Mystery Hunt, History Olympiad, Purple Comet, HMMT Guts, WMTC.

**Excluded from §§1–5:** CTF/NYU, programming, CFA. ICPC WF contest-session results are in **§6**.

**Metric definitions**

| Column | Meaning |
|---|---|
| Accuracy / TaskUtility | Mean session `task_utility` = official score / max_score |
| Nonzero / Exact | Sessions with util > 0 / util = 1 |
| Score/Max | Σ score / Σ max_score (micro) |
| CS / Comm / Plan | MultiAgentBench-style scores (0–5) |
| AAR / AB | ActiveAgentRate / ActionBalance |
| turns / API / tokens | From contest `budget` (`turns_used`, `api_calls_used`, `tokens_used`) |

### Competitions

| Competition | What it is |
|---|---|
| `arml_local` | ARML local mathematics team rounds: multi-part contest math with partial credit. |
| `science_bowl` | Science Bowl toss-up and bonus questions across science subjects; short-answer or multiple-choice. |
| `arml_national_team` | ARML national team mathematics rounds, answered as a shared team sheet. |
| `qanta` | Academic quiz-bowl questions; identify the requested person, place, work, event, or concept. |
| `mystery_hunt` | MIT Mystery Hunt-style puzzles whose final output is a short answer or phrase. |
| `history_olympiad` | International History Bowl/Olympiad round packets containing many history short-answer questions. |
| `purple_comet` | Purple Comet online team mathematics contests for middle- and high-school divisions. |
| `hmmt_guts` | HMMT/GUTS-style team mathematics set with several difficult problems on one answer sheet. |
| `wmtc` | World Mathematics Team Championship papers at junior, intermediate, and advanced levels. |

---

## 1. Overall (771 paired sessions)

| Variant | N | Accuracy | Nonzero | Exact | Score/Max | Mean CS | Mean Comm | Mean Plan | Mean AAR | Mean AB | Σ turns | Σ API | Σ tokens | mean turns | mean API | mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| OTC | 771 | **18.6%** | 154/771 | 132/771 | 10.8% | 2.95 | 3.58 | 2.33 | 84.8% | 60.1% | 5966 | 18096 | 1,604,120 | 7.74 | 23.47 | 2081 |
| Vanilla | 771 | **20.7%** | 187/771 | 123/771 | 29.9% | 1.68 | 1.43 | 1.93 | 46.4% | 17.3% | 2359 | 6371 | 409,055 | 3.06 | 8.26 | 531 |

Vanilla leads overall TaskUtility; OTC leads CS / AAR / AB and uses ~**2.8×** API calls and ~**3.9×** tokens.

---

## 2. Wave1 vs Remaining

| Run | N | Accuracy | Nonzero | Exact | Mean CS | Σ API | Σ tokens | mean turns | mean API | mean tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| OTC Wave1 (ARML Local + Science Bowl) | 146 | **54.9%** | 83/146 | 77/146 | 3.52 | 2107 | 221,565 | 4.96 | 14.43 | 1518 |
| Vanilla Wave1 | 146 | **45.9%** | 67/146 | 67/146 | 1.55 | 578 | 28,864 | 1.69 | 3.96 | 198 |
| OTC Remaining | 625 | **10.1%** | 71/625 | 55/625 | 2.82 | 15989 | 1,382,555 | 8.39 | 25.58 | 2212 |
| Vanilla Remaining | 625 | **14.8%** | 120/625 | 56/625 | 1.71 | 5793 | 380,191 | 3.38 | 9.27 | 608 |

Wave1: OTC wins. Remaining: Vanilla wins (mainly History Olympiad).

---

## 3. By competition (paired)

| Competition | N | OTC Acc | Van Acc | OTC CS | Van CS | OTC mean API | Van mean API | OTC mean tok | Van mean tok | OTC mean turns | Van mean turns | OTC nz | Van nz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `arml_local` | 6 | **52.3%** | 0.0% | 3.25 | 2.83 | 37.00 | 36.00 | 7078 | 1761 | 12.00 | 12.00 | 6/6 | 0/6 |
| `science_bowl` | 140 | **55.0%** | 47.9% | 3.54 | 1.50 | 13.46 | 2.59 | 1279 | 131 | 4.66 | 1.25 | 77/140 | 67/140 |
| `arml_national_team` | 11 | 15.7% | **20.0%** | 2.05 | 2.23 | 13.00 | 9.27 | 2218 | 815 | 4.00 | 3.36 | 5/11 | 4/11 |
| `qanta` | 240 | 22.1% | **22.5%** | 3.61 | 1.18 | 14.97 | 2.16 | 1254 | 58 | 5.09 | 1.05 | 53/240 | 54/240 |
| `mystery_hunt` | 261 | 0.4% | **0.8%** | 2.26 | 2.02 | 30.14 | 16.81 | 2416 | 1034 | 9.76 | 5.82 | 1/261 | 2/261 |
| `history_olympiad` | 95 | 8.0% | **36.0%** | 2.57 | 2.09 | 36.38 | 5.39 | 3886 | 720 | 11.83 | 2.20 | 12/95 | 58/95 |
| `purple_comet` | 14 | 0.0% | **0.8%** | 2.11 | 1.93 | 55.00 | 15.57 | 3260 | 884 | 18.00 | 5.43 | 0/14 | 2/14 |
| `hmmt_guts` | 1 | 0.0% | 0.0% | 1.50 | 1.50 | 49.00 | 4.00 | 3291 | 1843 | 16.00 | 2.00 | 0/1 | 0/1 |
| `wmtc` | 3 | 0.0% | 0.0% | 2.50 | 2.00 | 37.00 | 17.33 | 2858 | 1668 | 12.00 | 6.00 | 0/3 | 0/3 |

> **Do not treat §3 as the final OTC story.** National was contaminated (answer-key leak + failed `T-1.` split). History / Purple / HMMT / WMTC OTC Acc collapsed from non-submission and wrong task-family prompts. Corrected numbers are in **§3.1** and [contest-session-followups-20260904.md](contest-session-followups-20260904.md).

### 3.1 Corrected OTC after protocol fixes (2026-09-04/05)

Paired Vanilla rows below stay on the **original gold** runs except `arml_national_team` (clean 50-turn Vanilla). OTC rows marked † are substituted from clean/routing reruns; other OTC rows remain original gold.

| Competition | N | OTC Acc | Van Acc | OTC nz | Van nz | Notes |
|---|---:|---:|---:|---|---|---|
| `arml_local` | 6 | **52.3%** | 0.0% | 6/6 | 0/6 | original |
| `science_bowl` | 140 | **55.0%** | 47.9% | 77/140 | 67/140 | original |
| `arml_national_team` † | 11 | **22.3%** | **0.0%** | **11/11** | 0/11 | clean split, no answer leak, 50 turns |
| `qanta` | 240 | 22.1% | **22.5%** | 53/240 | 54/240 | original |
| `mystery_hunt` † | 261 | 0.4% | **0.8%** | 1/261 | 2/261 | routing rerun; Acc unchanged |
| `history_olympiad` † | 95 | **64.4%** | 36.0% | **94/95** | 58/95 | routing + deadline; Van still original |
| `purple_comet` † | 14 | **9.2%** | 0.8% | **11/14** | 2/14 | routing rerun; Van still original |
| `hmmt_guts` † | 1 | **2.8%** | 0.0% | **1/1** | 0/1 | routing rerun; Van still original |
| `wmtc` † | 3 | **16.7%** | 0.0% | **3/3** | 0/3 | routing rerun; Van still original |
| **OTC session-weighted (w/ †)** | 771 | **~25.9%** | 20.4%* | **257/771** | 183/771* | *Van TOTAL uses clean National 0% |

Artifacts: `results/arml_national_team_clean_50turn_{otc,vanilla}_20260904/`, `results/otc_task_routing_low_accuracy_20260904/`.

---

## 4. History Olympiad — original loss, then protocol fix

### 4.1 Original gold (pre-fix)

On 95 History Olympiad bowl rounds: Vanilla **36.0%** vs OTC **8.0%** (nonzero 58/95 vs 12/95).

| | OTC | Vanilla |
|---|---:|---:|
| mean turns | 11.83 | 2.20 |
| mean API | 36.38 | 5.39 |
| mean tokens | 3886 | 720 |
| mean CS | 2.57 | 2.09 |

Failure mode (paired session dig):

- OTC burns budget on `rest` / `speak` / `coach_personal_assignment` / review; many high-gap sessions end with **no graded submission** (`nsub=0`).
- Vanilla does `select_problem → work/submit` in ~2 turns and collects large partial credit.
- History bowls are multi-question short-answer sheets that reward **fast sheet fill**. Coach/review helps Science Bowl / ARML Local but displaces answering here.
- Higher CS with lower TaskUtility again: process looks better, score does not.

### 4.2 Fixes and rerun outcome

**Deadline draft submit:** `contest_runner.py` submits every latest non-programming draft still lacking a valid submission when a strategic session ends (`deadline_drafts_submitted`).

**HMMT probe (deadline only):** still **0/36** — drafts were “need stdin/stdout” status text because the workflow misclassified math as programming.

**Task-family routing probe:** mathematics / short-answer / puzzle / programming prompts; HMMT → **1/36 (2.78%)**.

**Full low-accuracy OTC rerun (374 sessions, complete):**

| Competition | Gold OTC | Rerun OTC | Gold Van (unchanged) |
|---|---:|---:|---:|
| `history_olympiad` | 8.0% (12/95 nz) | **64.4%** (94/95 nz; 3628/5642 pts) | 36.0% |
| `purple_comet` | 0.0% | **9.2%** (11/14 nz) | 0.8% |
| `hmmt_guts` | 0.0% | **2.8%** | 0.0% |
| `wmtc` | 0.0% | **16.7%** (3/3 nz) | 0.0% |
| `mystery_hunt` | 0.4% | 0.4% (1/261) | 0.8% |

History OTC now **beats** original Vanilla. Mystery Hunt did not move — incomplete media/IRL puzzle text and hard extractions; gold JSON answers are fine (only win is answer-in-prompt `mystery_hunt_00819`). Full ledgers: [contest-session-followups-20260904.md](contest-session-followups-20260904.md).

---

## 5. Per-session ledger — OTC

`accuracy = score / max_score` per session. CS = coordination score (0–5).

### OTC (`strategic_team`)

Wall-clock `sec` was not persisted on contest sessions; column left blank.

| competition | problem_id | score | max_score | accuracy | Communication | Planning | CS | turns | api_calls | tokens | sec |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| arml_local | arml_local_2009 | 17.78 | 40 | 44.44% | 3 | 3 | 3 | 12 | 37 | 8578 |  |
| arml_local | arml_local_2010 | 26.67 | 40 | 66.67% | 4 | 3 | 3.5 | 12 | 37 | 7174 |  |
| arml_local | arml_local_2011 | 30 | 40 | 75.00% | 5 | 3 | 4 | 12 | 37 | 5088 |  |
| arml_local | arml_local_2012 | 17.78 | 40 | 44.44% | 4 | 2 | 3 | 12 | 37 | 6617 |  |
| arml_local | arml_local_2013 | 6.67 | 40 | 16.67% | 3 | 3 | 3 | 12 | 37 | 10532 |  |
| arml_local | arml_local_2014 | 40 | 60 | 66.67% | 4 | 2 | 3 | 12 | 37 | 4479 |  |
| science_bowl | science_bowl_sample_set_10_10a_hs_reg_2016_bonus_13 | 1 | 1 | 100.00% | 5 | 3 | 4 | 6 | 18 | 1549 |  |
| science_bowl | science_bowl_sample_set_10_10a_hs_reg_2016_toss_up_16 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 4 | 11 | 988 |  |
| science_bowl | science_bowl_sample_set_10_10a_hs_reg_2016_toss_up_17 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 10 | 31 | 2083 |  |
| science_bowl | science_bowl_sample_set_10_11a_hs_reg_2016_bonus_22 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 6 | 19 | 1418 |  |
| science_bowl | science_bowl_sample_set_10_12a_hs_reg_2016_bonus_02 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 11 | 1201 |  |
| science_bowl | science_bowl_sample_set_10_12a_hs_reg_2016_toss_up_07 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 7 | 878 |  |
| science_bowl | science_bowl_sample_set_10_12a_hs_reg_2016_toss_up_12 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 9 | 1205 |  |
| science_bowl | science_bowl_sample_set_10_13a_hs_reg_2016_toss_up_03 | 1 | 1 | 100.00% | 5 | 3 | 4 | 5 | 14 | 1250 |  |
| science_bowl | science_bowl_sample_set_10_14a_hs_reg_2016_bonus_20 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 8 | 22 | 1580 |  |
| science_bowl | science_bowl_sample_set_10_14a_hs_reg_2016_toss_up_23 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 4 | 10 | 1032 |  |
| science_bowl | science_bowl_sample_set_10_15a_hs_reg_2016_toss_up_11 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 2 | 6 | 785 |  |
| science_bowl | science_bowl_sample_set_10_16a_hs_reg_2016_bonus_03 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 10 | 31 | 2400 |  |
| science_bowl | science_bowl_sample_set_10_2a_hs_reg_2016_bonus_10 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 7 | 19 | 2351 |  |
| science_bowl | science_bowl_sample_set_10_5a_hs_reg_2016_bonus_04 | 1 | 1 | 100.00% | 4 | 2 | 3 | 3 | 9 | 720 |  |
| science_bowl | science_bowl_sample_set_10_6a_hs_reg_2016_bonus_04 | 1 | 1 | 100.00% | 1 | 3 | 2 | 4 | 11 | 1166 |  |
| science_bowl | science_bowl_sample_set_10_7a_hs_reg_2016_bonus_06 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 9 | 1146 |  |
| science_bowl | science_bowl_sample_set_10_8a_hs_reg_2016_bonus_02 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 3 | 8 | 965 |  |
| science_bowl | science_bowl_sample_set_10_9a_hs_reg_2016_bonus_10 | 0 | 1 | 0.00% | 5 | 3 | 4 | 4 | 10 | 1230 |  |
| science_bowl | science_bowl_sample_set_10_9a_hs_reg_2016_bonus_12 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 9 | 25 | 1598 |  |
| science_bowl | science_bowl_sample_set_10_9a_hs_reg_2016_toss_up_13 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 10 | 1075 |  |
| science_bowl | science_bowl_sample_set_11_hs_10a_toss_up_02 | 1 | 1 | 100.00% | 5 | 3 | 4 | 5 | 15 | 1214 |  |
| science_bowl | science_bowl_sample_set_11_hs_15a_bonus_04 | 0 | 1 | 0.00% | 5 | 4 | 4.5 | 4 | 10 | 1152 |  |
| science_bowl | science_bowl_sample_set_11_hs_17a_toss_up_18 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 11 | 1005 |  |
| science_bowl | science_bowl_sample_set_11_hs_3a_toss_up_01 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 12 | 1080 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_12_bonus_13 | 1 | 1 | 100.00% | 5 | 3 | 4 | 10 | 29 | 2024 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_13_bonus_10 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 5 | 13 | 1467 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_13_bonus_21 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 3 | 8 | 1333 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_14_toss_up_05 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 7 | 938 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_15_toss_up_05 | 1 | 1 | 100.00% | 4 | 4 | 4 | 3 | 8 | 1062 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_1_bonus_14 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 8 | 24 | 1457 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_1_toss_up_04 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 12 | 1258 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_2_bonus_08 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 15 | 1522 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_2_bonus_23 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 13 | 1210 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_2_toss_up_10 | 1 | 1 | 100.00% | 4 | 2 | 3 | 2 | 5 | 579 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_4_bonus_06 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 2 | 7 | 911 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_5_toss_up_04 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 2 | 6 | 914 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_5_toss_up_12 | 1 | 1 | 100.00% | 4 | 2 | 3 | 5 | 14 | 1314 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_6_bonus_03 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 10 | 1022 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_6_toss_up_10 | 1 | 1 | 100.00% | 4 | 2 | 3 | 4 | 12 | 1133 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_7_bonus_11 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 6 | 18 | 1246 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_8_bonus_22 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 4 | 11 | 1522 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_8_toss_up_13 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 3 | 7 | 861 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_8_toss_up_15 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 15 | 1229 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_9_bonus_21 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 11 | 1141 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_15a_toss_up_23 | 1 | 1 | 100.00% | 4 | 2 | 3 | 10 | 31 | 2013 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_17a_bonus_04 | 0 | 1 | 0.00% | 5 | 4 | 4.5 | 3 | 9 | 1120 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_17a_bonus_18 | 0 | 1 | 0.00% | 2 | 4 | 3 | 3 | 7 | 1102 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_17a_toss_up_02 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 1094 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_17a_toss_up_07 | 1 | 1 | 100.00% | 4 | 2 | 3 | 10 | 31 | 1993 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_1a_bonus_11 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 9 | 1166 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_2a_toss_up_19 | 1 | 1 | 100.00% | 4 | 4 | 4 | 3 | 8 | 962 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_3a_toss_up_21 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 8 | 1145 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_4a_toss_up_05 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 9 | 996 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_5a_bonus_23 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2907 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_5a_toss_up_12 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 17 | 1930 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_5a_toss_up_14 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 2 | 6 | 855 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_5a_toss_up_16 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 3 | 7 | 852 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_6a_bonus_10 | 0 | 1 | 0.00% | 1 | 4 | 2.5 | 3 | 9 | 1045 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_6a_bonus_11 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 6 | 19 | 1364 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_11a_toss_up_06 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 13 | 1184 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_12a_bonus_22 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 2 | 7 | 946 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_14a_toss_up_11 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 8 | 22 | 2077 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_9a_bonus_06 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 16 | 1434 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_9a_bonus_23 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 3 | 9 | 1087 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd10_bonus_13 | 0 | 1 | 0.00% | 5 | 4 | 4.5 | 3 | 9 | 1188 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd10_bonus_18 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 10 | 31 | 1837 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd10_toss_up_01 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 9 | 1059 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd10_toss_up_18 | 1 | 1 | 100.00% | 4 | 2 | 3 | 5 | 13 | 1076 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd11_bonus_06 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 8 | 992 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd13_toss_up_07 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 14 | 1554 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd14_bonus_02 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 5 | 15 | 1429 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd14_toss_up_05 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 10 | 31 | 1779 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd15_toss_up_05 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 4 | 12 | 1055 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd15_toss_up_11 | 1 | 1 | 100.00% | 5 | 3 | 4 | 10 | 31 | 1921 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd15_toss_up_13 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 4 | 10 | 926 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd17_bonus_11 | 0 | 1 | 0.00% | 5 | 3 | 4 | 4 | 11 | 1126 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd17_toss_up_02 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 4 | 12 | 1204 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd3_toss_up_03 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 932 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd5_bonus_07 | 0 | 1 | 0.00% | 4 | 2 | 3 | 5 | 15 | 1306 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd5_bonus_20 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 6 | 17 | 1543 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd6_bonus_18 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 9 | 1144 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd6_bonus_23 | 0 | 1 | 0.00% | 1 | 3 | 2 | 3 | 7 | 1055 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd7_bonus_17 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 15 | 1213 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd8_bonus_16 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 5 | 14 | 1247 |  |
| science_bowl | science_bowl_sample_set_16_set_10_hs_2021_toss_up_01 | 1 | 1 | 100.00% | 4 | 2 | 3 | 4 | 11 | 1182 |  |
| science_bowl | science_bowl_sample_set_16_set_2_hs_2021_bonus_06 | 0 | 1 | 0.00% | 5 | 4 | 4.5 | 4 | 11 | 1604 |  |
| science_bowl | science_bowl_sample_set_16_set_2_hs_2021_bonus_08 | 1 | 1 | 100.00% | 4 | 2 | 3 | 6 | 19 | 1887 |  |
| science_bowl | science_bowl_sample_set_16_set_2_hs_2021_bonus_18 | 1 | 1 | 100.00% | 2 | 3 | 2.5 | 5 | 15 | 1261 |  |
| science_bowl | science_bowl_sample_set_16_set_3_hs_2021_bonus_09 | 1 | 1 | 100.00% | 4 | 2 | 3 | 2 | 6 | 866 |  |
| science_bowl | science_bowl_sample_set_16_set_3_hs_2021_toss_up_15 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 2 | 6 | 873 |  |
| science_bowl | science_bowl_sample_set_16_set_3_hs_2021_toss_up_16 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 5 | 14 | 1276 |  |
| science_bowl | science_bowl_sample_set_16_set_5_hs_2021_bonus_01 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 10 | 30 | 2008 |  |
| science_bowl | science_bowl_sample_set_16_set_5_hs_2021_bonus_05 | 1 | 1 | 100.00% | 4 | 2 | 3 | 5 | 15 | 1510 |  |
| science_bowl | science_bowl_sample_set_16_set_5_hs_2021_toss_up_04 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 9 | 1247 |  |
| science_bowl | science_bowl_sample_set_16_set_5_hs_2021_toss_up_08 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 11 | 1226 |  |
| science_bowl | science_bowl_sample_set_16_set_6_hs_2021_toss_up_11 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 7 | 21 | 1543 |  |
| science_bowl | science_bowl_sample_set_16_set_7_hs_2021_bonus_11 | 0 | 1 | 0.00% | 4 | 4 | 4 | 3 | 7 | 813 |  |
| science_bowl | science_bowl_sample_set_16_set_8_hs_2021_bonus_12 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 9 | 969 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_01 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 9 | 1215 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_02 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 9 | 854 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_04 | 0 | 1 | 0.00% | 5 | 4 | 4.5 | 10 | 30 | 2109 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_10 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 14 | 1074 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_13 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 18 | 2803 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_18 | 1 | 1 | 100.00% | 4 | 2 | 3 | 10 | 31 | 2550 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_10_bonus_11 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 16 | 1516 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_10_bonus_16 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 9 | 28 | 1791 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_12_toss_up_18 | 1 | 1 | 100.00% | 4 | 2 | 3 | 4 | 12 | 981 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_13_toss_up_02 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 11 | 1159 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_15_bonus_01 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 4 | 12 | 1504 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_15_toss_up_01 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 5 | 15 | 1410 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_15_toss_up_05 | 1 | 1 | 100.00% | 3 | 3 | 3 | 3 | 8 | 933 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_15_toss_up_10 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 3 | 7 | 888 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_1_toss_up_17 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 12 | 887 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_2_bonus_09 | 1 | 1 | 100.00% | 4 | 2 | 3 | 9 | 25 | 1827 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_2_bonus_10 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 5 | 15 | 1240 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_2_toss_up_01 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 3 | 9 | 1004 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_2_toss_up_12 | 1 | 1 | 100.00% | 2 | 3 | 2.5 | 3 | 7 | 855 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_3_bonus_18 | 0 | 1 | 0.00% | 4 | 4 | 4 | 5 | 13 | 1374 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_3_toss_up_18 | 1 | 1 | 100.00% | 4 | 2 | 3 | 2 | 6 | 881 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_4_toss_up_05 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 15 | 1327 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_6_bonus_05 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 5 | 16 | 1323 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_6_toss_up_08 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 10 | 1041 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_8_bonus_01 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 3 | 9 | 1095 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_9_bonus_04 | 1 | 1 | 100.00% | 1 | 2 | 1.5 | 2 | 6 | 685 |  |
| science_bowl | science_bowl_sample_set_1_round16_bonus_18 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 4 | 10 | 1127 |  |
| science_bowl | science_bowl_sample_set_1_round7_toss_up_23 | 1 | 1 | 100.00% | 4 | 2 | 3 | 2 | 5 | 558 |  |
| science_bowl | science_bowl_sample_set_2_round15_bonus_15 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 5 | 15 | 1241 |  |
| science_bowl | science_bowl_sample_set_4_round11_bonus_04 | 0 | 1 | 0.00% | 4 | 2 | 3 | 7 | 19 | 1532 |  |
| science_bowl | science_bowl_sample_set_4_round17_bonus_07 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 10 | 1132 |  |
| science_bowl | science_bowl_sample_set_4_round6_bonus_01 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 10 | 890 |  |
| science_bowl | science_bowl_sample_set_5_round15_toss_up_18 | 0 | 1 | 0.00% | 4 | 4 | 4 | 5 | 15 | 1350 |  |
| science_bowl | science_bowl_sample_set_5_round4_toss_up_09 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 8 | 1201 |  |
| science_bowl | science_bowl_sample_set_6_sample6_round15_toss_up_12 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 2 | 7 | 1035 |  |
| science_bowl | science_bowl_sample_set_6_sample6_round15_toss_up_16 | 1 | 1 | 100.00% | 2 | 2 | 2 | 2 | 6 | 933 |  |
| science_bowl | science_bowl_sample_set_6_sample6_round8_toss_up_17 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 2 | 7 | 886 |  |
| science_bowl | science_bowl_sample_set_8_round_10_a_bonus_08 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1929 |  |
| science_bowl | science_bowl_sample_set_8_round_11_a_bonus_21 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 14 | 1458 |  |
| science_bowl | science_bowl_sample_set_8_round_2_a_toss_up_09 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 15 | 1304 |  |
| science_bowl | science_bowl_sample_set_9_regionalhs_13a_toss_up_16 | 1 | 1 | 100.00% | 2 | 2 | 2 | 3 | 7 | 816 |  |
| science_bowl | science_bowl_sample_set_9_regionalhs_4a_toss_up_05 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 9 | 1042 |  |
| arml_national_team | arml_national_team_2009 | 50 | 50 | 100.00% | 3 | 2 | 2.5 | 4 | 13 | 1482 |  |
| arml_national_team | arml_national_team_2010 | 0 | 50 | 0.00% | 3 | 1 | 2 | 4 | 13 | 1397 |  |
| arml_national_team | arml_national_team_2011 | 0 | 50 | 0.00% | 2 | 2 | 2 | 4 | 13 | 1208 |  |
| arml_national_team | arml_national_team_2012 | 0 | 50 | 0.00% | 3 | 2 | 2.5 | 4 | 13 | 1188 |  |
| arml_national_team | arml_national_team_2013 | 0 | 50 | 0.00% | 3 | 2 | 2.5 | 4 | 13 | 1386 |  |
| arml_national_team | arml_national_team_2014 | 0 | 50 | 0.00% | 2 | 2 | 2 | 4 | 13 | 1401 |  |
| arml_national_team | arml_national_team_2016 | 5.56 | 50 | 11.11% | 2 | 2 | 2 | 4 | 13 | 2149 |  |
| arml_national_team | arml_national_team_2017 | 0 | 50 | 0.00% | 3 | 2 | 2.5 | 4 | 13 | 4512 |  |
| arml_national_team | arml_national_team_2018 | 5.56 | 50 | 11.11% | 0 | 2 | 1 | 4 | 13 | 2500 |  |
| arml_national_team | arml_national_team_2019 | 10 | 50 | 20.00% | 0 | 2 | 1 | 4 | 13 | 2769 |  |
| arml_national_team | arml_national_team_2023 | 15 | 50 | 30.00% | 3 | 2 | 2.5 | 4 | 13 | 4409 |  |
| qanta | qanta_dev_102045 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 2 | 6 | 982 |  |
| qanta | qanta_dev_149935 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 8 | 1022 |  |
| qanta | qanta_dev_150473 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 19 | 1675 |  |
| qanta | qanta_train_10058 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 16 | 1198 |  |
| qanta | qanta_train_100927 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 11 | 1016 |  |
| qanta | qanta_train_101623 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 10 | 932 |  |
| qanta | qanta_train_101808 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 5 | 14 | 1156 |  |
| qanta | qanta_train_102465 | 0 | 1 | 0.00% | 4 | 2 | 3 | 9 | 26 | 2082 |  |
| qanta | qanta_train_10370 | 0 | 1 | 0.00% | 5 | 3 | 4 | 10 | 30 | 1900 |  |
| qanta | qanta_train_10469 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 4 | 12 | 1180 |  |
| qanta | qanta_train_10507 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 12 | 1186 |  |
| qanta | qanta_train_105981 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 7 | 21 | 1502 |  |
| qanta | qanta_train_106095 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 12 | 1044 |  |
| qanta | qanta_train_106447 | 0 | 1 | 0.00% | 4 | 2 | 3 | 2 | 6 | 765 |  |
| qanta | qanta_train_106504 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 10 | 876 |  |
| qanta | qanta_train_106567 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 18 | 1429 |  |
| qanta | qanta_train_106595 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 8 | 1327 |  |
| qanta | qanta_train_106604 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 14 | 1347 |  |
| qanta | qanta_train_106607 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 17 | 1248 |  |
| qanta | qanta_train_106769 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 13 | 1147 |  |
| qanta | qanta_train_106873 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 8 | 943 |  |
| qanta | qanta_train_107061 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 10 | 997 |  |
| qanta | qanta_train_107843 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 9 | 1122 |  |
| qanta | qanta_train_107921 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 10 | 30 | 1946 |  |
| qanta | qanta_train_108309 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 16 | 1529 |  |
| qanta | qanta_train_108623 | 0 | 1 | 0.00% | 5 | 3 | 4 | 4 | 12 | 1173 |  |
| qanta | qanta_train_108704 | 0 | 1 | 0.00% | 4 | 2 | 3 | 5 | 14 | 1213 |  |
| qanta | qanta_train_10987 | 1 | 1 | 100.00% | 5 | 3 | 4 | 6 | 18 | 1254 |  |
| qanta | qanta_train_110261 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 9 | 26 | 1548 |  |
| qanta | qanta_train_11143 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 3 | 8 | 1009 |  |
| qanta | qanta_train_112719 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 15 | 1321 |  |
| qanta | qanta_train_112933 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 6 | 17 | 1294 |  |
| qanta | qanta_train_113215 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 12 | 1072 |  |
| qanta | qanta_train_113216 | 0 | 1 | 0.00% | 4 | 2 | 3 | 5 | 15 | 1234 |  |
| qanta | qanta_train_114201 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1795 |  |
| qanta | qanta_train_114391 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 8 | 1080 |  |
| qanta | qanta_train_11488 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 7 | 789 |  |
| qanta | qanta_train_115444 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 5 | 14 | 1163 |  |
| qanta | qanta_train_115653 | 0 | 1 | 0.00% | 4 | 4 | 4 | 2 | 7 | 998 |  |
| qanta | qanta_train_116237 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 10 | 954 |  |
| qanta | qanta_train_11719 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 8 | 829 |  |
| qanta | qanta_train_11838 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 13 | 1059 |  |
| qanta | qanta_train_118455 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 10 | 1032 |  |
| qanta | qanta_train_119007 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 13 | 1252 |  |
| qanta | qanta_train_119982 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 8 | 1093 |  |
| qanta | qanta_train_121863 | 0 | 1 | 0.00% | 5 | 3 | 4 | 4 | 12 | 1178 |  |
| qanta | qanta_train_122042 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 10 | 1081 |  |
| qanta | qanta_train_122944 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 10 | 924 |  |
| qanta | qanta_train_123034 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 5 | 13 | 1511 |  |
| qanta | qanta_train_123766 | 1 | 1 | 100.00% | 5 | 3 | 4 | 2 | 6 | 886 |  |
| qanta | qanta_train_12431 | 1 | 1 | 100.00% | 5 | 3 | 4 | 10 | 31 | 1911 |  |
| qanta | qanta_train_125688 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 6 | 19 | 1378 |  |
| qanta | qanta_train_12630 | 0 | 1 | 0.00% | 5 | 3 | 4 | 8 | 23 | 1616 |  |
| qanta | qanta_train_126396 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 15 | 1370 |  |
| qanta | qanta_train_126475 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 6 | 18 | 1487 |  |
| qanta | qanta_train_12651 | 1 | 1 | 100.00% | 5 | 3 | 4 | 6 | 16 | 1406 |  |
| qanta | qanta_train_12761 | 0 | 1 | 0.00% | 4 | 2 | 3 | 8 | 24 | 1539 |  |
| qanta | qanta_train_128424 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 13 | 1080 |  |
| qanta | qanta_train_12895 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 10 | 31 | 1957 |  |
| qanta | qanta_train_129044 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 992 |  |
| qanta | qanta_train_129066 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 6 | 731 |  |
| qanta | qanta_train_13028 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 5 | 15 | 1400 |  |
| qanta | qanta_train_130288 | 0 | 1 | 0.00% | 5 | 4 | 4.5 | 4 | 12 | 1113 |  |
| qanta | qanta_train_131150 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 12 | 1209 |  |
| qanta | qanta_train_13154 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 1329 |  |
| qanta | qanta_train_13162 | 0 | 1 | 0.00% | 5 | 3 | 4 | 7 | 21 | 1431 |  |
| qanta | qanta_train_131686 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 7 | 795 |  |
| qanta | qanta_train_132989 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 11 | 1070 |  |
| qanta | qanta_train_133108 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 11 | 1199 |  |
| qanta | qanta_train_133321 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1836 |  |
| qanta | qanta_train_13339 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 3 | 9 | 1134 |  |
| qanta | qanta_train_13356 | 1 | 1 | 100.00% | 5 | 3 | 4 | 5 | 15 | 1347 |  |
| qanta | qanta_train_13399 | 1 | 1 | 100.00% | 5 | 3 | 4 | 10 | 31 | 1879 |  |
| qanta | qanta_train_134499 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1929 |  |
| qanta | qanta_train_135326 | 0 | 1 | 0.00% | 5 | 3 | 4 | 2 | 7 | 876 |  |
| qanta | qanta_train_135767 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 7 | 838 |  |
| qanta | qanta_train_136247 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 11 | 1218 |  |
| qanta | qanta_train_136253 | 1 | 1 | 100.00% | 5 | 3 | 4 | 8 | 22 | 1402 |  |
| qanta | qanta_train_13695 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 9 | 981 |  |
| qanta | qanta_train_13778 | 0 | 1 | 0.00% | 5 | 3 | 4 | 7 | 19 | 1657 |  |
| qanta | qanta_train_13824 | 1 | 1 | 100.00% | 5 | 3 | 4 | 7 | 21 | 1505 |  |
| qanta | qanta_train_138340 | 1 | 1 | 100.00% | 5 | 3 | 4 | 6 | 18 | 1548 |  |
| qanta | qanta_train_13850 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 12 | 1240 |  |
| qanta | qanta_train_13949 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 15 | 1109 |  |
| qanta | qanta_train_139521 | 0 | 1 | 0.00% | 4 | 2 | 3 | 8 | 22 | 1591 |  |
| qanta | qanta_train_142297 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 15 | 1355 |  |
| qanta | qanta_train_14254 | 0 | 1 | 0.00% | 5 | 3 | 4 | 7 | 20 | 1687 |  |
| qanta | qanta_train_142651 | 0 | 1 | 0.00% | 5 | 4 | 4.5 | 3 | 8 | 921 |  |
| qanta | qanta_train_14319 | 0 | 1 | 0.00% | 5 | 3 | 4 | 10 | 31 | 1661 |  |
| qanta | qanta_train_14438 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 838 |  |
| qanta | qanta_train_144532 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 9 | 1153 |  |
| qanta | qanta_train_145165 | 1 | 1 | 100.00% | 5 | 3 | 4 | 7 | 21 | 1586 |  |
| qanta | qanta_train_146319 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 14 | 1204 |  |
| qanta | qanta_train_14673 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 7 | 19 | 1480 |  |
| qanta | qanta_train_146818 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 14 | 1135 |  |
| qanta | qanta_train_147291 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2495 |  |
| qanta | qanta_train_150455 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 3 | 8 | 784 |  |
| qanta | qanta_train_15582 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 6 | 19 | 1259 |  |
| qanta | qanta_train_1566 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 12 | 1091 |  |
| qanta | qanta_train_160121 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 10 | 31 | 1928 |  |
| qanta | qanta_train_161416 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 3 | 9 | 1085 |  |
| qanta | qanta_train_161577 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 10 | 898 |  |
| qanta | qanta_train_162884 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 7 | 820 |  |
| qanta | qanta_train_167626 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 10 | 31 | 1785 |  |
| qanta | qanta_train_169176 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 3 | 9 | 1105 |  |
| qanta | qanta_train_171350 | 0 | 1 | 0.00% | 5 | 4 | 4.5 | 2 | 7 | 870 |  |
| qanta | qanta_train_171588 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 6 | 17 | 1252 |  |
| qanta | qanta_train_18751 | 0 | 1 | 0.00% | 2 | 2 | 2 | 6 | 18 | 1331 |  |
| qanta | qanta_train_20812 | 0 | 1 | 0.00% | 5 | 4 | 4.5 | 3 | 9 | 1035 |  |
| qanta | qanta_train_21606 | 0 | 1 | 0.00% | 5 | 3 | 4 | 2 | 7 | 781 |  |
| qanta | qanta_train_21725 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 7 | 758 |  |
| qanta | qanta_train_26320 | 0 | 1 | 0.00% | 4 | 2 | 3 | 6 | 18 | 1543 |  |
| qanta | qanta_train_27567 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 10 | 31 | 1917 |  |
| qanta | qanta_train_28946 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 12 | 937 |  |
| qanta | qanta_train_30345 | 1 | 1 | 100.00% | 5 | 3 | 4 | 6 | 17 | 1494 |  |
| qanta | qanta_train_31095 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 16 | 1109 |  |
| qanta | qanta_train_32747 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 17 | 1363 |  |
| qanta | qanta_train_33372 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 5 | 16 | 1165 |  |
| qanta | qanta_train_33880 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 6 | 16 | 1418 |  |
| qanta | qanta_train_35269 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 18 | 1292 |  |
| qanta | qanta_train_37123 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 6 | 16 | 1372 |  |
| qanta | qanta_train_37178 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 8 | 1029 |  |
| qanta | qanta_train_37358 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 5 | 16 | 1252 |  |
| qanta | qanta_train_38544 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 7 | 20 | 1578 |  |
| qanta | qanta_train_39120 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 1103 |  |
| qanta | qanta_train_39387 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 7 | 20 | 1512 |  |
| qanta | qanta_train_40825 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 8 | 1067 |  |
| qanta | qanta_train_42953 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 4 | 11 | 1034 |  |
| qanta | qanta_train_44955 | 0 | 1 | 0.00% | 2 | 2 | 2 | 5 | 15 | 1311 |  |
| qanta | qanta_train_46330 | 1 | 1 | 100.00% | 5 | 3 | 4 | 5 | 15 | 1404 |  |
| qanta | qanta_train_46554 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 3 | 9 | 900 |  |
| qanta | qanta_train_4662 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 7 | 22 | 1435 |  |
| qanta | qanta_train_46879 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 9 | 1118 |  |
| qanta | qanta_train_4810 | 1 | 1 | 100.00% | 5 | 3 | 4 | 8 | 24 | 1776 |  |
| qanta | qanta_train_48587 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 1153 |  |
| qanta | qanta_train_49297 | 1 | 1 | 100.00% | 5 | 3 | 4 | 10 | 29 | 1661 |  |
| qanta | qanta_train_49460 | 0 | 1 | 0.00% | 5 | 3 | 4 | 2 | 7 | 715 |  |
| qanta | qanta_train_51558 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 10 | 949 |  |
| qanta | qanta_train_51894 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 14 | 1187 |  |
| qanta | qanta_train_52355 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 17 | 1285 |  |
| qanta | qanta_train_52404 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 8 | 1041 |  |
| qanta | qanta_train_52420 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 890 |  |
| qanta | qanta_train_52729 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 10 | 1231 |  |
| qanta | qanta_train_52814 | 0 | 1 | 0.00% | 5 | 3 | 4 | 2 | 7 | 872 |  |
| qanta | qanta_train_52824 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 9 | 924 |  |
| qanta | qanta_train_52856 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 10 | 927 |  |
| qanta | qanta_train_52950 | 1 | 1 | 100.00% | 5 | 3 | 4 | 10 | 29 | 1918 |  |
| qanta | qanta_train_52976 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 18 | 1319 |  |
| qanta | qanta_train_53007 | 0 | 1 | 0.00% | 4 | 4 | 4 | 4 | 10 | 1286 |  |
| qanta | qanta_train_5424 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 14 | 1367 |  |
| qanta | qanta_train_55018 | 0 | 1 | 0.00% | 4 | 2 | 3 | 5 | 13 | 1343 |  |
| qanta | qanta_train_55218 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 17 | 1431 |  |
| qanta | qanta_train_55222 | 0 | 1 | 0.00% | 4 | 4 | 4 | 3 | 8 | 1070 |  |
| qanta | qanta_train_56260 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 7 | 765 |  |
| qanta | qanta_train_56844 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 3 | 9 | 1040 |  |
| qanta | qanta_train_56911 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 15 | 1253 |  |
| qanta | qanta_train_56996 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 4 | 12 | 1020 |  |
| qanta | qanta_train_57002 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1783 |  |
| qanta | qanta_train_57637 | 1 | 1 | 100.00% | 5 | 3 | 4 | 5 | 16 | 1130 |  |
| qanta | qanta_train_57652 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 14 | 1286 |  |
| qanta | qanta_train_58420 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 10 | 31 | 1804 |  |
| qanta | qanta_train_58437 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 10 | 31 | 1857 |  |
| qanta | qanta_train_5879 | 0 | 1 | 0.00% | 5 | 3 | 4 | 4 | 12 | 1127 |  |
| qanta | qanta_train_59764 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 6 | 737 |  |
| qanta | qanta_train_59769 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 10 | 28 | 1739 |  |
| qanta | qanta_train_59890 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 18 | 1448 |  |
| qanta | qanta_train_59903 | 0 | 1 | 0.00% | 4 | 2 | 3 | 9 | 27 | 1590 |  |
| qanta | qanta_train_60191 | 0 | 1 | 0.00% | 5 | 3 | 4 | 2 | 7 | 829 |  |
| qanta | qanta_train_60415 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 8 | 879 |  |
| qanta | qanta_train_60524 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 9 | 26 | 1550 |  |
| qanta | qanta_train_61076 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 6 | 16 | 1296 |  |
| qanta | qanta_train_61590 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 4 | 12 | 1264 |  |
| qanta | qanta_train_62036 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 7 | 856 |  |
| qanta | qanta_train_63832 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 10 | 984 |  |
| qanta | qanta_train_64000 | 0 | 1 | 0.00% | 5 | 3 | 4 | 9 | 25 | 1811 |  |
| qanta | qanta_train_64949 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 948 |  |
| qanta | qanta_train_6589 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 11 | 1135 |  |
| qanta | qanta_train_6629 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 5 | 14 | 1295 |  |
| qanta | qanta_train_68223 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 6 | 16 | 1134 |  |
| qanta | qanta_train_68245 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 5 | 15 | 1153 |  |
| qanta | qanta_train_68571 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 5 | 15 | 1250 |  |
| qanta | qanta_train_69534 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 18 | 1406 |  |
| qanta | qanta_train_70098 | 0 | 1 | 0.00% | 4 | 2 | 3 | 5 | 15 | 1159 |  |
| qanta | qanta_train_70375 | 0 | 1 | 0.00% | 5 | 3 | 4 | 10 | 31 | 1866 |  |
| qanta | qanta_train_70475 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 9 | 26 | 1747 |  |
| qanta | qanta_train_71054 | 1 | 1 | 100.00% | 5 | 4 | 4.5 | 3 | 8 | 867 |  |
| qanta | qanta_train_73579 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 4 | 12 | 1011 |  |
| qanta | qanta_train_74167 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 7 | 801 |  |
| qanta | qanta_train_74302 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 10 | 882 |  |
| qanta | qanta_train_7453 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 16 | 1252 |  |
| qanta | qanta_train_7490 | 1 | 1 | 100.00% | 5 | 3 | 4 | 6 | 18 | 1415 |  |
| qanta | qanta_train_75210 | 0 | 1 | 0.00% | 5 | 3 | 4 | 7 | 21 | 1620 |  |
| qanta | qanta_train_75229 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 7 | 729 |  |
| qanta | qanta_train_75693 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 18 | 1445 |  |
| qanta | qanta_train_75921 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 9 | 26 | 1953 |  |
| qanta | qanta_train_77359 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 10 | 31 | 1857 |  |
| qanta | qanta_train_77468 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 9 | 942 |  |
| qanta | qanta_train_77473 | 0 | 1 | 0.00% | 5 | 3 | 4 | 2 | 6 | 984 |  |
| qanta | qanta_train_78025 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 14 | 1273 |  |
| qanta | qanta_train_7829 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 13 | 1170 |  |
| qanta | qanta_train_78402 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 18 | 1481 |  |
| qanta | qanta_train_79335 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 17 | 1284 |  |
| qanta | qanta_train_801 | 0 | 1 | 0.00% | 4 | 2 | 3 | 8 | 24 | 1751 |  |
| qanta | qanta_train_80410 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 14 | 1122 |  |
| qanta | qanta_train_81669 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 7 | 817 |  |
| qanta | qanta_train_8203 | 0 | 1 | 0.00% | 2 | 4 | 3 | 5 | 13 | 1266 |  |
| qanta | qanta_train_82309 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1724 |  |
| qanta | qanta_train_83383 | 0 | 1 | 0.00% | 5 | 3 | 4 | 4 | 12 | 1139 |  |
| qanta | qanta_train_84125 | 0 | 1 | 0.00% | 5 | 3 | 4 | 4 | 13 | 1127 |  |
| qanta | qanta_train_85221 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 12 | 1084 |  |
| qanta | qanta_train_85318 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 12 | 1018 |  |
| qanta | qanta_train_85600 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 10 | 895 |  |
| qanta | qanta_train_87017 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 7 | 21 | 1457 |  |
| qanta | qanta_train_87124 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 15 | 1281 |  |
| qanta | qanta_train_87261 | 0 | 1 | 0.00% | 4 | 2 | 3 | 5 | 16 | 1188 |  |
| qanta | qanta_train_87437 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 4 | 13 | 966 |  |
| qanta | qanta_train_87984 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 8 | 1183 |  |
| qanta | qanta_train_88016 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 12 | 1051 |  |
| qanta | qanta_train_8802 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 14 | 1417 |  |
| qanta | qanta_train_88892 | 0 | 1 | 0.00% | 5 | 3 | 4 | 5 | 14 | 1229 |  |
| qanta | qanta_train_89005 | 0 | 1 | 0.00% | 5 | 3 | 4 | 6 | 18 | 1337 |  |
| qanta | qanta_train_89060 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 6 | 629 |  |
| qanta | qanta_train_89461 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 9 | 982 |  |
| qanta | qanta_train_89552 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 8 | 1244 |  |
| qanta | qanta_train_89751 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 8 | 1021 |  |
| qanta | qanta_train_90157 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 4 | 12 | 1235 |  |
| qanta | qanta_train_90372 | 0 | 1 | 0.00% | 5 | 3 | 4 | 3 | 8 | 1020 |  |
| qanta | qanta_train_90427 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 3 | 8 | 967 |  |
| qanta | qanta_train_90505 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 7 | 20 | 1298 |  |
| qanta | qanta_train_9051 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 7 | 20 | 1374 |  |
| qanta | qanta_train_92045 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1686 |  |
| qanta | qanta_train_92170 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 8 | 937 |  |
| qanta | qanta_train_92513 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 8 | 24 | 1789 |  |
| qanta | qanta_train_9400 | 0 | 1 | 0.00% | 5 | 2 | 3.5 | 10 | 31 | 1879 |  |
| qanta | qanta_train_94004 | 1 | 1 | 100.00% | 5 | 3 | 4 | 3 | 8 | 999 |  |
| qanta | qanta_train_9492 | 1 | 1 | 100.00% | 5 | 3 | 4 | 4 | 12 | 1212 |  |
| qanta | qanta_train_95205 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 7 | 20 | 1644 |  |
| qanta | qanta_train_96580 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 13 | 1025 |  |
| qanta | qanta_train_9758 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 11 | 1048 |  |
| qanta | qanta_train_98819 | 1 | 1 | 100.00% | 5 | 3 | 4 | 6 | 17 | 1432 |  |
| mystery_hunt | mystery_hunt_00002 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2320 |  |
| mystery_hunt | mystery_hunt_00003 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2092 |  |
| mystery_hunt | mystery_hunt_00004 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2265 |  |
| mystery_hunt | mystery_hunt_00006 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3874 |  |
| mystery_hunt | mystery_hunt_00007 | 0 | 1 | 0.00% | 4 | 4 | 4 | 7 | 19 | 1684 |  |
| mystery_hunt | mystery_hunt_00009 | 0 | 1 | 0.00% | 4 | 2 | 3 | 5 | 15 | 1371 |  |
| mystery_hunt | mystery_hunt_00014 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 31 | 1976 |  |
| mystery_hunt | mystery_hunt_00015 | 0 | 1 | 0.00% | 1 | 1 | 1 | 10 | 31 | 3033 |  |
| mystery_hunt | mystery_hunt_00028 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2171 |  |
| mystery_hunt | mystery_hunt_00032 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2221 |  |
| mystery_hunt | mystery_hunt_00033 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2053 |  |
| mystery_hunt | mystery_hunt_00035 | 0 | 1 | 0.00% | 2 | 4 | 3 | 3 | 7 | 891 |  |
| mystery_hunt | mystery_hunt_00036 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 6 | 17 | 2068 |  |
| mystery_hunt | mystery_hunt_00038 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 4650 |  |
| mystery_hunt | mystery_hunt_00044 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2318 |  |
| mystery_hunt | mystery_hunt_00068 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3042 |  |
| mystery_hunt | mystery_hunt_00078 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 1877 |  |
| mystery_hunt | mystery_hunt_00080 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2619 |  |
| mystery_hunt | mystery_hunt_00082 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2370 |  |
| mystery_hunt | mystery_hunt_00089 | 0 | 1 | 0.00% | 1 | 1 | 1 | 10 | 31 | 2432 |  |
| mystery_hunt | mystery_hunt_00094 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3094 |  |
| mystery_hunt | mystery_hunt_00095 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2159 |  |
| mystery_hunt | mystery_hunt_00096 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2630 |  |
| mystery_hunt | mystery_hunt_00102 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2419 |  |
| mystery_hunt | mystery_hunt_00103 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2344 |  |
| mystery_hunt | mystery_hunt_00105 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1814 |  |
| mystery_hunt | mystery_hunt_00106 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2091 |  |
| mystery_hunt | mystery_hunt_00112 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 16 | 2021 |  |
| mystery_hunt | mystery_hunt_00113 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2424 |  |
| mystery_hunt | mystery_hunt_00116 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2706 |  |
| mystery_hunt | mystery_hunt_00118 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2046 |  |
| mystery_hunt | mystery_hunt_00124 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 3283 |  |
| mystery_hunt | mystery_hunt_00136 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2983 |  |
| mystery_hunt | mystery_hunt_00137 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 3270 |  |
| mystery_hunt | mystery_hunt_00138 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 3699 |  |
| mystery_hunt | mystery_hunt_00140 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2512 |  |
| mystery_hunt | mystery_hunt_00144 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2888 |  |
| mystery_hunt | mystery_hunt_00147 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 31 | 2205 |  |
| mystery_hunt | mystery_hunt_00155 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 1956 |  |
| mystery_hunt | mystery_hunt_00160 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2205 |  |
| mystery_hunt | mystery_hunt_00165 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2643 |  |
| mystery_hunt | mystery_hunt_00166 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2344 |  |
| mystery_hunt | mystery_hunt_00169 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2704 |  |
| mystery_hunt | mystery_hunt_00177 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 7 | 20 | 1878 |  |
| mystery_hunt | mystery_hunt_00179 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2902 |  |
| mystery_hunt | mystery_hunt_00182 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2148 |  |
| mystery_hunt | mystery_hunt_00184 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3389 |  |
| mystery_hunt | mystery_hunt_00185 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2210 |  |
| mystery_hunt | mystery_hunt_00196 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2138 |  |
| mystery_hunt | mystery_hunt_00199 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2125 |  |
| mystery_hunt | mystery_hunt_00201 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 1995 |  |
| mystery_hunt | mystery_hunt_00203 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2244 |  |
| mystery_hunt | mystery_hunt_00215 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2556 |  |
| mystery_hunt | mystery_hunt_00220 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2082 |  |
| mystery_hunt | mystery_hunt_00226 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2262 |  |
| mystery_hunt | mystery_hunt_00356 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2127 |  |
| mystery_hunt | mystery_hunt_00358 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2196 |  |
| mystery_hunt | mystery_hunt_00368 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 31 | 2637 |  |
| mystery_hunt | mystery_hunt_00371 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2011 |  |
| mystery_hunt | mystery_hunt_00373 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2569 |  |
| mystery_hunt | mystery_hunt_00377 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2550 |  |
| mystery_hunt | mystery_hunt_00383 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2463 |  |
| mystery_hunt | mystery_hunt_00384 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2328 |  |
| mystery_hunt | mystery_hunt_00398 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2902 |  |
| mystery_hunt | mystery_hunt_00405 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2184 |  |
| mystery_hunt | mystery_hunt_00408 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2253 |  |
| mystery_hunt | mystery_hunt_00409 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2276 |  |
| mystery_hunt | mystery_hunt_00412 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2098 |  |
| mystery_hunt | mystery_hunt_00431 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2186 |  |
| mystery_hunt | mystery_hunt_00433 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2427 |  |
| mystery_hunt | mystery_hunt_00451 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2434 |  |
| mystery_hunt | mystery_hunt_00457 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2377 |  |
| mystery_hunt | mystery_hunt_00529 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2145 |  |
| mystery_hunt | mystery_hunt_00586 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 8 | 23 | 2028 |  |
| mystery_hunt | mystery_hunt_00601 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 1986 |  |
| mystery_hunt | mystery_hunt_00605 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2083 |  |
| mystery_hunt | mystery_hunt_00612 | 0 | 1 | 0.00% | 4 | 2 | 3 | 8 | 22 | 1510 |  |
| mystery_hunt | mystery_hunt_00617 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2478 |  |
| mystery_hunt | mystery_hunt_00624 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2773 |  |
| mystery_hunt | mystery_hunt_00628 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2726 |  |
| mystery_hunt | mystery_hunt_00629 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2171 |  |
| mystery_hunt | mystery_hunt_00645 | 0 | 1 | 0.00% | 1 | 2 | 1.5 | 10 | 31 | 2073 |  |
| mystery_hunt | mystery_hunt_00652 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2624 |  |
| mystery_hunt | mystery_hunt_00653 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2110 |  |
| mystery_hunt | mystery_hunt_00656 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2722 |  |
| mystery_hunt | mystery_hunt_00681 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2043 |  |
| mystery_hunt | mystery_hunt_00686 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2411 |  |
| mystery_hunt | mystery_hunt_00687 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 10 | 31 | 5147 |  |
| mystery_hunt | mystery_hunt_00691 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2319 |  |
| mystery_hunt | mystery_hunt_00697 | 0 | 1 | 0.00% | 1 | 2 | 1.5 | 10 | 31 | 1955 |  |
| mystery_hunt | mystery_hunt_00698 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2276 |  |
| mystery_hunt | mystery_hunt_00708 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 1812 |  |
| mystery_hunt | mystery_hunt_00715 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2300 |  |
| mystery_hunt | mystery_hunt_00719 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2767 |  |
| mystery_hunt | mystery_hunt_00743 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 31 | 2163 |  |
| mystery_hunt | mystery_hunt_00757 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 1921 |  |
| mystery_hunt | mystery_hunt_00760 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2359 |  |
| mystery_hunt | mystery_hunt_00766 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 10 | 31 | 2205 |  |
| mystery_hunt | mystery_hunt_00778 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2403 |  |
| mystery_hunt | mystery_hunt_00791 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2998 |  |
| mystery_hunt | mystery_hunt_00793 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2332 |  |
| mystery_hunt | mystery_hunt_00805 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2628 |  |
| mystery_hunt | mystery_hunt_00810 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3577 |  |
| mystery_hunt | mystery_hunt_00819 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 9 | 26 | 1840 |  |
| mystery_hunt | mystery_hunt_00833 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2554 |  |
| mystery_hunt | mystery_hunt_00836 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2195 |  |
| mystery_hunt | mystery_hunt_00843 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2462 |  |
| mystery_hunt | mystery_hunt_00847 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2111 |  |
| mystery_hunt | mystery_hunt_00868 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2596 |  |
| mystery_hunt | mystery_hunt_00869 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2345 |  |
| mystery_hunt | mystery_hunt_00871 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2484 |  |
| mystery_hunt | mystery_hunt_00874 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2216 |  |
| mystery_hunt | mystery_hunt_00882 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2001 |  |
| mystery_hunt | mystery_hunt_00887 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2501 |  |
| mystery_hunt | mystery_hunt_00896 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2258 |  |
| mystery_hunt | mystery_hunt_00913 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2735 |  |
| mystery_hunt | mystery_hunt_00916 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3285 |  |
| mystery_hunt | mystery_hunt_00918 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 1845 |  |
| mystery_hunt | mystery_hunt_00926 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2338 |  |
| mystery_hunt | mystery_hunt_00929 | 0 | 1 | 0.00% | 3 | 4 | 3.5 | 4 | 10 | 1194 |  |
| mystery_hunt | mystery_hunt_00930 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2304 |  |
| mystery_hunt | mystery_hunt_00941 | 0 | 1 | 0.00% | 4 | 4 | 4 | 7 | 19 | 2639 |  |
| mystery_hunt | mystery_hunt_00946 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2120 |  |
| mystery_hunt | mystery_hunt_00948 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 31 | 2301 |  |
| mystery_hunt | mystery_hunt_00956 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2066 |  |
| mystery_hunt | mystery_hunt_00960 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2340 |  |
| mystery_hunt | mystery_hunt_00961 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2228 |  |
| mystery_hunt | mystery_hunt_00994 | 0 | 1 | 0.00% | 2 | 2 | 2 | 9 | 25 | 2478 |  |
| mystery_hunt | mystery_hunt_01099 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2342 |  |
| mystery_hunt | mystery_hunt_01110 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2818 |  |
| mystery_hunt | mystery_hunt_01111 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2373 |  |
| mystery_hunt | mystery_hunt_01112 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2270 |  |
| mystery_hunt | mystery_hunt_01124 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2674 |  |
| mystery_hunt | mystery_hunt_01150 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3610 |  |
| mystery_hunt | mystery_hunt_01151 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2981 |  |
| mystery_hunt | mystery_hunt_01152 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2468 |  |
| mystery_hunt | mystery_hunt_01157 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2183 |  |
| mystery_hunt | mystery_hunt_01173 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2012 |  |
| mystery_hunt | mystery_hunt_01180 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2361 |  |
| mystery_hunt | mystery_hunt_01189 | 0 | 1 | 0.00% | 1 | 2 | 1.5 | 10 | 31 | 1948 |  |
| mystery_hunt | mystery_hunt_01206 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2545 |  |
| mystery_hunt | mystery_hunt_01209 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2103 |  |
| mystery_hunt | mystery_hunt_01226 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2143 |  |
| mystery_hunt | mystery_hunt_01244 | 0 | 1 | 0.00% | 3 | 3 | 3 | 10 | 31 | 2304 |  |
| mystery_hunt | mystery_hunt_01261 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2857 |  |
| mystery_hunt | mystery_hunt_01266 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2662 |  |
| mystery_hunt | mystery_hunt_01271 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3448 |  |
| mystery_hunt | mystery_hunt_01277 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2354 |  |
| mystery_hunt | mystery_hunt_01278 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 1897 |  |
| mystery_hunt | mystery_hunt_01286 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3077 |  |
| mystery_hunt | mystery_hunt_01301 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3022 |  |
| mystery_hunt | mystery_hunt_01307 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2895 |  |
| mystery_hunt | mystery_hunt_01313 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3137 |  |
| mystery_hunt | mystery_hunt_01315 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2712 |  |
| mystery_hunt | mystery_hunt_01324 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2403 |  |
| mystery_hunt | mystery_hunt_01337 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2782 |  |
| mystery_hunt | mystery_hunt_01343 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2674 |  |
| mystery_hunt | mystery_hunt_01357 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1982 |  |
| mystery_hunt | mystery_hunt_01358 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 1876 |  |
| mystery_hunt | mystery_hunt_01361 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 3032 |  |
| mystery_hunt | mystery_hunt_01363 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 6 | 18 | 3091 |  |
| mystery_hunt | mystery_hunt_01372 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2254 |  |
| mystery_hunt | mystery_hunt_01374 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 31 | 2148 |  |
| mystery_hunt | mystery_hunt_01377 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 1938 |  |
| mystery_hunt | mystery_hunt_01395 | 0 | 1 | 0.00% | 4 | 2 | 3 | 7 | 20 | 1550 |  |
| mystery_hunt | mystery_hunt_01398 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2399 |  |
| mystery_hunt | mystery_hunt_01402 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2522 |  |
| mystery_hunt | mystery_hunt_01408 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2869 |  |
| mystery_hunt | mystery_hunt_01410 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2221 |  |
| mystery_hunt | mystery_hunt_01418 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2624 |  |
| mystery_hunt | mystery_hunt_01429 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2019 |  |
| mystery_hunt | mystery_hunt_01431 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2702 |  |
| mystery_hunt | mystery_hunt_01432 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3605 |  |
| mystery_hunt | mystery_hunt_01446 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2332 |  |
| mystery_hunt | mystery_hunt_01454 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 31 | 1946 |  |
| mystery_hunt | mystery_hunt_01469 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2063 |  |
| mystery_hunt | mystery_hunt_01486 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2835 |  |
| mystery_hunt | mystery_hunt_01491 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2586 |  |
| mystery_hunt | mystery_hunt_01496 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 3505 |  |
| mystery_hunt | mystery_hunt_01497 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2464 |  |
| mystery_hunt | mystery_hunt_01501 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2153 |  |
| mystery_hunt | mystery_hunt_01520 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2346 |  |
| mystery_hunt | mystery_hunt_01521 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2887 |  |
| mystery_hunt | mystery_hunt_01523 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2810 |  |
| mystery_hunt | mystery_hunt_01543 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 31 | 2317 |  |
| mystery_hunt | mystery_hunt_01546 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2132 |  |
| mystery_hunt | mystery_hunt_01558 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2603 |  |
| mystery_hunt | mystery_hunt_01566 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2723 |  |
| mystery_hunt | mystery_hunt_01582 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2120 |  |
| mystery_hunt | mystery_hunt_01585 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2211 |  |
| mystery_hunt | mystery_hunt_01591 | 0 | 1 | 0.00% | 3 | 3 | 3 | 8 | 24 | 1713 |  |
| mystery_hunt | mystery_hunt_01597 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2604 |  |
| mystery_hunt | mystery_hunt_01603 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2560 |  |
| mystery_hunt | mystery_hunt_01610 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2128 |  |
| mystery_hunt | mystery_hunt_01616 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2309 |  |
| mystery_hunt | mystery_hunt_01618 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 1998 |  |
| mystery_hunt | mystery_hunt_01640 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 5 | 14 | 1184 |  |
| mystery_hunt | mystery_hunt_01642 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2514 |  |
| mystery_hunt | mystery_hunt_01645 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 3978 |  |
| mystery_hunt | mystery_hunt_01647 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2429 |  |
| mystery_hunt | mystery_hunt_01651 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2231 |  |
| mystery_hunt | mystery_hunt_01659 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2701 |  |
| mystery_hunt | mystery_hunt_01666 | 0 | 1 | 0.00% | 3 | 3 | 3 | 10 | 31 | 2657 |  |
| mystery_hunt | mystery_hunt_01667 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 3054 |  |
| mystery_hunt | mystery_hunt_01684 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2834 |  |
| mystery_hunt | mystery_hunt_01686 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 3448 |  |
| mystery_hunt | mystery_hunt_01687 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2582 |  |
| mystery_hunt | mystery_hunt_01689 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2187 |  |
| mystery_hunt | mystery_hunt_01692 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2622 |  |
| mystery_hunt | mystery_hunt_01702 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2430 |  |
| mystery_hunt | mystery_hunt_01712 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2540 |  |
| mystery_hunt | mystery_hunt_01719 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2659 |  |
| mystery_hunt | mystery_hunt_01727 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2900 |  |
| mystery_hunt | mystery_hunt_01732 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 10 | 31 | 2110 |  |
| mystery_hunt | mystery_hunt_01752 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 1835 |  |
| mystery_hunt | mystery_hunt_01775 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2809 |  |
| mystery_hunt | mystery_hunt_01794 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2445 |  |
| mystery_hunt | mystery_hunt_01800 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2043 |  |
| mystery_hunt | mystery_hunt_01802 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2584 |  |
| mystery_hunt | mystery_hunt_01807 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2996 |  |
| mystery_hunt | mystery_hunt_01810 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 1753 |  |
| mystery_hunt | mystery_hunt_01820 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2152 |  |
| mystery_hunt | mystery_hunt_01821 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2643 |  |
| mystery_hunt | mystery_hunt_01824 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2075 |  |
| mystery_hunt | mystery_hunt_01970 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2690 |  |
| mystery_hunt | mystery_hunt_01985 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2241 |  |
| mystery_hunt | mystery_hunt_01994 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2109 |  |
| mystery_hunt | mystery_hunt_01995 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2733 |  |
| mystery_hunt | mystery_hunt_01997 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2074 |  |
| mystery_hunt | mystery_hunt_02002 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 1836 |  |
| mystery_hunt | mystery_hunt_02007 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 31 | 2139 |  |
| mystery_hunt | mystery_hunt_02008 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2092 |  |
| mystery_hunt | mystery_hunt_02030 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2600 |  |
| mystery_hunt | mystery_hunt_02035 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2405 |  |
| mystery_hunt | mystery_hunt_02037 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2415 |  |
| mystery_hunt | mystery_hunt_02040 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2046 |  |
| mystery_hunt | mystery_hunt_02044 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 7 | 903 |  |
| mystery_hunt | mystery_hunt_02045 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2308 |  |
| mystery_hunt | mystery_hunt_02062 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2229 |  |
| mystery_hunt | mystery_hunt_02080 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2127 |  |
| mystery_hunt | mystery_hunt_02103 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 31 | 2207 |  |
| mystery_hunt | mystery_hunt_02107 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2114 |  |
| mystery_hunt | mystery_hunt_02109 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2043 |  |
| mystery_hunt | mystery_hunt_02124 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3751 |  |
| mystery_hunt | mystery_hunt_02133 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2024 |  |
| mystery_hunt | mystery_hunt_02144 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 3108 |  |
| mystery_hunt | mystery_hunt_02146 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 1886 |  |
| mystery_hunt | mystery_hunt_02156 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2830 |  |
| mystery_hunt | mystery_hunt_02166 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2982 |  |
| mystery_hunt | mystery_hunt_02174 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2457 |  |
| mystery_hunt | mystery_hunt_02185 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2364 |  |
| mystery_hunt | mystery_hunt_02186 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 31 | 1892 |  |
| mystery_hunt | mystery_hunt_02197 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2310 |  |
| mystery_hunt | mystery_hunt_02200 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2054 |  |
| mystery_hunt | mystery_hunt_02203 | 0 | 1 | 0.00% | 3 | 3 | 3 | 10 | 31 | 2077 |  |
| mystery_hunt | mystery_hunt_02205 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2455 |  |
| mystery_hunt | mystery_hunt_02218 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2076 |  |
| mystery_hunt | mystery_hunt_02220 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2106 |  |
| mystery_hunt | mystery_hunt_02241 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 31 | 2533 |  |
| mystery_hunt | mystery_hunt_02258 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 31 | 2284 |  |
| mystery_hunt | mystery_hunt_02262 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 31 | 2225 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_1 | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 37 | 7116 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_2 | 0 | 60 | 0.00% | 2 | 1 | 1.5 | 12 | 37 | 3040 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_5 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2411 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_6 | 47 | 60 | 78.33% | 3 | 2 | 2.5 | 12 | 37 | 5191 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_7 | 0 | 60 | 0.00% | 4 | 1 | 2.5 | 12 | 37 | 3264 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_8 | 0 | 59 | 0.00% | 2 | 2 | 2 | 12 | 37 | 2436 |  |
| history_olympiad | history_olympiad_bowl_2018_2019_ihbb_asia_alpha_set_bowl_round_2 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3245 |  |
| history_olympiad | history_olympiad_bowl_2018_2019_ihbb_asia_alpha_set_bowl_round_4 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2748 |  |
| history_olympiad | history_olympiad_bowl_2018_2019_ihbb_asia_alpha_set_bowl_round_5 | 48 | 60 | 80.00% | 4 | 2 | 3 | 6 | 18 | 3274 |  |
| history_olympiad | history_olympiad_bowl_2018_2019_ihbb_asia_alpha_set_bowl_round_7 | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 37 | 6056 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_1 | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 37 | 2290 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_2 | 0 | 60 | 0.00% | 2 | 1 | 1.5 | 12 | 37 | 2834 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_3 | 0 | 59 | 0.00% | 4 | 1 | 2.5 | 12 | 37 | 2717 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_4 | 0 | 58 | 0.00% | 3 | 1 | 2 | 12 | 37 | 2387 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_5 | 0 | 59 | 0.00% | 2 | 2 | 2 | 12 | 37 | 2481 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_6 | 0 | 59 | 0.00% | 2 | 2 | 2 | 12 | 37 | 2930 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_7 | 34 | 60 | 56.67% | 2 | 3 | 2.5 | 12 | 37 | 4123 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_finals | 0 | 59 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3989 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_quarterfinals | 0 | 59 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3018 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_1 | 45 | 60 | 75.00% | 4 | 2 | 3 | 12 | 37 | 4069 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_2 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 4146 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_3 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 3480 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_4 | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 37 | 4934 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_5 | 41 | 60 | 68.33% | 4 | 3 | 3.5 | 12 | 34 | 4822 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_1 | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 37 | 3170 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_2 | 0 | 59 | 0.00% | 2 | 2 | 2 | 12 | 37 | 6316 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_3 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 2531 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_4 | 0 | 59 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 2889 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_5 | 40 | 60 | 66.67% | 3 | 2 | 2.5 | 12 | 37 | 4395 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_6 | 0 | 60 | 0.00% | 3 | 3 | 3 | 12 | 37 | 3698 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_7 | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 12 | 37 | 5126 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_1_hs | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 3129 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_2 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3398 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_2_hs_asia_and_europe_1 | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 37 | 3560 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_3 | 43 | 59 | 72.88% | 4 | 3 | 3.5 | 12 | 37 | 3047 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_3_hs_1 | 0 | 59 | 0.00% | 4 | 1 | 2.5 | 12 | 37 | 2895 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_4 | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 12 | 37 | 6118 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_4_hs_1 | 0 | 58 | 0.00% | 2 | 2 | 2 | 12 | 37 | 8446 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_5 | 39 | 60 | 65.00% | 3 | 2 | 2.5 | 11 | 33 | 5725 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_6 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3038 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_6_hs_1 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2704 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_7 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 6977 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_7_hs_1 | 36 | 60 | 60.00% | 4 | 3 | 3.5 | 12 | 36 | 3628 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_8 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 6153 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_8_hs_1 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 7146 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_1 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 4791 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_2 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 3977 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_3 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2820 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_4 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2935 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_5 | 17 | 60 | 28.33% | 4 | 2 | 3 | 12 | 37 | 4472 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_6 | 0 | 62 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 4204 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_7 | 0 | 62 | 0.00% | 2 | 2 | 2 | 12 | 37 | 2714 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_1 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3458 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_2 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 2851 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_3 | 0 | 59 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 4118 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_4 | 37 | 60 | 61.67% | 4 | 2 | 3 | 12 | 37 | 6588 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_5 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 2283 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_6 | 0 | 60 | 0.00% | 4 | 1 | 2.5 | 12 | 37 | 2784 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_7 | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 7 | 19 | 2981 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_1 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3186 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_2 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 3702 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_3 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2953 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_4 | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 12 | 37 | 4943 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_5 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3982 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_6 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 5063 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_7 | 0 | 60 | 0.00% | 3 | 1 | 2 | 12 | 37 | 2921 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_8 | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 37 | 5078 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_9_backup_packet | 0 | 60 | 0.00% | 3 | 1 | 2 | 12 | 37 | 3416 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_1_varsity_and_jv | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 9382 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_3_varsity_and_jv | 0 | 60 | 0.00% | 2 | 1 | 1.5 | 12 | 37 | 2642 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_4_varsity_and_jv | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2596 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_6_varsity_and_jv | 0 | 59 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 5788 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_7_varsity_and_jv | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 5670 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_8_varsity_and_jv | 0 | 59 | 0.00% | 2 | 2 | 2 | 12 | 37 | 2710 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r1 | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 37 | 3403 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r2 | 0 | 60 | 0.00% | 4 | 1 | 2.5 | 12 | 37 | 3625 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r3 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 4022 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r4 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 2589 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r5 | 0 | 59 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 3432 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r6 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2568 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r7 | 31 | 60 | 51.67% | 3 | 2 | 2.5 | 12 | 37 | 7312 |  |
| history_olympiad | history_olympiad_bowl_intl_history_olympiad_history_bowl_samples | 0 | 24 | 0.00% | 2 | 1 | 1.5 | 12 | 37 | 3118 |  |
| history_olympiad | history_olympiad_bowl_playoff_rd_1_history_bowl_2021_ihbb_asian_championships | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 37 | 5493 |  |
| history_olympiad | history_olympiad_bowl_playoff_rd_2_history_bowl_2021_ihbb_asian_championships | 0 | 59 | 0.00% | 2 | 2 | 2 | 12 | 37 | 2254 |  |
| history_olympiad | history_olympiad_bowl_rd_1_history_bowl_2021_ihbb_asian_championships | 0 | 60 | 0.00% | 2 | 1 | 1.5 | 12 | 37 | 2522 |  |
| history_olympiad | history_olympiad_bowl_rd_2_history_bowl_2021_ihbb_asian_championships | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3213 |  |
| history_olympiad | history_olympiad_bowl_rd_3_history_bowl_2021_ihbb_asian_championships | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 12 | 37 | 4822 |  |
| history_olympiad | history_olympiad_bowl_rd_4_history_bowl_2021_ihbb_asian_championships | 0 | 60 | 0.00% | 2 | 1 | 1.5 | 12 | 37 | 3318 |  |
| history_olympiad | history_olympiad_bowl_rd_5_history_bowl_2021_ihbb_asian_championships | 0 | 60 | 0.00% | 3 | 3 | 3 | 8 | 23 | 3054 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_1 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 12 | 37 | 2817 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_2 | 0 | 58 | 0.00% | 4 | 3 | 3.5 | 12 | 37 | 3273 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_3 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2406 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_4 | 0 | 59 | 0.00% | 2 | 2 | 2 | 12 | 37 | 3542 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_5 | 0 | 60 | 0.00% | 4 | 2 | 3 | 12 | 37 | 3142 |  |
| history_olympiad | history_olympiad_bowl_vjv_bowl_round_1 | 0 | 56 | 0.00% | 2 | 2 | 2 | 12 | 37 | 3104 |  |
| purple_comet | purple_comet_hs_2018 | 0 | 30 | 0.00% | 2 | 1 | 1.5 | 18 | 55 | 3436 |  |
| purple_comet | purple_comet_hs_2019 | 0 | 30 | 0.00% | 3 | 1 | 2 | 18 | 55 | 3444 |  |
| purple_comet | purple_comet_hs_2020 | 0 | 30 | 0.00% | 4 | 2 | 3 | 18 | 55 | 3061 |  |
| purple_comet | purple_comet_hs_2021 | 0 | 30 | 0.00% | 2 | 1 | 1.5 | 18 | 55 | 3488 |  |
| purple_comet | purple_comet_hs_2022 | 0 | 30 | 0.00% | 2 | 2 | 2 | 18 | 55 | 3662 |  |
| purple_comet | purple_comet_hs_2023 | 0 | 30 | 0.00% | 2 | 2 | 2 | 18 | 55 | 3533 |  |
| purple_comet | purple_comet_hs_2024 | 0 | 30 | 0.00% | 4 | 1 | 2.5 | 18 | 55 | 3059 |  |
| purple_comet | purple_comet_ms_2018 | 0 | 20 | 0.00% | 4 | 2 | 3 | 18 | 55 | 3252 |  |
| purple_comet | purple_comet_ms_2019 | 0 | 20 | 0.00% | 2 | 2 | 2 | 18 | 55 | 3351 |  |
| purple_comet | purple_comet_ms_2020 | 0 | 20 | 0.00% | 4 | 2 | 3 | 18 | 55 | 2844 |  |
| purple_comet | purple_comet_ms_2021 | 0 | 20 | 0.00% | 2 | 1 | 1.5 | 18 | 55 | 2892 |  |
| purple_comet | purple_comet_ms_2022 | 0 | 20 | 0.00% | 4 | 1 | 2.5 | 18 | 55 | 3275 |  |
| purple_comet | purple_comet_ms_2023 | 0 | 20 | 0.00% | 2 | 1 | 1.5 | 18 | 55 | 3167 |  |
| purple_comet | purple_comet_ms_2024 | 0 | 20 | 0.00% | 2 | 1 | 1.5 | 18 | 55 | 3180 |  |
| hmmt_guts | hmmt_guts_2024 | 0 | 36 | 0.00% | 2 | 1 | 1.5 | 16 | 49 | 3291 |  |
| wmtc | wmtc_2018_advanced | 0 | 14 | 0.00% | 2 | 1 | 1.5 | 12 | 37 | 2675 |  |
| wmtc | wmtc_2018_intermediate | 0 | 14 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2977 |  |
| wmtc | wmtc_2018_junior | 0 | 14 | 0.00% | 4 | 2 | 3 | 12 | 37 | 2922 |  |
| **TOTAL** | **771 sessions** | **814** | **7521** | **macro 18.61%** | **mean 3.58** | **mean 2.33** | **mean 2.95** | **5966** | **18096** | **1604120** |  |

## 6. Per-session ledger — Vanilla

Same columns as §5. Matched problem ids; only `--system-variant` differs.

### Vanilla (`vanilla_team`)

Wall-clock `sec` was not persisted on contest sessions; column left blank.

| competition | problem_id | score | max_score | accuracy | Communication | Planning | CS | turns | api_calls | tokens | sec |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| arml_local | arml_local_2009 | 0 | 40 | 0.00% | 4 | 2 | 3 | 12 | 36 | 1879 |  |
| arml_local | arml_local_2010 | 0 | 40 | 0.00% | 4 | 2 | 3 | 12 | 36 | 1667 |  |
| arml_local | arml_local_2011 | 0 | 40 | 0.00% | 4 | 2 | 3 | 12 | 36 | 2209 |  |
| arml_local | arml_local_2012 | 0 | 40 | 0.00% | 4 | 2 | 3 | 12 | 36 | 1485 |  |
| arml_local | arml_local_2013 | 0 | 40 | 0.00% | 4 | 2 | 3 | 12 | 36 | 1519 |  |
| arml_local | arml_local_2014 | 0 | 60 | 0.00% | 2 | 2 | 2 | 12 | 36 | 1807 |  |
| science_bowl | science_bowl_sample_set_10_10a_hs_reg_2016_bonus_13 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 2 | 4 | 332 |  |
| science_bowl | science_bowl_sample_set_10_10a_hs_reg_2016_toss_up_16 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 61 |  |
| science_bowl | science_bowl_sample_set_10_10a_hs_reg_2016_toss_up_17 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 91 |  |
| science_bowl | science_bowl_sample_set_10_11a_hs_reg_2016_bonus_22 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 170 |  |
| science_bowl | science_bowl_sample_set_10_12a_hs_reg_2016_bonus_02 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 57 |  |
| science_bowl | science_bowl_sample_set_10_12a_hs_reg_2016_toss_up_07 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 64 |  |
| science_bowl | science_bowl_sample_set_10_12a_hs_reg_2016_toss_up_12 | 1 | 1 | 100.00% | 4 | 2 | 3 | 2 | 4 | 276 |  |
| science_bowl | science_bowl_sample_set_10_13a_hs_reg_2016_toss_up_03 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 62 |  |
| science_bowl | science_bowl_sample_set_10_14a_hs_reg_2016_bonus_20 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 55 |  |
| science_bowl | science_bowl_sample_set_10_14a_hs_reg_2016_toss_up_23 | 1 | 1 | 100.00% | 0 | 1 | 0.5 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_10_15a_hs_reg_2016_toss_up_11 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 60 |  |
| science_bowl | science_bowl_sample_set_10_16a_hs_reg_2016_bonus_03 | 1 | 1 | 100.00% | 4 | 4 | 4 | 2 | 4 | 288 |  |
| science_bowl | science_bowl_sample_set_10_2a_hs_reg_2016_bonus_10 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 189 |  |
| science_bowl | science_bowl_sample_set_10_5a_hs_reg_2016_bonus_04 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_10_6a_hs_reg_2016_bonus_04 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 60 |  |
| science_bowl | science_bowl_sample_set_10_7a_hs_reg_2016_bonus_06 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 80 |  |
| science_bowl | science_bowl_sample_set_10_8a_hs_reg_2016_bonus_02 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_10_9a_hs_reg_2016_bonus_10 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 4 | 273 |  |
| science_bowl | science_bowl_sample_set_10_9a_hs_reg_2016_bonus_12 | 0 | 1 | 0.00% | 3 | 3 | 3 | 2 | 4 | 207 |  |
| science_bowl | science_bowl_sample_set_10_9a_hs_reg_2016_toss_up_13 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 59 |  |
| science_bowl | science_bowl_sample_set_11_hs_10a_toss_up_02 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 55 |  |
| science_bowl | science_bowl_sample_set_11_hs_15a_bonus_04 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 92 |  |
| science_bowl | science_bowl_sample_set_11_hs_17a_toss_up_18 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 89 |  |
| science_bowl | science_bowl_sample_set_11_hs_3a_toss_up_01 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 2 | 4 | 211 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_12_bonus_13 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 148 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_13_bonus_10 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 61 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_13_bonus_21 | 0 | 1 | 0.00% | 4 | 2 | 3 | 2 | 4 | 370 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_14_toss_up_05 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_15_toss_up_05 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_1_bonus_14 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 97 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_1_toss_up_04 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 57 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_2_bonus_08 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 115 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_2_bonus_23 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_2_toss_up_10 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 81 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_4_bonus_06 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 57 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_5_toss_up_04 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_5_toss_up_12 | 1 | 1 | 100.00% | 3 | 3 | 3 | 2 | 4 | 210 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_6_bonus_03 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 216 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_6_toss_up_10 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 59 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_7_bonus_11 | 1 | 1 | 100.00% | 4 | 2 | 3 | 2 | 4 | 224 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_8_bonus_22 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 192 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_8_toss_up_13 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 60 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_8_toss_up_15 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 4 | 201 |  |
| science_bowl | science_bowl_sample_set_12_2018_hsround_9_bonus_21 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 3 | 7 | 520 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_15a_toss_up_23 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 63 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_17a_bonus_04 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 112 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_17a_bonus_18 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 72 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_17a_toss_up_02 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_17a_toss_up_07 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 63 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_1a_bonus_11 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 182 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_2a_toss_up_19 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 89 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_3a_toss_up_21 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 141 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_4a_toss_up_05 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 60 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_5a_bonus_23 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 147 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_5a_toss_up_12 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 64 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_5a_toss_up_14 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 60 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_5a_toss_up_16 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 62 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_6a_bonus_10 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 65 |  |
| science_bowl | science_bowl_sample_set_13_2019_nsb_hsr_round_6a_bonus_11 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 137 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_11a_toss_up_06 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 61 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_12a_bonus_22 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 371 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_14a_toss_up_11 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 60 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_9a_bonus_06 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 188 |  |
| science_bowl | science_bowl_sample_set_14_2019_nsb_hsr_round_9a_bonus_23 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 132 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd10_bonus_13 | 0 | 1 | 0.00% | 4 | 2 | 3 | 1 | 3 | 128 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd10_bonus_18 | 1 | 1 | 100.00% | 3 | 3 | 3 | 2 | 4 | 223 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd10_toss_up_01 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 64 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd10_toss_up_18 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd11_bonus_06 | 0 | 1 | 0.00% | 5 | 3 | 4 | 2 | 4 | 283 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd13_toss_up_07 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd14_bonus_02 | 1 | 1 | 100.00% | 2 | 2 | 2 | 1 | 3 | 113 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd14_toss_up_05 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 55 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd15_toss_up_05 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 2 | 4 | 230 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd15_toss_up_11 | 1 | 1 | 100.00% | 4 | 3 | 3.5 | 2 | 5 | 280 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd15_toss_up_13 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd17_bonus_11 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 60 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd17_toss_up_02 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 54 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd3_toss_up_03 | 1 | 1 | 100.00% | 3 | 3 | 3 | 2 | 4 | 241 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd5_bonus_07 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 54 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd5_bonus_20 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 166 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd6_bonus_18 | 1 | 1 | 100.00% | 2 | 3 | 2.5 | 2 | 4 | 266 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd6_bonus_23 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 60 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd7_bonus_17 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 304 |  |
| science_bowl | science_bowl_sample_set_15_2020_hs_rd8_bonus_16 | 1 | 1 | 100.00% | 0 | 1 | 0.5 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_16_set_10_hs_2021_toss_up_01 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 57 |  |
| science_bowl | science_bowl_sample_set_16_set_2_hs_2021_bonus_06 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 134 |  |
| science_bowl | science_bowl_sample_set_16_set_2_hs_2021_bonus_08 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 57 |  |
| science_bowl | science_bowl_sample_set_16_set_2_hs_2021_bonus_18 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_16_set_3_hs_2021_bonus_09 | 1 | 1 | 100.00% | 0 | 1 | 0.5 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_16_set_3_hs_2021_toss_up_15 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 61 |  |
| science_bowl | science_bowl_sample_set_16_set_3_hs_2021_toss_up_16 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_16_set_5_hs_2021_bonus_01 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 158 |  |
| science_bowl | science_bowl_sample_set_16_set_5_hs_2021_bonus_05 | 1 | 1 | 100.00% | 4 | 2 | 3 | 2 | 4 | 392 |  |
| science_bowl | science_bowl_sample_set_16_set_5_hs_2021_toss_up_04 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 66 |  |
| science_bowl | science_bowl_sample_set_16_set_5_hs_2021_toss_up_08 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_16_set_6_hs_2021_toss_up_11 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 55 |  |
| science_bowl | science_bowl_sample_set_16_set_7_hs_2021_bonus_11 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 60 |  |
| science_bowl | science_bowl_sample_set_16_set_8_hs_2021_bonus_12 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 73 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_01 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 148 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_02 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_04 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 55 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_10 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 61 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_13 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 2 | 4 | 499 |  |
| science_bowl | science_bowl_sample_set_16_set_9_hs_2021_bonus_18 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_10_bonus_11 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 112 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_10_bonus_16 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 143 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_12_toss_up_18 | 1 | 1 | 100.00% | 0 | 1 | 0.5 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_13_toss_up_02 | 1 | 1 | 100.00% | 2 | 4 | 3 | 2 | 4 | 258 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_15_bonus_01 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_15_toss_up_01 | 1 | 1 | 100.00% | 2 | 2 | 2 | 3 | 7 | 301 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_15_toss_up_05 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 55 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_15_toss_up_10 | 1 | 1 | 100.00% | 0 | 1 | 0.5 | 1 | 2 | 73 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_1_toss_up_17 | 1 | 1 | 100.00% | 2 | 3 | 2.5 | 2 | 4 | 214 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_2_bonus_09 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 52 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_2_bonus_10 | 0 | 1 | 0.00% | 4 | 4 | 4 | 2 | 4 | 241 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_2_toss_up_01 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 61 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_2_toss_up_12 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 57 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_3_bonus_18 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 6 | 776 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_3_toss_up_18 | 1 | 1 | 100.00% | 3 | 3 | 3 | 2 | 4 | 217 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_4_toss_up_05 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 5 | 393 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_6_bonus_05 | 1 | 1 | 100.00% | 4 | 2 | 3 | 2 | 4 | 325 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_6_toss_up_08 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 58 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_8_bonus_01 | 0 | 1 | 0.00% | 2 | 2 | 2 | 1 | 3 | 87 |  |
| science_bowl | science_bowl_sample_set_17_2022_hs_9_bonus_04 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 54 |  |
| science_bowl | science_bowl_sample_set_1_round16_bonus_18 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 51 |  |
| science_bowl | science_bowl_sample_set_1_round7_toss_up_23 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 51 |  |
| science_bowl | science_bowl_sample_set_2_round15_bonus_15 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 48 |  |
| science_bowl | science_bowl_sample_set_4_round11_bonus_04 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 47 |  |
| science_bowl | science_bowl_sample_set_4_round17_bonus_07 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 51 |  |
| science_bowl | science_bowl_sample_set_4_round6_bonus_01 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 49 |  |
| science_bowl | science_bowl_sample_set_5_round15_toss_up_18 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 224 |  |
| science_bowl | science_bowl_sample_set_5_round4_toss_up_09 | 0 | 1 | 0.00% | 2 | 2 | 2 | 1 | 3 | 101 |  |
| science_bowl | science_bowl_sample_set_6_sample6_round15_toss_up_12 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 55 |  |
| science_bowl | science_bowl_sample_set_6_sample6_round15_toss_up_16 | 0 | 1 | 0.00% | 2 | 2 | 2 | 1 | 3 | 100 |  |
| science_bowl | science_bowl_sample_set_6_sample6_round8_toss_up_17 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| science_bowl | science_bowl_sample_set_8_round_10_a_bonus_08 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 63 |  |
| science_bowl | science_bowl_sample_set_8_round_11_a_bonus_21 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 68 |  |
| science_bowl | science_bowl_sample_set_8_round_2_a_toss_up_09 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 3 | 7 | 315 |  |
| science_bowl | science_bowl_sample_set_9_regionalhs_13a_toss_up_16 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 261 |  |
| science_bowl | science_bowl_sample_set_9_regionalhs_4a_toss_up_05 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 56 |  |
| arml_national_team | arml_national_team_2009 | 0 | 50 | 0.00% | 2 | 1 | 1.5 | 3 | 7 | 389 |  |
| arml_national_team | arml_national_team_2010 | 30 | 50 | 60.00% | 2 | 2 | 2 | 3 | 7 | 442 |  |
| arml_national_team | arml_national_team_2011 | 35 | 50 | 70.00% | 2 | 2 | 2 | 3 | 7 | 384 |  |
| arml_national_team | arml_national_team_2012 | 5 | 50 | 10.00% | 2 | 2 | 2 | 2 | 4 | 272 |  |
| arml_national_team | arml_national_team_2013 | 0 | 50 | 0.00% | 3 | 1 | 2 | 4 | 12 | 704 |  |
| arml_national_team | arml_national_team_2014 | 40 | 50 | 80.00% | 2 | 1 | 1.5 | 2 | 5 | 445 |  |
| arml_national_team | arml_national_team_2016 | 0 | 50 | 0.00% | 3 | 2 | 2.5 | 4 | 12 | 2823 |  |
| arml_national_team | arml_national_team_2017 | 0 | 50 | 0.00% | 5 | 2 | 3.5 | 4 | 12 | 1043 |  |
| arml_national_team | arml_national_team_2018 | 0 | 50 | 0.00% | 2 | 2 | 2 | 4 | 12 | 761 |  |
| arml_national_team | arml_national_team_2019 | 0 | 50 | 0.00% | 5 | 2 | 3.5 | 4 | 12 | 1048 |  |
| arml_national_team | arml_national_team_2023 | 0 | 50 | 0.00% | 2 | 2 | 2 | 4 | 12 | 650 |  |
| qanta | qanta_dev_102045 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_dev_149935 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_dev_150473 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_10058 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 45 |  |
| qanta | qanta_train_100927 | 1 | 1 | 100.00% | 0 | 1 | 0.5 | 1 | 2 | 46 |  |
| qanta | qanta_train_101623 | 0 | 1 | 0.00% | 4 | 2 | 3 | 2 | 4 | 263 |  |
| qanta | qanta_train_101808 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_102465 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_10370 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_10469 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_10507 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_105981 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_106095 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_106447 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_106504 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_106567 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_106595 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 45 |  |
| qanta | qanta_train_106604 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_106607 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_106769 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 1 | 3 | 101 |  |
| qanta | qanta_train_106873 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_107061 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_107843 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_107921 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 55 |  |
| qanta | qanta_train_108309 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_108623 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_108704 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_10987 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_110261 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_11143 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_112719 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_112933 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 72 |  |
| qanta | qanta_train_113215 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_113216 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_114201 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_114391 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_11488 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_115444 | 0 | 1 | 0.00% | 2 | 4 | 3 | 2 | 4 | 254 |  |
| qanta | qanta_train_115653 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 2 | 4 | 321 |  |
| qanta | qanta_train_116237 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_11719 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_11838 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_118455 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_119007 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_119982 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_121863 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 45 |  |
| qanta | qanta_train_122042 | 0 | 1 | 0.00% | 2 | 2 | 2 | 1 | 3 | 92 |  |
| qanta | qanta_train_122944 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_123034 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_123766 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_12431 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_125688 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 1 | 3 | 71 |  |
| qanta | qanta_train_12630 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 50 |  |
| qanta | qanta_train_126396 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 43 |  |
| qanta | qanta_train_126475 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_12651 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_12761 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_128424 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_12895 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_129044 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_129066 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 59 |  |
| qanta | qanta_train_13028 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 67 |  |
| qanta | qanta_train_130288 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_131150 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_13154 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_13162 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 57 |  |
| qanta | qanta_train_131686 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_132989 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_133108 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_133321 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_13339 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_13356 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_13399 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_134499 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_135326 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_135767 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_136247 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 5 | 319 |  |
| qanta | qanta_train_136253 | 1 | 1 | 100.00% | 4 | 2 | 3 | 1 | 3 | 69 |  |
| qanta | qanta_train_13695 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 240 |  |
| qanta | qanta_train_13778 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 213 |  |
| qanta | qanta_train_13824 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_138340 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_13850 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_13949 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_139521 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_142297 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_14254 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_142651 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_14319 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_14438 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_144532 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 47 |  |
| qanta | qanta_train_145165 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_146319 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_14673 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 48 |  |
| qanta | qanta_train_146818 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_147291 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_150455 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_15582 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_1566 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 1 | 3 | 100 |  |
| qanta | qanta_train_160121 | 1 | 1 | 100.00% | 4 | 2 | 3 | 1 | 3 | 68 |  |
| qanta | qanta_train_161416 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_161577 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_162884 | 0 | 1 | 0.00% | 4 | 2 | 3 | 1 | 3 | 82 |  |
| qanta | qanta_train_167626 | 1 | 1 | 100.00% | 5 | 2 | 3.5 | 1 | 3 | 113 |  |
| qanta | qanta_train_169176 | 1 | 1 | 100.00% | 5 | 1 | 3 | 1 | 3 | 67 |  |
| qanta | qanta_train_171350 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_171588 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_18751 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 47 |  |
| qanta | qanta_train_20812 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_21606 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_21725 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_26320 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 69 |  |
| qanta | qanta_train_27567 | 0 | 1 | 0.00% | 3 | 4 | 3.5 | 2 | 4 | 268 |  |
| qanta | qanta_train_28946 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_30345 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 55 |  |
| qanta | qanta_train_31095 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_32747 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 48 |  |
| qanta | qanta_train_33372 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_33880 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_35269 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_37123 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_37178 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_37358 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_38544 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_39120 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_39387 | 0 | 1 | 0.00% | 4 | 2 | 3 | 1 | 3 | 180 |  |
| qanta | qanta_train_40825 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 44 |  |
| qanta | qanta_train_42953 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_44955 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 55 |  |
| qanta | qanta_train_46330 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_46554 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_4662 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_46879 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_4810 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_48587 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_49297 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_49460 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_51558 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_51894 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_52355 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_52404 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_52420 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_52729 | 1 | 1 | 100.00% | 5 | 3 | 4 | 2 | 4 | 211 |  |
| qanta | qanta_train_52814 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_52824 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_52856 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 57 |  |
| qanta | qanta_train_52950 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 50 |  |
| qanta | qanta_train_52976 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 61 |  |
| qanta | qanta_train_53007 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_5424 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_55018 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_55218 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_55222 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 3 | 71 |  |
| qanta | qanta_train_56260 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_56844 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_56911 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_56996 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_57002 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_57637 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_57652 | 0 | 1 | 0.00% | 4 | 2 | 3 | 1 | 3 | 70 |  |
| qanta | qanta_train_58420 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_58437 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_5879 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_59764 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_59769 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 57 |  |
| qanta | qanta_train_59890 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_59903 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_60191 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_60415 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_60524 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 50 |  |
| qanta | qanta_train_61076 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_61590 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_62036 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_63832 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 48 |  |
| qanta | qanta_train_64000 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 54 |  |
| qanta | qanta_train_64949 | 1 | 1 | 100.00% | 4 | 2 | 3 | 1 | 3 | 98 |  |
| qanta | qanta_train_6589 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_6629 | 1 | 1 | 100.00% | 0 | 1 | 0.5 | 1 | 2 | 45 |  |
| qanta | qanta_train_68223 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_68245 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_68571 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 49 |  |
| qanta | qanta_train_69534 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_70098 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_70375 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_70475 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_71054 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 50 |  |
| qanta | qanta_train_73579 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_74167 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 2 | 4 | 193 |  |
| qanta | qanta_train_74302 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_7453 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_7490 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_75210 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_75229 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 49 |  |
| qanta | qanta_train_75693 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_75921 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_77359 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_77468 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_77473 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_78025 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 51 |  |
| qanta | qanta_train_7829 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_78402 | 0 | 1 | 0.00% | 4 | 2 | 3 | 2 | 4 | 263 |  |
| qanta | qanta_train_79335 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_801 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_80410 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 232 |  |
| qanta | qanta_train_81669 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 59 |  |
| qanta | qanta_train_8203 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_82309 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 48 |  |
| qanta | qanta_train_83383 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_84125 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_85221 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_85318 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_85600 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_87017 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_87124 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_87261 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_87437 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_87984 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 46 |  |
| qanta | qanta_train_88016 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_8802 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_88892 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_89005 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_89060 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_89461 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 61 |  |
| qanta | qanta_train_89552 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_89751 | 0 | 1 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 256 |  |
| qanta | qanta_train_90157 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_90372 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 47 |  |
| qanta | qanta_train_90427 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_90505 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 50 |  |
| qanta | qanta_train_9051 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_92045 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_92170 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| qanta | qanta_train_92513 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| qanta | qanta_train_9400 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_94004 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| qanta | qanta_train_9492 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 45 |  |
| qanta | qanta_train_95205 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_96580 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 41 |  |
| qanta | qanta_train_9758 | 0 | 1 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 45 |  |
| qanta | qanta_train_98819 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 2 | 42 |  |
| mystery_hunt | mystery_hunt_00002 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 8 | 527 |  |
| mystery_hunt | mystery_hunt_00003 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 9 | 670 |  |
| mystery_hunt | mystery_hunt_00004 | 0 | 1 | 0.00% | 1 | 2 | 1.5 | 2 | 5 | 328 |  |
| mystery_hunt | mystery_hunt_00006 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 601 |  |
| mystery_hunt | mystery_hunt_00007 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 3 | 8 | 887 |  |
| mystery_hunt | mystery_hunt_00009 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 6 | 569 |  |
| mystery_hunt | mystery_hunt_00014 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 5 | 691 |  |
| mystery_hunt | mystery_hunt_00015 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 28 | 1585 |  |
| mystery_hunt | mystery_hunt_00028 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 8 | 575 |  |
| mystery_hunt | mystery_hunt_00032 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 7 | 21 | 1285 |  |
| mystery_hunt | mystery_hunt_00033 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 44 |  |
| mystery_hunt | mystery_hunt_00035 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 6 | 381 |  |
| mystery_hunt | mystery_hunt_00036 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 6 | 374 |  |
| mystery_hunt | mystery_hunt_00038 | 0 | 1 | 0.00% | 3 | 3 | 3 | 2 | 6 | 536 |  |
| mystery_hunt | mystery_hunt_00044 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 8 | 23 | 1198 |  |
| mystery_hunt | mystery_hunt_00068 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 6 | 17 | 980 |  |
| mystery_hunt | mystery_hunt_00078 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 10 | 612 |  |
| mystery_hunt | mystery_hunt_00080 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 12 | 807 |  |
| mystery_hunt | mystery_hunt_00082 | 0 | 1 | 0.00% | 2 | 2 | 2 | 9 | 26 | 1716 |  |
| mystery_hunt | mystery_hunt_00089 | 1 | 1 | 100.00% | 2 | 2 | 2 | 4 | 10 | 874 |  |
| mystery_hunt | mystery_hunt_00094 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 8 | 927 |  |
| mystery_hunt | mystery_hunt_00095 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 8 | 23 | 1231 |  |
| mystery_hunt | mystery_hunt_00096 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 2053 |  |
| mystery_hunt | mystery_hunt_00102 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 8 | 606 |  |
| mystery_hunt | mystery_hunt_00103 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1646 |  |
| mystery_hunt | mystery_hunt_00105 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1652 |  |
| mystery_hunt | mystery_hunt_00106 | 0 | 1 | 0.00% | 2 | 2 | 2 | 5 | 14 | 1230 |  |
| mystery_hunt | mystery_hunt_00112 | 0 | 1 | 0.00% | 2 | 2 | 2 | 6 | 18 | 1363 |  |
| mystery_hunt | mystery_hunt_00113 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1726 |  |
| mystery_hunt | mystery_hunt_00116 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 2126 |  |
| mystery_hunt | mystery_hunt_00118 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1464 |  |
| mystery_hunt | mystery_hunt_00124 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 10 | 1009 |  |
| mystery_hunt | mystery_hunt_00136 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 30 | 1312 |  |
| mystery_hunt | mystery_hunt_00137 | 0 | 1 | 0.00% | 1 | 1 | 1 | 10 | 30 | 1804 |  |
| mystery_hunt | mystery_hunt_00138 | 0 | 1 | 0.00% | 2 | 2 | 2 | 8 | 24 | 1268 |  |
| mystery_hunt | mystery_hunt_00140 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 8 | 766 |  |
| mystery_hunt | mystery_hunt_00144 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1805 |  |
| mystery_hunt | mystery_hunt_00147 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1526 |  |
| mystery_hunt | mystery_hunt_00155 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1088 |  |
| mystery_hunt | mystery_hunt_00160 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 9 | 26 | 1846 |  |
| mystery_hunt | mystery_hunt_00165 | 0 | 1 | 0.00% | 1 | 1 | 1 | 3 | 8 | 497 |  |
| mystery_hunt | mystery_hunt_00166 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 11 | 869 |  |
| mystery_hunt | mystery_hunt_00169 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 10 | 561 |  |
| mystery_hunt | mystery_hunt_00177 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 30 | 1446 |  |
| mystery_hunt | mystery_hunt_00179 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 12 | 817 |  |
| mystery_hunt | mystery_hunt_00182 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 30 | 1667 |  |
| mystery_hunt | mystery_hunt_00184 | 0 | 1 | 0.00% | 2 | 2 | 2 | 9 | 26 | 1264 |  |
| mystery_hunt | mystery_hunt_00185 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 354 |  |
| mystery_hunt | mystery_hunt_00196 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1406 |  |
| mystery_hunt | mystery_hunt_00199 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 7 | 21 | 1193 |  |
| mystery_hunt | mystery_hunt_00201 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 541 |  |
| mystery_hunt | mystery_hunt_00203 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 6 | 391 |  |
| mystery_hunt | mystery_hunt_00215 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 2 | 5 | 369 |  |
| mystery_hunt | mystery_hunt_00220 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 6 | 426 |  |
| mystery_hunt | mystery_hunt_00226 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1429 |  |
| mystery_hunt | mystery_hunt_00356 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 8 | 422 |  |
| mystery_hunt | mystery_hunt_00358 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 303 |  |
| mystery_hunt | mystery_hunt_00368 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 4 | 12 | 617 |  |
| mystery_hunt | mystery_hunt_00371 | 0 | 1 | 0.00% | 2 | 2 | 2 | 5 | 14 | 947 |  |
| mystery_hunt | mystery_hunt_00373 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 6 | 379 |  |
| mystery_hunt | mystery_hunt_00377 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1969 |  |
| mystery_hunt | mystery_hunt_00383 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 8 | 383 |  |
| mystery_hunt | mystery_hunt_00384 | 0 | 1 | 0.00% | 3 | 1 | 2 | 5 | 15 | 1195 |  |
| mystery_hunt | mystery_hunt_00398 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1487 |  |
| mystery_hunt | mystery_hunt_00405 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1926 |  |
| mystery_hunt | mystery_hunt_00408 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1527 |  |
| mystery_hunt | mystery_hunt_00409 | 0 | 1 | 0.00% | 2 | 2 | 2 | 9 | 27 | 1584 |  |
| mystery_hunt | mystery_hunt_00412 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 7 | 19 | 1246 |  |
| mystery_hunt | mystery_hunt_00431 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 9 | 25 | 1477 |  |
| mystery_hunt | mystery_hunt_00433 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1783 |  |
| mystery_hunt | mystery_hunt_00451 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 656 |  |
| mystery_hunt | mystery_hunt_00457 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1857 |  |
| mystery_hunt | mystery_hunt_00529 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1855 |  |
| mystery_hunt | mystery_hunt_00586 | 0 | 1 | 0.00% | 3 | 3 | 3 | 2 | 4 | 446 |  |
| mystery_hunt | mystery_hunt_00601 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 6 | 17 | 1008 |  |
| mystery_hunt | mystery_hunt_00605 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1656 |  |
| mystery_hunt | mystery_hunt_00612 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 413 |  |
| mystery_hunt | mystery_hunt_00617 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1614 |  |
| mystery_hunt | mystery_hunt_00624 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 9 | 27 | 1789 |  |
| mystery_hunt | mystery_hunt_00628 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 8 | 452 |  |
| mystery_hunt | mystery_hunt_00629 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 9 | 26 | 2386 |  |
| mystery_hunt | mystery_hunt_00645 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 7 | 473 |  |
| mystery_hunt | mystery_hunt_00652 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 7 | 480 |  |
| mystery_hunt | mystery_hunt_00653 | 0 | 1 | 0.00% | 2 | 2 | 2 | 6 | 17 | 953 |  |
| mystery_hunt | mystery_hunt_00656 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1433 |  |
| mystery_hunt | mystery_hunt_00681 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 330 |  |
| mystery_hunt | mystery_hunt_00686 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 7 | 523 |  |
| mystery_hunt | mystery_hunt_00687 | 0 | 1 | 0.00% | 4 | 2 | 3 | 2 | 5 | 1274 |  |
| mystery_hunt | mystery_hunt_00691 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 10 | 848 |  |
| mystery_hunt | mystery_hunt_00697 | 0 | 1 | 0.00% | 2 | 2 | 2 | 7 | 20 | 1311 |  |
| mystery_hunt | mystery_hunt_00698 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 7 | 20 | 1375 |  |
| mystery_hunt | mystery_hunt_00708 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1436 |  |
| mystery_hunt | mystery_hunt_00715 | 0 | 1 | 0.00% | 0 | 2 | 1 | 1 | 2 | 43 |  |
| mystery_hunt | mystery_hunt_00719 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 3 | 9 | 501 |  |
| mystery_hunt | mystery_hunt_00743 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 11 | 600 |  |
| mystery_hunt | mystery_hunt_00757 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 2 | 6 | 363 |  |
| mystery_hunt | mystery_hunt_00760 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 5 | 15 | 973 |  |
| mystery_hunt | mystery_hunt_00766 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 4 | 503 |  |
| mystery_hunt | mystery_hunt_00778 | 0 | 1 | 0.00% | 3 | 3 | 3 | 2 | 5 | 349 |  |
| mystery_hunt | mystery_hunt_00791 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 818 |  |
| mystery_hunt | mystery_hunt_00793 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 30 | 1571 |  |
| mystery_hunt | mystery_hunt_00805 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 8 | 549 |  |
| mystery_hunt | mystery_hunt_00810 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 6 | 560 |  |
| mystery_hunt | mystery_hunt_00819 | 1 | 1 | 100.00% | 0 | 2 | 1 | 1 | 3 | 127 |  |
| mystery_hunt | mystery_hunt_00833 | 0 | 1 | 0.00% | 1 | 1 | 1 | 10 | 30 | 1869 |  |
| mystery_hunt | mystery_hunt_00836 | 0 | 1 | 0.00% | 1 | 2 | 1.5 | 2 | 5 | 279 |  |
| mystery_hunt | mystery_hunt_00843 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 2062 |  |
| mystery_hunt | mystery_hunt_00847 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 12 | 865 |  |
| mystery_hunt | mystery_hunt_00868 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 9 | 1183 |  |
| mystery_hunt | mystery_hunt_00869 | 0 | 1 | 0.00% | 1 | 1 | 1 | 2 | 4 | 262 |  |
| mystery_hunt | mystery_hunt_00871 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1588 |  |
| mystery_hunt | mystery_hunt_00874 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 30 | 1796 |  |
| mystery_hunt | mystery_hunt_00882 | 0 | 1 | 0.00% | 4 | 2 | 3 | 8 | 24 | 1187 |  |
| mystery_hunt | mystery_hunt_00887 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 10 | 565 |  |
| mystery_hunt | mystery_hunt_00896 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 9 | 606 |  |
| mystery_hunt | mystery_hunt_00913 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 7 | 387 |  |
| mystery_hunt | mystery_hunt_00916 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1624 |  |
| mystery_hunt | mystery_hunt_00918 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 30 | 1560 |  |
| mystery_hunt | mystery_hunt_00926 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 2 | 4 | 220 |  |
| mystery_hunt | mystery_hunt_00929 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 2247 |  |
| mystery_hunt | mystery_hunt_00930 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 1122 |  |
| mystery_hunt | mystery_hunt_00941 | 0 | 1 | 0.00% | 2 | 2 | 2 | 9 | 26 | 1930 |  |
| mystery_hunt | mystery_hunt_00946 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 627 |  |
| mystery_hunt | mystery_hunt_00948 | 0 | 1 | 0.00% | 1 | 2 | 1.5 | 3 | 7 | 396 |  |
| mystery_hunt | mystery_hunt_00956 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 11 | 856 |  |
| mystery_hunt | mystery_hunt_00960 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 11 | 977 |  |
| mystery_hunt | mystery_hunt_00961 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1341 |  |
| mystery_hunt | mystery_hunt_00994 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1713 |  |
| mystery_hunt | mystery_hunt_01099 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1363 |  |
| mystery_hunt | mystery_hunt_01110 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 6 | 491 |  |
| mystery_hunt | mystery_hunt_01111 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1552 |  |
| mystery_hunt | mystery_hunt_01112 | 0 | 1 | 0.00% | 2 | 2 | 2 | 7 | 19 | 990 |  |
| mystery_hunt | mystery_hunt_01124 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 7 | 21 | 1031 |  |
| mystery_hunt | mystery_hunt_01150 | 0 | 1 | 0.00% | 1 | 2 | 1.5 | 3 | 7 | 357 |  |
| mystery_hunt | mystery_hunt_01151 | 0 | 1 | 0.00% | 1 | 2 | 1.5 | 2 | 5 | 348 |  |
| mystery_hunt | mystery_hunt_01152 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 451 |  |
| mystery_hunt | mystery_hunt_01157 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1244 |  |
| mystery_hunt | mystery_hunt_01173 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 8 | 557 |  |
| mystery_hunt | mystery_hunt_01180 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1543 |  |
| mystery_hunt | mystery_hunt_01189 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 30 | 1625 |  |
| mystery_hunt | mystery_hunt_01206 | 0 | 1 | 0.00% | 2 | 2 | 2 | 7 | 20 | 1285 |  |
| mystery_hunt | mystery_hunt_01209 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 8 | 488 |  |
| mystery_hunt | mystery_hunt_01226 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 29 | 1545 |  |
| mystery_hunt | mystery_hunt_01244 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1445 |  |
| mystery_hunt | mystery_hunt_01261 | 0 | 1 | 0.00% | 2 | 3 | 2.5 | 3 | 7 | 471 |  |
| mystery_hunt | mystery_hunt_01266 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 5 | 15 | 748 |  |
| mystery_hunt | mystery_hunt_01271 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 12 | 1305 |  |
| mystery_hunt | mystery_hunt_01277 | 0 | 1 | 0.00% | 3 | 3 | 3 | 4 | 11 | 706 |  |
| mystery_hunt | mystery_hunt_01278 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 4 | 653 |  |
| mystery_hunt | mystery_hunt_01286 | 0 | 1 | 0.00% | 2 | 2 | 2 | 5 | 14 | 641 |  |
| mystery_hunt | mystery_hunt_01301 | 0 | 1 | 0.00% | 2 | 2 | 2 | 9 | 26 | 1503 |  |
| mystery_hunt | mystery_hunt_01307 | 0 | 1 | 0.00% | 1 | 2 | 1.5 | 3 | 9 | 458 |  |
| mystery_hunt | mystery_hunt_01313 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 657 |  |
| mystery_hunt | mystery_hunt_01315 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 423 |  |
| mystery_hunt | mystery_hunt_01324 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 4 | 346 |  |
| mystery_hunt | mystery_hunt_01337 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 9 | 486 |  |
| mystery_hunt | mystery_hunt_01343 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 392 |  |
| mystery_hunt | mystery_hunt_01357 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 418 |  |
| mystery_hunt | mystery_hunt_01358 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 349 |  |
| mystery_hunt | mystery_hunt_01361 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 12 | 719 |  |
| mystery_hunt | mystery_hunt_01363 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 30 | 1926 |  |
| mystery_hunt | mystery_hunt_01372 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 4 | 10 | 716 |  |
| mystery_hunt | mystery_hunt_01374 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 30 | 1510 |  |
| mystery_hunt | mystery_hunt_01377 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1006 |  |
| mystery_hunt | mystery_hunt_01395 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 11 | 619 |  |
| mystery_hunt | mystery_hunt_01398 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 28 | 1592 |  |
| mystery_hunt | mystery_hunt_01402 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 5 | 14 | 775 |  |
| mystery_hunt | mystery_hunt_01408 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 7 | 19 | 1337 |  |
| mystery_hunt | mystery_hunt_01410 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 8 | 398 |  |
| mystery_hunt | mystery_hunt_01418 | 0 | 1 | 0.00% | 2 | 2 | 2 | 8 | 23 | 1499 |  |
| mystery_hunt | mystery_hunt_01429 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1743 |  |
| mystery_hunt | mystery_hunt_01431 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 8 | 663 |  |
| mystery_hunt | mystery_hunt_01432 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 413 |  |
| mystery_hunt | mystery_hunt_01446 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 7 | 446 |  |
| mystery_hunt | mystery_hunt_01454 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 456 |  |
| mystery_hunt | mystery_hunt_01469 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 6 | 16 | 911 |  |
| mystery_hunt | mystery_hunt_01486 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 2 | 5 | 506 |  |
| mystery_hunt | mystery_hunt_01491 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 7 | 501 |  |
| mystery_hunt | mystery_hunt_01496 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1549 |  |
| mystery_hunt | mystery_hunt_01497 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 8 | 487 |  |
| mystery_hunt | mystery_hunt_01501 | 0 | 1 | 0.00% | 2 | 2 | 2 | 5 | 13 | 1084 |  |
| mystery_hunt | mystery_hunt_01520 | 0 | 1 | 0.00% | 2 | 2 | 2 | 7 | 20 | 1660 |  |
| mystery_hunt | mystery_hunt_01521 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 4 | 11 | 696 |  |
| mystery_hunt | mystery_hunt_01523 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 8 | 457 |  |
| mystery_hunt | mystery_hunt_01543 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 463 |  |
| mystery_hunt | mystery_hunt_01546 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 800 |  |
| mystery_hunt | mystery_hunt_01558 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1624 |  |
| mystery_hunt | mystery_hunt_01566 | 0 | 1 | 0.00% | 4 | 2 | 3 | 4 | 12 | 867 |  |
| mystery_hunt | mystery_hunt_01582 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 7 | 583 |  |
| mystery_hunt | mystery_hunt_01585 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1473 |  |
| mystery_hunt | mystery_hunt_01591 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 2598 |  |
| mystery_hunt | mystery_hunt_01597 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 7 | 594 |  |
| mystery_hunt | mystery_hunt_01603 | 0 | 1 | 0.00% | 2 | 2 | 2 | 5 | 15 | 1029 |  |
| mystery_hunt | mystery_hunt_01610 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 11 | 721 |  |
| mystery_hunt | mystery_hunt_01616 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 11 | 931 |  |
| mystery_hunt | mystery_hunt_01618 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1706 |  |
| mystery_hunt | mystery_hunt_01640 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1597 |  |
| mystery_hunt | mystery_hunt_01642 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 449 |  |
| mystery_hunt | mystery_hunt_01645 | 0 | 1 | 0.00% | 2 | 2 | 2 | 5 | 15 | 1053 |  |
| mystery_hunt | mystery_hunt_01647 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1811 |  |
| mystery_hunt | mystery_hunt_01651 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 6 | 692 |  |
| mystery_hunt | mystery_hunt_01659 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 361 |  |
| mystery_hunt | mystery_hunt_01666 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 9 | 565 |  |
| mystery_hunt | mystery_hunt_01667 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 5 | 13 | 888 |  |
| mystery_hunt | mystery_hunt_01684 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 30 | 1694 |  |
| mystery_hunt | mystery_hunt_01686 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 5 | 489 |  |
| mystery_hunt | mystery_hunt_01687 | 0 | 1 | 0.00% | 2 | 2 | 2 | 8 | 24 | 1272 |  |
| mystery_hunt | mystery_hunt_01689 | 0 | 1 | 0.00% | 3 | 1 | 2 | 8 | 23 | 1240 |  |
| mystery_hunt | mystery_hunt_01692 | 0 | 1 | 0.00% | 4 | 2 | 3 | 10 | 30 | 2120 |  |
| mystery_hunt | mystery_hunt_01702 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 7 | 651 |  |
| mystery_hunt | mystery_hunt_01712 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1760 |  |
| mystery_hunt | mystery_hunt_01719 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 635 |  |
| mystery_hunt | mystery_hunt_01727 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 3 | 7 | 515 |  |
| mystery_hunt | mystery_hunt_01732 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1645 |  |
| mystery_hunt | mystery_hunt_01752 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 423 |  |
| mystery_hunt | mystery_hunt_01775 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 4 | 12 | 725 |  |
| mystery_hunt | mystery_hunt_01794 | 0 | 1 | 0.00% | 4 | 2 | 3 | 2 | 6 | 432 |  |
| mystery_hunt | mystery_hunt_01800 | 0 | 1 | 0.00% | 2 | 2 | 2 | 6 | 17 | 1162 |  |
| mystery_hunt | mystery_hunt_01802 | 0 | 1 | 0.00% | 2 | 2 | 2 | 9 | 27 | 1545 |  |
| mystery_hunt | mystery_hunt_01807 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 3 | 7 | 485 |  |
| mystery_hunt | mystery_hunt_01810 | 0 | 1 | 0.00% | 2 | 2 | 2 | 7 | 20 | 1357 |  |
| mystery_hunt | mystery_hunt_01820 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 5 | 14 | 881 |  |
| mystery_hunt | mystery_hunt_01821 | 0 | 1 | 0.00% | 2 | 2 | 2 | 9 | 27 | 1787 |  |
| mystery_hunt | mystery_hunt_01824 | 0 | 1 | 0.00% | 4 | 2 | 3 | 3 | 9 | 741 |  |
| mystery_hunt | mystery_hunt_01970 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 4 | 274 |  |
| mystery_hunt | mystery_hunt_01985 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1503 |  |
| mystery_hunt | mystery_hunt_01994 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1710 |  |
| mystery_hunt | mystery_hunt_01995 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 297 |  |
| mystery_hunt | mystery_hunt_01997 | 0 | 1 | 0.00% | 4 | 2 | 3 | 2 | 5 | 419 |  |
| mystery_hunt | mystery_hunt_02002 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 9 | 718 |  |
| mystery_hunt | mystery_hunt_02007 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 2 | 5 | 338 |  |
| mystery_hunt | mystery_hunt_02008 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1722 |  |
| mystery_hunt | mystery_hunt_02030 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 12 | 874 |  |
| mystery_hunt | mystery_hunt_02035 | 0 | 1 | 0.00% | 0 | 2 | 1 | 2 | 4 | 106 |  |
| mystery_hunt | mystery_hunt_02037 | 0 | 1 | 0.00% | 2 | 2 | 2 | 6 | 18 | 1203 |  |
| mystery_hunt | mystery_hunt_02040 | 0 | 1 | 0.00% | 2 | 2 | 2 | 2 | 5 | 399 |  |
| mystery_hunt | mystery_hunt_02044 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 5 | 14 | 814 |  |
| mystery_hunt | mystery_hunt_02045 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1741 |  |
| mystery_hunt | mystery_hunt_02062 | 0 | 1 | 0.00% | 2 | 2 | 2 | 3 | 7 | 421 |  |
| mystery_hunt | mystery_hunt_02080 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 30 | 1658 |  |
| mystery_hunt | mystery_hunt_02103 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1607 |  |
| mystery_hunt | mystery_hunt_02107 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 10 | 30 | 1575 |  |
| mystery_hunt | mystery_hunt_02109 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1673 |  |
| mystery_hunt | mystery_hunt_02124 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1959 |  |
| mystery_hunt | mystery_hunt_02133 | 0 | 1 | 0.00% | 1 | 1 | 1 | 10 | 30 | 1449 |  |
| mystery_hunt | mystery_hunt_02144 | 0 | 1 | 0.00% | 3 | 2 | 2.5 | 6 | 18 | 1322 |  |
| mystery_hunt | mystery_hunt_02146 | 0 | 1 | 0.00% | 2 | 2 | 2 | 10 | 30 | 1357 |  |
| mystery_hunt | mystery_hunt_02156 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 2140 |  |
| mystery_hunt | mystery_hunt_02166 | 0 | 1 | 0.00% | 4 | 2 | 3 | 2 | 6 | 668 |  |
| mystery_hunt | mystery_hunt_02174 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1711 |  |
| mystery_hunt | mystery_hunt_02185 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1485 |  |
| mystery_hunt | mystery_hunt_02186 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1372 |  |
| mystery_hunt | mystery_hunt_02197 | 0 | 1 | 0.00% | 4 | 2 | 3 | 9 | 25 | 1195 |  |
| mystery_hunt | mystery_hunt_02200 | 0 | 1 | 0.00% | 4 | 2 | 3 | 9 | 27 | 2618 |  |
| mystery_hunt | mystery_hunt_02203 | 0 | 1 | 0.00% | 4 | 1 | 2.5 | 10 | 30 | 2274 |  |
| mystery_hunt | mystery_hunt_02205 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 5 | 13 | 531 |  |
| mystery_hunt | mystery_hunt_02218 | 0 | 1 | 0.00% | 2 | 2 | 2 | 4 | 10 | 435 |  |
| mystery_hunt | mystery_hunt_02220 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1295 |  |
| mystery_hunt | mystery_hunt_02241 | 0 | 1 | 0.00% | 2 | 2 | 2 | 5 | 14 | 1052 |  |
| mystery_hunt | mystery_hunt_02258 | 0 | 1 | 0.00% | 3 | 1 | 2 | 10 | 30 | 1586 |  |
| mystery_hunt | mystery_hunt_02262 | 0 | 1 | 0.00% | 2 | 1 | 1.5 | 10 | 30 | 1442 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_1 | 0 | 60 | 0.00% | 0 | 2 | 1 | 1 | 3 | 427 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_2 | 36 | 60 | 60.00% | 2 | 2 | 2 | 2 | 4 | 506 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_5 | 35 | 60 | 58.33% | 4 | 2 | 3 | 2 | 5 | 500 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_6 | 48 | 60 | 80.00% | 3 | 2 | 2.5 | 2 | 5 | 705 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_7 | 42 | 60 | 70.00% | 4 | 2 | 3 | 2 | 5 | 630 |  |
| history_olympiad | history_olympiad_bowl_2017_2018_ihbb_alpha_set_high_school_bowl_round_8 | 39 | 59 | 66.10% | 0 | 2 | 1 | 1 | 3 | 437 |  |
| history_olympiad | history_olympiad_bowl_2018_2019_ihbb_asia_alpha_set_bowl_round_2 | 0 | 60 | 0.00% | 1 | 1 | 1 | 2 | 5 | 585 |  |
| history_olympiad | history_olympiad_bowl_2018_2019_ihbb_asia_alpha_set_bowl_round_4 | 40 | 60 | 66.67% | 3 | 2 | 2.5 | 3 | 8 | 983 |  |
| history_olympiad | history_olympiad_bowl_2018_2019_ihbb_asia_alpha_set_bowl_round_5 | 49 | 60 | 81.67% | 3 | 2 | 2.5 | 2 | 4 | 580 |  |
| history_olympiad | history_olympiad_bowl_2018_2019_ihbb_asia_alpha_set_bowl_round_7 | 0 | 60 | 0.00% | 4 | 2 | 3 | 3 | 8 | 1142 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_1 | 0 | 60 | 0.00% | 0 | 2 | 1 | 2 | 4 | 393 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_2 | 31 | 60 | 51.67% | 4 | 2 | 3 | 2 | 5 | 598 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_3 | 46 | 59 | 77.97% | 3 | 3 | 3 | 2 | 6 | 808 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_4 | 38 | 58 | 65.52% | 2 | 2 | 2 | 2 | 6 | 899 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_5 | 48 | 59 | 81.36% | 4 | 2 | 3 | 2 | 4 | 798 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_6 | 0 | 59 | 0.00% | 2 | 2 | 2 | 2 | 4 | 937 |  |
| history_olympiad | history_olympiad_bowl_2019_2020_asia_beta_set_bowl_round_7 | 34 | 60 | 56.67% | 2 | 2 | 2 | 2 | 5 | 708 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_finals | 0 | 59 | 0.00% | 2 | 3 | 2.5 | 2 | 5 | 1290 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_quarterfinals | 0 | 59 | 0.00% | 0 | 2 | 1 | 2 | 4 | 452 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_1 | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 2 | 5 | 1076 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_2 | 0 | 60 | 0.00% | 2 | 2 | 2 | 2 | 5 | 838 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_3 | 48 | 60 | 80.00% | 0 | 2 | 1 | 2 | 4 | 452 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_4 | 0 | 60 | 0.00% | 4 | 2 | 3 | 4 | 11 | 1466 |  |
| history_olympiad | history_olympiad_bowl_2019_ihbb_asian_championships_international_history_bowl_round_5 | 1 | 60 | 1.67% | 4 | 2 | 3 | 4 | 12 | 978 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_1 | 32 | 60 | 53.33% | 2 | 1 | 1.5 | 3 | 8 | 776 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_2 | 15 | 59 | 25.42% | 2 | 2 | 2 | 1 | 3 | 308 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_3 | 39 | 60 | 65.00% | 0 | 2 | 1 | 2 | 4 | 442 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_4 | 30 | 59 | 50.85% | 2 | 1 | 1.5 | 2 | 5 | 526 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_5 | 1 | 60 | 1.67% | 2 | 2 | 2 | 3 | 8 | 833 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_6 | 33 | 60 | 55.00% | 4 | 3 | 3.5 | 3 | 7 | 1073 |  |
| history_olympiad | history_olympiad_bowl_a_set_bowl_round_7 | 0 | 60 | 0.00% | 3 | 2 | 2.5 | 2 | 5 | 698 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_1_hs | 0 | 60 | 0.00% | 4 | 2 | 3 | 2 | 5 | 1290 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_2 | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 3 | 9 | 1209 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_2_hs_asia_and_europe_1 | 0 | 60 | 0.00% | 2 | 2 | 2 | 2 | 4 | 443 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_3 | 35 | 59 | 59.32% | 0 | 2 | 1 | 2 | 4 | 459 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_3_hs_1 | 38 | 59 | 64.41% | 3 | 2 | 2.5 | 3 | 8 | 866 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_4 | 40 | 60 | 66.67% | 3 | 1 | 2 | 3 | 9 | 838 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_4_hs_1 | 39 | 58 | 67.24% | 0 | 2 | 1 | 2 | 4 | 419 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_5 | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 671 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_6 | 40 | 60 | 66.67% | 3 | 2 | 2.5 | 1 | 3 | 440 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_6_hs_1 | 27 | 60 | 45.00% | 3 | 2 | 2.5 | 2 | 6 | 697 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_7 | 0 | 60 | 0.00% | 0 | 2 | 1 | 2 | 4 | 459 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_7_hs_1 | 37 | 60 | 61.67% | 2 | 1 | 1.5 | 2 | 4 | 617 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_8 | 0 | 60 | 0.00% | 1 | 2 | 1.5 | 2 | 5 | 596 |  |
| history_olympiad | history_olympiad_bowl_bowl_round_8_hs_1 | 0 | 60 | 0.00% | 1 | 2 | 1.5 | 2 | 4 | 538 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_1 | 35 | 60 | 58.33% | 0 | 2 | 1 | 2 | 4 | 428 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_2 | 0 | 60 | 0.00% | 2 | 2 | 2 | 3 | 7 | 1088 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_3 | 42 | 60 | 70.00% | 2 | 1 | 1.5 | 2 | 5 | 663 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_4 | 33 | 60 | 55.00% | 0 | 2 | 1 | 2 | 4 | 430 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_5 | 15 | 60 | 25.00% | 4 | 2 | 3 | 3 | 7 | 1117 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_6 | 36 | 62 | 58.06% | 2 | 2 | 2 | 2 | 4 | 574 |  |
| history_olympiad | history_olympiad_bowl_fall_league_history_bowl_round_7 | 0 | 62 | 0.00% | 4 | 2 | 3 | 2 | 5 | 1009 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_1 | 0 | 60 | 0.00% | 2 | 3 | 2.5 | 2 | 5 | 880 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_2 | 34 | 60 | 56.67% | 3 | 2 | 2.5 | 2 | 6 | 659 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_3 | 38 | 59 | 64.41% | 0 | 2 | 1 | 2 | 4 | 492 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_4 | 36 | 60 | 60.00% | 4 | 2 | 3 | 2 | 6 | 1105 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_5 | 35 | 60 | 58.33% | 0 | 2 | 1 | 2 | 4 | 502 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_6 | 39 | 60 | 65.00% | 2 | 2 | 2 | 2 | 6 | 761 |  |
| history_olympiad | history_olympiad_bowl_history_bowl_round_7 | 39 | 60 | 65.00% | 4 | 3 | 3.5 | 2 | 4 | 979 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_1 | 39 | 60 | 65.00% | 3 | 3 | 3 | 3 | 9 | 832 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_2 | 43 | 60 | 71.67% | 4 | 2 | 3 | 3 | 7 | 747 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_3 | 36 | 60 | 60.00% | 3 | 2 | 2.5 | 2 | 5 | 832 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_4 | 32 | 60 | 53.33% | 0 | 2 | 1 | 1 | 3 | 468 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_5 | 0 | 60 | 0.00% | 3 | 3 | 3 | 2 | 6 | 1439 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_6 | 36 | 60 | 60.00% | 0 | 2 | 1 | 3 | 7 | 585 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_7 | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 2 | 5 | 1058 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_8 | 0 | 60 | 0.00% | 2 | 1 | 1.5 | 9 | 26 | 1770 |  |
| history_olympiad | history_olympiad_bowl_ihbb_asia_bowl_round_9_backup_packet | 0 | 60 | 0.00% | 4 | 3 | 3.5 | 2 | 4 | 724 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_1_varsity_and_jv | 34 | 60 | 56.67% | 3 | 2 | 2.5 | 2 | 5 | 767 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_3_varsity_and_jv | 0 | 60 | 0.00% | 2 | 3 | 2.5 | 3 | 7 | 1250 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_4_varsity_and_jv | 0 | 60 | 0.00% | 0 | 2 | 1 | 2 | 4 | 445 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_6_varsity_and_jv | 37 | 59 | 62.71% | 4 | 2 | 3 | 2 | 5 | 652 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_7_varsity_and_jv | 0 | 60 | 0.00% | 3 | 3 | 3 | 2 | 4 | 918 |  |
| history_olympiad | history_olympiad_bowl_ihbb_championships_history_bowl_round_8_varsity_and_jv | 44 | 59 | 74.58% | 2 | 2 | 2 | 2 | 6 | 731 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r1 | 0 | 60 | 0.00% | 2 | 2 | 2 | 3 | 7 | 841 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r2 | 0 | 60 | 0.00% | 0 | 2 | 1 | 1 | 2 | 393 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r3 | 28 | 60 | 46.67% | 0 | 2 | 1 | 2 | 4 | 486 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r4 | 34 | 60 | 56.67% | 3 | 4 | 3.5 | 3 | 7 | 569 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r5 | 35 | 59 | 59.32% | 3 | 2 | 2.5 | 3 | 7 | 586 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r6 | 39 | 60 | 65.00% | 0 | 2 | 1 | 2 | 4 | 446 |  |
| history_olympiad | history_olympiad_bowl_ihbb_winter_bowl_r7 | 0 | 60 | 0.00% | 1 | 2 | 1.5 | 2 | 4 | 578 |  |
| history_olympiad | history_olympiad_bowl_intl_history_olympiad_history_bowl_samples | 17 | 24 | 70.83% | 2 | 2 | 2 | 2 | 5 | 520 |  |
| history_olympiad | history_olympiad_bowl_playoff_rd_1_history_bowl_2021_ihbb_asian_championships | 42 | 60 | 70.00% | 3 | 2 | 2.5 | 2 | 5 | 629 |  |
| history_olympiad | history_olympiad_bowl_playoff_rd_2_history_bowl_2021_ihbb_asian_championships | 38 | 59 | 64.41% | 0 | 2 | 1 | 1 | 3 | 431 |  |
| history_olympiad | history_olympiad_bowl_rd_1_history_bowl_2021_ihbb_asian_championships | 0 | 60 | 0.00% | 0 | 1 | 0.5 | 1 | 2 | 365 |  |
| history_olympiad | history_olympiad_bowl_rd_2_history_bowl_2021_ihbb_asian_championships | 0 | 60 | 0.00% | 2 | 2 | 2 | 2 | 4 | 554 |  |
| history_olympiad | history_olympiad_bowl_rd_3_history_bowl_2021_ihbb_asian_championships | 29 | 60 | 48.33% | 0 | 2 | 1 | 1 | 2 | 376 |  |
| history_olympiad | history_olympiad_bowl_rd_4_history_bowl_2021_ihbb_asian_championships | 0 | 60 | 0.00% | 3 | 3 | 3 | 2 | 5 | 1149 |  |
| history_olympiad | history_olympiad_bowl_rd_5_history_bowl_2021_ihbb_asian_championships | 38 | 60 | 63.33% | 2 | 2 | 2 | 2 | 5 | 608 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_1 | 37 | 60 | 61.67% | 3 | 2 | 2.5 | 2 | 5 | 863 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_2 | 37 | 58 | 63.79% | 0 | 2 | 1 | 1 | 2 | 419 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_3 | 0 | 60 | 0.00% | 0 | 2 | 1 | 2 | 4 | 435 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_4 | 16 | 59 | 27.12% | 0 | 2 | 1 | 1 | 2 | 278 |  |
| history_olympiad | history_olympiad_bowl_varsityjv_bowl_round_5 | 0 | 60 | 0.00% | 4 | 2 | 3 | 3 | 7 | 735 |  |
| history_olympiad | history_olympiad_bowl_vjv_bowl_round_1 | 0 | 56 | 0.00% | 3 | 2 | 2.5 | 3 | 9 | 819 |  |
| purple_comet | purple_comet_hs_2018 | 0 | 30 | 0.00% | 2 | 2 | 2 | 3 | 9 | 693 |  |
| purple_comet | purple_comet_hs_2019 | 2 | 30 | 6.67% | 2 | 2 | 2 | 3 | 7 | 481 |  |
| purple_comet | purple_comet_hs_2020 | 0 | 30 | 0.00% | 2 | 1 | 1.5 | 5 | 14 | 679 |  |
| purple_comet | purple_comet_hs_2021 | 0 | 30 | 0.00% | 4 | 3 | 3.5 | 3 | 8 | 386 |  |
| purple_comet | purple_comet_hs_2022 | 0 | 30 | 0.00% | 3 | 2 | 2.5 | 4 | 11 | 768 |  |
| purple_comet | purple_comet_hs_2023 | 0 | 30 | 0.00% | 2 | 1 | 1.5 | 18 | 54 | 2346 |  |
| purple_comet | purple_comet_hs_2024 | 0 | 30 | 0.00% | 2 | 2 | 2 | 2 | 5 | 357 |  |
| purple_comet | purple_comet_ms_2018 | 0 | 20 | 0.00% | 2 | 2 | 2 | 2 | 6 | 785 |  |
| purple_comet | purple_comet_ms_2019 | 0 | 20 | 0.00% | 2 | 1 | 1.5 | 4 | 11 | 866 |  |
| purple_comet | purple_comet_ms_2020 | 0 | 20 | 0.00% | 2 | 2 | 2 | 5 | 14 | 1237 |  |
| purple_comet | purple_comet_ms_2021 | 0 | 20 | 0.00% | 1 | 1 | 1 | 18 | 54 | 2453 |  |
| purple_comet | purple_comet_ms_2022 | 1 | 20 | 5.00% | 2 | 2 | 2 | 3 | 8 | 376 |  |
| purple_comet | purple_comet_ms_2023 | 0 | 20 | 0.00% | 2 | 1 | 1.5 | 4 | 11 | 533 |  |
| purple_comet | purple_comet_ms_2024 | 0 | 20 | 0.00% | 2 | 2 | 2 | 2 | 6 | 419 |  |
| hmmt_guts | hmmt_guts_2024 | 0 | 36 | 0.00% | 2 | 1 | 1.5 | 2 | 4 | 1843 |  |
| wmtc | wmtc_2018_advanced | 0 | 14 | 0.00% | 2 | 2 | 2 | 3 | 9 | 481 |  |
| wmtc | wmtc_2018_intermediate | 0 | 14 | 0.00% | 3 | 1 | 2 | 11 | 32 | 1853 |  |
| wmtc | wmtc_2018_junior | 0 | 14 | 0.00% | 2 | 2 | 2 | 4 | 11 | 2669 |  |
| **TOTAL** | **771 sessions** | **2250** | **7521** | **macro 20.69%** | **mean 1.43** | **mean 1.93** | **mean 1.68** | **2359** | **6371** | **409055** |  |

---

## 6. ICPC World Finals (contest-session, programming)

Separate from the structured-gold suite above. Same model / team size / turn clock as the gold contest sessions: Perplexity `openai/gpt-5.4-mini`, native tools, team size 3, `max_turns=50`, `max_simulated_minutes=300`, no API/token cap. Remote judging via local VJudge gateway → Kattis.

**Status (2026-09-04):** OTC + Vanilla for WF 2012 and WF 2014 complete. OTC rows below are the **judge-oracle gate** reruns (see 6.0); pre-fix OTC runs are kept for the before/after.

### 6.0 Fix applied before the OTC reruns (judge-oracle gate)

Pre-fix OTC runs produced sample-AC code but almost never reached a remote submit (WF 2014: **0** submits in 50 turns; WF 2012 rerun under the scheduler-only fix: 14 sample ACs, 9 reviews, **0** submits). Root cause was the strategic review gate, not the model:

1. `submit_code` was hidden until an independent **approve** on the exact version. Reviewers rejected sample-AC code on "not formally proven" grounds 9/9 times, so the team could never submit.
2. The coach scheduler moved the shared active-task cursor to unstarted assignments right after a sample AC, so pending reviews/submits were abandoned.

Changes (`src/contest_runner.py`, `src/contest_session.py`):

- Gate: sample AC + **one independent review of either decision** unlocks `submit_code`. A reject is advice to revise, not a veto; the remote judge is the oracle. Gate guidance after a reject now offers "fix and re-run samples" **or** "submit anyway".
- Scheduler: for programming tasks, pending reviews and reviewed-but-unsubmitted sample-AC versions are scheduled before untouched assignments.
- System prompt step (3)/(4) rewritten accordingly; reviewers are told to reject only with a concrete defect or failing input.
- Regression tests: `test_sample_ac_code_can_be_submitted_after_independent_reject`, `test_coach_scheduler_prioritizes_pending_review_over_unstarted_work`, `test_coach_scheduler_prioritizes_approved_code_over_unstarted_work`.

Vanilla is unaffected by the change (no review gate, no coach scheduler), so the original Vanilla runs remain the matched controls.

### 6.1 Session summary

| Contest | Variant | Acc (score/max) | CS | Comm | Plan | AAR | AB | turns | API | tokens | penalty_min | remote attempts | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| WF 2012 | **OTC** (judge-oracle) | **8.3%** (1/12) | 3.0 | 3.0 | 3.0 | 36.1% | 0.031 | 50 | 151 | 35,525 | 80 | **5** | `fibonacci` WA→WA→WA→**AC** (turn 37); `bustour` TLE |
| WF 2012 | OTC (pre-fix) | 8.3% (1/12) | 3.0 | 4.0 | 2.0 | 22.2% | ~0 | 50 | 151 | 61,772 | 0 | 1 | AC `fibonacci` on the only submit; `bustour` sample-AC ×2 never submitted |
| WF 2012 | **Vanilla** | **0.0%** (0/12) | 2.5 | 3.0 | 2.0 | 16.7% | 0.130 | 50 | 150 | 15,697 | 200 | 12 | All 12 submits on `fibonacci`: SAMPLE_WA / TLE / WA; no AC |
| WF 2014 | **OTC** (judge-oracle) | **0.0%** (0/12) | 2.0 | 2.0 | 2.0 | 27.8% | 0.000 | 50 | 151 | 46,710 | 20 | **1** | `game` TLE; 88 local runs, only 2 sample ACs |
| WF 2014 | OTC (pre-fix) | 0.0% (0/12) | 2.5 | 4.0 | 1.0 | 33.3% | 0.008 | 50 | 151 | 42,334 | 0 | 0 | 65 local sample runs; never `submit_code` |
| WF 2014 | **Vanilla** | **0.0%** (0/12) | 2.5 | 3.0 | 2.0 | 33.3% | 0.235 | 50 | 150 | 12,281 | 20 | 7 | SAMPLE_WA on baggage/buffet; 1× WA on buffet |

Matched pairs (same model/budget): WF 2012 OTC **1/12** vs Vanilla **0/12**; WF 2014 both **0/12**. After the fix, OTC WF 2012 shows the intended ICPC loop — remote WA → revise → resubmit → AC — instead of a single lucky submit. WF 2014 remains 0 for both variants because the team rarely passes the official samples (2/88 local runs for OTC); that is a model-capability ceiling, not a protocol block. Vanilla 2012 burned the clock retrying `fibonacci` (12 attempts, 200 penalty minutes).

### 6.2 Vanilla WF 2012 — per-task scores

| task_id | score | max |
|---|---:|---:|
| icpc_wf_2012_bottles | 0 | 1 |
| icpc_wf_2012_bustour | 0 | 1 |
| icpc_wf_2012_fibonacci | 0 | 1 |
| icpc_wf_2012_flightpath | 0 | 1 |
| icpc_wf_2012_infiltration2 | 0 | 1 |
| icpc_wf_2012_keys | 0 | 1 |
| icpc_wf_2012_minflow | 0 | 1 |
| icpc_wf_2012_rangers | 0 | 1 |
| icpc_wf_2012_roomservice | 0 | 1 |
| icpc_wf_2012_safebet | 0 | 1 |
| icpc_wf_2012_stacking | 0 | 1 |
| icpc_wf_2012_takeover | 0 | 1 |

Artifact: `results/icpc_wf_2012_vanilla_perplexity_gpt54mini_native_20260903/`.

### 6.3 Vanilla WF 2014 — per-task scores

| task_id | score | max |
|---|---:|---:|
| icpc_wf_2014_baggage | 0 | 1 |
| icpc_wf_2014_buffet | 0 | 1 |
| icpc_wf_2014_crane | 0 | 1 |
| icpc_wf_2014_game | 0 | 1 |
| icpc_wf_2014_maze | 0 | 1 |
| icpc_wf_2014_messenger | 0 | 1 |
| icpc_wf_2014_metal | 0 | 1 |
| icpc_wf_2014_pachinko | 0 | 1 |
| icpc_wf_2014_sensor | 0 | 1 |
| icpc_wf_2014_skiing | 0 | 1 |
| icpc_wf_2014_surveillance | 0 | 1 |
| icpc_wf_2014_wire | 0 | 1 |

Vanilla spent budget on `rest` / `scoreboard` / `work` / sample-gated `submit_code` (7 submits, no AC). Artifact: `results/icpc_wf_2014_vanilla_perplexity_gpt54mini_native_20260903/`.

### 6.4 OTC WF 2014 — per-task scores

| task_id | score | max |
|---|---:|---:|
| icpc_wf_2014_baggage | 0 | 1 |
| icpc_wf_2014_buffet | 0 | 1 |
| icpc_wf_2014_crane | 0 | 1 |
| icpc_wf_2014_game | 0 | 1 |
| icpc_wf_2014_maze | 0 | 1 |
| icpc_wf_2014_messenger | 0 | 1 |
| icpc_wf_2014_metal | 0 | 1 |
| icpc_wf_2014_pachinko | 0 | 1 |
| icpc_wf_2014_sensor | 0 | 1 |
| icpc_wf_2014_skiing | 0 | 1 |
| icpc_wf_2014_surveillance | 0 | 1 |
| icpc_wf_2014_wire | 0 | 1 |

Judge-oracle rerun: 1 remote submit (`game` TLE, turn 24); 88 local `execute_code` runs, only 2 sample ACs (`game`), so no other version became submittable. Artifact: `results/icpc_wf_2014_otc_judge_oracle_perplexity_gpt54mini_native_20260904/`.
Pre-fix run: 0 remote submits; `assignment_task_scheduled` ×140, local runs ×65 with sample ACs on `crane`/`maze` that were rejected in review and never submitted. Artifact: `results/icpc_wf_2014_otc_perplexity_gpt54mini_native_20260904/`.

### 6.5 OTC WF 2012 (judge-oracle) — submission trace

| turn | task | verdict | note |
|---:|---|---|---|
| 13 | fibonacci | — | sample AC; reviewer **reject** (recurrence unproven) |
| 21 | fibonacci | **WA** | author submitted after an approve on a revised version |
| 26 | fibonacci | **WA** | revised, resubmitted |
| 29 | fibonacci | **WA** | revised, resubmitted |
| 37 | fibonacci | **AC** | fourth attempt; 60 penalty minutes accrued |
| 48 | bustour | **TLE** | first submit of a sample-AC version |

Reviews: 4 approve / 6 reject; 14 sample ACs. Artifact: `results/icpc_wf_2012_otc_judge_oracle_perplexity_gpt54mini_native_20260904/`.

## 7. Artifacts

| Path | Contents |
|---|---|
| `results/otc_arml_science_bowl_20260903/` | OTC Wave1 (146) |
| `results/vanilla_arml_science_bowl_20260903/` | Vanilla Wave1 (146) |
| `results/otc_gold_remaining_20260903/` | OTC Remaining (625) |
| `results/vanilla_gold_remaining_20260903/` | Vanilla Remaining (625) |
| `results/icpc_wf_2012_otc_judge_oracle_perplexity_gpt54mini_native_20260904/` | ICPC WF 2012 OTC, judge-oracle gate (1/12, 5 submits) |
| `results/icpc_wf_2012_pair_perplexity_gpt54mini_native_20260903/` | ICPC WF 2012 OTC, pre-fix (1/12, 1 submit) |
| `results/icpc_wf_2012_otc_scheduler_fix_perplexity_gpt54mini_native_20260904/` | ICPC WF 2012 OTC, scheduler-only fix (0/12, 0 submits; diagnostic) |
| `results/icpc_wf_2012_vanilla_perplexity_gpt54mini_native_20260903/` | ICPC WF 2012 vanilla (0/12) |
| `results/icpc_wf_2014_otc_judge_oracle_perplexity_gpt54mini_native_20260904/` | ICPC WF 2014 OTC, judge-oracle gate (0/12, 1 submit) |
| `results/icpc_wf_2014_otc_perplexity_gpt54mini_native_20260904/` | ICPC WF 2014 OTC, pre-fix (0/12, 0 submits) |
| `results/icpc_wf_2014_vanilla_perplexity_gpt54mini_native_20260903/` | ICPC WF 2014 vanilla (0/12) |
| `results/gold_suite_sheets_20260903/icpc_*.tsv` | ICPC sheets (`scripts/_export_icpc_sheets.py`) |
| `results/gold_suite_results_20260903.md` | Compact auto report |
| `results/arml_national_team_clean_50turn_otc_20260904/` | National Team clean OTC (50 turns) |
| `results/arml_national_team_clean_50turn_vanilla_20260904/` | National Team clean Vanilla (50 turns) |
| `results/otc_task_routing_low_accuracy_20260904/` | Low-accuracy OTC rerun **complete** (374; History 64.4%, MH 0.4%) |
| Each session | `contest_session.json` + `summary.tsv` at run root |

```bash
# Regenerate compact report
python scripts/write_gold_suite_report.py
```

Weekly narrative context: [weekly-summary-2026-08-26-to-09-01.md](weekly-summary-2026-08-26-to-09-01.md) §9 (code) / §10 (metrics).  
Protocol follow-up write-up: [contest-session-followups-20260904.md](contest-session-followups-20260904.md).  
Later protocol hardening (Docker judge, vanilla deadline parity, …): [otc-protocol-fixes-20260906.md](otc-protocol-fixes-20260906.md).

## 8. Follow-ups after this suite — **done**

Canonical write-up: [contest-session-followups-20260904.md](contest-session-followups-20260904.md).

| Item | Result |
|---|---|
| National Team clean split / no-leak / 50-turn | OTC **22.3%** vs Vanilla **0%** |
| Low-accuracy OTC (task routing + 50 turns) | History **64.4%**; Purple **9.2%**; WMTC **16.7%**; HMMT **2.8%**; MH **0.4%** |
| Corrected session-weighted OTC Acc | **~25.9%** (original gold OTC was 18.6%) |

**Still optional:** paired Vanilla under the same 50-turn + routing setup for History/math; Mystery Hunt text-solvable filter; full 50-turn re-run of Local / Science Bowl / Qanta.
