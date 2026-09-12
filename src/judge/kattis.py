"""Direct Kattis submission provider using a home-directory .kattisrc token."""

from __future__ import annotations

import configparser
import re
import time
from pathlib import Path
from typing import Any

import requests

from judge.remote import RemoteRun, RemoteSubmitRequest

_STATUS_VERDICTS = {
    6: "SUBMIT_FAILED",
    7: "SUBMIT_FAILED",
    8: "CE",
    9: "RE",
    10: "MLE",
    11: "OLE",
    12: "TLE",
    13: "RE",
    14: "WA",
    16: "AC",
}


class KattisClient:
    """Authenticate, submit, and poll through Kattis' script endpoints."""

    def __init__(
        self,
        *,
        config: configparser.ConfigParser | None = None,
        config_path: str | Path | None = None,
        session: Any | None = None,
        timeout: float = 10.0,
        min_submit_interval: float = 2.0,
    ) -> None:
        self.config = config or self._load_config(config_path)
        self.session = session or requests.Session()
        self.timeout = timeout
        self.min_submit_interval = max(0.0, min_submit_interval)
        self.headers = {"User-Agent": "agent-olympiad-kattis/1.0"}
        self._logged_in = False
        self._last_submit_at = 0.0

    @staticmethod
    def _load_config(path: str | Path | None) -> configparser.ConfigParser:
        config_path = Path(path) if path else Path.home() / ".kattisrc"
        cfg = configparser.ConfigParser()
        if not cfg.read(config_path, encoding="utf-8"):
            raise ValueError(f"Kattis config not found: {config_path}")
        for section, keys in {
            "user": ("username", "token"),
            "kattis": ("hostname", "loginurl", "submissionurl", "submissionsurl"),
        }.items():
            if not cfg.has_section(section):
                raise ValueError(f"Kattis config is missing [{section}]")
            for key in keys:
                if not cfg.get(section, key, fallback="").strip():
                    raise ValueError(f"Kattis config is missing {section}.{key}")
        return cfg

    @staticmethod
    def _language(language: str) -> tuple[str, str]:
        key = (language or "").strip().lower()
        if key in {"python", "python3", "py"}:
            return "Python 3", "main.py"
        if key in {"cpp", "cpp17", "c++", "c++17"}:
            return "C++", "main.cpp"
        raise ValueError(f"Unsupported Kattis language: {language!r}")

    def _login(self) -> None:
        if self._logged_in:
            return
        response = self.session.post(
            self.config["kattis"]["loginurl"],
            data={
                "user": self.config["user"]["username"],
                "token": self.config["user"]["token"],
                "script": "true",
            },
            headers=self.headers,
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Kattis login failed with HTTP {response.status_code}")
        self._logged_in = True

    def submit(self, request: RemoteSubmitRequest) -> RemoteRun:
        try:
            self._login()
            language, filename = self._language(request.language)
            wait = self.min_submit_interval - (
                time.monotonic() - self._last_submit_at
            )
            if wait > 0:
                time.sleep(wait)
            response = self.session.post(
                self.config["kattis"]["submissionurl"],
                data={
                    "submit": "true",
                    "submit_ctr": 2,
                    "language": language,
                    "mainclass": filename,
                    "problem": request.problem,
                    "tag": "",
                    "script": "true",
                },
                files={
                    "sub_file[]": (
                        filename,
                        request.source.encode("utf-8"),
                        "application/octet-stream",
                    )
                },
                headers=self.headers,
                timeout=self.timeout,
            )
            self._last_submit_at = time.monotonic()
            if response.status_code != 200:
                raise RuntimeError(
                    f"Kattis submission failed with HTTP {response.status_code}"
                )
            match = re.search(r"Submission ID:\s*(\d+)", response.text)
            if match is None:
                response_summary = re.sub(r"<[^>]+>", " ", response.text)
                response_summary = " ".join(response_summary.split())[:300]
                detail = (
                    f": {response_summary}"
                    if response_summary
                    else " (empty response)"
                )
                raise RuntimeError(
                    "Kattis response did not include a submission ID" + detail
                )
            run_id = match.group(1)
            return RemoteRun(
                run_id=run_id,
                status="submitted",
                verdict="PENDING",
                message="submitted",
                poll_url=f"{self.config['kattis']['submissionsurl']}/{run_id}",
            )
        except Exception as exc:
            return RemoteRun(
                run_id="",
                status="failed",
                verdict="SUBMIT_FAILED",
                message=str(exc),
            )

    def get_result(self, run_id: str) -> RemoteRun:
        try:
            self._login()
            url = f"{self.config['kattis']['submissionsurl']}/{run_id}"
            response = self.session.get(
                f"{url}?json",
                headers=self.headers,
                timeout=self.timeout,
            )
            if response.status_code != 200:
                raise RuntimeError(f"Kattis polling failed with HTTP {response.status_code}")
            payload = response.json()
            status_id = int(payload.get("status_id", 0))
            verdict = _STATUS_VERDICTS.get(status_id, "PENDING")
            terminal = status_id in _STATUS_VERDICTS
            return RemoteRun(
                run_id=run_id,
                status="final" if terminal else "polling",
                verdict=verdict,
                message=verdict,
                raw={"status_id": status_id},
                poll_url=url,
            )
        except Exception as exc:
            return RemoteRun(
                run_id=run_id,
                status="failed",
                verdict="SUBMIT_FAILED",
                message=str(exc),
            )

    def submit_and_poll(
        self,
        request: RemoteSubmitRequest,
        *,
        interval_sec: float = 2.0,
        timeout_sec: float = 180.0,
    ) -> RemoteRun:
        result = self.submit(request)
        if result.status != "submitted":
            return result
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            result = self.get_result(result.run_id)
            if result.status in {"final", "failed", "needs_human"}:
                return result
            time.sleep(interval_sec)
        return RemoteRun(
            run_id=result.run_id,
            status="polling",
            verdict="PENDING",
            message="Kattis polling timed out",
            poll_url=result.poll_url,
        )
