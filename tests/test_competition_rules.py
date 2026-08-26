from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "collectors"))

from collaboration import (
    _agent_user_prompt,
    _system_prompt,
    run_round_table,
    CollabConfig,
)
from env import OlympiadEnvironment
from llm import mock_agent_llm
from rules import load_rule_card
from configure_coordination_rules import (
    COMMUNICATION_BUDGETS,
    ROLE_SPECIALIZED,
    STRUCTURED_DELIBERATION,
)


SCIENCE_BOWL_PROBLEM = (
    "science_bowl_sample_set_10_10a_hs_reg_2016_bonus_13"
)
ARML_PROBLEM = "arml_local_2009"
IEO_PROBLEM = "ieo_business_case_2021"
WSC_PROBLEM = "wsc_writing_gq_001"


class CompetitionRuleCardTests(unittest.TestCase):
    def test_science_bowl_rule_card_loads_by_competition_id(self):
        card = load_rule_card("science_bowl", required=True)

        self.assertEqual(card.competition_id, "science_bowl")
        self.assertEqual(card.profile, "proxy")
        self.assertEqual(card.protocol, "buzzer_match_question_proxy")
        self.assertEqual(card.team_size_default, 4)
        self.assertEqual(card.allowed_tools, ("query_rules",))
        self.assertGreaterEqual(len(card.human_constraints), 5)
        self.assertEqual(len(card.agent_roles), 4)

    def test_environment_applies_science_bowl_rule_card(self):
        env = OlympiadEnvironment("science_bowl", SCIENCE_BOWL_PROBLEM)
        metadata = env.get_metadata()

        self.assertEqual(env.team_size, 4)
        self.assertEqual(env.max_turns, 24)
        self.assertEqual(env.get_available_tools(), ["query_rules"])
        self.assertEqual(metadata["rule"]["rule_id"], "science_bowl:2026:question_proxy")
        self.assertEqual(metadata["rule"]["comparability"]["overall"], "non_comparable")
        self.assertIn("RULE VIOLATION", env.execute_action("Agent_1", "use_calculator", "2+2"))
        rules = env.query_rules("what are the rules")
        self.assertIn("human_constraints", rules)
        self.assertNotIn("evaluation_guidance", rules)
        self.assertNotIn("rubric_path", rules)
        self.assertNotIn('"scoring"', rules)

    def test_arml_local_injects_role_and_human_rules_into_agent_prompt(self):
        env = OlympiadEnvironment("arml_local", ARML_PROBLEM)
        prompt = _system_prompt(env, "Agent_3")

        self.assertIn("Calculators are not allowed on any ARML part", prompt)
        self.assertIn("HUMAN CONTEST RULES (BINDING)", prompt)
        self.assertIn("contestant", prompt)
        self.assertIn("May submit final answer: yes", prompt)
        self.assertEqual(env.get_available_tools(), ["query_rules"])

    def test_arml_local_mock_round_table_runs_with_gold_scoring_path(self):
        env = OlympiadEnvironment("arml_local", ARML_PROBLEM)
        result = run_round_table(
            env,
            mock_agent_llm,
            CollabConfig(rounds=1, synthesize=True),
        )

        self.assertTrue(result["submitted"])
        self.assertEqual(result["evaluation"]["scoring"]["mode"], "gold")
        self.assertEqual(len(result["roster"]), 6)
        self.assertEqual(result["submitted_by"], "Agent_1")

    def test_explicit_turn_budget_overrides_rule_card_safety_budget(self):
        env = OlympiadEnvironment(
            "science_bowl",
            SCIENCE_BOWL_PROBLEM,
            max_turns=7,
        )

        self.assertEqual(env.max_turns, 7)

    def test_business_case_prompts_share_rules_but_assign_rule_specialties(self):
        env = OlympiadEnvironment("ieo_business_case", IEO_PROBLEM)

        captain = _system_prompt(env, "Agent_1")
        analyst = _system_prompt(env, "Agent_2")
        designer = _system_prompt(env, "Agent_5")

        self.assertIn("No contact with anyone outside the team", captain)
        self.assertIn("No contact with anyone outside the team", analyst)
        self.assertIn("No contact with anyone outside the team", designer)
        self.assertIn("Timeline:", captain)
        self.assertIn("Integrity And Compliance:", analyst)
        self.assertIn("Deliverable Format:", designer)
        self.assertNotIn("PUBLIC EVALUATION GUIDANCE", captain)
        self.assertNotIn("PUBLIC EVALUATION GUIDANCE", analyst)
        self.assertNotIn("PUBLIC EVALUATION GUIDANCE", designer)
        self.assertNotIn("evaluation_guidance", captain)
        self.assertNotIn("rubric_path", analyst)
        self.assertIn("slide", designer)

    def test_query_rules_shows_common_rules_and_role_specialties(self):
        env = OlympiadEnvironment("ieo_business_case", IEO_PROBLEM)

        analyst_view = env.execute_action("Agent_2", "query_rules", "all rules")
        captain_view = env.execute_action("Agent_1", "query_rules", "all rules")
        designer_view = env.execute_action("Agent_5", "query_rules", "rubric")

        self.assertIn("human_constraints", analyst_view)
        self.assertNotIn("rubric_path", analyst_view)
        self.assertIn("human_constraints", captain_view)
        self.assertNotIn("rubric_path", captain_view)
        self.assertNotIn("evaluation_guidance", designer_view)
        self.assertNotIn("rubric_path", designer_view)
        self.assertNotIn("evaluator_id", designer_view)
        self.assertIn("integrity_and_compliance", analyst_view)
        self.assertIn("timeline", captain_view)
        self.assertIn("deliverable_format", designer_view)

    def test_role_specialized_code_cannot_read_repository_files(self):
        env = OlympiadEnvironment("ieo_business_case", IEO_PROBLEM)

        blocked = env.execute_action(
            "Agent_3",
            "execute_code",
            "print(open('data/rules/ieo_business_case.json').read())",
        )
        computation = env.execute_action(
            "Agent_3",
            "execute_code",
            "import statistics\nprint(statistics.mean([10, 20, 30]))",
        )

        self.assertIn("filesystem", blocked)
        self.assertIn("20", computation)

    def test_writing_roles_must_exchange_rules_and_evaluation_guidance(self):
        env = OlympiadEnvironment("wsc_writing", WSC_PROBLEM)

        planner = _system_prompt(env, "Agent_1")
        writer = _system_prompt(env, "Agent_2")

        self.assertIn("The team receives three to four prompts", planner)
        self.assertIn("The team receives three to four prompts", writer)
        self.assertIn("AGENT COLLABORATION RULES", planner)
        self.assertIn("Timeline:", planner)
        self.assertIn("Resource Policy:", writer)
        self.assertNotIn("PUBLIC EVALUATION GUIDANCE", planner)
        self.assertNotIn("PUBLIC EVALUATION GUIDANCE", writer)

    def test_selected_coordination_tracks_have_asymmetric_information(self):
        for competition_id in (
            "ieo_business_case",
            "cfa_research_challenge",
            "wharton_investment",
            "gcch_harvard",
            "wsc_writing",
        ):
            with self.subTest(competition=competition_id):
                card = load_rule_card(competition_id, required=True)
                self.assertEqual(
                    card.information_policy.get("mode"), "role_specialized"
                )
                access_sets = {
                    role.rule_expertise for role in card.agent_roles
                }
                self.assertGreaterEqual(len(access_sets), 2)
                self.assertTrue(
                    all(
                        "contest_rules" in role.information_access
                        for role in card.agent_roles
                    )
                )
                self.assertEqual(
                    card.deliberation.get("mode"), "structured"
                )

    def test_coordination_overlay_matches_curated_policy_matrix(self):
        import json

        index = json.loads(
            (REPO_ROOT / "data" / "benchmarks" / "index.json").read_text(
                encoding="utf-8"
            )
        )
        for olympiad in index["olympiads"]:
            competition_id = olympiad["id"]
            card = load_rule_card(competition_id, required=True)
            with self.subTest(competition=competition_id):
                is_specialized = competition_id in ROLE_SPECIALIZED
                self.assertEqual(
                    card.information_policy.get("mode") == "role_specialized",
                    is_specialized,
                )
                self.assertEqual(
                    card.deliberation.get("mode") == "structured",
                    competition_id in STRUCTURED_DELIBERATION,
                )
                self.assertEqual(
                    card.communication.get("mode") == "limited",
                    competition_id in COMMUNICATION_BUDGETS,
                )
                if is_specialized:
                    self.assertTrue(card.rule_sections)
                    for role in card.agent_roles:
                        self.assertIn("contest_rules", role.information_access)
                        self.assertTrue(role.rule_expertise)
                        self.assertTrue(
                            set(role.rule_expertise).issubset(card.rule_sections)
                        )
                if competition_id in COMMUNICATION_BUDGETS:
                    team, per_agent, max_chars = COMMUNICATION_BUDGETS[
                        competition_id
                    ]
                    self.assertEqual(
                        (
                            card.communication["team_message_budget"],
                            card.communication["per_agent_message_budget"],
                            card.communication["max_message_chars"],
                        ),
                        (team, per_agent, max_chars),
                    )

    def test_disagreement_protocol_records_evidence_revision_and_decision(self):
        env = OlympiadEnvironment("ieo_business_case", IEO_PROBLEM)

        proposal = env.execute_action(
            "Agent_2", "propose", "Prioritize the premium market segment."
        )
        challenge = env.execute_action(
            "Agent_3",
            "challenge",
            "P1 | The sample is too small to support premium demand.",
        )
        evidence = env.execute_action(
            "Agent_4",
            "provide_evidence",
            "P1 | Survey results show stronger demand in the mid-market segment.",
        )
        revision = env.execute_action(
            "Agent_2",
            "revise",
            "P1 | Prioritize the mid-market segment and test premium demand later.",
        )
        decision = env.execute_action(
            "Agent_1",
            "decide",
            "P1 | accept | The revised claim fits the cited demand evidence.",
        )

        self.assertIn("P1 proposed", proposal)
        self.assertIn("challenge on P1", challenge)
        self.assertIn("provide_evidence on P1", evidence)
        self.assertIn("revise on P1", revision)
        self.assertIn("accept", decision)

        report = env.deliberation.report()
        self.assertEqual(report["counts"]["challenge"], 1)
        self.assertEqual(report["counts"]["provide_evidence"], 1)
        self.assertEqual(report["counts"]["revise"], 1)
        self.assertEqual(report["counts"]["decide"], 1)
        self.assertEqual(report["evidence_led_revisions"], 1)
        self.assertEqual(report["decisions_after_evidence"], 1)
        self.assertEqual(report["open_proposals"], [])

    def test_disagreement_protocol_enforces_role_responsibilities(self):
        env = OlympiadEnvironment("ieo_business_case", IEO_PROBLEM)
        env.execute_action("Agent_2", "propose", "Use a premium strategy.")

        self_challenge = env.execute_action(
            "Agent_2", "challenge", "P1 | I disagree with myself."
        )
        foreign_revision = env.execute_action(
            "Agent_3", "revise", "P1 | Replace it with a mass-market strategy."
        )
        worker_decision = env.execute_action(
            "Agent_3", "decide", "P1 | reject | My model disagrees."
        )

        self.assertIn("cannot challenge their own", self_challenge)
        self.assertIn("only the proposal author", foreign_revision)
        self.assertIn("only a designated submitter", worker_decision)

    def test_limited_communication_budget_forces_private_work(self):
        env = OlympiadEnvironment("ieo_business_case", IEO_PROBLEM)

        for index in range(3):
            result = env.execute_action(
                "Agent_2", "speak", f"Counted update {index + 1}"
            )
            self.assertIn("broadcast", result)
        rejected = env.execute_action(
            "Agent_2", "speak", "One update too many"
        )
        private = env.execute_action(
            "Agent_2",
            "write_private_notes",
            "Privately compare segment assumptions before sending a conclusion.",
        )

        self.assertIn("COMMUNICATION LIMIT", rejected)
        self.assertIn("no communication budget used", private)
        report = env.communication.report()
        self.assertEqual(report["by_agent"]["Agent_2"], 3)
        self.assertEqual(report["team_used"], 3)
        self.assertEqual(len(report["rejected"]), 1)

    def test_private_notes_are_visible_only_to_their_author(self):
        env = OlympiadEnvironment("ieo_business_case", IEO_PROBLEM)
        secret = "Sensitivity analysis favors the mid-market scenario."
        env.execute_action("Agent_3", "write_private_notes", secret)

        modeler_prompt = _agent_user_prompt(env, "Agent_3", "test")
        analyst_prompt = _agent_user_prompt(env, "Agent_2", "test")

        self.assertIn(secret, modeler_prompt)
        self.assertNotIn(secret, analyst_prompt)
        self.assertNotIn(secret, str(env.chat_history))
        self.assertEqual(env.communication.report()["team_used"], 0)

    def test_communication_budget_rejects_oversized_messages(self):
        env = OlympiadEnvironment("wsc_writing", WSC_PROBLEM)

        rejected = env.execute_action("Agent_2", "speak", "x" * 1201)

        self.assertIn("1201 characters", rejected)
        self.assertEqual(env.communication.report()["team_used"], 0)

    def test_ground_truth_rule_cards_exist(self):
        for competition_id in (
            "arml_local",
            "purple_comet",
            "wmtc",
            "qanta",
            "science_bowl",
        ):
            card = load_rule_card(competition_id, required=True)
            self.assertEqual(card.scoring.get("mode"), "gold")
            self.assertTrue(card.human_constraints)
            self.assertTrue(card.agent_roles)

    def test_every_index_competition_has_a_loadable_rule_card(self):
        import json

        index = json.loads((REPO_ROOT / "data" / "benchmarks" / "index.json").read_text(
            encoding="utf-8"
        ))
        for olympiad in index["olympiads"]:
            card = load_rule_card(olympiad["id"], required=True)
            self.assertEqual(card.competition_id, olympiad["id"])
            self.assertTrue(card.human_constraints)
            self.assertEqual(len(card.agent_roles), card.team_size_default)

    def test_index_points_at_base_layout(self):
        import json

        index = json.loads(
            (REPO_ROOT / "data" / "benchmarks" / "index.json").read_text(encoding="utf-8")
        )
        self.assertEqual(index.get("base_root"), "data/base")
        self.assertEqual(index.get("task_cards_path"), "data/base/task_cards.json")

        base_index = json.loads(
            (REPO_ROOT / "data" / "base" / "index.json").read_text(encoding="utf-8")
        )
        base_ids = {row["id"] for row in base_index["competitions"]}

        for olympiad in index["olympiads"]:
            with self.subTest(competition=olympiad["id"]):
                self.assertEqual(
                    olympiad["base_path"], f"data/base/tasks/{olympiad['id']}"
                )
                self.assertIn(olympiad["id"], base_ids)
                self.assertGreaterEqual(olympiad["base_tasks"], 0)
                if olympiad["base_tasks"]:
                    self.assertTrue((REPO_ROOT / olympiad["base_path"]).is_dir())


if __name__ == "__main__":
    unittest.main()
