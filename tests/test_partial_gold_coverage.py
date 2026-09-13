"""Partial deterministic gold never masquerades as full-contest evaluation."""
import copy
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from contest_adapters import GradingUnavailable, _grade_non_programming, grade_contest_result
from contest_manifest import ContestManifest, ManifestTask
import run_pipeline
import run_competition_batch
import contest_manifest


def task(parts=None, *, question_id=None, maximum=10, name="packet", expected=None):
    gold = {"parts": parts} if parts is not None else {"expected_answer": expected}
    return ManifestTask(name, "packet", question_id, "Fixture", "math", maximum, False,
                        {"problem_id": "packet", "gold_label": gold})


def mixed_parts():
    return [{"id": "1", "expected": "42", "points": 4},
            {"id": "2", "reference": "A proof", "points": 6, "match_mode": "reference_llm"}]


def grade(tasks, submissions=None):
    return grade_contest_result(ContestManifest("fixture", "math", tuple(tasks)),
                                {"submissions": submissions or {}})


class PartialGoldCoverageTests(unittest.TestCase):
    def test_mixed_parts_keep_full_denominator_without_official_score(self):
        result = grade([task(mixed_parts())], {"packet": "42"})
        self.assertFalse(result["graded"])
        self.assertEqual(result["max_score"], 10)
        self.assertIsNone(result["score"])
        self.assertIsNone(result["task_utility"])
        self.assertEqual(result["partial_score"], 4)
        self.assertEqual(result["graded_max_score"], 4)
        self.assertEqual(result["score_evaluation_coverage"], 0.4)
        self.assertEqual(result["part_evaluation_coverage"], 0.5)
        self.assertEqual(result["ungraded_tasks"], 1)
        row = result["tasks"]["packet"]
        self.assertEqual(row["status"], "partial")
        self.assertEqual(row["ungraded_part_ids"], ["2"])
        self.assertEqual(row["max_score"], 10)
        self.assertIsNone(row["score"])

    def test_unsupported_whole_task_stays_in_contest_denominator(self):
        result = grade([task(expected="42", maximum=4, name="known"),
                        task(expected=None, maximum=6, name="unknown")], {"known": "42"})
        self.assertEqual(result["max_score"], 10)
        self.assertIsNone(result["score"])
        self.assertIsNone(result["task_utility"])
        self.assertEqual(result["partial_score"], 4)
        self.assertEqual(result["evaluation_coverage"], 0.5)
        self.assertEqual(result["tasks"]["unknown"]["max_score"], 6)

    def test_split_reference_part_keeps_its_own_weight(self):
        parts = mixed_parts()
        result = grade([task(parts, question_id="1", maximum=4, name="p1"),
                        task(parts, question_id="2", maximum=6, name="p2")], {"p1": "42"})
        self.assertEqual(result["max_score"], 10)
        self.assertEqual(result["graded_max_score"], 4)
        self.assertEqual(result["partial_score"], 4)
        self.assertEqual(result["tasks"]["p2"]["ungraded_part_ids"], ["2"])
        self.assertIsNone(result["score"])

    def test_all_unsupported_retains_maximum_and_no_zero_score(self):
        result = grade([task([{"id": "1", "points": 4},
                              {"id": "2", "points": 6, "match_mode": "reference_llm"}])])
        self.assertEqual(result["max_score"], 10)
        self.assertIsNone(result["score"])
        self.assertIsNone(result["partial_score"])
        self.assertEqual(result["graded_max_score"], 0)
        self.assertEqual(result["part_evaluation_coverage"], 0)

    def test_wrong_supported_answer_is_only_a_partial_zero(self):
        result = grade([task(mixed_parts())], {"packet": "wrong"})
        self.assertIsNone(result["score"])
        self.assertEqual(result["partial_score"], 0)
        self.assertEqual(result["max_score"], 10)

    def test_multiple_supported_parts_preserve_all_missing_weights(self):
        parts = [{"id": "1", "expected": "42", "points": 2},
                 {"id": "2", "expected": "7", "max_score": 3},
                 {"id": "3", "points": 5, "reference": "Proof", "match_mode": "reference_llm"}]
        result = grade([task(parts)], {"packet": "1. 42\n2. 7"})
        self.assertEqual(result["max_score"], 10)
        self.assertEqual(result["partial_score"], 5)
        self.assertEqual(result["graded_parts"], 2)
        self.assertEqual(result["ungraded_parts"], 1)

    def test_unweighted_multipart_scope_does_not_inherit_packet_weight_per_part(self):
        parts = [{"id": "1", "expected": "42"}, {"id": "2", "match_mode": "reference_llm"}]
        result = grade([task(parts, maximum=2)], {"packet": "42"})
        self.assertEqual(result["max_score"], 2)
        self.assertEqual(result["graded_max_score"], 1)
        self.assertEqual(result["partial_score"], 1)

    def test_fully_supported_scores_and_macro_task_utility_are_unchanged(self):
        parts = [{"id": "1", "expected": "42", "points": 2},
                 {"id": "2", "expected": "yes", "points": 3, "aliases": ["Y"]}]
        result = grade([task(parts, question_id="1", maximum=2, name="p1"),
                        task(parts, question_id="2", maximum=3, name="p2")],
                       {"p1": "42", "p2": "wrong"})
        self.assertTrue(result["graded"])
        self.assertEqual(result["score"], 2)
        self.assertEqual(result["max_score"], 5)
        self.assertEqual(result["task_utility"], 0.5)
        self.assertEqual(result["part_evaluation_coverage"], 1)
        self.assertEqual(result["score_evaluation_coverage"], 1)

    def test_missing_submission_is_wrong_not_missing_evaluator(self):
        result = grade([task(expected="42", maximum=4)])
        self.assertTrue(result["graded"])
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["max_score"], 4)

    def test_private_tuple_grader_refuses_silent_partial_success(self):
        with self.assertRaises(GradingUnavailable):
            _grade_non_programming(task(mixed_parts()), "42")

    def test_grading_does_not_modify_benchmark(self):
        original = task(mixed_parts())
        before = copy.deepcopy(original.benchmark)
        grade([original], {"packet": "42"})
        self.assertEqual(original.benchmark, before)

    def test_pipeline_blocks_partial_gold_before_launch(self):
        manifest = ContestManifest("fixture", "math", (task(mixed_parts()),))
        job = {"id": "fixture", "route": "native", "competition": "math", "manifest": "unused.json"}
        with patch.object(run_competition_batch, "inspect_contest_run", return_value=("new", {})), \
             patch.object(contest_manifest, "load_contest_manifest", return_value=manifest):
            with self.assertRaisesRegex(ValueError, "Full-session deterministic evaluation unavailable"):
                run_pipeline.command(job, ROOT / "results" / "not-created",
                                     SimpleNamespace(provider="perplexity", model="mock"))


if __name__ == "__main__":
    unittest.main()
