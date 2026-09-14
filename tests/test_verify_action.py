from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from env import OlympiadEnvironment  # noqa: E402


class InspectProblemActionTests(unittest.TestCase):
    """``inspect_problem`` is the desk's self-check; there is no separate ``verify``."""

    def test_programming_environment_exposes_executable_code_history(self) -> None:
        env = OlympiadEnvironment(
            "icpc",
            "icpc_wf_2012_bottles",
            max_turns=3,
            rules_mode="off",
        )
        # Not a contest tool: it is a desk action, so it is not gated by (and
        # does not appear in) the tool allowlist.
        self.assertEqual(env.get_available_tools(), ["execute_code"])
        env.execute_action("Agent_1", "execute_code", "print(1)")

        inspected = json.loads(
            env.execute_action("Agent_1", "inspect_problem", "| check edge cases")
        )

        self.assertEqual(inspected["focus"], "check edge cases")
        self.assertEqual(inspected["latest_code"], "print(1)")
        self.assertTrue(
            any(item["action"] == "execute_code" for item in inspected["history"])
        )
        self.assertEqual(env.action_log[-1]["action"], "inspect_problem")
        self.assertNotIn("invoked_as", env.action_log[-1])

        # Typed arguments are the same call.
        typed = json.loads(
            env.execute_action("Agent_1", "inspect_problem", {"focus": "check edge cases"})
        )
        self.assertEqual(typed["focus"], "check edge cases")
        self.assertEqual(typed["latest_code"], "print(1)")

    def test_legacy_verify_spelling_is_rejected(self) -> None:
        env = OlympiadEnvironment(
            "icpc",
            "icpc_wf_2012_bottles",
            max_turns=1,
            rules_mode="off",
        )
        result = env.execute_action("Agent_1", "verify", "check edge cases")
        self.assertIn("Unrecognized action 'verify'", result)
        self.assertEqual(env.action_log[-1]["action"], "verify")

    def test_inspect_on_a_board_contest_is_the_board_overview(self) -> None:
        env = OlympiadEnvironment(
            "arml_local",
            "arml_local_2009",
            max_turns=1,
            rules_mode="off",
        )
        self.assertNotIn("inspect_problem", env.get_available_tools())
        self.assertIn(
            "=== PROBLEM BOARD ===", env.execute_action("Agent_1", "inspect_problem", "")
        )

    def test_rule_aware_programming_keeps_inspect_available(self) -> None:
        env = OlympiadEnvironment(
            "icpc",
            "icpc_wf_2012_bottles",
            max_turns=1,
            rules_mode="enforced",
        )
        self.assertIn("execute_code", env.get_available_tools())
        self.assertNotIn(
            "RULE VIOLATION", env.execute_action("Agent_1", "inspect_problem", "| x")
        )


if __name__ == "__main__":
    unittest.main()
