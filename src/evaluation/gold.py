"""Deterministic gold / multipart graders for numerical answer sheets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import Criterion, CriterionResult, EvaluationError, EvaluationResult, Rubric


ANSWER_LINE_RE = re.compile(
    r"(?m)^\s*(?:problem\s*)?(\d+)\s*[.):\-]\s*(.+?)\s*$",
    re.IGNORECASE,
)


def normalize_answer(value: str) -> str:
    text = value.lower().strip()
    text = text.replace("−", "-").replace("–", "-")
    text = re.sub(r"\s+", "", text)
    text = text.replace("$", "")
    return text


def parse_numbered_answers(submission: str) -> dict[str, str]:
    answers: dict[str, str] = {}
    for match in ANSWER_LINE_RE.finditer(submission):
        answers[match.group(1)] = match.group(2).strip()
    return answers


@dataclass(frozen=True)
class GoldPart:
    id: str
    expected: str
    points: float
    aliases: tuple[str, ...] = ()
    reference: str = ""
    match_mode: str = "normalized"  # normalized | exact | reference_llm


def load_gold_parts(gold_label: dict[str, Any]) -> list[GoldPart]:
    """Load structured multipart gold. Prefers gold_label['parts']."""
    raw_parts = gold_label.get("parts")
    if raw_parts:
        parts: list[GoldPart] = []
        for item in raw_parts:
            parts.append(
                GoldPart(
                    id=str(item["id"]),
                    expected=str(item.get("expected") or ""),
                    points=float(item.get("points", item.get("max_score", 1))),
                    aliases=tuple(str(value) for value in item.get("aliases", [])),
                    reference=str(item.get("reference") or ""),
                    match_mode=str(item.get("match_mode") or ("normalized" if item.get("expected") else "reference_llm")),
                )
            )
        return parts

    answers = gold_label.get("answers")
    if isinstance(answers, dict) and answers:
        default_points = float(gold_label.get("points_per_part", 1))
        return [
            GoldPart(id=str(key), expected=str(value), points=default_points)
            for key, value in answers.items()
        ]

    raise EvaluationError(
        "gold_label has no structured 'parts' or 'answers'. "
        "Run collectors/enrich_evaluation_metadata.py or add multipart gold."
    )


def gold_parts_to_rubric(
    parts: list[GoldPart],
    *,
    rubric_id: str = "gold_multipart",
    title: str = "Multipart gold answers",
) -> Rubric:
    criteria = tuple(
        Criterion(
            id=part.id,
            name=f"Problem {part.id}",
            max_score=part.points,
            description=f"Match official answer for problem {part.id}.",
            observable=True,
        )
        for part in parts
    )
    return Rubric(
        rubric_id=rubric_id,
        title=title,
        total_points=sum(part.points for part in parts),
        criteria=criteria,
    )


def answers_match(expected: str, actual: str, aliases: tuple[str, ...] = ()) -> bool:
    candidates = (expected,) + aliases
    norm_actual = normalize_answer(actual)
    for candidate in candidates:
        norm_expected = normalize_answer(candidate)
        if not norm_expected:
            continue
        if norm_expected == norm_actual or norm_expected in norm_actual or norm_actual in norm_expected:
            return True
    return False


@dataclass
class GoldAnswerEvaluator:
    """Compare a numbered answer sheet against structured gold parts."""

    parts: list[GoldPart]
    submission_text: str
    evaluator_id: str = "gold_answer_v1"
    evaluator_version: str = "1.0.0"
    model: str = "deterministic"

    def evaluate(self) -> EvaluationResult:
        if not self.parts:
            raise EvaluationError("GoldAnswerEvaluator requires at least one part.")
        gradeable = [
            part
            for part in self.parts
            if part.expected and part.match_mode != "reference_llm"
        ] or [
            # Allow explicit reference_llm parts that still carry an expected short string.
            part for part in self.parts if part.expected
        ]
        if not gradeable:
            raise EvaluationError(
                "No short-answer gold parts to grade. Use rubric_llm_v1 instead."
            )
        rubric = gold_parts_to_rubric(gradeable)
        parsed = parse_numbered_answers(self.submission_text)
        criteria: list[CriterionResult] = []
        warnings: list[str] = []
        skipped = [
            part.id
            for part in self.parts
            if part.id not in {g.id for g in gradeable}
        ]
        if skipped:
            warnings.append(
                "Skipped parts without curated short answers (use rubric_llm_v1): "
                + ", ".join(skipped)
            )

        if not parsed:
            warnings.append(
                "Could not parse numbered answers (expected lines like '1. ...')."
            )

        for part in gradeable:
            actual = parsed.get(part.id, "")
            correct = bool(actual) and answers_match(part.expected, actual, part.aliases)
            score = part.points if correct else 0.0
            evidence = [
                f"submitted[{part.id}]={actual or '(missing)'}",
                f"expected[{part.id}]={part.expected}",
            ]
            criteria.append(
                CriterionResult(
                    id=part.id,
                    score=score,
                    max_score=part.points,
                    evidence=evidence,
                    justification=(
                        "Exact/normalized match against gold."
                        if correct
                        else "No normalized match against gold."
                    ),
                    confidence=1.0,
                    observable=True,
                )
            )

        result = EvaluationResult(
            evaluator_id=self.evaluator_id,
            evaluator_version=self.evaluator_version,
            prompt_version="deterministic_gold_v1",
            model=self.model,
            rubric_id=rubric.rubric_id,
            criteria=criteria,
            total_score=sum(item.score for item in criteria),
            max_score=rubric.total_points,
            warnings=warnings,
            limitations=[
                "Deterministic string match only; equivalent forms may be marked wrong.",
                "Only curated short-answer parts are included in this score.",
            ],
            artifact_checks={
                "parsed_answer_ids": sorted(parsed),
                "skipped_part_ids": skipped,
            },
        )
        result.validate(rubric)
        return result
