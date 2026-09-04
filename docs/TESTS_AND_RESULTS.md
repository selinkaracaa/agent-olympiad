# Tests and results

Status of the Agent Olympiad pipeline: budgets, collaboration schemas, evaluation, and smoke runs.

This is **not** a paper table yet. Pipeline smokes now include **registered judges** on live runs (gold substring, rubric LLM, or slide text proxy). ICPC/IIOT programming judges remain deferred. The ARML Local three-schema run remains the multi-baseline scored pilot.

---

## Big picture

Multi-agent AI teams take olympiad-style **team contests**. Three layers:

1. **Environment** (`env.py`) — contest room: problem text, tools, shared chat/scratchpad, budgets (time / API / tokens).
2. **Collaboration** (`collaboration.py`) — how teammates talk (round table / centralized / decentralized).
3. **Evaluation** — how the final answer is scored (gold, LLM rubric, slide judge, or programming judge later).

**Current coverage:** all **20** competition families in `docs/DATA_COLLECTION.md` have `data/benchmarks/*/benchmark.json` (**525** problems/years total). Offline and live smoke across all 20 are green; live judged smoke scores **18/20** contests (2 programming deferred).

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

`llm_judge_required` on a smoke row means either judge was off (`--no-judge` / mock) or that problem still has no runnable registered judge (e.g. programming sandbox). Live smoke defaults to `--judge`: after submit it runs `rubric_llm_v1` / text proxy for `slide_deck_v1` via `evaluation.finalize.apply_registered_judge`.

**Coordination / collaboration score (MultiAgentBench):** live competition batches also report `CS = mean(Communication, Planning)` on a 0–5 scale (`src/evaluation/collaboration_score.py`, arXiv:2503.01935). Independent of task accuracy.

**Contest rules audit:** `python3 src/contest_rules.py --report` — 20 families mapped; env encodes tools/search policy/wrong-submit counters; gaps remain for shared-computer locks, guts batches, staged WSC, orals, ICPC secret tests.

**Reality upgrades (2026-08-21):** duration→turn budgets; live DuckDuckGo search; ICPC Kattis **sample** judge (WA burns 20 min remaining clock); gold shorts on ARML Local, ARML National Team, Purple Comet HS/MS 2018–2024, HMMT Guts 2024.

## Phase B matrix (multi-model + CS, registry budgets)

```bash
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_phase_b_matrix.py --live
# resume if interrupted:
python3 src/run_phase_b_matrix.py --live --resume results/phase_b/<ts>/phase_b_matrix.json
```

- 5 gold contests × 4 schemas × 4 teams (gpt / claude / gemini / hetero) = **80 cells**
- Turns = contest duration registry (ARML Local 12, National 4, Purple 18, HMMT Guts 16, ICPC 60)
- Scores: task grade + MultiAgentBench **CS** (`--judge-collab` on by default)
- Artifacts under `results/phase_b/<timestamp>/phase_b_matrix.json` (saved after each cell)

---

```bash
python3 src/run_phase_a.py --live --max-turns 8
```

- Model: `openai/gpt-5.4-mini` · 8 turns · artifact `results/phase_a/20260821-155239/phase_a.json`
- Rescored (no re-run): `phase_a_rescored.json` after gold parser v2 (`T-1`, semicolon sheets, √→sqrt)
- Result: **20/20 ok** (5 contests × single_agent / centralized / round_table / decentralized)

| Contest | single | centralized | round_table | decentralized |
|---|---:|---:|---:|---:|
| ARML Local /40 | 8.9 | **22.2** | **31.1** | 17.8 |
| ARML National Team /50 | **37.5** | 37.5 | **43.8** | **43.8** |
| Purple Comet HS /30 | 5 | **6** | 4 | 4 |
| HMMT Guts /50 | **5.6** | 4.2 | 4.2 | 2.8 |
| ICPC bottles (sample) | 0 | 0 | 0 | 0 |

Note: prior zeros on National Team were mostly **answer-format parse misses** (`T-1 …` / `a; b; c`), not wrong math. Solo often still submitted early (1–2 turns). ICPC sample AC unmet at 8 turns.

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

## 3. Live smoke — all 20 contests with judges (current)

```bash
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_smoke_batch.py --live --rounds 1 --schema round_table
# judge defaults on for --live; use --no-judge for pipeline-only
```

