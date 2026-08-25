#!/usr/bin/env python3
"""Collect resumable Kattis sample archives for the ICPC benchmark."""

from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "data" / "benchmarks" / "icpc" / "benchmark.json"
SAMPLES_ROOT = ROOT / "data" / "benchmarks" / "icpc" / "samples"
USER_AGENT = "agent-olympiad-icpc-samples/1.0"


def has_samples(directory: Path) -> bool:
    if not directory.is_dir():
        return False
    for input_path in directory.glob("*.in"):
        if input_path.with_suffix(".ans").is_file() or input_path.with_suffix(".out").is_file():
            return True
    return False


def validated_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    seen: set[str] = set()
    for member in members:
        path = Path(member.filename.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"ZIP path traversal rejected: {member.filename}")
        if member.is_dir():
            continue
        name = path.name
        if name in seen:
            raise ValueError(f"Duplicate flattened ZIP member: {name}")
        seen.add(name)
    return members


def extract_samples_atomic(payload: bytes, destination: Path) -> int:
    """Validate first, then atomically replace each accepted sample file."""
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = validated_members(archive)
        accepted = [
            member
            for member in members
            if not member.is_dir()
            and Path(member.filename).suffix.lower() in {".in", ".ans", ".out"}
        ]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=f".{destination.name}.", dir=destination.parent
        ) as temporary:
            staging = Path(temporary)
            for member in accepted:
                (staging / Path(member.filename).name).write_bytes(archive.read(member))
            if not has_samples(staging):
                raise ValueError("Archive contains no paired .in/.ans or .in/.out samples.")
            destination.mkdir(parents=True, exist_ok=True)
            for source in staging.iterdir():
                os.replace(source, destination / source.name)
    return len(accepted)


def fetch_archive(
    kattis_id: str,
    *,
    opener: Callable[..., Any] = urlopen,
) -> bytes:
    url = f"https://open.kattis.com/problems/{kattis_id}/file/statement/samples.zip"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with opener(request, timeout=30) as response:
        return response.read()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def collect(
    *,
    benchmark_path: Path = BENCHMARK,
    samples_root: Path = SAMPLES_ROOT,
    limit: int | None = None,
    force: bool = False,
    problem: str | None = None,
    dry_run: bool = False,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    records = json.loads(benchmark_path.read_text(encoding="utf-8"))
    records = [record for record in records if record.get("kattis_id")]
    if problem:
        records = [
            record
            for record in records
            if problem in {str(record.get("problem_id")), str(record.get("kattis_id"))}
        ]
    if limit is not None:
        records = records[: max(0, limit)]

    results: list[dict[str, Any]] = []
    for record in records:
        problem_id = str(record["problem_id"])
        kattis_id = str(record["kattis_id"])
        destination = samples_root / problem_id
        if has_samples(destination) and not force:
            results.append(
                {"problem_id": problem_id, "kattis_id": kattis_id, "status": "existing"}
            )
            continue
        if dry_run:
            results.append(
                {
                    "problem_id": problem_id,
                    "kattis_id": kattis_id,
                    "status": "would-fetch",
                }
            )
            continue
        try:
            payload = fetch_archive(kattis_id, opener=opener)
            files = extract_samples_atomic(payload, destination)
        except Exception as exc:
            results.append(
                {
                    "problem_id": problem_id,
                    "kattis_id": kattis_id,
                    "status": "error",
                    "error": str(exc),
                }
            )
        else:
            results.append(
                {
                    "problem_id": problem_id,
                    "kattis_id": kattis_id,
                    "status": "fetched",
                    "files": files,
                }
            )

    summary = {
        "schema_version": "ao.icpc-samples-manifest/v1",
        "benchmark_problem_count": len(
            [record for record in json.loads(benchmark_path.read_text(encoding="utf-8")) if record.get("kattis_id")]
        ),
        "selected": len(results),
        "fetched": sum(item["status"] == "fetched" for item in results),
        "existing": sum(item["status"] == "existing" for item in results),
        "errors": sum(item["status"] == "error" for item in results),
        "dry_run": dry_run,
        "problems": results,
    }
    if not dry_run:
        _atomic_json(samples_root / "manifest.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--problem")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    summary = collect(
        limit=args.limit,
        force=args.force,
        problem=args.problem,
        dry_run=args.dry_run,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
