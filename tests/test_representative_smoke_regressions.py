"""Regressions for representative five-baseline smoke and artifact schemas."""
import json
import tempfile
import unittest
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import Mock, patch

from artifact_contract import contract_for
from contest_config import BASELINE_NAMES, ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask, load_contest_manifest
from contest_memory import ContestMemory
from contest_policy import _resolved_actions, _actions_for_agent
from contest_runner import run_contest
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from llm import LLMRequest
from rules.loader import load_rule_card
from run_all_contest_smoke import CatalogSmokeAgent, mock_task_executor, run_case
from tool_registry import render_function_tools
from test_contest_work_guards import fixture


class RepresentativeSmokeTests(unittest.TestCase):
    def test_artifact_functions_have_unique_names_in_every_baseline(self):
        for competition in ("mcm", "ieo_business_case"):
            card = load_rule_card(competition)
            manifest = ContestManifest("schema-test", competition, (
                ManifestTask("deliverable", "deliverable", None, "Public task.", "artifact", 1, False, {}),
            ), metadata={"artifact_contract": asdict(contract_for(card))})
            for variant in BASELINE_NAMES:
                with self.subTest(competition=competition, variant=variant):
                    config = ContestRunConfig(variant, 1 if variant == "single_agent" else card.team_size_default,
                                              12, rule_card=card)
                    session = ContestSession([TaskUnit("deliverable", kind="non_programming")],
                                             ContestBudgetState(max_turns=12))
                    session.select_task("deliverable")
                    memory = ContestMemory(run_id="r", session_id=manifest.session_id, competition_id=competition)
                    actions = _actions_for_agent(_resolved_actions(manifest, config), session, config,
                                                 "Agent_1", answer_sheet_contest=True, memory=memory)
                    names = [tool["name"] for tool in render_function_tools(actions)]
                    self.assertEqual(len(names), len(set(names)), Counter(names))
                    self.assertEqual(names.count("render_pdf"), 1)
                    self.assertEqual(next(s for s in actions if s.name == "render_pdf").visibility, "team")

    def test_multitask_programming_finishes_in_all_five_baselines(self):
        manifest, _, _ = fixture(programming=True)
        card = load_rule_card("icpc")
        for variant in BASELINE_NAMES:
            with self.subTest(variant=variant):
                case = run_case(manifest, card, variant, 24)
                self.assertEqual(case["status"], "PASS", case["checks"])
                self.assertFalse(case["action_errors"])
                self.assertEqual(set(case["result"]["submissions"]), {"q1", "q2"})
                self.assertTrue(all(case["result"]["submissions"].values()))
                self.assertTrue(all(case["result"]["diagnostics"]["attempts_to_ac"].values()))

    def test_puzzle_smoke_advances_beyond_first_submission(self):
        base, _, _ = fixture()
        manifest = replace(base, competition_id="mystery_hunt",
                           tasks=tuple(replace(t, task_type="puzzle") for t in base.tasks))
        for variant in ("single_agent", "decentralized"):
            with self.subTest(variant=variant):
                case = run_case(manifest, load_rule_card("mystery_hunt"), variant, 24)
                self.assertTrue(all(case["result"]["submissions"].values()))
                self.assertEqual(case["status"], "PASS", case["checks"])

    def test_arml_smoke_performs_required_challenge_without_exhausting_messages(self):
        base, _, _ = fixture()
        manifest = replace(base, tasks=base.tasks + (
            replace(base.tasks[0], task_id="q3", parent_problem_id="q3"),
            replace(base.tasks[0], task_id="q4", parent_problem_id="q4"),
        ))
        case = run_case(manifest, load_rule_card("arml_local"), "otc", 32)
        self.assertEqual(case["status"], "PASS", case["checks"])
        self.assertFalse(case["action_errors"])
        self.assertGreaterEqual(case["called_actions"].get("challenge", 0), 1)
        self.assertEqual(case["called_actions"].get("submit"), 1)
        self.assertLess(case["called_actions"].get("speak", 0), 60)

    def test_centralized_leader_never_calls_external_coach(self):
        manifest, _, _ = fixture(programming=True)
        config = ContestRunConfig("centralized", 3, 24, max_tokens=200000, minutes_per_turn=0)
        planner = Mock(return_value=json.dumps({
            "summary": "The contestant Leader allocates tasks.",
            "work_assignments": {"Agent_1": ["q1", "q2"], "Agent_2": ["q1"], "Agent_3": ["q2"]},
            "review_assignments": {}, "task_order": ["q1", "q2"],
        }))
        external_coach = Mock(side_effect=AssertionError("Centralized must not call the external Coach"))
        agent = CatalogSmokeAgent(manifest, config)
        result = run_contest(manifest, planner, config, action_request_fn=agent,
                             action_transport="native", coach_query_fn=external_coach,
                             task_action_executor=mock_task_executor)
        external_coach.assert_not_called()
        self.assertTrue(planner.called)
        self.assertEqual(result["plan_author"], "Agent_1")
        self.assertFalse(result["modules"]["coach"])
        self.assertFalse(result["modules"]["memory"])
        self.assertFalse(any(e["actor"] == "Coach" for e in result["memory"]["events"]))
        self.assertTrue(all(result["submissions"].values()))
        from run_representative_contest_smoke import common_details
        self.assertTrue(common_details(result, manifest, "centralized")["checks"]["coach_once"])

    def test_smoke_rejects_duplicate_function_schemas(self):
        manifest, _, _ = fixture(two=False)
        config = ContestRunConfig("single_agent", 1, 12)
        agent = CatalogSmokeAgent(manifest, config)
        tool = {"name": "rest", "parameters": {"type": "object",
                "properties": {"reason": {"type": "string"}}, "required": ["reason"]}}
        request = LLMRequest(system_prompt="You are Agent_1", user_prompt="", tools=(tool, tool))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            agent(request)

    def test_hmmt_selection_uses_structured_record_and_records_scope_change(self):
        import run_representative_contest_smoke as smoke
        with tempfile.TemporaryDirectory() as temp, patch.object(smoke, "OUT", Path(temp)):
            manifest = smoke.representative_manifest("hmmt_guts", count=3)
        self.assertEqual(len(manifest.tasks), 3)
        self.assertTrue(all(t.question_id for t in manifest.tasks))
        selection = manifest.metadata["smoke_selection"]
        self.assertEqual(selection["previous_record"], "hmmt_guts_2000")
        self.assertEqual(selection["selected_record"], "hmmt_guts_2024")
        self.assertTrue(selection["split_parts"])


if __name__ == "__main__":
    unittest.main()
