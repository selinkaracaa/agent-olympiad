"""Archive publisher-linked ABC materials without inventing judge readiness.

Consumes the curated download plan. Updates only the selected record and its
derived cards. No compiler, submission, test runner, or network call is invoked.
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
from dataset_catalog import scorecard
from scripts.repair_data_catalog import Store


def digest(data):
    return hashlib.sha256(data).hexdigest()


def selected(items, key, value):
    matches = [item for item in items if item.get(key) == value]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {key}={value}; found {len(matches)}")
    return matches[0]


def main():
    store = Store(ROOT)
    plan = store.read("data/.cache/iiot_repair_20260913/abc_apply_plan.json")
    pid = plan["target_problem_id"]
    task_id = "iiot/" + pid
    report = dict(operation="iiot_abc_publisher_source_repair", timestamp_utc=store.stamp,
                  problem_id=pid, program_execution_performed=False,
                  backup=store.backup.relative_to(ROOT).as_posix(), status="preparing")
    try:
        rows = deepcopy(store.read(plan["benchmark_path"]))
        if digest(store.raw[store.path(plan["benchmark_path"])]) != plan["expected_benchmark_sha256"]:
            raise RuntimeError("IIOT benchmark changed since the source audit; no writes applied")
        before = selected(rows, "problem_id", pid)
        if before != plan["before_row"]:
            raise RuntimeError("Selected IIOT record changed since the source audit")
        row = deepcopy(plan["after_row"])

        # Load only metadata that this bounded repair needs to transform.
        score_path = "data/rubrics/task_scorecards/iiot.json"
        scorecards = deepcopy(store.read(score_path))
        cards = {layout: deepcopy(store.read(f"data/{layout}/task_cards.json"))
                 for layout in ("base", "last_exam")}
        manifests = {layout: deepcopy(store.read(f"data/{layout}/input_asset_manifest.json"))
                     for layout in ("base", "last_exam")}
        base_card = selected(cards["base"]["tasks"], "task_id", task_id)
        last_card = selected(cards["last_exam"]["tasks"], "task_id", task_id)
        relative = Path(last_card["source_repo_path"])
        if relative != Path(base_card["source_repo_path"]):
            raise RuntimeError("The two task directories do not agree")
        reference_path = (Path("data/last_exam") / relative / "eval/reference.json").as_posix()
        reference = deepcopy(store.read(reference_path))

        # Prepare all new bytes before changing canonical metadata. Existing raw
        # files are never overwritten; every destination must stay in the repo.
        payloads = {}
        for item in plan["files"]:
            data = store.path(item["source"]).read_bytes()
            if digest(data) != item["sha256"]:
                raise RuntimeError(f"Downloaded material changed: {item['source']}")
            payloads[item["destination"]] = data
        for item in plan["inline_files"]:
            payloads[item["destination"]] = item["text"].encode("utf-8")
        mirror = plan["mirror_file"]
        payloads[mirror["destination"]] = store.path(mirror["source"]).read_bytes()

        template_files = []
        for asset in row["assets"]:
            if asset["role"] != "agent_visible" or asset["path"] == row["source_file"]:
                continue
            subpath = Path(asset["path"]).relative_to(Path(row["source_file"]).parent)
            template_files.append(subpath.as_posix())
            for layout in ("base", "last_exam"):
                destination = (Path("data") / layout / relative / "base/input" / subpath).as_posix()
                payloads[destination] = payloads[asset["path"]]
                manifests[layout]["files"].append(dict(
                    task_id=task_id, source=asset["path"], sha256=asset["sha256"],
                    staged=(relative / "base/input" / subpath).as_posix()))

        for path in payloads:
            if store.path(path).exists():
                raise RuntimeError(f"New destination is occupied; stopped before writes: {path}")
        if store.path(plan["report_path"]).exists():
            raise RuntimeError("A repair report already exists; this operation is not a blind rerun")

        before.clear()
        before.update(row)
        base_card.update(title=row["title"], source_url=row["source_url"],
                         evaluation=deepcopy(row["evaluation"]), solution_file=row["solution_file"])
        last_card.update(title=row["title"], source_url=row["source_url"])
        for subpath in template_files:
            base_card["input_files"].append(dict(name=Path(subpath).name,
                path="input/" + subpath, description="Agent-visible input"))
            last_card["input"]["files"].append(dict(name=Path(subpath).name, path="base/input/" + subpath))
        base_card["input_files"].sort(key=lambda item: item["path"])
        last_card["input"]["files"].sort(key=lambda item: item["path"])
        reference.update(solution_file=row["solution_file"], evaluation=deepcopy(row["evaluation"]),
                         evaluator_id=None, evaluator_status="not_ready")
        replacement = scorecard(row, ROOT, read_json=store.read, hash_file=store.sha)
        old_scorecard = selected(scorecards["records"], "problem_id", pid)
        old_scorecard.clear()
        old_scorecard.update(replacement)

        # Save the intended operation before applying it. All replacements use
        # Store's backup and concurrent-edit guard; new source bytes use xb.
        report.update(status="applying", new_files=[dict(path=p, sha256=digest(b), bytes=len(b))
                      for p, b in payloads.items()],
                      metadata_files=[plan["benchmark_path"], score_path, reference_path]
                      + [f"data/{layout}/{name}.json" for layout in ("base", "last_exam")
                         for name in ("task_cards", "input_asset_manifest")])
        store.finish(report)
        for path, data in payloads.items():
            destination = store.path(path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(data)
            store.hashes[destination] = digest(data)
            store.changes.append(dict(path=path, before_sha256=None, after_sha256=digest(data)))
        store.save(plan["benchmark_path"], rows)
        store.save(score_path, scorecards)
        store.save(reference_path, reference)
        for layout in ("base", "last_exam"):
            store.save(f"data/{layout}/task_cards.json", cards[layout])
            store.save(f"data/{layout}/input_asset_manifest.json", manifests[layout])
        report.update(status="source_repair_completed_readiness_deferred", official_test_pairs=26,
                      reference_programs=3, contestant_templates=2, official_max_score=100,
                      evaluator_status="not_ready", unresolved=row["evaluation"]["limitations"],
                      record_count_change=0, readiness_count_change=0,
                      post_write_validation_performed=False,
                      note="No original test grouping, checker, limits, or acceptance was invented. "
                           "Other records and all existing source files are retained.")
        store.save(plan["report_path"], report)
        store.finish(report)
        print(json.dumps({k: report[k] for k in (
            "status", "problem_id", "official_test_pairs", "reference_programs",
            "contestant_templates", "official_max_score", "evaluator_status", "backup",
            "program_execution_performed", "post_write_validation_performed")}, indent=2))
    except Exception as exc:
        report.update(status="interrupted", error=str(exc))
        store.finish(report)
        raise


if __name__ == "__main__":
    main()
