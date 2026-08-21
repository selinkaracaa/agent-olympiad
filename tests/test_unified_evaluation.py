"""Tests for dual media ingest, gold grading, registry, and eval modes."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from artifacts.pdf_ingest import PdfIngestError, parse_pdf, slice_pdf
from evaluation.default_rubrics import ensure_default_rubrics
from evaluation.finalize import apply_registered_judge
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts, parse_numbered_answers
from evaluation.modes import QuestionSpec, build_competition_packet, build_question_packet
from evaluation.registry import RegistryError, resolve_evaluator_spec, strategy_kind
import json


def write_pdf(path: Path, pages: int = 2) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as handle:
        writer.write(handle)


class PdfIngestTests(unittest.TestCase):
    def test_render_images_and_max_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = root / "task.pdf"
            write_pdf(pdf, pages=3)
            parsed = parse_pdf(pdf, root / "pages", media="images", page_start=1, page_end=2)
            self.assertEqual(len(parsed.page_images), 2)
            self.assertTrue(parsed.page_images[0].path.is_file())
            self.assertEqual(parsed.page_images[0].mime_type, "image/jpeg")
            self.assertTrue(parsed.page_images[0].path.suffix == ".jpg")
            with self.assertRaises(PdfIngestError):
                parse_pdf(pdf, root / "too_many", media="images", max_pages=1)

    def test_slice_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = root / "task.pdf"
            write_pdf(pdf, pages=3)
            sliced = slice_pdf(pdf, root / "q.pdf", page_start=2, page_end=3)
            from pypdf import PdfReader

            self.assertEqual(len(PdfReader(str(sliced)).pages), 2)


class GoldEvaluatorTests(unittest.TestCase):
    def test_multipart_match(self):
        parts = load_gold_parts(
            {
                "parts": [
                    {"id": "1", "expected": "(-6, 13)", "points": 4},
                    {"id": "2", "expected": "-21", "points": 4},
                    {"id": "3", "expected": "52", "points": 4, "aliases": ["$52"]},
                ]
            }
        )
        submission = "1. (-6, 13)\n2. slope -21\n3. $52\n"
        self.assertEqual(set(parse_numbered_answers(submission)), {"1", "2", "3"})
        result = GoldAnswerEvaluator(parts=parts, submission_text=submission).evaluate()
        self.assertEqual(result.total_score, 12)
        self.assertEqual(result.max_score, 12)

    def test_parse_team_tokens_and_semicolons(self):
        team = parse_numbered_answers(
            "T-1 135432 T-2 2√10 T-3 32 T-4 49/3"
        )
        self.assertEqual(team["1"], "135432")
        self.assertEqual(team["2"], "2√10")
        self.assertEqual(team["3"], "32")

        semi = parse_numbered_answers(
            "135432; 2sqrt(10); 32; 49/3; (2+sqrt(2),1+sqrt(2))"
        )
        self.assertEqual(semi["1"], "135432")
        self.assertEqual(semi["2"], "2sqrt(10)")
        self.assertEqual(semi["5"], "(2+sqrt(2),1+sqrt(2))")

    def test_semicolon_sheet_scores_against_gold(self):
        parts = load_gold_parts(
            {
                "parts": [
                    {"id": "1", "expected": "135432", "points": 5},
                    {"id": "2", "expected": "2√10", "points": 5, "aliases": ["2sqrt(10)"]},
                    {"id": "3", "expected": "32", "points": 5},
                ]
            }
        )
        submission = "135432; 2sqrt(10); 32"
        result = GoldAnswerEvaluator(parts=parts, submission_text=submission).evaluate()
        self.assertEqual(result.total_score, 15)

    def test_missing_structured_gold_raises(self):
        with self.assertRaises(Exception):
            load_gold_parts({"expected_answer": "only a blob"})


class RegistryAndModeTests(unittest.TestCase):
    def test_registry_dispatch(self):
        slide = resolve_evaluator_spec("business_case")
        self.assertEqual(slide.id, "slide_deck_v1")
        self.assertEqual(strategy_kind(slide), "llm_judge")
        gold = resolve_evaluator_spec("numerical_sheet")
        self.assertEqual(strategy_kind(gold), "gold")
        writing = resolve_evaluator_spec("collaborative_writing_discussion")
        self.assertEqual(writing.id, "rubric_llm_v1")
        with self.assertRaises(RegistryError):
            resolve_evaluator_spec("oral_presentation")

    def test_question_and_competition_packets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = root / "task.pdf"
            write_pdf(pdf, pages=3)
            competition = build_competition_packet(
                competition_id="demo",
                problem_id="demo_1",
                task_type="team_contest",
                source_pdf=pdf,
                work_dir=root / "comp",
                media="images",
            )
            self.assertEqual(competition.mode, "competition")
            self.assertEqual(len(competition.page_image_paths), 3)

            question = build_question_packet(
                competition_id="demo",
                problem_id="demo_1",
                task_type="team_contest",
                question=QuestionSpec(question_id="q2", page_start=2, page_end=2),
                source_pdf=pdf,
                work_dir=root / "q",
                media="images",
            )
            self.assertEqual(question.mode, "question")
            self.assertEqual(len(question.page_image_paths), 1)


from evaluation.models import EvaluationError, load_rubric, scale_rubric
from evaluation.rubric_llm import RubricDocumentEvaluator
from llm import LLMRequest, LLMResponse


class RubricScaleTests(unittest.TestCase):
    def test_scale_rubric(self):
        ensure_default_rubrics()
        rubric = load_rubric(REPO_ROOT / "data/rubrics/numerical_sheet_reference_40_v1.json")
        scaled = scale_rubric(rubric, 50)
        self.assertEqual(scaled.total_points, 50)
        self.assertAlmostEqual(sum(c.max_score for c in scaled.criteria), 50)


class RubricDocumentTests(unittest.TestCase):
    def test_mock_document_judge(self):
        ensure_default_rubrics()
        rubric = load_rubric(REPO_ROOT / "data/rubrics/wsc_writing_28_v1.json")

        def mock_request(request: LLMRequest) -> LLMResponse:
            payload = {
                "criteria": [
                    {
                        "id": c.id,
                        "score": c.max_score / 2,
                        "max_score": c.max_score,
                        "evidence": ["para 1"],
                        "justification": "ok",
                        "confidence": 0.7,
                        "observable": True,
                    }
                    for c in rubric.criteria
                ],
                "total_score": rubric.total_points / 2,
                "max_score": rubric.total_points,
                "warnings": [],
                "limitations": [],
            }
            return LLMResponse(text=json.dumps(payload), provider="mock", model="mock")

        result = RubricDocumentEvaluator(
            request_fn=mock_request,
            rubric=rubric,
            task_text="Write about cooperation.",
            submission_text="Cooperation enables teams to solve harder problems.",
            media="text",
        ).evaluate()
        self.assertEqual(result.total_score, 14)
        self.assertEqual(result.evaluator_id, "rubric_llm_v1")


class FinalizeJudgeTests(unittest.TestCase):
    def test_applies_rubric_when_env_flags_llm_judge(self):
        ensure_default_rubrics()
        problem = {
            "problem_id": "wsc_writing_gq_001",
            "task_type": "collaborative_writing_discussion",
            "problem_description": "Write about cooperation.",
            "evaluation": {
                "evaluator_id": "rubric_llm_v1",
                "status": "ready",
                "rubric_path": "data/rubrics/wsc_writing_28_v1.json",
                "deliverable": "written_essay",
            },
            "gold_label": {"grading_rubric": "Clear thesis."},
        }
        rubric = load_rubric(REPO_ROOT / "data/rubrics/wsc_writing_28_v1.json")

        def mock_request(request: LLMRequest) -> LLMResponse:
            payload = {
                "criteria": [
                    {
                        "id": c.id,
                        "score": c.max_score,
                        "max_score": c.max_score,
                        "evidence": ["line 1"],
                        "justification": "meets criterion",
                        "confidence": 0.9,
                        "observable": True,
                    }
                    for c in rubric.criteria
                ],
                "total_score": rubric.total_points,
                "max_score": rubric.total_points,
                "warnings": [],
                "limitations": [],
            }
            return LLMResponse(text=json.dumps(payload), provider="mock", model="mock")

        quick = {
            "graded": False,
            "method": "llm_judge_required",
            "score": None,
            "max_score": None,
            "reason": "No exact gold answer on file; use LLM or human judge.",
        }
        graded = apply_registered_judge(
            problem,
            "Cooperation enables teams to solve harder problems together.",
            quick,
            request_fn=mock_request,
            work_dir=REPO_ROOT / "results" / "test_finalize_judge",
            repo_root=REPO_ROOT,
        )
        self.assertTrue(graded["graded"])
        self.assertEqual(graded["method"], "rubric_llm_v1")
        self.assertEqual(graded["score"], 28)
        self.assertEqual(graded["max_score"], 28)

    def test_leaves_gold_and_offline_untouched(self):
        gold_grade = {
            "graded": True,
            "method": "gold_substring_match",
            "score": 1.0,
            "max_score": 1.0,
            "correct": True,
        }
        self.assertEqual(
            apply_registered_judge({}, "1. 42", gold_grade, request_fn=None),
            gold_grade,
        )
        pending = {"graded": False, "method": "llm_judge_required", "score": None}
        self.assertEqual(
            apply_registered_judge(
                {"evaluation": {"evaluator_id": "rubric_llm_v1", "status": "ready"}},
                "essay text",
                pending,
                request_fn=None,
            ),
            pending,
        )


if __name__ == "__main__":
    unittest.main()
