# Tests and results

Status of the Agent Olympiad pipeline: budgets, collaboration schemas, evaluation, and smoke runs.

This is **not** a paper table yet. Most runs are **pipeline smokes** (“does it finish without crashing?”). Only the ARML Local three-schema run has a full LLM **score**.

---

## Big picture

Multi-agent AI teams take olympiad-style **team contests**. Three layers:

1. **Environment** (`env.py`) — contest room: problem text, tools, shared chat/scratchpad, budgets (time / API / tokens).
2. **Collaboration** (`collaboration.py`) — how teammates talk (round table / centralized / decentralized).
3. **Evaluation** — how the final answer is scored (gold, LLM rubric, slide judge, or programming judge later).

**Current coverage:** all **20** competition families in `docs/DATA_COLLECTION.md` have `data/benchmarks/*/benchmark.json` (**525** problems/years total). Offline smoke across all 20 is green.

---

## Vocabulary

| Term | Meaning |
|---|---|
| **Competition / contest** | One olympiad type (ARML Local, ICPC, Jessup, …). |
| **Problem / year** | One concrete packet, e.g. ARML Local 2009. |
| **Agent** | One LLM teammate. Team size follows contest rules. |
| **Turn** | One step of the **contest clock**. Each eligible agent ≤ **one** model call per turn, or **sleep**. |
| **API call** | One model request (cost). Separate from turns. |
| **Token** | Text chunk; long answers cost more. |
| **Schema / baseline** | Round table, centralized, or decentralized. |
| **Smoke test** | End-to-end pipeline check — not a quality score. |
| **Gold answer** | Short official finals for automatic matching. |
| **LLM judge / rubric** | Model scores open-ended work against a rubric. |
| **Submitted** | Team called `submit_final`. |
| **Pipeline OK** | Load → act → submit → no crash. |

---

## How a single run works

Example: ARML Local 2009, round table, 2 turns, 6 agents.

1. Load `data/benchmarks/arml_local/benchmark.json` → `arml_local_2009`.
2. Create `OlympiadEnvironment` (team 6, paper-only tools, max turns = 2).
3. **Turn 1:** each agent gets one LLM call (or sleeps), in order.
4. **Turn 2:** same.
5. **Synthesis:** one agent writes the numbered sheet and submits.
6. **Grading:** env gold check and/or LLM judge (`run_exam.py`).

- `run_smoke_batch.py` — one sample per contest; stability.
- `run_exam.py` — deeper run + LLM judge scores.

---

## Budgets

| Budget | Role | Default |
|---|---|---|
| **Turns** | Contest clock | **50** (placeholder; smokes use 1–2) |
| **API calls** | Cost across discussion + synthesis | unlimited in smokes |
| **Output tokens / call** | Cap one reply | unlimited (ICPC/IIOT placeholder **4096**) |
| **Total tokens** | Team-wide output cap | unlimited |

Registry: `src/contest_budget.py`.

Rule: ≤1 LLM call per agent per turn, or `ACTION: sleep`.

---

## Collaboration baselines

| Schema | Behavior |
|---|---|
| **Round table** | Full history; agents speak in order each turn |
| **Centralized** | Leader plans; workers act; leader submits |
| **Decentralized** | No leader; peers use chat/scratchpad |

---

## Evaluation paths

| Situation | Label | Meaning |
|---|---|---|
| Curated short math | `gold_answer_v1` | Auto match |
| Writing / proofs / memorials / reports | `rubric_llm_v1` | Need LLM/human rubric |
| Business-case slides | `slide_deck_v1` | Slide pipeline |
| ICPC / IIOT | `programming_judge` | Deferred (sandbox) |

`llm_judge_required` on a smoke = agent loop finished; rubric judge was not called inside the smoke batch.

---

# Test results

## 1. Unit tests

```bash
python3 -m unittest discover -s tests -v
```

| Suite | Covers | Result (2026-08-12) |
|---|---|---|
| `tests/test_contest_budget.py` | Budgets, truncation | **6/6 pass** |
| `tests/test_unified_evaluation.py` | PDF ingest, gold, registry, rubric | **8/8 pass** |
| `tests/test_artifact_evaluation.py` | Slide HTML/PDF rules | **3/4 pass** |

**Known fail:** HTML→PDF renderer timeout on this machine (Playwright). Not a collaboration/budget bug.

---

## 2. Offline smoke — all 20 contests (current)

```bash
python3 src/run_smoke_batch.py --rounds 1
```

- Mock LLM · round_table · 1 turn · **one problem per family**
- Artifact: `results/smoke_batch/20260812-185837/smoke_batch.json`
- Result: **20/20 ok**, all submitted

`src/run_smoke_batch.py` lists all 20 DATA_COLLECTION families.

