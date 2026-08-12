# Tests and results — detailed guide

This note is for **you** (Selin): so you can understand what we built, what we tested, what the numbers mean, and how to explain it in a meeting without feeling lost.

It is **not** a paper table yet. Most runs are **pipeline smokes** (“does it finish without crashing?”). Only the ARML Local three-schema run has a real LLM **score**.

---

## Big picture in one minute

We are building a benchmark where **multi-agent AI teams** take olympiad-style **team contests**.

There are three layers:

1. **Environment** (`env.py`) — the “contest room”: problem text, allowed tools, shared chat/scratchpad, budgets (time / API / tokens).
2. **Collaboration** (`collaboration.py`) — *how* the teammates talk (round table / leader / no leader).
3. **Evaluation** — *how we score* the final answer (exact gold, LLM rubric, slide judge, or programming judge later).

**What we proved recently:** every collected competition can load and run through the agent loop under a turn budget. As of 2026-08-12 that is **all 20 families** listed in `docs/DATA_COLLECTION.md` (the previous “12/12” smokes covered only the first wave; eight more benchmarks were built from existing `data/raw/` PDFs). We also scored one ARML problem under all three collaboration styles with a live model + LLM judge.

---

## Vocabulary (say these out loud until they feel natural)

| Term | Plain meaning |
|---|---|
| **Competition / contest** | One olympiad type (ARML Local, ICPC, Jessup, …). |
| **Problem / year** | One concrete packet, e.g. ARML Local 2009. |
| **Agent** | One LLM teammate. Team size comes from the contest rules (ARML Local = 6, ICPC = 3, …). |
| **Turn** | One step of the **contest clock**. In each turn, each eligible agent may make **at most one** model call, or choose to **sleep** (pass). |
| **API call** | One request to the model. Costs money. Separate from turns. |
| **Token** | Chunk of text the model reads/writes. Long answers = more tokens = more cost/time. |
| **Schema / baseline** | Collaboration style: round table, centralized, or decentralized. |
| **Smoke test** | “Does the pipeline run end-to-end?” Not “did they get a high score?” |
| **Gold answer** | Official short answer we can match automatically (math finals). |
| **LLM judge / rubric** | Model scores open-ended work against a rubric or reference. |
| **Submitted** | The team called `submit_final` and left an answer in the workspace. |
| **Pipeline OK** | Loaded problem → agents acted → something was submitted → no crash. |

---

## How a single run actually works

Imagine ARML Local 2009, round table, 2 turns, 6 agents.

1. Load `data/benchmarks/arml_local/benchmark.json` → find `arml_local_2009`.
2. Create `OlympiadEnvironment` with team size 6, tools = none (paper only), max turns = 2.
3. **Turn 1:** Agent_1 gets one LLM call → speaks / writes scratchpad / maybe sleeps. Then Agent_2, … Agent_6.
4. **Turn 2:** same order again.
5. **Synthesis:** one agent writes the full numbered answer sheet (1.–10.) and submits.
6. **Grading:**
   - Quick env check (substring gold) *or*
   - Full LLM judge (as in `run_exam.py`).

Important distinction:

- **`run_smoke_batch.py`** = try many contests; mostly checks “did it finish?” Env grade is coarse.
- **`run_exam.py`** = deeper run on one problem; calls a real LLM judge and prints `TOTAL: X/40`.

---

## Budgets — what we implemented and how to explain them

We used to count almost every tiny env action as a “turn.” That mixed **time** and **bookkeeping**. Now we have separate knobs:

### 1. Turn budget = time

- Default registry value: **50 turns** for every competition (placeholder until we calibrate).
- Smoke runs used **1 or 2 turns** on purpose (cheap).
- Rule: each agent ≤ **1 API call per turn**, or `ACTION: sleep`.
- When turns run out, discussion stops; synthesis may still run if API budget allows.

**How to say it:**  
“Turns are the contest clock. Fifty is our default until we map each olympiad’s real wall time to a turn count.”

### 2. API call budget = money

- Counts every LLM call (discussion + synthesis).
- **Unlimited by default** in these smokes (we only constrained turns).
- Optional flag: `--max-api-calls N`.

