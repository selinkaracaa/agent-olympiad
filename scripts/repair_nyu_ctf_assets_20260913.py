"""Source-preserving NYU CTF contestant attachment repair; never run challenges."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import mimetypes
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import zipfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.repair_data_catalog import Store, provenance
from scripts.build_data_packages import build_packages
from dataset_catalog import scorecard, update_track_index

CID = "nyu_ctf_bench"
BENCHMARK = f"data/benchmarks/{CID}/benchmark.json"
CACHE = "data/.cache/nyu_ctf_repair_20260913"
RAW = "data/raw/nyu_ctf_bench/separated_20260913"
REPORT = "data/benchmarks/nyu_ctf_asset_repair_20260913.json"
MANIFEST = "data/raw/nyu_ctf_bench/contestant_manifest_20260913.json"
REVISION = "4c5744f55a31a58e03d6118c9dbb1c18e5bbdfa9"
WITHHELD = {
    ("nyu_ctf_2013q-cry-slurp", "slurp.py"): "Server source embeds the exact final vault key; no publisher-redacted source is archived.",
    ("nyu_ctf_2015q-web-k_stairs", "arpahack.tar.gz"): "Server archive embeds the exact final flag in arpahack/game/util.py; original archive retained judge-only.",
}
EMBEDDED = {
    "nyu_ctf_2013q-msc-networking_1": "Publisher-listed packet capture; recovering its embedded flag is the forensic task.",
    "nyu_ctf_2013q-msc-networking_2": "Publisher-listed binary packet/process artifacts contain a process name with the flag; retain the forensic evidence.",
    "nyu_ctf_2014q-pwn-the_road_less_traveled": "Publisher-listed ELF binary; retain the original embedded string as challenge content.",
    "nyu_ctf_2015q-for-flash": "Publisher-listed disk-image archive; retain embedded filesystem evidence.",
    "nyu_ctf_2016f-cry-katy": "Publisher-listed ELF release contains the same placeholder-like flag as challenge.json; real service flag equivalence is unresolved.",
    "nyu_ctf_2016q-for-kill": "Publisher-listed packet capture; retain embedded forensic evidence.",
    "nyu_ctf_2018q-for-whyos": "Publisher-listed console log is the forensic artifact; retain original log content.",
    "nyu_ctf_2021q-for-lazy_leaks": "Publisher-listed packet capture; retain embedded forensic evidence.",
    "nyu_ctf_2023q-rev-baby_s_third": "Publisher-listed ELF binary for a strings/reversing task; retain the embedded flag.",
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe attachment path: {name}")
    if any(part.endswith((".", " ")) for part in p.parts):
        raise ValueError(f"Windows-ambiguous attachment path: {name}")
    return p.as_posix()


def locate(source, name):
    """One audited symlink stub; no heuristic search for missing attachments."""
    name = safe_name(name)
    path = source / name
    repair = None
    if not path.is_file() and source.name.lower() == "des2bites" and name.startswith("Challenge/"):
        stub = source / "Challenge"
        if stub.read_bytes() != b"dist":
            raise ValueError("DES2Bites symlink stub changed")
        path = source / "dist" / name.removeprefix("Challenge/")
        repair = dict(kind="publisher_symlink_materialized_as_text", stub=relative(stub), target="dist",
                      publisher_tree_mode="120000", publisher_revision=REVISION,
                      publisher_path="test/2019/CSAW-Quals/crypto/DES2Bites/Challenge")
    if not path.resolve().is_relative_to(source.resolve()) or path.is_symlink() or not path.is_file():
        raise ValueError(f"Missing or unsafe public file: {path}")
    return name, path, repair


def inspect_archive(path, flag):
    """Read archive members without extraction or execution; retain original bytes."""
    found, errors = [], []
    limit = 300_000_000
    total = 0
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    total += member.file_size
                    if total > limit:
                        errors.append("Archive inspection exceeded 300 MB uncompressed limit")
                        break
                    try:
                        content = archive.read(member)
                    except (RuntimeError, NotImplementedError) as error:
                        errors.append(f"{member.filename}: {type(error).__name__}")
                        continue
                    if flag in content:
                        found.append(member.filename)
        elif path.name.lower().endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")):
            with tarfile.open(path) as archive:
                for member in archive:
                    if not member.isfile():
                        continue
                    total += member.size
                    if total > limit:
                        errors.append("Archive inspection exceeded 300 MB uncompressed limit")
                        break
                    content = archive.extractfile(member).read()
                    if flag in content:
                        found.append(member.name)
    except (tarfile.TarError, zipfile.BadZipFile, OSError) as error:
        errors.append(type(error).__name__)
    return found, errors


def inspect():
    rows = read(ROOT / BENCHMARK)
    results = []
    for row in rows:
        source = ROOT / row["source_file"]
        metadata = read(source / "challenge.json")
        files = []
        for entry in metadata.get("files", []):
            name, path, repair = locate(source, entry)
            flag = metadata["flag"].encode()
            members, errors = inspect_archive(path, flag)
            files.append(dict(name=name, source=relative(path), bytes=path.stat().st_size,
                              exact_flag_in_bytes=flag in path.read_bytes(), archive_flag_members=members,
                              archive_scan_errors=errors, path_repair=repair))
        compose = [relative(p) for p in source.glob("*compose*.y*ml")]
        results.append(dict(problem_id=row["problem_id"], category=row["category"], files=files,
            box=metadata.get("box"), compose_declared=metadata.get("compose", False), compose_files=compose,
            points=metadata.get("points", metadata.get("initial")), flag_matches=row["gold_label"]["expected_answer"] == metadata["flag"],
            source_description_contains_flag=metadata["flag"] in metadata.get("description", ""),
            description_changed=row["problem_description"] != metadata.get("description", "")))
    store = Store(ROOT)
    store.save(CACHE + "/inspection.json", results)
    print(json.dumps(dict(records=len(results), files=sum(len(r["files"]) for r in results),
        attachment_bytes=sum(f["bytes"] for r in results for f in r["files"]),
        flagged=[dict(problem_id=r["problem_id"], category=r["category"], files=[f for f in r["files"]
            if f["exact_flag_in_bytes"] or f["archive_flag_members"] or f["archive_scan_errors"]]) for r in results
            if any(f["exact_flag_in_bytes"] or f["archive_flag_members"] or f["archive_scan_errors"] for f in r["files"])],
        no_files=[r["problem_id"] for r in results if not r["files"] and not r["compose_files"] and not r["box"]],
        flag_mismatches=[r["problem_id"] for r in results if not r["flag_matches"]]), indent=2))


def recover():
    store = Store(ROOT)
    sources = {}
    for name, url in {
        "README.md": f"https://raw.githubusercontent.com/NYU-LLM-CTF/NYU_CTF_Bench/{REVISION}/README.md",
        "challenge.py": f"https://raw.githubusercontent.com/NYU-LLM-CTF/NYU_CTF_Bench/{REVISION}/python/nyuctf/challenge.py",
        "des2bites_symlink.json": f"https://api.github.com/repos/NYU-LLM-CTF/NYU_CTF_Bench/contents/test/2019/CSAW-Quals/crypto/DES2Bites/Challenge?ref={REVISION}",
    }.items():
        target = f"{RAW}/source_evidence/{name}"
        if not store.path(target).exists():
            with urlopen(Request(url, headers={"User-Agent": "AgentOlympiad-source-audit"}), timeout=30) as response:
                text = response.read().decode("utf-8")
            store.save_text(target, text)
        sources[name] = dict(url=url, local_path=target, sha256=store.sha(target))
    evidence = read(store.path(sources["des2bites_symlink.json"]["local_path"]))
    if (evidence["type"], evidence["target"], evidence["sha"]) != ("symlink", "dist", "53c37a16608c014b2cf0bd2d5dfcafe953cdd857"):
        raise ValueError("Publisher symlink does not match the reviewed evidence")
    store.save(f"{RAW}/source_evidence/manifest.json", dict(
        retrieved_at_utc=store.stamp, publisher_revision=REVISION, sources=sources,
        revision_scope="Current loader and symlink evidence only; existing challenge trees are frozen by local file hashes, not asserted to be this revision."))
    print(json.dumps(dict(recovered_sources=len(sources), publisher_revision=REVISION)))


def prepare():
    store = Store(ROOT)
    if store.path(REPORT).exists():
        raise ValueError("Already applied; use verify")
    rows = store.read(BENCHMARK)
    inspection = {r["problem_id"]: r for r in store.read(CACHE + "/inspection.json")}
    evidence = store.read(f"{RAW}/source_evidence/manifest.json")
    hashes = {p: store.sha(p) for p in [BENCHMARK, f"data/rubrics/{CID}_short_answers.json",
              f"data/rubrics/{CID}_upstream_answer_key_v1.json", f"{RAW}/source_evidence/manifest.json"]}
    sources = {r["local_path"]: r["sha256"] for r in evidence["sources"].values()}
    after, copies, reviews = [], [], []
    for row in rows:
        pid = row["problem_id"]
        source = store.path(row["source_file"])
        for file in sorted(source.rglob("*")):
            if file.is_symlink():
                raise ValueError("Unexpected filesystem symlink in original archive")
            if file.is_file():
                sources[relative(file)] = store.sha(file)
        metadata_path = source / "challenge.json"
        metadata = read(metadata_path)
        if row["gold_label"]["expected_answer"] != metadata["flag"]:
            raise ValueError("Gold differs from publisher metadata")
        item = inspection[pid]
        if not item["flag_matches"]:
            raise ValueError("Inspection reported a mismatched reference")
        expected_files = {safe_name(n) for n in metadata.get("files", [])}
        if expected_files != {f["name"] for f in item["files"]}:
            raise ValueError("Attachment list changed after inspection")
        target = f"{RAW}/inputs/{hashlib.sha256(pid.encode()).hexdigest()[:16]}"
        assets, withheld, names = [], [], set()
        for f in item["files"]:
            name, path, repair = locate(source, f["name"])
            if name.casefold() in names or name.casefold() in {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}:
                raise ValueError("Input name collides with another attachment or generated instructions")
            names.add(name.casefold())
            if f["bytes"] != path.stat().st_size:
                raise ValueError("Attachment changed after inspection")
            sha = store.sha(path)
            if (pid, name) in WITHHELD:
                withheld.append(dict(name=name, path=relative(path), sha256=sha, reason=WITHHELD[(pid, name)]))
                assets.append(dict(path=relative(path), role="judge_only", sha256=sha))
                continue
            if (f["exact_flag_in_bytes"] or f["archive_flag_members"]) and pid not in EMBEDDED:
                raise ValueError("Unreviewed embedded flag")
            copy = dict(problem_id=pid, name=name, source=relative(path), destination=f"{target}/{name}",
                        sha256=sha, bytes=f["bytes"], path_repair=repair,
                        embedded_flag_review=EMBEDDED.get(pid) if f["exact_flag_in_bytes"] or f["archive_flag_members"] else None,
                        archive_scan_errors=f["archive_scan_errors"])
            copies.append(copy)
            assets.append(dict(path=copy["destination"], role="agent_visible", sha256=sha,
                               mime_type=mimetypes.guess_type(name)[0] or "application/octet-stream"))
        assets.append(dict(path=relative(metadata_path), role="judge_only", sha256=store.sha(metadata_path)))
        mode = ("service_declared" if item["compose_declared"] or item["compose_files"] else
                "host_declared_runtime_unresolved" if item["box"] else
                "static_artifacts_candidate" if item["files"] else "no_inputs_after_existing_redaction")
        limitations = ["Contestant attachments are explicitly separated and hash-verified; isolated delivery and a compatible exact-string flag evaluator have not been validated end to end."]
        if mode == "service_declared":
            limitations.append("Publisher Docker/service configuration is archived judge-side; no challenge service, network route or protected flag state was executed or validated.")
        elif mode == "host_declared_runtime_unresolved":
            limitations.append("Metadata declares a host without an archived Compose configuration; this does not establish either an active endpoint or a standalone task.")
        elif mode == "static_artifacts_candidate":
            limitations.append("No host or Compose configuration is declared in this snapshot; standalone solvability and tool dependencies remain unvalidated.")
        else:
            limitations.append("The publisher's welcome poem gives the exact flag in its description. Existing redaction is preserved; there are no other attachments or verified independent reasoning task.")
        limitations.extend(v["reason"] for v in withheld)
        if pid == "nyu_ctf_2016f-cry-katy":
            limitations.append(EMBEDDED[pid])
        if any(f["archive_scan_errors"] for f in item["files"]):
            limitations.append("The publisher password-protected ZIP remains intact; its encrypted member was not decrypted or exhaustively inspected.")
        review = dict(problem_id=pid, upstream_source_directory=row["source_file"], metadata_source=relative(metadata_path),
            input_manifest_path=MANIFEST, environment_kind=mode, target_host=metadata.get("box"),
            internal_port=metadata.get("internal_port"), compose_files=item["compose_files"],
            public_file_count=sum(a["role"] == "agent_visible" for a in assets), withheld_files=withheld,
            original_points=metadata.get("points", metadata.get("initial")),
            original_dynamic_scoring={k: metadata[k] for k in ("type", "initial", "minimum", "decay") if k in metadata},
            source_description_contains_flag=item["source_description_contains_flag"],
            existing_description_preserved=True, remaining_limitations=limitations)
        updated = deepcopy(row)
        updated.update(source_file=target, solution_file=relative(metadata_path), assets=assets, source_review=review,
            source_visibility="contestant_allowlist_directory", agent_prompt_source="problem_description",
            asset_policy="Only explicit agent_visible attachments enter task inputs. Original metadata, server trees, solvers and writeups stay judge-side. Released forensic/reversing artifacts retain their original bytes and embedded puzzle content.")
        updated["evaluation"].update(limitations=limitations, answer_match_contract="exact_string",
            score_basis="One-point benchmark flag success; publisher points/dynamic parameters retained separately in source_review. Generic normalized gold matching is not an exact-string CTF checker.")
        for part in updated["gold_label"].get("parts", []):
            part["match_mode"] = "exact"
        provenance(updated)
        after.append(updated)
        reviews.append(review)
    plan = dict(expected_hashes=hashes, original_source_hashes=sources, before_rows=rows, after_rows=after,
                copies=copies, reviews=reviews, evidence=evidence, inspection_sha256=store.sha(CACHE + "/inspection.json"))
    store.save(CACHE + "/plan.json", plan)
    print(json.dumps(dict(records=len(after), public_files=len(copies),
        original_files=len(sources), withheld=sum(len(r["withheld_files"]) for r in reviews),
        repaired_paths=sum(bool(f["path_repair"]) for f in copies),
        environment_counts=dict(Counter(r["environment_kind"] for r in reviews))), indent=2))


def check_packages(rows, data_root):
    checked = 0
    for layout in ("base", "last_exam"):
        cards = read(data_root / layout / "task_cards.json")["tasks"]
        selected = {c["problem_id"] if "problem_id" in c else c["task_id"].split("/", 1)[1]: c
                    for c in cards if c["task_id"].startswith(CID + "/")}
        if set(selected) != {r["problem_id"] for r in rows}:
            raise ValueError("Task membership changed")
        for row in rows:
            card = selected[row["problem_id"]]
            directory = data_root / layout / card["source_repo_path"] / "base/input"
            generated = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
            public = {Path(a["path"]).relative_to(row["source_file"]).as_posix(): a for a in row["assets"] if a["role"] == "agent_visible"}
            actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
            if actual != generated | set(public):
                raise ValueError(f"Unexpected or missing contestant file: {row['problem_id']}")
            if (directory / "problem.md").read_text(encoding="utf-8") != row["problem_description"] + "\n":
                raise ValueError("Prompt changed during packaging")
            for name in generated:
                if row["gold_label"]["expected_answer"].encode() in (directory / name).read_bytes():
                    raise ValueError("Final flag appears in generated instructions")
            for name, a in public.items():
                if digest(directory / name) != a["sha256"]:
                    raise ValueError("Staged attachment differs")
                checked += 1
            listed = card["input_files"] if layout == "base" else card["input"]["files"]
            prefix = "input/" if layout == "base" else "base/input/"
            if {f["path"].removeprefix(prefix) for f in listed} != actual:
                raise ValueError("Task card file listing differs from disk")
            if layout == "last_exam":
                reference = read(data_root / layout / card["source_repo_path"] / "eval/reference.json")
                if reference["evaluation"] != row["evaluation"] or reference["solution_file"] != row["solution_file"]:
                    raise ValueError("Judge reference projection differs")
    return checked


def verify(plan, report):
    rows = read(ROOT / BENCHMARK)
    if rows != plan["after_rows"]:
        raise ValueError("Canonical rows differ from reviewed plan")
    for p, expected in {**plan["original_source_hashes"], **report["preserved_hashes"]}.items():
        if digest(ROOT / p) != expected:
            raise ValueError(f"Preserved source or neighboring file changed: {p}")
    old = {r["problem_id"]: r for r in plan["before_rows"]}
    for row in rows:
        previous = old[row["problem_id"]]
        for field in ("problem_description", "year", "split", "license", "team_size", "total_points", "status"):
            if row.get(field) != previous.get(field):
                raise ValueError(f"Protected record field changed: {field}")
        if row["evaluation"]["status"] != "not_ready" or row["evaluation"]["evaluator_id"] is not None:
            raise ValueError("Unexpected readiness promotion")
        metadata = read(ROOT / row["solution_file"])
        if metadata["flag"] != row["gold_label"]["expected_answer"]:
            raise ValueError("Flag differs from upstream metadata")
        expected_public = {a["path"]: a["sha256"] for a in row["assets"] if a["role"] == "agent_visible"}
        actual_public = {relative(p): digest(p) for p in (ROOT / row["source_file"]).rglob("*") if p.is_file()}
        if actual_public != expected_public:
            raise ValueError("Raw contestant directory differs from allowlist")
        for a in row["assets"]:
            if digest(ROOT / a["path"]) != a["sha256"]:
                raise ValueError("Canonical asset hash mismatch")
    checked = check_packages(rows, ROOT / "data")
    index = read(ROOT / "data/benchmarks/index.json")
    total = sum(len(read(ROOT / t["benchmark_path"])) for t in index["olympiads"])
    if total != report["global_records"] or total != index["total_records"]:
        raise ValueError("Global record count drift")
    for layout in ("base", "last_exam"):
        for filename, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            content = read(ROOT / f"data/{layout}/{filename}")
            if filename == "task_cards.json" and (content["n_tasks"] != total or len(content[key]) != total):
                raise ValueError("Derived total differs")
            others = [v for v in content[key] if not v["task_id"].startswith(CID + "/")]
            if stable(others) != report["unrelated_derived_hashes"][layout + "/" + filename]:
                raise ValueError("Neighboring derived records changed")
            if key == "files":
                manifest_files = [v for v in content[key] if v["task_id"].startswith(CID + "/")]
                if len(manifest_files) != len(plan["copies"]):
                    raise ValueError("Input manifest attachment count differs")
                for f in manifest_files:
                    if digest(ROOT / f"data/{layout}" / f["staged"]) != f["sha256"]:
                        raise ValueError("Input manifest staged hash differs")
    if read(ROOT / f"data/rubrics/task_scorecards/{CID}.json")["records"] != [scorecard(r, ROOT) for r in rows]:
        raise ValueError("Scorecards differ")
    short = read(ROOT / f"data/rubrics/{CID}_short_answers.json")
    for row in rows:
        if short[row["problem_id"]]["1"]["match_mode"] != "exact":
            raise ValueError("Short-answer contract drift")
    if read(ROOT / MANIFEST)["files"] != plan["copies"]:
        raise ValueError("Published source manifest differs")
    return dict(records_checked=len(rows), global_records=total, public_files=len(plan["copies"]),
        copied_attachments_checked=checked, original_source_files_unchanged=len(plan["original_source_hashes"]),
        neighboring_canonical_tracks_unchanged=42, prompts_splits_licenses_and_answers_preserved=True,
        unexpected_input_files=0, flags_in_generated_instructions=0, readiness_promotions=0,
        challenge_execution_performed=False)


def apply():
    store = Store(ROOT)
    if store.path(REPORT).exists():
        raise ValueError("Already applied; use verify")
    plan = store.read(CACHE + "/plan.json")
    if digest(ROOT / CACHE / "inspection.json") != plan["inspection_sha256"]:
        raise ValueError("Reviewed attachment inspection changed")
    originals = {r["problem_id"]: r for r in plan["before_rows"]}
    for item in read(ROOT / CACHE / "inspection.json"):
        original = originals[item["problem_id"]]
        flag = original["gold_label"]["expected_answer"].encode()
        for f in item["files"]:
            _, path, _ = locate(ROOT / original["source_file"], f["name"])
            members, errors = inspect_archive(path, flag)
            if (flag in path.read_bytes(), members, errors) != (f["exact_flag_in_bytes"], f["archive_flag_members"], f["archive_scan_errors"]):
                raise ValueError("Attachment flag inspection no longer matches review")
    for p, expected in {**plan["expected_hashes"], **plan["original_source_hashes"]}.items():
        if digest(store.path(p)) != expected:
            raise ValueError(f"Source changed since review: {p}")
    for f in plan["copies"]:
        if store.path(f["destination"]).exists():
            raise ValueError("New destination occupied")
    rows = plan["after_rows"]
    index = deepcopy(store.read("data/benchmarks/index.json"))
    track = next(t for t in index["olympiads"] if t["id"] == CID)
    rules = {CID: {k: store.read(f"data/rules/{CID}/{k}.json") for k in ("competition", "collaboration", "evaluation")}}
    changing = {f"data/rubrics/{CID}_short_answers.json", f"data/rubrics/task_scorecards/{CID}.json"}
    preserve = [t["benchmark_path"] for t in index["olympiads"] if t["id"] != CID]
    for tree in ("data/rules", "data/rubrics"):
        preserve.extend(relative(p) for p in (ROOT / tree).rglob("*.json") if relative(p) not in changing)
    report = dict(operation="nyu_ctf_contestant_attachment_and_source_contract_repair", status="preparing",
        timestamp_utc=store.stamp, backup=relative(store.backup), global_records=index["total_records"],
        records_retained=len(rows), record_count_change=0, public_attachment_files=len(plan["copies"]),
        withheld_files=[dict(problem_id=r["problem_id"], **f) for r in plan["reviews"] for f in r["withheld_files"]],
        repaired_symlink_paths=sum(bool(f["path_repair"]) for f in plan["copies"]),
        environment_counts=dict(Counter(r["environment_kind"] for r in plan["reviews"])),
        preserved_hashes={p: store.sha(p) for p in preserve}, unrelated_derived_hashes={},
        source_evidence=plan["evidence"], readiness_promotions=0, execution_performed=False)
    catalogs, manifests = {}, {}
    for layout in ("base", "last_exam"):
        catalogs[layout] = deepcopy(store.read(f"data/{layout}/task_cards.json"))
        manifests[layout] = deepcopy(store.read(f"data/{layout}/input_asset_manifest.json"))
        for filename, data in (("task_cards.json", catalogs[layout]["tasks"]), ("input_asset_manifest.json", manifests[layout]["files"])):
            report["unrelated_derived_hashes"][layout + "/" + filename] = stable([v for v in data if not v["task_id"].startswith(CID + "/")])
    store.finish(report)
    try:
        for row in rows:
            store.path(row["source_file"]).mkdir(parents=True, exist_ok=True)
        for f in plan["copies"]:
            target = store.path(f["destination"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(store.path(f["source"]), target)
            if digest(target) != f["sha256"]:
                raise ValueError("Copied source differs")
            store.changes.append(dict(path=f["destination"], before_sha256=None, after_sha256=f["sha256"]))
        stage = store.path(CACHE + "/packages_" + store.stamp)
        report["packages"] = build_packages(ROOT, stage, {"olympiads": [track]}, {CID: rows}, rules, store.sha)
        report["staging_attachment_checks"] = check_packages(rows, stage)
        for layout in catalogs:
            replacements = {r["task_id"]: r for r in read(stage / layout / "task_cards.json")["tasks"]}
            if set(replacements) != {r["task_id"] for r in catalogs[layout]["tasks"] if r["task_id"].startswith(CID + "/")}:
                raise ValueError("Existing task membership differs")
            catalogs[layout]["tasks"] = [replacements.get(r["task_id"], r) for r in catalogs[layout]["tasks"]]
            manifests[layout]["files"] = [v for v in manifests[layout]["files"] if not v["task_id"].startswith(CID + "/")] + read(stage / layout / "input_asset_manifest.json")["files"]
        report["status"] = "applying"
        store.finish(report)
        short = deepcopy(store.read(f"data/rubrics/{CID}_short_answers.json"))
        for row in rows:
            short[row["problem_id"]]["1"]["match_mode"] = "exact"
        store.save(f"data/rubrics/{CID}_short_answers.json", short)
        store.save(BENCHMARK, rows)
        store.save(f"data/rubrics/task_scorecards/{CID}.json", dict(schema_version="1.1", dataset=CID,
            visibility="judge_only", records=[scorecard(r, ROOT) for r in rows]))
        update_track_index(index, CID, rows)
        index["latest_source_repair_report"] = REPORT
        store.save("data/benchmarks/index.json", index)
        store.save(MANIFEST, dict(visibility="maintainer_only", source_policy="Publisher challenge.json files allowlist with two reviewed server-source exclusions.",
            files=plan["copies"], records=plan["reviews"], original_source_hashes=plan["original_source_hashes"]))
        for name in (f"base/tasks/{CID}", f"last_exam/tasks/{CID}", f"last_exam/competitions/{CID}"):
            target = store.path("data/" + name)
            source = (stage / name).resolve()
            if not source.is_relative_to(stage.resolve()):
                raise ValueError("Staging path escaped")
            if target.exists():
                store.archive(target)
            shutil.copytree(source, target)
        for layout in catalogs:
            store.save(f"data/{layout}/task_cards.json", catalogs[layout])
            store.save(f"data/{layout}/input_asset_manifest.json", manifests[layout])
        report["validation"] = verify(plan, report)
        report["status"] = "completed_source_repair_readiness_deferred"
        store.save(REPORT, report)
        store.finish(report)
        print(json.dumps({k: report[k] for k in ("status", "backup", "public_attachment_files", "environment_counts", "validation")}, indent=2))
    except Exception as error:
        report.update(status="interrupted", error=str(error))
        store.finish(report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "recover", "prepare", "apply", "verify"))
    args = parser.parse_args()
    if args.mode == "verify":
        print(json.dumps(verify(read(ROOT / CACHE / "plan.json"), read(ROOT / REPORT)), indent=2))
    else:
        {"inspect": inspect, "recover": recover, "prepare": prepare, "apply": apply}[args.mode]()
