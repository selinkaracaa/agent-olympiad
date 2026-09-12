"""ICPC pipeline regressions: reporting, immutable source, and per-worker stalls."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_runner import ContestRunConfig, _apply_action, _scheduled_agent_task, run_contest
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from strategy import StrategicPolicy


def task(name, programming=True, task_type="algorithmic_programming"):
    return ManifestTask(name, name, None, "Solve " + name, task_type, 1, programming, {})


from contest_feature_fixtures import review_ablation_config, run_with_test_plan

class ProgrammingWorkflowRegressions(unittest.TestCase):
    def test_unreported_ac_precedes_unseen_and_failed_assignments(self):
        for other_drafted in (False, True):
            with self.subTest(other_drafted=other_drafted):
                s = ContestSession([TaskUnit("other"), TaskUnit("passed")], ContestBudgetState(max_turns=10))
                if other_drafted:
                    s.select_task("other")
                    s.create_answer("print(0)", author="Agent_1")
                s.select_task("passed")
                s.create_answer("print(42)", author="Agent_1", evidence_refs=("sample-ac",))
                selected = _scheduled_agent_task(s, agent="Agent_1", work_task_ids=["other", "passed"], review_task_ids=set(), reported_version_hashes=set())
                self.assertEqual(selected.task_id, "passed")

    def test_programming_work_preserves_code_and_review_evidence(self):
        m = ContestManifest("icpc", "icpc", (task("a"),))
        s = ContestSession([TaskUnit("a")], ContestBudgetState(max_turns=10))
        s.select_task("a")
        original = s.create_answer("print(42)", author="Agent_1", evidence_refs=("sample-ac",))
        memory = ContestMemory(run_id="r", session_id="icpc", competition_id="icpc")
        _apply_action(action="work", arguments={"content": "Sample AC achieved; waiting for independent review."}, agent="Agent_1", manifest=m, session=s, memory=memory, config=review_ablation_config(3, 10), strategic_policy=StrategicPolicy(), task_action_executor=lambda *_: {})
        self.assertIs(s.active_task.versions[-1], original)
        self.assertTrue(any(e.payload.get("content", "").startswith("Sample AC") for e in memory.view("Agent_1")))

    def test_programming_notes_before_code_do_not_become_candidates(self):
        m = ContestManifest("icpc", "icpc", (task("a"),))
        s = ContestSession([TaskUnit("a")], ContestBudgetState(max_turns=10))
        s.select_task("a")
        memory = ContestMemory(run_id="r", session_id="icpc", competition_id="icpc")
        _apply_action(action="work", arguments={"content": "I will derive the recurrence."}, agent="Agent_1", manifest=m, session=s, memory=memory, config=review_ablation_config(3, 10), strategic_policy=StrategicPolicy(), task_action_executor=lambda *_: {})
        self.assertEqual(s.active_task.versions, [])

    def test_math_short_answer_and_vanilla_work_still_create_answers(self):
        for variant, competition, programming, task_type in (
            ("strategic", "arml_local", False, "team_contest"),
            ("strategic", "science_bowl", False, "quiz"),
            ("vanilla", "icpc", True, "algorithmic_programming"),
        ):
            with self.subTest(variant=variant, competition=competition):
                m = ContestManifest(competition, competition, (task("a", programming, task_type),))
                s = ContestSession([TaskUnit("a", kind="programming" if programming else "non_programming")], ContestBudgetState(max_turns=10))
                s.select_task("a")
                memory = ContestMemory(run_id="r", session_id=competition, competition_id=competition)
                _apply_action(action="work", arguments={"content": "42"}, agent="Agent_1", manifest=m, session=s, memory=memory, config=(review_ablation_config(3, 10) if variant == "strategic" else ContestRunConfig(variant, 3, 10)), strategic_policy=StrategicPolicy(), task_action_executor=lambda *_: {})
                self.assertEqual(s.active_task.versions[-1].content, "42")

    def run_failed_samples(self, max_turns=10, session_checkpoint=None, memory_checkpoint=None, checkpoint_callback=None):
        ids = ["a1", "a2", "b1", "b2", "c1", "c2"]
        m = ContestManifest("icpc", "icpc", tuple(task(k) for k in ids))
        plan = json.dumps(dict(summary="Two per worker", work_assignments={"Agent_1": ids[:2], "Agent_2": ids[2:4], "Agent_3": ids[4:]}, review_assignments={"Agent_1": ids[2:4], "Agent_2": ids[4:], "Agent_3": ids[:2]}, task_order=ids, switch_conditions=[], final_check=[]))
        calls = 0
        def query(*_):
            nonlocal calls
            calls += 1
            return json.dumps({"action": "execute_code", "arguments": {"code": "print(" + str(calls) + ")"}})
        return run_with_test_plan(m, query, review_ablation_config(3, max_turns, stall_turns=3), coach_query_fn=lambda *_: plan, task_action_executor=lambda *_: {"valid": True, "sample_verdict": "WA", "result": "0"}, session_checkpoint=session_checkpoint, memory_checkpoint=memory_checkpoint, checkpoint_callback=checkpoint_callback)

    def test_three_agents_repeated_wa_rotate_without_official_penalty(self):
        result = self.run_failed_samples()
        counts = Counter(e["task_id"] for e in result["memory"]["events"] if e["kind"] == "execute_code_result")
        self.assertGreater(min(counts[k] for k in ("a2", "b2", "c2")), 1, counts)
        self.assertEqual(result["diagnostics"]["attempts"], 0)
        self.assertEqual(result["budget"]["penalty_minutes"], 0)
        self.assertFalse(any(e["kind"] == "action_error" for e in result["memory"]["events"]))
        for row in result["session_checkpoint"]["tasks"]:
            self.assertEqual(row["consecutive_non_ac"], 0)

    def test_resume_keeps_worker_stall_history(self):
        captured = {}
        def checkpoint(session, memory):
            if session["budget"]["turns_used"] == 3:
                captured.update(session=session, memory=memory)
                raise RuntimeError("test interruption")
        with self.assertRaisesRegex(RuntimeError, "test interruption"):
            self.run_failed_samples(checkpoint_callback=checkpoint)
        result = self.run_failed_samples(session_checkpoint=captured["session"], memory_checkpoint=captured["memory"])
        counts = Counter(e["task_id"] for e in result["memory"]["events"] if e["kind"] == "execute_code_result")
        self.assertGreater(min(counts[k] for k in ("a2", "b2", "c2")), 1, counts)

    def test_coached_ac_report_review_and_frozen_submit_complete(self):
        import hashlib
        source = "print(42)"
        source_hash = hashlib.sha256(("good\0\0\0" + source).encode()).hexdigest()
        m = ContestManifest("icpc", "icpc", (task("good"), task("other"), task("b")))
        plan = json.dumps(dict(summary="pipeline", work_assignments={"Agent_1": ["good", "other"], "Agent_2": ["b"]}, review_assignments={"Agent_1": ["b"], "Agent_2": ["good", "other"]}, task_order=["good", "other", "b"], switch_conditions=[], final_check=[]))
        responses = iter([
            {"action": "execute_code", "arguments": {"code": source}},
            {"action": "work", "arguments": {"content": "Thinking about b"}},
            {"action": "speak", "arguments": {"content": "Sample AC; please review"}},
            {"action": "review_answer", "arguments": {"problem_id": "good", "version_hash": source_hash, "decision": "reject", "content": "Check corner cases"}},
            {"action": "submit_code", "arguments": {}},
            {"action": "work", "arguments": {"content": "Still analyzing b"}},
        ])
        submitted = []
        def execute(t, action, args):
            if action == "execute_code":
                return {"valid": True, "sample_verdict": "AC", "result": "42"}
            submitted.append((t.task_id, args["code"]))
            return {"valid": True, "verdict": "AC"}
        result = run_with_test_plan(m, lambda *_: json.dumps(next(responses)), review_ablation_config(2, 3), coach_query_fn=lambda *_: plan, task_action_executor=execute)
        self.assertEqual(submitted, [("good", source)])
        self.assertEqual(result["tasks"]["good"]["state"], "solved")
        self.assertFalse(any(e["kind"] == "action_error" for e in result["memory"]["events"]))


if __name__ == "__main__":
    unittest.main()
