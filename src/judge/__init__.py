"""Consolidated programming judge public API."""

from .checkers import check_output
from .core import run_submission
from .models import (
    CaseResult,
    JudgeError,
    JudgeResult,
    Limits,
    ProblemPackage,
    Subtask,
    SubtaskResult,
    TestCase,
    TestGroup,
)
from .package import load_problem_package, package_from_sample_directory
from .remote import RemoteRun, RemoteSubmitRequest
from .runners import BackendUnavailable, DockerProgrammingJudge, NativePythonRunner

# Compatibility names from evaluation.programming.
ProgrammingJudgeError = JudgeError
ProgrammingJudgeResult = JudgeResult
TestResult = CaseResult

__all__ = [
    "BackendUnavailable",
    "CaseResult",
    "DockerProgrammingJudge",
    "JudgeError",
    "JudgeResult",
    "Limits",
    "NativePythonRunner",
    "ProblemPackage",
    "ProgrammingJudgeError",
    "ProgrammingJudgeResult",
    "RemoteRun",
    "RemoteSubmitRequest",
    "Subtask",
    "SubtaskResult",
    "TestCase",
    "TestGroup",
    "TestResult",
    "check_output",
    "load_problem_package",
    "package_from_sample_directory",
    "run_submission",
]
