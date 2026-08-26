"""Regrade a saved competition result with the current gold evaluator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from evaluation.gold import GoldAnswerEvaluator, load_gold_parts


def main() -> None:
    batch_path = REPO / "results/open_table_coach_arml_local_2009_tinker.json/competition_batch.json"
    transcript_path = (
        REPO
        / "results/open_table_coach_arml_local_2009_tinker.json/transcripts/arml_local__arml_local_2009__open_table_coach__enforced.json"
    )
    benchmark_path = REPO / "data/benchmarks/arml_local/benchmark.json"

    problems = json.loads(benchmark_path.read_text(encoding="utf-8"))
    problem = next(p for p in problems if p["problem_id"] == "arml_local_2009")
    gold = problem["gold_label"]

    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    result_item = batch["results"][0]
    submission = result_item["final_answer"]

    eval_result = GoldAnswerEvaluator(
        parts=load_gold_parts(gold),
        submission_text=submission,
    ).evaluate()
    grade = {
        "graded": True,
        "method": "gold_answer_v1",
        "score": eval_result.total_score,
        "max_score": eval_result.max_score,
        "correct": eval_result.total_score >= eval_result.max_score,
        "evaluation": eval_result.to_dict(),
        "submitted_by": result_item.get("submitted_by", "Agent_6"),
    }

    print("=== Regrade Summary ===")
    print(f"Total: {grade['score']:.4f} / {grade['max_score']:.4f}")
    print(f"Full credit: {grade['correct']}")
    print()
    for c in eval_result.criteria:
        mark = "OK" if c.score > 0 else "MISS"
        print(f"  Q{c.id}: {mark}  score={c.score:.4f}  {c.evidence[0]}  vs  {c.evidence[1]}")

    old_score = result_item.get("grade_score")
    result_item["grade_score"] = grade["score"]
    result_item["grade_max_score"] = grade["max_score"]
    result_item["graded"] = True
    batch_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    if "grade" in transcript:
        transcript["grade"] = grade
    final_result = transcript.get("final_result")
    if isinstance(final_result, dict):
        final_result["grade"] = grade
    transcript_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print()
    print(f"Updated batch score: {old_score} -> {grade['score']:.4f}")
    print("Wrote", batch_path)
    print("Wrote", transcript_path)


if __name__ == "__main__":
    main()
