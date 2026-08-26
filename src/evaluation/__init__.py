"""Structured, auditable evaluators for team-task submissions."""

from .default_rubrics import ensure_default_rubrics
from .error_taxonomy import ERROR_CODES, classify_errors
from .finalize import apply_registered_judge
from .collaboration_score import CoordinationScoreResult, score_coordination
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
from .registry import (
    EvaluatorSpec,
    RegistryError,
    load_registry,
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
from .team_metrics import (
    METRIC_DEFINITIONS,
    Action,
    Message,
    TeamTranscript,
    adapt_transcript,
    compute_team_metrics,
)

__all__ = [
    "Criterion",
    "CriterionResult",
    "ERROR_CODES",
    "EvalMode",
    "EvalPacket",
    "EvaluationError",
    "EvaluationResult",
    "EvaluatorSpec",
    "GoldAnswerEvaluator",
    "METRIC_DEFINITIONS",
    "Message",
    "CoordinationScoreResult",
    "QuestionSpec",
    "RegistryError",
    "Rubric",
    "RubricDocumentEvaluator",
    "SlideDeckEvaluator",
    "TeamTranscript",
    "Action",
    "adapt_transcript",
    "apply_registered_judge",
    "classify_errors",
    "compute_team_metrics",
    "score_coordination",
    "build_competition_packet",
    "build_question_packet",
    "build_task_asset",
    "ensure_default_rubrics",
    "evaluate_slide_deck",
    "load_gold_parts",
    "load_registry",
    "load_rubric",
    "resolve_evaluator_spec",
    "resolve_problem_task_pdf",
    "strategy_kind",
]
