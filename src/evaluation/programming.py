"""Compatibility imports for the consolidated :mod:`judge` package."""

from judge import (  # noqa: F401
    DockerProgrammingJudge,
    ProblemPackage,
    ProgrammingJudgeError,
    ProgrammingJudgeResult,
    TestCase,
    TestResult,
    check_output,
    load_problem_package,
    run_submission,
)

__all__ = [
    "DockerProgrammingJudge",
    "ProblemPackage",
    "ProgrammingJudgeError",
    "ProgrammingJudgeResult",
    "TestCase",
    "TestResult",
    "check_output",
    "load_problem_package",
    "run_submission",
]
