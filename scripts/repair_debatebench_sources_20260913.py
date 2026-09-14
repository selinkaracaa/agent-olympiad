"""Recover explicit DebateBench source and score relationships without guessing."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.repair_data_catalog import Store
from scripts.repair_data_catalog import provenance, sync_rules
from scripts.build_data_packages import build_packages
from dataset_catalog import scorecard, update_track_index

BENCHMARK = "data/benchmarks/debatebench/benchmark.json"
SCORES = "data/raw/debatebench/scores.xlsx"
CACHE = "data/.cache/debatebench_repair_20260913"
SPEAKING_ORDER = ("PM", "LO", "DPM", "DLO", "MG", "MO", "GW", "OW")
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
ALIASES = {
    "d_oxbridge_3_round_3_cvr_cr_box_df_4_vid2txt_Jan-08-2025_-13_full": "Doxbridge 3 Round 3",
    "doxbridge_pre_wu_dc_2022_round_5": "Doxbridge Pre-WUDC 2022 Round 5",
    "doxbridge_worlds_2021_west_round_5": "Doxbridge Worlds 2021 West Round 5",
    "LSE Open 2023 Round 3 Room 2_edited": "LSE Open 2023 Round 3 Room 2",
    "lse_open_2023_round_5": "LSE Open 2023 Round 5",
}
REPORT = "data/benchmarks/debatebench_source_repair_20260913.json"
REFERENCE = "data/rubrics/debatebench_historical_scores_20260913.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stable_sha(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=True).encode())


def role_alignment(text):
    tags = [(bool(close), role.upper()) for close, role in re.findall(
        r"<(\/?)\s*(PM|LO|DPM|DLO|MG|MO|GW|OW|OG|OO|CG|CO)\s*>", text, re.I)]
    opening = [role for close, role in tags if not close]
    expected = [(close, role) for role in SPEAKING_ORDER for close in (False, True)]
    return dict(valid_role_boundaries=tags == expected, opening_role_order=opening,
                expected_speaking_order=list(SPEAKING_ORDER),
                observed_role_tags=[("/" if close else "") + role for close, role in tags],
                note="Role tags are audited without changing transcript words or guessing mislabeled speakers.")


def label_records(rows):
    scores, _ = read_scores()
    labels = {}
    for row in rows:
        title = ALIASES.get(row["title"], row["title"])
        candidates = [s for s in scores if s["Tourney"] == title]
        valid = []
        for candidate in candidates:
            values = {role: candidate.get(role) for role in SPEAKING_ORDER}
            ranking = [candidate.get(role) for role in ("First", "Second", "Third", "Fourth")]
            if not all(isinstance(v, (int, float)) and 50 <= v <= 100 for v in values.values()):
                raise ValueError(f"Incomplete speaker scores in row {candidate['excel_row']}")
            if set(ranking) != {"OG", "OO", "CG", "CO"}:
                raise ValueError(f"Invalid house ordering in row {candidate['excel_row']}")
            valid.append(dict(sheet="Sheet1", excel_row=candidate["excel_row"],
                              cell_range=f"A{candidate['excel_row']}:M{candidate['excel_row']}",
                              tournament_title=candidate["Tourney"], speaker_scores=values, house_order=ranking))
        text = (ROOT / row["solution_file"]).read_text(encoding="utf-8-sig")
        labels[row["problem_id"]] = dict(
            transcript_file=row["solution_file"], transcript_sha256=sha((ROOT / row["solution_file"]).read_bytes()),
            score_workbook=SCORES, score_workbook_sha256=sha((ROOT / SCORES).read_bytes()),
            score_column_order=["PM", "DPM", "LO", "DLO", "MG", "GW", "MO", "OW"],
            score_matching_title=title, filename_alias_applied=title != row["title"],
            identity_status="matched" if len(valid) == 1 else "ambiguous" if valid else "missing",
            selected_scores=valid[0] if len(valid) == 1 else None, candidates=valid,
            role_alignment=role_alignment(text),
            semantics="These labels describe the archived human debate. They are not gold scores for newly generated speeches.")
    return labels


def audit_labels():
    rows = read_json(ROOT / BENCHMARK)
    labels = label_records(rows)
    report = dict(visibility="judge_only", original_task="speech_score_prediction_and_speaker_house_ranking",
                  paper_url="https://arxiv.org/abs/2502.06279", records=labels)
    Store(ROOT).save(CACHE + "/labels.json", report)
    print(json.dumps(dict(records=len(labels), identity_status_counts=dict(Counter(r["identity_status"] for r in labels.values())),
                         valid_role_boundaries=sum(r["role_alignment"]["valid_role_boundaries"] for r in labels.values()),
                         role_boundary_issues=[pid for pid,r in labels.items() if not r["role_alignment"]["valid_role_boundaries"]]), indent=2))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_scores():
    # Read the publisher workbook without rewriting its bytes or using cached formulas.
    with ZipFile(ROOT / SCORES) as workbook:
        strings = ["".join(node.itertext()) for node in ET.fromstring(workbook.read("xl/sharedStrings.xml"))]
        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in sheet.findall("s:sheetData/s:row", NS):
            cells = {}
            for cell in row:
                if cell.find("s:f", NS) is not None:
                    raise ValueError("Unexpected formula in raw scores")
                value = cell.find("s:v", NS)
                if value is None:
                    continue
                value = strings[int(value.text)] if cell.get("t") == "s" else float(value.text)
                cells[re.sub(r"\d+", "", cell.get("r"))] = value
            if cells:
                rows.append(dict(excel_row=int(row.get("r")), cells=cells))
        headers = rows[0]["cells"]
        if set(headers.values()) != {"Tourney", *SPEAKING_ORDER, "First", "Second", "Third", "Fourth"}:
            raise ValueError("Score workbook columns changed")
        records = [dict(excel_row=row["excel_row"], **{headers[c]: v for c, v in row["cells"].items()}) for row in rows[1:]]
        links = [node.attrib for node in sheet.findall("s:hyperlinks/s:hyperlink", NS)]
        return records, links


def inspect():
    rows = read_json(ROOT / BENCHMARK)
    scores, links = read_scores()
    print("SCORE ROWS", len(scores), "LINKS", links)
    for row in rows:
        text = (ROOT / row["solution_file"]).read_text(encoding="utf-8-sig")
        tags = re.findall(r"</?([a-zA-Z]+)>", text)
        matches = [s for s in scores if s["Tourney"] == row["title"]]
        print(json.dumps(dict(title=row["title"], exact_score_rows=[s["excel_row"] for s in matches],
                              tag_counts=dict(Counter(tags))), ensure_ascii=True))
    print("ALL SCORE TITLES")
    for score in scores:
        print(json.dumps(dict(excel_row=score["excel_row"], title=score["Tourney"]), ensure_ascii=True))


def recover():
    cache = ROOT / CACHE
    cache.mkdir(parents=True, exist_ok=True)
    api_url = "https://huggingface.co/api/datasets/utkarsh2105/DebateBench"
    with urlopen(Request(api_url, headers={"User-Agent": "AgentOlympiad-source-audit"}), timeout=30) as response:
        api_bytes = response.read()
    metadata = json.loads(api_bytes)
    revision = metadata["sha"]
    store = Store(ROOT)
    store.save_text(CACHE + "/hf_dataset_snapshot.json", api_bytes.decode())
    results = []
    for name in ("scores.xlsx", "Cleaned Speeches.zip", "README.md"):
        url = f"https://huggingface.co/datasets/utkarsh2105/DebateBench/resolve/{revision}/" + quote(name)
        target = cache / name
        with urlopen(Request(url, headers={"User-Agent": "AgentOlympiad-source-audit"}), timeout=45) as response:
            data = response.read()
        if target.exists() and target.read_bytes() != data:
            raise ValueError("Downloaded snapshot destination differs")
        if not target.exists():
            target.write_bytes(data)
        results.append(dict(name=name, url=url, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
    archived = {}
    with ZipFile(cache / "Cleaned Speeches.zip") as archive:
        for info in archive.infolist():
            if not info.is_dir() and "__MACOSX/" not in info.filename:
                archived[Path(info.filename).name] = hashlib.sha256(archive.read(info)).hexdigest()
    comparisons = []
    for row in read_json(ROOT / BENCHMARK):
        path = ROOT / row["solution_file"]
        comparisons.append(dict(problem_id=row["problem_id"], file=row["solution_file"],
            local_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), publisher_sha256=archived.get(path.name)))
    report = dict(revision=revision, files=results, transcript_comparisons=comparisons,
        original_score_workbook_matches=(ROOT / SCORES).read_bytes() == (cache / "scores.xlsx").read_bytes())
    store.save(CACHE + "/publisher_comparison.json", report)
    print(json.dumps(dict(revision=revision, original_score_workbook_matches=report["original_score_workbook_matches"],
        transcript_exact_matches=sum(r["local_sha256"] == r["publisher_sha256"] for r in comparisons),
        transcript_count=len(comparisons)), indent=2))


def verify_motion_source(html, source):
    from bs4 import BeautifulSoup

    normalize = lambda value: " ".join(value.split())
    soup = BeautifulSoup(html, "html.parser")
    statistics = source["source_url"].rstrip("/").endswith("/motions/statistics")
    heading_selector = "span.badge.badge-secondary" if statistics else "h4.card-title"
    headings = [node for node in soup.select(heading_selector)
                if normalize(node.get_text(" ", strip=True)) == source["round_heading"]]
    if len(headings) != 1:
        raise ValueError("Official snapshot does not identify exactly one matching round")
    block = headings[0].find_parent("div", class_="list-group" if statistics else "card")
    if block is None:
        raise ValueError("Official round container is missing")
    motions = block.select("h4.mb-3.mt-1" if statistics else "li.list-group-item > div.mr-auto.lead")
    if len(motions) != 1:
        raise ValueError("Official round does not contain exactly one motion")
    if statistics:
        for short_label in motions[0].select("small"):
            short_label.decompose()
    motion = normalize(motions[0].get_text(" ", strip=True))
    if not motion or motion != normalize(source["motion"]):
        raise ValueError("Motion differs from the selected official round")
    slides = block.select(".modal-body.lead")
    if len(slides) > 1:
        raise ValueError("Multiple infoslides require explicit review")
    infoslide = normalize(slides[0].get_text(" ", strip=True)) if slides else ""
    if infoslide != normalize(source.get("infoslide", "")):
        raise ValueError("Infoslide differs from the selected official round")
    status = "published_present" if infoslide else "published_blank_or_absent"
    if source.get("infoslide_status") != status:
        raise ValueError("Infoslide status differs from the selected official round")


def prepare():
    store = Store(ROOT)
    rows = deepcopy(store.read(BENCHMARK))
    labels = label_records(rows)
    motions = store.read(CACHE + "/motions.json")
    sources = {r["canonical_title"]: r for r in motions["records"]}
    if len(sources) != len(motions["records"]) or not set(sources) <= {r["title"] for r in rows}:
        raise ValueError("Motion-source membership is ambiguous")
    publisher = store.read(CACHE + "/publisher_comparison.json")
    if not publisher["original_score_workbook_matches"]:
        raise ValueError("Local workbook differs from the publisher snapshot")
    with ZipFile(ROOT / CACHE / "Cleaned Speeches.zip") as archive:
        for row in rows:
            name = Path(row["solution_file"]).name
            original = archive.read("Cleaned Speeches/" + name).decode("utf-8-sig")
            normalized = original.replace("\r\n", "\n").replace("\r", "\n")
            if normalized != (ROOT / row["solution_file"]).read_text(encoding="utf-8-sig"):
                raise ValueError(f"Transcript differs beyond line endings: {name}")
    raw_hashes = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
                  for p in (ROOT / "data/raw/debatebench").rglob("*") if p.is_file()}
    payloads, copies, after, reviews = {}, {}, [], []
    for row in rows:
        updated = deepcopy(row)
        pid = row["problem_id"]
        label = labels[pid]
        source = sources.get(row["title"])
        token = sha(pid.encode())[:12]
        reference_path = f"data/raw/debatebench/recovered_20260913/{token}/historical_scores.json"
        payloads[reference_path] = json.dumps(dict(problem_id=pid, visibility="judge_only", **label), ensure_ascii=False, indent=2) + "\n"
        assets = deepcopy(row["assets"])
        assets.extend([
            dict(path=reference_path, role="judge_only", mime_type="application/json", sha256=sha(payloads[reference_path].encode())),
            dict(path=SCORES, role="judge_only", mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", sha256=raw_hashes[SCORES]),
        ])
        review = dict(problem_id=pid, original_task="adjudicate_archived_debate",
            paper_url="https://arxiv.org/abs/2502.06279", publisher_revision=publisher["revision"],
            current_task_policy="Existing speech-generation adaptation retained; no automatic conversion to the original adjudication task.",
            historical_score_identity=label["identity_status"],
            historical_score_rows=[c["excel_row"] for c in label["candidates"]],
            speech_role_boundaries_verified=label["role_alignment"]["valid_role_boundaries"],
            historical_reference_path=reference_path, motion_recovered=source is not None)
        limitations = ["The current task asks for new speeches, while DebateBench's original labels evaluate an archived human debate; historical scores cannot grade newly generated speeches.",
                      "An eight-speech judging protocol and transcript-only/interactive delivery have not been validated for this adaptation."]
        if source:
            html = store.path(source["snapshot_path"]).read_bytes()
            if sha(html) != source["snapshot_sha256"]:
                raise ValueError("Official motion snapshot changed")
            verify_motion_source(html, source)
            public_path = f"data/raw/debatebench/recovered_20260913/{token}/motion.txt"
            public = "Motion\n\n" + source["motion"].strip()
            if source.get("infoslide"):
                public += "\n\nInformation Slide\n\n" + source["infoslide"].strip()
            public += "\n"
            payloads[public_path] = public
            assets.append(dict(path=public_path, role="agent_visible", mime_type="text/plain", sha256=sha(public.encode())))
            snapshot = "data/raw/debatebench/recovered_20260913/sources/" + source["snapshot_sha256"][:16] + ".html"
            copies[snapshot] = dict(source=source["snapshot_path"], sha256=source["snapshot_sha256"])
            review["motion_source"] = dict(source, archived_snapshot=snapshot)
            updated.update(source_file=public_path, source_url=source["source_url"],
                           problem_description=public.rstrip(), motion=source["motion"],
                           infoslide=source.get("infoslide"), source_visibility="agent_visible_motion_only")
        else:
            limitations.append("An event-and-round verified original motion/infoslide packet is still missing.")
        if label["identity_status"] == "missing":
            limitations.append("The publisher score workbook has no matching debate row.")
        elif label["identity_status"] == "ambiguous":
            limitations.append("The publisher workbook contains two conflicting same-title debate rows; neither is selected.")
        if not label["role_alignment"]["valid_role_boundaries"]:
            limitations.append("The original transcript has incomplete, inconsistent or out-of-order speaker-role tags; no speech-label alignment was guessed.")
        updated.update(assets=assets, source_review=review,
                       asset_policy="Only the extracted official motion and infoslide are contestant inputs for the retained speech-generation task. Human transcripts and historical scores are judge-only references, not target answers for new speeches.")
        updated["evaluation"].update(evaluator_id=None, status="not_ready", limitations=limitations,
                                    historical_reference_path=reference_path,
                                    historical_score_identity=label["identity_status"])
        provenance(updated)
        after.append(updated)
        reviews.append(review)
    plan = dict(expected_rows=rows, after_rows=after, inline_files=payloads, copies=copies,
                original_raw_hashes=raw_hashes, publisher=publisher, labels=labels, reviews=reviews,
                source_research_unresolved=motions.get("unresolved", []))
    store.save(CACHE + "/plan.json", plan)
    print(json.dumps(dict(records=len(after), motions_recovered=len(sources),
                         score_identities=dict(Counter(r["identity_status"] for r in labels.values())),
                         source_snapshots=len(copies)), indent=2))


def check_packages(rows, stage):
    input_count = 0
    for layout in ("base", "last_exam"):
        cards = read_json(stage / layout / "task_cards.json")["tasks"]
        selected = {c["task_id"].split("/", 1)[1]: c for c in cards if c["task_id"].startswith("debatebench/")}
        if set(selected) != {r["problem_id"] for r in rows}:
            raise ValueError("Derived task membership changed")
        for row in rows:
            folder = stage / layout / selected[row["problem_id"]]["source_repo_path"] / "base/input"
            expected = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
            public = [a for a in row["assets"] if a["role"] == "agent_visible"]
            expected.update(Path(a["path"]).name for a in public)
            actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
            if actual != expected:
                raise ValueError("Unexpected contestant input or missing motion")
            if (folder / "problem.md").read_text(encoding="utf-8") != row["problem_description"] + "\n":
                raise ValueError("Derived prompt differs")
            transcript_hash = sha((ROOT / row["solution_file"]).read_bytes())
            for path in folder.iterdir():
                if path.is_file() and sha(path.read_bytes()) == transcript_hash:
                    raise ValueError("Full historical transcript leaked into a generation input")
            for asset in public:
                if sha((folder / Path(asset["path"]).name).read_bytes()) != asset["sha256"]:
                    raise ValueError("Published motion bytes differ")
                input_count += 1
            if layout == "last_exam":
                hidden = read_json(folder.parent.parent / "eval/reference.json")
                if hidden["evaluation"] != row["evaluation"]:
                    raise ValueError("Hidden evaluation differs")
    return input_count


def verify(plan, report):
    rows = read_json(ROOT / BENCHMARK)
    if rows != plan["after_rows"]:
        raise ValueError("Canonical readback differs")
    for path, expected in {**plan["original_raw_hashes"], **report["unrelated_canonical_hashes"]}.items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError(f"Preserved input changed: {path}")
    if label_records(plan["expected_rows"]) != plan["labels"]:
        raise ValueError("Label association changed on independent readback")
    for path, info in plan["copies"].items():
        if sha((ROOT / path).read_bytes()) != info["sha256"]:
            raise ValueError("Archived official snapshot differs")
    if read_json(ROOT / REFERENCE)["records"] != plan["labels"]:
        raise ValueError("Aggregate historical score references differ")
    original = {r["problem_id"]: r for r in plan["expected_rows"]}
    for row in rows:
        for field in ("task_type", "title", "year", "team_size", "eval_unit", "split", "gold_label", "human_baseline"):
            if row.get(field) != original[row["problem_id"]].get(field):
                raise ValueError(f"Preserved task field changed: {field}")
        if row["evaluation"]["status"] != "not_ready" or row["evaluation"]["evaluator_id"] is not None:
            raise ValueError("Source recovery must not promote evaluator readiness")
        for asset in row["assets"]:
            if sha((ROOT / asset["path"]).read_bytes()) != asset["sha256"]:
                raise ValueError("Asset hash mismatch")
        reference = read_json(ROOT / row["evaluation"]["historical_reference_path"])
        if reference != dict(problem_id=row["problem_id"], visibility="judge_only", **plan["labels"][row["problem_id"]]):
            raise ValueError("Historical reference differs")
        if row["source_review"]["motion_recovered"]:
            source = row["source_review"]["motion_source"]
            verify_motion_source((ROOT / source["archived_snapshot"]).read_bytes(), source)
    count = check_packages(rows, ROOT / "data")
    index = read_json(ROOT / "data/benchmarks/index.json")
    for layout in ("base", "last_exam"):
        catalog = read_json(ROOT / f"data/{layout}/task_cards.json")
        unrelated = [c for c in catalog["tasks"] if not c["task_id"].startswith("debatebench/")]
        if stable_sha(unrelated) != report["unrelated_cards_hashes"][layout]:
            raise ValueError("Unrelated task cards changed")
        if len(catalog["tasks"]) != index["total_records"]:
            raise ValueError("Catalog totals differ")
    if read_json(ROOT / "data/rubrics/task_scorecards/debatebench.json")["records"] != [scorecard(r, ROOT) for r in rows]:
        raise ValueError("Scorecards differ from canonical records")
    return dict(records_checked=len(rows), copied_motion_inputs_checked=count,
                archived_round_sources_checked=len(plan["copies"]),
                original_raw_files_unchanged=len(plan["original_raw_hashes"]),
                unrelated_canonical_tracks_unchanged=len(report["unrelated_canonical_hashes"]),
                global_records=index["total_records"], original_workbook_unchanged=True,
                unexpected_contestant_files=0, readiness_promotions=0, live_evaluation_performed=False)


def apply():
    store = Store(ROOT)
    plan = store.read(CACHE + "/plan.json")
    if store.read(BENCHMARK) != plan["expected_rows"]:
        raise ValueError("Canonical records changed since source review")
    if store.path(REPORT).exists():
        raise ValueError("Repair report already exists")
    for path, expected in plan["original_raw_hashes"].items():
        if store.sha(path) != expected:
            raise ValueError("Original raw material changed")
    for path in [*plan["inline_files"], *plan["copies"], REFERENCE]:
        if store.path(path).exists():
            raise ValueError(f"New repair destination is occupied: {path}")
    rows = deepcopy(plan["after_rows"])
    index = deepcopy(store.read("data/benchmarks/index.json"))
    track = next(t for t in index["olympiads"] if t["id"] == "debatebench")
    rule_path = "data/rules/debatebench/evaluation.json"
    rule = deepcopy(store.read(rule_path))
    sync_rules("debatebench", rule, rows)
    rule["dataset_source_review"] = dict(original_task="adjudicate_archived_debate",
        paper_url="https://arxiv.org/abs/2502.06279", historical_scores_path=REFERENCE,
        current_adaptation="Existing eight-speaker generation task retained; historical scores are reference-only.")
    rules = {"debatebench": {"evaluation": rule,
                **{k: deepcopy(store.read(f"data/rules/debatebench/{k}.json")) for k in ("competition", "collaboration")}}}
    catalogs = {layout: deepcopy(store.read(f"data/{layout}/task_cards.json")) for layout in ("base", "last_exam")}
    manifests = {layout: deepcopy(store.read(f"data/{layout}/input_asset_manifest.json")) for layout in catalogs}
    report = dict(operation="debatebench_source_and_historical_score_repair", timestamp_utc=store.stamp, status="preparing",
        backup=store.backup.relative_to(ROOT).as_posix(), total_records=index["total_records"],
        records_retained=len(rows), record_count_change=0, readiness_promotions=0,
        motions_recovered=sum(r["motion_recovered"] for r in plan["reviews"]),
        score_identity_counts=dict(Counter(r["identity_status"] for r in plan["labels"].values())),
        valid_role_boundaries=sum(r["role_alignment"]["valid_role_boundaries"] for r in plan["labels"].values()),
        source_revision=plan["publisher"]["revision"], reviews=plan["reviews"],
        existing_task_mode_preserved=True, source_research_unresolved=plan["source_research_unresolved"],
        unrelated_canonical_hashes={t["benchmark_path"]: store.sha(t["benchmark_path"])
                                   for t in index["olympiads"] if t["id"] != "debatebench"},
        unrelated_cards_hashes={layout: stable_sha([c for c in catalog["tasks"] if not c["task_id"].startswith("debatebench/")])
                                for layout,catalog in catalogs.items()})
    store.finish(report)
    try:
        for path, text in plan["inline_files"].items():
            store.save_text(path, text)
        for path, info in plan["copies"].items():
            payload = store.path(info["source"]).read_bytes()
            if sha(payload) != info["sha256"]:
                raise ValueError("Motion HTML source changed")
            destination = store.path(path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(payload)
            store.changes.append(dict(path=path, before_sha256=None, after_sha256=sha(payload)))
        stage = store.path(CACHE + "/packages_" + store.stamp)
        report["packages"] = build_packages(ROOT, stage, {"olympiads": [track]}, {"debatebench": rows}, rules, store.sha)
        report["staged_motion_inputs_checked"] = check_packages(rows, stage)
        for layout, catalog in catalogs.items():
            replacements = {c["task_id"]: c for c in read_json(stage / layout / "task_cards.json")["tasks"]}
            existing = {c["task_id"] for c in catalog["tasks"] if c["task_id"].startswith("debatebench/")}
            if existing != set(replacements):
                raise ValueError("Derived DebateBench membership differs")
            catalog["tasks"] = [replacements.get(c["task_id"], c) for c in catalog["tasks"]]
            manifests[layout]["files"] = [f for f in manifests[layout]["files"] if not f["task_id"].startswith("debatebench/")] + read_json(stage / layout / "input_asset_manifest.json")["files"]
        report["status"] = "applying"
        store.finish(report)
        store.save(BENCHMARK, rows)
        store.save(rule_path, rule)
        store.save(REFERENCE, dict(visibility="judge_only", records=plan["labels"],
            source_revision=plan["publisher"]["revision"], source_workbook=SCORES,
            source_workbook_sha256=plan["original_raw_hashes"][SCORES]))
        store.save("data/rubrics/task_scorecards/debatebench.json", dict(schema_version="1.1", dataset="debatebench", visibility="judge_only",
            records=[scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in rows]))
        update_track_index(index, "debatebench", rows)
        index["latest_source_repair_report"] = REPORT
        store.save("data/benchmarks/index.json", index)
        for name in ("base/tasks/debatebench", "last_exam/tasks/debatebench", "last_exam/competitions/debatebench"):
            target = store.path("data/" + name)
            source = (stage / name).resolve()
            if not source.is_relative_to(stage.resolve()):
                raise ValueError("Staging directory escape")
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
        print(json.dumps({k: report[k] for k in ("status", "backup", "records_retained", "motions_recovered", "score_identity_counts", "validation")}, indent=2))
    except Exception as error:
        report.update(status="interrupted", error=str(error))
        store.finish(report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "recover", "audit-labels", "prepare", "apply", "verify"))
    args = parser.parse_args()
    if args.mode == "verify":
        print(json.dumps(verify(read_json(ROOT / CACHE / "plan.json"), read_json(ROOT / REPORT)), indent=2))
    else:
        {"inspect": inspect, "recover": recover, "audit-labels": audit_labels, "prepare": prepare, "apply": apply}[args.mode]()
