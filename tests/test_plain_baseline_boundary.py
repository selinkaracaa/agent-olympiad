"""The three ordinary baselines must not inherit optional OTC workflows."""
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src"),
               str(Path(__file__).resolve().parent)]

from contest_actions import _apply_action
from contest_config import ContestRunConfig
from contest_memory import ContestMemory
from contest_policy import _resolved_actions, _trim_to_baseline, _leader_plan_prompts
from contest_prompts import _system_prompt, _user_prompt
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from strategy import StrategicPolicy
from tool_registry import ACTION_REGISTRY, DELIBERATION_ACTION_NAMES
from test_otc_rulecard import arml_manifest
from llm import LLMResponse, LLMToolCall
from contest_runner import run_contest


PLAIN = ("single_agent", "decentralized", "centralized")


class PlainBaselineBoundaryTests(unittest.TestCase):
    def config(self, name):
        return ContestRunConfig(name, 1 if name == "single_agent" else 3, 3)

    def state(self):
        manifest = arml_manifest()
        session = ContestSession([TaskUnit(t.task_id) for t in manifest.tasks],
                                 ContestBudgetState(max_turns=3))
        session.select_task(manifest.tasks[0].task_id)
        session.create_answer("Visible common draft: 42", author="Agent_2")
        memory = ContestMemory(run_id="boundary", session_id=manifest.session_id,
                               competition_id=manifest.competition_id)
        return manifest, session, memory

    def test_plain_prompts_keep_drafts_without_an_eligible_review_queue(self):
        for baseline in PLAIN:
            with self.subTest(baseline=baseline):
                manifest, session, memory = self.state()
                prompt = _user_prompt(manifest, session, memory, self.config(baseline), "Agent_1")
                self.assertIn("Visible common draft: 42", prompt)
                self.assertIn("SHARED ANSWER HISTORY", prompt)
                self.assertNotIn("ELIGIBLE PENDING REVIEWS", prompt)
                self.assertNotIn("SHARED ANSWER REVIEW HISTORY", prompt)

    def test_disabled_review_projection_is_not_even_constructed(self):
        for baseline in PLAIN:
            with self.subTest(baseline=baseline), patch(
                "contest_prompts._pending_review_queue",
                side_effect=AssertionError("OTC review queue entered a plain prompt"),
            ):
                manifest, session, memory = self.state()
                _user_prompt(manifest, session, memory, self.config(baseline), "Agent_1")

    def test_unexpected_bundle_cannot_offer_otc_deliberation(self):
        for baseline in PLAIN:
            with self.subTest(baseline=baseline):
                available = _trim_to_baseline(set(ACTION_REGISTRY.values()), self.config(baseline))
                names = {spec.name for spec in available}
                self.assertFalse(names & (DELIBERATION_ACTION_NAMES | {
                    "remember", "recall", "share_note", "request_review", "review_answer"}))

    def test_centralized_planner_assigns_work_without_a_review_workflow(self):
        system, user = _leader_plan_prompts(arml_manifest(), self.config("centralized"))
        self.assertIn("work_assignments", system)
        self.assertNotIn("review_assignments", system)
        self.assertNotIn("at least one reviewer", user)
        self.assertNotIn("private memory", user)

    def test_plain_task_guidance_does_not_invent_reviewers(self):
        manifest = arml_manifest()
        for baseline in PLAIN:
            for family in ("mathematics", "short_answer", "programming", "puzzle"):
                with self.subTest(baseline=baseline, family=family):
                    config = self.config(baseline)
                    text = _system_prompt(config, "Agent_1", _resolved_actions(manifest, config),
                                          native_actions=True, task_family=family)
                    self.assertNotIn("Reviewers check", text)

    def test_direct_dispatch_rejects_disabled_workflows_without_side_effects(self):
        actions = {
            "request_review": {"content": "Review this", "reviewer": "Agent_2"},
            "review_answer": {"problem_id": arml_manifest().tasks[0].task_id,
                "decision": "approve", "content": "Looks correct"},
            **{name: {"content": "Do not execute", "proposal_id": "P1",
                       "outcome": "accept", "reason": "test"}
               for name in DELIBERATION_ACTION_NAMES},
        }
        for baseline in PLAIN:
            for name, args in actions.items():
                with self.subTest(baseline=baseline, action=name):
                    manifest, session, memory = self.state()
                    before = (session.checkpoint(), memory.to_checkpoint_json())
                    executor = Mock(side_effect=AssertionError("Unexpected external tool"))
                    with self.assertRaisesRegex(ValueError, "disabled|unavailable"):
                        _apply_action(action=name, arguments=args, agent="Agent_1",
                            manifest=manifest, session=session, memory=memory,
                            config=self.config(baseline), strategic_policy=StrategicPolicy(),
                            task_action_executor=executor)
                    self.assertEqual((session.checkpoint(), memory.to_checkpoint_json()), before)
                    executor.assert_not_called()

    def test_real_engine_plain_seats_never_enter_otc_or_memory_calls(self):
        for baseline in PLAIN:
            with self.subTest(baseline=baseline):
                requests = []
                plans = []
                config = replace(self.config(baseline), max_turns=1, deadline_submit=False)

                def query(system, user):
                    self.assertEqual(baseline, "centralized")
                    self.assertTrue(user.startswith("OPENING LEADER PLAN"))
                    self.assertNotIn("review_assignments", system)
                    plans.append((system, user))
                    return json.dumps({"work_assignments": {
                        f"Agent_{i}": ["q1", "q2"] for i in range(1, 4)}})

                def request(req):
                    requests.append(req)
                    names = {tool["name"] for tool in req.tools}
                    self.assertTrue(all(ACTION_REGISTRY[name].module == "common" for name in names))
                    self.assertFalse(names & (DELIBERATION_ACTION_NAMES | {
                        "remember", "recall", "share_note", "review_answer", "request_review"}))
                    self.assertNotIn("ELIGIBLE PENDING REVIEWS", req.user_prompt)
                    self.assertNotIn("PRE-CONTEST COACH BRIEF", req.system_prompt)
                    self.assertNotIn("MEMORY WRITE:", req.system_prompt)
                    return LLMResponse("", "mock", "plain", tool_calls=(LLMToolCall("rest", {}),),
                                       usage={"api_calls": 1, "output_tokens": 1})

                with patch("otc_runtime.think_system_prompt", side_effect=AssertionError("OTC think")):
                    result = run_contest(arml_manifest(), query, config, action_request_fn=request,
                        coach_query_fn=Mock(side_effect=AssertionError("External Coach")))
                self.assertEqual(len(plans), int(baseline == "centralized"))
                self.assertEqual(len(requests), config.team_size)
                self.assertFalse(any(e["actor"] == "Coach" or e["kind"] in {
                    "think", "note", "note_shared", "recall_result", "review_answer"}
                    for e in result["memory"]["events"]))


if __name__ == "__main__":
    unittest.main()
