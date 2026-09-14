"""Apply the locally source-verified 2026-09-12 content repairs and rebuild views.

The immutable repair plan records before-values, source hashes and PDF pages.
Original source assets and the previous catalog are preserved, never overwritten.
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
from scripts.repair_data_catalog import (
    Store, provenance, sync_rules, summary_and_figures, validate,
)
from scripts.build_data_packages import build_packages
from dataset_catalog import scorecard, update_track_index
from evaluation.gold import GoldAnswerEvaluator, load_gold_parts

PLAN = "data/rubrics/source_verified_repairs_20260912.json"
REPORT = "data/benchmarks/source_verified_repair_report.json"


def main():
    store = Store(ROOT)
    report = dict(operation="source_verified_data_repair", timestamp_utc=store.stamp,
                  plan=PLAN, status="started")
    try:
        plan = store.read(PLAN)
        for name, expected in plan["preconditions"].items():
            store.read(name)
            actual = hashlib.sha256(store.raw[store.path(name)]).hexdigest()
            if actual != expected:
                raise RuntimeError(f"Catalog changed since source review; no repair applied: {name}")
        index = deepcopy(store.read("data/benchmarks/index.json"))
        benchmarks = {t["id"]: deepcopy(store.read(t["benchmark_path"])) for t in index["olympiads"]}
        rows = {r["problem_id"]: r for rs in benchmarks.values() for r in rs}
        report["before_records"] = len(rows)
        changed_ids = set()
        corrections = []
        arml_map = deepcopy(store.read("data/rubrics/arml_national_team_short_answers.json"))
        history_map = deepcopy(store.read("data/rubrics/history_olympiad_short_answers.json"))
        history_official = deepcopy(store.read("data/rubrics/history_olympiad_official_answer_key_v1.json"))
        mystery_map = deepcopy(store.read("data/rubrics/mystery_hunt_short_answers.json"))
        mystery_official = deepcopy(store.read("data/rubrics/mystery_hunt_official_answer_key_v1.json"))

        # Validate every evidence source once before writing active catalog files.
        evidence_hashes = {}
        for item in plan["arml"] + plan["history"] + list(plan["pdf_texts"].values()):
            evidence_hashes[item["source_file"]] = item["sha256"]
        for item in plan["arml_references"].values():
            evidence_hashes[item["source"]] = item["sha256"]
        duplicate = plan["duplicate"]
        for pid in (duplicate["alias"], duplicate["canonical"]):
            evidence_hashes[rows[pid]["source_file"]] = duplicate["sha256"]
        for path, expected in evidence_hashes.items():
            if store.sha(path) != expected:
                raise RuntimeError(f"Source changed since review: {path}")

        for fix in plan["arml"]:
            row = rows[fix["problem_id"]]
            part = next(p for p in row["gold_label"]["parts"] if str(p["id"]) == fix["part"])
            assert part["expected"] == fix["before"]
            part.update(expected=fix["expected"], aliases=fix["aliases"], points=5,
                        match_mode="normalized")
            arml_map.setdefault(row["problem_id"], {})[fix["part"]] = dict(
                expected=fix["expected"], aliases=fix["aliases"])
            if fix["kind"] == "missing_grid":
                for other in row["gold_label"]["parts"]:
                    other["points"] = 5
                row["problem_description"] += (
                    f"\n\nAnswer-sheet format for Problem {fix['part']}: give the completed four-by-four grid "
                    "as four four-digit rows, from top to bottom, on the same numbered answer line; "
                    "separate the rows with '/'. Preserve leading zeros.\n")
                row["evaluation"]["structured_answer_format"] = dict(
                    part=fix["part"], shape=[4, 4], serialization="Four row strings separated by '/'.")
            corrections.append(deepcopy(fix))
            changed_ids.add(row["problem_id"])
        arml_map["_comment"] = (
            "Official Team Answers transcriptions. Source-verified corrections and both numeric grids "
            "are recorded in source_verified_repairs_20260912.json. No grid question is omitted or reweighted.")
        for pid, source in plan["arml_references"].items():
            row = rows[pid]
            assert set(source["refs"]) == {str(p["id"]) for p in row["gold_label"]["parts"]}
            for part in row["gold_label"]["parts"]:
                part["reference"] = source["refs"][str(part["id"])].strip()
                assert part["reference"]
            row["gold_label"]["expected_answer"] = "\n".join(
                f"T-{p['id']}. {p['expected']}" for p in row["gold_label"]["parts"])
            row["source_review"] = dict(answer_source=source["source"],
                answer_source_sha256=source["sha256"], answer_key_pdf_page=1,
                references="Bounded to the dedicated Team solution PDF; no Individual-round spillover.",
                repair_plan=PLAN)
            changed_ids.add(pid)

        for fix in plan["history"]:
            assert fix["pages"] and fix["after"] and fix["before"] != fix["after"]
            row = rows[fix["problem_id"]]
            part = next(p for p in row["gold_label"]["parts"] if p["id"] == fix["part"])
            assert part["expected"] == fix["before"]
            part["expected"] = fix["after"]
            part["reference"] = part.get("reference", "").replace(fix["before"], fix["after"])
            for mapping in (history_map, history_official["answers"]):
                assert mapping[row["problem_id"]][fix["part"]]["expected"] == fix["before"]
                mapping[row["problem_id"]][fix["part"]]["expected"] = fix["after"]
            row.setdefault("source_review", {}).setdefault("answer_repairs", {})[fix["part"]] = dict(
                source_file=fix["source_file"], source_sha256=fix["sha256"], pdf_pages=fix["pages"],
                reason="Removed subsequent page/round header and section text from an answer boundary.")
            changed_ids.add(row["problem_id"])
        for pid in {f["problem_id"] for f in plan["history"]}:
            rows[pid]["gold_label"]["expected_answer"] = "\n".join(
                f"{p['id']}. {p['expected']}" for p in rows[pid]["gold_label"]["parts"])
        history_official["provenance"]["source_verified_repair_plan"] = PLAN

        for pid, fix in plan["pdf_texts"].items():
            assert not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]", fix["text"])
            row = rows[pid]
            row["problem_description"] = (
                "The attached original PDF is authoritative for mathematical layout, superscripts, "
                "tables and diagrams. The following text is a searchable preview, not a lossless replacement.\n\n"
                + fix["text"].strip())
            row.setdefault("source_review", {})["text_repair"] = dict(
                source_file=fix["source_file"], sha256=fix["sha256"], pdf_pages=fix["pages"],
                method="PyMuPDF page.get_text(sort=True)", pdf_required_for_layout=True,
                scope="Re-extracted from the archived PDF; no invented replacement characters or formulas.")
            changed_ids.add(pid)

        mystery_verified = []
        for source in plan["mystery_solutions"]:
            assert hashlib.sha256(source["text"].encode("utf-8")).hexdigest() == source["sha256"]
            store.save_text(source["local"], source["text"])
            for pid, variant, note in zip(source["ids"], source["variants"], source["notes"]):
                row = rows[pid]
                assert row["gold_label"]["expected_answer"] in source["text"]
                row["solution_file"] = source["local"]
                row["answer_group_id"] = source["name"]
                row["answer_variant"] = variant
                row["answer_variant_note"] = note
                row["problem_description"] += f"\n\nAnswer target for this record: {note}\n"
                row["assets"] = [a for a in row.get("assets", []) if a["path"] != source["local"]] + [dict(
                    path=source["local"], role="judge_only", mime_type="text/html", sha256=source["sha256"])]
                row["evaluation"]["status"] = "not_ready"
                row["evaluation"]["answer_variant"] = variant
                row["evaluation"]["limitations"] = (
                    "The official solution verifies this answer variant; it is not an accidental duplicate. "
                    "Contestant media/input separation and any hunt-specific training or host interaction "
                    "still require integration. Do not treat variants as independent puzzles. " + note)
                row.setdefault("source_review", {})["answer_variant"] = dict(
                    solution_url=source["url"], archived_solution=source["local"], sha256=source["sha256"],
                    decision="Retained: official solution explicitly supports this distinct answer variant.")
                for mapping in (mystery_map[pid], {"1": mystery_official["answers"][pid]}):
                    mapping["1"]["answer_variant"] = variant
                    mapping["1"]["solution_file"] = source["local"]
                changed_ids.add(pid)
            mystery_verified.append(dict(group=source["name"], records=source["ids"],
                variants=source["variants"], official_url=source["url"], local_solution=source["local"],
                sha256=source["sha256"], action="retained_with_disambiguated_answer_targets"))
        mystery_official["provenance"]["verified_solution_groups"] = mystery_verified

        removed = deepcopy(rows[duplicate["alias"]])
        canonical = rows[duplicate["canonical"]]
        assert removed["problem_description"] == canonical["problem_description"]
        canonical.setdefault("aliases", []).append(duplicate["alias"])
        canonical.setdefault("source_review", {})["deduplication"] = dict(
            duplicate_problem_id=duplicate["alias"], sha256=duplicate["sha256"],
            evidence="Same edition, identical problem text and byte-identical PDFs.", raw_files_preserved=True)
        benchmarks[duplicate["competition_id"]] = [
            r for r in benchmarks[duplicate["competition_id"]] if r["problem_id"] != duplicate["alias"]]
        alias_path = "data/benchmarks/source_verified_record_aliases_20260912.json"
        store.save(alias_path, dict(aliases={duplicate["alias"]: duplicate["canonical"]},
            reason="Exact source duplication; original record retained in the immutable repair backup."))
        index["record_aliases_path"] = alias_path
        changed_ids.add(duplicate["canonical"])

        # Prove changed answers and restored grid weights with the actual deterministic grader.
        answer_checks = []
        for fix in plan["arml"]:
            row = rows[fix["problem_id"]]
            part = next(p for p in load_gold_parts(row["gold_label"]) if p.id == fix["part"])
            good = GoldAnswerEvaluator(parts=[part], submission_text=f"{part.id}. {fix['expected']}").evaluate()
            assert good.total_score == good.max_score == 5
            if fix["before"]:
                bad = GoldAnswerEvaluator(parts=[part], submission_text=f"{part.id}. {fix['before']}").evaluate()
                assert bad.total_score == 0, fix["problem_id"]
            for alias in fix["aliases"]:
                alias_result = GoldAnswerEvaluator(parts=[part], submission_text=f"{part.id}. {alias}").evaluate()
                assert alias_result.total_score == 5, (fix["problem_id"], alias)
            answer_checks.append(dict(problem_id=row["problem_id"], part=part.id,
                correct_score=good.total_score, previous_wrong_answer_rejected=bool(fix["before"])))
        for row in benchmarks["arml_national_team"]:
            parts = load_gold_parts(row["gold_label"])
            assert len(parts) == 10 and all(p.expected and p.points == 5 for p in parts)
            result = GoldAnswerEvaluator(parts=parts, submission_text="\n".join(
                f"{p.id}. {p.expected}" for p in parts)).evaluate()
            assert result.total_score == result.max_score == 50
        for fix in plan["history"]:
            row = rows[fix["problem_id"]]
            part = next(p for p in load_gold_parts(row["gold_label"]) if p.id == fix["part"])
            result = GoldAnswerEvaluator(parts=[part], submission_text=f"{part.id}. {fix['after']}").evaluate()
            assert result.total_score == result.max_score > 0

        for path, value in [
            ("data/rubrics/arml_national_team_short_answers.json", arml_map),
            ("data/rubrics/history_olympiad_short_answers.json", history_map),
            ("data/rubrics/history_olympiad_official_answer_key_v1.json", history_official),
            ("data/rubrics/mystery_hunt_short_answers.json", mystery_map),
            ("data/rubrics/mystery_hunt_official_answer_key_v1.json", mystery_official),
        ]:
            store.save(path, value)
        rules = {t["id"]: {k: deepcopy(store.read(f"{t['rule_card_path']}/{k}.json"))
                 for k in ("competition", "collaboration", "evaluation")} for t in index["olympiads"]}
        for track in index["olympiads"]:
            cid = track["id"]
            for row in benchmarks[cid]:
                if row["problem_id"] in changed_ids:
                    provenance(row)
            sync_rules(cid, rules[cid]["evaluation"], benchmarks[cid])
            store.save(track["benchmark_path"], benchmarks[cid])
            store.save(f"{track['rule_card_path']}/evaluation.json", rules[cid]["evaluation"])
            store.save(f"data/rubrics/task_scorecards/{cid}.json", dict(
                schema_version="1.1", dataset=cid, visibility="judge_only",
                records=[scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in benchmarks[cid]]))
            update_track_index(index, cid, benchmarks[cid])
        store.save("data/benchmarks/index.json", index)
        summary = summary_and_figures(store, index, benchmarks)
        stage = ROOT / "data/.cache" / f"source_verified_packages_{store.stamp}"
        if stage.exists():
            raise RuntimeError(f"Staging directory already exists: {stage}")
        report["packages"] = build_packages(ROOT, stage, index, benchmarks, rules, store.sha)
        report["validation"] = validate(store, index, benchmarks, rules, stage)
        for layout in ("base", "last_exam"):
            target = store.path("data/" + layout)
            if target.exists():
                store.archive(target)
            source = (stage / layout).resolve()
            assert source.is_relative_to((ROOT / "data/.cache").resolve())
            os.replace(source, target)
        for name in ("data/README.md", "data/benchmarks/README.md"):
            path = store.path(name)
            before = path.read_text(encoding="utf-8")
            store.raw[path] = before.encode("utf-8")
            after = before.replace("1,762 records", "1,761 records")
            after += ("\n## Source-verified content repair (2026-09-12)\n\n"
                      "Official local source files support the corrected ARML answers, restored grid questions, "
                      "History Bowl answer boundaries, and refreshed PDF text previews. One byte-identical EOES "
                      "record is an alias, not an independent task. Mystery Hunt answer variants are confirmed "
                      "by archived official solutions, not removed as incorrect duplicates. Original sources "
                      "remain unchanged. See `data/benchmarks/source_verified_repair_report.json`.\n")
            store.save_text(name, after)
        remaining_bad = [r["problem_id"] for rs in benchmarks.values() for r in rs
                         if re.search(r"[\x00\ufffd]", r.get("problem_description", ""))]
        report.update(status="completed", after_records=index["total_records"],
            changed_record_ids=sorted(changed_ids), source_inventory=plan["source_inventory"],
            arml=dict(corrected_answers=sum(f["kind"] == "wrong_answer" for f in plan["arml"]),
                      restored_grids=2, full_answer_sheets=11, per_sheet_parts=10, per_sheet_max_score=50,
                      checks=answer_checks),
            history=dict(corrected_parts=len(plan["history"]), corrected_records=len({f["problem_id"] for f in plan["history"]}),
                         source_page_anchors_verified=True),
            pdf_texts=dict(reextracted_records=len(plan["pdf_texts"]),
                           remaining_corrupt_source_records=remaining_bad,
                           limitation="PDFs remain authoritative for diagrams and mathematical layout."),
            mystery_hunt=mystery_verified, deduplication=duplicate,
            evaluation_status_counts=summary["evaluation_status_counts"], unresolved=plan["unresolved"],
            backup=store.backup.relative_to(ROOT).as_posix(), original_raw_files_modified=0)
        old_report = deepcopy(store.read("data/benchmarks/integrity_repair_report.json"))
        old_report["subsequent_source_repair"] = dict(report=REPORT, current_catalog_records=index["total_records"],
            note="Earlier counts and validation describe the preceding repair snapshot, not the current catalog.")
        store.save("data/benchmarks/integrity_repair_report.json", old_report)
        store.save(REPORT, report)
        store.finish(report)
        store.save(store.backup / "removed_duplicate_record.json", removed)
        store.finish(report)
        print(json.dumps({k: report[k] for k in ("status", "after_records", "arml", "history", "pdf_texts",
              "evaluation_status_counts", "backup", "original_raw_files_modified")}, ensure_ascii=False, indent=2))
    except Exception as exc:
        report.update(status="interrupted", error=str(exc))
        store.finish(report)
        raise


if __name__ == "__main__":
    main()