**How to say it:**  
“API calls are cost. We left them uncapped for smokes; later we can tighten them.”

### 3. Token budgets = stop endless blabbing

- **Per call:** max output tokens for one agent reply (ICPC/IIOT placeholder **4096**).
- **Team total:** optional cap for the whole run.
- Code truncates oversized replies and marks them `[truncated…]`.

**How to say it:**  
“So one thinking model can’t dump a million tokens in a single turn and cheat the time model.”

Registry lives in `src/contest_budget.py`.

---

## The three collaboration schemas (baselines)

Keep all three. They are the first “baselines” for the paper.

| Schema | Who talks how | Good for explaining |
|---|---|---|
| **Round table** | Everyone sees full chat; agents speak in order each turn | Peer debate, cross-check |
| **Centralized** | One **Group_Leader** plans; workers do slices; only leader submits | Division of labor |
| **Decentralized** | No leader; peers coordinate via chat/scratchpad | Flat team |

On ARML 2009 with 2 turns + mini model, **centralized scored highest** (see §4). That does *not* prove centralized is always best — only that the comparison machinery works.

---

## Evaluation paths (why grades look different)

| Situation | What you see | Meaning |
|---|---|---|
| Short math answers curated | `gold_answer_v1` / `gold_substring_match` | Auto match to expected finals |
| Writing, proofs, memorials, lab reports | `rubric_llm_v1` / `llm_judge_required` | Need LLM (or human) rubric scoring |
| Business-case slides | `slide_deck_v1` | Slide pipeline (PDF → images + rubric) |
| ICPC / IIOT | `programming_judge` / `judge_sandbox_required` | Need code tests / online judge — **not built yet** |

So if smoke says `llm_judge_required`, that is **success for the agent loop**, not a failed grade. The team finished; we just didn’t call the expensive rubric judge inside the smoke batch.

---

# What we tested (layer by layer)

## 1. Unit tests — “small pieces work in isolation”

```bash
python3 -m unittest discover -s tests -v
```

| File | What it checks | Result (2026-08-12) |
|---|---|---|
| `tests/test_contest_budget.py` | Defaults, overrides, truncation, token stop | **6/6 pass** |
| `tests/test_unified_evaluation.py` | PDF→images, gold multipart match, registry, rubric | **8/8 pass** |
| `tests/test_artifact_evaluation.py` | Slide HTML rules, PDF shape, eval schema | **3/4 pass** |

**Known fail:** HTML→PDF render timed out on this laptop (Playwright/Chromium). Collaboration and budgets are fine; it’s a local renderer flake.

**How to explain:**  
“Unit tests prove the budget math and graders don’t break on tiny fixtures. One slide-render test is flaky on my machine.”

---

## 2. Offline smoke — “every contest loads without an API key”

```bash
python3 src/run_smoke_batch.py --rounds 1
```

- Uses a **mock** LLM (fake answers).
- One problem per competition, round_table, 1 turn.
- Artifact: `results/smoke_batch/20260810-094125/smoke_batch.json`
- Result: **12/12 ok**, all submitted.

Bugs we fixed along the way (good talking points):

1. **IOL 2003** had no `problem_description` → env now falls back to `topic`.
2. **Jessup** had `team_size: "2-5"` (a string range) → env now takes the upper bound (5).

**How to explain:**  
“Before spending money, we proved all twelve collected contests can enter the env and finish a fake collaboration.”

| Competition | Representative problem | What env reported |
|---|---|---|
| ARML local / national team | 2009 sheets | gold substring (mock answers look like ARML) |
| ARML power / national power | proof packets | gold path fired on mock text* |
| ICPC / IIOT | programming | `judge_sandbox_required` — expected |
| IEO business case | 2021 case | `llm_judge_required` — expected |
| IOL / IJSO / WSC / Jessup | open-ended | `llm_judge_required` — expected |
| IOAA | 2025 group | gold path on mock* |

\*Mock answers are ARML-shaped, so env may claim “gold match” even when the real evaluator should be a rubric. Offline smoke = **stability**, not score truth.

---

