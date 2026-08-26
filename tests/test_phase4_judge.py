from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from collectors.fetch_icpc_samples import collect, extract_samples_atomic
from actions import build_action_instructions
from collaboration import _agent_user_prompt
from env import OlympiadEnvironment
from evaluation.programming_judge import judge_programming_submission
from judge import (
    DockerProgrammingJudge,
    check_output,
    load_problem_package,
    run_submission,
)


def write_package(
    root: Path,
    *,
    time_ms: int = 1000,
    output_kb: int = 8,
    subtasks: list[dict] | None = None,
) -> Path:
    for scope in ("sample", "secret"):
        directory = root / "tests" / scope
        directory.mkdir(parents=True)
        (directory / "one.in").write_text("2\n", encoding="utf-8")
        expected = "4\n" if scope == "sample" else "secret-answer\n"
        (directory / "one.ans").write_text(expected, encoding="utf-8")
    manifest = {
        "schema_version": "ao.icpc-package/v1",
        "problem_id": "demo",
        "limits": {"time_ms": time_ms, "memory_mb": 64, "output_kb": output_kb},
        "checker": {"mode": "token"},
        "groups": [
            {"id": "sample", "scope": "sample", "tests": "tests/sample"},
            {"id": "secret", "scope": "secret", "tests": "tests/secret"},
        ],
        "subtasks": subtasks
        or [
            {"id": "samples", "points": 10, "groups": ["sample"]},
            {"id": "hidden", "points": 90, "groups": ["secret"]},
        ],
    }
    (root / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


class PackageAndCheckerTests(unittest.TestCase):
    def test_package_parses_groups_limits_and_subtasks(self):
        with tempfile.TemporaryDirectory() as temp:
            package = load_problem_package(write_package(Path(temp)))
            self.assertEqual(package.time_limit_ms, 1000)
            self.assertEqual(len(package.tests_for("sample")), 1)
            self.assertEqual(package.subtasks[1].points, 90)

    def test_subtask_default_all_pass_and_min_score(self):
        subtasks = [
            {"id": "all", "points": 50, "groups": ["sample"]},
            {
                "id": "partial",
                "points": 50,
                "groups": ["sample"],
                "min_score": 0,
            },
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = write_package(Path(temp), subtasks=subtasks)
            sample = root / "tests" / "sample"
            (sample / "two.in").write_text("", encoding="utf-8")
            (sample / "two.ans").write_text("wrong\n", encoding="utf-8")
            result = run_submission(root, "print(4)", "python3", "sample")
            self.assertEqual(result.verdict, "WA")
            self.assertEqual(result.subtasks[0].points, 0)
            self.assertEqual(result.subtasks[1].points, 25)

    def test_exact_token_and_float_checkers(self):
        self.assertFalse(check_output("a\n", "a", {"mode": "exact"})[0])
        self.assertTrue(check_output("a  b\n", "a b", {"mode": "token"})[0])
        self.assertTrue(
            check_output(
                "1.0", "1.00001", {"mode": "float", "absolute_tolerance": 0.001}
            )[0]
        )

    def test_custom_checker_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "checker.py"
            script.write_text(
                "import pathlib, sys\n"
                "raise SystemExit(pathlib.Path(sys.argv[2]).read_text() != "
                "pathlib.Path(sys.argv[3]).read_text())\n",
                encoding="utf-8",
            )
            accepted, _ = check_output(
                "answer",
                "answer",
                {
                    "mode": "custom",
                    "command": [
                        sys.executable,
                        str(script),
                        "{input}",
                        "{expected}",
                        "{actual}",
                    ],
                },
            )
            self.assertTrue(accepted)


class NativeRunnerTests(unittest.TestCase):
    def test_python_verdicts_and_output_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = write_package(Path(temp), output_kb=1)
            self.assertEqual(
                run_submission(root, "print(int(input()) ** 2)", "python3", "sample").verdict,
                "AC",
            )
            self.assertEqual(
                run_submission(root, "print('bad')", "python3", "sample").verdict,
                "WA",
            )
            self.assertEqual(
                run_submission(root, "print('x' * 5000)", "python3", "sample").verdict,
                "OLE",
            )
            self.assertEqual(
                run_submission(root, "if True print(1)", "python3", "sample").verdict,
                "CE",
            )
            self.assertEqual(
                run_submission(root, "raise RuntimeError('boom')", "python3", "sample").verdict,
                "RE",
            )
        with tempfile.TemporaryDirectory() as temp:
            root = write_package(Path(temp), time_ms=50)
            self.assertEqual(
                run_submission(root, "while True: pass", "python3", "sample").verdict,
                "TLE",
            )

    def test_secret_results_do_not_leak_expected_or_input(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_submission(
                write_package(Path(temp)),
                "import sys; print(sys.stdin.read()); raise RuntimeError('secret-answer')",
                "python3",
                "secret",
            )
            serialized = json.dumps(result.to_dict())
            self.assertNotIn("secret-answer", serialized)
            self.assertNotIn('"2\\n"', serialized)


class DockerTests(unittest.TestCase):
    def test_cpp_commands_include_security_and_cpp17_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            root = write_package(Path(temp))
            package = load_problem_package(root)
            judge = DockerProgrammingJudge(package)
            source = root / "main.cpp"
            source.write_text("int main(){}", encoding="utf-8")
            build = root / "build"
            build.mkdir()
            command = judge.build_compile_command(source, build)
            joined = " ".join(command)
            for required in (
                "--network none",
                "--read-only",
                "--cap-drop ALL",
                "no-new-privileges",
                "--pids-limit 64",
                "--memory 64m",
                "--cpus 1",
                "-std=c++17",
            ):
                self.assertIn(required, joined)

    def test_cpp_unavailable_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(DockerProgrammingJudge, "available", return_value=False):
                result = run_submission(
                    write_package(Path(temp)), "int main(){}", "cpp17", "sample"
                )
            self.assertEqual(result.verdict, "JUDGE_ERROR")
            self.assertFalse(result.graded)
            self.assertIn("not executed on the host", result.reason)


class EnvironmentSubmissionTests(unittest.TestCase):
    def test_submit_code_instructions_are_programming_only(self):
        self.assertIn(
            "submit_code",
            build_action_instructions([], programming_contest=True),
        )
        self.assertNotIn(
            "submit_code",
            build_action_instructions([], programming_contest=False),
        )

    def test_submit_code_is_private_penalized_and_nonfinal(self):
        env = OlympiadEnvironment("icpc", "icpc_wf_2012_bottles", max_turns=20)
        before = env.simulated_minutes
        response = json.loads(env.execute_action("Agent_1", "submit_code", "print('bad')"))
        self.assertEqual(response["attempt"], 1)
        self.assertFalse(response["finalized"])
        self.assertFalse(env.submitted)
        self.assertEqual(env.wrong_submissions, 1)
        self.assertEqual(env.simulated_minutes, before + 20)
        observations = env.consume_agent_observations("Agent_1")
        self.assertEqual(observations[-1]["visibility"], "private")
        self.assertEqual(env.action_log[-1]["visibility"], "private")
        self.assertEqual(env.code_submissions, [])

    def test_submit_code_is_team_visible_when_enforced(self):
        env = OlympiadEnvironment(
            "icpc",
            "icpc_wf_2012_bottles",
            max_turns=20,
            rules_mode="enforced",
        )
        env.execute_action("Agent_2", "submit_code", "print('bad')")
        self.assertEqual(env.action_log[-1]["visibility"], "team")
        self.assertEqual(len(env.code_submissions), 1)
        self.assertEqual(env.code_submissions[0]["agent"], "Agent_2")
        self.assertTrue(
            any(entry["sender"] == "Contest_Control" for entry in env.chat_history)
        )
        teammate_obs = env.consume_agent_observations("Agent_3")
        self.assertTrue(teammate_obs)
        self.assertEqual(teammate_obs[-1]["visibility"], "team")
        prompt = _agent_user_prompt(env, "Agent_1", "centralized", extra="")
        self.assertIn("TEAM CODE SUBMISSIONS", prompt)
        self.assertIn("print('bad')", prompt)

    def test_final_prefers_official_secret_and_labels_sample_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = write_package(Path(temp))
            problem = {
                "problem_id": "demo",
                "task_type": "algorithmic_programming",
                "evaluation": {"official_bundle_path": str(root)},
            }
            secret = judge_programming_submission(
                problem,
                "print('secret-answer')",
                competition_id="icpc",
                repo_root=REPO_ROOT,
                fetch_kattis=False,
            )
            self.assertEqual(secret.test_scope, "secret")
            self.assertEqual(secret.grading_scope_label, "official-secret")
            sample = judge_programming_submission(
                {
                    "problem_id": "icpc_wf_2012_bottles",
                    "task_type": "algorithmic_programming",
                },
                "print('bad')",
                competition_id="icpc",
                repo_root=REPO_ROOT,
                fetch_kattis=False,
            )
            self.assertEqual(sample.grading_scope_label, "sample-only")


class CollectorTests(unittest.TestCase):
    def test_dry_run_filters_without_network_or_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            benchmark = root / "benchmark.json"
            benchmark.write_text(
                json.dumps(
                    [
                        {"problem_id": "p1", "kattis_id": "one"},
                        {"problem_id": "p2", "kattis_id": "two"},
                    ]
                ),
                encoding="utf-8",
            )
            summary = collect(
                benchmark_path=benchmark,
                samples_root=root / "samples",
                limit=1,
                dry_run=True,
                opener=lambda *_args, **_kwargs: self.fail("network used"),
            )
            self.assertEqual(summary["selected"], 1)
            self.assertEqual(summary["problems"][0]["status"], "would-fetch")
            self.assertFalse((root / "samples" / "manifest.json").exists())

    def test_zip_slip_is_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = io.BytesIO()
            with zipfile.ZipFile(payload, "w") as archive:
                archive.writestr("../escape.in", "bad")
                archive.writestr("case.ans", "bad")
            destination = root / "samples" / "problem"
            destination.parent.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "traversal"):
                extract_samples_atomic(payload.getvalue(), destination)
            self.assertFalse((root / "samples" / "escape.in").exists())

    def test_upstream_benchmark_kattis_ids_are_usable_and_unique(self):
        records = json.loads(
            (REPO_ROOT / "data" / "benchmarks" / "icpc" / "benchmark.json").read_text(
                encoding="utf-8"
            )
        )
        kattis_ids = [str(record["kattis_id"]) for record in records if record.get("kattis_id")]
        self.assertTrue(kattis_ids)
        self.assertEqual(len(kattis_ids), len(set(kattis_ids)))


if __name__ == "__main__":
    unittest.main()
