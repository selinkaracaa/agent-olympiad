from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_session import TaskState, TaskUnit  # noqa: E402
from strategy import StrategicPolicy  # noqa: E402


class StrategicPolicyTests(unittest.TestCase):
    def test_blocked_problem_switches_before_stall_threshold(self) -> None:
        policy = StrategicPolicy(stall_turns=4)
        task = TaskUnit("a", state=TaskState.BLOCKED, blocked_until_turn=8)
        self.assertEqual(
            policy.switch_reason(task, current_turn=3, last_progress_turn=3),
            "three_consecutive_non_ac",
        )

    def test_stalled_candidate_switches_but_fresh_candidate_continues(self) -> None:
        policy = StrategicPolicy(stall_turns=3)
        task = TaskUnit("a", kind="non_programming", state=TaskState.CANDIDATE)
        self.assertIsNone(
            policy.switch_reason(task, current_turn=4, last_progress_turn=2)
        )
        self.assertEqual(
            policy.switch_reason(task, current_turn=5, last_progress_turn=2),
            "stalled_turns",
        )

    def test_cooldown_revisit_requires_expiry(self) -> None:
        policy = StrategicPolicy()
        task = TaskUnit("a", state=TaskState.BLOCKED, blocked_until_turn=5)
        self.assertFalse(policy.can_revisit(task, current_turn=4))
        self.assertTrue(policy.can_revisit(task, current_turn=5))


if __name__ == "__main__":
    unittest.main()
