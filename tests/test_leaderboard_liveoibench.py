from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from judge.models import JudgeError
from leaderboard import (
    aggregate_contest_scores,
    build_global_table,
    codeforces_equivalent_rating,
    compute_icpc_standings,
    human_percentile,
    load_human_baselines,
    medal_from_cutoffs,
    select_best_solution,
)
from liveoibench_adapter import (
    build_code_export,
    load_contestant_data,
    load_liveoibench_problem,
    sanitized_package_metadata,
)


def write_liveoi_problem(root: Path, *, bad_subtask: bool = False) -> Path:
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "01.in").write_text("public input\n", encoding="utf-8")
    (root / "tests" / "01.out").write_text("TOP SECRET ANSWER\n", encoding="utf-8")
    (root / "problem.json").write_text(
        json.dumps({"time_limit": 2, "memory_limit": 256, "task_type": "batch"}),
        encoding="utf-8",
    )
    tests = ["../outside"] if bad_subtask else ["01"]
    (root / "subtasks.json").write_text(
        json.dumps({"1": {"score": 100, "testcases": tests}}),
        encoding="utf-8",
    )
    return root


class IcpcLeaderboardTests(unittest.TestCase):
    def test_penalties_attempts_ties_and_deterministic_order(self):
        submissions = [
            {"team": "beta", "problem": "A", "minute": 10, "verdict": "WA"},
            {"team": "beta", "problem": "A", "minute": 30, "verdict": "AC"},
            {"team": "alpha", "problem": "A", "minute": 10, "verdict": "WA"},
            {"team": "alpha", "problem": "A", "minute": 30, "verdict": "AC"},
            {"team": "gamma", "problem": "A", "minute": 30, "verdict": "AC"},
            {"team": "gamma", "problem": "B", "minute": 60, "verdict": "WA"},
        ]
        rows = compute_icpc_standings(submissions)
        self.assertEqual([row["team"] for row in rows], ["gamma", "alpha", "beta"])
        self.assertEqual(rows[0]["penalty"], 30)
        self.assertEqual(rows[1]["penalty"], 50)
        self.assertEqual(rows[1]["rank"], rows[2]["rank"])
        self.assertEqual(rows[1]["attempts"], 2)
        self.assertEqual(rows[1]["problems"]["A"]["wrong_before_ac"], 1)
        self.assertEqual(rows[0]["attempts"], 2)


