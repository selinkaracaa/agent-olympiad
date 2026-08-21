"""Structured, auditable evaluators for team-task submissions."""

from .default_rubrics import ensure_default_rubrics
from .gold import GoldAnswerEvaluator, load_gold_parts
from .modes import (
    EvalMode,
    EvalPacket,
    QuestionSpec,
    build_competition_packet,
    build_question_packet,
)
from .models import (
    Criterion,
    CriterionResult,
    EvaluationError,
    EvaluationResult,
    Rubric,
    load_rubric,
)
from .programming import (
    DockerProgrammingJudge,
    ProblemPackage,
    ProgrammingJudgeError,
    ProgrammingJudgeResult,
    load_problem_package,
)
from .registry import (
    EvaluatorSpec,
    RegistryError,
    load_registry,
    resolve_evaluator_by_id,
    resolve_evaluator_spec,
    strategy_kind,
)
from .rubric_llm import RubricDocumentEvaluator
from .slides import SlideDeckEvaluator
from .slides_pipeline import (
    build_task_asset,
    evaluate_slide_deck,
    resolve_problem_task_pdf,
)

__all__ = [
    "Criterion",
    "CriterionResult",
    "EvalMode",
    "EvalPacket",
    "EvaluationError",
    "EvaluationResult",
    "EvaluatorSpec",
    "DockerProgrammingJudge",
    "GoldAnswerEvaluator",
    "ProblemPackage",
    "ProgrammingJudgeError",
    "ProgrammingJudgeResult",
    "QuestionSpec",
    "RegistryError",
    "Rubric",
    "RubricDocumentEvaluator",
    "SlideDeckEvaluator",
    "build_competition_packet",
    "build_question_packet",
    "build_task_asset",
    "ensure_default_rubrics",
    "evaluate_slide_deck",
    "load_gold_parts",
    "load_problem_package",
    "load_registry",
    "load_rubric",
    "resolve_evaluator_by_id",
    "resolve_evaluator_spec",
    "resolve_problem_task_pdf",
    "strategy_kind",
]
