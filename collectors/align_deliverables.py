"""Align each rule card's submission/scoring block with the rest of the repo.

Three places describe what a team hands in, and they used to disagree:

- `data/benchmarks/{cid}/benchmark.json` carries `task_type` and, for some tracks,
  an `evaluation` block naming the evaluator and rubric;
- `data/evaluators/registry.json` says which mime types each evaluator accepts;
- `data/rules/{cid}.json` told the agent to submit plain text regardless.

This script makes the rule card state the official deliverable, the mime types the
official contest expects, the mime types the `src/` runner can actually accept
today, and the evaluator/rubric that will grade the result.

Usage:
    python collectors/align_deliverables.py --dry-run
    python collectors/align_deliverables.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "rules"
BENCHMARKS = REPO / "data" / "benchmarks"

sys.path.insert(0, str(REPO / "src"))

from evaluation.registry import load_registry  # noqa: E402

# What the official contest actually collects from a team.
OFFICIAL_DELIVERABLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "arml_local": ("answer_sheet", ("text/plain",)),
    "arml_national_team": ("answer_sheet", ("text/plain",)),
    "arml_national_power": ("proof_packet", ("text/plain",)),
    "arml_power": ("proof_packet", ("text/plain",)),
    "pumac_power": ("proof_packet", ("text/plain",)),
    "hmmt_guts": ("answer_sheet", ("text/plain",)),
    "purple_comet": ("answer_sheet", ("text/plain",)),
    "wmtc": ("answer_sheet", ("text/plain",)),
    "iol_team": ("worked_answers", ("text/plain",)),
    "ioaa_group": ("worked_answers", ("text/plain",)),
    "fyziklani": ("answer_sheet", ("text/plain",)),
    "science_olympiad": ("event_answer_sheet", ("text/plain",)),
    "ijso_practical": ("lab_report", ("text/plain",)),
    "eoes": ("lab_report", ("text/plain",)),
    "science_bowl": ("spoken_answer", ("text/plain",)),
    "qanta": ("spoken_answer", ("text/plain",)),
    "history_olympiad": ("spoken_answer", ("text/plain",)),
    "mystery_hunt": ("puzzle_answer", ("text/plain",)),
    "cybench": ("flag", ("text/plain",)),
    "nyu_ctf_bench": ("flag", ("text/plain",)),
    "icpc": ("source_code", ("text/x-c++src", "text/x-python")),
    "iiot": ("source_code", ("text/x-c++src", "text/x-python")),
    "ioai_team": ("code_and_predictions", ("text/x-python", "text/plain")),
    "ieo_business_case": ("slide_deck", ("text/html", "application/pdf")),
    "gcch_harvard": ("slide_deck", ("text/html", "application/pdf")),
    "cfa_research_challenge": ("research_report_and_deck", ("application/pdf", "text/html")),
    "wharton_investment": ("investment_report", ("application/pdf",)),
    "jessup": ("written_memorial", ("application/pdf",)),
    "vis_moot": ("written_memorandum", ("application/pdf",)),
    "wsc_writing": ("written_essay", ("text/plain",)),
    "ichto": ("oral_report_and_opposition", ("text/plain",)),
    "ethics_bowl_appe": ("oral_case_presentation", ("text/plain",)),
    "ethics_bowl_nhseb": ("oral_case_presentation", ("text/plain",)),
    "debatebench": ("oral_speech", ("text/plain",)),
    "odyssey_of_the_mind": ("long_term_performance", ("text/plain",)),
    "wro": ("robot_and_program", ("text/plain",)),
    "ccdc": ("defended_services_and_reports", ("text/plain",)),
}

# What the collaboration runner in src/ can actually submit today.
RUNNER_MIME_TYPES = ("text/plain",)

ADAPTATION_NOTES = {
    "slide_deck": "Official entries are slide files; the runner submits the deck as structured text.",
    "research_report_and_deck": "Official entries are a written report plus a deck; the runner submits both as text.",
    "investment_report": "Official entries are PDF reports; the runner submits the report as text.",
    "written_memorial": "Official memorials are filed as PDF; the runner submits the memorial text.",
    "written_memorandum": "Official memoranda are filed as PDF; the runner submits the memorandum text.",
    "source_code": "Official submissions are compiled and judged; the runner submits source text only.",
    "code_and_predictions": "Official entries are notebooks and prediction files; the runner submits code and results as text.",
    "oral_report_and_opposition": "Official rounds are spoken; the runner submits the argument in writing.",
    "oral_case_presentation": "Official rounds are spoken; the runner submits the presentation in writing.",
    "oral_speech": "Official speeches are spoken under time limits; the runner submits the speech text.",
    "spoken_answer": "Official answers are spoken to a moderator; the runner submits the answer text.",
    "long_term_performance": "Official solutions are performed and physically judged; the runner submits a written plan.",
    "robot_and_program": "Official runs use physical robots; the runner submits design and program text.",
    "defended_services_and_reports": "Official scoring watches live services; the runner submits written actions and reports.",
}


def benchmark_facts(competition_id: str) -> dict:
    path = BENCHMARKS / competition_id / "benchmark.json"
    if not path.is_file():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    task_types: Counter[str] = Counter()
    evaluators: Counter[str] = Counter()
    rubrics: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    for row in rows:
        if row.get("task_type"):
            task_types[row["task_type"]] += 1
        evaluation = row.get("evaluation") or {}
        if evaluation.get("evaluator_id"):
            evaluators[evaluation["evaluator_id"]] += 1
        if evaluation.get("rubric_path"):
            rubrics[evaluation["rubric_path"]] += 1
        if evaluation.get("status"):
            statuses[evaluation["status"]] += 1
    return {
        "task_types": [name for name, _ in task_types.most_common()],
        "evaluator_id": evaluators.most_common(1)[0][0] if evaluators else None,
        "rubric_path": rubrics.most_common(1)[0][0] if rubrics else None,
        "status": statuses.most_common(1)[0][0] if statuses else None,
        "row_count": len(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    registry = {spec.id: spec for spec in load_registry()}
    changed = 0
    for path in sorted(RULES.glob("*.json")):
        if path.name == "schema.json":
            continue
        competition_id = path.stem
        card = json.loads(path.read_text(encoding="utf-8"))
        facts = benchmark_facts(competition_id)
        deliverable, official_mimes = OFFICIAL_DELIVERABLES.get(
            competition_id, ("document", ("text/plain",))
        )

        submission = dict(card.get("submission") or {})
        submission["task_types"] = facts.get("task_types") or []
        submission["official_deliverable"] = deliverable
        submission["official_mime_types"] = list(official_mimes)
        submission["mime_types"] = list(RUNNER_MIME_TYPES)
        if set(official_mimes) - set(RUNNER_MIME_TYPES):
            submission["adaptation"] = ADAPTATION_NOTES.get(
                deliverable,
                "The runner submits text where the official contest collects a file.",
            )
        else:
            submission.pop("adaptation", None)

        scoring = dict(card.get("scoring") or {})
        evaluator_id = facts.get("evaluator_id")
        if evaluator_id:
            scoring["evaluator_id"] = evaluator_id
            scoring["evaluator_status"] = facts.get("status") or "unknown"
            rubric_path = facts.get("rubric_path")
            if rubric_path:
                scoring["rubric_path"] = rubric_path
            else:
                scoring.pop("rubric_path", None)
            spec = registry.get(evaluator_id)
            if spec is not None:
                scoring["evaluator_strategy"] = spec.strategy
        else:
            scoring["evaluator_id"] = None
            scoring["evaluator_status"] = "unassigned"
            scoring.pop("evaluator_strategy", None)
            scoring.pop("rubric_path", None)

        updated = dict(card)
        updated["submission"] = submission
        updated["scoring"] = scoring
        if updated == card:
            continue
        changed += 1
        print(
            f"{competition_id}: deliverable={deliverable} "
            f"evaluator={scoring['evaluator_id']} status={scoring['evaluator_status']}"
        )
        if not args.dry_run:
            path.write_text(
                json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    print(f"\n{changed} cards updated" + (" (dry run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
