from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from env import OlympiadEnvironment
from rules import PhaseSchedule, RulesMode


class ContestPhaseTests(unittest.TestCase):
    def test_ieo_enforced_blocks_early_submit(self) -> None:
        env = OlympiadEnvironment(
            "ieo_business_case",
            "ieo_business_case_2021",
            rules_mode=RulesMode.ENFORCED,
        )
        self.assertIsNotNone(env.phase_schedule)
        env.begin_turn()
        self.assertEqual(env.current_turn, 1)
        violation = env.validate_action("submit_final", "Agent_1")
        self.assertIsNotNone(violation)
        assert violation is not None
        self.assertIn("locked", violation)

    def test_ieo_enforced_blocks_web_search_after_prep(self) -> None:
        env = OlympiadEnvironment(
            "ieo_business_case",
            "ieo_business_case_2021",
            rules_mode=RulesMode.ENFORCED,
        )
        env.current_turn = 21
        violation = env.validate_action("web_search", "Agent_1")
        self.assertIsNotNone(violation)
        assert violation is not None
        self.assertIn("banned", violation)

    def test_phase_transition_announced_in_chat(self) -> None:
        env = OlympiadEnvironment(
            "ieo_business_case",
            "ieo_business_case_2021",
            rules_mode=RulesMode.ENFORCED,
        )
        for _ in range(21):
            env.begin_turn()
        self.assertTrue(
            any(
                "Slide lock" in item.get("message", "")
                for item in env.chat_history
                if item.get("sender") == "Contest_Control"
            )
        )

    def test_off_mode_ignores_phases(self) -> None:
        env = OlympiadEnvironment("ieo_business_case", "ieo_business_case_2021")
        self.assertIsNone(env.phase_schedule)
        env.begin_turn()
        self.assertIsNone(env.validate_action("submit_final", "Solo"))


if __name__ == "__main__":
    unittest.main()
