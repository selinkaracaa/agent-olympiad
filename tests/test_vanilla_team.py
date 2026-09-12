from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import CollabConfig, SCHEMAS, run_collaboration  # noqa: E402
from env import OlympiadEnvironment  # noqa: E402


class VanillaTeamTests(unittest.TestCase):
    def make_env(self, turns: int = 1) -> OlympiadEnvironment:
        return OlympiadEnvironment(
            "arml_local",
            "arml_local_2009",
            max_turns=turns,
            rules_mode="off",
        )

    def test_vanilla_schema_is_rules_off_and_prompt_minimal(self) -> None:
        self.assertIn("vanilla_team", SCHEMAS)
        env = self.make_env()
        calls: list[tuple[str, str]] = []

        def query(system: str, user: str) -> str:
            calls.append((system, user))
            return "ACTION: rest | PAYLOAD: no contribution"

        result = run_collaboration(
            "vanilla_team",
            env,
            query,
            CollabConfig(max_turns=1, synthesize=False),
        )

        self.assertIsNone(env.rule_card)
        self.assertEqual(result["schema"], "vanilla_team")
        self.assertEqual(result["api_calls"], env.team_size)
        rendered = "\n".join(system + "\n" + user for system, user in calls).lower()
        self.assertNotIn("coach", rendered)
        self.assertNotIn("rule card", rendered)
        self.assertNotIn("recovery", rendered)
        self.assertNotIn("mandatory review", rendered)

    def test_vanilla_executes_at_most_one_action_per_call(self) -> None:
        env = self.make_env()

        result = run_collaboration(
            "vanilla_team",
            env,
            lambda _system, _user: (
                "ACTION: speak | PAYLOAD: first\n"
                "ACTION: submit_final | PAYLOAD: forbidden second action"
            ),
            CollabConfig(max_turns=1, max_api_calls=1, synthesize=False),
        )

        self.assertFalse(result["submitted"])
        self.assertEqual(env.action_log[0]["action"], "rest")
        self.assertIn("exactly one", env.action_log[0]["protocol_error"])

    def test_vanilla_synthesis_is_one_charged_plain_call(self) -> None:
        env = self.make_env()
        responses = iter(
            [
                *["ACTION: rest | PAYLOAD: done" for _ in range(env.team_size)],
                "\n".join(f"{index}. answer" for index in range(1, 11)),
            ]
        )

        result = run_collaboration(
            "vanilla_team",
            env,
            lambda _system, _user: next(responses),
            CollabConfig(max_turns=1, max_api_calls=env.team_size + 1, synthesize=True),
        )

        self.assertTrue(result["submitted"])
        self.assertEqual(result["api_calls"], env.team_size + 1)
        self.assertEqual(result["submitted_by"], "Agent_1")


if __name__ == "__main__":
    unittest.main()
