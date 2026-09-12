"""Canonical rubric and evaluation result schemas."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class EvaluationError(ValueError):
    """Raised when an evaluator returns malformed or inconsistent scoring."""


@dataclass(frozen=True)
class Criterion:
    id: str
    name: str
    max_score: float
    description: str
    observable: bool = True


@dataclass(frozen=True)
class Rubric:
    rubric_id: str
    title: str
    total_points: float
    criteria: tuple[Criterion, ...]
    not_observable_from_deck: tuple[str, ...] = ()

    def as_prompt_dict(self) -> dict:
        return {
            "rubric_id": self.rubric_id,
            "title": self.title,
            "total_points": self.total_points,
            "criteria": [asdict(criterion) for criterion in self.criteria],
            "not_observable_from_deck": list(self.not_observable_from_deck),
        }


@dataclass
class CriterionResult:
    id: str
    score: float
    max_score: float
    evidence: list[str]
    justification: str
    confidence: float
    observable: bool = True


@dataclass
class EvaluationResult:
    evaluator_id: str
    evaluator_version: str
    prompt_version: str
    model: str
    rubric_id: str
    criteria: list[CriterionResult]
    total_score: float
    max_score: float
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    artifact_checks: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def validate(self, rubric: Rubric) -> None:
        expected = {criterion.id: criterion for criterion in rubric.criteria}
        actual_ids = [criterion.id for criterion in self.criteria]
        if len(actual_ids) != len(set(actual_ids)):
            raise EvaluationError("Evaluator returned duplicate criterion IDs.")
        if set(actual_ids) != set(expected):
            raise EvaluationError(
                f"Criterion mismatch: expected {sorted(expected)}, got {sorted(actual_ids)}"
            )

        for result in self.criteria:
            definition = expected[result.id]
            if abs(result.max_score - definition.max_score) > 1e-6:
                raise EvaluationError(
                    f"Wrong maximum for {result.id}: "
                    f"{result.max_score} != {definition.max_score}"
                )
            if result.score < 0 or result.score > result.max_score:
                raise EvaluationError(
                    f"Score out of range for {result.id}: {result.score}/{result.max_score}"
                )
            if result.confidence < 0 or result.confidence > 1:
                raise EvaluationError(
                    f"Confidence out of range for {result.id}: {result.confidence}"
                )
            if result.observable and not result.evidence:
                raise EvaluationError(f"Observable criterion {result.id} has no slide evidence.")

        computed_total = sum(result.score for result in self.criteria)
        if abs(computed_total - self.total_score) > 1e-6:
            raise EvaluationError(
                f"Total does not equal criterion sum: {self.total_score} != {computed_total}"
            )
        if abs(self.max_score - rubric.total_points) > 1e-6:
            raise EvaluationError(
                f"Wrong evaluation maximum: {self.max_score} != {rubric.total_points}"
            )


def scale_rubric(rubric: Rubric, total_points: float) -> Rubric:
    """Proportionally rescale criterion maxima to a target total."""
    if abs(rubric.total_points - total_points) < 1e-6:
        return rubric
    if rubric.total_points <= 0:
        raise EvaluationError("Cannot scale a zero-point rubric.")
    factor = total_points / rubric.total_points
    criteria = tuple(
        Criterion(
            id=item.id,
            name=item.name,
            max_score=item.max_score * factor,
            description=item.description,
            observable=item.observable,
        )
        for item in rubric.criteria
    )
    return Rubric(
        rubric_id=f"{rubric.rubric_id}_scaled_{total_points:g}",
        title=rubric.title,
        total_points=total_points,
        criteria=criteria,
        not_observable_from_deck=rubric.not_observable_from_deck,
    )


def load_rubric(path: str | Path) -> Rubric:
    with Path(path).open(encoding="utf-8") as source:
        raw = json.load(source)
    criteria = tuple(
        Criterion(
            id=item["id"],
            name=item["name"],
            max_score=float(item["max_score"]),
            description=item["description"],
            observable=bool(item.get("observable", True)),
        )
        for item in raw["criteria"]
    )
    rubric = Rubric(
        rubric_id=raw["rubric_id"],
        title=raw["title"],
        total_points=float(raw["total_points"]),
        criteria=criteria,
        not_observable_from_deck=tuple(raw.get("not_observable_from_deck", [])),
    )
    ids = [item.id for item in criteria]
    if len(ids) != len(set(ids)):
        # A judge cannot return a unique score per duplicated id, so catch this
        # at load time rather than as a confusing validation failure later.
        raise EvaluationError(f"Rubric {rubric.rubric_id} has duplicate criterion IDs.")
    if abs(sum(item.max_score for item in criteria) - rubric.total_points) > 1e-6:
        raise EvaluationError("Rubric criterion maxima do not sum to total_points.")
    return rubric


def parse_evaluation_payload(
    raw_text: str,
    *,
    rubric: Rubric,
    evaluator_id: str,
    evaluator_version: str,
    prompt_version: str,
    model: str,
    warnings: list[str] | None = None,
    artifact_checks: dict[str, Any] | None = None,
    usage: dict[str, Any] | None = None,
) -> EvaluationResult:
    text = raw_text.strip()
    if text.startswith("```"):
        text = restrip_code_fence(text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise EvaluationError(f"Evaluator did not return JSON: {exc}") from exc
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError as nested_exc:
            raise EvaluationError(f"Malformed evaluator JSON: {nested_exc}") from nested_exc

    try:
        criteria = [
            CriterionResult(
                id=item["id"],
                score=float(item["score"]),
                max_score=float(item["max_score"]),
                evidence=[str(value) for value in item.get("evidence", [])],
                justification=str(item["justification"]),
                confidence=float(item["confidence"]),
                observable=bool(item.get("observable", True)),
            )
            for item in payload["criteria"]
        ]
        # total_score is derived from the criterion scores, so trust those and
        # recompute rather than discarding an otherwise-valid scoring over the
        # judge's arithmetic. Long rubrics make that slip common.
        reported_total = float(payload["total_score"])
        computed_total = sum(item.score for item in criteria)
        total_warnings = list(warnings or [])
        if abs(reported_total - computed_total) > 1e-6:
            total_warnings.append(
                f"Judge reported total_score={reported_total:g} but the criterion "
                f"scores sum to {computed_total:g}; using the criterion sum."
            )
        result = EvaluationResult(
            evaluator_id=evaluator_id,
            evaluator_version=evaluator_version,
            prompt_version=prompt_version,
            model=model,
            rubric_id=rubric.rubric_id,
            criteria=criteria,
            total_score=computed_total,
            max_score=float(payload["max_score"]),
            warnings=total_warnings + [str(value) for value in payload.get("warnings", [])],
            limitations=[str(value) for value in payload.get("limitations", [])],
            artifact_checks=dict(artifact_checks or {}),
            usage=dict(usage or {}),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EvaluationError(f"Evaluator JSON has the wrong schema: {exc}") from exc
    result.validate(rubric)
    return result


def restrip_code_fence(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
