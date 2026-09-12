"""Public-interface tests for a multi-task contest session."""

from __future__ import annotations

import json
import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_session import (
    AnswerVersion,
    BudgetExceededError,
    ContestBudgetState,
    ContestSession,
    TaskBlockedError,
    TaskLockedError,
    TaskState,
    TaskUnit,
)
from submission_policy import SubmissionPolicy


class ContestSessionTests(unittest.TestCase):
    def test_selecting_a_task_keeps_exactly_one_task_active(self):
        session = ContestSession(
            tasks=[
                TaskUnit("code", kind="programming"),
                TaskUnit("essay", kind="non_programming"),
            ],
            budget=ContestBudgetState(max_turns=10),
        )

        session.select_task("code")
        self.assertEqual(session.active_task.task_id, "code")
        self.assertEqual(session.task("code").state, TaskState.ACTIVE)

        session.select_task("essay")
        self.assertEqual(session.active_task.task_id, "essay")
        self.assertEqual(session.task("code").state, TaskState.UNSEEN)
        self.assertEqual(session.task("essay").state, TaskState.ACTIVE)

    def test_answer_versions_form_an_immutable_chain_and_age_reviews(self):
        session = ContestSession(
            [TaskUnit("code")],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("code")

        first = session.create_answer("print(1)")
        review = session.record_review("agent-2", "looks correct")
        second = session.create_answer("print(2)")

        self.assertIsInstance(first, AnswerVersion)
        self.assertNotEqual(first.version_hash, second.version_hash)
        self.assertEqual(second.parent_hash, first.version_hash)
        self.assertEqual(first.content, "print(1)")
        with self.assertRaises(FrozenInstanceError):
            first.content = "mutated"
        self.assertEqual(review.version_hash, first.version_hash)
        self.assertTrue(review.stale)
        self.assertTrue(session.task("code").reviews[0].stale)
        self.assertEqual(session.task("code").state, TaskState.CANDIDATE)

    def test_all_tasks_consume_one_shared_atomic_budget(self):
        budget = ContestBudgetState(
            max_turns=3,
            max_api_calls=2,
            max_tokens=100,
            max_simulated_minutes=15,
        )
        session = ContestSession([TaskUnit("a"), TaskUnit("b")], budget)

        session.consume_budget(turns=1, api_calls=1, tokens=40, simulated_minutes=5)
        session.select_task("b")
        session.consume_budget(turns=2, api_calls=1, tokens=60, simulated_minutes=10)
        self.assertEqual(
            (
                budget.turns_used,
                budget.api_calls_used,
                budget.tokens_used,
                budget.simulated_minutes_used,
            ),
            (3, 2, 100, 15),
        )

        with self.assertRaises(BudgetExceededError):
            session.consume_budget(turns=1, tokens=1)
        self.assertEqual((budget.turns_used, budget.tokens_used), (3, 100))

    def test_programming_submissions_block_then_cool_down_and_first_ac_locks(self):
        session = ContestSession(
            [TaskUnit("code")],
            ContestBudgetState(max_turns=10),
            submission_policy=SubmissionPolicy(
                consecutive_non_ac_limit=3,
                cooldown_turns=2,
            ),
        )
        session.select_task("code")
        session.create_answer("attempt")

        session.submit("WA")
        session.submit("TLE")
        session.submit("RE")
        self.assertEqual(session.task("code").state, TaskState.BLOCKED)
        with self.assertRaises(TaskBlockedError):
            session.revisit_task("code")

        session.consume_budget(turns=2)
        session.revisit_task("code")
        session.create_answer("fixed")
        accepted = session.submit("AC")
        self.assertEqual(accepted.verdict, "AC")
        self.assertEqual(session.task("code").state, TaskState.SOLVED)
        with self.assertRaises(TaskLockedError):
            session.create_answer("too late")
        with self.assertRaises(TaskLockedError):
            session.record_review("agent-2", "too late")
        with self.assertRaises(TaskLockedError):
            session.submit("WA")

    def test_skipping_and_revisiting_preserve_a_candidate(self):
        session = ContestSession(
            [TaskUnit("a"), TaskUnit("b")],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("a")
        version = session.create_answer("work in progress")

        skipped = session.skip_task()
        self.assertEqual(skipped.task_id, "a")
        self.assertIsNone(session.active_task)
        self.assertEqual(session.task("a").state, TaskState.CANDIDATE)

        revisited = session.revisit_task("a")
        self.assertEqual(revisited.versions[-1], version)
        self.assertEqual(revisited.state, TaskState.CANDIDATE)
        session.select_task("b")
        self.assertEqual(session.task("a").state, TaskState.CANDIDATE)

    def test_non_programming_multipart_score_uses_latest_valid_part_submissions(self):
        session = ContestSession(
            [TaskUnit("report", kind="non_programming", parts=("analysis", "result"))],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("report")

        session.create_answer("analysis v1", part="analysis")
        session.submit("GRADED", score=3, part="analysis")
        self.assertEqual(session.task("report").part_scores, {"analysis": 3.0})
        self.assertEqual(session.task("report").state, TaskState.SUBMITTED)

        session.create_answer("result v1", part="result")
        session.submit("GRADED", score=4, part="result")
        session.create_answer("analysis v2", part="analysis")
        session.submit("GRADED", score=5, part="analysis")
        session.create_answer("invalid result", part="result")
        session.submit("INVALID", score=99, valid=False, part="result")

        task = session.task("report")
        self.assertEqual(task.part_scores, {"analysis": 5.0, "result": 4.0})
        self.assertEqual(task.score, 9.0)
        self.assertEqual(task.state, TaskState.SOLVED)

    def test_finalize_events_and_checkpoint_round_trip(self):
        session = ContestSession(
            [
                TaskUnit("code", kind="programming"),
                TaskUnit("essay", kind="non_programming"),
            ],
            ContestBudgetState(max_turns=10, max_tokens=100),
        )
        session.select_task("code")
        session.create_answer("wrong")
        session.submit("WA", score=50)
        session.select_task("essay")
        session.create_answer("final essay")
        session.submit("GRADED", score=7)

        summary = session.finalize()
        self.assertEqual(summary["tasks"]["code"]["score"], 0.0)
        self.assertEqual(summary["tasks"]["essay"]["score"], 7.0)
        self.assertEqual(summary["tasks"]["code"]["state"], "submitted")

        serialized_events = json.dumps(session.events)
        self.assertIn('"finalized"', serialized_events)
        exposed = session.events
        exposed[0]["type"] = "tampered"
        self.assertNotEqual(session.events[0]["type"], "tampered")

        wire_checkpoint = json.loads(json.dumps(session.checkpoint()))
        restored = ContestSession.from_checkpoint(wire_checkpoint)
        self.assertEqual(restored.checkpoint(), wire_checkpoint)
        self.assertEqual(restored.finalize(), summary)


if __name__ == "__main__":
    unittest.main()
