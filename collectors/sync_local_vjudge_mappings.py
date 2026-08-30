#!/usr/bin/env python3
"""Write VJudge problem-mode mappings for local programming benchmarks.

- Codeforces: packages under data/benchmarks/codeforces/packages → CodeForces-{id}
- ICPC: every benchmark row with kattis_id → Kattis-{kattis_id}
- IIOT: skipped (no remote OJ id in local metadata)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_codeforces() -> dict:
    packages = REPO_ROOT / "data" / "benchmarks" / "codeforces" / "packages"
    path = REPO_ROOT / "data" / "benchmarks" / "codeforces" / "benchmark.json"
    rows = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    by_id = {str(row.get("problem_id")): row for row in rows}
    updated = 0
    for package in sorted(packages.iterdir()) if packages.is_dir() else []:
        if not package.is_dir() or not (package / "package.json").is_file():
            continue
        problem_id = f"cf_{package.name}"
        row = by_id.get(problem_id)
        if row is None:
            continue
        evaluation = dict(row.get("evaluation") or {})
        evaluation["vjudge_oj"] = "CodeForces"
        evaluation["vjudge_prob_num"] = package.name
        evaluation["vjudge_submit_mode"] = "problem"
        evaluation.pop("vjudge_contest_id", None)
        evaluation.pop("vjudge_problem", None)
        row["codeforces_id"] = package.name
        row["evaluation"] = evaluation
        by_id[problem_id] = row
        updated += 1
    ordered = [by_id[key] for key in sorted(by_id)]
    _write(path, ordered)
    return {"competition": "codeforces", "updated": updated, "total": len(ordered)}


def sync_icpc() -> dict:
    path = REPO_ROOT / "data" / "benchmarks" / "icpc" / "benchmark.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    updated = 0
    for row in rows:
        kattis_id = str(row.get("kattis_id") or "").strip()
        if not kattis_id:
            continue
        evaluation = dict(row.get("evaluation") or {})
        evaluation["vjudge_oj"] = "Kattis"
        evaluation["vjudge_prob_num"] = kattis_id
        evaluation["vjudge_submit_mode"] = "problem"
        evaluation.pop("vjudge_contest_id", None)
        evaluation.pop("vjudge_problem", None)
        row["evaluation"] = evaluation
        updated += 1
    _write(path, rows)
    return {"competition": "icpc", "updated": updated, "total": len(rows)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--competitions",
        nargs="+",
        default=["codeforces", "icpc"],
        choices=["codeforces", "icpc"],
    )
    args = parser.parse_args(argv)
    reports = []
    if "codeforces" in args.competitions:
        reports.append(sync_codeforces())
    if "icpc" in args.competitions:
        reports.append(sync_icpc())
    print(json.dumps({"reports": reports, "iiot": "skipped_no_remote_oj_id"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
