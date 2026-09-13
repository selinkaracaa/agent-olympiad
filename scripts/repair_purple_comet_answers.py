"""Promote Purple Comet only after edition-matched official answer review.

Reads the captured review produced in data/.cache/purple_comet_review.
Raw problem PDFs, unrelated records, splits and license decisions are preserved.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.repair_data_catalog import Store, provenance, sync_rules, summary_and_figures, validate
from scripts.build_data_packages import build_packages
from dataset_catalog import scorecard, update_track_index
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts

REVIEW = "data/.cache/purple_comet_review/review_complete.json"
BENCHMARK = "data/benchmarks/purple_comet/benchmark.json"
SHORT = "data/rubrics/purple_comet_short_answers.json"
KEY = "data/rubrics/purple_comet_verified_answer_key_20260912.json"
REPORT = "data/benchmarks/purple_comet_repair_report.json"


def main():
    store = Store(ROOT)
    report = dict(operation="purple_comet_readiness_repair", timestamp_utc=store.stamp, status="started")
    try:
        reviewed = store.read(REVIEW)
        sources = {r["problem_id"]: r for r in reviewed["records"]}
        index = deepcopy(store.read("data/benchmarks/index.json"))
        benchmarks = {t["id"]: deepcopy(store.read(t["benchmark_path"])) for t in index["olympiads"]}
        rows = benchmarks["purple_comet"]
        assert len(sources) == len(rows) == 44
        assert set(sources) == {r["problem_id"] for r in rows}
        assert all(r["status"] == "verified" for r in sources.values())
        before_counts = Counter(r["evaluation"]["status"] for rs in benchmarks.values() for r in rs)
        old_short = deepcopy(store.read(SHORT))
        official = dict(rubric_id="purple_comet_verified_answer_key_20260912", dataset="purple_comet",
            kind="official_answer_key", visibility="judge_only",
            provenance=dict(authority="Purple Comet official year-and-level answer tables",
                official_index="https://www.purplecomet.org/answers", review_timestamp=reviewed["created_at_utc"]),
            scoring_basis="One point per correct answer in the complete archived paper; no timing or leaderboard tie-break simulation.",
            answers={})
        promoted, total_fixes, manifest, checks = [], [], [], []
        for row in rows:
            source = sources[row["problem_id"]]
            assert source["year"] == row["year"]
            assert source["source_file"] == row["source_file"]
            assert store.sha(row["source_file"]) == source["source_sha256"]
            answers = source["answers"]
            n = source["question_count"]
            assert set(map(int, answers)) == set(source["problem_ids"]) == set(range(1, n + 1))
            assert not source["existing_answer_differences"]
            assert not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]", source["source_text"])
            if row["evaluation"]["status"] == "ready":
                previous = {str(p["id"]): str(p["expected"]) for p in row["gold_label"]["parts"]}
                assert previous == answers, f"Existing curated answers differ: {row['problem_id']}"
            elif row["evaluation"]["status"] == "not_ready":
                promoted.append(row["problem_id"])
            else:
                raise ValueError(f"Unexpected readiness status: {row['problem_id']}")
            answer_path = f"data/raw/purple_comet/official_answers/{row['year']}/{source['level'].lower()}_answers.html"
            captured = store.path(source["answer_snapshot"]).read_bytes()
            assert hashlib.sha256(captured).hexdigest() == source["answer_sha256"]
            store.save_text(answer_path, captured.decode("utf-8"))
            if row.get("total_points") != n:
                total_fixes.append(dict(problem_id=row["problem_id"], before=row.get("total_points"), after=n))
            parts = []
            mapped = {}
            for number in range(1, n + 1):
                answer = answers[str(number)]
                assert re.fullmatch(r"\d+", answer)
                aliases = [format(int(answer), ",")] if int(answer) >= 1000 else []
                mapped[str(number)] = dict(expected=answer, aliases=aliases)
                parts.append(dict(id=str(number), expected=answer, aliases=aliases, points=1,
                    match_mode="normalized", reference=f"Official {source['answer_heading']}, problem {number}: {answer}."))
            old_short[row["problem_id"]] = mapped
            official["answers"][row["problem_id"]] = dict(year=row["year"], level=source["level"],
                question_count=n, total_points=n, answer_source=answer_path,
                answer_source_url=source["answer_url"], answer_source_sha256=source["answer_sha256"], parts=mapped)
            row["gold_label"]["parts"] = parts
            row["gold_label"]["expected_answer"] = "\n".join(f"{p['id']}. {p['expected']}" for p in parts)
            row["gold_label"]["grading_rubric"] = "One point per correct official integer answer; every printed question is scored."
            row.update(question_count=n, total_points=n, status="collected")
            row["problem_description"] = (
                f"This archived {row['year']} {source['level']} paper contains {n} numbered questions. "
                "Later editions' question counts do not apply. The attached original PDF is authoritative "
                "for formulas, superscripts, diagrams and tables; the text below is a searchable preview. "
                "Submit one numbered line per question in the form '<number>. <integer answer>'.\n\n"
                + source["source_text"].strip())
            row["assets"] = [a for a in row.get("assets", []) if a["path"] != answer_path] + [dict(
                path=answer_path, mime_type="text/html", role="judge_only", sha256=source["answer_sha256"])]
            row["evaluation"].update(evaluator_id="gold_answer_v1", status="ready", rubric_path=KEY,
                answer_key_path=KEY, answer_key_record=row["problem_id"], short_answer_source=SHORT,
                deliverable="answer_sheet", score_basis=official["scoring_basis"],
                test_scope="complete_archived_answer_sheet", question_count=n,
                limitations="Official answer-key grading covers all questions in this archived paper. Original PDFs are required for mathematical layout; live contest timing and leaderboard tie-breaks are not reproduced.")
            row.setdefault("source_review", {})["official_answers"] = dict(
                answer_url=source["answer_url"], answer_heading=source["answer_heading"],
                answer_snapshot=answer_path, answer_sha256=source["answer_sha256"],
                problem_pdf_sha256=source["source_sha256"], question_ids=list(range(1, n + 1)),
                checked="Official year/level heading; local PDF edition and level; identical complete problem/answer ID sets.")
            provenance(row)
            loaded = load_gold_parts(row["gold_label"])
            perfect = GoldAnswerEvaluator(parts=loaded, submission_text="\n".join(
                f"{p.id}. {p.expected}" for p in loaded)).evaluate()
            wrong = GoldAnswerEvaluator(parts=loaded, submission_text="\n".join(
                f"{p.id}. {int(p.expected) + 1}" for p in loaded)).evaluate()
            missing = GoldAnswerEvaluator(parts=loaded, submission_text="\n".join(
                f"{p.id}. {p.expected}" for p in loaded[1:])).evaluate()
            formatted = GoldAnswerEvaluator(parts=loaded, submission_text="\n".join(
                f"{p.id}. {int(p.expected):,}" for p in loaded)).evaluate()
            assert perfect.total_score == perfect.max_score == formatted.total_score == n
            assert wrong.total_score == 0 and missing.total_score == n - 1
            checks.append(dict(problem_id=row["problem_id"], max_score=n, perfect_score=perfect.total_score,
                all_wrong_score=wrong.total_score, first_answer_missing_score=missing.total_score,
                thousands_separator_score=formatted.total_score))
            manifest.append({k: source[k] for k in ("problem_id", "year", "level", "answer_url", "answer_heading",
                "answer_sha256", "source_file", "source_sha256", "source_pages", "question_count")})
            manifest[-1]["answer_snapshot"] = answer_path
            manifest[-1]["pdf_header_offset"] = source.get("pdf_header_offset", 0)
        assert len(promoted) == 30 and sum(r["question_count"] for r in rows) == 1050
        old_short["_comment"] = "Complete official year/level answer tables, 2005-2026. All problem IDs match archived PDFs. See purple_comet_verified_answer_key_20260912.json."
        official["coverage"] = dict(records=44, mapped_parts=1050, newly_gradeable_records=30,
            newly_added_parts=sum(sources[pid]["question_count"] for pid in promoted), unresolved_records=[])
        store.save(SHORT, old_short)
        store.save(KEY, official)
        store.save("data/raw/purple_comet/official_answers/manifest.json", dict(
            collected_at_utc=reviewed["created_at_utc"], official_index=official["provenance"]["official_index"], records=manifest))
        store.save(BENCHMARK, rows)
        rules = {t["id"]: {k: deepcopy(store.read(f"{t['rule_card_path']}/{k}.json"))
                 for k in ("competition", "collaboration", "evaluation")} for t in index["olympiads"]}
        track = next(t for t in index["olympiads"] if t["id"] == "purple_comet")
        sync_rules("purple_comet", rules["purple_comet"]["evaluation"], rows)
        store.save(f"{track['rule_card_path']}/evaluation.json", rules["purple_comet"]["evaluation"])
        store.save("data/rubrics/task_scorecards/purple_comet.json", dict(schema_version="1.1", dataset="purple_comet",
            visibility="judge_only", records=[scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in rows]))
        update_track_index(index, "purple_comet", rows)
        index["latest_readiness_repair_report"] = REPORT
        store.save("data/benchmarks/index.json", index)
        summary = summary_and_figures(store, index, benchmarks)
        stage = ROOT / "data/.cache" / f"purple_comet_packages_{store.stamp}"
        if stage.exists():
            raise RuntimeError(f"Staging path already exists: {stage}")
        report["packages"] = build_packages(ROOT, stage, index, benchmarks, rules, store.sha)
        report["validation"] = validate(store, index, benchmarks, rules, stage)
        # Official answer snapshots must remain entirely outside contestant inputs.
        for layout in ("base", "last_exam"):
            assets = json.loads((stage / layout / "input_asset_manifest.json").read_text(encoding="utf-8"))
            assert not any("/official_answers/" in a["source"] for a in assets["files"])
            target = store.path("data/" + layout)
            if target.exists():
                store.archive(target)
            source = (stage / layout).resolve()
            assert source.is_relative_to((ROOT / "data/.cache").resolve())
            os.replace(source, target)
        report.update(status="completed", competition_id="purple_comet", records=44,
            promoted_records=promoted, newly_added_answers=official["coverage"]["newly_added_parts"],
            total_answer_parts=1050, edition_total_corrections=total_fixes, grader_checks=checks,
            before_evaluation_status_counts=dict(before_counts),
            after_evaluation_status_counts=summary["evaluation_status_counts"],
            original_problem_pdfs_modified=0, split_and_license_changes=0,
            backup=store.backup.relative_to(ROOT).as_posix(), unresolved_purple_comet_records=[])
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps(dict(status=report["status"], records=44, promoted_records=len(promoted),
            newly_added_answers=report["newly_added_answers"], total_answer_parts=1050,
            edition_total_corrections=len(total_fixes), grader_scenarios=len(checks)*4,
            validation=report["validation"], evaluation_status_counts=report["after_evaluation_status_counts"],
            backup=report["backup"], original_problem_pdfs_modified=0), ensure_ascii=False, indent=2))
    except Exception as exc:
        report.update(status="interrupted", error=str(exc))
        store.finish(report)
        raise


if __name__ == "__main__":
    main()
