import base64
import io
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Optional

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
class LLMToolCall:
    name: str
    arguments: dict[str, Any]
    call_id: str = ""


@dataclass(frozen=True)
class LLMRequest:
    system_prompt: str
    user_prompt: str
    attachments: tuple[LLMAttachment, ...] = ()
    purpose: str = "generation"
    metadata: dict[str, Any] = field(default_factory=dict)
    tools: tuple[dict[str, Any], ...] = ()
    tool_choice: Literal["auto", "required", "none"] = "auto"


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    usage: dict[str, Any] = field(default_factory=dict)
    tool_calls: tuple[LLMToolCall, ...] = ()


RequestFn = Callable[[LLMRequest], LLMResponse]

ActionTransport = Literal["native", "emulated", "prompt_json"]


@dataclass(frozen=True)
class ProviderCapabilities:
    """Provider features that affect how agent actions are transported."""

    native_tools: bool = False
    emulated_tools: bool = False
    json_schema: bool = False
    token_usage: bool = False
    attachments: bool = False

    @property
    def action_transport(self) -> ActionTransport:
        if self.native_tools:
            return "native"
        if self.emulated_tools:
            return "emulated"
        return "prompt_json"


_PROVIDER_CAPABILITIES: dict[str, ProviderCapabilities] = {
    "perplexity": ProviderCapabilities(
        native_tools=True,
        token_usage=True,
        attachments=True,
    ),
    "pplx": ProviderCapabilities(
        native_tools=True,
        token_usage=True,
        attachments=True,
    ),
    "openai": ProviderCapabilities(
        native_tools=True,
        token_usage=True,
        attachments=True,
    ),
    "oai": ProviderCapabilities(
        native_tools=True,
        token_usage=True,
        attachments=True,
    ),
    # Tinker 0.26 exposes plain sampling but no tools/JSON-schema parameter.
    # Its adapter therefore renders the same schemas into the prompt, validates
    # the sampled call, and performs bounded repair attempts.
    "tinker": ProviderCapabilities(emulated_tools=True),
    "tml": ProviderCapabilities(emulated_tools=True),
}


def provider_capabilities(provider: str) -> ProviderCapabilities:
    """Return explicit capabilities instead of branching on provider names."""
    return _PROVIDER_CAPABILITIES.get(
        provider.lower().strip(),
        ProviderCapabilities(),
    )


def provider_action_transport(provider: str) -> ActionTransport:
    return provider_capabilities(provider).action_transport


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
    if any(item.get("type") == "function_call" for item in data.get("output", [])):
        return ""
    return str(data)


def parse_response_tool_calls(data: dict[str, Any]) -> tuple[LLMToolCall, ...]:
    """Parse provider responses using the OpenAI Responses function-call shape."""
    calls: list[LLMToolCall] = []
    for item in data.get("output", []):
        if item.get("type") != "function_call":
            continue
        raw_arguments = item.get("arguments", {})
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError as exc:
                raise ValueError("Function-call arguments are not valid JSON.") from exc
        else:
            arguments = raw_arguments
        if not isinstance(arguments, dict):
            raise ValueError("Function-call arguments must decode to an object.")
        name = str(item.get("name") or "").strip()
        if not name:
            raise ValueError("Function call is missing its name.")
        calls.append(
            LLMToolCall(
                name=name,
                arguments=arguments,
                call_id=str(item.get("call_id") or item.get("id") or ""),
            )
        )
    return tuple(calls)


