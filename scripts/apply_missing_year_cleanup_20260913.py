"""Apply the reviewed, source-backed year exclusions and recovered raw assets."""
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
from scripts.repair_data_catalog import (
    Store, build_packages, provenance, scorecard, summary_and_figures,
    sync_rules, update_track_index, validate,
)

PLAN = "data/.cache/missing_editions_20260913/operation_plan.json"
REPORT = "data/benchmarks/not_ready_cleanup_report.json"
EXCLUSIONS = "data/benchmarks/unavailable_year_exclusions_20260913.json"


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
    store = Store(ROOT)
    report = {
        "operation": plan["operation"], "timestamp_utc": store.stamp,
        "status": "preflight", "preservation_policy": plan["preserve_policy"],
        "backup": store.backup.relative_to(ROOT).as_posix(),
        "previous_exclusions_path": plan["prior_exclusions_path"],
        "exclusions_path": EXCLUSIONS,
        "validation_scope": "Local source, role, scorecard and package integrity; no live LLM or contest-runtime validation.",
    }
    # Detect intervening edits before writing any canonical file. Reuse the
    # reviewed snapshot rather than reparsing and overwriting a newer version.
    for name, snapshot in plan["snapshots"].items():
        path = store.path(name)
        raw = snapshot["text"].encode("utf-8")
        if digest(raw) != snapshot["sha256"] or digest(path.read_bytes()) != snapshot["sha256"]:
            raise RuntimeError(f"Concurrent edit detected; no canonical changes applied: {name}")
        store.raw[path] = raw
        store.hashes[path] = snapshot["sha256"]
        if name.endswith(".json"):
            store.parsed[path] = json.loads(raw.decode("utf-8-sig"))

    index = deepcopy(store.read("data/benchmarks/index.json"))
    benchmarks = {t["id"]: deepcopy(store.read(t["benchmark_path"])) for t in index["olympiads"]}
    rules = {
        t["id"]: {k: deepcopy(store.read(f"{t['rule_card_path']}/{k}.json"))
                  for k in ("competition", "collaboration", "evaluation")}
        for t in index["olympiads"]
    }
    original = {(cid, r["problem_id"]): deepcopy(r) for cid, rows in benchmarks.items() for r in rows}
    removed = {(r["competition_id"], r["problem_id"]) for r in plan["removed"]}
    changed = {(r["competition_id"], r["problem_id"]) for r in plan["updates"]}
    assert len(original) == plan["before_records"] == 1760
    assert len(removed) == 12 and len(changed) == 12 and not removed & changed
    assert all(original[k]["evaluation"]["status"] == "not_ready" for k in removed | changed)
    for item in plan["removed"]:
        key = (item["competition_id"], item["problem_id"])
        assert item["original_record"] == original[key]
    for item in plan["updates"]:
        cid, pid, row = item["competition_id"], item["problem_id"], item["row"]
        assert row["problem_id"] == pid and row["competition_id"] == cid
        assert row["split"] == original[cid, pid]["split"]
        assert row["license"] == original[cid, pid]["license"]
        provenance(row)
        benchmarks[cid] = [deepcopy(row) if r["problem_id"] == pid else r for r in benchmarks[cid]]
    for cid in benchmarks:
        benchmarks[cid] = [r for r in benchmarks[cid] if (cid, r["problem_id"]) not in removed]
        assert benchmarks[cid], f"Refusing to empty a track: {cid}"
    current = {(cid, r["problem_id"]): r for cid, rows in benchmarks.items() for r in rows}
    assert set(current) == set(original) - removed
    assert all(current[k] == original[k] for k in set(current) - changed)
    assert sum(r["evaluation"]["status"] == "not_ready" for r in current.values()) == 723

    # Load each source once for the copy, checking the reviewed content hash.
    copies = []
    for entry in plan["copies"] + plan["evidence_copies"]:
        src, dst = store.path(entry["source"]), store.path(entry["destination"])
        assert src.is_relative_to((ROOT / "data/.cache").resolve())
        assert dst.is_relative_to((ROOT / "data/raw").resolve()) and not dst.exists(), dst
        raw = src.read_bytes()
        assert digest(raw) == entry["sha256"], src
        if dst.suffix == ".pdf":
            assert b"%PDF-" in raw[:1024], src
        if dst.suffix == ".docx":
            assert raw[:2] == b"PK", src
        copies.append((entry, dst, raw))
    for entry in plan["quarantine"]:
        assert store.sha(entry["path"]) == entry["sha256"]
        assert not any(entry["path"] == a.get("path") for r in current.values() for a in r.get("assets", []))
        assert not any(entry["path"] in (r.get("source_file"), r.get("solution_file")) for r in current.values())

    before_counts = Counter(r["evaluation"]["status"] for r in original.values())
    report.update(before_records=len(original), before_status_counts=dict(before_counts),
                  removed_records=[{k: v for k, v in r.items() if k != "original_record"} for r in plan["removed"]],
                  repaired_records=[dict(competition_id=r["competition_id"], problem_id=r["problem_id"],
                                         evaluation_status=r["row"]["evaluation"]["status"])
                                    for r in plan["updates"]],
                  unchanged_records_verified=len(current) - len(changed),
                  previously_usable_records_preserved=sum(v for k, v in before_counts.items() if k != "not_ready"),
                  status="applying")
    # Save the full removal manifest before excluding any active record.
    store.finish(report)
    try:
        previous = deepcopy(store.read(plan["prior_exclusions_path"]))
        excluded = {
            "schema_version": "1.0", "visibility": "judge_only",
            "timestamp_utc": store.stamp,
            "previous_manifest": plan["prior_exclusions_path"],
            "restoration_policy": "All original rows and valid raw files are retained. Restore only after the missing packet/reference is supplied and contestant/judge roles are verified.",
            "records": previous["records"] + [dict(r, disposition="excluded_from_active_catalog_raw_preserved") for r in plan["removed"]],
        }
        store.save(EXCLUSIONS, excluded)
        for entry, dst, raw in copies:
            dst.parent.mkdir(parents=True, exist_ok=True)
            with dst.open("xb") as stream:
                stream.write(raw)
            store.hashes[dst] = entry["sha256"]
            store.changes.append(dict(path=entry["destination"], before_sha256=None, after_sha256=entry["sha256"]))
        for path, rubric in plan["new_rubrics"].items():
            assert sum(c["max_score"] for c in rubric["criteria"]) == rubric["total_points"]
            assert all("OFFICIAL REFERENCE:" in c["description"] for c in rubric["criteria"])
            store.save(path, rubric)
        affected = {cid for cid, _ in removed | changed}
        for track in index["olympiads"]:
            cid = track["id"]
            if cid not in affected:
                continue
            rows = benchmarks[cid]
            sync_rules(cid, rules[cid]["evaluation"], rows)
            store.save(track["benchmark_path"], rows)
            store.save(f"{track['rule_card_path']}/evaluation.json", rules[cid]["evaluation"])
            store.save(f"data/rubrics/task_scorecards/{cid}.json", dict(
                schema_version="1.1", dataset=cid, visibility="judge_only",
                records=[scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in rows]))
            update_track_index(index, cid, rows)
        assert index["total_records"] == 1748 and index["active_tracks"] == 43
        index["latest_readiness_repair_report"] = REPORT
        index["excluded_records_path"] = EXCLUSIONS
        store.save("data/benchmarks/index.json", index)
        evidence_path = "data/raw/source_verification/20260913/missing_editions_research.json"
        store.save(evidence_path, dict(
            reviewed_at_utc=store.stamp, research=plan["research"],
            imported_files=plan["copies"] + plan["evidence_copies"],
            findings="Public-source lookup is bounded, not a claim that no copy exists anywhere. HTTP errors alone did not cause deletion where a verified packet could be recovered."))

        summary = summary_and_figures(store, index, benchmarks)
        stage = store.path(f"data/.cache/packages_missing_years_{store.stamp}")
        assert not stage.exists()
        report["packages"] = build_packages(ROOT, stage, index, benchmarks, rules, store.sha)
        report["validation"] = validate(store, index, benchmarks, rules, stage)
        for layout in ("base", "last_exam"):
            target = store.path("data/" + layout)
            source = (stage / layout).resolve()
            assert source.is_relative_to((ROOT / "data/.cache").resolve())
            if target.exists():
                store.archive(target)
            os.replace(source, target)
        for item in plan["quarantine"]:
            store.archive(item["path"])

        note = (
            "\n## Missing-year cleanup (2026-09-13)\n\n"
            "Current catalog: 43 tracks, 1,748 records, including 723 not_ready records. "
            "Twelve records lacking usable packets or scoring references were excluded; all valid raw material and full original rows are retained. "
            "Seventeen original source/marking files were recovered, and the IOL 2003 solution was relinked. "
            "ARML Power 2023-2025 now have reference-anchored rubrics. ARML 2022 remains not_ready because its printed weights total 39 despite the 40-point header, and problem 16 has no printed weight. "
            "Environmental, physical, image-delivery and source-isolation limitations are not treated as reasons to erase otherwise valid sources. "
            "See `data/benchmarks/not_ready_cleanup_report.json` and `data/benchmarks/unavailable_year_exclusions_20260913.json`.\n"
        )
        for name in ("data/README.md", "data/benchmarks/README.md"):
            old = plan["snapshots"][name]["text"]
            if name == "data/README.md":
                old = old.replace("(43 tracks, 1,761 records)", "(43 tracks, 1,748 records)")
                old = old.replace("(43 tracks, 1,760 records)", "(43 tracks, 1,748 records)")
            store.save_text(name, old.rstrip() + "\n" + note)
        report.update(
            status="completed", after_records=index["total_records"], tracks=index["active_tracks"],
            evaluation_status_counts=summary["evaluation_status_counts"],
            imported_source_files=len(plan["copies"]), imported_evidence_pages=len(plan["evidence_copies"]),
            references_relinked=["iol_team_2003"], quarantined=plan["quarantine"],
            evidence_path=evidence_path,
            retained_not_ready_by_track={cid: sum(r["evaluation"]["status"] == "not_ready" for r in rows)
                                         for cid, rows in benchmarks.items()
                                         if any(r["evaluation"]["status"] == "not_ready" for r in rows)},
            retained_focus_limitations=[dict(competition_id=cid, problem_id=r["problem_id"], limitations=r["evaluation"].get("limitations"))
                                       for cid, rows in benchmarks.items() if cid in affected
                                       for r in rows if r["evaluation"]["status"] == "not_ready"],
            source_lookup_scope="Rechecked the 25 packet/reference-gap records. The other 713 previously triaged not_ready records were preserved unchanged, not re-audited as runtime-ready.",
        )
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps({k: report[k] for k in (
            "status", "before_records", "after_records", "tracks", "evaluation_status_counts",
            "imported_source_files", "unchanged_records_verified", "previously_usable_records_preserved",
            "retained_not_ready_by_track", "validation", "backup")}, ensure_ascii=False, indent=2), flush=True)
    except Exception as exc:
        report.update(status="interrupted", error=str(exc))
        store.finish(report)
        raise


if __name__ == "__main__":
    main()
