"""Regression seams for the three requested ICPC fixes; no model/remote calls."""
import sys
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_runner import ContestRunConfig, _apply_action, _collect_programming_deadline, run_contest
from contest_adapters import EnvironmentTaskExecutor
from contest_session import ContestSession, ContestBudgetState, TaskUnit
from judge import package_from_sample_directory
from judge.checkers import check_output
from strategy import StrategicPolicy


from contest_feature_fixtures import review_ablation_config, run_with_test_plan

class GapRepairTests(unittest.TestCase):
    def seed(self, programming=True, variant="strategic", review=None):
        self.task = ManifestTask("a", "a", None, "Solve", "algorithmic_programming" if programming else "quiz", 1, programming, {})
        self.manifest = ContestManifest("s", "icpc", (self.task,))
        self.session = ContestSession([TaskUnit("a", kind="programming" if programming else "non_programming")], ContestBudgetState(max_turns=20))
        self.session.select_task("a")
        self.memory = ContestMemory(run_id="r", session_id="s", competition_id="icpc")
        self.config = (review_ablation_config(2, 20, require_review=review) if variant == "strategic" else ContestRunConfig(variant, 2, 20, require_review=review))

    def execute(self, code, executor, agent="Agent_1", **arguments):
        _apply_action(action="execute_code", arguments={"code": code, **arguments}, agent=agent,
                      manifest=self.manifest, session=self.session, memory=self.memory, config=self.config,
                      strategic_policy=StrategicPolicy(), task_action_executor=executor)

    def source(self, code, verdict=None):
        version = self.session.create_answer(code, author="Agent_1")
        self.memory.append(task_id="a", question_id=None, actor="Tool", visibility="public",
                           kind="programming_source_recorded", payload={"version_hash": version.version_hash}, turn=0)
        if verdict:
            self.memory.append(task_id="a", question_id=None, actor="Judge", visibility="public",
                               kind="sample_judge_result", payload={"version_hash": version.version_hash, "sample_verdict": verdict}, turn=0)
        return version

    def collect(self):
        calls = []
        _collect_programming_deadline(self.manifest, self.session, self.memory,
                                     lambda t, a, args: calls.append(args["code"]) or {"valid": True, "verdict": "WA"}, lambda: None)
        return calls

    def test_infiltration_reordered_and_alternative_optimal_sets(self):
        package = package_from_sample_directory("icpc_wf_2012_infiltration2", ROOT / "data/benchmarks/icpc/samples/icpc_wf_2012_infiltration2")
        case = package.tests[0]
        expected = case.answer_path.read_text(encoding="utf-8")
        for answer in ("Case 1: 1 2\nCase 2: 2 2 1\nCase 3: 2 3 2",
                       "Case 1: 1 2\nCase 2: 2 2 3\nCase 3: 2 2 3"):
            with self.subTest(answer=answer):
                self.assertTrue(check_output(expected, answer, package.checker, input_path=case.input_path)[0])

    def test_infiltration_rejects_invalid_outputs(self):
        package = package_from_sample_directory("icpc_wf_2012_infiltration2", ROOT / "data/benchmarks/icpc/samples/icpc_wf_2012_infiltration2")
        case = package.tests[0]
        expected = case.answer_path.read_text(encoding="utf-8")
        for bad in (expected.replace("Case 1: 1 2", "Case 1: 1 1"),
                    expected.replace("Case 2: 2 1 2", "Case 2: 2 1 1"),
                    expected.replace("Case 2: 2 1 2", "Case 2: 2 1 4"),
                    expected.replace("Case 2: 2 1 2", "Case 2: 3 1 2 3"),
                    expected.replace("Case 2:", "Case 9:"), expected + "\nextra", ""):
            with self.subTest(bad=bad):
                self.assertFalse(check_output(expected, bad, package.checker, input_path=case.input_path)[0])

    def test_unrelated_checker_stays_strict(self):
        p = package_from_sample_directory("another_problem", ROOT)
        self.assertEqual(p.checker, {"mode": "token"})
        self.assertFalse(check_output("1 2", "2 1", p.checker)[0])

    def test_infiltration_single_cell_and_whitespace(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "one.in"
            p.write_text("1\n0\n", encoding="utf-8")
            self.assertTrue(check_output("Case 1: 1 1", "\nCase\t1: 1\n1\n", {"mode": "infiltration"}, input_path=p)[0])
            self.assertFalse(check_output("Case 1: 1 1", "Case 1: 0", {"mode": "infiltration"}, input_path=p)[0])

    def test_adapter_sample_context_tracks_file_changes_and_disables_custom_bundle_cache(self):
        self.seed()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "data/benchmarks/icpc/samples/a"
            folder.mkdir(parents=True)
            (folder / "sample.in").write_text("1\n", encoding="utf-8")
            answer = folder / "sample.ans"
            answer.write_text("2\n", encoding="utf-8")
            executor = EnvironmentTaskExecutor(self.manifest, benchmark_root=root / "data/benchmarks")
            first = executor.execution_context_key(self.task)
            self.assertIsInstance(first, str)
            self.assertEqual(first, executor.execution_context_key(self.task))
            answer.write_text("3\n", encoding="utf-8")
            self.assertNotEqual(first, executor.execution_context_key(self.task))
            self.task.benchmark["evaluation"] = {"official_package_path": "custom"}
            self.assertIsNone(executor.execution_context_key(self.task))

    def test_full_engine_cached_failures_do_not_reset_source_or_progress_counters(self):
        self.seed()
        calls = []
        def executor(*args):
            calls.append(args)
            return {"valid": True, "sample_verdict": "WA"}
        result = run_with_test_plan(self.manifest,
                             lambda *_: json.dumps({"action": "execute_code", "arguments": {"code": "print(0)"}}),
                             review_ablation_config(1, 4, stall_turns=10), task_action_executor=executor,
                             session_checkpoint=self.session.checkpoint())
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["diagnostics"]["programming_duplicate_executions_avoided"], 3)
        self.assertEqual(len(result["session_checkpoint"]["tasks"][0]["versions"]), 1)
        events = result["memory"]["events"]
        progress = [e["payload"] for e in events if e["kind"] == "programming_worker_progress"]
        self.assertEqual(progress[-1]["actions_without_source"], 3)
        self.assertFalse(progress[-1]["progressed"])
        self.assertFalse(any(e["kind"] == "action_error" for e in events))

    def test_failed_source_reused_across_agents_and_resume_without_new_version(self):
        self.seed()
        calls = []
        def executor(*args):
            calls.append(args)
            return {"valid": True, "sample_verdict": "WA", "sample_cases": [{"actual": "wrong"}]}
        self.execute("print(0)", executor)
        self.source("print(1)")  # Retrying older bad code must not overwrite this.
        latest = self.session.active_task.versions[-1]
        self.memory = ContestMemory.from_checkpoint_json(self.memory.to_checkpoint_json())
        self.session = ContestSession.from_checkpoint(self.session.checkpoint())
        self.execute("print(0)\n", executor, agent="Agent_2")
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.session.active_task.versions[-1], latest)
        cached = self.memory.archival_snapshot()["events"][-1]
        self.assertEqual(cached["kind"], "execute_code_result")
        self.assertTrue(cached["payload"]["execution_reused"])
        self.assertEqual(cached["payload"]["sample_verdict"], "WA")

    def test_changed_source_and_context_are_executed(self):
        self.seed()
        calls = []
        def executor(*args):
            calls.append(args)
            return {"valid": True, "sample_verdict": "WA"}
        executor.execution_context_key = lambda task: "samples-v1"
        self.execute("print(0)", executor)
        self.execute("print(1)", executor)
        executor.execution_context_key = lambda task: "samples-v2"
        self.execute("print(0)", executor)
        self.assertEqual(len(calls), 3)

    def test_infrastructure_unknown_and_success_are_not_cached(self):
        for result in ({"valid": False, "sample_verdict": "WA"}, {"valid": True, "sample_verdict": "JUDGE_ERROR"},
                       {"valid": True, "sample_verdict": None}, {"valid": True, "sample_verdict": "AC"}):
            with self.subTest(result=result):
                self.seed()
                calls = []
                def executor(*args):
                    calls.append(args)
                    return result
                self.execute("print(0)", executor)
                self.execute("print(0)", executor)
                self.assertEqual(len(calls), 2)

    def test_dedup_does_not_change_vanilla_nonprogramming_or_review_disabled(self):
        for programming, variant, review in ((True, "vanilla", None), (False, "strategic", None), (True, "strategic", False)):
            with self.subTest(programming=programming, variant=variant, review=review):
                self.seed(programming, variant, review)
                calls = []
                def executor(*args):
                    calls.append(args)
                    return {"valid": True, "sample_verdict": "WA"}
                self.execute("print(0)", executor)
                self.execute("print(0)", executor)
                self.assertEqual(len(calls), 2)

    def test_deadline_submits_new_source_after_official_failure(self):
        self.seed()
        self.source("print(0)", "AC")
        self.session.submit("TLE")
        self.source("print(1)", "AC")
        self.assertEqual(self.collect(), ["print(1)"])
        self.assertEqual(self.collect(), [])

    def test_deadline_preserves_sample_ac_over_later_wa(self):
        self.seed()
        self.source("print(1)", "AC")
        self.source("print(2)", "WA")
        self.assertEqual(self.collect(), ["print(1)"])
        intent = next(e for e in self.memory.archival_snapshot()["events"] if e["kind"] == "programming_deadline_submit_started")
        self.assertEqual(intent["payload"]["selection_reason"], "sample_ac")

    def test_deadline_does_not_resubmit_same_source_with_new_version_hash(self):
        self.seed()
        self.source("print(1)", "AC")
        self.session.submit("WA")
        self.session.create_answer("thinking")
        self.source("print(1)\n", "AC")
        self.source("print(2)", "WA")
        self.assertEqual(self.collect(), ["print(2)"])

    def test_deadline_sample_ac_tie_prefers_approved_historical_candidate(self):
        self.seed()
        self.source("print(1)", "AC")
        self.session.record_review("Agent_2", "checked", decision="approve")
        self.source("print(2)", "AC")
        self.assertEqual(self.collect(), ["print(1)"])

    def test_deadline_ac_tie_without_approval_prefers_recent_candidate(self):
        self.seed()
        self.source("print(1)", "AC")
        self.source("print(2)", "AC")
        self.assertEqual(self.collect(), ["print(2)"])

    def test_deadline_active_cooldown_does_not_crash_or_bypass_policy(self):
        self.seed()
        self.source("print(0)", "AC")  # Historical, unsubmitted candidate.
        self.source("print(1)", "WA")
        for _ in range(3):
            self.session.submit("WA")
        self.assertEqual(self.collect(), [])
        self.assertTrue(any(e["kind"] == "programming_deadline_skipped" for e in self.memory.archival_snapshot()["events"]))

    def test_empty_recorded_source_is_reported(self):
        self.seed()
        self.source("   ")
        self.assertEqual(self.collect(), [])
        self.assertTrue(any(e["kind"] == "programming_deadline_no_source" for e in self.memory.archival_snapshot()["events"]))

    def test_deadline_does_not_retry_uncertain_normal_submission(self):
        self.seed()
        self.source("print(1)", "AC")
        self.session.submit("PENDING", valid=False)
        self.assertEqual(self.collect(), [])

    def test_deadline_retries_local_only_sample_rejection(self):
        self.seed()
        self.source("print(1)", "WA")
        self.session.submit("SAMPLE_WA", valid=False)
        self.assertEqual(self.collect(), ["print(1)"])


if __name__ == "__main__":
    unittest.main()
