"""Offline-first Codeforces problem adapter for local judging.

Fetches public problem metadata and statement samples, materializes an
``ao.icpc-package/v1`` bundle, and loads it through the consolidated judge.
Hidden tests are never downloaded from Codeforces; add ``tests/secret/`` manually
if you have an authorized bundle.
"""

from __future__ import annotations

import html
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from judge.models import JudgeError
    from judge.package import load_problem_package
    from problem_package_writer import SampleCase, write_problem_package as _write_problem_package
except ImportError:  # pragma: no cover
    from src.judge.models import JudgeError
    from src.judge.package import load_problem_package
    from src.problem_package_writer import (
        SampleCase,
        write_problem_package as _write_problem_package,
    )

REPO_ROOT = Path(__file__).resolve().parents[1]
UA = "agent-olympiad-codeforces-adapter/1.0 (research; local judging)"
PROBLEM_ID_RE = re.compile(r"^(\d+)([A-Z]\d?)$", re.IGNORECASE)
API_URL = "https://codeforces.com/api/problemset.problems"
INPUT_BLOCK_RE = re.compile(
    r'<div class="input">\s*<div class="title">Input</div>\s*<pre>(.*?)</pre>',
    re.IGNORECASE | re.DOTALL,
)
OUTPUT_BLOCK_RE = re.compile(
    r'<div class="output">\s*<div class="title">Output</div>\s*<pre>(.*?)</pre>',
    re.IGNORECASE | re.DOTALL,
)
TIME_LIMIT_RE = re.compile(
    r"time limit per test[^<]*</div>\s*<div[^>]*>([^<]+)",
    re.IGNORECASE | re.DOTALL,
)
MEMORY_LIMIT_RE = re.compile(
    r"memory limit per test[^<]*</div>\s*<div[^>]*>([^<]+)",
    re.IGNORECASE | re.DOTALL,
)
TIME_FALLBACK_RE = re.compile(
    r"time limit.*?(\d+(?:\.\d+)?)\s*seconds?",
    re.IGNORECASE | re.DOTALL,
)
MEMORY_FALLBACK_RE = re.compile(
    r"memory limit.*?(\d+)\s*megabytes?",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class CodeforcesProblemRef:
    problem_id: str
    contest_id: int
    index: str

    @property
    def canonical_id(self) -> str:
        return f"{self.contest_id}{self.index}"

    @property
    def problemset_url(self) -> str:
        return f"https://codeforces.com/problemset/problem/{self.contest_id}/{self.index}"

    @property
    def contest_url(self) -> str:
        return f"https://codeforces.com/contest/{self.contest_id}/problem/{self.index}"


def parse_problem_id(raw: str) -> CodeforcesProblemRef:
    text = str(raw or "").strip().upper().replace("_", "").replace("-", "")
    if text.startswith("CF"):
        text = text[2:]
    match = PROBLEM_ID_RE.fullmatch(text)
    if not match:
        raise ValueError(
            f"Invalid Codeforces problem id {raw!r}; expected forms like 4A or 1900A."
        )
    contest_id = int(match.group(1))
    index = match.group(2).upper()
    return CodeforcesProblemRef(
        problem_id=f"cf_{contest_id}{index}",
        contest_id=contest_id,
        index=index,
    )


def _normalize_pre(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\r\n", "\n").replace("\r", "\n")
    return text.strip("\n")


def extract_samples_from_html(page_html: str) -> list[SampleCase]:
    inputs = [_normalize_pre(match) for match in INPUT_BLOCK_RE.findall(page_html)]
    outputs = [_normalize_pre(match) for match in OUTPUT_BLOCK_RE.findall(page_html)]
    if not inputs or len(inputs) != len(outputs):
        raise JudgeError(
            "Could not parse paired Codeforces sample tests from problem HTML."
        )
    return [
        SampleCase(name=f"{index:02d}", input_text=stdin, output_text=stdout)
        for index, (stdin, stdout) in enumerate(zip(inputs, outputs), start=1)
    ]


def _parse_limit_value(raw: str) -> float:
    cleaned = html.unescape(raw).strip().lower()
    match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    if not match:
        raise JudgeError(f"Could not parse limit value from {raw!r}.")
    return float(match.group(1))


def extract_limits_from_html(page_html: str) -> tuple[int, int]:
    time_match = TIME_LIMIT_RE.search(page_html) or TIME_FALLBACK_RE.search(page_html)
    memory_match = MEMORY_LIMIT_RE.search(page_html) or MEMORY_FALLBACK_RE.search(
        page_html
    )
    if not time_match or not memory_match:
        raise JudgeError("Could not parse Codeforces time/memory limits from HTML.")
    time_seconds = _parse_limit_value(time_match.group(1))
    memory_mb = int(_parse_limit_value(memory_match.group(1)))
    return max(1, round(time_seconds * 1000)), max(1, memory_mb)


def fetch_problem_html(ref: CodeforcesProblemRef, *, timeout: float = 30.0) -> str:
    request = Request(ref.problemset_url, headers={"User-Agent": UA})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"Failed to fetch Codeforces problem page for {ref.canonical_id}: {exc}"
        ) from exc
    return payload.decode("utf-8", errors="replace")


def fetch_problem_metadata(ref: CodeforcesProblemRef, *, timeout: float = 30.0) -> dict[str, Any]:
    request = Request(API_URL, headers={"User-Agent": UA})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Failed to fetch Codeforces API metadata for {ref.canonical_id}: {exc}"
        ) from exc
    if payload.get("status") != "OK":
        raise RuntimeError(payload.get("comment", "Codeforces API error"))
    problems = payload.get("result", {}).get("problems", [])
    for item in problems:
        if int(item.get("contestId", -1)) == ref.contest_id and str(
            item.get("index", "")
        ).upper() == ref.index:
            return dict(item)
    raise RuntimeError(
        f"Problem {ref.canonical_id} not found in Codeforces problemset API."
    )


