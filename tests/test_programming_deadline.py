"""Deadline collection must submit actual code, without changing other families."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from contest_adapters import EnvironmentTaskExecutor
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import ContestRunConfig, run_contest, _collect_programming_deadline
from contest_memory import ContestMemory
from contest_session import ContestSession, ContestBudgetState, TaskUnit


def task(name, programming=True):
    return ManifestTask(name, name, None, "Solve " + name,
                        "algorithmic_programming" if programming else "quiz",
                        1, programming, {})


from contest_feature_fixtures import review_ablation_config, run_with_test_plan

class ProgrammingDeadlineTests(unittest.TestCase):
    def seeded(self, tasks):
        manifest = ContestManifest("icpc", "icpc", tuple(tasks))
        session = ContestSession([TaskUnit(t.task_id, kind="programming" if t.programming else "non_programming") for t in tasks], ContestBudgetState(max_turns=1))
        memory = ContestMemory(run_id="icpc:decentralized", session_id="icpc", competition_id="icpc")
        return manifest, session, memory

    def source(self, session, memory, name, code="print(7)"):
        session.select_task(name)
        version = session.create_answer(code, author="Agent_1")
        memory.append(task_id=name, question_id=None, actor="Tool", visibility="public",
                      kind="programming_source_recorded", payload={"version_hash": version.version_hash}, turn=0)
        return version

    def test_last_turn_code_is_submitted_without_sample_ac_or_review(self):
        manifest = ContestManifest("icpc", "icpc", (task("a"), task("blank")))
        session = ContestSession([TaskUnit("a"), TaskUnit("blank")], ContestBudgetState(max_turns=1))
        session.select_task("a")
        submitted = []
        def execute(t, action, args):
            if action == "execute_code":
                return {"valid": True, "sample_verdict": "WA"}
            submitted.append((t.task_id, args["code"]))
            return {"valid": True, "verdict": "WA"}
        result = run_with_test_plan(
            manifest, lambda *_: json.dumps({"action": "execute_code", "arguments": {"code": "print(7)"}}),
            review_ablation_config(1, 1, programming_deadline_submit=True),
            session_checkpoint=session.checkpoint(), task_action_executor=execute)
        self.assertEqual(submitted, [("a", "print(7)")])
        self.assertEqual(result["budget"]["turns_used"], 1)
        self.assertEqual(result["budget"]["api_calls_used"], 1)
        self.assertEqual(result["budget"]["penalty_minutes"], 20)
        self.assertEqual(result["tasks"]["a"]["terminal_verdict"], "WA")
        self.assertEqual(result["programming_deadline"]["no_source_task_ids"], ["blank"])
        self.assertEqual(result["programming_deadline"]["officially_submitted_before"], [])

    def test_default_off_preserves_unsubmitted_code(self):
        manifest, session, memory = self.seeded([task("a")])
        self.source(session, memory, "a")
        session.budget.turns_used = 1
        execute = Mock(side_effect=AssertionError("must not submit"))
        result = run_with_test_plan(manifest, Mock(side_effect=AssertionError("no budget")),
                             review_ablation_config(1, 1), task_action_executor=execute,
                             session_checkpoint=session.checkpoint(), memory_checkpoint=memory.to_checkpoint_json())
        self.assertEqual(len(result["session_checkpoint"]["tasks"][0]["versions"]), 1)
        self.assertEqual(result["diagnostics"]["attempts"], 0)
        execute.assert_not_called()

    def test_latest_executed_source_only_and_no_duplicate_official_submissions(self):
        manifest, session, memory = self.seeded([task("pending"), task("notes"), task("empty"), task("ac"), task("wa"), task("math", False)])
        self.source(session, memory, "pending", "print(1)")
        self.source(session, memory, "pending", "print(2)")
        session.create_answer("Waiting for review", author="Agent_1")
        session.select_task("notes")
        session.create_answer("Thinking about the algorithm")
        self.source(session, memory, "empty", "  ")
        self.source(session, memory, "ac")
        session.submit("AC")
        self.source(session, memory, "wa")
        session.submit("WA")
        session.select_task("math")
        session.create_answer("42")
        execute = Mock(return_value={"valid": True, "verdict": "AC"})
        # A function, not Mock directly: dynamic Mock attributes impersonate methods.
        _collect_programming_deadline(manifest, session, memory, lambda *args: execute(*args), lambda: None)
        execute.assert_called_once_with(manifest.tasks[0], "submit_code", {"code": "print(2)"})
        self.assertTrue(session.task("pending").locked)
        self.assertEqual(len(session.task("ac").submissions), 1)
        self.assertEqual(len(session.task("wa").submissions), 1)
        self.assertEqual(session.task("math").submissions, [])
        self.assertEqual(session.active_task.task_id, "math")

    def test_failure_continues_and_resume_never_retries_uncertain_attempts(self):
        manifest, session, memory = self.seeded([task("a"), task("b")])
        self.source(session, memory, "a")
        self.source(session, memory, "b")
        calls = []
        def execute(t, *_):
            calls.append(t.task_id)
            if t.task_id == "a":
                raise RuntimeError("remote connection lost")
            return {"valid": True, "verdict": "AC"}
        _collect_programming_deadline(manifest, session, memory, execute, lambda: None)
        self.assertEqual(calls, ["a", "b"])
        self.assertFalse(session.task("a").submissions[0].valid)
        self.assertTrue(session.task("b").locked)
        self.assertEqual(session.budget.penalty_minutes, 0)
        _collect_programming_deadline(manifest, session, memory, execute, lambda: None)
        self.assertEqual(calls, ["a", "b"])

    def test_intent_is_checkpointed_before_external_side_effect(self):
        manifest, session, memory = self.seeded([task("a")])
        self.source(session, memory, "a")
        saved = {}
        def persist():
            saved.update(session=session.checkpoint(), memory=memory.to_checkpoint_json())
        def interrupted(*_):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            _collect_programming_deadline(manifest, session, memory, interrupted, persist)
        resumed = ContestSession.from_checkpoint(saved["session"])
        resumed_memory = ContestMemory.from_checkpoint_json(saved["memory"])
        calls = []
        _collect_programming_deadline(manifest, resumed, resumed_memory, lambda *args: calls.append(args), lambda: None)
        self.assertEqual(calls, [])

    def test_sample_or_pending_result_never_becomes_official_ac(self):
        for verdict in ("SAMPLE_AC", "PENDING", "JUDGE_ERROR", "NEEDS_HUMAN"):
            with self.subTest(verdict=verdict):
                manifest, session, memory = self.seeded([task("a")])
                self.source(session, memory, "a")
                _collect_programming_deadline(manifest, session, memory, lambda *_: {"valid": True, "verdict": verdict}, lambda: None)
                self.assertFalse(session.task("a").submissions[-1].valid)
                self.assertFalse(session.task("a").locked)
                self.assertEqual(session.budget.penalty_minutes, 0)

    def test_completed_history_cannot_be_rewritten_by_enabling_deadline(self):
        manifest, session, memory = self.seeded([task("a")])
        self.source(session, memory, "a")
        session.finalize()
        with self.assertRaisesRegex(ValueError, "finalized checkpoint"):
            run_with_test_plan(manifest, Mock(), review_ablation_config(1, 1, programming_deadline_submit=True),
                        session_checkpoint=session.checkpoint(), memory_checkpoint=memory.to_checkpoint_json())

    def test_adapter_deadline_bypasses_only_the_local_sample_gate(self):
        manifest = ContestManifest("icpc", "icpc", (task("a"),))
        executor = EnvironmentTaskExecutor(manifest, benchmark_root="data/benchmarks")
        env = Mock()
        env.execute_action.return_value = json.dumps({"remote": {"status": "done", "verdict": "WA"}})
        executor._environments["a"] = env
        with patch("contest_adapters.run_sample_report", return_value={
            "sample_verdict": "WA", "sample_summary": "failed", "sample_cases": []
        }):
            normal = executor(manifest.tasks[0], "submit_code", {"code": "print(7)", "_deadline_submission": True})
            self.assertFalse(normal["valid"])
            env.execute_action.assert_not_called()
            forced = executor.submit_at_deadline(manifest.tasks[0], "print(7)")
        self.assertTrue(forced["valid"])
        self.assertEqual(forced["verdict"], "WA")
        env.execute_action.assert_called_once_with("Team", "submit_code", {"code": "print(7)"})


if __name__ == "__main__":
    unittest.main()
