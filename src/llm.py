import base64
import io
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from pypdf import PdfReader, PdfWriter

QueryFn = Callable[[str, str], str]


@dataclass(frozen=True)
class LLMAttachment:
    path: Path
    mime_type: str
    role: str = "agent_visible"
    page_start: int | None = None
    page_end: int | None = None


@dataclass(frozen=True)
class LLMRequest:
    system_prompt: str
    user_prompt: str
    attachments: tuple[LLMAttachment, ...] = ()
    purpose: str = "generation"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    usage: dict[str, Any] = field(default_factory=dict)


RequestFn = Callable[[LLMRequest], LLMResponse]


def _attachment_bytes(attachment: LLMAttachment) -> bytes:
    if not attachment.path.is_file():
        raise ValueError(f"Missing LLM attachment: {attachment.path}")
    if attachment.mime_type != "application/pdf" or attachment.page_start is None:
        return attachment.path.read_bytes()

    reader = PdfReader(str(attachment.path))
    start = attachment.page_start
    end = attachment.page_end
    if end is None or start < 1 or end < start or end > len(reader.pages):
        raise ValueError(
            f"Invalid PDF page range {start}-{end} for {attachment.path} "
            f"({len(reader.pages)} pages)"
        )
    writer = PdfWriter()
    for page_index in range(start - 1, end):
        writer.add_page(reader.pages[page_index])
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def _openai_style_content(request: LLMRequest) -> list[dict[str, str]]:
    content: list[dict[str, str]] = [{"type": "input_text", "text": request.user_prompt}]
    for attachment in request.attachments:
        encoded = base64.b64encode(_attachment_bytes(attachment)).decode("ascii")
        if attachment.mime_type == "application/pdf":
            content.append(
                {
                    "type": "input_file",
                    "filename": attachment.path.name,
                    "file_data": f"data:application/pdf;base64,{encoded}",
                }
            )
        elif attachment.mime_type.startswith("image/"):
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:{attachment.mime_type};base64,{encoded}",
                }
            )
        else:
            raise ValueError(f"Unsupported attachment MIME type: {attachment.mime_type}")
    return content


def _response_output_text(data: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                chunks.append(str(content["text"]))
    if chunks:
        return "\n".join(chunks)
    return str(data)


def make_openai_responses_caller(model: str = "gpt-4.1") -> RequestFn:
    """Create a file-capable OpenAI Responses API caller (PDF + images)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY to use direct PDF/image inputs.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    def call(request: LLMRequest) -> LLMResponse:
        response = client.responses.create(
            model=model,
            instructions=request.system_prompt,
            input=[{"role": "user", "content": _openai_style_content(request)}],
        )
        usage = {}
        if getattr(response, "usage", None):
            raw_usage = response.usage
            usage = raw_usage.model_dump() if hasattr(raw_usage, "model_dump") else {}
        return LLMResponse(
            text=response.output_text,
            provider="openai",
            model=model,
            usage=usage,
        )

    return call


def make_perplexity_responses_caller(
    model: str = "openai/gpt-5.4",
) -> RequestFn:
    """Perplexity Agent API caller with multi-image (and optional PDF) attachments.

    Prefer page images for vision models. Native PDF `input_file` support varies by
    backend; rasterize with artifacts.pdf_ingest when in doubt.
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("Set PERPLEXITY_API_KEY to use Perplexity multimodal calls.")

    import requests

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def call(request: LLMRequest, max_retries: int = 3) -> LLMResponse:
        content = _openai_style_content(request)
        # Prepend system guidance into the first text block for Agent API.
        if request.system_prompt.strip():
            content = [
                {
                    "type": "input_text",
                    "text": f"{request.system_prompt.strip()}\n\n{request.user_prompt}",
                },
                *[part for part in content if part.get("type") != "input_text"],
            ]
        payload = {
            "model": model,
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": 16000,
        }
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    "https://api.perplexity.ai/v1/agent",
                    headers=headers,
                    json=payload,
                    timeout=180,
                )
                if not resp.ok:
                    detail = resp.text[:800]
                    raise requests.exceptions.HTTPError(
                        f"{resp.status_code} {resp.reason}: {detail}",
                        response=resp,
                    )
                data = resp.json()
                usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
                return LLMResponse(
                    text=_response_output_text(data),
                    provider="perplexity",
                    model=model,
                    usage=usage,
                )
            except requests.exceptions.SSLError as exc:
                last_error = RuntimeError(
                    "TLS failed talking to api.perplexity.ai (often a huge image "
                    "payload). Re-render pages as smaller JPEGs, or retry with "
                    "--pages 1-1. Original error: "
                    f"{exc}"
                )
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    raise last_error from exc
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    time.sleep(10 * (attempt + 1))
                else:
                    raise
        raise RuntimeError(f"Perplexity multimodal call failed: {last_error}")

    return call


