from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .models import BenchmarkProblem
from .src_bridge import REPO_ROOT, ensure_src_imports

ensure_src_imports()

from artifacts.assets import Asset  # noqa: E402
from evaluation.gold import GoldAnswerEvaluator, GoldPart, load_gold_parts  # noqa: E402
from evaluation.models import (  # noqa: E402
    EvaluationError,
    EvaluationResult,
    load_rubric,
    scale_rubric,
)
from evaluation.registry import (  # noqa: E402
    RegistryError,
    resolve_evaluator_by_id,
    resolve_evaluator_spec,
)
from evaluation.rubric_llm import RubricDocumentEvaluator  # noqa: E402
from llm import RequestFn  # noqa: E402


@dataclass(frozen=True)
class ScoreResult:
    method: str
    raw_score: float
    max_score: float
    normalized_100: float
    breakdown: list[dict[str, Any]]
    judge_feedback: str
    evaluator: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_score(raw_score: float, max_score: float) -> float:
    if max_score <= 0:
        raise ValueError("max_score must be positive")
    return round(max(0.0, min(100.0, raw_score / max_score * 100)), 4)


def _score_result(result: EvaluationResult) -> ScoreResult:
    feedback = "\n".join([*result.warnings, *result.limitations]).strip()
    return ScoreResult(
        method=result.evaluator_id,
        raw_score=result.total_score,
        max_score=result.max_score,
        normalized_100=normalize_score(result.total_score, result.max_score),
        breakdown=[asdict(item) for item in result.criteria],
        judge_feedback=feedback,
        evaluator=result.to_dict(),
    )


def _reference_text(problem: BenchmarkProblem) -> str:
    gold = problem.gold_label
    if gold.get("parts"):
        return "\n\n".join(
            f"Part {part.get('id')}: {part.get('reference') or part.get('expected')}"
            for part in gold["parts"]
        )
    return str(gold.get("expected_answer") or gold.get("grading_rubric") or "")


def _task_asset(problem: BenchmarkProblem) -> Asset | None:
    source = next(
        (asset for asset in problem.assets if asset.mime_type == "application/pdf"),
        None,
    )
    if source is None:
        return None
    return Asset(
        path=source.path,
        mime_type=source.mime_type,
        role="agent_visible",
        page_start=source.page_start,
        page_end=source.page_end,
    )


def score_submission(
    problem: BenchmarkProblem,
    answer: str,
    request_fn: RequestFn,
    *,
    work_dir: Path,
    media: str = "text",
) -> ScoreResult:
    evaluation = problem.evaluation
    evaluator_id = evaluation.get("evaluator_id")
    spec = (
        resolve_evaluator_by_id(str(evaluator_id))
        if evaluator_id
        else resolve_evaluator_spec(problem.task_type)
    )

    if spec.id == "gold_answer_v1":
        try:
            try:
                parts = load_gold_parts(problem.gold_label)
                submission_text = answer
            except EvaluationError:
                expected = problem.gold_label.get("expected_answer")
                if expected is None:
                    raise
                candidates = expected if isinstance(expected, list) else [expected]
                parts = [
                    GoldPart(
                        id="1",
                        expected=str(candidates[0]),
                        aliases=tuple(str(value) for value in candidates[1:]),
                        points=float(problem.total_points or 100),
                    )
                ]
                submission_text = f"1. {answer}"
            if not any(part.expected for part in parts):
                raise EvaluationError("No deterministic short-answer parts")
            return _score_result(
                GoldAnswerEvaluator(
                    parts=parts,
                    submission_text=submission_text,
                ).evaluate()
            )
        except EvaluationError:
            fallback = evaluation.get("fallback_evaluator_id")
            if not fallback:
                raise
            spec = resolve_evaluator_by_id(str(fallback))

    if spec.id == "rubric_llm_v1":
        rubric_path = evaluation.get("rubric_path")
        if not rubric_path:
            raise RegistryError(
                f"{problem.problem_id} requires evaluation.rubric_path"
            )
        rubric = load_rubric(REPO_ROOT / str(rubric_path))
        if problem.total_points:
            rubric = scale_rubric(rubric, problem.total_points)
        evaluator_media = media if media in {"text", "pdf", "images"} else "images"
        result = RubricDocumentEvaluator(
            request_fn=request_fn,
            rubric=rubric,
            task_text=problem.problem_description,
            task_asset=_task_asset(problem),
            submission_text=answer,
            reference_text=_reference_text(problem),
            media=evaluator_media,
            image_work_dir=work_dir / "judge_pages",
            task_label=problem.task_type or "contest task",
            deliverable_label=str(evaluation.get("deliverable") or "team submission"),
        ).evaluate()
        for limitation in evaluation.get("limitations") or []:
            if str(limitation) not in result.limitations:
                result.limitations.append(str(limitation))
        return _score_result(result)

    if spec.id == "slide_deck_v1":
        raise RegistryError(
            "slide_deck_v1 requires an HTML/PDF artifact; text-only pipeline output "
            "cannot be scored as a slide deck"
        )
    raise RegistryError(
        f"Pipeline has no runnable implementation for evaluator {spec.id} "
        f"(status={spec.status})"
    )