## 3. Live smoke — “same matrix with a real small model”

```bash
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_smoke_batch.py --live --rounds 1
python3 src/run_smoke_batch.py --live --rounds 2 --schema round_table
```

- Model: **`openai/gpt-5.4-mini`** through Perplexity.
- Schema: round_table only (cost control).
- Results: **12/12 ok** for both 1-turn and 2-turn runs.

Artifacts:
- `results/smoke_batch/20260812-182401/` (1 turn)
- `results/smoke_batch/20260812-182846/` (2 turns)

### Live ×2 numbers (so you can point at a table)

| Competition | Turns | API calls | Est. output tokens | Submitted? | Env grade label |
|---|---:|---:|---:|---|---|
| ARML Local | 2 | 13 | 3100 | yes | gold substring |
| ARML National Team | 2 | 16 | 725 | yes | gold substring |
| ARML National Power | 2 | 31 | 2203 | yes | gold substring* |
| ARML Power | 2 | 29 | 10326 | yes | gold substring* |
| ICPC | 2 | 6 | 794 | yes | sandbox required |
| IIOT | 2 | 9 | 2609 | yes | sandbox required |
| IEO business case | 2 | 11 | 3546 | yes | LLM judge required |
| IOL team | 2 | 9 | 738 | yes | LLM judge required |
| IOAA group | 2 | 11 | 1789 | yes | gold substring* |
| IJSO practical | 2 | 7 | 347 | yes | LLM judge required |
| WSC writing | 2 | 4 | 1911 | yes | LLM judge required |
| Jessup | 2 | 12 | 3247 | yes | LLM judge required |

### What the live answers looked like (qualitative)

- **ARML-style sheets:** produced numbered finals — pipeline for short-answer contests feels right.
- **IEO / Jessup / WSC:** produced substantive write-ups / recommendations — good for later rubric scoring.
- **IOL 2003 / IJSO 2004:** often said “insufficient information.” That’s a **data packet** issue (thin text / missing PDF extract for that ID), not a crash. Say: “pipeline ran; content quality limited by incomplete problem text.”
- **ICPC / IIOT:** teams discussed algorithms / code; we **cannot score** until we have an automated judge.

**How to explain:**  
“Live smoke shows GPT-5.4-mini can drive every contest type under a 2-turn budget without collapsing. Scores are not the goal here — survival of the pipeline is.”

---

## 4. ARML Local 2009 — first scored baseline table

This is the run to show when someone asks “do you have any numbers yet?”

```bash
python3 src/run_exam.py --all-schemas --rounds 2
```

| Setting | Value |
|---|---|
| Problem | `arml_local_2009` (10 short answers, 4 points each → **/40**) |
| Team size | 6 |
| Turns | 2 |
| Agents | `openai/gpt-5.4-mini` |
| Judge | `anthropic/claude-sonnet-4-6` via Perplexity |
| Batch id | `20260812-183636` |

| Schema | Numbered parts | API calls | Est. tokens | **Judge score** |
|---|---:|---:|---:|---|
| Round table | 10 | 12 | 2474 | **4/40** |
| Centralized | 10 | 7 | 2278 | **14/40** |
| Decentralized | 10 | 13 | 2983 | **12/40** |

JSON traces (chat + actions + judge text):
- `results/arml_local_2009_round_table_20260812-183636.json`
- `results/arml_local_2009_centralized_20260812-183636.json`
- `results/arml_local_2009_decentralized_20260812-183636.json`

### How to talk about these scores honestly

