"""Completed artifact reuse requires identity, submission and score bindings."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from artifacts.assets import file_sha256
from contest_run_identity import content_hash
from evaluation.models import CriterionResult, EvaluationResult
from otc_artifact_pipeline import run_artifact_contest, _evaluation_binding


class ArtifactResultIdentityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.identity = {"settings": {"run": "A"}, "fingerprint": content_hash({"run": "A"})}
        self.rubric = self.root / "rubric.json"
        self.write("rubric.json", {"rubric_id": "r", "title": "R", "total_points": 1,
            "criteria": [{"id": "c", "name": "C", "max_score": 1, "description": "Evidence"}]})
        source = self.root / "submission.txt"
        source.write_text("Submitted answer", encoding="utf-8")
        pdf = self.root / "submission.pdf"
        pdf.write_bytes(b"%PDF-1.4 fixture")
        receipt = {"source": str(source), "source_sha256": file_sha256(source),
                   "pdf": str(pdf), "pdf_sha256": file_sha256(pdf)}
        evaluation = EvaluationResult("fixture", "1", "1", "mock", "r",
            [CriterionResult("c", 1, 1, ["Evidence"], "Fixture", 1)], 1, 1).to_dict()
        self.result = {"status": "complete", "graded": True, "run_identity": self.identity,
            "artifact": receipt, "evaluation": evaluation,
            "contest_file": str(self.root / "contest_session.json"),
            "evaluation_binding": _evaluation_binding(self.identity, receipt, evaluation)}
        self.contest = {"run_identity": self.identity, "submissions": {"deliverable": "Submitted answer"},
                        "session_checkpoint": {"final_summary": {}}}
        self.write("run_identity.json", self.identity)
        self.write("contest_session.json", self.contest)
        self.prepared = {"output": self.root, "identity": self.identity, "rubric": self.rubric}

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def resume(self):
        self.write("result.json", self.result)
        no_call = Mock(side_effect=AssertionError("No model calls during completed reuse"))
        try:
            return run_artifact_contest(self.prepared, resume=True,
                                        agent_request=no_call, judge_request=no_call)
        finally:
            no_call.assert_not_called()

    def test_valid_complete_result_is_reused_exactly(self):
        self.assertEqual(self.resume(), self.result)

    def test_foreign_result_is_refused_even_when_directory_identity_matches(self):
        self.result["run_identity"] = {"settings": {"run": "B"},
                                       "fingerprint": content_hash({"run": "B"})}
        with self.assertRaisesRegex(ValueError, "configuration mismatch"):
            self.resume()

    def test_missing_result_identity_is_refused(self):
        del self.result["run_identity"]
        with self.assertRaisesRegex(ValueError, "missing resolved run identity"):
            self.resume()

    def test_score_cannot_be_swapped_without_changing_binding(self):
        self.result["evaluation"]["total_score"] = 0
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            self.resume()

    def test_invalid_score_is_rejected_even_with_recomputed_binding(self):
        self.result["evaluation"]["total_score"] = 0
        self.result["evaluation_binding"] = _evaluation_binding(
            self.identity, self.result["artifact"], self.result["evaluation"])
        with self.assertRaisesRegex(ValueError, "criterion sum"):
            self.resume()

    def test_receipt_cannot_point_to_another_submission(self):
        self.contest["submissions"]["deliverable"] = "Different answer"
        self.write("contest_session.json", self.contest)
        with self.assertRaisesRegex(ValueError, "finalized submission"):
            self.resume()

    def test_foreign_session_is_rejected(self):
        self.contest["run_identity"] = {"settings": {"run": "B"},
                                       "fingerprint": content_hash({"run": "B"})}
        self.write("contest_session.json", self.contest)
        with self.assertRaisesRegex(ValueError, "configuration mismatch"):
            self.resume()

    def test_tampered_pdf_is_rejected(self):
        Path(self.result["artifact"]["pdf"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "modified"):
            self.resume()

    def test_ungraded_complete_marker_is_rejected(self):
        self.result["graded"] = False
        with self.assertRaisesRegex(ValueError, "successful evaluation"):
            self.resume()

    def test_legacy_unbound_result_is_not_certified(self):
        del self.result["evaluation_binding"]
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            self.resume()


if __name__ == "__main__":
    unittest.main()
