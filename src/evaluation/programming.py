"""Docker-isolated evaluator for ICPC-style programming submissions."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class ProgrammingJudgeError(RuntimeError):
    """Raised when a problem package or judge environment is invalid."""


@dataclass(frozen=True)
class TestCase:
    name: str
    input_path: Path
    answer_path: Path


@dataclass(frozen=True)
class ProblemPackage:
    problem_id: str
    root: Path
    time_limit_ms: int
    memory_limit_mb: int
    output_limit_kb: int
    image: str
    checker: dict[str, Any]
    tests: tuple[TestCase, ...]


@dataclass(frozen=True)
class TestResult:
    name: str
    verdict: str
    detail: str = ""


@dataclass(frozen=True)
class ProgrammingJudgeResult:
    evaluator_id: str
    problem_id: str
    language: str
    verdict: str
    passed: int
    total: int
    tests: tuple[TestResult, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["total_score"] = 1 if self.verdict == "AC" else 0
        payload["max_score"] = 1
        return payload


def load_problem_package(path: str | Path) -> ProblemPackage:
    root = Path(path).resolve()
    manifest_path = root / "package.json"
    if not manifest_path.is_file():
        raise ProgrammingJudgeError(f"Missing problem package manifest: {manifest_path}")
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "ao.icpc-package/v1":
        raise ProgrammingJudgeError("Unsupported ICPC package schema.")

    tests_root = (root / str(raw.get("tests", "tests"))).resolve()
    if root not in tests_root.parents or not tests_root.is_dir():
        raise ProgrammingJudgeError("Problem test directory is missing or escapes package root.")
    tests = []
    for input_path in sorted(tests_root.glob("*.in")):
        answer_path = input_path.with_suffix(".ans")
        if not answer_path.is_file():
            raise ProgrammingJudgeError(f"Missing answer for {input_path.name}.")
        tests.append(TestCase(input_path.stem, input_path, answer_path))
    if not tests:
        raise ProgrammingJudgeError("Problem package contains no tests.")

    return ProblemPackage(
        problem_id=str(raw["problem_id"]),
        root=root,
        time_limit_ms=int(raw["time_limit_ms"]),
        memory_limit_mb=int(raw["memory_limit_mb"]),
        output_limit_kb=int(raw.get("output_limit_kb", 1024)),
        image=str(raw.get("image", "python:3.12-slim")),
        checker=dict(raw.get("checker") or {"type": "token"}),
        tests=tuple(tests),
    )


def check_output(expected: str, actual: str, checker: dict[str, Any]) -> tuple[bool, str]:
    """Compare token streams, allowing configured tolerance for numeric tokens."""
    checker_type = str(checker.get("type", "token"))
    if checker_type == "exact":
        ok = expected == actual
        return ok, "" if ok else "exact output mismatch"
    if checker_type not in {"token", "float"}:
        raise ProgrammingJudgeError(f"Unsupported checker type: {checker_type}")

    expected_tokens = expected.split()
    actual_tokens = actual.split()
    if len(expected_tokens) != len(actual_tokens):
        return False, (
            f"token count mismatch: expected {len(expected_tokens)}, "
            f"received {len(actual_tokens)}"
        )

    absolute = float(checker.get("absolute_tolerance", 0.0))
    relative = float(checker.get("relative_tolerance", 0.0))
    for index, (wanted, received) in enumerate(
        zip(expected_tokens, actual_tokens), start=1
    ):
        if wanted == received:
            continue
        if checker_type == "float":
            try:
                wanted_number = float(wanted)
                received_number = float(received)
            except ValueError:
                pass
            else:
                if math.isfinite(received_number) and math.isclose(
                    wanted_number,
                    received_number,
                    rel_tol=relative,
                    abs_tol=absolute,
                ):
                    continue
        return False, f"token {index} mismatch"
    return True, ""


class DockerProgrammingJudge:
    """Run Python submissions with no network and constrained container resources."""

    evaluator_id = "programming_judge"

    def __init__(self, package: ProblemPackage):
        self.package = package

    @staticmethod
    def available() -> bool:
        if shutil.which("docker") is None:
            return False
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def evaluate(self, submission: str | Path, *, language: str) -> ProgrammingJudgeResult:
        source = Path(submission).resolve()
        if language != "python3":
            raise ProgrammingJudgeError("Pilot judge currently supports only python3.")
        if not source.is_file():
            raise ProgrammingJudgeError(f"Submission does not exist: {source}")
        if not self.available():
            raise ProgrammingJudgeError(
                "Docker is unavailable; refusing to execute an untrusted submission on the host."
            )

        results = []
        for test in self.package.tests:
            result = self._run_test(source, test)
            results.append(result)
            if result.verdict != "AC":
                break
        passed = sum(result.verdict == "AC" for result in results)
        verdict = next(
            (result.verdict for result in results if result.verdict != "AC"),
            "AC",
        )
        return ProgrammingJudgeResult(
            evaluator_id=self.evaluator_id,
            problem_id=self.package.problem_id,
            language=language,
            verdict=verdict,
            passed=passed,
            total=len(self.package.tests),
            tests=tuple(results),
        )

    def _run_test(self, source: Path, test: TestCase) -> TestResult:
        timeout_seconds = max(1, math.ceil(self.package.time_limit_ms / 1000))
        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "64",
            "--memory",
            f"{self.package.memory_limit_mb}m",
            "--cpus",
            "1",
            "--user",
            "65534:65534",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--mount",
            f"type=bind,source={source},target=/submission/main.py,readonly",
            self.package.image,
            "timeout",
            f"{timeout_seconds}s",
            "python3",
            "-I",
            "/submission/main.py",
        ]
        try:
            process = subprocess.run(
                command,
                input=test.input_path.read_text(encoding="utf-8"),
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 10,
            )
        except subprocess.TimeoutExpired:
            return TestResult(test.name, "JUDGE_ERROR", "Docker command did not terminate.")

        output_bytes = len(process.stdout.encode("utf-8", errors="replace"))
        if output_bytes > self.package.output_limit_kb * 1024:
            return TestResult(test.name, "OLE", "Output limit exceeded.")
        if process.returncode == 124:
            return TestResult(test.name, "TLE", "Time limit exceeded.")
        if process.returncode == 137:
            return TestResult(test.name, "MLE", "Container exceeded its memory limit.")
        if process.returncode == 139:
            return TestResult(test.name, "RE", "Process terminated by segmentation fault.")
        if process.returncode != 0:
            return TestResult(test.name, "RE", f"Process exited with {process.returncode}.")

        expected = test.answer_path.read_text(encoding="utf-8")
        accepted, detail = check_output(expected, process.stdout, self.package.checker)
        return TestResult(test.name, "AC" if accepted else "WA", detail)
