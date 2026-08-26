from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from analyze_runs import compute_decompositions, group_summaries
from collaboration import _agent_user_prompt, _system_prompt
from env import OlympiadEnvironment
from rules import (
    COMPONENT_FILES,
    RuleCardResolutionError,
    RulesMode,
    agent_view,
    iter_rule_card_ids,
    load_rule_card,
)
from run_competition_batch import run_one

RULES_ROOT = REPO_ROOT / "data" / "rules"
IEO_PROBLEM = "ieo_business_case_2021"
ICPC_PROBLEM = "icpc_wf_2012_bottles"
MISSING_CURRENT = {"hmmt_team", "icm", "itym", "iypt", "mcm"}


class RuleBundleTests(unittest.TestCase):
    def test_exactly_37_canonical_three_file_bundles_load(self):
        ids = iter_rule_card_ids(RULES_ROOT)
        self.assertEqual(len(ids), 37)
        for competition_id in ids:
            with self.subTest(competition_id=competition_id):
                directory = RULES_ROOT / competition_id
                self.assertEqual(
                    {path.name for path in directory.iterdir()},
                    set(COMPONENT_FILES.values()),
                )
                self.assertEqual(
                    load_rule_card(competition_id, required=True).competition_id,
                    competition_id,
                )

    def test_agent_views_hide_evaluation_fields(self):
        forbidden = {
            "evaluation_guidance",
            "scoring",
            "submission",
            "rubric_path",
            "evaluator_id",
            "gold_label",
        }

        def keys(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield key
                    yield from keys(child)
            elif isinstance(value, list):
                for child in value:
                    yield from keys(child)

        for competition_id in iter_rule_card_ids(RULES_ROOT):
            card = load_rule_card(competition_id, required=True)
            self.assertTrue(forbidden.isdisjoint(set(keys(agent_view(card)))))


class RulesModeTests(unittest.TestCase):
    def test_off_is_default_and_preserves_legacy_prompt_and_tools(self):
        env = OlympiadEnvironment("icpc", ICPC_PROBLEM)
        self.assertIs(env.rules_mode, RulesMode.OFF)
        self.assertIsNone(env.rule_card)
        self.assertEqual(env.get_available_tools(), ["execute_code"])
        self.assertNotIn("CONTESTANT-VISIBLE COMPETITION RULES", _system_prompt(env, "Agent_1"))

    def test_prompt_only_injects_rules_without_enforcing_card_constraints(self):
        env = OlympiadEnvironment(
            "ieo_business_case", IEO_PROBLEM, rules_mode="prompt_only"
        )
        role = env.rule_card.roster(env.team_size)[1]
        prompt = _system_prompt(env, role.name)
        self.assertIn("CONTESTANT-VISIBLE COMPETITION RULES", prompt)
        self.assertIn("YOUR ROLE DUTIES", prompt)
        self.assertNotIn("evaluation_guidance", prompt)
        self.assertNotIn(
            "RULE VIOLATION",
            env.execute_action(role.name, "read_star_chart", "missing"),
        )
        self.assertIn(
            "Unrecognized action",
            env.execute_action(role.name, "write_private_notes", "private"),
        )
        non_submitter = next(item for item in env.rule_card.agent_roles if not item.may_submit)
        self.assertIn(
            "finalized",
            env.execute_action(
                non_submitter.name, "submit_final", "a sufficiently long final answer"
            ),
        )

    def test_enforced_constraints_private_notes_and_deliberation(self):
        env = OlympiadEnvironment(
            "ieo_business_case", IEO_PROBLEM, rules_mode="enforced"
        )
        roles = env.rule_card.roster(env.team_size)
        submitter = next(role for role in roles if role.may_submit)
        worker = next(role for role in roles if not role.may_submit)
        other = next(role for role in roles if role.name != worker.name)

        self.assertIn(
            "not authorized",
            env.execute_action(
                worker.name, "submit_final", "a sufficiently long final answer"
            ),
        )
        self.assertIn(
            "banned",
            env.execute_action(worker.name, "read_star_chart", "missing"),
        )
        secret = "private sensitivity result"
        env.execute_action(worker.name, "write_private_notes", secret)
        self.assertIn(secret, _agent_user_prompt(env, worker.name, "test"))
        self.assertNotIn(secret, _agent_user_prompt(env, other.name, "test"))

        proposed = env.execute_action(worker.name, "propose", "Use the mid market.")
        challenged = env.execute_action(other.name, "challenge", "P1 | Demand is uncertain.")
        evidence = env.execute_action(
            other.name, "provide_evidence", "P1 | Survey data supports demand."
        )
        revised = env.execute_action(
            worker.name, "revise", "P1 | Test mid-market demand before launch."
        )
        decided = env.execute_action(
            submitter.name, "decide", "P1 | accept | Evidence supports the revision."
        )
        self.assertIn("P1 proposed", proposed)
        self.assertIn("challenge on P1", challenged)
        self.assertIn("provide_evidence on P1", evidence)
        self.assertIn("revise on P1", revised)
        self.assertIn("accept", decided)

        limited = env.communication.policy
        for index in range(int(limited["per_agent_message_budget"])):
            env.execute_action(other.name, "speak", f"message {index}")
        rejection = env.execute_action(other.name, "speak", "over budget")
        self.assertIn("COMMUNICATION LIMIT", rejection)
        self.assertTrue(env.communication.rejected)
        self.assertTrue(env.rule_violations)

    def test_missing_current_cards_are_explicitly_unavailable(self):
        for competition_id in MISSING_CURRENT:
            baseline = OlympiadEnvironment(
                competition_id,
                {
                    "hmmt_team": "hmmt_team_2024",
                    "icm": "icm_2024_D",
                    "itym": "itym_2024",
                    "iypt": "iypt_2024",
                    "mcm": "mcm_2024_A",
                }[competition_id],
                rules_mode="prompt_only",
            ).rules_baseline
            self.assertFalse(baseline.available)
            self.assertEqual(baseline.metadata()["rules_coverage"], "missing_card")

        with self.assertRaises(RuleCardResolutionError):
            OlympiadEnvironment(
                "mcm", "mcm_2024_A", rules_mode="enforced", rules_strict=True
            )

    def test_runner_records_hash_coverage_and_analysis_separates_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            row = run_one(
                "icpc",
                ICPC_PROBLEM,
                schema="round_table",
                query_fn=lambda _system, _user: "ACTION: sleep | PAYLOAD: test",
                request_fn=None,
                rounds=1,
                synthesize=False,
                judge_task=False,
                judge_collab=False,
                out_dir=Path(directory),
                rules_mode="prompt_only",
            )
            transcript = json.loads(Path(row["transcript_path"]).read_text(encoding="utf-8"))
        self.assertEqual(row["rules_mode"], "prompt_only")
        self.assertEqual(len(row["rule_card_content_hash"]), 64)
        self.assertEqual(transcript["metadata"]["rules_coverage"], "covered")

        rows = [
            {
                "competition": "icpc",
                "problem_id": "p",
                "schema": "round_table",
                "team": "gpt",
                "rules_mode": mode,
                "grade_score": 1,
                "grade_max_score": 1,
            }
            for mode in ("off", "prompt_only")
        ]
        self.assertEqual(len(group_summaries(rows)), 2)
        self.assertEqual(len(compute_decompositions(rows)), 2)


if __name__ == "__main__":
    unittest.main()
