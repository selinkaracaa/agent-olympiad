"""Run a PDF-first agent team, generate HTML slides, render, and evaluate them.

Uses the same slide_deck_v1 pipeline as evaluate_artifact / evaluate_submission.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from artifacts import normalize_submission
from artifacts.assets import file_sha256
from evaluation.slides_pipeline import (
    build_task_asset,
    evaluate_slide_deck,
    resolve_problem_task_pdf,
)
from llm import LLMAttachment, LLMRequest, RequestFn, resolve_request_fn

REPO_ROOT = Path(__file__).resolve().parent.parent

TEAM_SYSTEM = """You are one member of a team solving a presentation task.
The original task PDF is attached. Work from that PDF, not an extracted paraphrase.
Contribute new analysis, calculations, evidence, criticism, or coordination.
Read the team discussion carefully and do not repeat completed work."""

SYNTHESIS_SYSTEM = """You are the final slide editor for a team presentation.
The original task PDF is attached. Return one complete self-contained HTML document only.
Do not wrap it in a Markdown code fence."""


def discussion_text(messages: list[dict]) -> str:
    if not messages:
        return "(No discussion yet.)"
    return "\n\n".join(
        f"[Agent {message['agent_id']} — Round {message['round']}]\n{message['content']}"
        for message in messages
    )


def strip_html_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:html)?\s*", "", stripped, count=1, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped, count=1)
    return stripped.strip()


def attachments_for_provider(
    provider: str, task_asset, work_dir: Path
) -> tuple[LLMAttachment, ...]:
    """Perplexity gets page images; OpenAI can take the PDF directly."""
    if provider in {"perplexity", "pplx"}:
        from artifacts.pdf_ingest import parse_pdf

        parsed = parse_pdf(
            task_asset.path,
            work_dir / "agent_pages",
            media="images",
            page_start=task_asset.page_start,
            page_end=task_asset.page_end,
            stem="task",
            max_pages=12,
        )
        return tuple(
            LLMAttachment(path=image.path, mime_type=image.mime_type, role="agent_visible")
            for image in parsed.page_images
        )
    return (
        LLMAttachment(
            path=task_asset.path,
            mime_type=task_asset.mime_type,
            role=task_asset.role,
            page_start=task_asset.page_start,
            page_end=task_asset.page_end,
        ),
    )


def run_team(
    request_fn: RequestFn,
    attachments: tuple[LLMAttachment, ...],
    *,
    team_size: int,
    rounds: int,
    min_slides: int,
    max_slides: int,
) -> tuple[list[dict], str]:
    messages: list[dict] = []
    for round_number in range(1, rounds + 1):
        for agent_id in range(1, team_size + 1):
            prompt = f"""TEAM DISCUSSION:
{discussion_text(messages)}

YOUR TURN:
You are Agent {agent_id}, round {round_number}/{rounds}. What is your contribution?"""
            response = request_fn(
                LLMRequest(
                    system_prompt=TEAM_SYSTEM,
                    user_prompt=prompt,
                    attachments=attachments,
                    purpose="collaboration",
                    metadata={"agent_id": agent_id, "round": round_number},
                )
            )
            messages.append(
                {
                    "agent_id": agent_id,
                    "round": round_number,
                    "content": response.text,
                    "model": response.model,
                    "usage": response.usage,
                }
            )
            print(f"Round {round_number}/{rounds}, Agent {agent_id}/{team_size}: done")

    synthesis_prompt = f"""FULL TEAM DISCUSSION:
{discussion_text(messages)}

FINAL DELIVERABLE:
Create a complete {min_slides}–{max_slides} slide deck that answers the attached task.

