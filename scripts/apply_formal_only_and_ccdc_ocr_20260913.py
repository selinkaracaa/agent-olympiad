"""Apply the bounded formal-task/source repair and rebuild derived packages.

No reference programs, submissions, or test suites are executed. Practice
records and their unused source PDFs are archived, never irreversibly deleted.
"""
from __future__ import annotations

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
from scripts.build_data_packages import build_packages
from scripts.repair_data_catalog import Store, provenance, summary_and_figures, sync_rules


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    store = Store(ROOT)
    plan = store.read("data/.cache/iiot_repair_20260913/formal_ccdc_apply_plan.json")
    report = dict(operation=plan["operation"], timestamp_utc=store.stamp,
                  status="preparing", program_execution_performed=False,
                  post_write_validation_performed=False,
                  backup=store.backup.relative_to(ROOT).as_posix(), **plan["summary"])
    try:
        index = deepcopy(store.read("data/benchmarks/index.json"))
        benchmarks = {t["id"]: deepcopy(store.read(t["benchmark_path"])) for t in index["olympiads"]}
        rules = {t["id"]: {kind: deepcopy(store.read(f"{t['rule_card_path']}/{kind}.json"))
                          for kind in ("competition", "collaboration", "evaluation")}
                 for t in index["olympiads"]}
        if sum(map(len, benchmarks.values())) != plan["expected_total_records"]:
            raise RuntimeError("Catalog size changed since the repair plan; no writes applied")
        for cid, expected in plan["expected"].items():
            if benchmarks[cid] != expected:
                raise RuntimeError(f"Unexpected concurrent change in {cid}; no writes applied")
        if store.read(plan["rubric"]["path"]) != plan["rubric"]["before"]:
            raise RuntimeError("IIOT rubric changed since the source audit")

        removed_ids = {r["problem_id"] for r in plan["removed"]}
        before_ids = {r["problem_id"] for r in benchmarks["iiot"]}
        after_ids = {r["problem_id"] for r in plan["after"]["iiot"]}
        if before_ids - after_ids != removed_ids or after_ids - before_ids:
            raise RuntimeError("The plan removes something other than the seven identified practice tasks")
        for cid, rows in plan["after"].items():
            benchmarks[cid] = deepcopy(rows)
        used_sources = {r.get("source_file") for rows in benchmarks.values() for r in rows}
        used_sources.update(a["path"] for rows in benchmarks.values() for r in rows for a in r.get("assets", []))
        for item in plan["removed"]:
            if item["source_file"] in used_sources:
                raise RuntimeError("A practice PDF is also referenced by a retained record")
            if store.sha(item["source_file"]) != item["source_sha256"]:
                raise RuntimeError("A practice PDF changed since the source audit")

        payloads = {}
        for item in plan["files"]:
            data = store.path(item["source"]).read_bytes()
            if sha(data) != item["sha256"]:
                raise RuntimeError(f"Downloaded reference changed: {item['source']}")
            payloads[item["destination"]] = data
        for item in plan["inline_files"]:
            payloads[item["destination"]] = item["text"].encode("utf-8")
        for name in [*payloads, plan["exclusions_path"], plan["report_path"]]:
            if store.path(name).exists():
                raise RuntimeError(f"New destination is occupied; no writes applied: {name}")

        for cid in plan["after"]:
            sync_rules(cid, rules[cid]["evaluation"], benchmarks[cid])
            update_track_index(index, cid, benchmarks[cid])
        iiot_track = next(t for t in index["olympiads"] if t["id"] == "iiot")
        iiot_track["excluded_practice_records"] = len(removed_ids)
        iiot_track["task_scope"] = "international_final_only"
        index["excluded_practice_records_path"] = plan["exclusions_path"]
        index["latest_source_repair_report"] = plan["report_path"]
        report.update(status="applying", before_records=plan["expected_total_records"],
                      after_records=index["total_records"],
                      new_source_files=[dict(path=p, bytes=len(b), sha256=sha(b)) for p, b in payloads.items()],
                      excluded_problem_ids=sorted(removed_ids),
                      original_source_policy="Preserve formal sources; archive only unused practice PDFs.",
                      readiness_policy="No source-only repair is promoted to ready.")
        store.finish(report)

        for name, data in payloads.items():
            path = store.path(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(data)
            store.hashes[path] = sha(data)
            store.changes.append(dict(path=name, before_sha256=None, after_sha256=sha(data)))
        exclusions = deepcopy(plan["removed"])
        for item in exclusions:
            item["archived_source_file"] = (store.backup / item["source_file"]).relative_to(ROOT).as_posix()
        store.save(plan["exclusions_path"], dict(
            schema_version="1.0", policy="Exclude publisher-labeled practice tasks at user request.",
            scope="Individual tasks, not the entire 2017 edition.", records=exclusions))
        store.save(plan["rubric"]["path"], plan["rubric"]["after"])
        for cid in plan["after"]:
            track = next(t for t in index["olympiads"] if t["id"] == cid)
            store.save(track["benchmark_path"], benchmarks[cid])
            store.save(f"{track['rule_card_path']}/evaluation.json", rules[cid]["evaluation"])
            store.save(f"data/rubrics/task_scorecards/{cid}.json", dict(
                schema_version="1.1", dataset=cid, visibility="judge_only",
                records=[scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in benchmarks[cid]]))
        store.save("data/benchmarks/index.json", index)

        collection_path = "data/raw/collection_manifest.json"
        if store.path(collection_path).exists():
            collection = deepcopy(store.read(collection_path))
            if isinstance(collection.get("entries"), list):
                excluded_paths = {item["source_file"] for item in plan["removed"]}
                collection["entries"] = [entry for entry in collection["entries"]
                    if not any(entry.get(key) in excluded_paths for key in ("file", "source_file", "path"))]
                collection["practice_exclusions_path"] = plan["exclusions_path"]
                store.save(collection_path, collection)

        summary = summary_and_figures(store, index, benchmarks)
        stage = store.path(f"data/.cache/formal_ccdc_packages_{store.stamp}")
        if stage.exists():
            raise RuntimeError("Package staging destination is occupied")
        report["packages"] = build_packages(ROOT, stage, index, benchmarks, rules, store.sha)
        for layout in ("base", "last_exam"):
            target = store.path("data/" + layout)
            if target.exists():
                store.archive(target)
            source = (stage / layout).resolve()
            if not source.is_relative_to(store.path("data/.cache")):
                raise RuntimeError("Package source escaped the staging directory")
            os.replace(source, target)
        for item in plan["removed"]:
            store.archive(item["source_file"])

        for name in ("data/README.md", "data/benchmarks/README.md"):
            path = store.path(name)
            if path.exists():
                data = path.read_bytes()
                store.raw[path] = data
                text = data.decode("utf-8-sig")
                text = text.replace("1,748 records", "1,741 records", 1)
                text += ("\n\n## Formal-only IIOT and CCDC source repair (2026-09-13)\n\n"
                         "IIOT retains 31 international-final tasks; seven publisher-labeled 2017 practice tasks "
                         "are archived in the exclusion manifest. Reference programs and official subtask "
                         "weights are archived, but missing original judge material keeps the records not_ready. "
                         "Six scanned CCDC packets have automatic, page-labeled OCR transcripts; consult "
                         "the original PDFs for exact text, addresses, tables, and diagrams. CCDC 2022's "
                         "missing network map and unavailable original execution/scoring environments remain unresolved.\n\n"
                         "Report: `data/benchmarks/iiot_ccdc_repair_20260913.json`. No execution tests were run.\n")
                store.save_text(name, text)
        report.update(status="completed_with_recorded_readiness_blockers",
                      evaluation_status_counts=summary["evaluation_status_counts"],
                      unresolved=dict(iiot="Original judge data/configuration and isolated execution remain incomplete.",
                                      ccdc="Original environments/scoring services and the 2022 network map are unavailable; OCR is advisory."))
        store.save(plan["report_path"], report)
        store.finish(report)
        print(json.dumps({k: report[k] for k in (
            "status", "before_records", "after_records", "practice_removed", "iiot_after",
            "iiot_new_reference_files", "iiot_official_point_tables", "ccdc_ocr_documents",
            "ccdc_ocr_pages", "readiness_promotions", "evaluation_status_counts", "packages", "backup")}, indent=2))
    except Exception as exc:
        report.update(status="interrupted", error=str(exc))
        store.finish(report)
        raise


if __name__ == "__main__":
    main()
