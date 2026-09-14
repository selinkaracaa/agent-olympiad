"""Rubric definitions, not judge output, govern finite scoring and evidence."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evaluation.models import (Criterion, CriterionResult, EvaluationError, EvaluationResult,
    Rubric, load_rubric, parse_evaluation_payload, scale_rubric)


class RubricValidationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.rubric = Rubric("r", "R", 1, (Criterion("c", "C", 1, "Evidence"),))
        self.payload = {"criteria": [{"id": "c", "score": 1, "max_score": 1,
            "confidence": 1, "observable": True, "evidence": ["Page 1"], "justification": "Evidence"}],
            "total_score": 1, "max_score": 1}

    def parse(self, payload=None, rubric=None):
        return parse_evaluation_payload(json.dumps(payload or self.payload),
            rubric=rubric or self.rubric, evaluator_id="fixture", evaluator_version="1",
            prompt_version="1", model="mock")

    def test_nonfinite_criterion_values_are_rejected(self):
        for field in ("score", "max_score", "confidence"):
            for value in ("NaN", "Infinity", "-Infinity", "1e999", float("nan"), float("inf")):
                with self.subTest(field=field, value=value):
                    payload = copy.deepcopy(self.payload)
                    payload["criteria"][0][field] = value
                    with self.assertRaises(EvaluationError):
                        self.parse(payload)

    def test_nonfinite_totals_are_rejected_before_arithmetic_repair(self):
        for field in ("total_score", "max_score"):
            for value in ("NaN", "Infinity", "-Infinity", "1e999"):
                with self.subTest(field=field, value=value):
                    payload = copy.deepcopy(self.payload)
                    payload[field] = value
                    with self.assertRaisesRegex(EvaluationError, "finite"):
                        self.parse(payload)

    def test_finite_arithmetic_slip_is_still_repaired(self):
        self.payload["total_score"] = 0
        result = self.parse()
        self.assertEqual(result.total_score, 1)
        self.assertTrue(result.warnings)

    def test_judge_cannot_disable_required_evidence(self):
        self.payload["criteria"][0].update(observable=False, evidence=[])
        with self.assertRaisesRegex(EvaluationError, "Observability"):
            self.parse()

    def test_blank_evidence_is_not_support(self):
        self.payload["criteria"][0]["evidence"] = ["", "  "]
        with self.assertRaisesRegex(EvaluationError, "evidence"):
            self.parse()

    def test_observable_must_be_boolean(self):
        for value in ("false", 0, None):
            with self.subTest(value=value):
                self.payload["criteria"][0]["observable"] = value
                with self.assertRaisesRegex(EvaluationError, "Observability"):
                    self.parse()

    def test_omitted_observability_uses_rubric(self):
        del self.payload["criteria"][0]["observable"]
        self.payload["criteria"][0]["evidence"] = []
        rubric = Rubric("r", "R", 1, (Criterion("c", "C", 1, "Not observable", observable=False),))
        self.assertFalse(self.parse(rubric=rubric).criteria[0].observable)

    def test_direct_result_validation_rejects_nonfinite_values(self):
        result = EvaluationResult("fixture", "1", "1", "mock", "r",
            [CriterionResult("c", float("nan"), 1, ["Page 1"], "Evidence", 1)], float("nan"), 1)
        with self.assertRaisesRegex(EvaluationError, "finite"):
            result.validate(self.rubric)

    def test_rubric_loader_rejects_nonfinite_maxima_and_totals(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rubric.json"
            for field in ("total_points", "max_score", "min_score"):
                payload = {"rubric_id": "r", "title": "R", "total_points": 1,
                           "criteria": [{"id": "c", "name": "C", "description": "Evidence", "max_score": 1}]}
                (payload if field == "total_points" else payload["criteria"][0])[field] = "NaN"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(EvaluationError, "finite"):
                    load_rubric(path)

    def test_nonfinite_scale_is_rejected(self):
        with self.assertRaisesRegex(EvaluationError, "finite"):
            scale_rubric(self.rubric, float("nan"))


if __name__ == "__main__":
    unittest.main()
