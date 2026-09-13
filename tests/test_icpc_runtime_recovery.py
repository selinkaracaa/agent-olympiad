"""Small reproductions of broken handoffs observed in the full v8 ICPC run."""
import json
import unittest
from dataclasses import replace

from contest_memory import ContestMemory
from contest_policy import _card_focus_task
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from strategy import StrategicPolicy
from contest_runner import ContestRunConfig, run_contest
from llm import LLMResponse, LLMToolCall
from test_otc_rulecard import ICPC, ScriptedLLM, action, icpc_manifest, task, arml_manifest


class PromptContractRecoveryTests(unittest.TestCase):
    def prompt(self, config):
        requests = []
        def model(request):
            requests.append(request)
            return LLMResponse("", "mock", "mock", tool_calls=(LLMToolCall("rest", {}),))
        run_contest(icpc_manifest(), ScriptedLLM({}), config, action_request_fn=model)
        return requests[0].system_prompt

    def test_disabled_memory_actions_have_no_usage_instructions(self):
        prompt = self.prompt(ContestRunConfig("decentralized", 2, 1))
        self.assertIn("inspect_problem reads", prompt)
        for instruction in ("remember stores", "recall searches", "share_note publishes"):
            self.assertNotIn(instruction, prompt)

    def test_reviewed_programming_has_one_consistent_work_contract(self):
        prompt = self.prompt(ContestRunConfig("otc", 3, 1, rule_card=ICPC))
        self.assertIn("Use work for programming analysis notes; execute_code records source.", prompt)
        self.assertNotIn("work is only for a candidate answer, never for notes", prompt)
        self.assertIn("remember stores", prompt)


class ProgrammingFocusRecoveryTests(unittest.TestCase):
    def table(self):
        session = ContestSession(
            [TaskUnit("repair", kind="programming"), TaskUnit("untouched", kind="programming")],
            ContestBudgetState(max_turns=60),
        )
        session.select_task("repair")
        session.create_answer("print(0)", author="Agent_1")
        memory = ContestMemory(run_id="r", session_id="s", competition_id="icpc")
        memory.append(task_id="repair", question_id=None, actor="Agent_1",
                      visibility="private", recipients=("Agent_1",), kind="execute_code",
                      payload={"code": "print(0)"}, turn=1)
        return session, memory

    def test_failed_source_keeps_worker_on_repair_before_unstarted_task(self):
        session, memory = self.table()
        selected = _card_focus_task(session, memory, "Agent_1", None, StrategicPolicy())
        self.assertEqual(selected.task_id, "repair")

    def test_inspecting_a_teammate_does_not_abandon_own_repair(self):
        session, memory = self.table()
        memory.append(task_id="untouched", question_id=None, actor="Agent_1",
                      visibility="private", recipients=("Agent_1",), kind="inspect_problem",
                      payload={"problem_id": "untouched"}, turn=2)
        restored = ContestMemory.from_checkpoint_json(memory.to_checkpoint_json())
        selected = _card_focus_task(session, restored, "Agent_1", None, StrategicPolicy())
        self.assertEqual(selected.task_id, "repair")

    def test_yield_and_skip_release_focus_but_explicit_revisit_still_works(self):
        for kind in ("programming_repair_yield", "skip_problem"):
            with self.subTest(kind=kind):
                session, memory = self.table()
                memory.append(task_id="repair", question_id=None,
                              actor="Contest_Scheduler" if kind.endswith("yield") else "Agent_1",
                              visibility="private", recipients=("Agent_1",), kind=kind,
                              payload={"agent": "Agent_1"}, turn=3)
                selected = _card_focus_task(session, memory, "Agent_1", None, StrategicPolicy())
                self.assertEqual(selected.task_id, "untouched")
                memory.append(task_id="repair", question_id=None, actor="Agent_1",
                              visibility="private", recipients=("Agent_1",), kind="select_problem",
                              payload={"problem_id": "repair"}, turn=4)
                self.assertEqual(_card_focus_task(session, memory, "Agent_1", None,
                                                 StrategicPolicy()).task_id, "repair")

    def test_native_repair_review_and_submission_reach_judge_before_deadline(self):
        scripts = ScriptedLLM({
            "Agent_1": [action("execute_code", code="print(42)"),
                        action("speak", content="p1 passes samples; please review the recorded source."),
                        action("submit_code")],
            "Agent_2": [action("rest", reason="Reading."),
                        action("review_answer", problem_id="p1", decision="approve",
                               content="Checked the full revised source and sample evidence.")],
        })
        calls = []
        def executor(task, name, arguments):
            calls.append((task.task_id, name, dict(arguments)))
            if name == "execute_code":
                return {"valid": True, "sample_verdict": "AC" if arguments["code"] == "print(42)" else "WA"}
            self.assertEqual(name, "submit_code")
            return {"valid": True, "verdict": "AC"}
        def native(request):
            value = json.loads(scripts(request.system_prompt, request.user_prompt))
            return LLMResponse("", "mock", "mock", tool_calls=(
                LLMToolCall(value["action"], value["arguments"]),))
        manifest = icpc_manifest()
        manifest = replace(manifest, tasks=(*manifest.tasks, task("p3", programming=True),
                                            task("p4", programming=True)))
        session = ContestSession([TaskUnit(t.task_id, kind="programming") for t in manifest.tasks],
                                 ContestBudgetState(max_turns=7, turns_used=3))
        memory = ContestMemory(run_id=f"{manifest.session_id}:otc",
                               session_id=manifest.session_id, competition_id="icpc")
        memory.append(task_id=None, question_id=None, actor="Coach", visibility="public",
                      kind="precontest_coach_guidance",
                      payload={"guidance": "Test, review, and submit.", "plan": None}, turn=0)
        # Restore a genuine repair stage: three seats have failed candidates,
        # and an untouched fourth task must not replace the author's context.
        for seat in (1, 2, 3):
            session.select_task(f"p{seat}")
            session.create_answer("print(0)", author=f"Agent_{seat}")
            memory.append(task_id=f"p{seat}", question_id=None, actor=f"Agent_{seat}",
                          visibility="private", recipients=(f"Agent_{seat}",), kind="execute_code",
                          payload={"code": "print(0)"}, turn=0)
        session.select_task("p1")
        result = run_contest(manifest, scripts,
                             ContestRunConfig("otc", 3, 7, rule_card=ICPC),
                             action_request_fn=native, task_action_executor=executor,
                             session_checkpoint=session.checkpoint(),
                             memory_checkpoint=memory.to_checkpoint_json())
        events = result["memory"]["events"]
        errors = [e["payload"] for e in events if e["kind"] == "action_error"]
        self.assertFalse(errors, errors)
        self.assertEqual(calls[0], ("p1", "execute_code", {"code": "print(42)"}))
        self.assertEqual([c for c in calls if c[1] == "submit_code"],
                         [("p1", "submit_code", {"code": "print(42)"})])
        self.assertEqual(result["tasks"]["p1"]["terminal_verdict"], "AC")
        self.assertFalse(any(e["kind"] == "programming_deadline_submit_result" for e in events))


