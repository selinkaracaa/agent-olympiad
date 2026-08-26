"""Execution backends for trusted Python smoke tests and isolated C++17."""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .checkers import check_output
from .models import CaseResult, JudgeError, ProblemPackage, TestCase


class BackendUnavailable(JudgeError):
    """The requested sandbox is unavailable; the submission was not run."""


def _detail(stderr: str, fallback: str) -> str:
    cleaned = stderr.strip()
    return cleaned[:2000] if cleaned else fallback


class NativePythonRunner:
    """Host CPython runner for trusted tests/smoke only."""

    name = "native-python-trusted"

    def run(
        self, package: ProblemPackage, source: str, tests: tuple[TestCase, ...]
    ) -> tuple[tuple[CaseResult, ...], str]:
        try:
            compile(source, "<submission>", "exec")
        except SyntaxError as exc:
            return (), f"{exc.__class__.__name__}: {exc.msg} (line {exc.lineno})"

        results: list[CaseResult] = []
        with tempfile.TemporaryDirectory(prefix="ao_python_") as temp:
            script = Path(temp) / "main.py"
            script.write_text(source, encoding="utf-8")
            for test in tests:
                results.append(self._run_case(package, script, test, Path(temp)))
        return tuple(results), ""

    def _run_case(
        self, package: ProblemPackage, script: Path, test: TestCase, cwd: Path
    ) -> CaseResult:
        output_path = cwd / "stdout.bin"
        started = time.monotonic()
        with test.input_path.open("rb") as stdin, output_path.open("wb") as stdout:
            try:
                process = subprocess.run(
                    [sys.executable, "-I", str(script)],
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.PIPE,
                    timeout=package.limits.time_ms / 1000,
                    cwd=cwd,
                )
            except subprocess.TimeoutExpired:
                return CaseResult(
                    test.name, "TLE", scope=test.scope, group=test.group,
                    time_ms=package.limits.time_ms,
                    detail="Time limit exceeded.",
                )
            except OSError as exc:
                return CaseResult(
                    test.name, "JUDGE_ERROR", scope=test.scope, group=test.group,
                    detail=f"Python backend failed: {exc}",
                )
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if output_path.stat().st_size > package.limits.output_kb * 1024:
            return CaseResult(
                test.name, "OLE", scope=test.scope, group=test.group,
                time_ms=elapsed_ms,
                detail="Output limit exceeded.",
            )
        stderr = (process.stderr or b"").decode("utf-8", errors="replace")
        if process.returncode != 0:
            return CaseResult(
                test.name, "RE", scope=test.scope, group=test.group,
                time_ms=elapsed_ms,
                detail=_detail(stderr, f"Process exited with {process.returncode}."),
            )
        actual = output_path.read_text(encoding="utf-8", errors="replace")
        expected = test.answer_path.read_text(encoding="utf-8", errors="replace")
        try:
            accepted, detail = check_output(
                expected, actual, package.checker, input_path=test.input_path
            )
        except JudgeError as exc:
            return CaseResult(
                test.name, "JUDGE_ERROR", scope=test.scope, group=test.group,
                time_ms=elapsed_ms,
                detail=str(exc),
            )
        return CaseResult(
            test.name,
            "AC" if accepted else "WA",
            scope=test.scope,
            group=test.group,
            time_ms=elapsed_ms,
            detail=detail,
        )


