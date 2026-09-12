from __future__ import annotations

import sys
import unittest
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_otc_gold_suite import _group_problems  # noqa: E402


class GoldSuiteManifestGroupingTests(unittest.TestCase):
    def test_arml_2012_q10_prompt_does_not_include_pdf_page_number(self) -> None:
        benchmark = json.loads(
            (REPO_ROOT / "data/benchmarks/arml_local/benchmark.json").read_text(
                encoding="utf-8"
            )
        )
        row = next(item for item in benchmark if item["problem_id"] == "arml_local_2012")
        self.assertIn("x2− 56.", row["problem_description"])
        self.assertNotIn("56. 328", row["problem_description"])

    def test_mystery_hunt_groups_puzzles_by_year(self) -> None:
        problems = [
            {"problem_id": "m1", "year": 1999},
            {"problem_id": "m2", "year": 1999},
            {"problem_id": "m3", "year": 2000},
        ]

        groups = _group_problems("mystery_hunt", problems)

        self.assertEqual(
            [(session_id, [p["problem_id"] for p in rows]) for session_id, rows in groups],
            [
                ("mystery_hunt_1999", ["m1", "m2"]),
                ("mystery_hunt_2000", ["m3"]),
            ],
        )

    def test_science_bowl_groups_questions_by_official_packet(self) -> None:
        problems = [
            {"problem_id": "s1", "parent_session_id": "Science Bowl Packet A"},
            {"problem_id": "s2", "parent_session_id": "Science Bowl Packet A"},
            {"problem_id": "s3", "parent_session_id": "Science Bowl Packet B"},
        ]

        groups = _group_problems("science_bowl", problems)

        self.assertEqual([session_id for session_id, _ in groups], [
            "science_bowl_packet_a",
            "science_bowl_packet_b",
        ])
        self.assertEqual([len(rows) for _, rows in groups], [2, 1])

    def test_qanta_groups_questions_by_tournament_and_year(self) -> None:
        problems = [
            {"problem_id": "q1", "year": 2001, "tournament": "ACF Nationals"},
            {"problem_id": "q2", "year": 2001, "tournament": "ACF Nationals"},
            {"problem_id": "q3", "year": 2002, "tournament": "ACF Nationals"},
        ]

        groups = _group_problems("qanta", problems)

        self.assertEqual([session_id for session_id, _ in groups], [
            "qanta_2001_acf_nationals",
            "qanta_2002_acf_nationals",
        ])
        self.assertEqual([len(rows) for _, rows in groups], [2, 1])

    def test_packet_competitions_remain_one_session_per_benchmark_row(self) -> None:
        problems = [
            {"problem_id": "arml_2009", "year": 2009},
            {"problem_id": "arml_2010", "year": 2010},
        ]

        groups = _group_problems("arml_local", problems)

        self.assertEqual(
            [(session_id, len(rows)) for session_id, rows in groups],
            [("arml_2009", 1), ("arml_2010", 1)],
        )


if __name__ == "__main__":
    unittest.main()
