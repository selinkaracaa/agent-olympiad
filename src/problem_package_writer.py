"""Shared ``ao.icpc-package/v1`` materialization for programming benchmarks."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from judge.package import SCHEMA_VERSION
except ImportError:  # pragma: no cover
    from src.judge.package import SCHEMA_VERSION


@dataclass(frozen=True)
class SampleCase:
    name: str
    input_text: str
    output_text: str


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def load_samples_from_directory(directory: Path) -> list[SampleCase]:
    """Read paired ``*.in`` / ``*.ans`` (or ``*.out``) files from a flat folder."""
    if not directory.is_dir():
        return []
    cases: list[SampleCase] = []
    for input_path in sorted(directory.glob("*.in")):
        answer_path = input_path.with_suffix(".ans")
        if not answer_path.is_file():
            answer_path = input_path.with_suffix(".out")
        if not answer_path.is_file():
            continue
        cases.append(
            SampleCase(
                name=input_path.stem,
                input_text=input_path.read_text(encoding="utf-8", errors="replace"),
                output_text=answer_path.read_text(encoding="utf-8", errors="replace"),
            )
        )
    return cases


def write_problem_package(
    *,
    problem_id: str,
    destination: Path,
    samples: list[SampleCase],
    time_ms: int = 5000,
    memory_mb: int = 256,
    output_kb: int = 1024,
    checker_mode: str = "token",
    source: str = "unknown",
    extra_manifest: dict[str, Any] | None = None,
    include_secret_group: bool = False,
    grading_scope_labels: dict[str, str] | None = None,
    sample_points: float = 0.0,
    secret_points: float = 1.0,
) -> Path:
    """Write an ``ao.icpc-package/v1`` bundle with public sample tests."""
    if not samples:
        raise ValueError("At least one public sample is required to build a package.")

    root = destination.resolve()
    sample_dir = root / "tests" / "sample"
    secret_dir = root / "tests" / "secret"
    sample_dir.mkdir(parents=True, exist_ok=True)

    for sample in samples:
        (sample_dir / f"{sample.name}.in").write_text(
            _ensure_trailing_newline(sample.input_text),
            encoding="utf-8",
        )
        (sample_dir / f"{sample.name}.ans").write_text(
            _ensure_trailing_newline(sample.output_text),
            encoding="utf-8",
        )

    groups: list[dict[str, str]] = [
        {"id": "sample", "scope": "sample", "tests": "tests/sample"},
    ]
    subtasks: list[dict[str, Any]] = [
        {"id": "sample", "points": sample_points, "groups": ["sample"]},
    ]
    if include_secret_group and secret_dir.is_dir() and any(secret_dir.glob("*.in")):
        groups.append({"id": "secret", "scope": "secret", "tests": "tests/secret"})
        subtasks.append(
            {"id": "official", "points": secret_points, "groups": ["secret"]}
        )

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "problem_id": problem_id,
        "source": source,
        "limits": {
            "time_ms": time_ms,
            "memory_mb": memory_mb,
            "output_kb": output_kb,
        },
        "checker": {"mode": checker_mode},
        "groups": groups,
        "subtasks": subtasks,
    }
    if grading_scope_labels:
        manifest["grading_scope_labels"] = grading_scope_labels
    if extra_manifest:
        manifest.update(extra_manifest)

    _atomic_write_text(root / "package.json", json.dumps(manifest, indent=2) + "\n")
    return root


def materialize_package_from_directory(
    *,
    problem_id: str,
    sample_directory: Path,
    package_directory: Path,
    time_ms: int = 5000,
    memory_mb: int = 256,
    output_kb: int = 1024,
    source: str = "kattis",
    kattis_id: str | None = None,
    include_secret_group: bool = True,
    grading_scope_labels: dict[str, str] | None = None,
) -> Path:
    """Build a package from an existing flat sample directory."""
    samples = load_samples_from_directory(sample_directory)
    if not samples:
        raise ValueError(f"No paired samples found in {sample_directory}")
    extra: dict[str, Any] = {}
    if kattis_id:
        extra["kattis_id"] = kattis_id
    return write_problem_package(
        problem_id=problem_id,
        destination=package_directory,
        samples=samples,
        time_ms=time_ms,
        memory_mb=memory_mb,
        output_kb=output_kb,
        source=source,
        extra_manifest=extra or None,
        include_secret_group=include_secret_group,
        grading_scope_labels=grading_scope_labels
        or {
            "sample": "kattis-public-sample",
            "secret": "authorized-local-secret",
        },
    )
