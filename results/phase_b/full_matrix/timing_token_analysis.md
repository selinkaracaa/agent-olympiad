# Phase B timing & token analysis

Generated: 2026-08-28 20:45
Source: `results/phase_b/full_matrix/phase_b_matrix.json` (55 completed cells)

## Summary

| Metric | min | median | mean | max | total |
|---|---:|---:|---:|---:|---:|
| Output tokens (est.) | 28 | 9,121 | 23,043 | 257,229 | 1,267,363 |
| API calls | 1 | 29 | 44 | 129 | 2,405 |
| Turns used | 1 | 4 | 7 | 18 | 411 |
| Max turns (budget) | 4 | 12 | 12 | 18 | 656 |
| Tokens / API call | 28 | 214 | 834 | 7,270 | 45,878 |
| Chat chars saved | 0 | 5,297 | 17,937 | 158,223 | 986,559 |

**Run status:** process was stuck on cell 56/80 (HMMT Guts · Claude · decentralized).
Completed: 55/80 cells. Contests done: ARML Local, ARML National, Purple Comet; HMMT 7/16; ICPC 0/16.

## By schema

| Schema | n | med tokens | med API | med turns | med tok/call |
|---|---:|---:|---:|---:|---:|
| single_agent | 14 | 586 | 2 | 1 | 145 |
| centralized | 14 | 18,846 | 57 | 12 | 215 |
| round_table | 14 | 9,819 | 30 | 5 | 250 |
| decentralized | 13 | 5,955 | 25 | 5 | 320 |

## By contest

| Contest | n | med tokens | med API | med turns | max tokens |
|---|---:|---:|---:|---:|---:|
| arml_local | 16 | 5,034 | 22 | 4 | 44,848 |
| arml_national_team | 16 | 1,728 | 4 | 1 | 22,069 |
| hmmt_guts | 7 | 21,810 | 103 | 13 | 132,215 |
| purple_comet | 16 | 21,301 | 88 | 18 | 257,229 |

## Top token outliers

| Tokens | API | Turns | Contest | Schema | Submitted |
|---:|---:|---:|---|---|:---:|
| 257,229 | 87 | 18/18 | purple_comet | centralized | True |
| 132,215 | 24 | 3/16 | hmmt_guts | round_table | True |
| 110,362 | 107 | 16/16 | hmmt_guts | centralized | True |
| 96,077 | 103 | 18/18 | purple_comet | decentralized | True |
| 76,615 | 103 | 18/18 | purple_comet | round_table | True |
| 59,109 | 87 | 18/18 | purple_comet | centralized | True |
| 49,012 | 109 | 18/18 | purple_comet | decentralized | True |
| 44,848 | 57 | 12/12 | arml_local | centralized | True |

## API reliability (from log)

- Failures logged: **6**
- Read timeouts (180s): **3**
- DNS / resolve errors: **3**
- Completed cells in log (`ok` lines): **42**
- Total `thinking...` lines (≈ agent API calls started): **2531**

## Diagnosis

1. **High agent demand (main factor):** Multi-agent schemas run many *sequential* API calls per cell. Centralized median **57 calls**; HMMT cells reach **107–129 calls** (8 agents × up to 16 turns + synthesis).
2. **Large outputs (second factor):** No `max_total_tokens` on math contests. One Purple Comet centralized cell hit **257k** estimated output tokens — likely long tool/code rambling, not useful chat.
3. **API issues (third factor):** Timeouts and DNS failures during Purple Comet; can waste hours per failed cell.
4. **Post-run judging:** CS + IHS add extra LLM calls per completed cell (not in `api_calls` above).
5. **Rough wall time:** ~55 cells in ~47h → **~51 min/cell** → full 80-cell matrix ≈ **68h** on one machine (vs 8h target).

## Recommendations for Friday

| Lever | Action |
|---|---|
| Cap rambling | Set `max_output_tokens_per_call` (e.g. 4k) + `max_total_tokens` per contest |
| Faster eval | **Mini benchmark**: subset of contests or 1 schema + solo baseline |
| Parallelism | Run teams/schemas on separate machines |
| Resume | Kill stuck process; `--resume` skips finished cells |
| Instrumentation | New runs include `tokens_by_turn` for per-turn breakdown |
