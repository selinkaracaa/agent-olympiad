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
            if "PRIVATE DELIBERATION ONLY" in system:
                return "Private working note."
            return "ACTION: speak | PAYLOAD: phase contribution"

        result = run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=3, synthesize=False),
        )

        opening_coach_call = 1 + (2 * env.team_size)
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
            if "PRIVATE DELIBERATION ONLY" in system:
                return "Private working note."
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

    def test_contestants_choose_one_isolated_action_per_turn(self) -> None:
        env = self.make_env(3)
        calls: list[tuple[str, str]] = []
        private_secret = "private factorization only Agent_1 may see"
        direct_summary = "Agent_2: please verify my P1 candidate."
        group_proof = "P2 proof shared only with Agent_1."

        def query(system: str, user: str) -> str:
            calls.append((system, user))
            if "PRIVATE DELIBERATION ONLY" in system:
                return (
                    private_secret
                    if system.startswith("You are Agent_1")
                    else "private working note"
                )
            if system.startswith("You are Coach"):
                return "ACTION: speak | PAYLOAD: concise coach guidance"
            if system.startswith("You are Agent_1"):
                if "Contestant-only collaboration turn 3" in user:
                    return "ACTION: speak | PAYLOAD: P1 checked; use the shared result."
                return (
                    "ACTION: speak | TARGET: Agent_2 | "
                    f"PAYLOAD: {direct_summary}"
                )
            if system.startswith("You are Agent_2"):
                if "Contestant-only collaboration turn 3" in user:
                    return "ACTION: rest | PAYLOAD: work complete"
                return (
                    "ACTION: work | TARGET: Agent_1 | "
                    f"PAYLOAD: {group_proof}"
                )
            if system.startswith("You are Agent_3"):
                if "Contestant-only collaboration turn 3" in user:
                    return "ACTION: rest | PAYLOAD:"
                return "ACTION: speak | PAYLOAD: " + ("S" * 500)
            if system.startswith("You are Agent_4"):
                return "ACTION: rest | PAYLOAD: " + ("R" * 200)
            if system.startswith("You are Agent_5"):
                if "Contestant-only collaboration turn 3" in user:
                    return "ACTION: rest | PAYLOAD:"
                return (
                    "ACTION: think | PAYLOAD: first\n"
                    "ACTION: speak | PAYLOAD: second"
                )
            if system.startswith("You are Agent_6"):
                if "Contestant-only collaboration turn 3" in user:
                    return "ACTION: submit_final | PAYLOAD: premature answer"
                return "unstructured long reasoning must not become public speech"
            if "Contestant-only collaboration turn 3" in user:
                return "ACTION: rest | PAYLOAD:"
            return "ACTION: rest | PAYLOAD:"

        result = run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=3, synthesize=False),
        )

        self.assertEqual(result["api_calls"], 26)
        self.assertNotIn(
            "think",
            [item["action"] for item in env.action_log],
        )
        self.assertEqual(
            env.private_thoughts["Agent_1"][0]["content"],
            private_secret,
        )
        self.assertEqual(
            env.workspace["work_artifacts"][0]["content"],
            group_proof,
        )

        agent_1_prompts = [
            user for system, user in calls if system.startswith("You are Agent_1")
        ]
        agent_2_prompts = [
            user for system, user in calls if system.startswith("You are Agent_2")
        ]
        agent_3_prompts = [
            user for system, user in calls if system.startswith("You are Agent_3")
        ]
        coach_prompts = [
            user
            for system, user in calls
            if system.startswith("You are Coach")
        ]
        self.assertIn(private_secret, agent_1_prompts[-1])
        self.assertNotIn(private_secret, agent_2_prompts[-1])
        self.assertIn(direct_summary, agent_2_prompts[-1])
        self.assertNotIn(direct_summary, agent_3_prompts[-1])
        self.assertIn(group_proof, agent_1_prompts[-1])
        self.assertNotIn(group_proof, agent_3_prompts[-1])
        self.assertNotIn(group_proof, coach_prompts[-1])

        agent_3_message = next(
            item["message"]
            for item in env.chat_history
            if item["sender"] == "Agent_3"
        )
        self.assertEqual(len(agent_3_message), 320)
        self.assertTrue(agent_3_message.endswith("…"))
        self.assertFalse(
            any(
                item["sender"] in {"Agent_5", "Agent_6"}
                for item in env.chat_history
            )
        )
        self.assertFalse(env.submitted)
        self.assertEqual(env.protocol_action_counts["Agent_1"]["think"], 2)
        self.assertEqual(env.protocol_action_counts["Agent_1"]["speak"], 2)
        self.assertEqual(env.protocol_action_counts["Agent_2"]["work"], 1)
        self.assertEqual(env.protocol_action_counts["Agent_5"]["rest"], 2)
        self.assertTrue(
            any(
                "exactly one structured ACTION" in violation
                for violation in env.rule_violations
            )
        )
        transcript = env.to_transcript()
        self.assertIn("private_thoughts", transcript)
        self.assertIn("group_messages", transcript)
        self.assertNotIn(private_secret, str(transcript["action_log"]))
        self.assertEqual(result["shared_work_artifacts"], 1)

    def test_speak_budget_exhaustion_disables_speak_without_immediate_stop(
        self,
    ) -> None:
        env = self.make_env(12)
        calls: list[tuple[str, str]] = []

        def query(system: str, user: str) -> str:
            calls.append((system, user))
            if "PRIVATE DELIBERATION ONLY" in system:
                return "Private working note."
            return "ACTION: speak | PAYLOAD: concise update"

        result = run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=12, synthesize=False),
        )

        self.assertEqual(env.communication.team_used, 60)
        self.assertGreater(result["api_calls"], 60)
        self.assertEqual(result["turns_used"], 12)
        self.assertEqual(result["stop_reason"], "all_contestants_ready")
        self.assertFalse(env.communication.rejected)

    def test_all_contestants_rest_ends_before_max_turns(self) -> None:
        env = self.make_env(12)

        def query(system: str, user: str) -> str:
            if "PRIVATE DELIBERATION ONLY" in system:
                return "Private working note."
            if system.startswith("You are Coach"):
                return "ACTION: speak | PAYLOAD: concise guidance"
            if "Contestant-only collaboration turn" in user:
                return "ACTION: rest | PAYLOAD: all assigned work is complete"
            return "ACTION: work | PAYLOAD: initial assigned solution"

        result = run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=12, synthesize=False),
        )

        self.assertEqual(result["turns_used"], 10)
        self.assertEqual(result["api_calls"], 110)
        self.assertEqual(result["stop_reason"], "all_contestants_ready")

    def test_open_table_prompt_has_only_turn_protocol_actions(self) -> None:
        env = self.make_env(2)
        contestant_systems: list[str] = []

        def query(system: str, _user: str) -> str:
            if "PRIVATE DELIBERATION ONLY" in system:
                return "Private working note."
            if system.startswith("You are Agent_"):
                contestant_systems.append(system)
                return "ACTION: rest | PAYLOAD:"
            return "ACTION: sleep | PAYLOAD:"

        run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=2, synthesize=False),
        )

        self.assertTrue(contestant_systems)
        action_systems = [
            system
            for system in contestant_systems
            if "OPEN-TABLE SINGLE-ACTION PROTOCOL" in system
        ]
        self.assertTrue(action_systems)
        for system in action_systems:
            self.assertNotIn("ACTION: write_scratchpad", system)
            self.assertNotIn("ACTION: submit_final", system)
            self.assertIn("ONLY valid actions this turn", system)

    def test_silent_work_turn_forces_a_discussion_turn(self) -> None:
        env = self.make_env(4)
        action_systems_by_turn: dict[int, list[str]] = {}

        def query(system: str, user: str) -> str:
            if "PRIVATE DELIBERATION ONLY" in system:
                return "Private working note."
            if system.startswith("You are Coach"):
                return "ACTION: speak | PAYLOAD: concise guidance"
            for turn in (2, 3, 4):
                if f"turn {turn} of" in user.lower():
                    action_systems_by_turn.setdefault(turn, []).append(system)
                    if turn == 3:
                        return (
                            "ACTION: speak | TARGET: public | "
                            "PAYLOAD: reporting my prior result"
                        )
                    return (
                        "ACTION: work | TARGET: public | "
                        "PAYLOAD: Q1 | new derivation"
                    )
            return "ACTION: rest | PAYLOAD:"

        run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=4, synthesize=False),
        )

        self.assertTrue(action_systems_by_turn[3])
        self.assertTrue(
            all("ACTION: work" not in system for system in action_systems_by_turn[3])
        )
        self.assertTrue(
            all("ACTION: speak" in system for system in action_systems_by_turn[3])
        )
        self.assertTrue(
            all("ACTION: work" in system for system in action_systems_by_turn[4])
        )

    def test_synthesis_requires_independent_checks_and_no_visual_guessing(self) -> None:
        env = self.make_env(2)
        synthesis_prompts: list[str] = []
        self.assertIn("3^{f(3)+f(9)}", env._problem_statement())

        def query(system: str, user: str) -> str:
            if "official final answer sheet" in system:
                synthesis_prompts.append(user)
                return "\n".join(f"{index}. checked" for index in range(1, 11))
            if system.startswith("You are Coach"):
                return "ACTION: sleep | PAYLOAD:"
            return "ACTION: rest | PAYLOAD:"

        run_open_table_coach(
            env,
            query,
            CollabConfig(max_turns=2, synthesize=True),
        )

        self.assertEqual(len(synthesis_prompts), 1)
        prompt = synthesis_prompts[0]
        self.assertIn("independently recompute", prompt)
        self.assertIn("Do not use agreement or repetition as evidence", prompt)
        self.assertIn("probability mass sums to 1", prompt)
        self.assertIn("enumerate mutually exclusive winning cases", prompt)
        self.assertIn("leave that numbered answer blank", prompt)


if __name__ == "__main__":
    unittest.main()
