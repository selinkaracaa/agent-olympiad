"""Apply source-verified HMMT Team references, preserving original problem PDFs.

Uses the reviewed, judge-only plan rather than guessing answers from filenames.
Rebuilds derived catalogs and performs offline data/prompt checks, never LLM calls.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from dataset_catalog import scorecard, update_track_index
from evaluation.models import load_rubric
from evaluation.rubric_llm import RubricDocumentEvaluator
from scripts.build_data_packages import build_packages
from scripts.repair_data_catalog import Store, provenance, sync_rules, summary_and_figures, validate


PLAN = "data/rubrics/hmmt_team/official_reference_plan_20260912.json"
REPORT = "data/benchmarks/hmmt_team_repair_report.json"
LIMITATIONS = [
    "Proof grading uses an LLM and benchmark-defined partial credit, not deterministic answer matching or a recovered official partial-credit marking scheme. No live LLM grading accuracy was validated.",
    "Official PDFs are authoritative. Extracted text may flatten mathematical notation or omit diagrams. The current text-only judge does not attach official solution PDFs; ambiguous formulas or diagram-dependent arguments require PDF-aware or manual review.",
    "The current text judge clips submission text at 16000 characters. Longer proof submissions require a compatible PDF-aware or manual evaluation path.",
    "Official timing, proctoring, hand-in procedures and human grading are not reproduced. Printed raw marks are not sweepstakes-normalized scores.",
]
DIAGRAM_2015 = (
    "The 2015 problem sheet requires appropriate, sufficiently large, in-scale, clearly labeled diagrams for geometry problems (examples: 2, 4, 5), with a 2-point deduction for noncompliance. "
    "Apply this per-problem deduction only when the submitted diagram or its absence is observable; otherwise flag the requirement as unverified, not satisfied. Do not deduct twice or below zero."
)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def rubric_for(item):
    limits = list(LIMITATIONS)
    if item["year"] == 2015:
        limits.append(DIAGRAM_2015)
    criteria = []
    for part in item["parts"]:
        pages = f"{part['solution_page_start']}-{part['solution_page_end']}"
        description = (
            f"Grade problem {part['id']} only, from 0 to {part['points']} printed raw points. "
            "Require a complete, valid proof or justification for full credit, including when the requested result is numerical. "
            "Accept mathematically valid alternative proofs; the official reference is an example, not a required method. "
            "Award integer partial credit only for independently justified progress and identify the established claims and remaining gaps. "
            "Give zero for an absent, irrelevant or unsupported response. Do not award full credit for a correct final answer alone. "
            "This partial-credit policy is a benchmark adaptation, not an official detailed marking scheme. "
            "If the transcription makes a formula or diagram ambiguous, report the limitation rather than invent missing mathematics. "
            f"Authoritative judge-only solution: {item['solution_file']}, PDF pages {pages}. "
        )
        if item["year"] == 2015:
            description += DIAGRAM_2015 + " "
        description += (
            "The complete extracted reference for this problem follows inside this criterion so it is not lost to the separate reference-text length limit. "
            "PDF notation and figures take precedence over this text preview.\n\n"
            "OFFICIAL REFERENCE TEXT (JUDGE ONLY):\n" + part["reference_text"]
        )
        criteria.append(dict(id=f"problem_{part['id']}", name=f"Problem {part['id']}",
                             max_score=part["points"], min_score=0, observable=True,
                             description=description))
    return dict(
        rubric_id=f"hmmt_team_{item['year']}_official_proofs_v1",
        title=f"HMMT Team {item['year']}: official problem weights and proof references",
        visibility="judge_only", dataset="hmmt_team", total_points=item["total_points"],
        criteria=criteria, not_observable_from_deck=limits,
        scoring_basis="Sum of printed per-problem maxima; benchmark-defined proof partial credit; no normalization.",
        official_solution_file=item["solution_file"], official_solution_url=item["solution_url"],
        official_solution_sha256=item["solution_sha256"], source_verification_plan=PLAN,
    )


def main():
    store = Store(ROOT)
    report = dict(operation="hmmt_team_official_reference_repair", timestamp_utc=store.stamp,
                  source_verification_plan=PLAN, original_problem_pdfs="preserved",
                  grading_validation_scope="Offline reference delivery and data consistency only; no model accuracy claim.")
    try:
        plan = store.read(PLAN)
        items = {item["problem_id"]: item for item in plan["records"]}
        index = deepcopy(store.read("data/benchmarks/index.json"))
        benchmarks = {t["id"]: deepcopy(store.read(t["benchmark_path"])) for t in index["olympiads"]}
        rules = {t["id"]: {k: deepcopy(store.read(f"{t['rule_card_path']}/{k}.json"))
                 for k in ("competition", "collaboration", "evaluation")} for t in index["olympiads"]}
        rows = benchmarks["hmmt_team"]
        track = next(t for t in index["olympiads"] if t["id"] == "hmmt_team")
        assert set(items) == {r["problem_id"] for r in rows}
        assert sorted(i["year"] for i in items.values()) == list(range(2013, 2027))
        before = Counter(r["evaluation"]["status"] for rs in benchmarks.values() for r in rs)
        report["before_evaluation_status_counts"] = dict(before)
        report["before_hmmt_team_status_counts"] = dict(Counter(r["evaluation"]["status"] for r in rows))
        downloads, rubrics = {}, {}

        # Complete all source guards before changing the canonical rows.
        for row in rows:
            item = items[row["problem_id"]]
            assert row["year"] == item["year"] and row["source_file"] == item["source_file"]
            assert store.sha(item["source_file"]) == item["source_sha256"], "Original problem PDF changed"
            assert str(item["year"]) in item["source_intro"] and str(item["year"]) in item["solution_intro"]
            assert "Team" in item["solution_intro"]
            assert [p["id"] for p in item["parts"]] == [str(i) for i in range(1, 11)]
            assert sum(p["points"] for p in item["parts"]) == item["total_points"]
            for part in item["parts"]:
                assert part["points"] == part["source_points"]
                assert digest(part["reference_text"].encode("utf-8")) == part["reference_sha256"]
                assert len(part["reference_text"]) > len(part["problem_statement"]) + 80
                assert 1 <= part["solution_page_start"] <= part["solution_page_end"] <= item["solution_page_count"]
            target = store.path(item["solution_file"])
            if target.exists():
                assert store.sha(item["solution_file"]) == item["solution_sha256"], "Existing solution PDF changed"
            else:
                payload = store.path(item["download_path"]).read_bytes()
                assert digest(payload) == item["solution_sha256"], "Downloaded solution PDF changed"
                assert payload.find(b"%PDF-", 0, 1024) >= 0
                downloads[item["solution_file"]] = payload
            rubric_path = f"data/rubrics/hmmt_team/{item['year']}_official_proofs_v1.json"
            rubrics[rubric_path] = rubric_for(item)

        for path, payload in downloads.items():
            target = store.path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(payload)
            store.hashes[target] = digest(payload)
            store.changes.append(dict(path=path, before_sha256=None, after_sha256=digest(payload)))
        for path, rubric in rubrics.items():
            store.save(path, rubric)

        transitions = []
        for row in rows:
            item = items[row["problem_id"]]
            evaluation = row["evaluation"]
            old_status = evaluation["status"]
            rubric_path = f"data/rubrics/hmmt_team/{item['year']}_official_proofs_v1.json"
            row.update(solution_file=item["solution_file"], solution_url=item["solution_url"],
                       source_url=item["solution_url"].replace("/solutions.pdf", "/problems.pdf"),
                       question_count=item["question_count"], total_points=item["total_points"], season=item["season"])
            row["season_evidence"] = (
                "Both official packets identify HMMT Spring 2021, March 06, 2021; the upstream archive path still uses feb."
                if item["year"] == 2021 else "The official problem and solution packet headings identify the February edition."
            )
            label = "Spring" if item["season"] == "spring" else "February"
            prompt = (
                f"HMMT {label} {item['year']} Team Round: 10 proof/justification problems; {item['total_points']} printed raw points.\n"
                "Submit a numbered proof packet, with a full justification for each attempted problem even when the requested result is numerical. "
                "Use the attached original problem PDF as authoritative for formulas, figures and contest instructions; the text below is only a preview.\n"
            )
            if item["year"] == 2015:
                prompt += (
                    "For geometry problems, include sufficiently large, in-scale, clearly labeled diagrams as appropriate. "
                    "The official packet specifies a 2-point deduction for failing these requirements.\n"
                )
            body = row.get("problem_description", "")
            marker = "\n[Archived problem text]\n"
            if body.startswith("HMMT ") and marker in body:
                body = body.split(marker, 1)[1]
            row["problem_description"] = prompt + marker + body
            by_path = {a["path"]: a for a in row.get("assets", [])}
            for path, mime in ((item["solution_file"], "application/pdf"), (rubric_path, "application/json")):
                by_path[path] = dict(path=path, mime_type=mime, role="judge_only", sha256=store.sha(path))
            row["assets"] = list(by_path.values())
            evaluation.pop("rubric_paths", None)
            evaluation.update(
                evaluator_id="rubric_llm_v1", status="ready_with_limitations", rubric_path=rubric_path,
                judge_assets=[item["solution_file"], rubric_path], deliverable="numbered_proof_packet",
                limitations=deepcopy(rubrics[rubric_path]["not_observable_from_deck"]),
                score_basis="Printed official per-problem raw marks, summed without normalization. Proof partial credit is benchmark-defined, not official deterministic scoring.",
                official_problem_points={p["id"]: p["points"] for p in item["parts"]},
                reference_delivery="Full extracted per-problem references embedded in rubric criterion descriptions, outside the separate 12000-character reference-text cap.",
                source_verification_plan=PLAN,
            )
            gold = row.setdefault("gold_label", {})
            gold.update(expected_answer=None,
                        grading_rubric="Use the edition-specific proof rubric and original official solution PDF; no short-answer matching.",
                        parts=[dict(id=p["id"], points=p["points"], answer_type="proof", expected=None,
                                    reference=f"See complete official reference in rubric criterion problem_{p['id']}; {item['solution_file']}, pages {p['solution_page_start']}-{p['solution_page_end']}.")
                               for p in item["parts"]])
            provenance(row)
            row["provenance"]["official_solution_verification"] = dict(
                source_plan=PLAN, verified_at_utc=plan["verified_at_utc"], solution_url=item["solution_url"],
                correspondence="Edition headings, all ten question IDs, problem statements and printed weights matched.",
                scope="Packet correspondence and reference availability, not independent proof verification or grading accuracy.",
            )
            transitions.append(dict(problem_id=row["problem_id"], before=old_status, after=evaluation["status"],
                                    total_points=row["total_points"], question_count=row["question_count"]))

        sync_rules("hmmt_team", rules["hmmt_team"]["evaluation"], rows)
        store.save(track["benchmark_path"], rows)
        store.save(f"{track['rule_card_path']}/evaluation.json", rules["hmmt_team"]["evaluation"])
        store.save("data/rubrics/task_scorecards/hmmt_team.json", dict(
            schema_version="1.1", dataset="hmmt_team", visibility="judge_only",
            records=[scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in rows]))
        update_track_index(index, "hmmt_team", rows)
        index["latest_readiness_repair_report"] = REPORT
        store.save("data/benchmarks/index.json", index)

        # Offline check: all references, including the last problem, survive in
        # the actual structured-rubric prompt. This makes no paid model request.
        reference_checks = 0
        for row in rows:
            item = items[row["problem_id"]]
            rubric = load_rubric(store.path(row["evaluation"]["rubric_path"]))
            assert rubric.total_points == row["total_points"]
            judge = RubricDocumentEvaluator(request_fn=lambda request: None, rubric=rubric,
                                            task_text=row["problem_description"], submission_text="Offline prompt audit only.")
            prompt = judge._user_prompt()
            structured, _ = json.JSONDecoder().raw_decode(prompt.split("STRUCTURED RUBRIC:\n\n", 1)[1])
            assert len(structured["criteria"]) == 10
            for part, criterion in zip(item["parts"], structured["criteria"]):
                assert criterion["id"] == f"problem_{part['id']}"
                assert criterion["max_score"] == part["points"]
                assert part["reference_text"] in criterion["description"]
                reference_checks += 1
            assert all(not p.get("expected") for p in row["gold_label"]["parts"])

        summary = summary_and_figures(store, index, benchmarks)
        stage = ROOT / "data/.cache" / f"hmmt_team_packages_{store.stamp}"
        if stage.exists():
            raise ValueError(f"Staging directory already exists: {stage}")
        report["packages"] = build_packages(ROOT, stage, index, benchmarks, rules, store.sha)
        report["validation"] = validate(store, index, benchmarks, rules, stage)
        hidden_hashes = {store.sha(path) for row in rows for path in row["evaluation"]["judge_assets"]}
        manifest = json.loads((stage / "base/input_asset_manifest.json").read_text(encoding="utf-8"))
        assert not any(a["sha256"] in hidden_hashes for a in manifest["files"]), "Judge reference entered contestant assets"
        report["validation"].update(hmmt_team_rubrics_loaded=len(rows), complete_problem_references_in_prompt=reference_checks,
                                    judge_reference_assets="excluded_from_contestant_inputs", source_pdf_hashes="matched_reviewed_originals",
                                    model_calls=0)
        for layout in ("base", "last_exam"):
            target = store.path("data/" + layout)
            if target.exists():
                store.archive(target)
            source = (stage / layout).resolve()
            assert source.is_relative_to((ROOT / "data/.cache").resolve())
            os.replace(source, target)

        report.update(status="completed", records=index["total_records"], tracks=len(benchmarks),
                      newly_archived_solution_pdfs=len(downloads), repaired_not_ready=sum(t["before"] == "not_ready" for t in transitions),
                      hmmt_team_sessions=len(rows), official_problem_references=reference_checks,
                      transitions=transitions, evaluation_status_counts=summary["evaluation_status_counts"],
                      remaining_not_ready=summary["evaluation_status_counts"].get("not_ready", 0),
                      limitations=LIMITATIONS, backup=store.backup.relative_to(ROOT).as_posix())
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    except Exception as exc:
        report.update(status="interrupted", error=str(exc))
        store.finish(report)
        raise


if __name__ == "__main__":
    main()
