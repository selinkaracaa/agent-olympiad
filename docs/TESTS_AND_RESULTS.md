# Tests and results

Summary of what we ran to verify the Agent Olympiad pipeline (budgets, collaboration schemas, evaluation). Dates are UTC unless noted.

---

## 1. Unit tests

```bash
python3 -m unittest discover -s tests -v
```

| Suite | What it covers | Result (2026-08-12) |
|---|---|---|
| `tests/test_contest_budget.py` | 50-turn default, ICPC 4K output cap, truncations, API/token stop | **6/6 pass** |
| `tests/test_unified_evaluation.py` | PDF ingest, gold multipart match, registry, rubric scale, mock document judge | **8/8 pass** |
| `tests/test_artifact_evaluation.py` | Slide HTML contract, PDF aspect ratio, evaluation schema | **3/4 pass** |

**Known failure:** `test_html_normalizes_to_two_page_pdf` — local HTML→PDF renderer timed out (`RuntimeError: renderer timed out without a PDF`). Not a collaboration/budget bug; Playwright/Chromium path on this machine.

---

## 2. Offline smoke — all competitions (mock LLM)

```bash
python3 src/run_smoke_batch.py --rounds 1
```

**Run:** `results/smoke_batch/20260810-094125/smoke_batch.json`  
**Config:** mock model · round_table · 1 turn  
**Result:** **12/12 ok**, all submitted

Fixes applied before this green run:
- `iol_team_2003` missing `problem_description` → env falls back to `topic`
- `jessup` `team_size: "2-5"` → env uses upper bound (5)

| Competition | Problem | Env grade path |
|---|---|---|
| `arml_local` | `arml_local_2009` | `gold_substring_match` |
| `arml_national_team` | `arml_national_team_2009` | `gold_substring_match` |
| `arml_national_power` | `arml_national_power_2009` | `gold_substring_match`* |
| `arml_power` | `arml_power_fall_2018` | `gold_substring_match`* |
| `icpc` | `icpc_wf_2012_bottles` | `judge_sandbox_required` (expected) |
| `iiot` | `iiot_2017_01` | `judge_sandbox_required` (expected) |
| `ieo_business_case` | `ieo_business_case_2021` | `llm_judge_required` (expected) |
| `iol_team` | `iol_team_2003` | `llm_judge_required` (expected) |
| `ioaa_group` | `ioaa_group_2025` | `gold_substring_match`* |
| `ijso_practical` | `…2004…` | `llm_judge_required` (expected) |
| `wsc_writing` | `wsc_writing_gq_001` | `llm_judge_required` (expected) |
| `jessup` | `jessup_2024` | `llm_judge_required` (expected) |

\*Mock answers are ARML-shaped; env gold path may fire even when the official evaluator is `rubric_llm_v1`. This run checks **pipeline stability**, not score quality.

---

## 3. Live smoke — all competitions (Perplexity)

```bash
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_smoke_batch.py --live --rounds 1
python3 src/run_smoke_batch.py --live --rounds 2 --schema round_table
```

**Model:** `openai/gpt-5.4-mini` via Perplexity Agent API  
**Schema:** round_table  

| Run | Artifact | Rounds | Result |
|---|---|---|---|
| Live ×1 | `results/smoke_batch/20260812-182401/smoke_batch.json` | 1 | **12/12 ok**, 12 submitted |
| Live ×2 | `results/smoke_batch/20260812-182846/smoke_batch.json` | 2 | **12/12 ok**, 12 submitted |

### Live ×2 detail (pipeline + env grade)

| Competition | Turns | API calls | Est. tokens | Submitted | Env grade |
|---|---:|---:|---:|---|---|
| `arml_local` | 2 | 13 | 3100 | yes | gold substring |
| `arml_national_team` | 2 | 16 | 725 | yes | gold substring |
| `arml_national_power` | 2 | 31 | 2203 | yes | gold substring* |
| `arml_power` | 2 | 29 | 10326 | yes | gold substring* |
| `icpc` | 2 | 6 | 794 | yes | sandbox required |
| `iiot` | 2 | 9 | 2609 | yes | sandbox required |
| `ieo_business_case` | 2 | 11 | 3546 | yes | LLM judge required |
| `iol_team` | 2 | 9 | 738 | yes | LLM judge required |
| `ioaa_group` | 2 | 11 | 1789 | yes | gold substring* |
| `ijso_practical` | 2 | 7 | 347 | yes | LLM judge required |
| `wsc_writing` | 2 | 4 | 1911 | yes | LLM judge required |
| `jessup` | 2 | 12 | 3247 | yes | LLM judge required |

