# Contest-session follow-ups — National clean + low-accuracy OTC rerun (2026-09-04/05)

> Model: Perplexity `openai/gpt-5.4-mini`, native tools, team size 3  
> Parent suite: [contest-session-gold-suite-20260903.md](contest-session-gold-suite-20260903.md)  
> Status: **all experiments in this note complete**  
> Last updated: 2026-09-07

## Executive summary

| What changed | Before (gold OTC) | After (rerun) |
|---|---|---|
| Session-weighted OTC Acc (771, with substitutions) | 18.6% | **~25.9%** |
| `arml_national_team` (paired clean) | OTC 15.7% / Van 20.0% (contaminated) | OTC **22.3%** / Van **0%** |
| `history_olympiad` (OTC only rerun) | 8.0% | **64.4%** (beats original Van 36%) |
| `purple_comet` / `hmmt_guts` / `wmtc` | all ~0% | **9.2% / 2.8% / 16.7%** (all nonzero packets) |
| `mystery_hunt` | 0.4% | **0.4%** (data/env limited, not gold-JSON bug) |

Canonical corrected by-competition table also lives in gold-suite **§3.1**.

## Status board

| Experiment | Status | Headline |
|---|---|---|
| Gold suite (771×2) | **Complete** | OTC 18.6% vs Vanilla 20.7% (pre-fix baseline) |
| National Team clean rerun (split + no answer leak + 50 turns) | **Complete** | OTC **22.3%** (11/11 nz) vs Vanilla **0%** |
| Low-accuracy OTC rerun (task routing + 50 turns) | **Complete** | History **64.4%**; math packets nonzero; MH still **0.4%** |
| ICPC judge-oracle OTC | **Complete** | See gold-suite §6 |

No other gold-suite competitions have been fully re-run under the new 50-turn default yet.

---

## Fixes applied before these reruns

1. **Task-family routing** — mathematics / short-answer / puzzle / programming prompts no longer dump non-programming contests into a programming workflow (HMMT/WMTC/Purple used to get stdin/stdout instructions).
2. **Deadline draft submit** — strategic sessions submit latest non-programming drafts at end if review gates blocked them.
3. **National Team parser** — recognize `T-1.` markers; strip `Team Answers` / `Team Solutions` so prompts no longer leak the answer key; each year becomes 9–10 tasks in one session.
4. **Unified 50-turn budget** — `STANDARD_MAX_TURNS=50`; contest-session clock floor is `max(official_minutes, 50 × minutes_per_turn)` so a 20-minute National clock can no longer stop the run at turn 4.
5. **Wall-clock timing** — every new `contest_session.json` records `timing.elapsed_seconds` / `budget.wall_seconds_used`.

---

## 1. ARML National Team — clean 50-turn paired rerun

**Artifacts**

- OTC: `results/arml_national_team_clean_50turn_otc_20260904/`
- Vanilla: `results/arml_national_team_clean_50turn_vanilla_20260904/`

**Setup:** 11 years × 9–10 gradeable T-problems per year; one shared session per year; `max_turns=50`, `max_api_calls=151`; answer keys removed from prompts.

### 1.1 Summary

| Variant | N | Acc | Score/Max | Nonzero | CS | mean API | mean tok | mean turns | mean wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **OTC** | 11 | **22.3%** | 122.8 / 550 | **11/11** | 2.77 | 141.7 | 31,834 | 46.9 | 671 |
| **Vanilla** | 11 | **0.0%** | 0 / 550 | 0/11 | 3.23 | 150.0 | 8,155 | 50.0 | 289 |

### 1.2 Vs original gold-suite National row

| | Original OTC | Clean OTC | Original Vanilla | Clean Vanilla |
|---|---:|---:|---:|---:|
| Acc | 15.7% | **22.3%** | **20.0%** | 0.0% |
| Nonzero | 5/11 | **11/11** | 4/11 | 0/11 |
| mean turns | 4.0 | 46.9 | 3.4 | 50.0 |
| mean API | 13 | 142 | 9.3 | 150 |

Original Vanilla “wins” were contaminated: prompts included `Team Answers`, and the year was a single unsplit packet. After stripping answers and splitting into T-problems, Vanilla never produced a graded nonzero sheet; OTC consistently gets partial credit (often via deadline submit).

### 1.3 Per-year ledger

