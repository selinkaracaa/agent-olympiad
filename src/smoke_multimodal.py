"""Smoke-test PDF → page images → Perplexity multi-image reading.

Usage:
  export PERPLEXITY_API_KEY=pplx-...
  python3 src/smoke_multimodal.py data/raw/business_case/2024.pdf --pages 1-2
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from artifacts.pdf_ingest import parse_pdf
from llm import LLMAttachment, LLMRequest, resolve_request_fn


def parse_pages(value: str | None) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    start_text, end_text = value.split("-", 1)
    return int(start_text), int(end_text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", default="1-2", help="Inclusive range, e.g. 1-3")
    parser.add_argument("--provider", default="perplexity", choices=["perplexity", "openai"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--media", default="images", choices=["images", "both"])
    args = parser.parse_args()

    page_start, page_end = parse_pages(args.pages)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    work_dir = REPO_ROOT / "results" / "smoke_multimodal" / timestamp
    parsed = parse_pdf(
        args.pdf.resolve(),
        work_dir / "pages",
        media=args.media,
        page_start=page_start,
        page_end=page_end,
        max_pages=6,
    )
    if not parsed.page_images:
        raise SystemExit("No page images rendered; cannot smoke-test vision.")

    request_fn = resolve_request_fn(provider=args.provider, model=args.model)
    attachments = tuple(
        LLMAttachment(path=image.path, mime_type=image.mime_type, role="agent_visible")
        for image in parsed.page_images
    )
    prompt = (
        f"You are given {len(attachments)} page image(s) from a contest PDF "
        f"(pages {parsed.page_start}-{parsed.effective_page_end}). "
        "Briefly list: (1) contest/task type if visible, (2) any diagrams/figures, "
        "(3) the first concrete instruction or question you can read. "
        "Keep the answer under 120 words."
    )
    if parsed.text:
        prompt += "\n\nExtracted text (may be incomplete):\n" + parsed.text[:1500]

    response = request_fn(
        LLMRequest(
            system_prompt="You are a careful multimodal reader for olympiad PDFs.",
            user_prompt=prompt,
            attachments=attachments,
            purpose="smoke_test",
        )
    )
    payload = {
        "pdf": str(args.pdf.resolve()),
        "provider": response.provider,
        "model": response.model,
        "pages": [parsed.page_start, parsed.effective_page_end],
        "image_paths": [str(image.path.relative_to(REPO_ROOT)) for image in parsed.page_images],
        "warnings": parsed.warnings,
        "response": response.text,
        "usage": response.usage,
    }
    out = work_dir / "smoke.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(response.text)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
