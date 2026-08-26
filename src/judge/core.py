"""Public judge orchestration API."""

from __future__ import annotations

from pathlib import Path

from .models import (
    CaseResult,
    JudgeResult,
    ProblemPackage,
    SubtaskResult,
    TestScope,
)
from .package import load_problem_package
from .runners import BackendUnavailable, DockerProgrammingJudge, NativePythonRunner

_VERDICT_ORDER = {
    "AC": 0,
    "WA": 1,
    "RE": 2,
    "TLE": 3,
    "MLE": 4,
    "OLE": 5,
    "CE": 6,
    "JUDGE_ERROR": 7,
}


def _secret_safe(case: CaseResult) -> CaseResult:
    if case.scope != "secret" or not case.detail:
        return case
    messages = {
        "WA": "Output did not match.",
        "RE": "Runtime error.",
        "TLE": "Time limit exceeded.",
        "MLE": "Memory limit exceeded.",
        "OLE": "Output limit exceeded.",
        "JUDGE_ERROR": "Judge failed while running this case.",
    }
    return CaseResult(
        name=case.name,
        verdict=case.verdict,
        scope=case.scope,
        group=case.group,
        time_ms=case.time_ms,
        memory_kb=case.memory_kb,
        detail=messages.get(case.verdict, ""),
    )


def _subtask_results(
    package: ProblemPackage,
    scope: TestScope,
    cases: tuple[CaseResult, ...],
) -> tuple[SubtaskResult, ...]:
    selected_groups = {group.id for group in package.groups if group.scope == scope}
    results: list[SubtaskResult] = []
    for subtask in package.subtasks:
        relevant_groups = set(subtask.groups) & selected_groups
        relevant = [case for case in cases if case.group in relevant_groups]
        if not relevant:
            continue
        passed = sum(case.verdict == "AC" for case in relevant)
        ratio = passed / len(relevant)
        if subtask.min_score is None:
            points = subtask.points if passed == len(relevant) else 0.0
        else:
            points = subtask.points * ratio if ratio >= subtask.min_score else 0.0
        results.append(
            SubtaskResult(subtask.id, points, subtask.points, passed, len(relevant))
        )
    return tuple(results)


def build_result(
    package: ProblemPackage,
    language: str,
    scope: TestScope,
    cases: tuple[CaseResult, ...],
    *,
    compile_output: str = "",
    backend: str = "",
) -> JudgeResult:
    if compile_output and not cases:
        return JudgeResult(
            package.problem_id,
            language,
            scope,
            "CE",
            True,
            0.0,
            sum(
                subtask.points
                for subtask in package.subtasks
                if set(subtask.groups)
                & {group.id for group in package.groups if group.scope == scope}
            ),
            compile_output=compile_output,
            reason="Compilation failed.",
            backend=backend,
            grading_scope_label="official-secret" if scope == "secret" else "sample-only",
        )
    safe_cases = tuple(_secret_safe(case) for case in cases)
    subtasks = _subtask_results(package, scope, safe_cases)
    score = sum(subtask.points for subtask in subtasks)
    max_score = sum(subtask.max_points for subtask in subtasks)
    verdict = (
        "AC"
        if all(case.verdict == "AC" for case in safe_cases)
        else max(safe_cases, key=lambda case: _VERDICT_ORDER[case.verdict]).verdict
    )
    return JudgeResult(
        package.problem_id,
        language,
        scope,
        verdict,
        verdict != "JUDGE_ERROR",
        score if verdict != "JUDGE_ERROR" else None,
        max_score if verdict != "JUDGE_ERROR" else None,
        cases=safe_cases,
        subtasks=subtasks,
        compile_output=compile_output,
        reason=f"{sum(case.verdict == 'AC' for case in safe_cases)}/{len(safe_cases)} cases AC",
        backend=backend,
        grading_scope_label="official-secret" if scope == "secret" else "sample-only",
    )


def run_submission(
    package: ProblemPackage | str | Path,
    source: str,
    language: str,
    test_scope: TestScope | str,
) -> JudgeResult:
    """Run source against exactly one package scope.

    Python is a trusted host-only smoke backend. C++17 always uses Docker and
    fails closed when Docker is unavailable.
    """
    loaded = (
        load_problem_package(package)
        if isinstance(package, (str, Path))
        else package
    )
    scope = str(test_scope).lower()
    if scope not in {"sample", "secret"}:
        raise ValueError("test_scope must be SAMPLE or SECRET.")
    typed_scope: TestScope = scope  # type: ignore[assignment]
    tests = loaded.tests_for(typed_scope)
    canonical_language = language.lower().replace("+", "p")
    aliases = {
        "python": "python3",
        "py": "python3",
        "python3": "python3",
        "cpp": "cpp17",
        "cpp17": "cpp17",
        "cppp17": "cpp17",
        "c++17": "cpp17",
    }
    canonical_language = aliases.get(language.lower(), aliases.get(canonical_language, ""))
    if not canonical_language:
        return JudgeResult(
            loaded.problem_id,
            language,
            typed_scope,
            "CE",
            True,
            0.0,
            None,
            reason=f"Unsupported language: {language}",
            grading_scope_label="official-secret" if scope == "secret" else "sample-only",
        )
    if not tests:
        return JudgeResult(
            loaded.problem_id,
            canonical_language,
            typed_scope,
            "NO_TESTS",
            False,
            None,
            None,
            reason=f"Package has no {scope} tests.",
            grading_scope_label="official-secret" if scope == "secret" else "sample-only",
        )
    if canonical_language == "python3":
        runner = NativePythonRunner()
        cases, compile_output = runner.run(loaded, source, tests)
        return build_result(
            loaded,
            canonical_language,
            typed_scope,
            cases,
            compile_output=compile_output,
            backend=runner.name,
        )
    runner = DockerProgrammingJudge(loaded)
    try:
        cases, compile_output = runner.run(source, tests)
    except BackendUnavailable as exc:
        return JudgeResult(
            loaded.problem_id,
            canonical_language,
            typed_scope,
            "JUDGE_ERROR",
            False,
            None,
            None,
            reason=str(exc),
            backend=runner.name,
            grading_scope_label="official-secret" if scope == "secret" else "sample-only",
        )
    return build_result(
        loaded,
        canonical_language,
        typed_scope,
        cases,
        compile_output=compile_output,
        backend=runner.name,
    )
