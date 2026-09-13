"""Apply original CFA season materials without enabling a reconstructed task.

Only CFA canonical metadata and its derived task packages are replaced. No
submission, grading call, reference-program execution, or test suite is run.
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
import scripts.build_data_packages as builder
from scripts.repair_data_catalog import Store, sync_rules


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    store = Store(ROOT)
    plan = store.read("data/.cache/cfa_repair_20260913/apply_plan.json")
    cid = plan["competition_id"]
    benchmark_path = f"data/benchmarks/{cid}/benchmark.json"
    rule_path = f"data/rules/{cid}/evaluation.json"
    report = dict(operation=plan["operation"], timestamp_utc=store.stamp,
                  status="preparing", backup=store.backup.relative_to(ROOT).as_posix(),
                  program_execution_performed=False, post_write_validation_performed=False,
                  **plan["summary"])
    try:
        if store.read(benchmark_path) != plan["expected_rows"]:
            raise RuntimeError("CFA benchmark changed since the source audit; no writes applied")
        if store.read(rule_path) != plan["expected_rule"]:
            raise RuntimeError("CFA evaluation rules changed since the source audit")
        index = deepcopy(store.read("data/benchmarks/index.json"))
        if index.get("total_records") != plan["expected_total_records"]:
            raise RuntimeError("Global record count changed since the source audit")
        track = next(t for t in index["olympiads"] if t["id"] == cid)
        rows = deepcopy(plan["after_rows"])
        if {r["problem_id"] for r in rows} != {r["problem_id"] for r in plan["expected_rows"]}:
            raise RuntimeError("The source repair must not add or remove CFA records")
        rule = deepcopy(plan["after_rule"])
        sync_rules(cid, rule, rows)
        rules = {cid: {"evaluation": rule,
            "competition": deepcopy(store.read(f"data/rules/{cid}/competition.json")),
            "collaboration": deepcopy(store.read(f"data/rules/{cid}/collaboration.json"))}}
        cards = {layout: deepcopy(store.read(f"data/{layout}/task_cards.json"))
                 for layout in ("base", "last_exam")}
        manifests = {layout: deepcopy(store.read(f"data/{layout}/input_asset_manifest.json"))
                     for layout in ("base", "last_exam")}
        task_ids = {f"{cid}/{r['problem_id']}" for r in rows}
        for layout, catalog in cards.items():
            existing = [c["task_id"] for c in catalog["tasks"] if c["task_id"].startswith(cid + "/")]
            if len(existing) != len(task_ids) or set(existing) != task_ids:
                raise RuntimeError(f"CFA task membership differs in {layout}; stopped before writes")

        payloads = {}
        for item in plan["files"]:
            data = store.path(item["source"]).read_bytes()
            if digest(data) != item["sha256"]:
                raise RuntimeError(f"Downloaded original changed: {item['source']}")
            payloads[item["destination"]] = data
        new_paths = [*payloads, *(item["path"] for item in plan["json_files"]),
                     plan["source_manifest_path"], plan["report_path"]]
        for name in new_paths:
            if store.path(name).exists():
                raise RuntimeError(f"New destination is occupied; no writes applied: {name}")
        stage = store.path(f"data/.cache/cfa_packages_{store.stamp}")
        if stage.exists():
            raise RuntimeError("CFA staging destination is occupied")
        report.update(status="applying", new_files=new_paths,
                      modified_canonical_files=[benchmark_path, rule_path,
                          f"data/rubrics/task_scorecards/{cid}.json", "data/benchmarks/index.json"])
        store.finish(report)

        for name, data in payloads.items():
            path = store.path(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(data)
            store.hashes[path] = digest(data)
            store.changes.append(dict(path=name, before_sha256=None, after_sha256=digest(data)))
        for item in plan["json_files"]:
            store.save(item["path"], item["value"])
        store.save(plan["source_manifest_path"], dict(
            schema_version="1.0", source_policy="Original published documents only; no historical research task synthesized.",
            files=[{k: item[k] for k in ("destination", "url", "sha256")} for item in plan["files"]],
            old_timeline_url="https://www.cfatoronto.ca/docs/default-source/default-document-library/2026-research-challenge-timeline-local-competition.pdf?sfvrsn=2274141e_0",
            recovery_method="Public publisher media index supplied the migrated original PDF URL.",
            season_selection="2026 uses the Toronto host-published rules, byte-identical to the Brazil archive copy; a different Poland revision was not silently substituted.",
            information_boundary_policy="Host deadlines are recorded as deadlines, not invented valuation/information cutoffs.",
            license_policy="Existing unverified licensing is retained; no redistribution permission inferred."))
        store.save(benchmark_path, rows)
        store.save(rule_path, rule)
        store.save(f"data/rubrics/task_scorecards/{cid}.json", dict(
            schema_version="1.1", dataset=cid, visibility="judge_only",
            records=[scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in rows]))
        update_track_index(index, cid, rows)
        track["season_matched_rule_records"] = 2
        track["historical_host_timeline_records"] = 1
        index["latest_source_repair_report"] = plan["report_path"]
        store.save("data/benchmarks/index.json", index)

        # Capture generated metadata in memory while writing it, rather than
        # reopening generated files merely to inspect or verify them.
        captured = {}
        original_write_json = builder.write_json
        def capture_json(path, value):
            captured[path.relative_to(stage).as_posix()] = deepcopy(value)
            original_write_json(path, value)
        builder.write_json = capture_json
        try:
            report["cfa_packages"] = builder.build_packages(
                ROOT, stage, {"olympiads": [track]}, {cid: rows}, rules, store.sha)
        finally:
            builder.write_json = original_write_json
        for layout in ("base", "last_exam"):
            new_cards = {c["task_id"]: c for c in captured[f"{layout}/task_cards.json"]["tasks"]}
            cards[layout]["tasks"] = [new_cards.get(c["task_id"], c) for c in cards[layout]["tasks"]]
            manifests[layout]["files"] = [f for f in manifests[layout]["files"]
                if not f["task_id"].startswith(cid + "/")] + captured[f"{layout}/input_asset_manifest.json"]["files"]
        replacements = [f"base/tasks/{cid}", f"last_exam/tasks/{cid}", f"last_exam/competitions/{cid}"]
        for relative in replacements:
            target = store.path("data/" + relative)
            source = (stage / relative).resolve()
            if not source.is_relative_to(stage.resolve()):
                raise RuntimeError("Generated task path escaped the staging directory")
            if target.exists():
                store.archive(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target)
        for layout in ("base", "last_exam"):
            store.save(f"data/{layout}/task_cards.json", cards[layout])
            store.save(f"data/{layout}/input_asset_manifest.json", manifests[layout])
        report.update(status="completed_readiness_deferred", total_records=index["total_records"],
                      cfa_not_ready=19, active_record_count_change=0,
                      unresolved=["Original company research inputs and historical information boundary remain incomplete.",
                                  "Evaluation stage and authentic oral/Q&A evidence remain unresolved.",
                                  "Season-specific rules before the two repaired seasons remain unverified."])
        store.save(plan["report_path"], report)
        store.finish(report)
        print(json.dumps({k: report[k] for k in (
            "status", "total_records", "records_retained", "season_matched_records", "official_rule_pdfs",
            "host_timeline_pdfs", "new_numeric_rubrics", "readiness_promotions", "cfa_not_ready", "backup")}, indent=2))
    except Exception as exc:
        report.update(status="interrupted", error=str(exc))
        store.finish(report)
        raise


if __name__ == "__main__":
    main()
