"""Re-score Phase A artifacts with the current gold parser (no new LLM calls).

Usage:
  python3 src/rescore_phase_a.py
  python3 src/rescore_phase_a.py --input results/phase_a/20260821-155239/phase_a.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
from evaluation.programming_judge import judge_programming_submission


def load_problem(competition: str, problem_id: str) -> dict:
    path = REPO_ROOT / "data" / "benchmarks" / competition / "benchmark.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(items, dict):
        items = items.get("problems") or []
    for item in items:
        if item.get("problem_id") == problem_id:
            return item
    raise KeyError(f"{competition}/{problem_id}")


def submission_text(row: dict) -> tuple[str, bool]:
    """Return (text, truncated_preview). Prefer full final_answer when present."""
    full = row.get("final_answer")
    if isinstance(full, str) and full.strip():
        return full, False
    preview = row.get("final_answer_preview") or ""
    # Historical Phase A rows only stored a 300-char preview.
    truncated = len(preview) >= 300 and not preview.rstrip().endswith(
        (".", ")", "]", "}", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
    )
    # Safer: treat exactly 300 chars as truncated (legacy cap).
    if len(preview) == 300:
        truncated = True
    return preview, truncated


def rescore_row(row: dict) -> dict:
    if row.get("status") != "ok":
        return row
    competition = row["competition"]
    problem_id = row["problem_id"]
    problem = load_problem(competition, problem_id)
    text, truncated = submission_text(row)
    old = {
        "grade_score": row.get("grade_score"),
        "grade_max_score": row.get("grade_max_score"),
        "grade_method": row.get("grade_method"),
    }

    evaluation = problem.get("evaluation") or {}
    gold = problem.get("gold_label") or {}
    parts = gold.get("parts") or []
    has_short = any(str(p.get("expected") or "").strip() for p in parts)

    if has_short:
        result = GoldAnswerEvaluator(
            parts=load_gold_parts(gold),
            submission_text=text,
        ).evaluate()
        new_score = result.total_score
        # Never downgrade when we only have a truncated preview of the
        # originally graded full answer sheet.
        if (
            truncated
            and old["grade_score"] is not None
            and new_score < float(old["grade_score"])
        ):
            row["grade_method"] = old["grade_method"]
            row["grade_score"] = old["grade_score"]
            row["grade_max_score"] = old["grade_max_score"]
            row["graded"] = True
            row["rescored"] = False
            row["rescore_kept_original"] = True
            row["score_delta"] = 0
            row["would_have_scored"] = new_score
        else:
            row["grade_method"] = "gold_answer_v1"
            row["grade_score"] = new_score
            row["grade_max_score"] = result.max_score
            row["graded"] = True
            row["rescored"] = True
            row["score_delta"] = new_score - (old["grade_score"] or 0)
    elif evaluation.get("evaluator_id") == "programming_judge" or problem.get(
        "task_type"
    ) in {"algorithmic_programming", "programming"}:
        judged = judge_programming_submission(
            problem,
            text,
            competition_id=competition,
            repo_root=REPO_ROOT,
            fetch_kattis=False,
        )
        row["grade_method"] = judged.method
        row["grade_score"] = judged.score
        row["grade_max_score"] = judged.max_score
        row["graded"] = judged.graded
        row["verdict"] = judged.verdict
        row["rescored"] = True
        row["score_delta"] = (judged.score or 0) - (old["grade_score"] or 0)
    else:
        row["rescored"] = False
        row["score_delta"] = 0

    row["previous_grade"] = old
    row["preview_truncated"] = truncated
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=REPO_ROOT / "results" / "phase_a" / "20260821-155239" / "phase_a.json",
    )
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))

    rows = [rescore_row(dict(r)) for r in data.get("results") or []]
    data["results"] = rows
    data["rescored"] = True
    data["rescore_note"] = (
        "Regraded with gold parser v2 (T-/semicolon formats). "
        "Truncated 300-char previews never lower the original live grade."
    )

    out = args.input.with_name("phase_a_rescored.json")
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"{'contest':22} {'schema':14} {'old':12} {'new':12} delta")
    for r in rows:
        old = r.get("previous_grade") or {}
        old_s = "—"
        new_s = "—"
        if old.get("grade_score") is not None:
            old_s = f"{old['grade_score']:g}/{old['grade_max_score']:g}"
        if r.get("grade_score") is not None:
            new_s = f"{r['grade_score']:g}/{r['grade_max_score']:g}"
        flag = ""
        if r.get("rescore_kept_original"):
            flag = " kept-orig"
        elif r.get("preview_truncated"):
            flag = " trunc"
        print(
            f"{r.get('competition','?'):22} {r.get('schema','?'):14} "
            f"{old_s:12} {new_s:12} {r.get('score_delta',0):+g}{flag}"
        )
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