| Year | OTC Acc | OTC score | Van Acc | OTC deadline | OTC wall (s) | Van wall (s) |
|---|---:|---:|---:|---|---:|---:|
| 2009 | 40.0% | 20/50 | 0% | no | 396 | 276 |
| 2010 | 10.0% | 5/50 | 0% | yes | 545 | 261 |
| 2011 | 10.0% | 5/50 | 0% | yes | 475 | 268 |
| 2012 | 10.0% | 5/50 | 0% | no | 2042 | 324 |
| 2013 | 40.0% | 20/50 | 0% | yes | 450 | 324 |
| 2014 | 10.0% | 5/50 | 0% | yes | 577 | 322 |
| 2016 | 33.3% | 16.7/50 | 0% | yes | 465 | 305 |
| 2017 | 20.0% | 10/50 | 0% | yes | 692 | 265 |
| 2018 | 22.2% | 11.1/50 | 0% | yes | 541 | 274 |
| 2019 | 20.0% | 10/50 | 0% | yes | 556 | 288 |
| 2023 | 30.0% | 15/50 | 0% | yes | 640 | 273 |

**Read:** OTC is the only system scoring after the leakage fix. Most OTC sessions still need the deadline fallback (`deadline_submission=True` on 9/11 years). Vanilla burns the full 50 turns without a valid nonzero sheet under the whole-packet submit protocol.

---

## 2. Low-accuracy OTC rerun (task routing + 50 turns)

**Target competitions (original gold OTC Acc ≤ 8%):** Mystery Hunt, History Olympiad, Purple Comet, HMMT Guts, WMTC.

**Artifact:** `results/otc_task_routing_low_accuracy_20260904/`  
**Variant:** `strategic_team` only (no Vanilla paired rerun yet)  
**Budget:** 50 turns / 151 API (resume after interrupt; first ~49 Mystery Hunt sessions may still reflect the older shorter budget)

### 2.1 Final results (2026-09-05) — **374/374 complete**

| Competition | N | Acc | Nonzero | mean CS | mean API | mean turns | mean wall (s) | deadline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `mystery_hunt` | 261 | **0.4%** | 1/261 | 2.49 | 92.0 | 30.6 | 182 | 138/261 |
| `history_olympiad` | 95 | **64.4%** | **94/95** | 3.23 | 27.7 | 9.4 | 67 | 6/95 |
| `purple_comet` | 14 | **9.2%** | **11/14** | 2.61 | 103.8 | 34.5 | 215 | 9/14 |
| `hmmt_guts` | 1 | **2.8%** | **1/1** | 3.00 | 52.0 | 18.0 | 99 | 0/1 |
| `wmtc` | 3 | **16.7%** | **3/3** | 2.50 | 133.3 | 44.3 | 308 | 2/3 |
| **TOTAL** | **374** | — | — | — | — | — | — | — |

Only nonzero Mystery Hunt: `mystery_hunt_00819` (answer leaked in prompt). History zero: `history_olympiad_bowl_bowl_round_1_hs`.

### 2.2 Vs original gold OTC

| Competition | Gold OTC Acc | Gold nz | Rerun Acc | Rerun nz |
|---|---:|---|---:|---|
| `mystery_hunt` | 0.4% | 1/261 | 0.4% | 1/261 |
| `history_olympiad` | 8.0% | 12/95 | **64.4%** | **94/95** |
| `purple_comet` | 0.0% | 0/14 | **9.2%** | **11/14** |
| `hmmt_guts` | 0.0% | 0/1 | **2.8%** | **1/1** |
| `wmtc` | 0.0% | 0/3 | **16.7%** | **3/3** |

**Read:** Task routing + deadline submit + 50 turns fixed the History / math sheet-fill collapse (History now beats original Vanilla 36%). Mystery Hunt is unchanged at ~0% — incomplete puzzle media / IRL prompts, not non-submission. Math Acc is still low in absolute terms but every packet is now nonzero.

### 2.3 Math packet ledger (rerun)

