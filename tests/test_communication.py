from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from communication import CommunicationBudget  # noqa: E402


class CommunicationCompactionTests(unittest.TestCase):
    def make_budget(self) -> CommunicationBudget:
        return CommunicationBudget(
            {
                "mode": "limited",
                "team_message_budget": 3,
                "per_agent_message_budget": 2,
                "max_message_chars": 1200,
                "counted_actions": ["speak"],
            }
        )

    def test_payload_at_limit_is_unchanged(self) -> None:
        budget = self.make_budget()
        payload = "x" * 12
        compacted, metadata = budget.compact_payload(
            agent_name="Agent_1",
            action_type="speak",
            payload=payload,
            turn=1,
            max_chars=12,
        )
        self.assertEqual(compacted, payload)
        self.assertFalse(metadata["compacted"])
        self.assertEqual(budget.compacted, [])

    def test_long_payload_is_compacted_at_sentence_boundary(self) -> None:
        budget = self.make_budget()
        compacted, metadata = budget.compact_payload(
            agent_name="Agent_2",
            action_type="speak",
            payload="Keep this conclusion. " + ("detail " * 30),
            turn=2,
            max_chars=40,
        )
        self.assertLessEqual(len(compacted), 40)
        self.assertTrue(compacted.startswith("Keep this conclusion."))
        self.assertTrue(compacted.endswith("…"))
        self.assertTrue(metadata["compacted"])
        self.assertEqual(budget.compacted[0]["action"], "speak")
        self.assertEqual(budget.report()["compacted"][0]["original_chars"], 231)

    def test_compaction_does_not_spend_message_budget(self) -> None:
        budget = self.make_budget()
        compacted, _ = budget.compact_payload(
            agent_name="Agent_1",
            action_type="speak",
            payload="x" * 100,
            turn=1,
            max_chars=20,
        )
        self.assertIsNone(
            budget.check(
                agent_name="Agent_1",
                action_type="speak",
                payload=compacted,
                turn=1,
            )
        )
        self.assertEqual(budget.team_used, 0)
        budget.record(agent_name="Agent_1", action_type="speak")
        self.assertEqual(budget.team_used, 1)


if __name__ == "__main__":
    unittest.main()
