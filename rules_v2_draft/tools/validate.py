from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DRAFT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = DRAFT_ROOT.parent
sys.path.insert(0, str(DRAFT_ROOT))

from rules_v2 import RuleRepository  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the isolated Agent Olympiad rules-v2 draft."
    )
    parser.add_argument(
        "--check-current-benchmarks",
        action="store_true",
        help="also resolve every row for the eight draft-example competitions",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    repository = RuleRepository.open(DRAFT_ROOT)
    validation = repository.validate(check_source_hashes=True)
    benchmark = (
        repository.audit_benchmarks(PROJECT_ROOT / "data" / "benchmarks")
        if args.check_current_benchmarks
        else None
    )

    if args.json:
        output = {"validation": validation.as_dict()}
        if benchmark is not None:
            output["current_benchmark_audit"] = benchmark.as_dict()
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(
            f"rulesets={len(repository.rulesets)} "
            f"errors={len(validation.errors)} warnings={len(validation.warnings)}"
        )
        for issue in validation.issues:
            print(
                f"{issue.severity.upper():7} {issue.code:28} "
                f"{issue.location} :: {issue.message}"
            )
        if benchmark is not None:
            print(
                f"benchmark_rows={benchmark.rows_checked} "
                f"resolved={benchmark.rows_resolved} "
                f"migration_failures={sum(item['count'] for item in benchmark.failures)}"
            )
            for failure in benchmark.failures:
                print(
                    f"MIGRATE {failure['competition_id']:22} "
                    f"count={failure['count']} example={failure['example_problem_id']} "
                    f":: {failure['message']}"
                )

    return 0 if validation.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