def make_openai_responses_caller(model: str = "gpt-4.1", *, max_output_tokens: int = 8192) -> RequestFn:
    """Create a file-capable OpenAI Responses API caller (PDF + images)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY to use direct PDF/image inputs.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    def call(request: LLMRequest) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "instructions": request.system_prompt,
            "max_output_tokens": max_output_tokens,
            "input": [{"role": "user", "content": _openai_style_content(request)}],
        }
        if request.tools:
            kwargs["tools"] = list(request.tools)
            kwargs["tool_choice"] = request.tool_choice
        response = client.responses.create(
            **kwargs,
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
            tool_calls=parse_response_tool_calls(response.model_dump()),
        )

    return call


def make_perplexity_responses_caller(
    model: str = "openai/gpt-5.4",
    *,
    max_output_tokens: int = 16000,
    temperature: float = 0.2,
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

    def call(request: LLMRequest, max_retries: int = 5) -> LLMResponse:
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
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        }
        if request.tools:
            payload["tools"] = list(request.tools)
            payload["tool_choice"] = request.tool_choice
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    "https://api.perplexity.ai/v1/agent",
                    headers=headers,
                    json=payload,
                    timeout=300,
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
                    tool_calls=parse_response_tool_calls(data),
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
                    time.sleep(15 * (attempt + 1))
                else:
                    raise
        raise RuntimeError(f"Perplexity multimodal call failed: {last_error}")

    return call


def _json_objects(text: str) -> list[Any]:
    """Decode JSON values embedded in fences or provider-specific tags."""
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.replace("<tool_call>", "").replace("</tool_call>", "")
    decoder = json.JSONDecoder()
    values: list[Any] = []
    for index, char in enumerate(cleaned):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        values.append(value)
    return values


def _coerce_emulated_tool_call(text: str) -> LLMToolCall:
    """Parse common JSON tool-call shapes emitted by open-weight models."""
    values = _json_objects(text)
    if not values:
        raise ValueError("response contains no JSON tool-call object")
    value = values[0]
    if isinstance(value, list):
        if len(value) != 1:
            raise ValueError("response must contain exactly one tool call")
        value = value[0]
    if not isinstance(value, dict):
        raise ValueError("tool call must be a JSON object")
    function = value.get("function")
    if isinstance(function, dict):
        value = function
    name = value.get("name", value.get("action"))
    arguments = value.get("arguments", value.get("parameters"))
    if not isinstance(name, str) or not name.strip():
        raise ValueError("tool call is missing a string name")
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise ValueError("tool-call arguments are not valid JSON") from exc
    if not isinstance(arguments, dict):
        raise ValueError("tool-call arguments must be a JSON object")
    return LLMToolCall(name=name.strip(), arguments=arguments)


_JSON_TYPES: dict[str, type[Any] | tuple[type[Any], ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


def _validate_emulated_tool_call(
    call: LLMToolCall,
    tools: tuple[dict[str, Any], ...],
) -> str | None:
    """Validate one emulated call against the provider-neutral tool schemas."""
    by_name = {str(tool.get("name") or ""): tool for tool in tools}
    tool = by_name.get(call.name)
    if tool is None:
        return (
            f"tool {call.name!r} is unavailable; choose exactly one of "
            f"{sorted(name for name in by_name if name)}"
        )
    schema = tool.get("parameters") or {}
    properties = schema.get("properties") or {}
    required = set(schema.get("required") or ())
    missing = sorted(required - set(call.arguments))
    if missing:
        return f"tool {call.name!r} is missing required arguments {missing}"
    if schema.get("additionalProperties") is False:
        extras = sorted(set(call.arguments) - set(properties))
        if extras:
            return f"tool {call.name!r} has unknown arguments {extras}"
    for name, value in call.arguments.items():
        field = properties.get(name)
        if not isinstance(field, dict):
            continue
        expected = _JSON_TYPES.get(str(field.get("type") or ""))
        if expected is not None and (
            not isinstance(value, expected)
            or field.get("type") == "integer"
            and isinstance(value, bool)
        ):
            return (
                f"argument {name!r} for tool {call.name!r} must be "
                f"{field.get('type')}"
            )
        enum = field.get("enum")
        if isinstance(enum, list) and enum and value not in enum:
            return f"argument {name!r} must be one of {enum}"
        items = field.get("items")
        if field.get("type") == "array" and isinstance(items, dict):
            if not value:
                return f"argument {name!r} must contain at least one item"
            item_enum = items.get("enum")
            if isinstance(item_enum, list) and item_enum and any(
                item not in item_enum for item in value
            ):
                return f"argument {name!r} items must be one of {item_enum}"
    return None


def _tinker_tool_prompt(tools: tuple[dict[str, Any], ...]) -> str:
    compact_tools = [
        {
            "name": tool.get("name"),
            "description": tool.get("description"),
            "parameters": tool.get("parameters"),
        }
        for tool in tools
    ]
    return (
        "\n\nTOOL-CALL TRANSPORT CONTRACT\n"
        "Choose exactly one function from the schemas below. Return only one "
        'JSON object shaped as {"name":"function_name","arguments":{...}}. '
        "Do not use Markdown, prose, XML, or additional calls. Enum values are "
        "strict: copy one exactly as shown.\n"
        f"FUNCTION SCHEMAS:\n{json.dumps(compact_tools, ensure_ascii=False)}"
    )


def make_tinker_request_fn(
    model: str,
    *,
    max_output_tokens: int = 8192,
    temperature: float = 0.2,
    max_tool_retries: int = 2,
) -> RequestFn:
    """Adapt Tinker sampling to the provider-neutral request/tool interface."""
    if max_tool_retries < 0:
        raise ValueError("max_tool_retries must be non-negative")
    caller = make_tinker_caller(
        model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )

    def call(request: LLMRequest) -> LLMResponse:
        if not request.tools or request.tool_choice == "none":
            text = caller(request.system_prompt, request.user_prompt)
            return LLMResponse(
                text=text,
                provider="tinker",
                model=model,
                usage={
                    "output_tokens": max(1, len(text) // 4),
                    "api_calls": 1,
                    "action_transport": "prompt_json",
                },
            )

        system = request.system_prompt + _tinker_tool_prompt(request.tools)
        user = request.user_prompt
        output_tokens = 0
        last_text = ""
        last_error = "unknown tool-call error"
        requested_attempts = request.metadata.get("max_transport_attempts")
        attempts = max_tool_retries + 1
        if isinstance(requested_attempts, int):
            attempts = max(1, min(attempts, requested_attempts))
        for attempt in range(attempts):
            last_text = caller(system, user)
            output_tokens += max(1, len(last_text) // 4)
            try:
                tool_call = _coerce_emulated_tool_call(last_text)
                error = _validate_emulated_tool_call(tool_call, request.tools)
                if error:
                    raise ValueError(error)
            except ValueError as exc:
                last_error = str(exc)
                if attempt >= max_tool_retries:
                    break
                user = (
                    f"{request.user_prompt}\n\n"
                    "YOUR PREVIOUS TOOL CALL WAS INVALID\n"
                    f"Error: {last_error}\n"
                    f"Invalid output: {last_text[:1200]}\n"
                    "Return one corrected JSON tool-call object only."
                )
                continue
            return LLMResponse(
                text="",
                provider="tinker",
                model=model,
                usage={
                    "output_tokens": output_tokens,
                    "api_calls": attempt + 1,
                    "tool_retries": attempt,
                    "action_transport": "emulated",
                },
                tool_calls=(
                    LLMToolCall(
                        name=tool_call.name,
                        arguments=tool_call.arguments,
                        call_id=f"tinker-emulated-{attempt + 1}",
                    ),
                ),
            )
        return LLMResponse(
            text=last_text,
            provider="tinker",
            model=model,
            usage={
                "output_tokens": output_tokens,
                "api_calls": attempts,
                "tool_retries": attempts - 1,
                "tool_error": last_error,
                "action_transport": "emulated",
            },
        )

    return call


def resolve_request_fn(
    provider: str = "perplexity",
    model: str | None = None,
    *,
    max_output_tokens: int = 8192,
    temperature: float = 0.2,
) -> RequestFn:
    """Factory for multimodal judges/agents."""
    provider = provider.lower().strip()
    if provider in {"perplexity", "pplx"}:
        return make_perplexity_responses_caller(
            model=model or "openai/gpt-5.4",
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
    if provider in {"openai", "oai"}:
        return make_openai_responses_caller(model=model or "gpt-4.1", max_output_tokens=max_output_tokens)
    if provider in {"tinker", "tml"}:
        resolved_model = (
            model or os.environ.get("TINKER_MODEL") or "Qwen/Qwen3.6-35B-A3B"
        )
        return make_tinker_request_fn(
            resolved_model,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
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

    if "you are coach" in system_prompt.lower() and "pre-contest brief" in system_prompt.lower():
        return (
            "ACTION: speak | PAYLOAD: Triage first, assign independent checks, "
            "and reserve the final quarter for integration and verification."
        )

    if "you are coach" in system_prompt.lower() and "opening discussion" in system_prompt.lower():
        return (
            "ACTION: speak | PAYLOAD: Follow the opening assignments, publish "
            "checkpoints, and escalate disagreements early. I am now exiting."
        )

    if "synthesize" in combined.lower() or "final team answer" in combined.lower():
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

    if (
        "codeforces" in combined.lower()
        or "cf_4a" in combined.lower()
        or (
            "algorithmic_programming" in combined.lower()
            and "submit_code" in combined.lower()
        )
    ):
        solution = (
            "n = int(input())\n"
            'print("YES" if n % 2 == 0 and n > 2 else "NO")\n'
        )
        return (
            "ACTION: execute_code | PAYLOAD: "
            + solution
            + "ACTION: submit_code | PAYLOAD: "
            + solution
            + "ACTION: submit_final | PAYLOAD: "
            + solution
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
    max_output_tokens: int = 16000,
) -> QueryFn:
    """Build a real LLM caller using PERPLEXITY_API_KEY. Raises if key missing."""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("Set PERPLEXITY_API_KEY to use a live LLM caller.")

    import requests

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def call_agent(system_prompt: str, user_prompt: str, max_retries: int = 5) -> str:
        full_input = f"{system_prompt}\n\n{user_prompt}"
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    "https://api.perplexity.ai/v1/agent",
                    headers=headers,
                    json={"model": model, "input": full_input, "max_output_tokens": max_output_tokens},
                    timeout=300,
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
                    time.sleep(15 * (attempt + 1))
                else:
                    raise

    def call_sonar(system_prompt: str, user_prompt: str, max_retries: int = 5) -> str:
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


def _safe_api_error(exc: Exception) -> str:
    message = str(exc)
    for name in ("TINKER_API_KEY", "PERPLEXITY_API_KEY", "OPENAI_API_KEY"):
        secret = os.environ.get(name)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    message = re.sub(
        r"(?i)(authorization[\"']?\s*[:=]\s*[\"']?bearer\s+)\S+",
        r"\1[REDACTED]",
        message,
    )
    return f"{type(exc).__name__}: {message}"


def _normalize_tinker_api_key(raw: str) -> str:
    """Accept bare ``tml-...`` keys or ``tinker:tml-...`` credential files."""
    key = str(raw or "").strip()
    if key.lower().startswith("tinker:"):
        key = key.split(":", 1)[1].strip()
    match = re.search(r"(tml-[A-Za-z0-9_-]+)", key)
    if match:
        return match.group(1)
    return key


def make_tinker_caller(
    model: str,
    max_output_tokens: int = 8192,
    temperature: float = 0.2,
) -> QueryFn:
    """Build a native Tinker sampling caller with lazy per-caller resources."""
    api_key = _normalize_tinker_api_key(os.environ.get("TINKER_API_KEY", ""))
    if not api_key:
        raise ValueError("Set TINKER_API_KEY to use the Tinker provider.")
    os.environ["TINKER_API_KEY"] = api_key
    if not model or not model.strip():
        raise ValueError("Set --model or TINKER_MODEL to select a Tinker model.")
    if max_output_tokens <= 0:
        raise ValueError("max_output_tokens must be positive.")
    if temperature < 0:
        raise ValueError("temperature must be non-negative.")

    try:
        import tinker
    except ImportError as exc:
        raise RuntimeError(
            "The Tinker SDK is unavailable. Install the 'tinker' package."
        ) from exc

    client = None
    tokenizer = None
    transient_errors = tuple(
        error_type
        for name in (
            "APIConnectionError",
            "APITimeoutError",
            "RateLimitError",
            "InternalServerError",
            "RequestFailedError",
            "SidecarDiedError",
        )
        if isinstance((error_type := getattr(tinker, name, None)), type)
    )

    def resources():
        nonlocal client, tokenizer
        if client is None or tokenizer is None:
            try:
                new_client = tinker.ServiceClient().create_sampling_client(
                    base_model=model
                )
                new_tokenizer = new_client.get_tokenizer()
            except Exception as exc:
                raise RuntimeError(
                    f"Tinker client initialization failed: {_safe_api_error(exc)}"
                ) from exc
            client, tokenizer = new_client, new_tokenizer
        return client, tokenizer

    def call(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        sampling_client, sampling_tokenizer = resources()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            encoded = sampling_tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            input_ids = encoded["input_ids"] if hasattr(encoded, "keys") else encoded
            prompt = tinker.ModelInput.from_ints(input_ids)
            sampling_params = tinker.SamplingParams(
                max_tokens=max_output_tokens,
                temperature=temperature,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Tinker prompt preparation failed: {_safe_api_error(exc)}"
            ) from exc

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = sampling_client.sample(
                    prompt,
                    num_samples=1,
                    sampling_params=sampling_params,
                ).result()
                break
            except transient_errors as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
            except Exception as exc:
                raise RuntimeError(
                    f"Tinker sampling failed: {_safe_api_error(exc)}"
                ) from exc
        else:
            raise RuntimeError(
                f"Tinker sampling failed after {max_retries} attempts: "
                f"{_safe_api_error(last_error or RuntimeError('unknown error'))}"
            ) from last_error

        if not response.sequences:
            raise RuntimeError("Tinker returned no sampled sequences.")
        sequence = response.sequences[0]
        try:
            text = sampling_tokenizer.decode(
                sequence.tokens, skip_special_tokens=True
            ).strip()
        except Exception as exc:
            raise RuntimeError(
                f"Tinker decode failed: {_safe_api_error(exc)}"
            ) from exc
        if not isinstance(text, str) or not text.strip():
            stop_reason = getattr(sequence, "stop_reason", None)
            raise RuntimeError(
                f"Tinker returned an empty decoded completion "
                f"(stop_reason={stop_reason!r})."
            )
        return text

    return call


def resolve_query_fn(
    use_mock: bool = True,
    model: Optional[str] = None,
) -> QueryFn:
    if use_mock:
        return mock_agent_llm
    return make_perplexity_caller(model=model or "openai/gpt-5.4-mini")


_AGENT_ROLE_RE = re.compile(r"^You are ([A-Za-z0-9_]+)\b", re.MULTILINE)


def make_roster_caller(
    models_by_agent: dict[str, str],
    *,
    default_model: str,
    api: str = "agent",
    max_output_tokens: int = 16000,
) -> QueryFn:
    """Route each agent call to a model based on the system-prompt role line.

    Collaboration prompts start with ``You are Agent_1 ...`` / ``You are Solo ...``.
    Missing agents fall back to ``default_model``.
    """
    callers: dict[str, QueryFn] = {}
    models = {**models_by_agent}
    models.setdefault("__default__", default_model)

    def _caller_for(model: str) -> QueryFn:
        if model not in callers:
            callers[model] = make_perplexity_caller(
                model=model, api=api, max_output_tokens=max_output_tokens
            )
        return callers[model]

    def call(system_prompt: str, user_prompt: str) -> str:
        match = _AGENT_ROLE_RE.search(system_prompt or "")
        agent = match.group(1) if match else None
        model = models.get(agent) if agent else None
        model = model or models["__default__"]
        return _caller_for(model)(system_prompt, user_prompt)

    return call
