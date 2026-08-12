from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import _system_prompt, run_round_table, CollabConfig
from env import OlympiadEnvironment
from llm import mock_agent_llm
from rules import load_rule_card


SCIENCE_BOWL_PROBLEM = (
    "science_bowl_sample_set_10_10a_hs_reg_2016_bonus_13"
)
ARML_PROBLEM = "arml_local_2009"


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
        self.assertIn("human_constraints", env.query_rules("what are the rules"))

    def test_arml_local_injects_role_and_human_rules_into_agent_prompt(self):
        env = OlympiadEnvironment("arml_local", ARML_PROBLEM)
        prompt = _system_prompt(env, "Agent_3")

        self.assertIn("Paper and pencil only; calculators are banned on every ARML round.", prompt)
        self.assertIn("HUMAN CONTEST RULES (BINDING)", prompt)
        self.assertIn("geometry specialist", prompt)
        self.assertIn("May submit final answer: no", prompt)
        self.assertEqual(env.get_available_tools(), ["query_rules"])

    def test_arml_local_mock_round_table_runs_with_gold_scoring_path(self):
        env = OlympiadEnvironment("arml_local", ARML_PROBLEM)
        result = run_round_table(
            env,
            mock_agent_llm,
            CollabConfig(rounds=1, synthesize=True),
        )

        self.assertTrue(result["submitted"])
        self.assertEqual(result["rule"]["scoring"]["mode"], "gold")
        self.assertEqual(len(result["roster"]), 6)
        self.assertEqual(result["submitted_by"], "Agent_1")

    def test_explicit_turn_budget_overrides_rule_card_safety_budget(self):
        env = OlympiadEnvironment(
            "science_bowl",
            SCIENCE_BOWL_PROBLEM,
            max_turns=7,
        )

        self.assertEqual(env.max_turns, 7)

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
