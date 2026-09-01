"""Experimental VJudge web adapter (non-official internal endpoints).

Requires a logged-in browser session cookie. Turnstile / Challenge responses
stop in ``needs_human`` — never auto-solved.

Working submit flows (observed 2026-08-27 / 2026-08-28):

Contest mode:
1. POST /contest/login/{id} with accessCode
2. Read contest HTML for problems[].num and contest version (e.g. \"6c3\")
3. GET /contest/{id}/submitMethods for own-account bindingId when method=1
4. POST /contest/submit/{id}/{num} with source/language/method/open/accessCode/version[/bindingId]

Problem mode (no private contest):
1. Optional bindingId from VJUDGE_BINDING_ID when method=1
2. POST /problem/submit/{OJ}-{probNum} with source/language/method/open[/bindingId]
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from judge.remote import (
    NormalizedVerdict,
    RemoteRun,
    RemoteStatus,
    RemoteSubmitRequest,
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0.0.0 Safari/537.36"
)
DEFAULT_BASE = "https://vjudge.net"

LANGUAGE_IDS: dict[str, str] = {
    "cpp": "54",
    "cpp17": "54",
    "c++": "54",
    "c++17": "54",
    "python": "31",
    "python3": "31",
    "py": "31",
}

STATUS_MAP: list[tuple[re.Pattern[str], NormalizedVerdict, RemoteStatus]] = [
    (re.compile(r"accept", re.I), "AC", "final"),
    (re.compile(r"wrong\s*answer|\bWA\b", re.I), "WA", "final"),
    (re.compile(r"time\s*limit|\bTLE\b", re.I), "TLE", "final"),
    (re.compile(r"memory\s*limit|\bMLE\b", re.I), "MLE", "final"),
    (re.compile(r"output\s*limit|\bOLE\b", re.I), "OLE", "final"),
    (re.compile(r"runtime|segmentation|\bRE\b", re.I), "RE", "final"),
    (re.compile(r"compil", re.I), "CE", "final"),
    (re.compile(r"challenge|turnstile", re.I), "CHALLENGE", "needs_human"),
    (re.compile(r"login\s*fail", re.I), "LOGIN_FAILED", "needs_human"),
    (re.compile(r"submit\s*fail|problem_set_updated|not_found|not_allowed", re.I), "SUBMIT_FAILED", "failed"),
    (re.compile(r"pending|queue|judg|running|process", re.I), "PENDING", "polling"),
]

Opener = Callable[..., Any]
PROBLEM_OBJ_RE = re.compile(
    r'\{\s*"pid"\s*:\s*\d+\s*,\s*"title"\s*:\s*"(?:\\.|[^"\\])*"\s*,\s*"oj"\s*:\s*"(?:\\.|[^"\\])*"\s*,\s*"probNum"\s*:\s*"(?:\\.|[^"\\])*"\s*,\s*"num"\s*:\s*"(?P<num>[A-Z])"',
    re.S,
)
VERSION_RE = re.compile(r'"version"\s*:\s*"(?P<version>[^"]+)"\s*,\s*"started"\s*:')


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def resolve_language_id(language: str) -> str:
    raw = (language or "").strip()
    if raw.isdigit():
        return raw
    key = raw.lower()
    if key in LANGUAGE_IDS:
        env_key = (
            "VJUDGE_LANGUAGE_CPP"
            if key in {"cpp", "cpp17", "c++", "c++17"}
            else "VJUDGE_LANGUAGE_PYTHON"
        )
        return _env(env_key, LANGUAGE_IDS[key])
    raise ValueError(
        f"Unsupported language {language!r}; use cpp17/python3 or a numeric VJudge id."
    )


def problem_num(problem: str) -> str:
    """Contest problem path segment: letter A/B/C (not 0-based index)."""
    text = str(problem or "").strip()
    if not text:
        raise ValueError("problem is required")
    if text.isdigit():
        # Allow numeric only if caller already resolved it; prefer letters.
        return text
    letter = text.upper()
    if len(letter) == 1 and "A" <= letter <= "Z":
        return letter
    raise ValueError(f"Invalid contest problem id {problem!r}; use A/B/C.")


def problem_submit_key(*, oj: str, problem: str) -> str:
    """Build VJudge path key like CodeForces-4A."""
    oj_text = (oj or "CodeForces").strip() or "CodeForces"
    text = str(problem or "").strip()
    if not text:
        raise ValueError("problem is required")
    if "-" in text and text.split("-", 1)[0].lower() == oj_text.lower():
        return text
    # Accept cf_4A / 4A / CodeForces-4A
    cleaned = text
    if cleaned.lower().startswith("cf_"):
        cleaned = cleaned[3:]
    if cleaned.lower().startswith("cf"):
        cleaned = cleaned[2:]
    return f"{oj_text}-{cleaned}"


def normalize_status(text: str) -> tuple[NormalizedVerdict, RemoteStatus]:
    blob = str(text or "").strip() or "UNKNOWN"
    for pattern, verdict, status in STATUS_MAP:
        if pattern.search(blob):
            return verdict, status
    return "UNKNOWN", "polling"


class VJudgeClient:
    """Thin wrapper around VJudge's current web submit/poll endpoints."""

    def __init__(
        self,
        *,
        cookie: str | None = None,
        base_url: str | None = None,
        method: int | None = None,
        access_code: str | None = None,
        opener: Opener = urllib.request.urlopen,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or _env("VJUDGE_BASE_URL", DEFAULT_BASE)).rstrip("/")
        self.cookie = cookie if cookie is not None else _env("VJUDGE_COOKIE")
        if not self.cookie:
            raise ValueError(
                "VJUDGE_COOKIE is required (copy Cookie header from a logged-in browser)."
            )
        self.method = (
            method
            if method is not None
            else int(_env("VJUDGE_SUBMIT_METHOD", "1") or "1")
        )
        self.access_code = (
            access_code if access_code is not None else _env("VJUDGE_ACCESS_CODE")
        )
        self.opener = opener
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        form: bool = True,
        referer: str | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = {
            "User-Agent": UA,
            "Cookie": self.cookie,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": self.base_url,
            "Referer": referer or f"{self.base_url}/",
            "X-Requested-With": "XMLHttpRequest",
        }
        body: bytes | None = None
        if data is not None:
            if form:
                body = urllib.parse.urlencode(data).encode("utf-8")
                headers["Content-Type"] = (
                    "application/x-www-form-urlencoded; charset=UTF-8"
                )
            else:
                body = json.dumps(data).encode("utf-8")
                headers["Content-Type"] = "application/json; charset=UTF-8"
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener(request, timeout=self.timeout) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            if payload.lstrip()[:1] in "{[":
                try:
                    return json.loads(payload)
                except json.JSONDecodeError:
                    pass
            raise RuntimeError(
                f"VJudge HTTP {exc.code} at {path}: {payload[:300]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"VJudge network error: {exc}") from exc

        text = raw.decode("utf-8", errors="replace")
        if "Enable JavaScript and cookies" in text or "cf-browser-verification" in text:
            return RemoteRun(
                run_id="",
                status="needs_human",
                verdict="CHALLENGE",
                message="Cloudflare interstitial; open VJudge in browser and refresh cookie.",
                raw={"html_preview": text[:200]},
            )
        if "application/json" in content_type or text[:1] in "{[":
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return text

    def login_contest(self, contest_id: str) -> RemoteRun | None:
        if not self.access_code:
            return None
        result = self._request(
            "POST",
            f"/contest/login/{urllib.parse.quote(contest_id)}",
            data={"accessCode": self.access_code},
            form=True,
            referer=f"{self.base_url}/contest/{contest_id}",
        )
        if isinstance(result, RemoteRun):
            return result
        return None

    def fetch_contest_meta(self, contest_id: str) -> dict[str, Any] | RemoteRun:
        page = self._request(
            "GET",
            f"/contest/{urllib.parse.quote(contest_id)}",
            referer=f"{self.base_url}/contest/{contest_id}",
        )
        if isinstance(page, RemoteRun):
            return page
        if not isinstance(page, str):
            raise RuntimeError("Unexpected contest page response")
        version_match = VERSION_RE.search(page)
        nums = [m.group("num") for m in PROBLEM_OBJ_RE.finditer(page)]
        return {
            "version": version_match.group("version") if version_match else "",
            "problem_nums": nums,
            "raw_len": len(page),
        }

    def fetch_binding_id(self, contest_id: str, oj_hint: str = "CodeForces") -> str:
        payload = self._request(
            "GET",
            f"/contest/{urllib.parse.quote(contest_id)}/submitMethods",
            referer=f"{self.base_url}/contest/{contest_id}",
        )
        if not isinstance(payload, dict):
            return _env("VJUDGE_BINDING_ID")
        for item in payload.get("myBindings") or []:
            if not isinstance(item, dict):
                continue
            if oj_hint and str(item.get("oj") or "") not in {"", oj_hint}:
                continue
            binding = item.get("bindingId") or item.get("id")
            if binding is not None:
                return str(binding)
        return _env("VJUDGE_BINDING_ID")

    def submit(self, request: RemoteSubmitRequest) -> RemoteRun:
        if str(request.contest_id or "").strip():
            return self._submit_contest(request)
        return self._submit_problem(request)

    def _submit_problem(self, request: RemoteSubmitRequest) -> RemoteRun:
        language_id = resolve_language_id(request.language)
        key = problem_submit_key(oj=request.oj, problem=request.problem)
        referer = f"{self.base_url}/problem/{key}"
        form: dict[str, Any] = {
            "method": str(self.method),
            "language": language_id,
            "open": "1" if request.open_source else "0",
            "source": request.source,
            "token": "",
        }
        if self.method in {1, 2}:
            binding_id = _env("VJUDGE_BINDING_ID")
            if not binding_id:
                # Reuse contest submitMethods as a binding lookup (same OJ account).
                contest_hint = _env("VJUDGE_BINDING_CONTEST_ID") or _env(
                    "VJUDGE_CONTEST_ID"
                )
                if contest_hint:
                    binding_id = self.fetch_binding_id(
                        contest_hint, oj_hint=request.oj or "CodeForces"
                    )
            if binding_id:
                form["bindingId"] = binding_id
        path = f"/problem/submit/{urllib.parse.quote(key, safe='-')}"
        result = self._request("POST", path, data=form, form=True, referer=referer)
        return self._finalize_submit_response(result)

    def _submit_contest(self, request: RemoteSubmitRequest) -> RemoteRun:
        language_id = resolve_language_id(request.language)
        num = problem_num(request.problem)
        contest_id = request.contest_id
        referer = f"{self.base_url}/contest/{contest_id}"

        login_result = self.login_contest(contest_id)
        if isinstance(login_result, RemoteRun):
            return login_result
        meta = self.fetch_contest_meta(contest_id)
        if isinstance(meta, RemoteRun):
            return meta
        version = _env("VJUDGE_CONTEST_VERSION") or str(meta.get("version") or "")
        if not version:
            return RemoteRun(
                run_id="",
                status="failed",
                verdict="SUBMIT_FAILED",
                message="Could not parse contest version; set VJUDGE_CONTEST_VERSION.",
                raw=meta,
            )

        form: dict[str, Any] = {
            "method": str(self.method),
            "language": language_id,
            "open": "1" if request.open_source else "0",
            "source": request.source,
            "accessCode": self.access_code or "",
            "version": version,
            "token": "",
        }
        if self.method in {1, 2}:
            binding_id = self.fetch_binding_id(contest_id)
            if binding_id:
                form["bindingId"] = binding_id

        path = f"/contest/submit/{urllib.parse.quote(contest_id)}/{urllib.parse.quote(num)}"
        result = self._request("POST", path, data=form, form=True, referer=referer)
        return self._finalize_submit_response(result)

    def _finalize_submit_response(self, result: Any) -> RemoteRun:
        if isinstance(result, RemoteRun):
            return result
        run_id = _extract_run_id(result)
        if not run_id:
            message = _extract_message(result) or "Submit response missing run id."
            verdict, status = normalize_status(message)
            if status == "polling":
                status = "failed"
                verdict = "SUBMIT_FAILED"
            return RemoteRun(
                run_id="",
                status=status,
                verdict=verdict,
                message=message,
                raw=_as_dict(result),
            )
        return RemoteRun(
            run_id=str(run_id),
            status="submitted",
            verdict="PENDING",
            message="submitted",
            raw=_as_dict(result),
            poll_url=f"{self.base_url}/solution/data/{run_id}",
        )

    def get_result(self, run_id: str) -> RemoteRun:
        if not run_id:
            return RemoteRun(
                run_id="",
                status="failed",
                verdict="UNKNOWN",
                message="empty run_id",
            )
        result = self._request(
            "POST",
            f"/solution/data/{urllib.parse.quote(run_id)}",
            data={},
            form=True,
        )
        if isinstance(result, RemoteRun):
            result.run_id = run_id
            return result
        payload = _as_dict(result)
        status_text = str(
            payload.get("statusCanonical")
            or payload.get("status")
            or payload.get("statusType")
            or payload.get("result")
            or payload.get("verdict")
            or ""
        )
        # Numeric statusType 0 is Accepted on current VJudge payloads.
        if status_text == "0" or payload.get("statusType") == 0:
            status_text = str(payload.get("statusCanonical") or payload.get("status") or "Accepted")
        if not status_text and isinstance(result, str):
            status_text = result
        if payload.get("processing") is True:
            status_text = status_text or "Pending"
        verdict, status = normalize_status(status_text)
        if payload.get("processing") is False and verdict == "UNKNOWN" and payload.get("status"):
            verdict, status = normalize_status(str(payload.get("status")))

        return RemoteRun(
            run_id=str(run_id),
            status=status,
            verdict=verdict,
            remote_run_id=_stringify(
                payload.get("remoteRunId") or payload.get("remote_run_id")
            ),
            time_ms=_int_or_none(payload.get("runtime") or payload.get("time")),
            memory_kb=_int_or_none(payload.get("memory")),
            message=status_text or "ok",
            raw=payload,
            poll_url=f"{self.base_url}/solution/data/{run_id}",
        )

    def submit_and_poll(
        self,
        request: RemoteSubmitRequest,
        *,
        interval_sec: float = 2.0,
        timeout_sec: float = 120.0,
    ) -> RemoteRun:
        current = self.submit(request)
        if current.status in {"failed", "needs_human"} or not current.run_id:
            return current
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            current = self.get_result(current.run_id)
            if current.status in {"final", "failed", "needs_human"}:
                return current
            time.sleep(interval_sec)
        current.status = "needs_human"
        current.message = (current.message or "") + " (poll timeout)"
        return current


def _extract_run_id(result: Any) -> str | None:
    if isinstance(result, (int, float)):
        return str(int(result))
    if isinstance(result, str):
        text = result.strip()
        if text.isdigit():
            return text
        match = re.search(r"\b(\d{5,})\b", text)
        return match.group(1) if match else None
    if isinstance(result, dict):
        for key in ("runId", "run_id", "id", "data"):
            if key in result and result[key] is not None:
                found = _extract_run_id(result[key])
                if found:
                    return found
    return None


def _extract_message(result: Any) -> str:
    if isinstance(result, str):
        return result[:500]
    if isinstance(result, dict):
        err = result.get("error")
        if isinstance(err, dict):
            key = err.get("i18nKey") or err.get("message") or err.get("msg")
            if key:
                return str(key)[:500]
        for key in ("errMsg", "error", "message", "msg", "status"):
            if result.get(key):
                return str(result[key])[:500]
    return ""


def _as_dict(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return dict(result)
    return {"value": result}


def _stringify(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value).replace("ms", "").replace("KB", "").strip()))
    except (TypeError, ValueError):
        return None


# Back-compat alias used by early tests.
problem_index = problem_num
