from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import CollabConfig, run_open_table_coach  # noqa: E402
from env import OlympiadEnvironment  # noqa: E402
from evaluation.collaboration_score import format_agent_profiles  # noqa: E402
from llm import mock_agent_llm  # noqa: E402
from run_phase_b_matrix import agent_roster, models_for_team  # noqa: E402


class OpenTableCoachTests(unittest.TestCase):
    def make_env(self, turns: int = 3) -> OlympiadEnvironment:
        return OlympiadEnvironment(
            competition_id="arml_local",
            problem_id="arml_local_2009",
            max_turns=turns,
        )

    def test_coach_brief_is_problem_blind_and_coach_exits_after_opening(self):
        env = self.make_env(turns=3)
        calls: list[tuple[str, str]] = []

        def query(system: str, user: str) -> str:
            calls.append((system, user))
            return "ACTION: speak | PAYLOAD: phase contribution"

        result = run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=3, synthesize=False),
        )

        first_system, first_user = calls[0]
        self.assertIn("You are Coach", first_system)
        self.assertNotIn("=== PROBLEM ===", first_user)
        self.assertNotIn(env.get_state()["problem_statement"], first_user)
        self.assertNotIn('"evaluation_guidance"', first_user)
        self.assertNotIn('"scoring"', first_user)

        coach_turns = [
            item["turn"] for item in env.action_log if item["agent"] == "Coach"
        ]
        self.assertEqual(coach_turns, [1, 2])
        self.assertFalse(
            any(
                "You are Coach" in system
                for system, _ in calls[1 + env.team_size + 1 :]
            )
        )
        self.assertEqual(result["turns_used"], 3)
        self.assertLessEqual(result["api_calls"], env.team_size * result["max_turns"])

    def test_coach_actions_are_limited_by_code(self):
        env = self.make_env(turns=2)

        def query(system: str, user: str) -> str:
            if "You are Coach" in system and "pre-contest" in system:
                return "ACTION: execute_code | PAYLOAD: print('forbidden')"
            if "You are Coach" in system:
                return "ACTION: submit_final | PAYLOAD: forbidden answer"
            return "ACTION: speak | PAYLOAD: contestant contribution"

        run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=2, synthesize=False),
        )

        coach_actions = [
            item["action"] for item in env.action_log if item["agent"] == "Coach"
        ]
        self.assertEqual(coach_actions, ["sleep", "sleep"])
        self.assertFalse(env.submitted)
        self.assertEqual(env.workspace["scratchpad"], "")

    def test_preparation_uses_the_shared_api_budget(self):
        env = self.make_env(turns=3)

        result = run_open_table_coach(
            env,
            lambda _system, _user: "ACTION: speak | PAYLOAD: brief",
            CollabConfig(max_turns=3, max_api_calls=1, synthesize=False),
        )

        self.assertEqual(result["api_calls"], 1)
        self.assertEqual(result["turns_used"], 1)
        self.assertEqual(
            [item["agent"] for item in env.action_log],
            ["Coach"],
        )

    def test_agent_one_not_coach_performs_final_synthesis(self):
        env = self.make_env(turns=2)

        result = run_open_table_coach(
            env,
            mock_agent_llm,
            CollabConfig(max_turns=2, synthesize=True),
        )

        self.assertTrue(result["submitted"])
        self.assertEqual(result["submitted_by"], "Agent_1")

    def test_missing_rule_card_uses_public_metadata_fallback(self):
        env = self.make_env(turns=1)
        prompts: list[str] = []

        def query(_system: str, user: str) -> str:
            prompts.append(user)
            return "ACTION: speak | PAYLOAD: brief"

        with patch("collaboration.load_rule_card", return_value=None):
            run_open_table_coach(
                env,
                query,
                CollabConfig(max_turns=1, synthesize=False),
            )

        self.assertIn('"competition_id": "arml_local"', prompts[0])
        self.assertIn('"allowed_tools"', prompts[0])

    def test_roster_and_evaluator_identify_the_coach_role(self):
        roster = agent_roster("open_table_coach", 3)
        self.assertEqual(roster, ["Agent_1", "Agent_2", "Agent_3", "Coach"])

        models = models_for_team(
            "hetero",
            "open_table_coach",
            "icpc",
            "icpc_wf_2012_bottles",
        )
        self.assertEqual(models["Coach"], models["Agent_1"])

        profiles = format_agent_profiles(roster, "open_table_coach")
        self.assertIn("Coach: pre-contest and opening-turn adviser", profiles)
        self.assertIn("cannot use tools or submit", profiles)


if __name__ == "__main__":
    unittest.main()
