from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from evaluation.programming import (  # noqa: E402
    DockerProgrammingJudge,
    ProgrammingJudgeError,
    check_output,
    load_problem_package,
)


def write_package(root: Path) -> Path:
    package = root / "problem"
    tests = package / "tests"
    tests.mkdir(parents=True)
    (package / "package.json").write_text(
        json.dumps(
            {
                "schema_version": "ao.icpc-package/v1",
                "problem_id": "demo",
                "time_limit_ms": 1000,
                "memory_limit_mb": 128,
                "output_limit_kb": 64,
                "image": "python:3.12-slim",
                "checker": {"type": "token"},
                "tests": "tests",
            }
        ),
        encoding="utf-8",
    )
    (tests / "001.in").write_text("2\n", encoding="utf-8")
    (tests / "001.ans").write_text("4\n", encoding="utf-8")
    return package


class OutputCheckerTests(unittest.TestCase):
    def test_token_checker_ignores_whitespace(self):
        self.assertTrue(check_output("a  2\n", "a\n2 ", {"type": "token"})[0])

    def test_float_checker_honors_tolerance(self):
        checker = {
            "type": "float",
            "absolute_tolerance": 0.01,
            "relative_tolerance": 0.0,
        }
        self.assertTrue(check_output("Case 1: 3.14", "Case 1: 3.145", checker)[0])
        self.assertFalse(check_output("Case 1: 3.14", "Case 1: 3.16", checker)[0])


class ProblemPackageTests(unittest.TestCase):
    def test_loads_test_pairs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = load_problem_package(write_package(Path(temp_dir)))
            self.assertEqual(package.problem_id, "demo")
            self.assertEqual([test.name for test in package.tests], ["001"])

    def test_rejects_test_directory_outside_package(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package = write_package(root)
            manifest = json.loads((package / "package.json").read_text(encoding="utf-8"))
            manifest["tests"] = "../outside"
            (package / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "outside").mkdir()
            with self.assertRaises(ProgrammingJudgeError):
                load_problem_package(package)

    def test_bottles_package_is_hidden_and_loadable(self):
        package_path = (
            REPO_ROOT / "data/private/icpc/icpc_wf_2012_bottles"
        )
        package = load_problem_package(package_path)
        self.assertEqual(package.problem_id, "icpc_wf_2012_bottles")
        self.assertGreaterEqual(len(package.tests), 3)

        reference = json.loads(
            (
                REPO_ROOT
                / "data/last_exam/tasks/icpc/icpc_wf_2012_bottles/eval/reference.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(reference["visibility"], "hidden_until_grade")
        self.assertEqual(reference["problem_package"], package_path.relative_to(REPO_ROOT).as_posix())
        task_input = REPO_ROOT / "data/last_exam/tasks/icpc/icpc_wf_2012_bottles/base/input"
        self.assertFalse(any(path.suffix in {".in", ".ans"} for path in task_input.iterdir()))


class DockerJudgeTests(unittest.TestCase):
    def test_accepts_matching_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            judge = DockerProgrammingJudge(load_problem_package(write_package(root)))
            submission = root / "solution.py"
            submission.write_text("print(4)\n", encoding="utf-8")
            completed = subprocess.CompletedProcess(
                args=["docker"], returncode=0, stdout="4\n", stderr=""
            )
            with (
                patch.object(judge, "available", return_value=True),
                patch("evaluation.programming.subprocess.run", return_value=completed) as run,
            ):
                result = judge.evaluate(submission, language="python3")
            self.assertEqual(result.verdict, "AC")
            command = run.call_args.args[0]
            self.assertIn("none", command)
            self.assertIn("no-new-privileges", command)
            self.assertIn("readonly", command[-7])

    def test_reports_wrong_answer_and_timeout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            judge = DockerProgrammingJudge(load_problem_package(write_package(root)))
            submission = root / "solution.py"
            submission.write_text("print(0)\n", encoding="utf-8")
            with (
                patch.object(judge, "available", return_value=True),
                patch(
                    "evaluation.programming.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        args=["docker"], returncode=0, stdout="0\n", stderr=""
                    ),
                ),
            ):
                self.assertEqual(judge.evaluate(submission, language="python3").verdict, "WA")
            with (
                patch.object(judge, "available", return_value=True),
                patch(
                    "evaluation.programming.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        args=["docker"], returncode=124, stdout="", stderr=""
                    ),
                ),
            ):
                self.assertEqual(judge.evaluate(submission, language="python3").verdict, "TLE")


if __name__ == "__main__":
    unittest.main()
