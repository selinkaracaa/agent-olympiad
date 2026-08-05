from __future__ import annotations

import json
from pathlib import Path

from .models import ProblemAsset
from .src_bridge import ensure_src_imports

ensure_src_imports()

from artifacts.pdf_ingest import parse_pdf  # noqa: E402
from llm import (  # noqa: E402
    LLMAttachment,
    LLMRequest,
    LLMResponse,
    QueryFn,
    RequestFn,
    bind_attachments,
    resolve_request_fn,
)


def make_request_caller(
    provider: str,
    model: str,
    *,
    base_url: str | None = None,
) -> RequestFn:
    return resolve_request_fn(
        provider=provider,
        model=model,
        base_url=base_url,
    )


def build_agent_attachments(
    assets: tuple[ProblemAsset, ...],
    *,
    media: str,
    work_dir: Path,
) -> tuple[LLMAttachment, ...]:
    if media == "text":
        return ()
    attachments: list[LLMAttachment] = []
    for index, asset in enumerate(assets):
        if asset.mime_type == "application/pdf" and media in {"images", "both"}:
            parsed = parse_pdf(
                asset.path,
                work_dir / f"asset_{index}",
                media="images",
                page_start=asset.page_start,
                page_end=asset.page_end,
                max_pages=40,
                stem=f"asset_{index}",
            )
            attachments.extend(
                LLMAttachment(
                    path=image.path,
                    mime_type=image.mime_type,
                    role="agent_visible",
                )
                for image in parsed.page_images
            )
        elif asset.mime_type == "application/pdf" or asset.mime_type.startswith("image/"):
            attachments.append(
                LLMAttachment(
                    path=asset.path,
                    mime_type=asset.mime_type,
                    role="agent_visible",
                    page_start=asset.page_start,
                    page_end=asset.page_end,
                )
            )
    return tuple(attachments)


def bind_problem_assets(
    request_fn: RequestFn,
    assets: tuple[ProblemAsset, ...],
    *,
    media: str,
    work_dir: Path,
) -> QueryFn:
    return bind_attachments(
        request_fn,
        build_agent_attachments(assets, media=media, work_dir=work_dir),
        purpose="competition_solving",
    )


def mock_query(system: str, user: str) -> str:
    combined = f"{system}\n{user}".lower()
    if "team formation" in combined:
        return json.dumps(
            {
                "team_size": 4,
                "members": [
                    {"name": "Agent_1", "role": "captain and synthesizer"},
                    {"name": "Agent_2", "role": "primary solver"},
                    {"name": "Agent_3", "role": "independent verifier"},
                    {"name": "Agent_4", "role": "notation and completeness checker"},
                ],
            }
        )
    if "return only valid json" in combined and "normalized_score" in combined:
        return json.dumps(
            {
                "raw_score": 62,
                "max_score": 100,
                "normalized_score": 62,
                "breakdown": [{"criterion": "mock rubric", "score": 62, "max_score": 100}],
                "feedback": "Mock judge score for offline pipeline verification.",
            }
        )
    if "official final answer" in combined:
        return "1. Mock synthesized solution with reasoning from the team."
    system_lower = system.lower()
    if "you are agent_1," in system_lower:
        return "ACTION: query_rules | PAYLOAD: What tools and team constraints apply?"
    if "you are agent_2," in system_lower:
        return "ACTION: write_scratchpad | PAYLOAD: Draft analysis: identify correspondences and test each mapping."
    if "you are agent_3," in system_lower:
        return "ACTION: speak | PAYLOAD: I will independently verify the proposed linguistic mappings."
    return "ACTION: skip | PAYLOAD: No additional contribution this round."


def mock_request(request: LLMRequest) -> LLMResponse:
    marker = "REQUIRED JSON SHAPE:"
    if marker in request.user_prompt:
        schema_text = request.user_prompt.rsplit(marker, 1)[1].strip()
        schema = json.loads(schema_text)
        criteria = []
        for item in schema["criteria"]:
            maximum = float(item["max_score"])
            criteria.append(
                {
                    "id": item["id"],
                    "score": maximum * 0.62,
                    "max_score": maximum,
                    "evidence": ["mock submission evidence"],
                    "justification": "Mock rubric score for offline verification.",
                    "confidence": 0.8,
                    "observable": bool(item.get("observable", True)),
                }
            )
        payload = {
            "criteria": criteria,
            "total_score": sum(item["score"] for item in criteria),
            "max_score": sum(item["max_score"] for item in criteria),
            "warnings": [],
            "limitations": ["Mock evaluation; not a real benchmark score."],
        }
        text = json.dumps(payload)
    else:
        text = mock_query(request.system_prompt, request.user_prompt)
    return LLMResponse(text=text, provider="mock", model="mock")