class SingleActionTransportRecoveryTests(unittest.TestCase):
    def test_multiple_native_calls_are_corrected_before_any_action_executes(self):
        requests = []
        def model(request):
            requests.append(request)
            if len(requests) == 1:
                return LLMResponse("", "mock", "mock", usage={"output_tokens": 5}, tool_calls=(
                    LLMToolCall("work", {"content": "discard-one", "problem_id": "q1"}, "bad-1"),
                    LLMToolCall("work", {"content": "discard-two", "problem_id": "q1"}, "bad-2")))
            return LLMResponse("", "mock", "mock", usage={"output_tokens": 7}, tool_calls=(
                LLMToolCall("work", {"content": "chosen", "problem_id": "q1"}, "corrected"),))
        result = run_contest(arml_manifest(), lambda *_: "",
                             ContestRunConfig("decentralized", 1, 1, max_api_calls=2),
                             action_request_fn=model)
        works = [e["payload"]["content"] for e in result["memory"]["events"] if e["kind"] == "work"]
        self.assertEqual(works, ["chosen"])
        self.assertEqual(result["budget"]["api_calls_used"], 2)
        self.assertEqual(result["budget"]["tokens_used"], 12)
        self.assertIn("No action from that response executed", requests[1].user_prompt)
        self.assertEqual([c["executed"] for c in result["action_transport_log"]], [False, False, True])

    def test_multiple_calls_cannot_spend_past_budget_or_partially_execute(self):
        requests = []
        def model(request):
            requests.append(request)
            return LLMResponse("", "mock", "mock", usage={"output_tokens": 5}, tool_calls=(
                LLMToolCall("work", {"content": "not-selected", "problem_id": "q1"}),
                LLMToolCall("work", {"content": "also-not-selected", "problem_id": "q1"})))
        result = run_contest(arml_manifest(), lambda *_: "",
                             ContestRunConfig("decentralized", 1, 1, max_api_calls=1),
                             action_request_fn=model)
        self.assertEqual(len(requests), 1)
        self.assertEqual(result["budget"]["api_calls_used"], 1)
        self.assertFalse(any(e["kind"] == "work" for e in result["memory"]["events"]))
        self.assertTrue(all(not c["executed"] for c in result["action_transport_log"]))

    def test_rejected_native_invocation_is_not_logged_as_executed(self):
        def model(_request):
            return LLMResponse("", "mock", "mock", tool_calls=(
                LLMToolCall("submit_code", {"code": "not permitted in this math contest"}),))
        result = run_contest(arml_manifest(), lambda *_: "",
                             ContestRunConfig("decentralized", 1, 1, max_api_calls=1),
                             action_request_fn=model)
        self.assertTrue(any(e["kind"] == "action_error" for e in result["memory"]["events"]))
        self.assertFalse(result["action_transport_log"][0]["executed"])


if __name__ == "__main__":
    unittest.main()