| Session | Acc | Score | turns | API | deadline |
|---|---:|---|---:|---:|---|
| `purple_comet_hs_2018` | 16.7% | 5/30 | 50 | 151 | yes |
| `purple_comet_hs_2019` | 3.3% | 1/30 | 7 | 19 | no |
| `purple_comet_hs_2020` | 3.3% | 1/30 | 8 | 23 | no |
| `purple_comet_hs_2021` | 13.3% | 4/30 | 50 | 151 | yes |
| `purple_comet_hs_2022` | 3.3% | 1/30 | 5 | 15 | no |
| `purple_comet_hs_2023` | 0.0% | 0/30 | 50 | 151 | yes |
| `purple_comet_hs_2024` | 13.3% | 4/30 | 50 | 151 | yes |
| `purple_comet_ms_2018` | 5.0% | 1/20 | 50 | 151 | yes |
| `purple_comet_ms_2019` | 0.0% | 0/20 | 7 | 19 | no |
| `purple_comet_ms_2020` | 30.0% | 6/20 | 50 | 151 | yes |
| `purple_comet_ms_2021` | 0.0% | 0/20 | 50 | 151 | yes |
| `purple_comet_ms_2022` | 20.0% | 4/20 | 50 | 151 | yes |
| `purple_comet_ms_2023` | 5.0% | 1/20 | 6 | 18 | no |
| `purple_comet_ms_2024` | 15.0% | 3/20 | 50 | 151 | yes |
| `hmmt_guts_2024` | 2.8% | 1/36 | 18 | 52 | no |
| `wmtc_2018_advanced` | 7.1% | 1/14 | 33 | 98 | no |
| `wmtc_2018_intermediate` | 14.3% | 2/14 | 50 | 151 | yes |
| `wmtc_2018_junior` | 28.6% | 4/14 | 50 | 151 | yes |

### 2.4 Why Mystery Hunt stays ~0%

Not a gold-JSON / grading bug. Answers are short official phrases with `match_mode=normalized`; the only exact win (`mystery_hunt_00819`) literally has `The answer is SNIFF` in the prompt.

| Prompt bucket (≈261) | Count | Issue |
|---|---:|---|
| Needs PDF / image / audio | ~51 | Text says “print this PDF” but media is absent |
| Physical / IRL / HQ pickup | ~59 | Floppy disks, cheese, appointments — agent cannot act |
| Text-only-ish | ~142 | Still hard MH extractions; many descriptions incomplete |
| Answer leaked in prompt | ~1–2 | Only reliable Acc source |

Submission styles on the rerun: many short wrong guesses (`EDAM` vs gold `DAME`) and long hypothesis drafts forced in by deadline submit. Treating MH Acc as a protocol signal requires filtering to text-solvable puzzles or attaching media transcripts first.

---

## 3. Updated OTC / Vanilla by-competition snapshot

OTC rows for `arml_national_team` + the five low-accuracy competitions use the clean / routing reruns. Untouched rows and all Vanilla rows remain original gold suite. TOTAL is session-weighted Acc with those OTC substitutions (token means for substituted rows left as gold-era estimates where the rerun summary has no token column).

### Open Table Coach

| Competition | Description | N | total_questions | Acc | CS | mean API | mean tok | mean turns | non-zero scores |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| arml_local | ARML local mathematics team rounds featuring multi-part problems completed collaboratively on one shared answer sheet. | 6 | 44 | 0.523 | 3.25 | 37 | 7078 | 12 | 6/6 |
| science_bowl | Fast-paced science toss-up and bonus questions covering biology, chemistry, physics, mathematics, earth science, and energy. | 140 | 140 | 0.55 | 3.54 | 13.46 | 1279 | 4.66 | 77/140 |
| arml_national_team | ARML National Team Round where teammates divide ten challenging mathematics problems and combine their answers. | 11 | 108 | **0.223** | 2.77 | 141.73 | 31834 | 46.91 | **11/11** |
| qanta | Quiz-bowl questions with progressively revealed clues requiring identification of a person, place, work, event, or concept. | 240 | 240 | 0.221 | 3.61 | 14.97 | 1254 | 5.09 | 53/240 |
| mystery_hunt | MIT Mystery Hunt-style puzzles requiring teams to discover hidden mechanisms and extract a final answer. | 261 | 261 | **0.004** | 2.49 | 92.0 | — | 30.6 | **1/261** |
| history_olympiad | History questions requiring concise identification of historical people, places, events, and concepts. | 95 | 5642 | **0.644** | 3.23 | 27.7 | — | 9.4 | **94/95** |
| purple_comet | A timed online team mathematics contest with short-answer problems for middle- and high-school divisions. | 14 | 350 | **0.092** | 2.61 | 103.8 | — | 34.5 | **11/14** |
| hmmt_guts | A fast HMMT team mathematics round where new problem sets are released throughout the contest. | 1 | 36 | **0.028** | 3.00 | 52.0 | — | 18.0 | **1/1** |
| wmtc | World Mathematics Team Championship rounds featuring challenging individual and collaborative mathematics problems. | 3 | 42 | **0.167** | 2.50 | 133.3 | — | 44.3 | **3/3** |
| **TOTAL** |  | **771** | **6863** | **0.259** | — | — | — | — | **257/771** |