class DockerProgrammingJudge:
    """Compile and execute C++17 submissions in hardened Docker containers."""

    evaluator_id = "programming_judge"
    name = "docker-cpp17"

    def __init__(self, package: ProblemPackage):
        self.package = package

    @staticmethod
    def available() -> bool:
        if shutil.which("docker") is None:
            return False
        try:
            process = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return process.returncode == 0

    def _security_flags(self) -> list[str]:
        return [
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--pids-limit", "64",
            "--memory", f"{self.package.limits.memory_mb}m",
            "--cpus", "1",
            "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        ]

    def build_compile_command(self, source: Path, build_dir: Path) -> list[str]:
        return [
            "docker", "run", "--rm", *self._security_flags(),
            "--mount", f"type=bind,source={source.resolve()},target=/submission/main.cpp,readonly",
            "--mount", f"type=bind,source={build_dir.resolve()},target=/work",
            "--workdir", "/work",
            self.package.images.get("cpp17", "gcc:14"),
            "g++", "-std=c++17", "-O2", "-pipe", "-o", "main", "/submission/main.cpp",
        ]

    def build_run_command(self, executable: Path) -> list[str]:
        timeout_seconds = max(1, math.ceil(self.package.limits.time_ms / 1000))
        return [
            "docker", "run", "--rm", *self._security_flags(),
            "--mount", f"type=bind,source={executable.resolve()},target=/submission/main,readonly",
            self.package.images.get("cpp17", "gcc:14"),
            "timeout", f"{timeout_seconds}s", "/submission/main",
        ]

    def run(
        self, source: str, tests: tuple[TestCase, ...]
    ) -> tuple[tuple[CaseResult, ...], str]:
        if not self.available():
            raise BackendUnavailable(
                "Docker backend unavailable; C++ was not executed on the host."
            )
        with tempfile.TemporaryDirectory(prefix="ao_cpp_") as temp:
            work = Path(temp)
            source_path = work / "main.cpp"
            build = work / "build"
            build.mkdir()
            source_path.write_text(source, encoding="utf-8")
            source_path.chmod(0o444)
            build.chmod(0o777)
            compile_process = subprocess.run(
                self.build_compile_command(source_path, build),
                capture_output=True,
                text=True,
                timeout=max(30, math.ceil(self.package.limits.time_ms / 1000) * 5),
            )
            compile_output = (
                (compile_process.stdout or "") + (compile_process.stderr or "")
            )[:4000]
            if compile_process.returncode != 0:
                return (), compile_output or "C++17 compilation failed."
            executable = build / "main"
            results = tuple(self._run_case(executable, test) for test in tests)
            return results, ""

    def _run_case(self, executable: Path, test: TestCase) -> CaseResult:
        timeout_seconds = max(1, math.ceil(self.package.limits.time_ms / 1000))
        started = time.monotonic()
        try:
            process = subprocess.run(
                self.build_run_command(executable),
                input=test.input_path.read_text(encoding="utf-8", errors="replace"),
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 10,
            )
        except subprocess.TimeoutExpired:
            return CaseResult(
                test.name, "JUDGE_ERROR", scope=test.scope, group=test.group,
                detail="Docker command did not terminate.",
            )
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if len((process.stdout or "").encode("utf-8", errors="replace")) > (
            self.package.limits.output_kb * 1024
        ):
            verdict, detail = "OLE", "Output limit exceeded."
        elif process.returncode == 124:
            verdict, detail = "TLE", "Time limit exceeded."
        elif process.returncode == 137:
            verdict, detail = "MLE", "Container exceeded its memory limit."
        elif process.returncode != 0:
            verdict, detail = "RE", f"Process exited with {process.returncode}."
        else:
            expected = test.answer_path.read_text(encoding="utf-8", errors="replace")
            try:
                accepted, detail = check_output(
                    expected,
                    process.stdout or "",
                    self.package.checker,
                    input_path=test.input_path,
                )
                verdict = "AC" if accepted else "WA"
            except JudgeError as exc:
                verdict, detail = "JUDGE_ERROR", str(exc)
        return CaseResult(
            test.name, verdict, scope=test.scope, group=test.group,
            time_ms=elapsed_ms,
            detail=detail,
        )

    def evaluate(self, submission: str | Path, *, language: str):
        """Compatibility API retained for callers of evaluation.programming."""
        source_path = Path(submission)
        if language not in {"cpp17", "c++17", "cpp"}:
            raise JudgeError("DockerProgrammingJudge supports C++17.")
        results, compile_output = self.run(
            source_path.read_text(encoding="utf-8"), self.package.tests
        )
        from .core import build_result

        return build_result(
            self.package,
            "cpp17",
            "secret",
            results,
            compile_output=compile_output,
            backend=self.name,
        )
