"""Evaluate an HTML or PDF slide deck against a task PDF and rubric JSON.

Thin wrapper around the shared slide pipeline (same path as evaluate_submission
and run_presentation_artifact).
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from evaluation.slides_pipeline import evaluate_slide_deck, resolve_problem_task_pdf

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_problem(benchmark: Path, problem_id: str) -> dict:
    data = json.loads(benchmark.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("problems") or []
    for item in items:
        if item.get("problem_id") == problem_id:
            return item
    raise SystemExit(f"problem_id {problem_id!r} not found in {benchmark}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path, nargs="?", default=None)
    parser.add_argument("--benchmark", type=Path, default=None)
    parser.add_argument("--problem-id", default=None)
    parser.add_argument("--task-pdf", type=Path, default=None)
    parser.add_argument("--rubric", type=Path, default=None)
    parser.add_argument("--task-pages", default=None, help="Inclusive range, e.g. 1-10")
    parser.add_argument("--task-label", default="presentation task")
    parser.add_argument("--min-slides", type=int, default=1)
    parser.add_argument("--max-slides", type=int, default=20)
    parser.add_argument("--max-file-size-mb", type=int, default=20)
    parser.add_argument(
        "--provider",
        default=os.environ.get("EVALUATOR_PROVIDER", "perplexity"),
        choices=["perplexity", "openai"],
    )
    parser.add_argument("--model", default=os.environ.get("EVALUATOR_MODEL"))
    parser.add_argument(
        "--media",
        default="images",
        choices=["pdf", "images"],
        help="pdf=native PDF attach (OpenAI); images=rasterized pages (Perplexity-friendly)",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    problem = None
    if args.benchmark and args.problem_id:
        problem = load_problem(args.benchmark.resolve(), args.problem_id)
        evaluation = problem.get("evaluation") or {}
        if evaluation.get("evaluator_id") not in {None, "slide_deck_v1"}:
            raise SystemExit(
                f"Problem {args.problem_id} is registered as "
                f"{evaluation.get('evaluator_id')}, not slide_deck_v1. "
                "Use src/evaluate_submission.py instead."
            )
        if not args.rubric and evaluation.get("rubric_path"):
            args.rubric = REPO_ROOT / evaluation["rubric_path"]
        if not args.task_pdf:
            args.task_pdf = resolve_problem_task_pdf(problem, REPO_ROOT)
        if args.task_label == "presentation task":
            args.task_label = problem.get("topic") or problem.get("task_type") or args.task_label

    if not args.submission or not args.task_pdf or not args.rubric:
        raise SystemExit(
            "Need submission + task PDF + rubric "
            "(pass flags or --benchmark/--problem-id for IEO-style cases)."
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = REPO_ROOT / "results" / "evaluations" / f"slide_deck_{timestamp}"
    result = evaluate_slide_deck(
        task_pdf=args.task_pdf,
        submission=args.submission,
        rubric=args.rubric,
        work_dir=run_dir,
        provider=args.provider,
        model=args.model,
        media=args.media,
        task_pages=args.task_pages,
        task_label=args.task_label,
        min_slides=args.min_slides,
        max_slides=args.max_slides,
        max_file_size_mb=args.max_file_size_mb,
        extra_payload={
            "problem_id": args.problem_id,
            "benchmark": str(args.benchmark) if args.benchmark else None,
        },
    )
    # Prefer repo-relative normalized path in saved JSON when possible.
    try:
        result.payload["normalized_pdf"] = str(
            result.submission.pdf_path.relative_to(REPO_ROOT)
        )
    except ValueError:
        pass

    output_path = args.output.resolve() if args.output else run_dir / "evaluation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.payload, indent=2), encoding="utf-8")
    print(f"[slide_deck_v1] Score: {result.evaluation.total_score:g}/{result.evaluation.max_score:g}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
