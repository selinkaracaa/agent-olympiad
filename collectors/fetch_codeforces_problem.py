#!/usr/bin/env python3
"""Fetch one Codeforces problem and materialize a local judge package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from codeforces_adapter import materialize_problem, parse_problem_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download public Codeforces metadata/samples and write an "
            "ao.icpc-package/v1 bundle plus benchmark.json entry."
        )
    )
    parser.add_argument(
        "problem_id",
        help="Codeforces id like 4A or cf_4A",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild even if the local package already exists.",
    )
    parser.add_argument(
        "--offline-html",
        type=Path,
        help="Use a cached statement HTML file instead of downloading.",
    )
    parser.add_argument(
        "--offline-metadata",
        type=Path,
        help="Use a cached metadata.json instead of calling the API.",
    )
    args = parser.parse_args(argv)

    html = (
        args.offline_html.read_text(encoding="utf-8")
        if args.offline_html
        else None
    )
    metadata = (
        json.loads(args.offline_metadata.read_text(encoding="utf-8-sig"))
        if args.offline_metadata
        else None
    )
    result = materialize_problem(
        args.problem_id,
        repo_root=REPO_ROOT,
        force=args.force,
        html=html,
        metadata=metadata,
    )
    ref = result["ref"]
    record = result["benchmark_record"]
    print(
        json.dumps(
            {
                "problem_id": ref.problem_id,
                "codeforces_id": ref.canonical_id,
                "package_dir": str(result["package_dir"]),
                "reused": result["reused"],
                "sample_count": record.get("sample_count"),
                "official_bundle_path": record["evaluation"]["official_bundle_path"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
