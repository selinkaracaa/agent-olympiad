"""Data model for ``ao.icpc-package/v1`` judging."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

TestScope = Literal["sample", "secret"]
Verdict = Literal[
    "AC", "WA", "TLE", "MLE", "OLE", "RE", "CE", "NO_TESTS", "JUDGE_ERROR"
]


class JudgeError(ValueError):
    """An invalid package or trusted judge configuration."""


@dataclass(frozen=True)
class Limits:
    time_ms: int
    memory_mb: int
    output_kb: int


@dataclass(frozen=True)
class TestCase:
    name: str
    input_path: Path
    answer_path: Path
    scope: TestScope = "secret"
    group: str = "secret"


@dataclass(frozen=True)
class TestGroup:
    id: str
    scope: TestScope
    tests: tuple[TestCase, ...]


@dataclass(frozen=True)
class Subtask:
    id: str
    points: float
    groups: tuple[str, ...]
    min_score: float | None = None


@dataclass(frozen=True)
class ProblemPackage:
    problem_id: str
    root: Path
    limits: Limits
    checker: dict[str, Any]
    groups: tuple[TestGroup, ...]
    subtasks: tuple[Subtask, ...]
    images: dict[str, str] = field(default_factory=dict)

    @property
    def time_limit_ms(self) -> int:
        return self.limits.time_ms

    @property
    def memory_limit_mb(self) -> int:
        return self.limits.memory_mb

    @property
    def output_limit_kb(self) -> int:
        return self.limits.output_kb

    @property
    def image(self) -> str:
        return self.images.get("python3", "python:3.12-slim")

    @property
    def tests(self) -> tuple[TestCase, ...]:
        return tuple(test for group in self.groups for test in group.tests)

    def tests_for(self, scope: TestScope) -> tuple[TestCase, ...]:
        return tuple(
            test
            for group in self.groups
            if group.scope == scope
            for test in group.tests
        )


@dataclass(frozen=True)
class CaseResult:
    name: str
    verdict: Verdict
    detail: str = ""
    scope: TestScope = "secret"
    group: str = "secret"
    time_ms: int | None = None
    memory_kb: int | None = None

    def to_dict(self) -> dict[str, Any]:
        # Intentionally contains neither test input nor expected output.
        return asdict(self)


@dataclass(frozen=True)
class SubtaskResult:
    id: str
    points: float
    max_points: float
    passed: int
    total: int


@dataclass(frozen=True)
class JudgeResult:
    problem_id: str
    language: str
    test_scope: TestScope
    verdict: Verdict
    graded: bool
    score: float | None
    max_score: float | None
    cases: tuple[CaseResult, ...] = ()
    subtasks: tuple[SubtaskResult, ...] = ()
    compile_output: str = ""
    reason: str = ""
    backend: str = ""
    grading_scope_label: str = ""

    @property
    def passed(self) -> int:
        return sum(case.verdict == "AC" for case in self.cases)

    @property
    def total(self) -> int:
        return len(self.cases)

    @property
    def tests(self) -> tuple[CaseResult, ...]:
        return self.cases

    @property
    def wrong_submission(self) -> bool:
        return self.verdict in {"WA", "TLE", "MLE", "RE", "CE"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluator_id": "programming_judge",
            "problem_id": self.problem_id,
            "language": self.language,
            "test_scope": self.test_scope,
            "grading_scope_label": self.grading_scope_label,
            "verdict": self.verdict,
            "graded": self.graded,
            "score": self.score,
            "total_score": self.score,
            "max_score": self.max_score,
            "correct": self.verdict == "AC",
            "passed": self.passed,
            "total": self.total,
            "cases": [case.to_dict() for case in self.cases],
            "tests": [case.to_dict() for case in self.cases],
            "subtasks": [asdict(subtask) for subtask in self.subtasks],
            "compile_output": self.compile_output,
            "reason": self.reason,
            "backend": self.backend,
            "wrong_submission": self.wrong_submission,
        }

    def to_grade_dict(self, *, submitted_by: str | None = None) -> dict[str, Any]:
        method = (
            "programming_sample_judge"
            if self.grading_scope_label == "sample-only"
            else "programming_judge"
        )
        return {**self.to_dict(), "method": method, "submitted_by": submitted_by}
