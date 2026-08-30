from __future__ import annotations

import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import CollabConfig, run_open_table_coach  # noqa: E402
from env import OlympiadEnvironment  # noqa: E402
from run_competition_batch import (  # noqa: E402
    _aggregate_metrics,
    _build_summary,
    _discover_structured_gold_cases,
    _load_resume_rows,
    _row_is_complete,
    _write_results_tsv,
    _write_summary_tsv,
)


class StructuredGoldBatchTests(unittest.TestCase):
    def test_discovers_structured_gold_suite_includes_aligned_answer_keys(self) -> None:
        cases = _discover_structured_gold_cases(REPO_ROOT / "data" / "benchmarks")
        counts = Counter(competition for competition, _ in cases)

        # Original curated math sheets.
        self.assertEqual(counts["arml_local"], 6)
        self.assertEqual(counts["arml_national_team"], 11)
        self.assertEqual(counts["purple_comet"], 14)
        self.assertEqual(counts["hmmt_guts"], 1)
        # Answer-key rubrics aligned into short_answers + benchmark parts.
        self.assertEqual(counts["science_bowl"], 140)
        self.assertEqual(counts["qanta"], 240)
        self.assertEqual(counts["mystery_hunt"], 261)
        self.assertEqual(counts["nyu_ctf_bench"], 194)
        self.assertEqual(counts["history_olympiad"], 95)
        self.assertEqual(counts["cfa_research_challenge"], 19)
        self.assertEqual(counts["wmtc"], 3)
        self.assertGreaterEqual(len(cases), 982)

    def test_aggregate_metrics_use_weighted_and_macro_accuracy(self) -> None:
        rows = [
            {
                "status": "ok",
                "graded": True,
                "grade_score": 8,
                "grade_max_score": 10,
                "communication_score": 4,
                "planning_score": 2,
                "coordination_score": 3,
                "api_calls": 10,
                "tokens_used": 100,
                "elapsed_seconds": 20,
            },
            {
                "status": "ok",
                "graded": True,
                "grade_score": 5,
                "grade_max_score": 5,
                "communication_score": 5,
                "planning_score": 3,
                "coordination_score": 4,
                "api_calls": 7,
                "tokens_used": 50,
                "elapsed_seconds": 10,
            },
        ]

        metrics = _aggregate_metrics(rows)

        self.assertAlmostEqual(metrics["answer_accuracy_micro"], 13 / 15)
        self.assertAlmostEqual(metrics["answer_accuracy_macro"], 0.9)
        self.assertAlmostEqual(metrics["full_credit_task_rate"], 0.5)
        self.assertAlmostEqual(metrics["mean_communication_score"], 4.5)
        self.assertAlmostEqual(metrics["mean_planning_score"], 2.5)
        self.assertAlmostEqual(metrics["mean_coordination_score"], 3.5)
        self.assertEqual(metrics["total_api_calls"], 17)
        self.assertEqual(metrics["total_tokens_used"], 150)
        self.assertEqual(metrics["total_elapsed_seconds"], 30)

    def test_resume_validates_configuration_and_completion(self) -> None:
        metadata = {
            "mode": "live",
            "provider": "perplexity",
            "model": "openai/gpt-5.4-mini",
            "schema": "open_table_coach",
            "rules_mode": "enforced",
        }
        payload = {
            **metadata,
            "timestamp": "20260827-000000",
            "results": [
                {
                    "status": "ok",
                    "graded": True,
                    "coordination_score": 4,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "competition_batch.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            rows, timestamp = _load_resume_rows(path, metadata)
            self.assertEqual(timestamp, "20260827-000000")
            self.assertTrue(
                _row_is_complete(rows[0], judge_task=True, judge_collab=True)
            )

            changed = {**metadata, "model": "different-model"}
            with self.assertRaisesRegex(ValueError, "model changed"):
                _load_resume_rows(path, changed)

    def test_writes_excel_compatible_tsv(self) -> None:
        row = {
            "competition": "arml_local",
            "problem_id": "arml_local_2009",
            "status": "ok",
            "grade_score": 30,
            "grade_max_score": 40,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "results.tsv"
            _write_results_tsv(path, [row])
            text = path.read_text(encoding="utf-8-sig")

        self.assertIn("answer_accuracy", text)
        self.assertIn("0.75", text)

    def test_builds_and_writes_competition_aggregates(self) -> None:
        rows = [
            {
                "competition": "alpha",
                "status": "ok",
                "grade_score": 1,
                "grade_max_score": 2,
            },
            {
                "competition": "beta",
                "status": "ok",
                "grade_score": 3,
                "grade_max_score": 4,
            },
        ]
        summary = _build_summary(rows, {"schema": "open_table_coach"})
        self.assertAlmostEqual(
            summary["aggregate_by_competition"]["alpha"]["answer_accuracy_micro"],
            0.5,
        )
        self.assertAlmostEqual(
            summary["aggregate_by_competition"]["beta"]["answer_accuracy_micro"],
            0.75,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "summary.tsv"
            _write_summary_tsv(path, summary)
            text = path.read_text(encoding="utf-8-sig")

        self.assertIn("overall", text)
        self.assertIn("alpha", text)
        self.assertIn("beta", text)

    def test_all_selected_competitions_enable_open_table_policy(self) -> None:
        cases = {
            "arml_local": "arml_local_2009",
            "arml_national_team": "arml_national_team_2009",
            "purple_comet": "purple_comet_hs_2024",
            "hmmt_guts": "hmmt_guts_2024",
        }
        for competition, problem_id in cases.items():
            with self.subTest(competition=competition):
                env = OlympiadEnvironment(
                    competition,
                    problem_id,
                    max_turns=1,
                    rules_mode="enforced",
                )
                result = run_open_table_coach(
                    env,
                    lambda _system, _user: "ACTION: sleep | PAYLOAD:",
                    CollabConfig(max_turns=1, synthesize=False),
                )
                self.assertEqual(result["turns_used"], 1)


if __name__ == "__main__":
    unittest.main()
