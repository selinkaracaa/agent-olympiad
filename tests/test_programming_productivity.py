"""Programming-only source visibility, fair repair, and artifact progress."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_runner import ContestRunConfig, _apply_action, _user_prompt, _scheduled_agent_task, _actions_for_agent, _resolved_actions, run_contest
from contest_session import ContestSession, ContestBudgetState, TaskUnit
from llm import LLMResponse, LLMToolCall
from strategy import StrategicPolicy
from programming_workflow import ProgrammingProgress


def manifest(ids=("a", "b")):
    return ContestManifest("p", "icpc", tuple(ManifestTask(t, t, None, "Solve " + t,
                           "algorithmic_programming", 1, True, {}) for t in ids))


from contest_feature_fixtures import review_ablation_config, run_with_test_plan

class ProgrammingProductivityTests(unittest.TestCase):
    def test_empty_source_is_not_a_progress_artifact(self):
        m = manifest()
        s = ContestSession([TaskUnit("a"), TaskUnit("b")], ContestBudgetState(max_turns=10))
        s.select_task("a")
        memory = ContestMemory(run_id="r", session_id="p", competition_id="icpc")
        called = []
        with self.assertRaisesRegex(ValueError, "nonempty candidate source"):
            _apply_action(action="execute_code", arguments={"code": "  \n"}, agent="Agent_1",
                          manifest=m, session=s, memory=memory, config=review_ablation_config(2, 10),
                          strategic_policy=StrategicPolicy(), task_action_executor=lambda *args: called.append(args))
        self.assertEqual(called, [])
        self.assertEqual(s.active_task.versions, [])

    def test_owner_source_and_sample_details_survive_memory_eviction(self):
        m = manifest()
        s = ContestSession([TaskUnit("a"), TaskUnit("b")], ContestBudgetState(max_turns=50))
        s.select_task("a")
        memory = ContestMemory(run_id="p:open_table_coach", session_id="p", competition_id="icpc")
        config = review_ablation_config(2, 50)
        source = "import sys\n" + "# preserve this code\n" * 500 + "print('UNIQUE_SOURCE_END')\n"
        _apply_action(action="execute_code", arguments={"code": source}, agent="Agent_1",
                      manifest=m, session=s, memory=memory, config=config, strategic_policy=StrategicPolicy(),
                      task_action_executor=lambda *_: {"valid": True, "sample_verdict": "WA",
                          "sample_cases": [{"input": "rare-input", "expected": "42", "actual": "0"}]})
        for i in range(9):
            memory.append(task_id="a", question_id=None, actor="Agent_1", visibility="public",
                          kind="work", payload={"content": "Thinking"}, turn=i+2)
        prompt = _user_prompt(m, s, memory, config, "Agent_1")
        self.assertTrue(source in prompt or json.dumps(source)[1:-1] in prompt)
        self.assertIn("rare-input", prompt)
        self.assertIn(s.active_task.versions[-1].version_hash, prompt)

    def test_repair_order_is_honored_with_uncoded_alternatives(self):
        for remote_wa in (False, True):
            with self.subTest(remote_wa=remote_wa):
                s = ContestSession([TaskUnit("a"), TaskUnit("b")], ContestBudgetState(max_turns=10))
                s.select_task("a")
                s.create_answer("print(0)", author="Agent_1", evidence_refs=("sample",) if remote_wa else ())
                if remote_wa:
                    s.submit("WA")
                picked = _scheduled_agent_task(s, agent="Agent_1", work_task_ids=["a", "b"],
                    review_task_ids=set(), reported_version_hashes={s.active_task.versions[-1].version_hash})
                self.assertEqual(picked.task_id, "a")
                picked = _scheduled_agent_task(s, agent="Agent_1", work_task_ids=["b", "a"],
                    review_task_ids=set(), reported_version_hashes={s.active_task.versions[-1].version_hash})
                self.assertEqual(picked.task_id, "b")

    def test_native_model_cannot_rest_forever_and_both_tasks_get_repaired(self):
        m = manifest(("a", "b", "c", "d"))
        plan = json.dumps(dict(summary="assign", work_assignments={"Agent_1": ["a", "b"], "Agent_2": ["c", "d"]},
                               review_assignments={}, task_order=["a", "b", "c", "d"], switch_conditions=[], final_check=[]))
        exposed = []
        def model(request):
            names = {t["name"] for t in request.tools}
            exposed.append(names)
            if "rest" in names:
                call = LLMToolCall("rest", {"reason": "Need source first"})
            else:
                self.assertEqual(names, {"execute_code"})
                self.assertIn("SOURCE ACTION REQUIRED", request.user_prompt)
                call = LLMToolCall("execute_code", {"code": "print(0)"})
            return LLMResponse("", "mock", "mock", tool_calls=(call,))
        result = run_with_test_plan(m, lambda *_: "", review_ablation_config(2, 18),
            coach_query_fn=lambda *_: plan, action_request_fn=model,
            task_action_executor=lambda *_: {"valid": True, "sample_verdict": "WA"})
        executed = Counter(e["task_id"] for e in result["memory"]["events"] if e["kind"] == "execute_code_result")
        self.assertGreaterEqual(executed["a"], 2)
        self.assertGreaterEqual(executed["b"], 2)
        self.assertFalse(any(e["kind"] == "action_error" for e in result["memory"]["events"]))
        self.assertEqual(result["budget"]["penalty_minutes"], 0)
        self.assertEqual(result["programming_workflow_version"], "programming_workflow_v4")
        self.assertGreater(result["diagnostics"]["programming_source_required_actions"], 0)

    def test_rotation_and_resume_cannot_clear_source_requirement(self):
        memory = ContestMemory(run_id="r", session_id="s", competition_id="icpc")
        progress = ProgrammingProgress(memory, stall_actions=1)
        for turn in (1, 2):
            self.assertTrue(progress.record("Agent_1", "a", turn=turn, progressed=False))
        restored = ProgrammingProgress(ContestMemory.from_checkpoint_json(memory.to_checkpoint_json()), stall_actions=1)
        self.assertTrue(restored.source_required("Agent_1", "a"))
        self.assertFalse(restored.source_required("Agent_2", "a"))
        self.assertFalse(restored.source_required("Agent_1", "b"))
        restored.record("Agent_1", "a", turn=3, progressed=False, source_attempted=True)
        self.assertFalse(restored.source_required("Agent_1", "a"))

    def test_source_gate_preserves_math_short_answer_and_vanilla(self):
        for variant, programming, task_type, review in (
            ("strategic", False, "team_contest", None),
            ("strategic", False, "quiz", None),
            ("vanilla", True, "algorithmic_programming", None),
            ("strategic", True, "algorithmic_programming", False),
        ):
            with self.subTest(variant=variant, task_type=task_type, review=review):
                competition = "icpc" if programming else ("arml_local" if task_type == "team_contest" else "science_bowl")
                m = ContestManifest("s", competition, (
                    ManifestTask("a", "a", None, "Solve", task_type, 1, programming, {}),))
                s = ContestSession([TaskUnit("a", kind="programming" if programming else "non_programming")], ContestBudgetState(max_turns=5))
                s.select_task("a")
                s.create_answer("42", author="Agent_1")
                config = (review_ablation_config(2, 5, require_review=review) if variant == "strategic" else ContestRunConfig(variant, 2, 5, require_review=review))
                actions = _resolved_actions(m)
                before = _actions_for_agent(actions, s, config, "Agent_1")
                after = _actions_for_agent(actions, s, config, "Agent_1", programming_source_required=True)
                self.assertEqual(before, after)
                memory = ContestMemory(run_id="r", session_id="s", competition_id=m.competition_id)
                self.assertNotIn("ACTIVE PROGRAMMING SOURCE", _user_prompt(m, s, memory, config, "Agent_1"))

    def test_sample_ac_reporting_and_reviewed_submit_are_not_source_gated(self):
        m = manifest()
        s = ContestSession([TaskUnit("a"), TaskUnit("b")], ContestBudgetState(max_turns=10))
        s.select_task("a")
        s.create_answer("print(42)", author="Agent_1", evidence_refs=("sample-ac",))
        config = review_ablation_config(2, 10)
        actions = _resolved_actions(m)
        names = {a.name for a in _actions_for_agent(actions, s, config, "Agent_1", programming_source_required=True)}
        self.assertIn("speak", names)
        s.record_review("Agent_2", "Looks correct", decision="approve")
        names = {a.name for a in _actions_for_agent(actions, s, config, "Agent_1", programming_source_required=True)}
        self.assertIn("submit_code", names)

    def test_engine_resume_after_two_notes_still_requires_source(self):
        m = manifest()
        plan = json.dumps(dict(summary="assign", work_assignments={"Agent_1": ["a"], "Agent_2": ["b"]},
                               review_assignments={}, task_order=["a", "b"], switch_conditions=[], final_check=[]))
        saved = {}
        def checkpoint(session, memory):
            if session["budget"]["turns_used"] == 2 and session["budget"]["api_calls_used"] == 5:
                saved.update(session=session, memory=memory)
                raise RuntimeError("pause test")
        config = review_ablation_config(2, 6)
        with self.assertRaisesRegex(RuntimeError, "pause test"):
            run_with_test_plan(m, lambda *_: json.dumps({"action": "rest", "arguments": {"reason": "thinking"}}), config,
                        coach_query_fn=lambda *_: plan, checkpoint_callback=checkpoint)
        seen = []
        def model(request):
            names = {t["name"] for t in request.tools}
            seen.append(names)
            call = (LLMToolCall("execute_code", {"code": "print(0)"}) if names == {"execute_code"}
                    else LLMToolCall("rest", {"reason": "thinking"}))
            return LLMResponse("", "mock", "mock", tool_calls=(call,))
        result = run_with_test_plan(m, lambda *_: "", config, action_request_fn=model,
                            task_action_executor=lambda *_: {"valid": True, "sample_verdict": "WA"},
                            session_checkpoint=saved["session"], memory_checkpoint=saved["memory"])
        self.assertEqual(seen[:2], [{"execute_code"}, {"execute_code"}])
        self.assertFalse(any(e["kind"] == "action_error" for e in result["memory"]["events"]))


if __name__ == "__main__":
    unittest.main()
