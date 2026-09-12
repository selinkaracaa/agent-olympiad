from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_manifest import load_contest_manifest  # noqa: E402


class ContestManifestTests(unittest.TestCase):
    def write_benchmark(self, root: Path, competition: str, rows: list[dict]) -> None:
        target = root / competition
        target.mkdir(parents=True)
        (target / "benchmark.json").write_text(json.dumps(rows), encoding="utf-8")

    def test_structured_math_packet_splits_into_numbered_task_units(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_benchmark(
                root,
                "math",
                [
                    {
                        "problem_id": "packet",
                        "task_type": "team_contest",
                        "problem_description": "Problems 1. Easy sum. 2. Hard proof.",
                        "gold_label": {
                            "parts": [
                                {"id": "1", "expected": "2", "points": 1},
                                {"id": "2", "expected": "yes", "points": 2},
                            ]
                        },
                    }
                ],
            )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "session_id": "math-packet",
                        "competition_id": "math",
                        "problem_ids": ["packet"],
                        "split_parts": True,
                    }
                ),
                encoding="utf-8",
            )

            manifest = load_contest_manifest(manifest_path, benchmark_root=root)

            self.assertEqual([task.task_id for task in manifest.tasks], ["packet:1", "packet:2"])
            self.assertEqual(manifest.tasks[0].prompt, "Easy sum.")
            self.assertEqual(manifest.tasks[1].max_score, 2.0)

    def test_arml_team_markers_split_without_exposing_answer_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_benchmark(
                root,
                "arml_national_team",
                [
                    {
                        "problem_id": "arml_team_2010",
                        "task_type": "team_contest",
                        "problem_description": (
                            "2010 Team Problems T-1. Compute the first value. "
                            "T-2. Compute the second value. "
                            "2010 Team Answers T-1. 42 T-2. 99"
                        ),
                        "gold_label": {
                            "parts": [
                                {"id": "1", "expected": "42", "points": 5},
                                {"id": "2", "expected": "99", "points": 5},
                            ]
                        },
                    }
                ],
            )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "session_id": "arml-team",
                        "competition_id": "arml_national_team",
                        "problem_ids": ["arml_team_2010"],
                        "split_parts": True,
                    }
                ),
                encoding="utf-8",
            )

            manifest = load_contest_manifest(manifest_path, benchmark_root=root)

            self.assertEqual(
                [task.task_id for task in manifest.tasks],
                ["arml_team_2010:1", "arml_team_2010:2"],
            )
            self.assertEqual(manifest.tasks[0].prompt, "Compute the first value.")
            self.assertEqual(manifest.tasks[1].prompt, "Compute the second value.")
            self.assertNotIn("Team Answers", " ".join(task.prompt for task in manifest.tasks))

    def test_manifest_selects_gradeable_questions_and_repairs_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_benchmark(
                root,
                "math",
                [
                    {
                        "problem_id": "packet",
                        "task_type": "team_contest",
                        "problem_description": (
                            "Problems 1. Keep this. 2. Missing gold. "
                            "3. Garbled diagram."
                        ),
                        "gold_label": {
                            "parts": [
                                {"id": "1", "expected": "2", "points": 1},
                                {"id": "2", "expected": "", "points": 0},
                                {"id": "3", "expected": "9", "points": 1},
                            ]
                        },
                    }
                ],
            )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "session_id": "math-packet",
                        "competition_id": "math",
                        "problem_ids": ["packet"],
                        "split_parts": True,
                        "question_ids": ["1", "3"],
                        "prompt_overrides": {"3": "Repaired diagram."},
                    }
                ),
                encoding="utf-8",
            )

            manifest = load_contest_manifest(manifest_path, benchmark_root=root)

            self.assertEqual(
                [task.task_id for task in manifest.tasks],
                ["packet:1", "packet:3"],
            )
            self.assertEqual(manifest.tasks[0].prompt, "Keep this.")
            self.assertEqual(manifest.tasks[1].prompt, "Repaired diagram.")

    def test_programming_manifest_keeps_each_benchmark_record_as_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_benchmark(
                root,
                "icpc",
                [
                    {
                        "problem_id": "a",
                        "task_type": "algorithmic_programming",
                        "problem_description": "Solve A",
                    },
                    {
                        "problem_id": "b",
                        "task_type": "algorithmic_programming",
                        "problem_description": "Solve B",
                    },
                ],
            )
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "session_id": "icpc-two",
                        "competition_id": "icpc",
                        "problem_ids": ["a", "b"],
                    }
                ),
                encoding="utf-8",
            )

            manifest = load_contest_manifest(manifest_path, benchmark_root=root)

            self.assertEqual([task.task_id for task in manifest.tasks], ["a", "b"])
            self.assertTrue(all(task.programming for task in manifest.tasks))

    def test_manifest_rejects_missing_problem_instead_of_silently_dropping_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_benchmark(root, "quiz", [])
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "session_id": "bad",
                        "competition_id": "quiz",
                        "problem_ids": ["missing"],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing"):
                load_contest_manifest(manifest_path, benchmark_root=root)


if __name__ == "__main__":
    unittest.main()