def package_dir_for(ref: CodeforcesProblemRef, repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / "data" / "benchmarks" / "codeforces" / "packages" / ref.canonical_id


def benchmark_path(repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / "data" / "benchmarks" / "codeforces" / "benchmark.json"


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb",
        dir=path.parent,
        delete=False,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _atomic_write_text(path: Path, text: str) -> None:
    _atomic_write_bytes(path, text.encode("utf-8"))


def write_problem_package(
    ref: CodeforcesProblemRef,
    *,
    samples: list[SampleCase],
    time_ms: int,
    memory_mb: int,
    output_kb: int = 1024,
    destination: Path,
    metadata: dict[str, Any] | None = None,
    statement_html: str | None = None,
    include_secret_group: bool = False,
) -> Path:
    if not samples:
        raise JudgeError("At least one public sample is required to build a package.")

    root = _write_problem_package(
        problem_id=ref.problem_id,
        destination=destination,
        samples=samples,
        time_ms=time_ms,
        memory_mb=memory_mb,
        output_kb=output_kb,
        source="codeforces",
        extra_manifest={
            "codeforces_id": ref.canonical_id,
            "contest_id": ref.contest_id,
            "problem_index": ref.index,
        },
        include_secret_group=include_secret_group,
        grading_scope_labels={
            "sample": "codeforces-public-sample",
            "secret": "authorized-local-secret",
        },
    )
    if metadata is not None:
        _atomic_write_text(
            root / "metadata.json", json.dumps(metadata, indent=2) + "\n"
        )
    if statement_html is not None:
        _atomic_write_text(root / "statement.html", statement_html)
    return root


def load_codeforces_package(package_dir: str | Path):
    return load_problem_package(package_dir)


def build_benchmark_record(
    ref: CodeforcesProblemRef,
    *,
    metadata: dict[str, Any],
    samples: list[SampleCase],
    time_ms: int,
    memory_mb: int,
    package_path: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    rel_package = package_path.resolve().relative_to(root.resolve()).as_posix()
    tags = [str(tag) for tag in metadata.get("tags", [])]
    return {
        "problem_id": ref.problem_id,
        "competition": "Codeforces",
        "competition_id": "codeforces",
        "year": None,
        "codeforces_id": ref.canonical_id,
        "contest_id": ref.contest_id,
        "problem_index": ref.index,
        "title": str(metadata.get("name") or ref.canonical_id),
        "task_type": "algorithmic_programming",
        "team_size": 1,
        "rating": metadata.get("rating"),
        "tags": tags,
        "source_url": ref.problemset_url,
        "problem_description": (
            f"Codeforces problem {ref.canonical_id}. "
            "Statement is cached locally in the generated package. "
            "Judging uses public samples by default; mount authorized secret tests "
            "under tests/secret/ for full local reproduction."
        ),
        "gold_label": {
            "expected_answer": None,
            "grading_rubric": (
                "Local trusted judge over ao.icpc-package/v1 bundles. "
                "Sample scope uses public statement tests only."
            ),
            "human_baseline": None,
        },
        "status": "collected",
        "time_limit_ms": time_ms,
        "memory_limit_mb": memory_mb,
        "sample_count": len(samples),
        "evaluation": {
            "evaluator_id": "programming_judge",
            "status": "sample_tests_ready",
            "reason": "Public Codeforces samples materialized locally.",
            "official_bundle_path": rel_package,
            "sample_tests_path": f"{rel_package}/tests/sample",
            "notes": (
                "Automatic judging is available for sample scope immediately. "
                "Add tests/secret/*.in/*.ans and rebuild package.json to grade secrets."
            ),
        },
    }


def materialize_problem(
    raw_problem_id: str,
    *,
    repo_root: Path | None = None,
    force: bool = False,
    html: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fetch (or reuse cached HTML), write package + benchmark record."""

    root = repo_root or REPO_ROOT
    ref = parse_problem_id(raw_problem_id)
    destination = package_dir_for(ref, root)
    manifest = destination / "package.json"
    if manifest.is_file() and not force:
        package = load_problem_package(destination)
        record = next(
            (
                item
                for item in _load_benchmark_records(root)
                if item.get("problem_id") == ref.problem_id
            ),
            None,
        )
        if record is None:
            record = build_benchmark_record(
                ref,
                metadata=metadata or {"name": ref.canonical_id},
                samples=[
                    SampleCase("01", "", "")
                ],  # placeholder; package already exists
                time_ms=package.limits.time_ms,
                memory_mb=package.limits.memory_mb,
                package_path=destination,
                repo_root=root,
            )
        return {
            "ref": ref,
            "package_dir": destination,
            "benchmark_record": record,
            "reused": True,
        }

    page_html = html if html is not None else fetch_problem_html(ref)
    api_metadata = metadata if metadata is not None else fetch_problem_metadata(ref)
    samples = extract_samples_from_html(page_html)
    time_ms, memory_mb = extract_limits_from_html(page_html)
    write_problem_package(
        ref,
        samples=samples,
        time_ms=time_ms,
        memory_mb=memory_mb,
        destination=destination,
        metadata=api_metadata,
        statement_html=page_html,
        include_secret_group=True,
    )
    record = build_benchmark_record(
        ref,
        metadata=api_metadata,
        samples=samples,
        time_ms=time_ms,
        memory_mb=memory_mb,
        package_path=destination,
        repo_root=root,
    )
    _upsert_benchmark_record(record, repo_root=root)
    return {
        "ref": ref,
        "package_dir": destination,
        "benchmark_record": record,
        "reused": False,
    }


def _load_benchmark_records(repo_root: Path) -> list[dict[str, Any]]:
    path = benchmark_path(repo_root)
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected list benchmark file: {path}")
    return [dict(item) for item in payload]


def _upsert_benchmark_record(record: dict[str, Any], *, repo_root: Path) -> None:
    path = benchmark_path(repo_root)
    records = _load_benchmark_records(repo_root)
    updated = False
    for index, existing in enumerate(records):
        if existing.get("problem_id") == record.get("problem_id"):
            records[index] = record
            updated = True
            break
    if not updated:
        records.append(record)
    records.sort(key=lambda item: str(item.get("problem_id")))
    _atomic_write_text(path, json.dumps(records, indent=2) + "\n")
