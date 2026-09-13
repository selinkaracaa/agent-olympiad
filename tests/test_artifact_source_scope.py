"""Artifact identity tracks runtime code, not unrelated generated Python files."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfWriter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import otc_artifact_pipeline as artifact


class ArtifactSourceScopeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "src").mkdir()
        (self.root / "src/engine.py").write_text("VERSION = 1\n", encoding="utf-8")
        self.pdf = self.root / "task.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        with self.pdf.open("wb") as stream:
            writer.write(stream)
        self.rubric = artifact.resolve_rubric(artifact.load_rule_card("wsc_writing", required=True), ROOT)

    def identity(self):
        with patch.object(artifact, "ROOT", self.root), patch.object(artifact, "preflight_renderer"):
            return artifact.prepare_artifact_run(
                competition="wsc_writing", task_pdf=self.pdf, output=self.root / "run",
                rubric=self.rubric, rules_root=ROOT / "data/rules", max_turns=1,
                provider="openai", model="mock", judge_model="mock", system_variant="single_agent")["identity"]

    def test_generated_files_outside_runtime_do_not_invalidate_resume(self):
        before = self.identity()
        for directory in ("results/other-run", "scripts", "tests"):
            folder = self.root / directory
            folder.mkdir(parents=True)
            (folder / "generated.py").write_text("print(42)\n", encoding="utf-8")
        after = self.identity()
        self.assertEqual(before, after)
        self.assertEqual(set(after["settings"]["source_hashes"]), {"engine.py"})

    def test_actual_runtime_change_still_invalidates_resume(self):
        before = self.identity()
        (self.root / "src/engine.py").write_text("VERSION = 2\n", encoding="utf-8")
        self.assertNotEqual(before["fingerprint"], self.identity()["fingerprint"])


if __name__ == "__main__":
    unittest.main()
