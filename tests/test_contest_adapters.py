from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_adapters import (  # noqa: E402
    EnvironmentTaskExecutor,
    grade_contest_result,
    run_sample_report,
)
from contest_manifest import ContestManifest, ManifestTask, load_contest_manifest  # noqa: E402


def _programming_task(problem_id: str) -> ManifestTask:
    return ManifestTask(
        problem_id,
        problem_id,
        None,
        "Double the input.",
        "algorithmic_programming",
        1,
        True,
        {"problem_id": problem_id, "time_limit_ms": 2000},
    )


def _write_samples(root: Path, competition: str, problem_id: str) -> None:
    samples = root / "data" / "benchmarks" / competition / "samples" / problem_id
    samples.mkdir(parents=True)
    (samples / "1.in").write_text("21\n", encoding="utf-8")
    (samples / "1.ans").write_text("42\n", encoding="utf-8")
    (samples / "2.in").write_text("5\n", encoding="utf-8")
    (samples / "2.ans").write_text("10\n", encoding="utf-8")


class _NoRemoteEnvironment:
    def execute_action(self, *_args, **_kwargs):
        raise AssertionError("remote judge must not be called when samples fail")


class ContestAdapterTests(unittest.TestCase):
    def test_grades_latest_math_answers_per_task(self) -> None:
        benchmark = {
            "problem_id": "packet",
            "gold_label": {
                "parts": [
                    {"id": "1", "expected": "42", "points": 2, "aliases": []},
                    {"id": "2", "expected": "yes", "points": 3, "aliases": ["Y"]},
                ]
            },
        }
        manifest = ContestManifest(
            "packet",
            "math",
            (
                ManifestTask("packet:1", "packet", "1", "Q1", "team_contest", 2, False, benchmark),
                ManifestTask("packet:2", "packet", "2", "Q2", "team_contest", 3, False, benchmark),
            ),
        )

        grade = grade_contest_result(
            manifest,
            {"submissions": {"packet:1": "42", "packet:2": "wrong"}},
        )

        self.assertEqual(grade["score"], 2.0)
        self.assertEqual(grade["max_score"], 5.0)
        self.assertEqual(grade["task_utility"], 0.5)

    def test_grades_explicit_final_answer_inside_math_derivation(self) -> None:
        benchmark = {
            "problem_id": "packet",
            "gold_label": {
                "parts": [
                    {
                        "id": "1",
                        "expected": "48.5",
                        "points": 4,
                        "aliases": ["97/2"],
                    }
                ]
            },
        }
        manifest = ContestManifest(
            "packet",
            "math",
            (
                ManifestTask(
                    "packet:1",
                    "packet",
                    "1",
                    "Q1",
                    "team_contest",
                    4,
                    False,
                    benchmark,
                ),
            ),
        )

        grade = grade_contest_result(
            manifest,
            {
                "submissions": {
                    "packet:1": (
                        "The middle divisors are 30 and 67.\n"
                        "Final answer: 97/2."
                    )
                }
            },
        )

        self.assertEqual(grade["score"], 4.0)

    def test_programming_utility_uses_ac_state_not_latest_text(self) -> None:
        benchmark = {"problem_id": "a"}
        manifest = ContestManifest(
            "icpc",
            "icpc",
            (ManifestTask("a", "a", None, "A", "algorithmic_programming", 1, True, benchmark),),
        )
        grade = grade_contest_result(
            manifest,
            {
                "submissions": {"a": "some code"},
                "tasks": {"a": {"state": "blocked", "score": 0.0}},
            },
        )
        self.assertEqual(grade["score"], 0.0)
        self.assertEqual(grade["max_score"], 1.0)
        self.assertEqual(grade["task_utility"], 0.0)

    def test_local_sample_verdict_is_evidence_not_official_ac(self) -> None:
        manifest = load_contest_manifest(
            REPO_ROOT / "data" / "contest_manifests" / "icpc_wf_2012_5.json",
            benchmark_root=REPO_ROOT / "data" / "benchmarks",
        )
        result = EnvironmentTaskExecutor(
            manifest,
            benchmark_root=REPO_ROOT / "data" / "benchmarks",
        )(
            manifest.tasks[0],
            "submit_code",
            {"code": "print(0)"},
        )
        self.assertFalse(result["valid"])
        self.assertTrue(result["verdict"].startswith("SAMPLE_"))

    def test_sample_report_marks_ac_and_explains_failures(self) -> None:
        task = _programming_task("double")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_samples(root, "icpc", "double")

            passing = run_sample_report(
                task,
                "print(int(input()) * 2)",
                competition_id="icpc",
                repo_root=root,
            )
            self.assertEqual(passing["sample_verdict"], "AC")
            self.assertEqual(
                [case["verdict"] for case in passing["sample_cases"]], ["AC", "AC"]
            )
            self.assertNotIn("expected", passing["sample_cases"][0])

            failing = run_sample_report(
                task,
                "print(int(input()) + 1)",
                competition_id="icpc",
                repo_root=root,
            )
            self.assertEqual(failing["sample_verdict"], "WA")
            first = failing["sample_cases"][0]
            self.assertEqual(first["verdict"], "WA")
            self.assertEqual(first["input"], "21")
            self.assertEqual(first["expected"], "42")
            self.assertEqual(first["actual"], "22")
            self.assertIn("0/2", failing["sample_summary"])

            missing = run_sample_report(
                _programming_task("nowhere"),
                "print(1)",
                competition_id="icpc",
                repo_root=root,
            )
            self.assertIsNone(missing["sample_verdict"])
            self.assertEqual(missing["sample_cases"], [])

    def test_execute_code_returns_sample_verdict_and_submit_short_circuits(self) -> None:
        manifest = load_contest_manifest(
            REPO_ROOT / "data" / "contest_manifests" / "icpc_wf_2012_bottles.json",
            benchmark_root=REPO_ROOT / "data" / "benchmarks",
        )
        executor = EnvironmentTaskExecutor(
            manifest,
            benchmark_root=REPO_ROOT / "data" / "benchmarks",
        )
        task = manifest.tasks[0]

        executed = executor(task, "execute_code", {"code": "print(0)"})
        self.assertTrue(executed["valid"])
        self.assertIn("Code output", executed["result"])
        self.assertEqual(executed["sample_verdict"], "WA")
        self.assertTrue(executed["sample_cases"])
        self.assertIn("expected", executed["sample_cases"][0])

        executor._environments[task.parent_problem_id] = _NoRemoteEnvironment()
        submitted = executor(task, "submit_code", {"code": "print(0)"})
        self.assertFalse(submitted["valid"])
        self.assertEqual(submitted["verdict"], "SAMPLE_WA")
        self.assertEqual(submitted["feedback"]["test_scope"], "sample")
        self.assertEqual(submitted["sample_verdict"], "WA")


if __name__ == "__main__":
    unittest.main()
