"""Programming judge outages are missing evaluation, not contestant failures."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from contest_adapters import EnvironmentTaskExecutor, grade_contest_result
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import ContestRunConfig, run_contest


TASK = ManifestTask("a", "a", None, "Print 42", "algorithmic_programming", 1, True, {})
MANIFEST = ContestManifest("fixture", "icpc", (TASK,))


def event(verdict=None, valid=True, kind="submit_code_result", task_id="a"):
    return {"task_id": task_id, "kind": kind, "payload": {"verdict": verdict, "valid": valid}}


def grade(*events, state="active", **extra):
    return grade_contest_result(MANIFEST, {"tasks": {"a": {"state": state}},
        "memory": {"events": list(events)}, **extra})


class ProgrammingGradingAvailabilityTests(unittest.TestCase):
    def test_infrastructure_failures_never_become_graded_zero(self):
        for verdict in ("JUDGE_ERROR", "SUBMIT_FAILED", "PENDING", "CHALLENGE", "NEEDS_HUMAN", "SAMPLE_AC"):
            for valid in (False, True):
                with self.subTest(verdict=verdict, valid=valid):
                    result = grade(event(verdict, valid))
                    self.assertFalse(result["graded"])
                    self.assertIsNone(result["score"])
                    self.assertIsNone(result["task_utility"])
                    self.assertEqual(result["max_score"], 1)
                    self.assertEqual(result["evaluation_coverage"], 0)

    def test_official_negative_verdict_is_a_real_zero(self):
        for verdict in ("WA", "TLE", "MLE", "RE", "CE", "OLE"):
            with self.subTest(verdict=verdict):
                result = grade(event(verdict))
                self.assertTrue(result["graded"])
                self.assertEqual(result["score"], 0)

    def test_no_attempt_and_local_rejection_are_not_judge_outages(self):
        for events in ([], [event("SAMPLE_WA", False)], [event("SAMPLE_CE", False)]):
            self.assertEqual(grade(*events)["score"], 0)
            self.assertTrue(grade(*events)["graded"])

    def test_retry_resolves_outage_but_later_uncertainty_is_preserved(self):
        self.assertTrue(grade(event("JUDGE_ERROR", False), event("WA"))["graded"])
        self.assertFalse(grade(event("WA"), event("JUDGE_ERROR", False))["graded"])
        self.assertFalse(grade(event("JUDGE_ERROR", False), event("SAMPLE_WA", False))["graded"])

    def test_accepted_locked_task_remains_solved(self):
        result = grade(event("JUDGE_ERROR", False), state="solved")
        self.assertEqual(result["score"], 1)
        self.assertTrue(result["graded"])

    def test_interrupted_deadline_attempt_is_not_inferred_wrong(self):
        started = event(kind="programming_deadline_submit_started")
        self.assertFalse(grade(started)["graded"])
        self.assertTrue(grade(started, event("WA", kind="programming_deadline_submit_result"))["graded"])

    def test_queued_verdict_requires_delivery(self):
        self.assertFalse(grade(event(kind="verdict_queued"))["graded"])
        self.assertTrue(grade(event(kind="verdict_queued"), event("WA"))["graded"])

    def test_checkpoint_and_terminal_fallbacks(self):
        for result in (
            {"session_checkpoint": {"tasks": [{"task_id": "a", "submissions": [
                {"verdict": "JUDGE_ERROR", "valid": False}]}]}},
            {"tasks": {"a": {"state": "active", "terminal_verdict": "JUDGE_ERROR"}}},
            {"tasks": {"a": {"state": "active", "submissions": [
                {"verdict": "JUDGE_ERROR", "valid": False}]}}},
        ):
            self.assertFalse(grade_contest_result(MANIFEST, result)["graded"])

    def test_other_tasks_and_non_submission_tools_do_not_change_grade(self):
        result = grade(event("JUDGE_ERROR", False, task_id="b"),
                       event("JUDGE_ERROR", False, kind="execute_code_result"))
        self.assertTrue(result["graded"])

    def test_mixed_programming_contest_keeps_full_denominator(self):
        other = ManifestTask("b", "b", None, "Task B", "algorithmic_programming", 1, True, {})
        result = grade_contest_result(ContestManifest("fixture", "icpc", (TASK, other)), {
            "tasks": {"a": {"state": "solved"}, "b": {"state": "active"}},
            "memory": {"events": [event("JUDGE_ERROR", False, task_id="b")]}})
        self.assertFalse(result["graded"])
        self.assertEqual(result["max_score"], 2)
        self.assertEqual(result["partial_score"], 1)
        self.assertEqual(result["graded_max_score"], 1)

    def test_adapter_rejects_judge_error_even_with_remote_scope(self):
        executor = EnvironmentTaskExecutor(MANIFEST, benchmark_root="data/benchmarks")
        env = Mock()
        env.execute_action.return_value = '{"remote":{"status":"done","verdict":"JUDGE_ERROR"}}'
        executor._environments["a"] = env
        result = executor.submit_at_deadline(TASK, "print(42)")
        self.assertFalse(result["valid"])
        self.assertEqual(result["verdict"], "JUDGE_ERROR")


if __name__ == "__main__":
    unittest.main()
