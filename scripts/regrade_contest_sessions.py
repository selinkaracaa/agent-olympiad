#!/usr/bin/env python3
"""Regrade saved contest_session.json files with the current gold grader."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_adapters import grade_contest_result  # noqa: E402
from contest_manifest import load_contest_manifest  # noqa: E402

MANIFEST_ROOT = REPO_ROOT / "data" / "contest_manifests" / "generated"
BENCH_ROOT = REPO_ROOT / "data" / "benchmarks"


def regrade_dir(out_root: Path) -> list[dict]:
    rows: list[dict] = []
    for session_path in sorted(out_root.glob("*/contest_session.json")):
        problem_id = session_path.parent.name
        manifest_path = MANIFEST_ROOT / f"{problem_id}.json"
        row = {
            "problem_id": problem_id,
            "status": "missing_manifest",
            "score": "",
            "max_score": "",
            "task_utility": "",
            "coordination_score": "",
            "turns_used": "",
            "api_calls_used": "",
            "deadline_submission": "",
        }
        if not manifest_path.is_file():
            rows.append(row)
            continue
        try:
            payload = json.loads(session_path.read_text(encoding="utf-8"))
            manifest = load_contest_manifest(manifest_path, benchmark_root=BENCH_ROOT)
            grade = grade_contest_result(
                manifest,
                {
                    "tasks": payload.get("tasks") or {},
                    "submissions": payload.get("submissions") or {},
                },
            )
            metrics = dict(payload.get("metrics") or {})
            metrics["task_utility"] = grade.get("task_utility")
            payload["grade"] = grade
            payload["metrics"] = metrics
            session_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            budget = payload.get("budget") or {}
            diag = payload.get("diagnostics") or {}
            row.update(
                {
                    "status": "ok",
                    "score": grade.get("score", ""),
                    "max_score": grade.get("max_score", ""),
                    "task_utility": grade.get("task_utility", ""),
                    "coordination_score": metrics.get("coordination_score", ""),
                    "turns_used": budget.get("turns_used", ""),
                    "api_calls_used": budget.get("api_calls_used", ""),
                    "deadline_submission": diag.get("deadline_submission", ""),
                }
            )
        except Exception as exc:  # noqa: BLE001
            row["status"] = f"error:{type(exc).__name__}"
            row["score"] = str(exc)[:120]
        rows.append(row)

    summary = out_root / "summary.tsv"
    if rows:
        fields = list(rows[0].keys())
        with summary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    args = parser.parse_args()
    for root in args.roots:
        rows = regrade_dir(root)
        ok = sum(1 for row in rows if row["status"] == "ok")
        nz = sum(
            1
            for row in rows
            if row["status"] == "ok" and float(row.get("task_utility") or 0) > 0
        )
        print(f"{root}: regraded {ok}/{len(rows)} | nonzero_util={nz}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
