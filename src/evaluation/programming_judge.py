"""Compatibility adapter from benchmark records to the consolidated judge."""

from __future__ import annotations

import json
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from judge import JudgeResult, load_problem_package, package_from_sample_directory
from judge import run_submission as run_package_submission

REPO_ROOT = Path(__file__).resolve().parents[2]
UA = "agent-olympiad-local-judge/2.0 (research sample collector)"


@dataclass(frozen=True)
class TestCase:
    """Legacy in-memory sample shape retained for callers."""

    name: str
    stdin: str
    expected: str


def samples_dir(competition_id: str, problem_id: str, repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / "data" / "benchmarks" / competition_id / "samples" / problem_id


def load_sample_cases(directory: Path) -> list[TestCase]:
    if not directory.is_dir():
        return []
    cases: list[TestCase] = []
    for input_path in sorted(directory.glob("*.in")):
        answer_path = input_path.with_suffix(".ans")
        if not answer_path.is_file():
            answer_path = input_path.with_suffix(".out")
        if answer_path.is_file():
            cases.append(
                TestCase(
                    input_path.stem,
                    input_path.read_text(encoding="utf-8", errors="replace"),
                    answer_path.read_text(encoding="utf-8", errors="replace"),
                )
            )
    return cases


def _safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    for member in members:
        path = Path(member.filename.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError(f"Unsafe ZIP path: {member.filename}")
    return members


def ensure_kattis_samples(
    kattis_id: str,
    dest: Path,
    *,
    force: bool = False,
) -> list[TestCase]:
    """Download and atomically install a Kattis sample archive."""
    existing = load_sample_cases(dest)
    if existing and not force:
        return existing
    url = f"https://open.kattis.com/problems/{kattis_id}/file/statement/samples.zip"
    request = Request(url, headers={"User-Agent": UA})
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read()
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch Kattis samples for {kattis_id}: {exc}") from exc

    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{dest.name}.", dir=dest.parent) as temp:
        staging = Path(temp) / "samples"
        staging.mkdir()
        archive_path = Path(temp) / "samples.zip"
        archive_path.write_bytes(payload)
        with zipfile.ZipFile(archive_path) as archive:
            for member in _safe_members(archive):
                if member.is_dir():
                    continue
                target = staging / Path(member.filename.replace("\\", "/")).name
                if target.suffix.lower() not in {".in", ".ans", ".out"}:
                    continue
                target.write_bytes(archive.read(member))
        if not load_sample_cases(staging):
            raise RuntimeError(f"Kattis archive for {kattis_id} has no paired samples.")
        if dest.exists():
            for old in dest.glob("*"):
                if old.is_file():
                    old.unlink()
        dest.mkdir(parents=True, exist_ok=True)
        for source in staging.iterdir():
            os.replace(source, dest / source.name)
    return load_sample_cases(dest)


def _extract_source(submission: str) -> tuple[str, str]:
    fence = re.search(
        r"```(?P<language>python|py|python3|cpp|c\+\+|cpp17|c\+\+17)?\s*\n"
        r"(?P<source>.*?)```",
        submission,
        re.IGNORECASE | re.DOTALL,
    )
    if not fence:
        source = submission.strip()
        if (
            "#include" in source
            or "using namespace std" in source
            or re.search(r"\bint\s+main\s*\(", source)
        ):
            return source, "cpp17"
        return source, "python3"
    language = (fence.group("language") or "python3").lower()
    if language in {"cpp", "c++", "cpp17", "c++17"}:
        language = "cpp17"
    else:
        language = "python3"
    return fence.group("source").strip(), language


def _official_package_path(problem: dict[str, Any], root: Path) -> Path | None:
    evaluation = dict(problem.get("evaluation") or {})
    raw = (
        evaluation.get("official_bundle_path")
        or evaluation.get("official_package_path")
        or evaluation.get("judge_package_path")
        or problem.get("official_bundle_path")
    )
    if not raw:
        return None
    path = Path(str(raw))
    if not path.is_absolute():
        path = root / path
    return path if (path / "package.json").is_file() else None


def judge_programming_submission(
    problem: dict[str, Any],
    submission_text: str,
    *,
    competition_id: str,
    repo_root: Path | None = None,
    fetch_kattis: bool = True,
    test_scope: str | None = None,
) -> JudgeResult:
    """Judge a benchmark submission, preferring mounted official bundles."""
    root = repo_root or REPO_ROOT
    problem_id = str(problem.get("problem_id") or "")
    official_path = _official_package_path(problem, root)
    package = load_problem_package(official_path) if official_path else None

    requested_scope = test_scope.lower() if test_scope else None
    if requested_scope is None:
        requested_scope = "secret" if package and package.tests_for("secret") else "sample"
    if requested_scope == "sample" and (
        package is None or not package.tests_for("sample")
    ):
        destination = samples_dir(competition_id, problem_id, root)
        if not load_sample_cases(destination) and fetch_kattis and problem.get("kattis_id"):
            try:
                ensure_kattis_samples(str(problem["kattis_id"]), destination)
            except RuntimeError:
                pass
        package = package_from_sample_directory(
            problem_id,
            destination,
            time_ms=int(problem.get("time_limit_ms", 5000)),
            memory_mb=int(problem.get("memory_limit_mb", 256)),
            output_kb=int(problem.get("output_limit_kb", 1024)),
        )
    if package is None:
        package = package_from_sample_directory(
            problem_id, samples_dir(competition_id, problem_id, root)
        )
    source, language = _extract_source(submission_text)
    return run_package_submission(package, source, language, requested_scope)


def run_python_cases(
    code: str,
    cases: list[TestCase],
    *,
    timeout_sec: float = 5.0,
):
    """Legacy helper implemented through a temporary v1 package."""
    with tempfile.TemporaryDirectory(prefix="ao_legacy_cases_") as temp:
        root = Path(temp)
        for case in cases:
            (root / f"{case.name}.in").write_text(case.stdin, encoding="utf-8")
            (root / f"{case.name}.ans").write_text(case.expected, encoding="utf-8")
        package = package_from_sample_directory(
            "legacy", root, time_ms=max(1, int(timeout_sec * 1000))
        )
        return list(run_package_submission(package, code, "python3", "sample").cases)


def icpc_rank_key(
    *, solved: int, penalty_minutes: int, last_accept_minute: int = 0
) -> tuple[int, int, int]:
    return (-solved, penalty_minutes, last_accept_minute)


def write_samples_manifest(
    competition_id: str, problem_id: str, cases: list[TestCase]
) -> Path:
    destination = samples_dir(competition_id, problem_id)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / "manifest.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(
            {
                "competition_id": competition_id,
                "problem_id": problem_id,
                "n_cases": len(cases),
                "cases": [case.name for case in cases],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)
    return path
