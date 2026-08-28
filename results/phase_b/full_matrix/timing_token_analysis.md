# Phase B timing & token analysis

Generated: 2026-08-28 22:26
Source: `results/phase_b/full_matrix/phase_b_matrix.json` (55 completed cells)

## Summary

| Metric | min | median | mean | max | total |
|---|---:|---:|---:|---:|---:|
| Output tokens (est.) | 28 | 9,121 | 23,043 | 257,229 | 1,267,363 |
| API calls | 1 | 29 | 44 | 129 | 2,405 |
| Turns used | 1 | 4 | 7 | 18 | 411 |
| Max turns (budget) | 4 | 12 | 12 | 18 | 656 |
| Tokens / API call | 28 | 214 | 834 | 7,270 | 45,878 |

**Run status:** 55/80 cells complete (ARML Local, ARML National, Purple Comet done; HMMT 7/16; ICPC 0/16).

**Token note:** estimated from visible output text (`chars÷4`); excludes prompt tokens and hidden reasoning unless returned in output.

## By model team

| Group | n | med tokens | med API | med turns | med tok/call | max tokens |
|---|---:|---:|---:|---:|---:|---:|
| gpt | 16 | 5,580 | 40 | 6 | 133 | 22,385 |
| claude | 15 | 35,700 | 29 | 4 | 933 | 257,229 |
| gemini | 12 | 2,718 | 26 | 3 | 176 | 22,014 |
| hetero | 12 | 9,474 | 22 | 4 | 342 | 59,109 |

## By model label

| Group | n | med tokens | med API | med turns | med tok/call | max tokens |
|---|---:|---:|---:|---:|---:|---:|
| openai/gpt-5.4-mini | 16 | 5,580 | 40 | 6 | 133 | 22,385 |
| anthropic/claude-sonnet-4-6 | 15 | 35,700 | 29 | 4 | 933 | 257,229 |
| google/gemini-3.5-flash | 12 | 2,718 | 26 | 3 | 176 | 22,014 |
| hetero:gpt,claude,gemini | 12 | 9,474 | 22 | 4 | 342 | 59,109 |

## By schema

| Group | n | med tokens | med API | med turns | med tok/call | max tokens |
|---|---:|---:|---:|---:|---:|---:|
| single_agent | 14 | 586 | 2 | 1 | 145 | 35,700 |
| centralized | 14 | 18,846 | 57 | 12 | 215 | 257,229 |
| round_table | 14 | 9,819 | 30 | 5 | 250 | 132,215 |
| decentralized | 13 | 5,955 | 25 | 5 | 320 | 96,077 |

## By contest

| Group | n | med tokens | med API | med turns | med tok/call | max tokens |
|---|---:|---:|---:|---:|---:|---:|
| arml_local | 16 | 5,034 | 22 | 4 | 331 | 44,848 |
| arml_national_team | 16 | 1,728 | 4 | 1 | 150 | 22,069 |
| purple_comet | 16 | 21,301 | 88 | 18 | 258 | 257,229 |
| hmmt_guts | 7 | 21,810 | 103 | 13 | 183 | 132,215 |

## Top token outliers

| Tokens | API | Turns | Contest | Team | Schema |
|---:|---:|---:|---|---|---|
| 257,229 | 87 | 18/18 | purple_comet | claude | centralized |
| 132,215 | 24 | 3/16 | hmmt_guts | claude | round_table |
| 110,362 | 107 | 16/16 | hmmt_guts | claude | centralized |
| 96,077 | 103 | 18/18 | purple_comet | claude | decentralized |
| 76,615 | 103 | 18/18 | purple_comet | claude | round_table |
| 59,109 | 87 | 18/18 | purple_comet | hetero | centralized |
| 49,012 | 109 | 18/18 | purple_comet | hetero | decentralized |
| 44,848 | 57 | 12/12 | arml_local | claude | centralized |

## API reliability (from log)

- Failures logged: **28** (timeouts **3**, DNS **3**)

## Diagnosis

1. **High agent demand:** centralized median **57 API calls**; HMMT up to **129**.
2. **Large outputs:** max **257k** tokens (Purple Comet · Gemini · centralized).
3. **By model:** Gemini and hetero cells tend toward higher token use on long contests (Purple Comet / HMMT); GPT solo cells stay low.
4. **Wall time:** ~**51 min/cell** → full 80-cell matrix ≈ **68h** on one machine.
