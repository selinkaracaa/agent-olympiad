"""HTTP client for the local VJudge gateway (used by agent env)."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
import uuid
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
    # A stable child key makes a repeated client call reuse the same quota retry.
    attempt_key = idempotency_key or uuid.uuid4().hex
    payload = {
        "contest_id": contest_id,
        "oj": oj,
        "problem": problem,
        "language": language,
        "source": source,
        "idempotency_key": attempt_key,
        "poll": poll,
    }
    retries = []
    for attempt in range(2):
        result = _post_submission(base, payload, timeout)
        delay = _quota_retry_delay(result, oj)
        if attempt or delay is None:
            return {**result, "quota_retries": retries} if retries else result
        retries.append({"gateway_run_id": result.get("gateway_run_id"),
                        "idempotency_key": payload["idempotency_key"],
                        "message": result.get("message"), "wait_seconds": delay})
        # The judge explicitly rejected this request before assigning a run ID.
        # Network errors and any response with a remote ID never enter this path.
        remaining = delay
        while remaining > 0:
            pause = min(60, remaining)
            time.sleep(pause)
            remaining -= pause
        payload = {**payload, "idempotency_key": attempt_key + ":quota-retry-1"}


def _quota_retry_delay(result: dict[str, Any], oj: str) -> int | None:
    if (oj.strip().lower() != "kattis" or result.get("status") != "failed"
            or result.get("verdict") != "SUBMIT_FAILED"
            or any(result.get(key) for key in ("run_id", "remote_run_id", "vjudge_run_id"))):
        return None
    match = re.search(r"You are out of submission tokens\.\s*Your next token will regenerate in (\d+) seconds?\.",
                      str(result.get("message") or ""), re.IGNORECASE)
    if match and int(match.group(1)) <= 120:
        return int(match.group(1)) + 1
    return None


def _post_submission(base: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
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