class LiveoiRankingTests(unittest.TestCase):
    def test_strict_percentile_does_not_count_ties(self):
        self.assertEqual(human_percentile(50, [40, 50, 60]), 100 / 3)
        self.assertIsNone(human_percentile(50, []))

    def test_medal_cutoffs_are_inclusive(self):
        cutoffs = {"Gold": 90, "Silver": 70, "Bronze": 50}
        self.assertEqual(medal_from_cutoffs(90, cutoffs), "Gold")
        self.assertEqual(medal_from_cutoffs(70, cutoffs), "Silver")
        self.assertEqual(medal_from_cutoffs(50, cutoffs), "Bronze")
        self.assertEqual(medal_from_cutoffs(49.9, cutoffs), "None")
        self.assertIsNone(medal_from_cutoffs(100, {}))

    def test_codeforces_rating_is_monotone_and_empty_is_none(self):
        ratings = [1200, 1500, 1800, 2100]
        first = codeforces_equivalent_rating(1, ratings)
        second = codeforces_equivalent_rating(2, ratings)
        last = codeforces_equivalent_rating(5, ratings)
        self.assertGreater(first, second)
        self.assertGreater(second, last)
        self.assertIsNone(codeforces_equivalent_rating(1, []))

    def test_best_of_eight_is_explicitly_oracle_selected(self):
        candidates = {
            f"answer_{index}.cpp": {
                "score": 10 if index < 7 else 90,
                "relative_score": index,
                "tests_passed_pct": index,
                "time": 8 - index,
            }
            for index in range(8)
        }
        result = select_best_solution(candidates)
        self.assertEqual(result["best_solution"], "answer_7.cpp")
        self.assertEqual(result["candidate_count"], 8)
        self.assertEqual(result["selection_protocol"], "oracle_best_of_8")
        self.assertTrue(result["oracle_selected"])

    def test_best_solution_uses_all_documented_tiebreakers(self):
        result = select_best_solution(
            {
                "slow.cpp": {
                    "score": 50,
                    "relative_score": 50,
                    "tests_passed_pct": 80,
                    "time": 3,
                },
                "fast.cpp": {
                    "score": 50,
                    "relative_score": 50,
                    "tests_passed_pct": 80,
                    "time": 2,
                },
            }
        )
        self.assertEqual(result["best_solution"], "fast.cpp")

    def test_contest_aggregation_rejects_mixed_scale(self):
        results = {
            "A": {"score": 50, "max_score": 100},
            "B": {"score": 5, "max_score": 10},
        }
        metadata = {
            "A": {"contest_id": "IOI-2025", "score_scale": "points", "max_score": 100},
            "B": {"contest_id": "IOI-2025", "score_scale": "stars", "max_score": 10},
        }
        with self.assertRaisesRegex(ValueError, "mixes raw score scales"):
            aggregate_contest_scores(results, metadata)

    def test_global_aggregation_never_sums_raw_scales(self):
        rows = build_global_table(
            {
                "model": {
                    "IOI-2025": {
                        "competition": "IOI",
                        "total_score": 300,
                        "relative_score": 75,
                    },
                    "USACO-2025": {
                        "competition": "USACO",
                        "total_score": 700,
                        "relative_score": 50,
                    },
                }
            }
        )
        self.assertNotIn("total_score", rows[0])
        self.assertEqual(rows[0]["global_relative_score"], 62.5)
        self.assertEqual(rows[0]["raw_score_status"], "not_aggregated_across_contests")

    def test_missing_human_data_has_clear_status(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = load_human_baselines(Path(temp) / "not-there")
            empty = load_human_baselines(Path(temp))
        self.assertEqual(missing["status"], "missing")
        self.assertIn("not found", missing["reason"])
        self.assertEqual(empty["status"], "missing")
        self.assertIn("No JSON or CSV", empty["reason"])


class LiveoiAdapterTests(unittest.TestCase):
    def test_export_schema_and_path_validation(self):
        payload = build_code_export(
            [
                {
                    "problem_id": "IOI-2025-contest-demo",
                    "filename": "demo_0.cpp",
                    "code": "int main() {}",
                }
            ]
        )
        self.assertEqual(
            payload,
            {"IOI-2025-contest-demo": {"demo_0.cpp": "int main() {}"}},
        )
        with self.assertRaisesRegex(ValueError, "Unsafe solution filename"):
            build_code_export(
                {
                    "IOI-2025-contest-demo": {
                        "../escape.cpp": "int main() {}",
                    }
                }
            )
        with self.assertRaisesRegex(ValueError, "Unsafe problem_id"):
            build_code_export({"../escape": {"ok.cpp": "int main() {}"}})

    def test_json_contestants_work_without_optional_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contestants.json"
            path.write_text(json.dumps([{"contest_id": "IOI", "score": 50}]))
            self.assertEqual(load_contestant_data(path)[0]["score"], 50)

    def test_invalid_problem_package_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = write_liveoi_problem(Path(temp), bad_subtask=True)
            with self.assertRaisesRegex(JudgeError, "unknown tests"):
                load_liveoibench_problem(root, problem_id="IOI-2025-contest-demo")

    def test_adapter_does_not_load_secret_contents_or_execute_scripts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = write_liveoi_problem(Path(temp))
            graders = root / "graders"
            graders.mkdir()
            (graders / "evaluate.sh").write_text(
                "echo SHOULD NEVER EXECUTE > pwned.txt\n", encoding="utf-8"
            )
            package = load_liveoibench_problem(
                root, problem_id="IOI-2025-contest-demo"
            )
            safe = sanitized_package_metadata(package)
            serialized = json.dumps(safe)
            self.assertNotIn("TOP SECRET ANSWER", serialized)
            self.assertNotIn("public input", serialized)
            self.assertFalse(safe["secrets"]["expected_outputs_loaded"])
            self.assertFalse(safe["secrets"]["unsafe_host_judge_executed"])
            self.assertFalse((root / "pwned.txt").exists())
            self.assertEqual(package.tests[0].scope, "secret")


if __name__ == "__main__":
    unittest.main()
