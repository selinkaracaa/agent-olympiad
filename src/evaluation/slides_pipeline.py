"""Shared slide-deck evaluation pipeline used by all CLIs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from artifacts import Asset, normalize_submission
from artifacts.assets import file_sha256
from artifacts.slides import NormalizedSubmission
from llm import RequestFn, resolve_request_fn

from .models import Rubric, load_rubric
from .slides import MediaAttach, SlideDeckEvaluator

REPO_ROOT = Path(__file__).resolve().parents[2]


def parse_page_range(value: str | None, page_count: int) -> tuple[int, int]:
    if not value:
        return 1, page_count
    try:
        start_text, end_text = value.split("-", 1)
        start, end = int(start_text), int(end_text)
    except (ValueError, AttributeError) as exc:
        raise ValueError("Page range must look like START-END, e.g. 3-12.") from exc
    if start < 1 or end < start or end > page_count:
        raise ValueError(f"Invalid page range {start}-{end} for {page_count}-page PDF.")
    return start, end


def build_task_asset(task_pdf: Path, pages: str | None = None) -> Asset:
    path = Path(task_pdf).resolve()
    if not path.is_file() or path.read_bytes()[:5] != b"%PDF-":
        raise ValueError(f"Task input is not a readable PDF: {path}")
    page_count = len(PdfReader(str(path)).pages)
    page_start, page_end = parse_page_range(pages, page_count)
    return Asset(
        path=path,
        mime_type="application/pdf",
        role="agent_visible",
        page_start=page_start,
        page_end=page_end,
        sha256=file_sha256(path),
    )


def resolve_problem_task_pdf(problem: dict[str, Any], repo_root: Path | None = None) -> Path | None:
    """Resolve the official case PDF from benchmark problem metadata."""
    root = Path(repo_root) if repo_root else REPO_ROOT
    for asset in problem.get("assets") or []:
        path_text = str(asset.get("path") or "")
        if asset.get("role") == "agent_visible" and path_text.endswith(".pdf"):
            path = Path(path_text)
            return path if path.is_absolute() else root / path
    source = problem.get("source_file")
    if source:
        path = Path(str(source))
        return path if path.is_absolute() else root / path
    return None


def choose_slide_media(provider: str, media: str) -> MediaAttach:
    provider = provider.lower()
    if media in {"images", "both"}:
        return "images"
    if provider in {"perplexity", "pplx"} and media == "pdf":
        raise ValueError(
            "Perplexity expects --media images (PDF→page images). "
            "Use --provider openai for native PDF attachments."
        )
    return "pdf"


@dataclass
class SlideEvalResult:
    task_asset: Asset
    submission: NormalizedSubmission
    rubric: Rubric
    evaluation: Any
    payload: dict[str, Any]


def evaluate_slide_deck(
    *,
    task_pdf: Path,
    submission: Path,
    rubric: Path | Rubric,
    work_dir: Path,
    provider: str = "perplexity",
    model: str | None = None,
    media: str = "images",
    task_pages: str | None = None,
    task_label: str = "presentation task",
    min_slides: int = 1,
    max_slides: int = 20,
    max_file_size_mb: int = 20,
    request_fn: RequestFn | None = None,
    extra_payload: dict[str, Any] | None = None,
) -> SlideEvalResult:
    """Normalize an HTML/PDF deck and score it with SlideDeckEvaluator."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    attach_media = choose_slide_media(provider, media)
    task_asset = build_task_asset(task_pdf, task_pages)
    rubric_obj = rubric if isinstance(rubric, Rubric) else load_rubric(Path(rubric).resolve())
    normalized = normalize_submission(
        Path(submission),
        work_dir / "submission",
        min_slides=min_slides,
        max_slides=max_slides,
        max_file_size_mb=max_file_size_mb,
    )
    if not normalized.validation.valid:
        raise ValueError(
            "Submission validation failed: " + "; ".join(normalized.validation.errors)
        )

    caller = request_fn or resolve_request_fn(provider=provider, model=model)
    evaluation = SlideDeckEvaluator(
        request_fn=caller,
        task_asset=task_asset,
        submission=normalized,
        rubric=rubric_obj,
        task_label=task_label,
        media=attach_media,
        image_work_dir=work_dir / "judge_pages",
    ).evaluate()

    payload = {
        "evaluator_id": "slide_deck_v1",
        "provider": provider,
        "media": attach_media,
        "task_pdf": str(task_asset.path),
        "task_page_range": [task_asset.page_start, task_asset.page_end],
        "task_pdf_sha256": task_asset.sha256,
        "rubric": rubric_obj.rubric_id,
        "submission_source": str(Path(submission).resolve()),
        "submission_sha256": file_sha256(normalized.pdf_path),
        "normalized_pdf": str(normalized.pdf_path),
        "evaluation": evaluation.to_dict(),
    }
    if extra_payload:
        payload.update(extra_payload)
    return SlideEvalResult(
        task_asset=task_asset,
        submission=normalized,
        rubric=rubric_obj,
        evaluation=evaluation,
        payload=payload,
    )
