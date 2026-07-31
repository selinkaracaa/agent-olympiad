"""Question-level vs competition-level evaluation packets.

Question-level: feed one independent item (or page slice) at a time.
Competition-level: full contest packet under shared time/compute pressure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from artifacts.pdf_ingest import MediaMode, ParsedPdf, parse_pdf, slice_pdf

EvalMode = Literal["question", "competition"]


@dataclass(frozen=True)
class QuestionSpec:
    """One independently scorable item inside a contest."""

    question_id: str
    prompt_text: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    max_points: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalPacket:
    """Normalized inputs for agents and judges."""

    mode: EvalMode
    competition_id: str
    problem_id: str
    task_type: str
    media: MediaMode
    source_pdf: Path | None
    parsed: ParsedPdf | None
    question: QuestionSpec | None = None
    questions: tuple[QuestionSpec, ...] = ()
    text_fallback: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def agent_text(self) -> str:
        if self.parsed and self.parsed.text:
            return self.parsed.text
        return self.text_fallback

    @property
    def page_image_paths(self) -> list[Path]:
        if not self.parsed:
            return []
        return [image.path for image in self.parsed.page_images]


def build_competition_packet(
    *,
    competition_id: str,
    problem_id: str,
    task_type: str,
    source_pdf: Path | None,
    work_dir: Path,
    media: MediaMode = "both",
    text_fallback: str = "",
    page_start: int | None = None,
    page_end: int | None = None,
    max_pages: int | None = 20,
    questions: list[QuestionSpec] | tuple[QuestionSpec, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> EvalPacket:
    parsed = None
    if source_pdf is not None:
        parsed = parse_pdf(
            source_pdf,
            work_dir / "input_pages",
            media=media,
            page_start=page_start,
            page_end=page_end,
            max_pages=max_pages,
            stem=f"{problem_id}_p",
        )
    elif media in {"images", "both"}:
        raise ValueError("competition mode with images requires source_pdf.")

    return EvalPacket(
        mode="competition",
        competition_id=competition_id,
        problem_id=problem_id,
        task_type=task_type,
        media=media,
        source_pdf=Path(source_pdf).resolve() if source_pdf else None,
        parsed=parsed,
        questions=tuple(questions),
        text_fallback=text_fallback,
        metadata=dict(metadata or {}),
    )


def build_question_packet(
    *,
    competition_id: str,
    problem_id: str,
    task_type: str,
    question: QuestionSpec,
    source_pdf: Path | None,
    work_dir: Path,
    media: MediaMode = "both",
    text_fallback: str = "",
    max_pages: int | None = 10,
    metadata: dict[str, Any] | None = None,
) -> EvalPacket:
    """Build a single-question packet, optionally slicing the source PDF."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    parsed = None
    active_pdf = Path(source_pdf).resolve() if source_pdf else None

    if active_pdf is not None and question.page_start is not None:
        page_end = question.page_end or question.page_start
        sliced = work_dir / f"{problem_id}_{question.question_id}.pdf"
        active_pdf = slice_pdf(
            active_pdf,
            sliced,
            page_start=question.page_start,
            page_end=page_end,
        )
        parsed = parse_pdf(
            active_pdf,
            work_dir / "input_pages",
            media=media,
            max_pages=max_pages,
            stem=f"{problem_id}_{question.question_id}_p",
        )
    elif active_pdf is not None:
        parsed = parse_pdf(
            active_pdf,
            work_dir / "input_pages",
            media=media,
            max_pages=max_pages,
            stem=f"{problem_id}_{question.question_id}_p",
        )
    elif media in {"images", "both"}:
        raise ValueError("question mode with images requires source_pdf.")

    prompt = question.prompt_text or (parsed.text if parsed else text_fallback)
    return EvalPacket(
        mode="question",
        competition_id=competition_id,
        problem_id=problem_id,
        task_type=task_type,
        media=media,
        source_pdf=active_pdf,
        parsed=parsed,
        question=question,
        questions=(question,),
        text_fallback=prompt,
        metadata=dict(metadata or {}),
    )
