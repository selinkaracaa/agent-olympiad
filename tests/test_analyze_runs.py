"""Focused tests for the deterministic run-analysis CLI."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analyze_runs import (
    analyze_files,
    compute_decompositions,
    main,
    normalized_task_score,
)


class AnalyzeRunsTests(unittest.TestCase):
    def test_normalized_score_and_complete_decomposition(self):
        rows = [
            {
                "competition": "demo",
                "problem_id": "p1",
                "team": "gpt",
                "condition": "solo",
                "grade_score": 4,
                "grade_max_score": 10,
            },
            {
                "competition": "demo",
                "problem_id": "p1",
                "team": "gpt",
                "condition": "subagent",
                "grade_score": 6,
                "grade_max_score": 10,
            },
            {
                "competition": "demo",
                "problem_id": "p1",
                "team": "gpt",
                "condition": "team",
                "grade_score": 8,
                "grade_max_score": 10,
                "transcript_ceiling": 0.9,
            },
        ]
        self.assertEqual(normalized_task_score(rows[0]), 0.4)
        result = compute_decompositions(rows)[0]
        self.assertAlmostEqual(result["division_gain"], 0.2)
        self.assertAlmostEqual(result["cohesion_gain"], 0.2)
        self.assertAlmostEqual(result["synthesis_loss"], 0.1)
        self.assertIsNone(result["gain_reason"])

    def test_decomposition_missing_data_is_null_with_reason(self):
        result = compute_decompositions(
            [
                {
                    "competition": "demo",
                    "problem_id": "p1",
                    "condition": "team",
                    "grade_score": 1,
                    "grade_max_score": 2,
                }
            ]
        )[0]
        self.assertIsNone(result["division_gain"])
        self.assertIsNone(result["cohesion_gain"])
        self.assertIn("solo", result["gain_reason"])
        self.assertIsNone(result["synthesis_loss"])
        self.assertEqual(result["synthesis_loss_reason"], "missing_transcript_ceiling")

    def test_cli_writes_analysis_and_errors_csv(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            transcript = root / "transcript.json"
            transcript.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "agents": ["Leader", "Worker"],
                            "allowed_tools": ["execute_code"],
                        },
                        "chat_history": [
                            {"sender": "Leader", "message": "Can you check this?"},
                            {"sender": "Worker", "message": "pass"},
                        ],
                        "action_log": [
                            {
                                "turn": 2,
                                "agent": "Leader",
                                "action": "submit_final",
                                "payload": "long enough final answer",
                                "result": "ok",
                            }
                        ],
                        "submission": {"final_answer": "long enough final answer"},
                    }
                ),
                encoding="utf-8",
            )
            phase = root / "phase.json"
            phase.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "competition": "demo",
                                "problem_id": "p1",
                                "schema": "centralized",
                                "grade_score": 1,
                                "grade_max_score": 2,
                                "transcript_path": "transcript.json",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            analysis, errors = analyze_files([phase])
            self.assertEqual(analysis["runs"][0]["normalized_task_score"], 0.5)
            self.assertIsNotNone(analysis["runs"][0]["team_metrics"])
            self.assertTrue(errors)

            output = root / "output"
            self.assertEqual(main([str(phase), "--output-dir", str(output)]), 0)
            analysis_path = output / "analysis.json"
            errors_path = output / "errors.csv"
            self.assertTrue(analysis_path.is_file())
            self.assertTrue(errors_path.is_file())
            emitted = json.loads(analysis_path.read_text(encoding="utf-8"))
            self.assertEqual(emitted["schema_version"], "team-analysis.v1")
            with errors_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            self.assertIn("code", rows[0])
            self.assertFalse(any(path.suffix == ".tmp" for path in output.iterdir()))


if __name__ == "__main__":
    unittest.main()