### Vanilla

| Competition | Description | N | total_questions | Acc | CS | mean API | mean tok | mean turns | non-zero scores |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| arml_local | ARML local mathematics team rounds featuring multi-part problems completed collaboratively on one shared answer sheet. | 6 | 44 | 0 | 2.83 | 36 | 1761 | 12 | 0/6 |
| science_bowl | Fast-paced science toss-up and bonus questions covering biology, chemistry, physics, mathematics, earth science, and energy. | 140 | 140 | 0.479 | 1.5 | 2.59 | 131 | 1.25 | 67/140 |
| arml_national_team | ARML National Team Round where teammates divide ten challenging mathematics problems and combine their answers. | 11 | 108 | **0** | 3.23 | 150 | 8155 | 50 | **0/11** |
| qanta | Quiz-bowl questions with progressively revealed clues requiring identification of a person, place, work, event, or concept. | 240 | 240 | 0.225 | 1.18 | 2.16 | 58 | 1.05 | 54/240 |
| mystery_hunt | MIT Mystery Hunt-style puzzles requiring teams to discover hidden mechanisms and extract a final answer. | 261 | 261 | 0.008 | 2.02 | 16.81 | 1034 | 5.82 | 2/261 |
| history_olympiad | History questions requiring concise identification of historical people, places, events, and concepts. | 95 | 5642 | 0.36 | 2.09 | 5.39 | 720 | 2.2 | 58/95 |
| purple_comet | A timed online team mathematics contest with short-answer problems for middle- and high-school divisions. | 14 | 350 | 0.008 | 1.93 | 15.57 | 884 | 5.43 | 2/14 |
| hmmt_guts | A fast HMMT team mathematics round where new problem sets are released throughout the contest. | 1 | 36 | 0 | 1.5 | 4 | 1843 | 2 | 0/1 |
| wmtc | World Mathematics Team Championship rounds featuring challenging individual and collaborative mathematics problems. | 3 | 42 | 0 | 2 | 17.33 | 1668 | 6 | 0/3 |
| **TOTAL** |  | **771** | **6863** | **0.204** | **1.69** | **10.27** | **636** | **3.73** | **183/771** |

---

## 4. Conclusions

1. **Original National Vanilla lead was not trustworthy** — answer-key leakage + unsplit packet. Clean rerun: OTC 22.3% vs Vanilla 0%.
2. **Task routing + deadline submit fixed History / math sheet-fill** — History OTC 8% → **64.4%** (beats original Vanilla 36%); Purple/HMMT/WMTC all leave 0% for nonzero Acc.
3. **Mystery Hunt stays ~0.4%** — incomplete media/IRL puzzle text and hard extractions; not a gold-JSON grading bug (only win is answer-in-prompt `00819`).
4. Substituting National + low-acc OTC reruns lifts session-weighted OTC Acc from **18.7% → ~25.9%** (still no paired Vanilla under the new protocol for History/math).

## 5. Next (optional)

1. Paired Vanilla under the same 50-turn + routing setup for History / Purple / HMMT / WMTC.
2. Filter or enrich Mystery Hunt to text-solvable puzzles only before treating Acc as a protocol signal.
3. Full gold-suite re-run under the 50-turn default for untouched competitions (Local / Science Bowl / Qanta).

## Related docs

| Doc | Role |
|---|---|
| [contest-session-gold-suite-20260903.md](contest-session-gold-suite-20260903.md) | Original paired gold + corrected §3.1 |
| [otc-protocol-fixes-20260906.md](otc-protocol-fixes-20260906.md) | Later protocol hardening (Docker judge, vanilla deadline parity, …) |
| [weekly-summary-2026-08-26-to-09-01.md](weekly-summary-2026-08-26-to-09-01.md) | Earlier weekly narrative |
| [open-table-coach-batch-results.md](open-table-coach-batch-results.md) | Older OTC batch notes |
