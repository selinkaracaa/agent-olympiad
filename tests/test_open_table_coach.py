from __future__ import annotations

import sys
import unittest
from pathlib import Path

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
            rules_mode="enforced",
        )

    def test_three_stages_and_problem_access(self) -> None:
        env = self.make_env(3)
        calls: list[tuple[str, str]] = []

        def query(system: str, user: str) -> str:
            calls.append((system, user))
            return "ACTION: speak | PAYLOAD: phase contribution"

        result = run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=3, synthesize=False),
        )

        opening_coach_call = 1 + env.team_size
        self.assertNotIn(env._problem_statement(), calls[0][1])
        self.assertIn(env._problem_statement(), calls[opening_coach_call][1])
        self.assertEqual(
            [item["turn"] for item in env.action_log if item["agent"] == "Coach"],
            [1, 2],
        )
        self.assertFalse(
            any(
                "You are Coach" in system
                for system, _ in calls[opening_coach_call + 1 :]
            )
        )
        self.assertEqual(result["turns_used"], 3)

    def test_coach_actions_are_limited_by_code(self) -> None:
        env = self.make_env(2)

        def query(system: str, _user: str) -> str:
            if "You are Coach" in system and "pre-contest brief" in system:
                return "ACTION: execute_code | PAYLOAD: print('forbidden')"
            if "You are Coach" in system:
                return "ACTION: submit_final | PAYLOAD: forbidden answer"
            return "ACTION: speak | PAYLOAD: contestant contribution"

        run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=2, synthesize=False),
        )

        self.assertEqual(
            [
                item["action"]
                for item in env.action_log
                if item["agent"] == "Coach"
            ],
            ["sleep", "sleep"],
        )
        self.assertFalse(env.submitted)
        self.assertEqual(env.workspace["scratchpad"], "")

    def test_preparation_uses_shared_budget(self) -> None:
        env = self.make_env(3)
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

    def test_agent_one_performs_final_synthesis(self) -> None:
        result = run_open_table_coach(
            self.make_env(2),
            mock_agent_llm,
            CollabConfig(max_turns=2, synthesize=True),
        )
        self.assertTrue(result["submitted"])
        self.assertEqual(result["submitted_by"], "Agent_1")

    def test_result_labels_counterfactual_policy(self) -> None:
        result = run_open_table_coach(
            self.make_env(1),
            lambda _system, _user: "ACTION: speak | PAYLOAD: brief",
            CollabConfig(max_turns=1, synthesize=False),
        )
        self.assertEqual(
            result["coach_policy_status"],
            "counterfactual_synthetic_baseline_not_official_arml_rule",
        )
        self.assertFalse(result["coach_problem_access"]["precontest_brief"])
        self.assertTrue(result["coach_problem_access"]["opening_discussion"])

    def test_roster_models_and_evaluator_include_coach(self) -> None:
        roster = agent_roster("open_table_coach", 3)
        self.assertEqual(roster, ["Agent_1", "Agent_2", "Agent_3", "Coach"])
        models = models_for_team(
            "hetero",
            "open_table_coach",
            "arml_local",
            "arml_local_2009",
            rules_mode="enforced",
        )
        self.assertEqual(models["Coach"], models["Agent_1"])
        profiles = format_agent_profiles(roster, "open_table_coach")
        self.assertIn("Coach: problem-blind pre-contest adviser", profiles)
        self.assertIn("exits after turn 2", profiles)


if __name__ == "__main__":
    unittest.main()