| Competition | Problem | Env grade |
|---|---|---|
| `arml_local` | `arml_local_2009` | gold_substring_match |
| `arml_national_team` | `arml_national_team_2009` | gold_substring_match |
| `arml_national_power` | `arml_national_power_2009` | gold_substring_match |
| `arml_power` | `arml_power_fall_2018` | gold_substring_match |
| `icpc` | `icpc_wf_2012_bottles` | judge_sandbox_required |
| `iiot` | `iiot_2017_01` | judge_sandbox_required |
| `ieo_business_case` | `ieo_business_case_2021` | llm_judge_required |
| `iol_team` | `iol_team_2003` | llm_judge_required |
| `ioaa_group` | `ioaa_group_2025` | gold_substring_match |
| `ijso_practical` | `ijso_practical_2004_team_practical_2004` | llm_judge_required |
| `wsc_writing` | `wsc_writing_gq_001` | llm_judge_required |
| `jessup` | `jessup_2024` | llm_judge_required |
| `iypt` | `iypt_2024` | llm_judge_required |
| `hmmt_team` | `hmmt_team_2024` | llm_judge_required |
| `hmmt_guts` | `hmmt_guts_2024` | llm_judge_required |
| `mcm` | `mcm_2024_A` | llm_judge_required |
| `icm` | `icm_2024_D` | llm_judge_required |
| `fyziklani` | `fyziklani_2024` | llm_judge_required |
| `purple_comet` | `purple_comet_hs_2024` | llm_judge_required |
| `itym` | `itym_2024` | llm_judge_required |

\*Mock answers can trigger `gold_substring_match` even when the official evaluator is a rubric. Offline smoke = **stability**, not score truth.

Fixes applied earlier: IOL missing description → topic fallback; Jessup `team_size: "2-5"` → upper bound 5.

---

## 3. Live smoke — first 12 families (earlier wave)

Before the last eight benchmarks were added, live smokes covered the original 12 families:

```bash
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_smoke_batch.py --live --rounds 2 --schema round_table
```

- Model: `openai/gpt-5.4-mini`
- Results: **12/12 ok** (1-turn and 2-turn)
- Artifacts: `results/smoke_batch/20260812-182401/`, `…/20260812-182846/`

| Competition | Turns | API | Tokens | Env grade |
|---|---:|---:|---:|---|
| ARML Local | 2 | 13 | 3100 | gold substring |
| ARML National Team | 2 | 16 | 725 | gold substring |
| ARML National Power | 2 | 31 | 2203 | gold substring* |
| ARML Power | 2 | 29 | 10326 | gold substring* |
| ICPC | 2 | 6 | 794 | sandbox required |
| IIOT | 2 | 9 | 2609 | sandbox required |
| IEO business case | 2 | 11 | 3546 | LLM judge required |
| IOL team | 2 | 9 | 738 | LLM judge required |
| IOAA group | 2 | 11 | 1789 | gold substring* |
| IJSO practical | 2 | 7 | 347 | LLM judge required |
| WSC writing | 2 | 4 | 1911 | LLM judge required |
| Jessup | 2 | 12 | 3247 | LLM judge required |

Live smoke for the **full 20** (including IYPT/HMMT/MCM/ICM/Fyziklání/Purple Comet/ITYM) is the next live pass: same command now iterates all 20 cases.

---

## 4. ARML Local 2009 — three-schema scored pilot

```bash
python3 src/run_exam.py --all-schemas --rounds 2
```

| Setting | Value |
|---|---|
| Problem | `arml_local_2009` (/40) |
| Team | 6 |
| Turns | 2 |
| Agents | `openai/gpt-5.4-mini` |
| Judge | `anthropic/claude-sonnet-4-6` |
| Batch | `20260812-183636` |

| Schema | Parts | API | Tokens | **Score** |
|---|---:|---:|---:|---|
| Round table | 10 | 12 | 2474 | **4/40** |
| Centralized | 10 | 7 | 2278 | **14/40** |
| Decentralized | 10 | 13 | 2983 | **12/40** |

Pilots under `results/arml_local_2009_*_20260812-183636.json`.

Pilot only: small model, 2 turns, diagram problem often unsolved from text.

---

## 5. Evaluation-only smokes

**Gold grader:** curated ARML Local 2009 sheet → **40/40** gradeable shorts  
`results/evaluations/gold_answer_v1_20260730-221142/evaluation.json`

**Multimodal:** PDF pages → JPEG → Perplexity correctly read IEO 2024 business-case cover  
`results/smoke_multimodal/20260730-225235/smoke.json`

---

## 6. What “20/20 ok” does not mean

| Misread | Correct |
|---|---|
| Solved all contests | **Ran** all contest families through the agent loop |
| Full scores for everything | Only ARML 2009 has LLM judge scores so far |
| ICPC is graded | ICPC submits; **judge deferred** |
| Labs fully scored | Written-report **proxy** only |
| 50 turns is final | Default **placeholder**; calibrate later |

---

## 7. Done vs next

**Done:** dual media; gold/rubric/slide evaluators; turn/API/token parameters; three schemas; **20 contest benchmarks**; offline **20/20** smoke; ARML three-schema pilot.

**Next:** live smoke on all 20; more turns + pressure; rubric judges in the matrix; ICPC/IIOT judge; scale to paper table; integrate additional contests as needed.

---

## 8. Reproduce

```bash
python3 -m unittest discover -s tests -v
python3 src/run_smoke_batch.py --rounds 1                    # offline 20
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_smoke_batch.py --live --rounds 2             # live 20
python3 src/run_exam.py --all-schemas --rounds 2             # ARML scored
```

---

## Meeting summary

All **20** DATA_COLLECTION contest families are benchmarked and offline-smoke green. Turns are the time clock (≤1 model call per agent per turn, or sleep); API and token caps are separate. Three collaboration baselines remain. ARML Local 2009 pilot scores: round table **4/40**, centralized **14/40**, decentralized **12/40** (GPT-5.4-mini, 2 turns). Next: live 20-way smoke, stronger budgets, programming judges, then scale.

---

## One-liner

**20/20 contest families pipeline-ok offline; ARML three-schema pilot 4 / 14 / 12 out of 40; programming judges and paper-scale runs still ahead.**