def resolve_request_fn(
    provider: str = "perplexity",
    model: str | None = None,
) -> RequestFn:
    """Factory for multimodal judges/agents."""
    provider = provider.lower().strip()
    if provider in {"perplexity", "pplx"}:
        return make_perplexity_responses_caller(model=model or "openai/gpt-5.4")
    if provider in {"openai", "oai"}:
        return make_openai_responses_caller(model=model or "gpt-4.1")
    raise ValueError(f"Unknown multimodal provider: {provider}")


def bind_attachments(
    request_fn: RequestFn,
    attachments: list[LLMAttachment] | tuple[LLMAttachment, ...],
    *,
    purpose: str = "generation",
) -> QueryFn:
    """Adapt a request-based multimodal caller to existing collaboration code."""
    frozen_attachments = tuple(attachments)

    def call(system_prompt: str, user_prompt: str) -> str:
        return request_fn(
            LLMRequest(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                attachments=frozen_attachments,
                purpose=purpose,
            )
        ).text

    return call


def mock_agent_llm(system_prompt: str, user_prompt: str) -> str:
    """Deterministic mock for offline diagnostics."""
    combined = f"{system_prompt}\n{user_prompt}"

    if (
        "writing the team's official final answer" in combined.lower()
        or "=== final team answer ===" in combined.lower()
    ):
        return (
            "ACTION: submit_final | PAYLOAD: "
            "1. (-6, 13)  2. slope -21  3. $52  4. 5√11  5. 49√3/2"
        )

    if "group leader" in combined.lower() and "compile" in combined.lower():
        return (
            "ACTION: write_scratchpad | PAYLOAD: Compiled team work: problems 1-5 solved.\n"
            "ACTION: submit_final | PAYLOAD: Team answer sheet: 1.(-6,13) 2.-21 3.52 4.5√11 5.49√3/2"
        )

    if "group leader" in combined.lower() and "assign" in combined.lower():
        return "Agent_2 handles problems 1-3. Agent_3 handles problems 4-6. I will synthesize."

    if "your assigned slice" in combined.lower():
        return "ACTION: speak | PAYLOAD: My slice is complete. Key results attached in scratchpad notes."

    if "icpc" in combined.lower() and "allowed_tools" in combined.lower():
        return (
            "ACTION: execute_code | PAYLOAD: print(sum(range(10)))\n"
            "ACTION: speak | PAYLOAD: Code confirms sum 0..9 = 45."
        )

    if "round table" in combined.lower():
        return "ACTION: speak | PAYLOAD: I propose we divide by sub-problem and cross-check arithmetic."

    if "decentralized" in combined.lower():
        return (
            "ACTION: write_scratchpad | PAYLOAD: Node patch: verified approach for problem 7.\n"
            "ACTION: speak | PAYLOAD: Updated scratchpad with probability calculation."
        )

    return "ACTION: speak | PAYLOAD: Let's align on a unified solution approach."


def make_perplexity_caller(
    model: str = "openai/gpt-5.4-mini",
    api: str = "agent",
) -> QueryFn:
    """Build a real LLM caller using PERPLEXITY_API_KEY. Raises if key missing."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("Set PERPLEXITY_API_KEY to use a live LLM caller.")

    import requests

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def call_agent(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        full_input = f"{system_prompt}\n\n{user_prompt}"
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    "https://api.perplexity.ai/v1/agent",
                    headers=headers,
                    json={"model": model, "input": full_input, "max_output_tokens": 16000},
                    timeout=180,
                )
                if not resp.ok:
                    detail = resp.text[:500]
                    raise requests.exceptions.HTTPError(
                        f"{resp.status_code} {resp.reason}: {detail}",
                        response=resp,
                    )
                data = resp.json()
                for item in data.get("output", []):
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            return content["text"]
                return str(data)
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(10 * (attempt + 1))
                else:
                    raise

    def call_sonar(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        for attempt in range(max_retries):
            try:
                r = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return r.choices[0].message.content
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(10 * (attempt + 1))
                else:
                    raise

    if api == "agent":
        return call_agent
    return call_sonar


def resolve_query_fn(
    use_mock: bool = True,
    model: Optional[str] = None,
) -> QueryFn:
    if use_mock:
        return mock_agent_llm
    return make_perplexity_caller(model=model or "openai/gpt-5.4-mini")