- Model: `openai/gpt-5.4-mini` · round_table · 1 turn · **judge=on**
- Artifact: `results/smoke_batch/20260812-193418/smoke_batch.json`
- Result: **20/20 ok**, **20** submitted, **18** graded (ICPC/IIOT still sandbox-deferred)

| Competition | Problem | Turns | API | Tokens | Grade | Score |
|---|---|---:|---:|---:|---|---|
| `arml_local` | `arml_local_2009` | 1 | 7 | 845 | gold_substring_match | 0/1 |
| `arml_national_team` | `arml_national_team_2009` | 1 | 5 | 238 | gold_substring_match | 0/1 |
| `arml_national_power` | `arml_national_power_2009` | 1 | 16 | 2492 | gold_substring_match | 0/1 |
| `arml_power` | `arml_power_fall_2018` | 1 | 16 | 4362 | gold_substring_match | 0/1 |
| `icpc` | `icpc_wf_2012_bottles` | 1 | 4 | 751 | judge_sandbox_required | — |
| `iiot` | `iiot_2017_01` | 1 | 5 | 1000 | judge_sandbox_required | — |
| `ieo_business_case` | `ieo_business_case_2021` | 1 | 6 | 2070 | slide_deck_v1 | 29.5/50 |
| `iol_team` | `iol_team_2003` | 1 | 5 | 591 | rubric_llm_v1 | 0/100 |
| `ioaa_group` | `ioaa_group_2025` | 1 | 6 | 1027 | gold_substring_match | 0/1 |
| `ijso_practical` | `ijso_practical_2004_team_practical_2004` | 1 | 4 | 296 | rubric_llm_v1 | 0/40 |
| `wsc_writing` | `wsc_writing_gq_001` | 1 | 4 | 2882 | rubric_llm_v1 | 24/28 |
| `jessup` | `jessup_2024` | 1 | 7 | 2125 | rubric_llm_v1 | 25/100 |
| `iypt` | `iypt_2024` | 1 | 6 | 1920 | rubric_llm_v1 | 59/100 |
| `hmmt_team` | `hmmt_team_2024` | 1 | 9 | 1508 | rubric_llm_v1 | 0/100 |
| `hmmt_guts` | `hmmt_guts_2024` | 1 | 9 | 1050 | rubric_llm_v1 | 26/100 |
| `mcm` | `mcm_2024_A` | 1 | 4 | 2006 | rubric_llm_v1 | 63/100 |
| `icm` | `icm_2024_D` | 1 | 4 | 1195 | rubric_llm_v1 | 24/100 |
| `fyziklani` | `fyziklani_2024` | 1 | 6 | 268 | rubric_llm_v1 | 40/100 |
| `purple_comet` | `purple_comet_hs_2024` | 1 | 7 | 1000 | rubric_llm_v1 | 0/30 |
| `itym` | `itym_2024` | 1 | 8 | 1914 | rubric_llm_v1 | 18/100 |

One-turn mini-model scores (not paper-scale). Gold rows are env substring 0/1 checks; open-ended rows use the registered rubric LLM. IEO uses a text proxy for `slide_deck_v1` (full HTML/PDF slide checks still via `evaluate_submission.py`).

### Prior live smoke (pipeline only, no in-batch judge)

Artifact: `results/smoke_batch/20260812-191248/smoke_batch.json` — **20/20 ok**, grades were mostly `llm_judge_required` before `apply_registered_judge` was wired.

### Earlier live wave (first 12 families, 2 turns)

Before the last eight benchmarks were added: **12/12 ok** at 2 turns  
Artifacts: `results/smoke_batch/20260812-182401/`, `…/20260812-182846/`

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

**Done:** dual media; gold/rubric/slide evaluators wired into live smoke; turn/API/token parameters; three schemas; **20 contest benchmarks**; offline **20/20**; live judged **20/20** ok / **18** scored (1 turn, mini); ARML three-schema pilot.

**Next:** more turns + pressure; full slide PDF path in-batch; ICPC/IIOT judge; scale to paper table.

---

## 8. Reproduce

```bash
python3 -m unittest discover -s tests -v
python3 src/run_smoke_batch.py --rounds 1                    # offline 20
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_smoke_batch.py --live --rounds 2             # live 20
python3 src/run_exam.py --all-schemas --rounds 2             # ARML scored
```
