# Evaluation strategy

The benchmark uses the simplest defensible evaluator for each deliverable type.
Scores from different evaluator versions are not treated as interchangeable.

## Unified design

1. **Input / output media** — contest PDFs (and rendered submissions) parse to
   **text** and/or **page images**. No third special PDF path.
2. **Granularity** — `question` (one item) vs `competition` (full packet).
3. **Evaluators by type** — each benchmark problem has `evaluation.evaluator_id`
   after `collectors/enrich_evaluation_metadata.py`:
   - **gold** (`gold_answer_v1`) when short answers exist in `gold_label.parts`
   - **LLM rubric** (`rubric_llm_v1` / `slide_deck_v1`) for open-ended work
   - **deferred** for programming sandboxes / true oral AV / instrument labs

## Coverage after enrichment

| Family | Evaluator | Notes |
|---|---|---|
| ARML Local / National Team (short answers) | `gold_answer_v1` | curated finals in `data/rubrics/arml_*_short_answers.json` (diagram/ambiguous left blank → skipped) |
| ARML Power / proof packets | `rubric_llm_v1` | `team_power_proof_40_v1` |
| IOL / IOAA worked answers | `rubric_llm_v1` | `worked_answer_100_v1` |
| IEO business case | `slide_deck_v1` | shared slide pipeline |
| WSC writing | `rubric_llm_v1` | `wsc_writing_28_v1` |
| Jessup memorial | `rubric_llm_v1` | written only; oral deferred |
| IJSO practical | `rubric_llm_v1` | **report proxy**; instruments not observed |
| ICPC / IIOT | `programming_judge` | **deferred** until sandbox + tests |

Refresh metadata:

```bash
python3 collectors/enrich_evaluation_metadata.py
```

## Presentation / slide path (connected)

Last week's slide evaluator is the same `slide_deck_v1` used everywhere:

| Entry | Role |
|---|---|
| `src/evaluation/slides_pipeline.py` | Shared normalize + judge |
| `src/evaluate_artifact.py` | Score an existing HTML/PDF deck |
| `src/evaluate_submission.py` | Registry dispatch (IEO → slide_deck_v1) |
| `src/run_presentation_artifact.py` | Team generates HTML → same judge |

```bash
export PERPLEXITY_API_KEY="pplx-..."

python3 src/evaluate_artifact.py results/demo_submission/submission.pdf \
  --benchmark data/benchmarks/ieo_business_case/benchmark.json \
  --problem-id ieo_business_case_2024 \
  --provider perplexity --media images

python3 src/run_presentation_artifact.py \
  --benchmark data/benchmarks/ieo_business_case/benchmark.json \
  --problem-id ieo_business_case_2024 \
  --provider perplexity --media images --rounds 2
```

## Media + providers

| Provider | Native PDF | Multi-image | Typical path |
|---|---|---|---|
| Perplexity | prefer images | yes | PDF → PNG → judge |
| OpenAI | yes | yes | PDF or images |

```bash
export PERPLEXITY_API_KEY="pplx-..."
python3 src/smoke_multimodal.py data/raw/business_case/2024.pdf --pages 1-2
```

## Run evaluators

```bash
# Benchmark-aware (uses problem.evaluation + gold_label.parts)
python3 src/evaluate_submission.py \
  --benchmark data/benchmarks/wsc_writing/benchmark.json \
  --problem-id wsc_writing_gq_001 \
  --submission-text essay.txt \
  --provider perplexity \
  --media text

python3 src/evaluate_submission.py \
  --benchmark data/benchmarks/arml_local/benchmark.json \
  --problem-id arml_local_2009 \
  --submission-text answers.txt \
  --provider perplexity \
  --media text

python3 src/evaluate_submission.py \
  --benchmark data/benchmarks/ieo_business_case/benchmark.json \
  --problem-id ieo_business_case_2024 \
  --submission results/demo_submission/submission.pdf \
  --provider perplexity \
  --media images
```

## Gold parts schema

```json
{
  "parts": [
    {
      "id": "1",
      "expected": "(-6, 13)",
      "points": 4,
      "reference": "official solution excerpt...",
      "match_mode": "normalized"
    }
  ]
}
```

`match_mode` is `normalized` when a short `expected` exists, else `reference_llm`
(use the rubric LLM judge with the reference text).


