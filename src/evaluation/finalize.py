"""Post-submit grading: use registered gold / rubric LLM / leave deferred.

The env's grade_submission() only does gold substring match (or flags that a
judge is needed). Call apply_registered_judge after collaboration so
rubric_llm_v1 / slide_deck_v1 actually score.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from llm import RequestFn

from .default_rubrics import ensure_default_rubrics
from .models import load_rubric, scale_rubric
from .registry import load_registry, strategy_kind
from .rubric_llm import RubricDocumentEvaluator


REPO_ROOT = Path(__file__).resolve().parents[2]


def _resolve_rubric_path(problem: dict, repo_root: Path) -> Path | None:
    evaluation = dict(problem.get("evaluation") or {})
    raw = evaluation.get("rubric_path")
    if not raw:
        return None
    path = Path(str(raw))
    if not path.is_absolute():
        path = repo_root / path
    return path if path.is_file() else None


def _reference_text(problem: dict) -> str:
    gold = problem.get("gold_label") or {}
    if gold.get("parts"):
        lines = []
        for part in gold["parts"]:
            ref = part.get("reference") or part.get("expected") or ""
            lines.append(f"Part {part.get('id')}: {ref}")
        return "\n\n".join(lines)
    return str(gold.get("expected_answer") or gold.get("grading_rubric") or "")


def apply_registered_judge(
    problem: dict,
    submission_text: str,
    quick_grade: dict[str, Any],
    *,
    request_fn: RequestFn | None,
    work_dir: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Upgrade llm_judge_required (and similar) into a real rubric score.

    Leaves gold matches and programming-sandbox stubs untouched. Without a
    request_fn (offline smoke), returns quick_grade unchanged.
    """
    method = quick_grade.get("method")
    if method in {"gold_substring_match", "judge_sandbox_required"}:
        return quick_grade
    if quick_grade.get("graded") and method not in {None, "llm_judge_required"}:
        return quick_grade
    if not submission_text.strip():
        return {
            **quick_grade,
            "graded": False,
            "method": method or "llm_judge_required",
            "reason": "No submission text to judge.",
        }
    if request_fn is None:
        return quick_grade

    evaluation = dict(problem.get("evaluation") or {})
    if evaluation.get("status") == "deferred":
        return {
            **quick_grade,
            "graded": False,
            "method": "evaluator_deferred",
            "reason": f"evaluation.status=deferred ({evaluation.get('evaluator_id')})",
        }

    ensure_default_rubrics()
    root = repo_root or REPO_ROOT
    evaluator_id = evaluation.get("evaluator_id") or "rubric_llm_v1"
    if evaluator_id == "programming_judge":
        return quick_grade

    registry = {item.id: item for item in load_registry()}
    spec = registry.get(evaluator_id)
    if spec is None:
        return {
            **quick_grade,
            "graded": False,
            "method": "unknown_evaluator",
            "reason": f"Unknown evaluator_id={evaluator_id}",
        }
    if spec.status.startswith("deferred"):
        return {
            **quick_grade,
            "graded": False,
            "method": "evaluator_deferred",
            "reason": f"Evaluator {spec.id} is deferred ({spec.status}).",
        }

    kind = strategy_kind(spec)
    if evaluator_id in {"rubric_llm_v1", "slide_deck_v1"} or kind == "llm_judge":
        rubric_path = _resolve_rubric_path(problem, root)
        if rubric_path is None:
            return {
                **quick_grade,
                "graded": False,
                "method": "llm_judge_required",
                "reason": "Missing evaluation.rubric_path for rubric LLM judge.",
            }
        rubric = load_rubric(rubric_path)
        if problem.get("total_points"):
            rubric = scale_rubric(rubric, float(problem["total_points"]))

        work = Path(work_dir or (root / "results" / "judge_scratch"))
        work.mkdir(parents=True, exist_ok=True)

        # Smoke / text workspace submissions: score on text. Full slide PDF
        # judging remains available via evaluate_submission.py.
        result = RubricDocumentEvaluator(
            request_fn=request_fn,
            rubric=rubric,
            task_text=str(problem.get("problem_description") or ""),
            submission_text=submission_text,
            reference_text=_reference_text(problem),
            media="text",
            image_work_dir=work / "judge_pages",
            task_label=str(problem.get("task_type") or "contest task"),
            deliverable_label=str(evaluation.get("deliverable") or "submission"),
            evaluator_id=evaluator_id if evaluator_id != "slide_deck_v1" else "rubric_llm_v1",
        ).evaluate()
        for limitation in evaluation.get("limitations") or []:
            if limitation not in result.limitations:
                result.limitations.append(str(limitation))
        if evaluator_id == "slide_deck_v1":
            result.limitations.append(
                "Scored as text via rubric LLM; HTML/PDF slide checks not run in-pipeline."
            )

        return {
            "graded": True,
            "method": evaluator_id,
            "score": result.total_score,
            "max_score": result.max_score,
            "correct": result.total_score >= result.max_score,
            "evaluation": result.to_dict(),
            "submitted_by": quick_grade.get("submitted_by"),
        }

    return quick_grade
