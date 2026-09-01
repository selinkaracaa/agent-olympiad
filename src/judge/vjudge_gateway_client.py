"""HTTP client for the local VJudge gateway (used by agent env)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def gateway_enabled() -> bool:
    return bool((os.environ.get("VJUDGE_GATEWAY_URL") or "").strip())


def gateway_base() -> str:
    return (os.environ.get("VJUDGE_GATEWAY_URL") or "").rstrip("/")


def submit_via_gateway(
    *,
    problem: str,
    language: str,
    source: str,
    contest_id: str = "",
    oj: str = "CodeForces",
    idempotency_key: str = "",
    poll: bool = True,
    timeout: float = 180.0,
) -> dict[str, Any]:
    base = gateway_base()
    if not base:
        raise RuntimeError("VJUDGE_GATEWAY_URL is not set")
    payload = {
        "contest_id": contest_id,
        "oj": oj,
        "problem": problem,
        "language": language,
        "source": source,
        "idempotency_key": idempotency_key,
        "poll": poll,
    }
    request = urllib.request.Request(
        f"{base}/v1/submit",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"status": "failed", "error": body or str(exc)}
    except urllib.error.URLError as exc:
        return {
            "status": "failed",
            "error": f"gateway unreachable at {base}: {exc}",
            "message": "Start: python src/vjudge_gateway.py serve",
        }


def extract_source_and_language(submission: str, fallback: str = "python3") -> tuple[str, str]:
    text = submission or ""
    fence = None
    if "```" in text:
        import re

        fence = re.search(
            r"```(?P<language>python|py|python3|cpp|c\+\+|cpp17|c\+\+17)?\s*\n(?P<source>.*?)```",
            text,
            re.IGNORECASE | re.DOTALL,
        )
    if fence:
        language = (fence.group("language") or fallback).lower()
        if language in {"cpp", "c++", "cpp17", "c++17"}:
            language = "cpp17"
        else:
            language = "python3"
        return fence.group("source").strip(), language
    return text.strip(), infer_remote_language(text, fallback=fallback)


def infer_remote_language(source: str, fallback: str = "python3") -> str:
    text = source.lstrip()
    if text.startswith("```"):
        first = text.split("\n", 1)[0].lower()
        if "cpp" in first or "c++" in first:
            return "cpp17"
        if "python" in first or first.endswith("py"):
            return "python3"
    if "#include" in source or "using namespace std" in source or "int main" in source:
        return "cpp17"
    return fallback
