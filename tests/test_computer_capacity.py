"""Offline integration coverage for opt-in computer capacity."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from computer_capacity import (
    COMPUTER_USE_EVENT, computer_capacity_state, session_computer_state,
    validate_computer_capacity,
)
from contest_actions import _apply_action
from contest_budget import MIN_RECOMMENDED_TURNS, resolve_contest_budget
from contest_config import ContestRunConfig
from contest_memory import ContestMemory
from contest_prompts import _user_prompt
from contest_run_identity import build_run_identity
from contest_runner import run_contest
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from env import OlympiadEnvironment
from run_competition_batch import _build_parser, _load_resume_rows
from strategy import StrategicPolicy
from submission_policy import SubmissionPolicy
from test_otc_rulecard import ICPC, action, icpc_manifest


class CapacityConfigurationTests(unittest.TestCase):
    def test_positive_integer_or_disabled(self):
        for value in (None, 1, 2):
            validate_computer_capacity(value)
        for value in (0, -1, True, False, 1.5, "2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ContestRunConfig("decentralized", 2, 5, computer_capacity=value)

    def test_cli_exposes_opt_in_capacity(self):
        parser = _build_parser()
        self.assertIsNone(parser.parse_args([]).computer_capacity)
        self.assertEqual(parser.parse_args(["--computer-capacity", "2"]).computer_capacity, 2)
        with patch("sys.stderr"), self.assertRaises(SystemExit):
            parser.parse_args(["--computer-capacity", "0"])

    def test_budget_recommendation_does_not_change_official_short_contests(self):
        self.assertEqual(MIN_RECOMMENDED_TURNS, 10)
        self.assertEqual(resolve_contest_budget("arml_national_team").max_turns, 4)
        self.assertEqual(resolve_contest_budget("icpc", max_turns=1).max_turns, 1)

    def test_capacity_is_part_of_contest_identity(self):
        with tempfile.TemporaryDirectory() as root:
            identities = [
                build_run_identity(
                    icpc_manifest(),
                    ContestRunConfig("decentralized", 2, 5, computer_capacity=capacity),
                    execution={}, evaluation={}, source_root=Path(root),
                )
                for capacity in (None, 1, 2)
            ]
        self.assertEqual(len({entry["fingerprint"] for entry in identities}), 3)
        self.assertEqual(identities[1]["settings"]["config"]["computer_capacity"], 1)

    def test_legacy_resume_checks_capacity_and_accepts_old_disabled_metadata(self):
        metadata = dict(mode="mock", provider="mock", model="mock",
                        schema="centralized", rules_mode="off")
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "batch.json"
            path.write_text(json.dumps({**metadata, "results": []}), encoding="utf-8")
            self.assertEqual(_load_resume_rows(path, metadata)[0], [])
            with self.assertRaisesRegex(ValueError, "computer_capacity"):
                _load_resume_rows(path, {**metadata, "computer_capacity": 1})


class EnvironmentCapacityTests(unittest.TestCase):
    def setUp(self):
        fixture = {
            "problem_id": "capacity_fixture", "problem_description": "Compute a sum.",
            "task_type": "short_answer", "gold_label": {},
        }
        with patch.object(OlympiadEnvironment, "_load_problem", return_value=fixture):
            self.env = OlympiadEnvironment(
                "purple_comet", "capacity_fixture", computer_capacity=1,
            )
        self.env.register_agents(["Agent_1", "Agent_2"])
        self.env.begin_turn()

    def calculate(self, agent="Agent_1", payload=None):
        return self.env.execute_action(
            agent, "use_calculator", {"expression": "1+1"} if payload is None else payload,
        )

    def test_capacity_is_shared_and_renews_next_turn(self):
        self.assertIn("Calculator output", self.calculate())
        with patch.object(self.env, "_run_calculator") as executor:
            self.assertIn("Resource error", self.calculate("Agent_2"))
            executor.assert_not_called()
        self.assertEqual(self.env.get_state()["computers_available_this_turn"], 0)
        self.env.begin_turn()
        self.assertIn("Calculator output", self.calculate("Agent_2"))
        self.assertEqual(self.env.get_metadata()["computer_capacity"], 1)

    def test_invalid_payload_and_banned_tool_do_not_use_a_slot(self):
        self.assertIn("Usage error", self.calculate(payload={}))
        self.assertIn("RULE VIOLATION", self.env.execute_action(
            "Agent_1", "execute_code", {"code": "print(1)"},
        ))
        self.assertEqual(self.env.get_state()["computers_used_this_turn"], 0)
        self.assertIn("Calculator output", self.calculate())

    def test_disabled_preserves_state_shape_and_tool_behavior(self):
        self.env.computer_capacity = None
        for _ in range(3):
            self.assertIn("Calculator output", self.calculate())
        self.assertNotIn("computer_capacity", self.env.get_state())
        self.assertEqual(computer_capacity_state(None), {})


class SessionCapacityTests(unittest.TestCase):
    def setUp(self):
        self.manifest = icpc_manifest()
        self.config = ContestRunConfig("decentralized", 2, 6, computer_capacity=1)
        self.session = ContestSession(
            [TaskUnit(task.task_id, kind="programming") for task in self.manifest.tasks],
            ContestBudgetState(max_turns=6), SubmissionPolicy(),
        )
        self.session.consume_budget(turns=1)
        self.session.select_task("p1")
        self.memory = ContestMemory(
            run_id="capacity", session_id=self.manifest.session_id,
            competition_id=self.manifest.competition_id,
        )
        self.executor = Mock(return_value={
            "valid": True, "verdict": "AC", "sample_verdict": "AC", "result": "ok",
        })

    def perform(self, name="execute_code", agent="Agent_1", **arguments):
        return _apply_action(
            action=name, arguments=arguments or {"code": "print(42)"}, agent=agent,
            manifest=self.manifest, session=self.session, memory=self.memory,
            config=self.config, strategic_policy=StrategicPolicy(),
            task_action_executor=self.executor,
        )

    def state(self):
        return session_computer_state(
            self.memory, self.session.budget.turns_used, self.config.computer_capacity,
        )

    def test_slots_are_shared_across_agents_and_problems(self):
        self.perform()
        self.session.select_task("p2")
        events_before = len(self.memory.archival_snapshot()["events"])
        with self.assertRaisesRegex(ValueError, "Resource error"):
            self.perform(agent="Agent_2")
        self.assertEqual(self.executor.call_count, 1)
        self.assertEqual(len(self.memory.archival_snapshot()["events"]), events_before)
        self.session.consume_budget(turns=1)
        self.perform(agent="Agent_2")
        self.assertEqual(self.executor.call_count, 2)
        self.assertEqual(self.state()["computers_used_this_turn"], 1)

    def test_usage_survives_checkpoint_restore_in_the_same_turn(self):
        self.perform()
        self.session = ContestSession.from_checkpoint(self.session.checkpoint())
        self.memory = ContestMemory.from_checkpoint_json(self.memory.to_checkpoint_json())
        with self.assertRaisesRegex(ValueError, "Resource error"):
            self.perform(agent="Agent_2")
        self.assertEqual(self.executor.call_count, 1)

    def test_failed_execution_consumes_a_slot(self):
        self.executor.return_value = {"valid": False, "result": "execution failed"}
        self.perform()
        self.assertEqual(self.state()["computers_available_this_turn"], 0)

    def test_submit_code_does_not_consume_computation_slots(self):
        self.perform("submit_code")
        self.assertEqual(self.state()["computers_used_this_turn"], 0)
        self.session.select_task("p2")
        self.perform()
        self.assertEqual(self.state()["computers_used_this_turn"], 1)

    def test_reused_failed_execution_does_not_consume_a_slot(self):
        self.config = ContestRunConfig(
            "decentralized", 2, 6, require_review=True, computer_capacity=1,
        )
        with patch("contest_actions.execution_key", return_value="cached"), patch(
            "contest_actions.failed_execution", return_value={"valid": True, "sample_verdict": "WA"},
        ):
            self.perform()
        self.executor.assert_not_called()
        self.assertEqual(self.state()["computers_used_this_turn"], 0)

    def test_existing_workstation_lease_still_blocks_another_agent(self):
        self.config = ContestRunConfig(
            "otc", ICPC.team_size_default, 6, rule_card=ICPC, computer_capacity=2,
        )
        self.perform()
        with self.assertRaisesRegex(ValueError, "workstation is held"):
            self.perform(agent="Agent_2")
        self.assertEqual(self.executor.call_count, 1)
        self.assertEqual(self.state()["computers_available_this_turn"], 1)

    def test_usage_event_contains_no_source_or_tool_output(self):
        self.perform()
        usage = [event for event in self.memory.archival_snapshot()["events"]
                 if event["kind"] == COMPUTER_USE_EVENT]
        self.assertEqual(usage[0]["payload"], {"action": "execute_code", "capacity": 1})
        self.assertEqual(usage[0]["visibility"], "public")
        prompt = _user_prompt(
            self.manifest, self.session, self.memory, self.config, "Agent_2",
        )
        self.assertIn('"computers_available_this_turn": 0', prompt)

    def test_enabled_engine_reports_capacity(self):
        result = run_contest(
            self.manifest, lambda _system, _user: action("rest", reason="idle"),
            self.config, task_action_executor=self.executor,
        )
        self.assertEqual(result["computer_capacity"], 1)
        self.assertEqual(result["computers_used_this_turn"], 0)
        self.executor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
