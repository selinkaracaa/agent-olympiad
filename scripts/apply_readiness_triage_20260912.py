"""Apply the reviewed single-edition exclusion and five source-text repairs.

Original raw files are retained. Derived packages are archived before replacement.
This audit does not promote tasks merely because their source files can be read.
"""

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
from scripts.build_data_packages import build_packages
from scripts.repair_data_catalog import Store, provenance, sync_rules, summary_and_figures, validate

PLAN = "data/rubrics/readiness_triage_repairs_20260912.json"
REPORT = "data/benchmarks/readiness_triage_report.json"
EXCLUSIONS = "data/benchmarks/readiness_triage_exclusions_20260912.json"
FILE_AUDIT = "data/benchmarks/readiness_file_audit_20260912.json"


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def row_digest(row):
    return digest(json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def blocker_group(cid):
    if cid in {"ijso_practical", "iol_team", "ioaa_group", "arml_power", "pumac_power"}:
        return "missing_or_incomplete_source_or_reference"
    if cid in {"mystery_hunt", "nyu_ctf_bench", "cybench", "iiot"}:
        return "contestant_asset_separation_or_runtime_integration"
    if cid in {"cfa_research_challenge", "debatebench", "eoes", "gcch_harvard", "science_olympiad", "wharton_investment"}:
        return "missing_task_context_or_numeric_scoring_integration"
    if cid in {"ccdc", "ioai_team", "odyssey_of_the_mind", "wro"}:
        return "live_physical_private_or_multimodal_protocol"
    return "requires_further_review"


def main():
    store = Store(ROOT)
    report = dict(operation="source_reverification_and_conservative_edition_exclusion",
                  timestamp_utc=store.stamp, plan=PLAN,
                  deletion_policy="Exclude only a specifically verified invalid record; never delete all not_ready records or an entire track by inference.")
    try:
        plan = store.read(PLAN)
        assert store.sha("data/benchmarks/index.json") == plan["expected_index_sha256"], "Catalog changed during review"
        index = deepcopy(store.read("data/benchmarks/index.json"))
        benchmarks = {t["id"]: deepcopy(store.read(t["benchmark_path"])) for t in index["olympiads"]}
        rules = {t["id"]: {k: deepcopy(store.read(f"{t['rule_card_path']}/{k}.json"))
                 for k in ("competition", "collaboration", "evaluation")} for t in index["olympiads"]}
        tracks = {t["id"]: t for t in index["olympiads"]}
        original = {(cid, r["problem_id"]): row_digest(r) for cid, rows in benchmarks.items() for r in rows}
        assert len(original) == plan["original_record_count"]
        for cid, expected in plan["expected_benchmark_hashes"].items():
            assert store.sha(tracks[cid]["benchmark_path"]) == expected, f"Concurrent benchmark edit: {cid}"
        removals = {(r["competition_id"], r["problem_id"]) for r in plan["removals"]}
        repaired = {(r["competition_id"], r["problem_id"]) for r in plan["repairs"]}
        by_id = {(cid, r["problem_id"]): r for cid, rows in benchmarks.items() for r in rows}
        original_gold = {key: deepcopy(by_id[key]["gold_label"]) for key in repaired}
        original_status = {key: by_id[key]["evaluation"]["status"] for key in repaired}

        # Preflight the whole bounded application before changing canonical data.
        for change in plan["repairs"]:
            key = change["competition_id"], change["problem_id"]
            assert by_id[key]["source_file"] == change["old_source_file"]
            assert store.sha(change["old_source_file"]) == change["old_source_sha256"]
            assert digest(change["new_source_text"].encode("utf-8")) == change["new_source_sha256"]
            assert "\ufffd" not in change["new_source_text"] and "\ufffd" not in change["new_problem_description"]
            destination = store.path(change["new_source_file"])
            if destination.exists():
                assert store.sha(change["new_source_file"]) == change["new_source_sha256"], "Unexpected replacement source already exists"
        for removal in plan["removals"]:
            row = by_id[(removal["competition_id"], removal["problem_id"])]
            assert row["year"] == removal["year"] == 2020
            assert not row.get("source_file") and not row.get("assets") and not row.get("problem_description")
            assert row["evaluation"]["status"] == "not_ready"
        if store.path(EXCLUSIONS).exists():
            raise RuntimeError("Exclusion manifest already exists; do not silently repeat an audit-specific removal")
        payloads = {}
        for evidence in plan["downloads"]:
            payload = store.path(evidence["source"]).read_bytes()
            assert digest(payload) == evidence["sha256"], "Evidence changed during review"
            destination = store.path(evidence["destination"])
            if destination.exists():
                assert store.sha(evidence["destination"]) == evidence["sha256"], "Conflicting archived evidence"
            else:
                payloads[evidence["destination"]] = payload

        for name, payload in payloads.items():
            destination = store.path(name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(payload)
            store.hashes[destination] = digest(payload)
            store.changes.append(dict(path=name, before_sha256=None, after_sha256=digest(payload)))

        for change in plan["repairs"]:
            row = by_id[(change["competition_id"], change["problem_id"])]
            store.save_text(change["new_source_file"], change["new_source_text"])
            row.update(source_file=change["new_source_file"], source_url=change["source_url"],
                       source_encoding="utf-8", problem_description=change["new_problem_description"])
            for asset in row.get("assets", []):
                if asset["path"] == change["old_source_file"]:
                    asset.update(path=change["new_source_file"], sha256=change["new_source_sha256"])
            provenance(row)
            row["provenance"]["source_text_repair"] = dict(
                verified_at_utc=plan["verified_at_utc"], plan=PLAN,
                previous_source_file=change["old_source_file"], previous_source_sha256=change["old_source_sha256"],
                current_source_sha256=change["new_source_sha256"],
                evidence_file=change["evidence_file"], evidence_sha256=change["evidence_sha256"],
                evidence_page=change.get("evidence_page"), notes=change["notes"],
            )

        excluded = []
        for removal in plan["removals"]:
            cid, pid = removal["competition_id"], removal["problem_id"]
            excluded.append(dict(**removal, original_record=deepcopy(by_id[(cid, pid)])))
            benchmarks[cid] = [row for row in benchmarks[cid] if row["problem_id"] != pid]
        store.save(EXCLUSIONS, dict(schema_version="1.0", visibility="maintainer_only",
                   timestamp_utc=store.stamp, restoration_policy="Original records retained verbatim; any reinstatement requires new edition evidence.", records=excluded))

        affected = {cid for cid, _ in repaired | removals}
        for cid in sorted(affected):
            rows = benchmarks[cid]
            sync_rules(cid, rules[cid]["evaluation"], rows)
            store.save(tracks[cid]["benchmark_path"], rows)
            store.save(f"{tracks[cid]['rule_card_path']}/evaluation.json", rules[cid]["evaluation"])
            store.save(f"data/rubrics/task_scorecards/{cid}.json", dict(
                schema_version="1.1", dataset=cid, visibility="judge_only",
                records=[scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in rows]))
            update_track_index(index, cid, rows)
        index["latest_readiness_repair_report"] = REPORT
        index["excluded_records_path"] = EXCLUSIONS
        store.save("data/benchmarks/index.json", index)

        after = {(cid, r["problem_id"]): r for cid, rows in benchmarks.items() for r in rows}
        assert set(after) == set(original) - removals
        for key, row in after.items():
            if key not in repaired:
                assert row_digest(row) == original[key], f"Unexpected unrelated change: {key}"
            else:
                assert row["gold_label"] == original_gold[key]
                assert row["evaluation"]["status"] == original_status[key]
                assert "\ufffd" not in row["problem_description"]
        for change in plan["repairs"]:
            assert store.sha(change["old_source_file"]) == change["old_source_sha256"]
            fresh = store.path(change["new_source_file"]).read_bytes()
            assert digest(fresh) == change["new_source_sha256"]
            assert "\ufffd" not in fresh.decode("utf-8")

        pending = [dict(competition_id=cid, problem_id=r["problem_id"], year=r.get("year"),
                        blocker_group=blocker_group(cid), disposition="retain_pending_further_integration_or_source_recovery",
                        current_reason=r["evaluation"].get("limitations") or r["evaluation"].get("reason"),
                        source_file=r.get("source_file"))
                   for cid, rows in benchmarks.items() for r in rows if r["evaluation"]["status"] == "not_ready"]
        report.update(before_records=len(original), after_records=len(after), tracks=len(benchmarks),
                      deleted_record_count=len(excluded), excluded_records=EXCLUSIONS,
                      repaired_source_records=[p["problem_id"] for p in plan["repairs"]],
                      repaired_source_record_count=len(repaired),
                      source_audit_summary=plan["source_audit_summary"],
                      audit_scope=plan["scope"],
                      remaining_not_ready=len(pending),
                      pending_by_blocker=dict(Counter(r["blocker_group"] for r in pending)),
                      pending_by_track=dict(Counter(r["competition_id"] for r in pending)),
                      pending_records=pending)
        audit = deepcopy(store.read("data/.cache/readiness_triage_20260912/file_audit.json"))
        audit.update(timestamp_utc=store.stamp, scope="Pre-repair referenced-source existence and PDF text extraction; no CTF execution, model evaluation, or full-page visual certification.",
                     source_audit_summary=plan["source_audit_summary"])
        for finding in audit["findings"]:
            change = next((p for p in plan["repairs"] if p["old_source_file"] == finding["path"]), None)
            if change:
                finding.update(disposition="repaired_in_new_canonical_source_original_preserved", replacement_path=change["new_source_file"])
            else:
                finding["disposition"] = "retain_image_pdf_requires_visual_delivery_not_evidence_of_file_corruption"
        store.save(FILE_AUDIT, audit)

        summary = summary_and_figures(store, index, benchmarks)
        stage = ROOT / "data/.cache" / f"readiness_triage_packages_{store.stamp}"
        if stage.exists():
            raise RuntimeError(f"Staging directory already exists: {stage}")
        report["packages"] = build_packages(ROOT, stage, index, benchmarks, rules, store.sha)
        report["validation"] = validate(store, index, benchmarks, rules, stage)
        report["validation"].update(only_intended_record_removed=True, unrelated_records_unchanged=True,
                                    original_raw_sources_preserved=True, repaired_source_utf8_checks=len(repaired),
                                    gold_labels_and_readiness_preserved_for_repaired_sources=True, model_calls=0)
        for layout in ("base", "last_exam"):
            target = store.path("data/" + layout)
            if target.exists():
                store.archive(target)
            source = (stage / layout).resolve()
            assert source.is_relative_to((ROOT / "data/.cache").resolve())
            os.replace(source, target)
        report.update(status="completed", evaluation_status_counts=summary["evaluation_status_counts"],
                      file_audit_report=FILE_AUDIT, backup=store.backup.relative_to(ROOT).as_posix())
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps({k: v for k, v in report.items() if k != "pending_records"}, ensure_ascii=False, indent=2), flush=True)
    except Exception as exc:
        report.update(status="interrupted", error=str(exc))
        store.finish(report)
        raise


if __name__ == "__main__":
    main()
