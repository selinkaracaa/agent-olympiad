"""Deterministic gold / multipart graders for numerical answer sheets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import Criterion, CriterionResult, EvaluationError, EvaluationResult, Rubric


# Classic: "1. answer" / "1) answer" / "Problem 1: answer"
ANSWER_LINE_RE = re.compile(
    r"(?m)^\s*(?:(?:problem|q|part)\s*)?(\d+)\s*[.):=\-]\s*(.+?)\s*$",
    re.IGNORECASE,
)
# Inline numbered tokens anywhere in the blob
INLINE_NUM_RE = re.compile(
    r"(?i)(?:^|[;\s])(?:(?:problem|q|part|t|team)\s*)?(\d+)\s*[.):=\-]\s*",
)


def normalize_answer(value: str) -> str:
    text = value.lower().strip()
    text = text.replace("−", "-").replace("–", "-")
    text = text.replace("√", "sqrt")
    text = re.sub(r"sqrt\s*\(", "sqrt(", text)
    text = re.sub(r"\\sqrt\s*\{([^}]+)\}", r"sqrt(\1)", text)
    text = re.sub(r"\\frac\s*\{([^}]+)\}\s*\{([^}]+)\}", r"(\1)/(\2)", text)
    text = text.replace("$", "").replace("\\", "")
    text = re.sub(r"\s+", "", text)
    return text


def _clean_answer_value(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^[:=\-\s]+", "", text)
    # Stop before the next numbered / T- token if glued on one line.
    text = re.split(
        r"(?i)\s+(?:t-?\d+\b|(?:problem|q|part|team)\s*\d+\s*[.):=\-])",
        text,
        maxsplit=1,
    )[0]
    text = text.strip(" ;,|")
    return text.strip()


def parse_numbered_answers(submission: str) -> dict[str, str]:
    """Parse contest answer sheets in several common agent formats.

    Supports:
      - ``1. ans`` / ``1) ans`` / ``Problem 1: ans`` (line-oriented)
      - ``T-1 ans`` / ``T1: ans`` / ``Team 1 - ans`` tokens
      - inline ``1. a 2. b`` on one line
      - ordered ``a; b; c`` lists when no ids are present
    """
    text = (submission or "").strip()
    if not text:
        return {}

    answers: dict[str, str] = {}

    # 1) Line-oriented classic numbering
    for match in ANSWER_LINE_RE.finditer(text):
        answers[match.group(1)] = _clean_answer_value(match.group(2))

    # 2) T-/Team- tokens (may be space-separated on one line)
    if re.search(r"(?i)\bT-?\d+\b|\bTeam\s*\d+\b", text):
        parts = re.split(r"(?i)(?=\b(?:T-?\d+\b|Team\s*\d+\b))", text)
        for part in parts:
            m = re.match(
                r"(?i)^\s*(?:T-?|Team\s*)(\d+)\s*[.):=\-]?\s*(.*)$",
                part.strip(),
                re.S,
            )
            if not m:
                continue
            val = _clean_answer_value(m.group(2))
            if val:
                answers[m.group(1)] = val

    # 3) Inline "1. ... 2. ..." if still sparse
    if len(answers) < 2:
        spans = list(INLINE_NUM_RE.finditer(text))
        for i, match in enumerate(spans):
            start = match.end()
            end = spans[i + 1].start() if i + 1 < len(spans) else len(text)
            val = _clean_answer_value(text[start:end])
            if val:
                answers[match.group(1)] = val

    # 4) Ordered semicolon / pipe / newline list with no ids
    if not answers:
        chunks = [c.strip() for c in re.split(r"[;\n|]+", text) if c.strip()]
        if len(chunks) >= 3:
            for idx, chunk in enumerate(chunks, start=1):
                chunk = re.sub(r"^\d+\s*[.):=\-]\s*", "", chunk).strip()
                if chunk:
                    answers[str(idx)] = chunk

    # 5) Ordered comma list of short tokens (last resort)
    if not answers:
        chunks = [c.strip() for c in text.split(",") if c.strip()]
        if len(chunks) >= 5 and all(len(c) <= 40 for c in chunks):
            for idx, chunk in enumerate(chunks, start=1):
                answers[str(idx)] = chunk

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
                    match_mode=str(
                        item.get("match_mode")
                        or ("normalized" if item.get("expected") else "reference_llm")
                    ),
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
        if (
            norm_expected == norm_actual
            or norm_expected in norm_actual
            or norm_actual in norm_expected
        ):
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
            part
            for part in self.parts
            if part.expected
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
            part.id for part in self.parts if part.id not in {g.id for g in gradeable}
        ]
        if skipped:
            warnings.append(
                "Skipped parts without curated short answers (use rubric_llm_v1): "
                + ", ".join(skipped)
            )

        if not parsed:
            warnings.append(
                "Could not parse numbered answers "
                "(expected '1. ...', 'T-1 ...', or semicolon-separated values)."
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
            prompt_version="deterministic_gold_v2",
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
                "parsed_answer_ids": sorted(
                    parsed, key=lambda x: int(x) if x.isdigit() else x
                ),
                "skipped_part_ids": skipped,
            },
        )
        result.validate(rubric)
        return result
