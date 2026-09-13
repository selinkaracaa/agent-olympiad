"""Batch entry guards: private assets, completion preflight, and exit status."""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
SPEC = importlib.util.spec_from_file_location("guarded_pipeline", ROOT / "scripts/run_pipeline.py")
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)


class AssetBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(pipeline, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        pipeline.write(self.root / "data/benchmarks/index.json", {"olympiads": [
            {"id": "proof", "benchmark_path": "proof.json"}
        ]})
        for component, data in (
            ("competition", {"deliverable": {"official_deliverable": "proof_packet"}}),
            ("collaboration", {}),
            ("evaluation", {"scoring": {"rubric_path": "rubric.json"}}),
        ):
            pipeline.write(self.root / "data/rules/proof" / (component + ".json"), data)
        pipeline.write(self.root / "rubric.json", {})
        for name in ("problems.pdf", "solutions.pdf"):
            (self.root / name).write_bytes(b"%PDF-1.4\nOffline role fixture")
        (self.root / "nested").mkdir()

    def row(self, assets=None, source="solutions.pdf"):
        row = {"problem_id": "proof_1", "source_file": source}
        if assets is not None:
            row["provenance"] = {"assets": assets}
        pipeline.write(self.root / "proof.json", [row])
        return row

    def register(self):
        return pipeline.register(self.root / "out")["jobs"][0]

    def test_judge_only_source_fallback_is_blocked(self):
        self.row([{"path": "solutions.pdf", "role": "judge_only"}])
        job = self.register()
        self.assertNotIn("task_pdf", job)
        self.assertTrue(job["blockers"])

    def test_conflicting_roles_use_canonical_path_and_fail_closed(self):
        self.row([
            {"path": "nested/../solutions.pdf", "role": "agent_visible"},
            {"path": "./solutions.pdf", "role": "judge_only"},
        ])
        job = self.register()
        self.assertNotIn("task_pdf", job)
        self.assertTrue(job["blockers"])

    def test_declared_assets_do_not_fall_back_to_unclassified_source(self):
        self.row([{"path": "chart.png", "role": "agent_visible"}])
        job = self.register()
        self.assertNotIn("task_pdf", job)
        self.assertTrue(job["blockers"])

    def test_explicit_public_pdf_wins_over_judge_only_source(self):
        self.row([
            {"path": "problems.pdf", "role": "agent_visible"},
            {"path": "solutions.pdf", "role": "judge_only"},
        ])
        job = self.register()
        self.assertEqual(Path(job["task_pdf"]), self.root / "problems.pdf")
        self.assertEqual(job["blockers"], [])

    def test_legacy_source_without_asset_manifest_remains_supported(self):
        self.row(source="problems.pdf")
        self.assertEqual(Path(self.register()["task_pdf"]), self.root / "problems.pdf")

    def test_existing_registry_cannot_bypass_current_role_checks(self):
        self.row([{"path": "solutions.pdf", "role": "judge_only"}])
        old_job = {
            "id": "legacy", "competition": "proof", "route": "document",
            "problem_ids": ["proof_1"], "task_pdf": str(self.root / "solutions.pdf"),
            "rubric": str(self.root / "rubric.json"), "blockers": [],
        }
        with self.assertRaises(ValueError):
            pipeline.command(old_job, self.root / "old-output",
                             SimpleNamespace(provider="mock", model="mock"))

    def test_existing_registry_rejects_changed_selected_pdf(self):
        self.row([{"path": "problems.pdf", "role": "agent_visible"}])
        job = self.register()
        job["task_pdf"] = str(self.root / "solutions.pdf")
        with self.assertRaises(ValueError):
            pipeline.command(job, self.root / "out",
                             SimpleNamespace(provider="mock", model="mock"))

    def test_valid_existing_registry_can_build_artifact_command(self):
        self.row([{"path": "problems.pdf", "role": "agent_visible"}])
        job = self.register()
        cmd = pipeline.command(job, self.root / "out",
                               SimpleNamespace(provider="mock", model="mock"))
        self.assertEqual(cmd[cmd.index("--task-pdf") + 1], str(self.root / "problems.pdf"))


class CompletionPreflightTests(unittest.TestCase):
    def setUp(self):
        self.job = {"id": "icpc-test", "competition": "icpc",
                    "route": "native", "manifest": "fixture.json"}
        self.args = SimpleNamespace(provider="mock", model="mock")
        self.manifest = SimpleNamespace(tasks=[SimpleNamespace(
            programming=True, benchmark={"evaluation": {
                "vjudge_prob_num": "A", "status": "remote_judge_ready",
            }},
        )])

    def test_complete_identity_skips_runtime_preflight(self):
        with patch("run_competition_batch.inspect_contest_run", return_value=("complete", {})) as inspect, \
             patch("contest_manifest.load_contest_manifest", side_effect=AssertionError("unnecessary manifest load")), \
             patch.object(pipeline.subprocess, "run") as process, \
             patch.object(pipeline.urllib.request, "urlopen") as health:
            self.assertIsNone(pipeline.command(self.job, Path("unused"), self.args))
        inspect.assert_called_once()
        process.assert_not_called()
        health.assert_not_called()

    def test_incompatible_identity_fails_before_external_preflight(self):
        with patch("run_competition_batch.inspect_contest_run", side_effect=ValueError("identity mismatch")), \
             patch("contest_manifest.load_contest_manifest", return_value=self.manifest), \
             patch.object(pipeline.subprocess, "run") as process:
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                pipeline.command(self.job, Path("unused"), self.args)
        process.assert_not_called()

    def test_new_and_resume_runs_still_require_docker(self):
        def probe(cmd, **kwargs):
            if cmd[0] == "powershell.exe":
                return SimpleNamespace(stdout="0", returncode=0)
            raise RuntimeError("Docker unavailable")
        for state in ("new", "resume"):
            with self.subTest(state=state), \
                 patch("run_competition_batch.inspect_contest_run", return_value=(state, {})) as inspect, \
                 patch("contest_manifest.load_contest_manifest", return_value=self.manifest), \
                 patch.object(pipeline.subprocess, "run", side_effect=probe):
                with self.assertRaisesRegex(RuntimeError, "Docker unavailable"):
                    pipeline.command(self.job, Path("unused"), self.args)
                inspect.assert_called_once()

    def test_ready_resume_keeps_resume_flag_and_health_probe(self):
        with patch("run_competition_batch.inspect_contest_run", return_value=("resume", {})), \
             patch("contest_manifest.load_contest_manifest", return_value=self.manifest), \
             patch.object(pipeline.subprocess, "run", return_value=SimpleNamespace(stdout="0", returncode=0)), \
             patch.object(pipeline.urllib.request, "urlopen", return_value=io.StringIO('{"ok": true}')) as health:
            cmd = pipeline.command(self.job, Path("unused"), self.args)
        self.assertIn("--resume", cmd)
        health.assert_called_once()


class BatchExitTests(unittest.TestCase):
    def job(self, name="a", competition="arml_local", route="native", blockers=None):
        return {"id": name, "competition": competition, "session": name,
                "route": route, "blockers": blockers or []}

    def run_batch(self, jobs, *, stage="run", extra=(), commands=None,
                  returncode=1, artifact_status=None):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            pipeline.write(out / "registry.json", {"jobs": jobs})
            def run(*args, **kwargs):
                if artifact_status is not None:
                    pipeline.write(out / "runs/a/result.json", {"status": artifact_status})
                elif returncode == 0:
                    pipeline.write(out / "runs/a/contest_session.json", {"grade": {"graded": True}})
                return SimpleNamespace(returncode=returncode)
            command_values = iter(commands or [["mock-runner"]])
            def command_result(job, output, args, *, completed_results=None):
                value = next(command_values)
                if value is None and completed_results is not None:
                    completed_results[job["id"]] = {"grade": {"graded": True}}
                return value
            with patch.object(sys, "argv", ["run_pipeline.py", stage, "--output", str(out), *extra]), \
                 patch.object(pipeline, "command", side_effect=command_result) as command, \
                 patch.object(pipeline.subprocess, "run", side_effect=run) as process:
                code = pipeline.main()
            state = pipeline.read(out / "batch_status.json")
            self.assertFalse((out / "pipeline.lock").exists())
            return code, state, command.call_count, process.call_count

    def test_failed_child_returns_nonzero_and_preserves_reason(self):
        code, state, _, _ = self.run_batch([self.job()])
        self.assertNotEqual(code, 0)
        self.assertIn("Runner exit 1", state["jobs"]["a"]["reason"])

    def test_selected_registration_blocker_returns_nonzero_without_launch(self):
        code, state, command_calls, process_calls = self.run_batch(
            [self.job(blockers=["Missing task PDF"])])
        self.assertNotEqual(code, 0)
        self.assertEqual(state["counts"], {"blocked": 1})
        self.assertEqual((command_calls, process_calls), (0, 0))

    def test_unselected_blocked_job_does_not_fail_successful_selection(self):
        code, state, _, process_calls = self.run_batch(
            [self.job(), self.job("b", "mcm", blockers=["Missing rubric"])],
            extra=("--competitions", "arml_local"), commands=[None],
        )
        self.assertEqual(code, 0)
        self.assertEqual(state["jobs"]["a"]["status"], "complete")
        self.assertEqual(process_calls, 0)

    def test_successful_child_returns_zero(self):
        code, state, _, _ = self.run_batch(
            [self.job()], commands=[["mock-runner"], None], returncode=0)
        self.assertEqual(code, 0)
        self.assertEqual(state["jobs"]["a"]["status"], "complete")

    def test_incomplete_artifact_returns_nonzero(self):
        code, state, _, _ = self.run_batch(
            [self.job(route="document")], returncode=0, artifact_status="ungraded")
        self.assertNotEqual(code, 0)
        self.assertEqual(state["jobs"]["a"]["status"], "ungraded")

    def test_report_only_returns_zero_with_blocked_jobs(self):
        code, _, command_calls, process_calls = self.run_batch(
            [self.job(blockers=["Missing task PDF"])], stage="report")
        self.assertEqual(code, 0)
        self.assertEqual((command_calls, process_calls), (0, 0))


if __name__ == "__main__":
    unittest.main()
