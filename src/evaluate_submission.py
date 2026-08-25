"""Unified evaluation entry: gold or LLM-judge by task type / problem metadata.

Examples:
  python3 collectors/enrich_evaluation_metadata.py

  # From benchmark problem metadata
  python3 src/evaluate_submission.py \
    --benchmark data/benchmarks/arml_local/benchmark.json \
    --problem-id arml_local_2009 \
    --submission-text answers.txt

  # Open-ended writing
  export PERPLEXITY_API_KEY=...
  python3 src/evaluate_submission.py \
    --benchmark data/benchmarks/wsc_writing/benchmark.json \
    --problem-id wsc_writing_gq_001 \
    --submission-text essay.txt \
    --provider perplexity \
    --media text
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from artifacts import Asset, normalize_submission
from artifacts.assets import file_sha256
from evaluation import (
    GoldAnswerEvaluator,
    RegistryError,
    load_gold_parts,
    load_rubric,
    resolve_evaluator_spec,
    strategy_kind,
)
from evaluation.default_rubrics import ensure_default_rubrics
from evaluation.models import scale_rubric
from evaluation.rubric_llm import RubricDocumentEvaluator
from evaluation.slides_pipeline import (
    build_task_asset,
    evaluate_slide_deck,
    resolve_problem_task_pdf,
)
from llm import resolve_request_fn
from pypdf import PdfReader


def load_problem(benchmark: Path, problem_id: str) -> dict:
    data = json.loads(benchmark.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("problems") or []
    for item in items:
        if item.get("problem_id") == problem_id:
            return item
    raise SystemExit(f"problem_id {problem_id!r} not found in {benchmark}")


def build_task_asset(task_pdf: Path, pages: str | None) -> Asset:
    path = task_pdf.resolve()
    page_count = len(PdfReader(str(path)).pages)
    if pages:
        start_text, end_text = pages.split("-", 1)
        page_start, page_end = int(start_text), int(end_text)
    else:
        page_start, page_end = 1, page_count
    return Asset(
        path=path,
        mime_type="application/pdf",
        role="agent_visible",
        page_start=page_start,
        page_end=page_end,
        sha256=file_sha256(path),
    )


def resolve_rubric_path(raw: str | None) -> Path | None:
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def main() -> None:
    ensure_default_rubrics()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=None)
    parser.add_argument("--problem-id", default=None)
    parser.add_argument("--task-type", default=None)
    parser.add_argument("--evaluator-id", default=None)
    parser.add_argument("--mode", choices=["question", "competition"], default="competition")
    parser.add_argument("--media", choices=["text", "images", "both", "pdf"], default="images")
    parser.add_argument("--provider", choices=["perplexity", "openai"], default="perplexity")
    parser.add_argument("--model", default=None)
    parser.add_argument("--task-pdf", type=Path, default=None)
    parser.add_argument("--task-pages", default=None)
    parser.add_argument("--rubric", type=Path, default=None)
    parser.add_argument("--gold-json", type=Path, default=None)
    parser.add_argument("--submission", type=Path, default=None)
    parser.add_argument("--submission-text", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    problem = None
    evaluation_meta: dict = {}
    if args.benchmark and args.problem_id:
        problem = load_problem(args.benchmark.resolve(), args.problem_id)
        evaluation_meta = dict(problem.get("evaluation") or {})
        args.task_type = args.task_type or problem.get("task_type")
        if not args.rubric:
            args.rubric = resolve_rubric_path(evaluation_meta.get("rubric_path"))
        if not args.gold_json and problem.get("gold_label"):
            # Use in-memory gold from problem later.
            pass
        if not args.task_pdf:
            args.task_pdf = resolve_problem_task_pdf(problem, REPO_ROOT)

    if not args.task_type and not args.evaluator_id:
        raise SystemExit("Provide --task-type or --benchmark/--problem-id")

    evaluator_id = args.evaluator_id or evaluation_meta.get("evaluator_id")
    if evaluator_id:
        spec = next(
            (
                item
                for item in __import__("evaluation.registry", fromlist=["load_registry"]).load_registry()
                if item.id == evaluator_id
            ),
            None,
        )
        if spec is None:
            raise RegistryError(f"Unknown evaluator_id={evaluator_id}")
    else:
        spec = resolve_evaluator_spec(args.task_type)

    if evaluation_meta.get("status") == "deferred" or spec.status.startswith("deferred"):
        raise RegistryError(
            f"Evaluator {spec.id} is deferred ({evaluation_meta.get('status') or spec.status})."
        )

    kind = strategy_kind(spec)
    # Prefer explicit evaluator kind by id.
    if spec.id == "gold_answer_v1":
        kind = "gold"
    elif spec.id in {"slide_deck_v1", "rubric_llm_v1"}:
        kind = "llm_judge"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = REPO_ROOT / "results" / "evaluations" / f"{spec.id}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    packet_meta = {
        "evaluator_id": spec.id,
        "strategy": spec.strategy,
        "strategy_kind": kind,
        "mode": args.mode,
        "media": args.media,
        "problem_id": args.problem_id,
        "task_type": args.task_type,
        "evaluation_meta": evaluation_meta,
    }

    submission_text = (
        args.submission_text.read_text(encoding="utf-8") if args.submission_text else ""
    )

    if kind == "gold" or spec.id == "gold_answer_v1":
        if problem and problem.get("gold_label"):
            gold_label = problem["gold_label"]
        elif args.gold_json:
            gold_label = json.loads(args.gold_json.read_text(encoding="utf-8"))
            gold_label = gold_label.get("gold_label", gold_label)
        else:
            raise SystemExit("gold evaluation needs --benchmark problem gold or --gold-json")
        if not submission_text:
            raise SystemExit("gold evaluation needs --submission-text")
        parts = load_gold_parts(gold_label)
        # If no short answers exist, automatically fall back to rubric LLM.
        if not any(part.expected for part in parts):
            print("No short gold answers; falling back to rubric_llm_v1.")
            from evaluation.registry import load_registry

            evaluator_id = evaluation_meta.get("fallback_evaluator_id") or "rubric_llm_v1"
            spec = next(item for item in load_registry() if item.id == evaluator_id)
            kind = "llm_judge"
            packet_meta["evaluator_id"] = spec.id
            packet_meta["strategy_kind"] = kind
            packet_meta["fallback_from"] = "gold_answer_v1"
        else:
            result = GoldAnswerEvaluator(parts=parts, submission_text=submission_text).evaluate()
            payload = {"packet": packet_meta, "evaluation": result.to_dict()}
            out = args.output.resolve() if args.output else run_dir / "evaluation.json"
            out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"[{spec.id}] Score: {result.total_score:g}/{result.max_score:g}")
            print(f"Saved: {out}")
            return

    if spec.id == "slide_deck_v1":
        if not args.task_pdf or not args.submission or not args.rubric:
            raise SystemExit("slide_deck_v1 requires --task-pdf, --submission, and --rubric")
        media = "images" if args.media in {"images", "both"} else "pdf"
        slide_result = evaluate_slide_deck(
            task_pdf=args.task_pdf,
            submission=args.submission,
            rubric=args.rubric,
            work_dir=run_dir,
            provider=args.provider,
            model=args.model,
            media=media,
            task_pages=args.task_pages,
            task_label=args.task_type or "presentation task",
            extra_payload={"packet": packet_meta},
        )
        try:
            slide_result.payload["normalized_pdf"] = str(
                slide_result.submission.pdf_path.relative_to(REPO_ROOT)
            )
        except ValueError:
            pass
        payload = {"packet": packet_meta, "evaluation": slide_result.evaluation.to_dict()}
        payload.update({k: v for k, v in slide_result.payload.items() if k != "evaluation"})

    elif kind == "llm_judge" or spec.id == "rubric_llm_v1":
        rubric_path = Path(args.rubric).resolve() if args.rubric else None
        if rubric_path is None:
            raise SystemExit("rubric_llm_v1 requires --rubric or evaluation.rubric_path")
        rubric = load_rubric(rubric_path)
        if problem and problem.get("total_points"):
            rubric = scale_rubric(rubric, float(problem["total_points"]))
        task_text = ""
        reference_text = ""
        if problem:
            task_text = str(problem.get("problem_description") or "")
            gold = problem.get("gold_label") or {}
            reference_text = str(gold.get("expected_answer") or gold.get("grading_rubric") or "")
            if gold.get("parts"):
                reference_text = "\n\n".join(
                    f"Part {part.get('id')}: {part.get('reference') or part.get('expected')}"
                    for part in gold["parts"]
                )
        task_asset = None
        if args.task_pdf:
            task_asset = build_task_asset(args.task_pdf, args.task_pages)
        submission_pdf = args.submission.resolve() if args.submission else None
        media = args.media
        if media == "both":
            media = "images"
        if args.provider == "perplexity" and media == "pdf":
            media = "images"
        if media in {"images", "pdf"} and submission_pdf is None and not submission_text:
            raise SystemExit("Provide --submission PDF and/or --submission-text")
        if media == "text" and not submission_text:
            raise SystemExit("text media requires --submission-text")
        result = RubricDocumentEvaluator(
            request_fn=resolve_request_fn(provider=args.provider, model=args.model),
            rubric=rubric,
            task_text=task_text,
            task_asset=task_asset,
            submission_text=submission_text,
            submission_pdf=submission_pdf,
            reference_text=reference_text,
            media=media if media in {"text", "pdf", "images"} else "text",
            image_work_dir=run_dir / "judge_pages",
            task_label=args.task_type or "contest task",
            deliverable_label=str(evaluation_meta.get("deliverable") or "submission"),
        ).evaluate()
        for limitation in evaluation_meta.get("limitations") or []:
            if limitation not in result.limitations:
                result.limitations.append(str(limitation))
        payload = {"packet": packet_meta, "evaluation": result.to_dict()}
    else:
        raise RegistryError(f"No runnable implementation for {spec.id} / kind={kind}")

    out = args.output.resolve() if args.output else run_dir / "evaluation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    evaluation = payload["evaluation"]
    print(f"[{spec.id}] Score: {evaluation['total_score']:g}/{evaluation['max_score']:g}")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
