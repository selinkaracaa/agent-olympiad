"""An execution-complete ungraded run stays ungraded on every scheduler pass."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import run_pipeline
import run_competition_batch
from contest_config import ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask
from contest_run_identity import build_run_identity, inspect_contest_output


class PipelineCompletionStateTests(unittest.TestCase):
    def run_existing(self, graded):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            source = out / "src"
            source.mkdir()
            manifest = ContestManifest("fixture", "arml_local", (
                ManifestTask("q", "q", None, "Question", "math", 1, False, {}),))
            identity = build_run_identity(manifest, ContestRunConfig("single_agent", 1, 1),
                                          execution={}, evaluation={}, source_root=source)
            settings = identity["settings"]
            result = {**{k: settings[k] for k in (
                "session_id", "competition_id", "protocol_version", "action_set_version")},
                "system_variant": "single_agent", "run_identity": identity,
                "grade": {"graded": graded, "score": 0 if graded else None, "max_score": 1,
                          "tasks": {"q": {"graded": graded, "reason": "Judge unavailable"}}},
                "metrics": {"task_utility": 0 if graded else None},
                "session_checkpoint": {"final_summary": {}}}
            job = {"id": "case", "route": "native", "competition": "arml_local",
                   "session": "fixture", "manifest": "unused.json", "blockers": []}
            run_pipeline.write(out / "registry.json", {"jobs": [job]})
            result_path = out / "runs/case/contest_session.json"
            run_pipeline.write(result_path, result)
            original = result_path.read_bytes()
            def inspect(argv):
                dest = Path(argv[argv.index("--output") + 1])
                return inspect_contest_output(dest, identity), identity
            history = []
            with patch.object(run_competition_batch, "inspect_contest_run", side_effect=inspect), \
                 patch.object(run_pipeline.subprocess, "run", side_effect=AssertionError("Do not rerun contestants")), \
                 patch.object(sys, "argv", ["pipeline", "run", "--output", str(out)]), \
                 redirect_stdout(io.StringIO()):
                for _ in range(2):
                    code = run_pipeline.main()
                    state = run_pipeline.read(out / "batch_status.json")
                    history.append((code, state["jobs"]["case"]))
            self.assertEqual(result_path.read_bytes(), original)
            return history

    def test_repeated_ungraded_resume_never_becomes_complete(self):
        for code, state in self.run_existing(False):
            self.assertEqual(code, 1)
            self.assertEqual(state["status"], "ungraded")
            self.assertIn("Judge unavailable", state["reason"])

    def test_fully_graded_resume_stays_complete_without_execution(self):
        for code, state in self.run_existing(True):
            self.assertEqual(code, 0)
            self.assertEqual(state["status"], "complete")

    def test_incomplete_evaluation_without_detailed_reason_is_explicit(self):
        state = run_pipeline.native_completion_state({"grade": {"graded": False}})
        self.assertEqual(state["status"], "ungraded")
        self.assertIn("evaluation is incomplete", state["reason"])


if __name__ == "__main__":
    unittest.main()
