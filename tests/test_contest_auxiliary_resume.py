"""Resume requested auxiliary evaluation without repeating contestant work."""
import copy
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import run_competition_batch as cli
import run_pipeline
from contest_config import BASELINE_NAMES
from contest_manifest import ContestManifest, ManifestTask
from contest_run_identity import (inspect_contest_output, read_completed_contest_result,
                                  read_finalized_contest_result, RunCompatibilityError)
from llm import LLMResponse, LLMToolCall


def scored(value):
    return SimpleNamespace(to_dict=lambda: dict(value))


class ContestAuxiliaryResumeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.out = self.root / "runs/case"
        self.manifest = ContestManifest("fixture", "arml_local", tuple(
            ManifestTask(name, name, None, "Question " + name, "math", 1, False,
                         {"problem_id": name, "gold_label": {"expected_answer": "42"}})
            for name in ("q1", "q2")))
        self.forbid_contestants = False
        self.action_calls = 0
        self.query_factories = 0
        self.action_factories = 0
        def agent(request):
            if self.forbid_contestants:
                raise AssertionError("Contestant called during evaluation-only resume")
            self.action_calls += 1
            names = {item["name"] for item in request.tools}
            name, arguments = ("work", {"problem_id": "q1", "content": "Final answer: 42"}) if "work" in names else (
                "rest", {"reason": "Wait"})
            return LLMResponse("", "mock", "mock", tool_calls=(LLMToolCall(name, arguments),))
        def query_factory(*args, **kwargs):
            if self.forbid_contestants:
                raise AssertionError("Contestant query factory started during judge resume")
            self.query_factories += 1
            return lambda *args: "Coordinate and check."
        def resolve(*, provider, **kwargs):
            if provider == "perplexity":
                if self.forbid_contestants:
                    raise AssertionError("Contestant action provider started during judge resume")
                self.action_factories += 1
                return agent
            return Mock(side_effect=AssertionError("Scoring functions are mocked"))
        self.coord = Mock(return_value=scored({
            "communication_score": 2, "planning_score": 4, "coordination_score": 3}))
        self.interaction = Mock(return_value=scored({"interaction_helpfulness_score": 4}))
        self.cce = Mock(return_value=scored({"cce": 0.5}))
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in (("load_contest_manifest", Mock(return_value=self.manifest)),
                            ("_make_live_query", query_factory), ("resolve_request_fn", resolve),
                            ("score_coordination", self.coord),
                            ("score_interaction_helpfulness", self.interaction), ("score_cce", self.cce)):
            self.stack.enter_context(patch.object(cli, name, value))
        self.stack.enter_context(patch.dict(os.environ, {"OPENAI_API_KEY": "offline-fixture-not-a-key"}))

    def invoke(self, *, resume=False, variant="single_agent", cce=False, collab=True):
        argv = ["batch", "--live", "--provider", "perplexity", "--model", "mock",
                "--judge-provider", "openai", "--judge-model", "mock",
                "--contest-manifest", "unused.json", "--system-variant", variant,
                "--max-turns", "1", "--output", str(self.out),
                "--judge-collab" if collab else "--no-judge-collab"]
        if resume:
            argv.append("--resume")
        if cce:
            argv.append("--judge-cce")
        with patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            try:
                cli.main()
            except SystemExit as exc:
                return exc.code
        return 0

    def result(self):
        return json.loads((self.out / "contest_session.json").read_text(encoding="utf-8"))

    def preserved(self, before, after):
        for key in ("budget", "submissions", "tasks", "memory", "session_checkpoint", "timing", "run"):
            self.assertEqual(before[key], after[key], key)

    def test_all_five_baselines_retry_only_failed_coordination(self):
        for variant in BASELINE_NAMES:
            with self.subTest(baseline=variant):
                self.out = self.root / variant
                self.forbid_contestants = False
                self.coord.reset_mock()
                self.interaction.reset_mock()
                self.coord.side_effect = RuntimeError("Synthetic judge outage")
                self.assertEqual(self.invoke(variant=variant), 1)
                before = self.result()
                self.assertIn("coordination_error", before)
                self.assertIn("interaction", before)
                self.assertEqual(inspect_contest_output(self.out, before["run_identity"]), "resume")
                self.assertEqual(self.interaction.call_count, 1)
                counters = (self.action_calls, self.query_factories, self.action_factories)
                self.forbid_contestants = True
                self.coord.side_effect = None
                self.assertEqual(self.invoke(resume=True, variant=variant), 0)
                after = self.result()
                self.preserved(before, after)
                self.assertEqual(self.coord.call_count, 2)
                self.assertEqual(self.interaction.call_count, 1)
                self.assertEqual(counters, (self.action_calls, self.query_factories, self.action_factories))
                self.assertEqual(after["evaluation_pending"], [])
                self.assertNotIn("coordination_error", after)
                self.assertEqual(inspect_contest_output(self.out, after["run_identity"]), "complete")
                self.assertEqual(self.invoke(resume=True, variant=variant), 0)
                self.assertEqual(self.coord.call_count, 2)

    def test_successful_coordination_survives_interaction_failure(self):
        self.interaction.side_effect = RuntimeError("Interaction judge outage")
        self.assertEqual(self.invoke(), 1)
        before = self.result()
        self.assertIn("coordination", before)
        self.assertIn("interaction_error", before)
        self.forbid_contestants = True
        self.interaction.side_effect = None
        self.assertEqual(self.invoke(resume=True), 0)
        self.preserved(before, self.result())
        self.assertEqual(self.coord.call_count, 1)
        self.assertEqual(self.interaction.call_count, 2)

    def test_interrupt_between_judges_keeps_successful_stage(self):
        self.interaction.side_effect = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.invoke()
        before = self.result()
        self.assertIn("coordination", before)
        self.forbid_contestants = True
        self.interaction.side_effect = None
        self.assertEqual(self.invoke(resume=True), 0)
        self.preserved(before, self.result())
        self.assertEqual(self.coord.call_count, 1)

    def test_cce_retries_only_failed_tasks(self):
        failed = True
        def cce(**kwargs):
            if kwargs["task_text"] == "Question q2" and failed:
                raise RuntimeError("CCE task outage")
            return scored({"cce": 0.5})
        self.cce.side_effect = cce
        self.assertEqual(self.invoke(cce=True, collab=False), 1)
        before = self.result()
        self.assertEqual(set(before["cce"]), {"q1"})
        self.assertIsNone(before["metrics"]["cce"])
        self.forbid_contestants = True
        failed = False
        self.assertEqual(self.invoke(resume=True, cce=True, collab=False), 0)
        after = self.result()
        self.preserved(before, after)
        self.assertEqual(set(after["cce"]), {"q1", "q2"})
        self.assertEqual(after["metrics"]["cce"], 0.5)
        self.assertEqual(self.cce.call_count, 3)
        self.assertEqual(after["cce_errors"], {})

    def test_pending_result_is_not_exported_as_complete(self):
        self.coord.side_effect = RuntimeError("Judge outage")
        self.assertEqual(self.invoke(), 1)
        result = self.result()
        with self.assertRaises(RunCompatibilityError):
            read_completed_contest_result(self.out, result["run_identity"])
        self.assertEqual(read_finalized_contest_result(self.out, result["run_identity"]), result)

    def test_scheduler_judge_resume_skips_docker_and_programming_preflight(self):
        self.coord.side_effect = RuntimeError("Judge outage")
        self.assertEqual(self.invoke(), 1)
        result = self.result()
        job = {"id": "case", "route": "native", "competition": "icpc", "manifest": "unused.json"}
        with patch.object(cli, "inspect_contest_run", return_value=("resume", result["run_identity"])), \
             patch("contest_manifest.load_contest_manifest", side_effect=AssertionError("No contestant preflight")), \
             patch.object(run_pipeline.subprocess, "run", side_effect=AssertionError("No Docker")), \
             patch.object(run_pipeline.urllib.request, "urlopen", side_effect=AssertionError("No gateway")):
            command = run_pipeline.command(job, self.root, SimpleNamespace(provider="perplexity", model="mock"))
        self.assertIn("--resume", command)

    def test_nonfinite_auxiliary_score_is_not_certified_complete(self):
        self.coord.return_value = scored({
            "communication_score": 2, "planning_score": 4, "coordination_score": float("nan")})
        self.assertEqual(self.invoke(), 1)
        result = self.result()
        self.assertNotIn("coordination", result)
        self.assertEqual(result["evaluation_pending"], ["coordination"])


if __name__ == "__main__":
    unittest.main()
