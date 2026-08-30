#!/usr/bin/env python3
"""Sync local Codeforces packages into benchmark.json with VJudge problem-mode ids.

Does not crawl the full Codeforces problemset. Only packages already present under
``data/benchmarks/codeforces/packages/`` are mapped as ``CodeForces-{id}``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from codeforces_adapter import (  # noqa: E402
    benchmark_path,
    materialize_problem,
    parse_problem_id,
)


def local_package_ids(repo_root: Path) -> list[str]:
    root = repo_root / "data" / "benchmarks" / "codeforces" / "packages"
    if not root.is_dir():
        return []
    ids: list[str] = []
    for path in sorted(root.iterdir()):
        if path.is_dir() and (path / "package.json").is_file():
            ids.append(path.name)
    return ids


def apply_problem_mode(record: dict) -> dict:
    evaluation = dict(record.get("evaluation") or {})
    cf_id = str(record.get("codeforces_id") or parse_problem_id(record["problem_id"]).canonical_id)
    evaluation["vjudge_oj"] = "CodeForces"
    evaluation["vjudge_prob_num"] = cf_id
    evaluation["vjudge_submit_mode"] = "problem"
    evaluation.pop("vjudge_contest_id", None)
    evaluation.pop("vjudge_problem", None)
    record = dict(record)
    record["codeforces_id"] = cf_id
    record["evaluation"] = evaluation
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild local packages/statements when refreshing records.",
    )
    parser.add_argument(
        "--ids-only",
        action="store_true",
        help="Only rewrite VJudge mapping fields on existing benchmark rows.",
    )
    args = parser.parse_args(argv)

    ids = local_package_ids(REPO_ROOT)
    if not ids:
        print("No local Codeforces packages found.", file=sys.stderr)
        return 1

    path = benchmark_path(REPO_ROOT)
    if args.ids_only:
        rows = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
        by_id = {str(row.get("problem_id")): row for row in rows}
        for package_id in ids:
            ref = parse_problem_id(package_id)
            existing = by_id.get(ref.problem_id)
            if existing is None:
                print(f"skip missing benchmark row for {ref.problem_id}", flush=True)
                continue
            by_id[ref.problem_id] = apply_problem_mode(existing)
        updated = [by_id[key] for key in sorted(by_id)]
        path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"updated": len(ids), "path": str(path)}, indent=2))
        return 0

    for package_id in ids:
        result = materialize_problem(package_id, repo_root=REPO_ROOT, force=args.force)
        record = apply_problem_mode(result["benchmark_record"])
        # materialize already upserts; rewrite mapping in case of reuse path
        from codeforces_adapter import _upsert_benchmark_record

        _upsert_benchmark_record(record, repo_root=REPO_ROOT)
        print(
            json.dumps(
                {
                    "problem_id": record["problem_id"],
                    "vjudge": f"CodeForces-{record['evaluation']['vjudge_prob_num']}",
                    "reused": result["reused"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    print(json.dumps({"synced": len(ids), "path": str(path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
