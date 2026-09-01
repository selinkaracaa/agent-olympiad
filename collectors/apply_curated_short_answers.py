"""Apply curated short-answer gold into benchmark JSON files.

Looks for data/rubrics/<contest>_short_answers.json and updates
data/benchmarks/<contest>/benchmark.json.

Usage:
  python3 collectors/apply_curated_short_answers.py
  python3 collectors/apply_curated_short_answers.py --contest arml_local
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUBRIC_DIR = REPO_ROOT / "data" / "rubrics"
BENCHMARK_ROOT = REPO_ROOT / "data" / "benchmarks"

# Contests that are not short-answer sheets (skip with explanation).
NON_SHORT_ANSWER = {
    "ieo_business_case": "slide/rubric deliverable",
    "wsc_writing": "essay/rubric deliverable",
    "jessup": "memorial/oral deliverable",
    "icpc": "programming judge (deferred)",
    "iiot": "programming judge (deferred)",
    "codeforces": "programming judge",
    "ijso_practical": "lab practical; report rubric only",
    "arml_power": "proof packet; use rubric_llm_v1",
    "arml_national_power": "proof packet; use rubric_llm_v1",
    "ioaa_group": "marking-scheme packet; use rubric_llm_v1",
    "iol_team": "linguistics marking scheme; use rubric_llm_v1",
    "cybench": "upstream flags not mapped into local answer key",
}


def _part_specs(raw_answers: dict) -> dict[str, dict]:
    """Keep only part entries; drop metadata keys like _provenance."""
    out: dict[str, dict] = {}
    for key, value in raw_answers.items():
        if str(key).startswith("_") or not isinstance(value, dict):
            continue
        if "expected" in value or "reference" in value or value.get("match_mode"):
            out[str(key)] = value
    return out


def _ordered_part_ids(existing: dict[str, dict], specs: dict[str, dict]) -> list[str]:
    """Prefer dense numeric 1..n for multipart sheets; keep sparse ids for quizzes."""
    curated_ids = list(specs.keys())
    numeric_curated = all(qid.isdigit() for qid in curated_ids) if curated_ids else False
    numeric_existing = all(qid.isdigit() for qid in existing) if existing else True
    if numeric_curated and numeric_existing:
        nums = [int(qid) for qid in curated_ids] + [int(qid) for qid in existing]
        max_n = max(nums) if nums else 0
        # Team math sheets omit some IDs but still occupy 1..N slots.
        if max_n >= 5:
            return [str(i) for i in range(1, max(max_n, 10) + 1)]
        return [str(i) for i in sorted(set(nums))]

    ordered: list[str] = []
    seen: set[str] = set()
    for qid in list(existing.keys()) + curated_ids:
        if qid not in seen:
            ordered.append(qid)
            seen.add(qid)
    return ordered

def apply_contest(contest: str) -> dict:
    curated_path = RUBRIC_DIR / f"{contest}_short_answers.json"
    benchmark_path = BENCHMARK_ROOT / contest / "benchmark.json"
    if not curated_path.exists():
        reason = NON_SHORT_ANSWER.get(contest, "no curated short-answer file")
        return {"contest": contest, "status": "skipped", "reason": reason}
    if not benchmark_path.exists():
        return {"contest": contest, "status": "error", "reason": f"missing {benchmark_path}"}

    curated = json.loads(curated_path.read_text(encoding="utf-8"))
    curated = {k: v for k, v in curated.items() if not str(k).startswith("_")}
    items = json.loads(benchmark_path.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        return {"contest": contest, "status": "error", "reason": "benchmark is not a list"}

    problems = []
    for item in items:
        pid = item["problem_id"]
        answers = curated.get(pid)
        if not isinstance(answers, dict):
            problems.append({"problem_id": pid, "updated": 0})
            continue

        specs = _part_specs(answers)
        if not specs:
            problems.append({"problem_id": pid, "updated": 0})
            continue

        gold = item.setdefault("gold_label", {})
        existing = {str(p.get("id")): p for p in (gold.get("parts") or [])}
        part_ids = _ordered_part_ids(existing, specs)
        short_ids = [qid for qid, spec in specs.items() if str(spec.get("expected") or "").strip()]
        if item.get("total_points"):
            each = float(item["total_points"]) / max(len(short_ids), 1)
        else:
            each = 1.0

        parts = []
        updated = 0
        for qid in part_ids:
            prev = existing.get(qid, {})
            entry = {
                "id": qid,
                "expected": "",
                "points": 0.0,
                "reference": prev.get("reference") or "",
                "match_mode": "reference_llm",
                "aliases": [],
            }
            if qid in specs:
                spec = specs[qid]
                expected = str(spec.get("expected") or "").strip()
                entry["aliases"] = list(spec.get("aliases") or [])
                if expected:
                    entry["expected"] = expected
                    entry["match_mode"] = str(spec.get("match_mode") or "normalized")
                    entry["points"] = each
                    if not entry["reference"]:
                        entry["reference"] = f"Official short answer: {expected}"
                    updated += 1
                else:
                    entry["match_mode"] = str(spec.get("match_mode") or "reference_llm")
                    if spec.get("reference"):
                        entry["reference"] = str(spec["reference"])
            parts.append(entry)

        gold["parts"] = parts
        short = sum(1 for p in parts if p.get("expected"))
        evaluation = item.setdefault("evaluation", {})
        if short >= 1:
            evaluation["evaluator_id"] = "gold_answer_v1"
            evaluation["status"] = "ready"
            evaluation["fallback_evaluator_id"] = "rubric_llm_v1"
            evaluation["deliverable"] = "answer_sheet"
            evaluation["short_answer_source"] = str(curated_path.relative_to(REPO_ROOT))
            evaluation.setdefault(
                "rubric_path",
                "data/rubrics/numerical_sheet_reference_40_v1.json",
            )
        problems.append(
            {
                "problem_id": pid,
                "updated": updated,
                "short_parts": short,
                "evaluator_id": evaluation.get("evaluator_id"),
            }
        )

    benchmark_path.write_text(
        json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {
        "contest": contest,
        "status": "applied",
        "curated_file": str(curated_path.relative_to(REPO_ROOT)),
        "problems": problems,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contest", default=None, help="Single contest id; default = all")
    args = parser.parse_args()

    if args.contest:
        contests = [args.contest]
    else:
        contests = sorted({p.parent.name for p in BENCHMARK_ROOT.glob("*/benchmark.json")})

    summaries = [apply_contest(contest) for contest in contests]
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