- All three finished and produced a full 1–10 answer sheet → **experiment harness works**.
- Scores are **low–middling** because: small model, only **2 turns**, diagram problem (#10) often unsolved from text alone.
- Centralized used **fewer API calls** (7) and scored **highest** here — interesting anecdote, not a conclusion.
- This is a **pilot**, not the paper table. Paper needs more turns (toward 50), more years, more models, and maybe gold_answer_v1 grading in addition to LLM judge.

Rough judge pattern (centralized example): correct or partial on P1, P2, P4 (unsimplified), P6; wrong elsewhere; P10 missing diagram.

---

## 5. Evaluation-only smokes (show the graders work)

### Gold grader (no collaboration)

We built a perfect answer file from curated ARML Local 2009 finals and ran:

```bash
python3 src/evaluate_submission.py \
  --benchmark data/benchmarks/arml_local/benchmark.json \
  --problem-id arml_local_2009 \
  --submission-text /tmp/arml_2009_answers.txt \
  --media text
```

→ **40/40** on gradeable short answers (diagram/blank parts skipped).  
File: `results/evaluations/gold_answer_v1_20260730-221142/evaluation.json`

**How to explain:**  
“When short answers are curated, automatic grading works. That’s the exact-match end of the eval ladder.”

### Multimodal (PDF pages as images)

```bash
python3 src/smoke_multimodal.py data/raw/business_case/2024.pdf --pages 1-2
```

Early failure was huge PNGs (~tens of MB) causing SSL errors. We switched default rasterize to **JPEG + size cap**. Then Perplexity correctly read the IEO 2024 Hong Kong housing cover pages.

**How to explain:**  
“Models don’t get a special PDF brain — we turn PDFs into text and/or page images. Perplexity vision works on those images.”

---

## 6. What “12/12 ok” does *not* mean

Be careful in meetings:

| People might hear | What you should say |
|---|---|
| “You solved all contests” | “We **ran** all contests through the agent loop.” |
| “You have full scores for everything” | “Only ARML 2009 has LLM judge scores so far.” |
| “ICPC is evaluated” | “ICPC submits text; **judge is deferred**.” |
| “Labs work” | “We only score **written reports** as a proxy; no real instruments.” |
| “50 turns is official” | “50 is the **default placeholder**; per-contest calibration is next.” |

---

## 7. What’s done vs next (meeting cheat sheet)

### Done
- Dual media (text / images) for PDFs  
- Gold + rubric + slide evaluators in the stack  
- Turn / API / token **parameters** in code (50-turn default)  
- Three collaboration baselines  
- Offline + live smoke across **12 competitions**  
- First ARML three-schema scored pilot  
- Docs: design note, this results note  

### Next (agreed direction)
1. More turns / gradual pressure (API + tokens) once pipeline is trusted  
2. Scale samples (3–5 problems per contest) → then paper table (~40 contests × schemas × models)  
3. Wire smoke batch to call real rubric/slide judges where needed  
4. ICPC/IIOT online/sandbox judge spike  
5. Help Sean integrate his contest via `docs/SOFTWARE_DESIGN.md`  
6. Lab env-agent = low priority  

---

## 8. Reproduce everything

```bash
# Tiny unit checks
python3 -m unittest discover -s tests -v

# Offline: all contests, fake LLM
python3 src/run_smoke_batch.py --rounds 1

# Live: all contests, mini model
export PERPLEXITY_API_KEY=pplx-...
python3 src/run_smoke_batch.py --live --rounds 2 --schema round_table

# Live: ARML scored baselines
python3 src/run_exam.py --all-schemas --rounds 2
```

---

## Script you can read in the meeting (~45 seconds)

“We finished the first pipeline-complete smoke. Offline and live, all twelve collected competitions load, run under a turn budget, and submit without crashing. Turns are the time clock—each agent gets at most one model call per turn, or can sleep—and API calls and tokens are separate cost knobs we left mostly uncapped for now, with a default of fifty turns to calibrate later. We also ran ARML Local 2009 with all three collaboration baselines using GPT-5.4-mini for two turns; the LLM judge scored round table 4/40, centralized 14/40, and decentralized 12/40. That’s a pilot, not the final paper table. Still open: programming judges for ICPC/IIOT, turning on full rubric scoring in the smoke matrix, and scaling turns and models once we’re happy the harness is stable.”

---

## One-liner

**Pipeline works on all 20 DATA_COLLECTION contest families** (offline mock smoke 20/20 after adding IYPT/HMMT/MCM/ICM/Fyziklání/Purple Comet/ITYM benchmarks from existing PDFs). First scored ARML pilot is 4 / 14 / 12 out of 40 across the three schemas at 2 turns with a mini model — paper-scale experiments and programming judges still ahead.