**Notes from live answers**
- ARML / national-team style sheets produced numbered answer sheets.
- `iol_team_2003` and `ijso_practical_2004` often returned “insufficient information” — problem text/media in the benchmark packet is thin for those IDs; pipeline still completed.
- ICPC/IIOT submitted reasoning/code outlines but **cannot be auto-scored** until a programming judge exists.

---

## 4. ARML Local 2009 — three-schema baseline (live + LLM judge)

```bash
python3 src/run_exam.py --all-schemas --rounds 2
```

**Batch stamp:** `20260812-183636`  
**Agents:** `openai/gpt-5.4-mini`  
**Judge:** `anthropic/claude-sonnet-4-6` (via Perplexity)  
**Problem:** `arml_local_2009` · team size 6 · 2 turns  

| Schema | Parts | Turns | API calls | Est. tokens | LLM judge |
|---|---:|---:|---:|---:|---|
| round_table | 10 | 2 | 12 | 2474 | **4/40** |
| centralized | 10 | 2 | 7 | 2278 | **14/40** |
| decentralized | 10 | 2 | 13 | 2983 | **12/40** |

Artifacts:
- `results/arml_local_2009_round_table_20260812-183636.json`
- `results/arml_local_2009_centralized_20260812-183636.json`
- `results/arml_local_2009_decentralized_20260812-183636.json`

**Takeaway:** With a small model and only 2 turns, centralized scored highest; all three schemas finished without crashes and produced full 10-part sheets. This is a **smoke baseline**, not a paper-ready table (need more turns, calibrated budgets, more problems).

---

## 5. Evaluation-path smokes (earlier)

### Gold answer grader (offline)

```bash
python3 src/evaluate_submission.py \
  --benchmark data/benchmarks/arml_local/benchmark.json \
  --problem-id arml_local_2009 \
  --submission-text /tmp/arml_2009_answers.txt \
  --media text
```

Perfect curated sheet → **40/40** on gradeable short answers  
Saved: `results/evaluations/gold_answer_v1_20260730-221142/evaluation.json`

### Multimodal PDF → images → Perplexity

```bash
python3 src/smoke_multimodal.py data/raw/business_case/2024.pdf --pages 1-2
```

Succeeded after JPEG downscale (large PNGs caused SSL EOF).  
Saved: `results/smoke_multimodal/20260730-225235/smoke.json`  
Model correctly identified IEO 2024 Hong Kong housing business case from page images.

---

## 6. Budget model under test

| Budget | Role | Default in these runs |
|---|---|---|
| Turns | Contest clock; ≤1 LLM call per agent per turn (or `sleep`) | smoke: 1–2; registry default: **50** |
| API calls | Cost cap across discussion + synthesis | unlimited |
| Output tokens / call | Cap one agent reply | unlimited (ICPC/IIOT registry placeholder **4096**) |
| Total tokens | Team-wide output cap | unlimited |

Registry: `src/contest_budget.py`.

---

## 7. What “ok” means vs what is still missing

**Pipeline OK (done for these smokes)**
- Load every collected competition
- Run round_table (and, for ARML, all 3 schemas)
- Respect turn budget
- Submit a final answer without crashing

**Not yet paper-complete**
- Programming sandbox / online judge for ICPC & IIOT
- Full rubric / slide LLM scoring wired into the smoke batch (env only flags `llm_judge_required`)
- Per-competition turn calibration (still default 50)
- Token / API pressure turned on for real experiments
- More turns + more models + more samples for the final table
- Fix HTML→PDF unit test timeout on this machine
- Richer problem packets for thin benchmarks (e.g. IOL 2003 text)

---

## 8. How to reproduce

```bash
# Unit tests
python3 -m unittest discover -s tests -v

# Offline pipeline matrix
python3 src/run_smoke_batch.py --rounds 1

# Live pipeline matrix
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_smoke_batch.py --live --rounds 2 --schema round_table

# ARML three-schema baseline + LLM judge
python3 src/run_exam.py --all-schemas --rounds 2
```

---

## One-liner

Offline and live smoke: **12/12 competitions** complete under turn budgets; ARML Local 2009 three-schema live baseline scored **4 / 14 / 12 out of 40** (round_table / centralized / decentralized) with GPT-5.4-mini at 2 turns. Programming judges and full rubric scoring of the smoke matrix are still open.
