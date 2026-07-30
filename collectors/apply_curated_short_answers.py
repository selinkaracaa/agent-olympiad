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
    "ijso_practical": "lab practical; report rubric only",
    "arml_power": "proof packet; use rubric_llm_v1",
    "arml_national_power": "proof packet; use rubric_llm_v1",
    "ioaa_group": "marking-scheme packet; use rubric_llm_v1",
    "iol_team": "linguistics marking scheme; use rubric_llm_v1",
}


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
        if not answers:
            problems.append({"problem_id": pid, "updated": 0})
            continue

        gold = item.setdefault("gold_label", {})
        total = float(item.get("total_points") or 50)
        existing = {str(p.get("id")): p for p in (gold.get("parts") or [])}
        n = max(len(existing), max((int(k) for k in answers), default=0), 10)
        short_ids = set(answers)
        each = total / max(len(short_ids), 1)

        parts = []
        updated = 0
        for i in range(1, n + 1):
            qid = str(i)
            prev = existing.get(qid, {})
            entry = {
                "id": qid,
                "expected": "",
                "points": 0.0,
                "reference": prev.get("reference") or "",
                "match_mode": "reference_llm",
                "aliases": [],
            }
            if qid in answers:
                spec = answers[qid]
                entry["expected"] = spec["expected"]
                entry["aliases"] = list(spec.get("aliases") or [])
                entry["match_mode"] = "normalized"
                entry["points"] = each
                if not entry["reference"]:
                    entry["reference"] = f"Official short answer: {spec['expected']}"
                updated += 1
            parts.append(entry)

        gold["parts"] = parts
        short = sum(1 for p in parts if p.get("expected"))
        evaluation = item.setdefault("evaluation", {})
        if short >= 5:
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
