#!/usr/bin/env python3
"""Download Kattis sample .in/.ans packs for ICPC benchmark problems.

Usage:
  python3 collectors/fetch_icpc_samples.py
  python3 collectors/fetch_icpc_samples.py --limit 5
  python3 collectors/fetch_icpc_samples.py --problem-id icpc_wf_2012_bottles
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from evaluation.programming_judge import ensure_kattis_samples, write_samples_manifest

BENCHMARK = REPO_ROOT / "data" / "benchmarks" / "icpc" / "benchmark.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--problem-id", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    problems = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    if args.problem_id:
        problems = [p for p in problems if p.get("problem_id") == args.problem_id]
    if args.limit is not None:
        problems = problems[: args.limit]

    ok = 0
    fail = 0
    for problem in problems:
        pid = problem.get("problem_id")
        kid = problem.get("kattis_id")
        if not kid:
            print(f"skip {pid}: no kattis_id")
            continue
        dest = REPO_ROOT / "data" / "benchmarks" / "icpc" / "samples" / str(pid)
        try:
            cases = ensure_kattis_samples(str(kid), dest, force=args.force)
            write_samples_manifest("icpc", str(pid), cases)
            # Mark sample judge ready on the problem.
            evaluation = problem.setdefault("evaluation", {})
            evaluation["evaluator_id"] = "programming_judge"
            evaluation["status"] = "sample_tests_ready"
            evaluation["sample_tests_path"] = str(dest.relative_to(REPO_ROOT))
            evaluation["notes"] = (
                "Local sample .in/.ans from Kattis; secret tests / DomJudge still deferred."
            )
            print(f"ok {pid} ({kid}): {len(cases)} cases")
            ok += 1
        except Exception as exc:
            print(f"FAIL {pid} ({kid}): {exc}")
            fail += 1

    BENCHMARK.write_text(json.dumps(problems, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Done: {ok} ok, {fail} failed")


if __name__ == "__main__":
    main()
