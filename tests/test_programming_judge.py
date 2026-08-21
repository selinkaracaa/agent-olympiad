"""Tests for local ICPC sample judge."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from env import OlympiadEnvironment
from evaluation.programming_judge import judge_programming_submission, load_sample_cases


class ProgrammingJudgeTests(unittest.TestCase):
    def test_bottles_samples_exist(self):
        dest = (
            REPO_ROOT
            / "data"
            / "benchmarks"
            / "icpc"
            / "samples"
            / "icpc_wf_2012_bottles"
        )
        cases = load_sample_cases(dest)
        self.assertGreaterEqual(len(cases), 1)

    def test_wrong_code_is_wa_and_burns_clock(self):
        env = OlympiadEnvironment("icpc", "icpc_wf_2012_bottles", max_turns=12)
        env.begin_turn()
        minutes_before = env.simulated_minutes
        bad = "print('nope')\n"
        env.execute_action("Agent_1", "submit_final", bad + " " * 10)
        grade = env.grade_submission()
        self.assertTrue(grade.get("graded"))
        self.assertEqual(grade.get("method"), "programming_sample_judge")
        self.assertNotEqual(grade.get("verdict"), "AC")
        self.assertGreaterEqual(env.wrong_submissions, 1)
        self.assertEqual(env.penalty_minutes(), 20)
        self.assertEqual(env.simulated_minutes, minutes_before + 20)
        self.assertTrue(grade.get("clock_burned_by_wa"))

    def test_direct_judge_api(self):
        problem = {
            "problem_id": "icpc_wf_2012_bottles",
            "kattis_id": "bottles",
            "task_type": "algorithmic_programming",
        }
        # Intentionally wrong
        result = judge_programming_submission(
            problem,
            "print(0)\n",
            competition_id="icpc",
            repo_root=REPO_ROOT,
            fetch_kattis=False,
        )
        self.assertTrue(result.graded)
        self.assertIn(result.verdict, {"WA", "RE", "TLE"})


if __name__ == "__main__":
    unittest.main()
