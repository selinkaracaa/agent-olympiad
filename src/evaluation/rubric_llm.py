"""Generic structured-rubric LLM judge for document-style deliverables.

Covers essays, collaborative writing, proof/power packets, memorials, and
worked-answer contests where deterministic gold parts are unavailable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from artifacts.assets import Asset
from artifacts.pdf_ingest import parse_pdf
from llm import LLMAttachment, LLMRequest, RequestFn

from .models import EvaluationError, EvaluationResult, Rubric, parse_evaluation_payload

MediaAttach = Literal["text", "pdf", "images"]


@dataclass
class RubricDocumentEvaluator:
    request_fn: RequestFn
    rubric: Rubric
    task_text: str = ""
    task_asset: Asset | None = None
    submission_text: str = ""
    submission_pdf: Path | None = None
    reference_text: str = ""
    media: MediaAttach = "text"
    image_work_dir: Path | None = None
    evaluator_id: str = "rubric_llm_v1"
    evaluator_version: str = "1.0.0"
    prompt_version: str = "rubric_document_v1"
    task_label: str = "contest task"
    deliverable_label: str = "team submission"

    def _system_prompt(self) -> str:
        return (
            "You are an expert olympiad grader. Score the submission against the "
            "structured rubric and the official task. Be strict, evidence-grounded, "
            "and do not invent content that is not present in the submission."
        )

    def _user_prompt(self) -> str:
        schema = {
            "criteria": [
                {
                    "id": criterion.id,
                    "score": "number",
                    "max_score": criterion.max_score,
                    "evidence": ["concrete quote or location in the submission"],
                    "justification": "2-4 sentences",
                    "confidence": "number from 0 to 1",
                    "observable": criterion.observable,
                }
                for criterion in self.rubric.criteria
            ],
            "total_score": "sum of criterion scores",
            "max_score": self.rubric.total_points,
            "warnings": ["scoring warning"],
            "limitations": ["what cannot be judged from this submission"],
        }
        sections = [
            f"TASK LABEL: {self.task_label}",
            f"DELIVERABLE: {self.deliverable_label}",
            "STRUCTURED RUBRIC:",
            json.dumps(self.rubric.as_prompt_dict(), indent=2),
        ]
        if self.task_text.strip():
            sections.extend(["TASK TEXT:", self.task_text.strip()[:12000]])
        if self.reference_text.strip():
            sections.extend(
                [
                    "OFFICIAL REFERENCE / MARKING NOTES (judge-only):",
                    self.reference_text.strip()[:12000],
                ]
            )
        if self.submission_text.strip():
            sections.extend(["SUBMISSION TEXT:", self.submission_text.strip()[:16000]])
        if self.media in {"pdf", "images"}:
            sections.append(
                "Additional task/submission files or page images are attached. "
                "Use them as the primary evidence when present."
            )
        sections.extend(
            [
                "SCORING RULES:",
                "- Score only the submission; use the task as context.",
                "- Use official reference notes when provided, but do not require "
                "verbatim wording if the mathematics/argument is equivalent.",
                "- Cite concrete evidence for every criterion.",
                "- Use each exact criterion id and maximum from the rubric.",
                "- total_score must equal the sum of criterion scores.",
                "- Return JSON only, with no Markdown fence or commentary.",
                "REQUIRED JSON SHAPE:",
                json.dumps(schema, indent=2),
            ]
        )
        return "\n\n".join(sections)

    def _attachments(self) -> tuple[LLMAttachment, ...]:
        if self.media == "text":
            return ()
        attachments: list[LLMAttachment] = []
        if self.media == "pdf":
            if self.task_asset is not None:
                attachments.append(
                    LLMAttachment(
                        path=self.task_asset.path,
                        mime_type=self.task_asset.mime_type,
                        role=self.task_asset.role,
                        page_start=self.task_asset.page_start,
                        page_end=self.task_asset.page_end,
                    )
                )
            if self.submission_pdf is not None:
                attachments.append(
                    LLMAttachment(
                        path=self.submission_pdf,
                        mime_type="application/pdf",
                        role="judge_only",
                    )
                )
            return tuple(attachments)

        work = Path(self.image_work_dir or Path("results") / "rubric_judge_pages")
        if self.task_asset is not None:
            task_pages = parse_pdf(
                self.task_asset.path,
                work / "task",
                media="images",
                page_start=self.task_asset.page_start,
                page_end=self.task_asset.page_end,
                stem="task",
            )
            for image in task_pages.page_images:
                attachments.append(
                    LLMAttachment(path=image.path, mime_type=image.mime_type, role="agent_visible")
                )
        if self.submission_pdf is not None:
            sub_pages = parse_pdf(
                self.submission_pdf,
                work / "submission",
                media="images",
                stem="submission",
            )
            for image in sub_pages.page_images:
                attachments.append(
                    LLMAttachment(path=image.path, mime_type=image.mime_type, role="judge_only")
                )
        self.prompt_version = "rubric_document_images_v1"
        return tuple(attachments)

    def evaluate(self) -> EvaluationResult:
        if (
            not self.submission_text.strip()
            and self.submission_pdf is None
            and self.media == "text"
        ):
            raise EvaluationError("RubricDocumentEvaluator needs submission text or PDF.")
        response = self.request_fn(
            LLMRequest(
                system_prompt=self._system_prompt(),
                user_prompt=self._user_prompt(),
                attachments=self._attachments(),
                purpose="evaluation",
                metadata={
                    "evaluator_id": self.evaluator_id,
                    "rubric_id": self.rubric.rubric_id,
                    "media": self.media,
                },
            )
        )
        result = parse_evaluation_payload(
            response.text,
            rubric=self.rubric,
            evaluator_id=self.evaluator_id,
            evaluator_version=self.evaluator_version,
            prompt_version=self.prompt_version,
            model=response.model,
            usage=response.usage,
        )
        for limitation in self.rubric.not_observable_from_deck:
            if limitation not in result.limitations:
                result.limitations.append(limitation)
        return result