HTML CONTRACT:
- Full HTML document with inline CSS only.
- One <section> per 16:9 slide; each section has an h1 or h2 title.
- Use strong visual hierarchy and concise text.
- Inline SVG charts and diagrams are allowed and encouraged.
- Put speaker notes in <aside class="speaker-notes">.
- No scripts, external URLs/assets, video, audio, iframe, or animation.
- Follow every required deliverable and constraint stated in the task PDF.
"""
    final_response = request_fn(
        LLMRequest(
            system_prompt=SYNTHESIS_SYSTEM,
            user_prompt=synthesis_prompt,
            attachments=attachments,
            purpose="synthesis",
        )
    )
    return messages, strip_html_fence(final_response.text)


def load_problem(benchmark: Path, problem_id: str) -> dict:
    data = json.loads(benchmark.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("problems") or []
    for item in items:
        if item.get("problem_id") == problem_id:
            return item
    raise SystemExit(f"problem_id {problem_id!r} not found in {benchmark}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=None)
    parser.add_argument("--problem-id", default=None)
    parser.add_argument("--task-pdf", type=Path, default=None)
    parser.add_argument("--rubric", type=Path, default=None)
    parser.add_argument("--task-pages", default=None, help="Inclusive range, e.g. 1-10")
    parser.add_argument("--task-label", default="presentation task")
    parser.add_argument("--team-size", type=int, default=5)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--min-slides", type=int, default=10)
    parser.add_argument("--max-slides", type=int, default=15)
    parser.add_argument("--max-file-size-mb", type=int, default=20)
    parser.add_argument(
        "--provider",
        default=os.environ.get("EVALUATOR_PROVIDER", "perplexity"),
        choices=["perplexity", "openai"],
    )
    parser.add_argument("--agent-model", default=os.environ.get("AGENT_MODEL"))
    parser.add_argument("--judge-model", default=os.environ.get("EVALUATOR_MODEL"))
    parser.add_argument("--media", default="images", choices=["pdf", "images"])
    args = parser.parse_args()

    problem = None
    if args.benchmark and args.problem_id:
        problem = load_problem(args.benchmark.resolve(), args.problem_id)
        evaluation = problem.get("evaluation") or {}
        if evaluation.get("evaluator_id") not in {None, "slide_deck_v1"}:
            raise SystemExit(
                f"{args.problem_id} is not a slide_deck_v1 problem "
                f"(got {evaluation.get('evaluator_id')})."
            )
        if not args.rubric and evaluation.get("rubric_path"):
            args.rubric = REPO_ROOT / evaluation["rubric_path"]
        if not args.task_pdf:
            args.task_pdf = resolve_problem_task_pdf(problem, REPO_ROOT)
        args.team_size = args.team_size or int(problem.get("team_size") or 5)
        if args.task_label == "presentation task":
            args.task_label = problem.get("topic") or "business case"

    if not args.task_pdf or not args.rubric:
        raise SystemExit("Need --task-pdf and --rubric (or --benchmark/--problem-id).")

    task_asset = build_task_asset(args.task_pdf, args.task_pages)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = (
        REPO_ROOT
        / "results"
        / "presentation_artifacts"
        / f"{task_asset.path.stem}_{stamp}"
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    agent_fn = resolve_request_fn(provider=args.provider, model=args.agent_model)
    attachments = attachments_for_provider(args.provider, task_asset, run_dir)

    messages, html = run_team(
        agent_fn,
        attachments,
        team_size=args.team_size,
        rounds=args.rounds,
        min_slides=args.min_slides,
        max_slides=args.max_slides,
    )
    html_path = run_dir / "slides.html"
    html_path.write_text(html, encoding="utf-8")

    # Validate/render once so failures surface before the judge call.
    normalized = normalize_submission(
        html_path,
        run_dir,
        min_slides=args.min_slides,
        max_slides=args.max_slides,
        max_file_size_mb=args.max_file_size_mb,
    )
    if not normalized.validation.valid:
        raise ValueError(
            "Generated deck failed validation: " + "; ".join(normalized.validation.errors)
        )

    slide_result = evaluate_slide_deck(
        task_pdf=args.task_pdf,
        submission=html_path,
        rubric=args.rubric,
        work_dir=run_dir / "evaluation",
        provider=args.provider,
        model=args.judge_model,
        media=args.media,
        task_pages=args.task_pages,
        task_label=args.task_label,
        min_slides=args.min_slides,
        max_slides=args.max_slides,
        max_file_size_mb=args.max_file_size_mb,
        extra_payload={
            "problem_id": args.problem_id,
            "benchmark": str(args.benchmark) if args.benchmark else None,
            "agent_model": args.agent_model,
            "judge_model": args.judge_model,
            "team_size": args.team_size,
            "rounds": args.rounds,
        },
    )
    result = {
        **slide_result.payload,
        "discussion": messages,
        "artifacts": {
            "html": str(html_path.relative_to(REPO_ROOT)),
            "pdf": str(normalized.pdf_path.relative_to(REPO_ROOT)),
        },
        "submission_pdf_sha256": file_sha256(normalized.pdf_path),
    }
    try:
        result["normalized_pdf"] = str(normalized.pdf_path.relative_to(REPO_ROOT))
    except ValueError:
        pass

    result_path = run_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[slide_deck_v1] Score: {slide_result.evaluation.total_score:g}/{slide_result.evaluation.max_score:g}")
    print(f"Saved: {result_path}")


if __name__ == "__main__":
    main()
