"""Repair historical IOAI source text, edition contracts, and score semantics."""
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
from urllib.request import Request, urlopen
from zipfile import ZipFile

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.repair_data_catalog import Store, provenance, sync_rules
from scripts.build_data_packages import build_packages
from dataset_catalog import scorecard, update_track_index

CID = "ioai_team"
BENCHMARK = "data/benchmarks/ioai_team/benchmark.json"
CACHE = "data/.cache/ioai_repair_20260913"
RECOVERED = "data/raw/ioai/Team-Challenge/recovered_20260913"
REPORT = "data/benchmarks/ioai_source_repair_20260913.json"
RULES_URL = "https://ioai-official.org/wp-content/uploads/2025/08/Contest-Rules-for-IOAI-2025-version-2.3-1.pdf"
GUIDE_URL = "https://ioai-official.org/wp-content/uploads/2025/06/2025-IOAI-Team-Challenge-Factory-of-the-Future-Grand-Challenge-.pdf"
BUNDLE_URL = "https://ioai-official.org/wp-content/uploads/2025/06/Practical-Round-problems.zip"
UPSTREAM = "https://api.github.com/repos/galbot-ioai/physics_sim_edu"
RUBRICS = {2024: "data/rubrics/ioai_team_2024_official_scoring_v1.json",
           2025: "data/rubrics/ioai_team_2025_official_scoring_protocol_v1.json"}


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def stable(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=True).encode())


def nonspacing(text):
    return re.sub(r"\s+", "", text).replace("\u200b", "")


def download(url, name, limit=160_000_000):
    target = ROOT / CACHE / name
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(Request(url, headers={"User-Agent": "AgentOlympiad-source-audit"}), timeout=60) as response:
            payload = response.read(limit + 1)
        if len(payload) > limit:
            raise ValueError("Source exceeds bounded download size")
        with target.open("xb") as stream:
            stream.write(payload)
    return dict(url=url, cache_path=target.relative_to(ROOT).as_posix(),
                sha256=digest(target), bytes=target.stat().st_size)


def extract_pages(row):
    with pymupdf.open(ROOT / row["source_file"]) as document:
        # Sorting repairs the 2024 spacing; the 2025 table order must stay unchanged.
        pages = [p.get_text(sort=row["year"] == 2024).replace("\u200b", "").strip() for p in document]
    original = row["problem_description"].split("\n\n--- Lyrics / brief ---\n", 1)[0]
    if nonspacing("".join(pages)) != nonspacing(original):
        raise ValueError("Extraction changed non-whitespace source content")
    return pages


def recover():
    store = Store(ROOT)
    rows = store.read(BENCHMARK)
    sources = {"rules_2025": download(RULES_URL, "rules_2025.pdf"),
               "guide_2025": download(GUIDE_URL, "guide_2025.pdf"),
               "bundle_2024": download(BUNDLE_URL, "practical_2024.zip"),
               "tasks_page_2024": download("https://ioai-official.org/2024-tasks/", "tasks_2024.html"),
               "guide_page_2025": download("https://ioai-official.org/team-challenge/", "team_2025.html"),
               "upstream_branches": download(UPSTREAM + "/branches?per_page=100", "upstream_branches.json")}
    branches = read(ROOT / sources["upstream_branches"]["cache_path"])
    revision = next(b["commit"]["sha"] for b in branches if b["name"] == "master")
    sources["upstream_tree"] = download(UPSTREAM + f"/git/trees/{revision}?recursive=1", "upstream_tree.json")
    sources["upstream_commit"] = download(UPSTREAM + f"/commits/{revision}", "upstream_commit.json")
    sources["upstream_license"] = download(f"https://raw.githubusercontent.com/galbot-ioai/physics_sim_edu/{revision}/LICENSE", "upstream_LICENSE.txt")
    tree = read(ROOT / sources["upstream_tree"]["cache_path"])
    if tree["truncated"]:
        raise ValueError("Incomplete upstream tree metadata")
    row24, row25 = sorted(rows, key=lambda r: r["year"])
    if digest(ROOT / row25["source_file"]) != sources["guide_2025"]["sha256"]:
        raise ValueError("Official 2025 guide differs from the local original")
    matches = []
    with ZipFile(ROOT / sources["bundle_2024"]["cache_path"]) as bundle:
        members = {i.filename: i for i in bundle.infolist() if not i.is_dir() and not i.filename.startswith("__MACOSX/")}
        public = [a for a in row24["assets"] if a["role"] == "agent_visible"]
        for asset in public:
            suffix = asset["path"].split("/problems/", 1)[1]
            if suffix not in members or sha(bundle.read(suffix)) != digest(ROOT / asset["path"]):
                raise ValueError(f"Publisher bundle asset differs: {suffix}")
            matches.append(dict(path=asset["path"], member=suffix, sha256=digest(ROOT / asset["path"])))
        if set(members) != {m["member"] for m in matches}:
            raise ValueError("Publisher bundle and contestant asset sets differ")
    rules_pdf = pymupdf.open(ROOT / sources["rules_2025"]["cache_path"])
    first = rules_pdf[0].get_text(sort=True)
    if "Version 2.4 (August 3, 2025)" not in first:
        raise ValueError("Verify the actual rules cover, not the filename version")
    rules_pdf.close()
    for row in rows:
        pages = extract_pages(row)
        store.save(CACHE + f"/pages_{row['year']}.json", pages)
        with pymupdf.open(ROOT / row["source_file"]) as document:
            chosen = range(len(document)) if row["year"] == 2024 else (0, 1, 5, 21)
            for page in chosen:
                document[page].get_pixmap(dpi=110).save(ROOT / CACHE / f"qa_{row['year']}_{page + 1:02}.png")
    with pymupdf.open(ROOT / sources["rules_2025"]["cache_path"]) as document:
        for page in (0, 7, 8):
            document[page].get_pixmap(dpi=110).save(ROOT / CACHE / f"qa_rules_2025_{page + 1:02}.png")
    upstream = dict(repository="https://github.com/galbot-ioai/physics_sim_edu", revision=revision,
                    observed_branch="master", guide_branch="ioai/master",
                    guide_branch_currently_present=any(b["name"] == "ioai/master" for b in branches),
                    commit_date=read(ROOT / sources["upstream_commit"]["cache_path"])["commit"]["committer"]["date"],
                    original_contest_revision_verified=False, implementation_archived=False,
                    runtime_executed=False, current_entry_paths=[t for t in tree["tree"] if t["path"] in
                        ("ioai/main.py", "ioai/main_referee.py", "ioai/referee/referee.py", "LICENSE")],
                    license_note="The observed public repository license restricts use and redistribution; public visibility is not a redistribution grant.")
    evidence = dict(sources=sources, publisher_bundle_matches=matches, upstream=upstream,
                    official_2025_guide_matches=True, rules_2025_cover_version="2.4 (August 3, 2025)",
                    rules_2025_url_filename_version="2.3", source_text_nonspacing_preserved=True)
    store.save(CACHE + "/evidence.json", evidence)
    print(json.dumps(dict(publisher_assets_checked=len(matches), source_snapshots=len(sources),
                         rules_cover=evidence["rules_2025_cover_version"], upstream=upstream), indent=2))


def task_contract(row, evidence):
    contract = dict(problem_id=row["problem_id"], year=row["year"],
                    authority="Selected edition only; the original task PDF controls exact requirements.",
                    task_source=row["source_file"], source_sha256=digest(ROOT / row["source_file"]))
    if row["year"] == 2024:
        contract.update(official_minutes=240, deliverable="cover_image_and_music_video_with_process_documentation",
            required_artifacts=["Framed cover image at least 1024 by 1024 pixels", "47-second video exported from NeuralFrames without upscaling",
                "Image AI/non-AI tool usage and prompting strategy", "Video style, included objects, extra tools and timeline screenshots"],
            tools=dict(image="Free AI or non-AI image editing tools; entirely non-AI images are permitted.",
                provided="Basic Midjourney via Discord on monitored screens; NeuralFrames model-training credits.",
                video="Render entirely in NeuralFrames, one tab at a time; no subsequent video editing.",
                supplementary="The task allows additional free AI tools and LLMs for concepts and workflow, and artist images from the web."),
            raw_task_maxima=dict(image_cover=40, music_video=40), ranking_weight_ratio=dict(image_cover=40, music_video=60),
            final_ranking_formula=None, rubric_pages=[2, 3, 4, 5])
    else:
        contract.update(official_minutes=None, deliverable="robot_control_program_for_factory_navigation_and_manipulation",
            required_artifacts=["Program Galbot to locate and organize warehouse objects while avoiding obstacles"],
            exact_submission_schema=None, numeric_scoring=None,
            tools=dict(environment="The guide identifies the Galbot MuJoCo-based simulator.",
                contest_access="Machine count, permitted sites and tools require the task-specific announcements."),
            collaboration="Team members may cooperate; external hall communication is prohibited.",
            translation="The organizer translation service is available; this is not an exclusive website allowlist.",
            items="Apply the Team Challenge item policy referencing Individual/GAITE supplies, not their entire technical environment.",
            appeals="The team leader may appeal from round start until one hour after round end.",
            rules_source=f"{RECOVERED}/rules_2025_v2_4.pdf", rules_sections=["3", "2.13"],
            rules_cover_version=evidence["rules_2025_cover_version"],
            guide_example_urls=["https://github.com/galbot-ioai/physics_sim_edu/blob/ioai/master/examples/ioai/ioai_grasp_env.py",
                               "https://github.com/galbot-ioai/physics_sim_edu/blob/ioai/master/examples/ioai/ioai_nav_env.py"],
            pdf_rendering_note="On guide page 6 the old Issac Sim heading is struck through; the replacement paragraph specifies MuJoCo. Plain extraction does not preserve strike-through or executable code layout.",
            historical_environment_verified=False)
    return contract


def fix_rubrics(original, evidence):
    result = deepcopy(original)
    rubric = result[2024]
    rubric.update(task_weights=dict(image_cover=40, music_video=60), task_weight_unit="relative_final_ranking_weight",
        raw_task_maxima=dict(image_cover=40, music_video=40), total_points_basis="sum_of_raw_criterion_maxima_not_final_ranking",
        final_ranking_formula=None)
    rubric["limitations"][0] = ("Each raw task rubric has a 40-point maximum; the final-ranking image/video weight ratio is 40:60. "
        "The retained 80-point total is an unweighted sum of raw criterion maxima, not an official final-ranking scale. "
        "The complete scaling and jury/peer aggregation formula remains unresolved.")
    rubric["provenance"][0]["supports"] = ["criterion maxima", "raw task maxima of 40 each", "final-ranking weight ratio of 40:60"]
    rubric["provenance"][0]["source_pages"] = [1, 2, 3, 4, 5]
    source = result[2025]["provenance"][0]
    source.update(title="Contest Rules for IOAI 2025, cover version 2.4 (August 3, 2025)",
                  path=f"{RECOVERED}/rules_2025_v2_4.pdf", sha256=evidence["sources"]["rules_2025"]["sha256"],
                  source_pages=[1, 8, 9], filename_version_warning="URL says 2.3; rendered cover says 2.4.")
    result[2025]["source_review"] = dict(upstream_implementation=evidence["upstream"],
        current_public_implementation_is_not_verified_historical_judge=True)
    result[2025]["limitations"].append("A current upstream simulator and referee are identified, but the original contest revision, licensing, scene assets and scoring equivalence are not verified.")
    return result


def fix_rules(original, rows, contracts):
    rules = deepcopy(original)
    competition = rules["competition"]
    competition["execution"] = dict(official_minutes=None, rules_edition="selected_historical_task",
        required_selectors=["problem_id", "year", "task_contract"],
        official_minutes_by_year={str(r["year"]): contracts[r["problem_id"]]["official_minutes"] for r in rows})
    competition["resources"] = dict(policy="Selected edition's attached task_contract.json and original task PDF.",
        internet="edition_and_task_specific", calculator="edition_specific_item_policy", code_execution="edition_specific_environment",
        provided_materials_only=None, provided_materials_only_scope="No universal restriction; 2024 expressly permits some external tools and artist images.")
    competition["human_constraints"] = ["Use only the selected edition's source-verified task contract.",
        "The 2024 creative-media task and 2025 robotics task have different tools, outputs and scoring.",
        "Benchmark collaboration overlays and action names do not establish official tool permissions."]
    competition["rules_text"] = ("IOAI historical team tasks. Apply the task_contract.json for the selected problem_id and year, "
        "together with that edition's original task PDF. In 2024, teams have four hours to produce a cover image, a music video "
        "and the required process documentation using the task's creative-tool permissions. In 2025, teams program Galbot for "
        "warehouse navigation and manipulation; the historical runtime and exact submission interface remain unresolved. "
        "A prose report does not substitute for the required media or robot program. Never import a different edition's "
        "tool restrictions, timing, scoring or submission format. Do not access judge-only solutions or claim unobserved execution.")
    competition["deliverable"] = dict(shared=True, task_types=["team_challenge"], official_deliverable="edition_specific_task_artifacts",
        answer_format="Follow the selected task_contract.json; media/program artifacts and their required documentation are not interchangeable.",
        mime_types=["application/octet-stream"], official_mime_types=None,
        by_problem_id={pid: c["deliverable"] for pid, c in contracts.items()})
    competition["provenance"]["source_review"] = dict(reviewed_at="2026-09-13", report=REPORT,
        applicability="Only the two cataloged historical editions; previous future-edition defaults are superseded, not deleted from source archives.",
        source_files=[r["source_file"] for r in rows] + [f"{RECOVERED}/rules_2025_v2_4.pdf"],
        runtime_validated=False)
    competition["provenance"]["rules_text_source"] = "historical_task_contracts_20260913"
    competition["provenance"]["superseded_sources"] = competition["provenance"]["sources"]
    competition["provenance"]["sources"] = [dict(title=f"IOAI {r['year']} original team task", local_file=r["source_file"],
        url=r["source_url"], authority="official", edition=r["year"], sha256=digest(ROOT / r["source_file"])) for r in rows] + [
        dict(title="Contest Rules for IOAI 2025, rendered cover version 2.4", local_file=f"{RECOVERED}/rules_2025_v2_4.pdf",
             url=RULES_URL, authority="official", edition=2025, sections=["3", "2.13"])]
    competition["provenance"]["proxy_limitations"] = ["Media generation services and historical robot execution are not reproduced.",
        "Historical task-specific outputs and final-ranking rules must not be replaced with a generic text response."]
    competition["provenance"]["research_confidence"] = "source_contract_verified_runtime_unverified"
    method = rules["collaboration"]
    method["rule_sections"] = dict(competition_format=["Apply the selected historical team task and its four-member roster."],
        timeline=["2024: four hours. 2025: exact duration remains unspecified. Runner turns are not official elapsed time."],
        resource_policy=["Use the selected task_contract.json. Permissions vary by edition and task."],
        collaboration_protocol=["Keep collaboration within the selected edition's permitted team and official channels."],
        integrity_and_compliance=["Protect judge-only solutions and do not claim unavailable actions or outside assistance."],
        deliverable_format=[competition["deliverable"]["answer_format"]],
        evaluation_criteria=["Use the selected record's rubric and score basis. Both historical evaluators remain not_ready."],
        runtime_limitations=competition["provenance"]["proxy_limitations"])
    method["agent_constraints"] = [
        "Apply the selected historical task_contract.json; do not import rules from another year or contest."
        if line.startswith(("Banned during", "Do not generalize Individual")) else line
        for line in method["agent_constraints"]]
    evaluation = rules["evaluation"]
    sync_rules(CID, evaluation, rows)
    scoring = evaluation["scoring"]
    mechanics = dict(completeness="edition_specific_incomplete_final_aggregation", source_refs=[r["source_file"] for r in rows],
        mechanics=["2024: image/video raw maxima 40 each, with a separate final-ranking weight ratio of 40:60.",
                   "2025: task-specific robotics performance; no validated historical numeric scoring adapter."],
        tie_breakers=[], unresolved=["Final jury/peer aggregation for 2024; historical environment and scoring equivalence for 2025."])
    scoring["official_scoring"] = mechanics
    scoring["official_performance"] = dict(mechanics, mode="edition_specific", unit="task_artifact",
        repository_evaluator_id=None, repository_evaluator_status="not_ready")
    scoring["current_repository_availability"].update(required_selectors=["problem_id", "year", "task_contract"],
        proxy_limitations=competition["provenance"]["proxy_limitations"],
        submission_adaptation="No text-only equivalent of the historical media or robot execution has been validated.")
    evaluation["submission"]["adaptation"] = scoring["current_repository_availability"]["submission_adaptation"]
    evaluation["submission"]["max_count_basis"] = "benchmark_overlay_not_verified_official_submission_limit"
    evaluation["evaluation_guidance"] = ("Resolve evaluator, rubric and score basis from the selected historical record. "
        "2024 requires actual image/video artifacts; 2025 requires robot-control execution. Both remain not_ready. "
        "Keep performance, rule compliance and collaboration diagnostics separate; do not invent execution or final-ranking scores.")
    return rules


def prepare():
    store = Store(ROOT)
    before = deepcopy(store.read(BENCHMARK))
    if {r["year"] for r in before} != {2024, 2025} or len(before) != 2:
        raise ValueError("Historical repair membership changed")
    evidence = store.read(CACHE + "/evidence.json")
    for source in evidence["sources"].values():
        if digest(ROOT / source["cache_path"]) != source["sha256"]:
            raise ValueError("Source snapshot changed after review")
    raw_hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in (ROOT / "data/raw/ioai/Team-Challenge").rglob("*") if p.is_file()}
    contracts, inline, rows = {}, {}, []
    copies = {}
    for name, source in evidence["sources"].items():
        if name in ("bundle_2024", "guide_2025"):
            continue
        filename = "rules_2025_v2_4.pdf" if name == "rules_2025" else Path(source["cache_path"]).name
        copies[f"{RECOVERED}/{filename}"] = source
    for old in before:
        row = deepcopy(old)
        pages = extract_pages(old)
        text = "\n\n".join(f"--- Source PDF page {i + 1} ---\n\n{p}" for i, p in enumerate(pages)) + "\n"
        directory = f"{RECOVERED}/{row['year']}"
        text_path = directory + "/task_statement.txt"
        inline[text_path] = text
        separator = "\n\n--- Lyrics / brief ---\n"
        suffix = separator + old["problem_description"].split(separator, 1)[1] if separator in old["problem_description"] else ""
        row["problem_description"] = text.rstrip() + suffix
        contract = task_contract(old, evidence)
        contracts[row["problem_id"]] = contract
        contract_path = directory + "/task_contract.json"
        inline[contract_path] = json.dumps(contract, indent=2, ensure_ascii=False) + "\n"
        for path in (text_path, contract_path):
            row["assets"].append(dict(path=path, role="agent_visible", mime_type="application/json" if path.endswith(".json") else "text/plain", sha256=sha(inline[path].encode())))
        if row["year"] == 2025:
            row["assets"].append(dict(path=f"{RECOVERED}/rules_2025_v2_4.pdf", role="agent_visible", mime_type="application/pdf", sha256=evidence["sources"]["rules_2025"]["sha256"]))
        row["evaluation"].update(deliverable=contract["deliverable"], task_contract_path=contract_path,
            reason="Historical source contract restored; required execution and final scoring remain unvalidated.",
            limitations=(["Creative-tool accounts and multimodal judging have not been reproduced.",
                "The raw 40+40 criterion sum is not the final ranking: image/video weights are 40:60 and full jury/peer aggregation is unresolved."]
                if row["year"] == 2024 else ["The official guide and current simulator/referee repository are identified, but the original contest revision, scene assets and execution/scoring equivalence remain unverified.",
                "The guide's ioai/master branch is not in the current branch list; the observed master commit postdates the event.",
                "The upstream license restricts reuse; public repository access is not a redistribution grant.",
                "PDF code snippets retain source line wrapping and are not validated executable scripts."]))
        row["source_review"] = dict(report=REPORT, task_contract_path=contract_path, text_path=text_path,
            source_pdf_pages=len(pages), non_whitespace_content_preserved=True, original_pdf_sha256=digest(ROOT / row["source_file"]),
            publisher_bundle_assets_verified=26 if row["year"] == 2024 else None,
            upstream_environment=evidence["upstream"] if row["year"] == 2025 else None)
        if row["year"] == 2024:
            row["evaluation"]["score_basis"] = "raw_criterion_sum_not_official_final_ranking"
        provenance(row)
        rows.append(row)
    original_rules = {k: deepcopy(store.read(f"data/rules/{CID}/{k}.json")) for k in ("competition", "collaboration", "evaluation")}
    original_rubrics = {year: deepcopy(store.read(path)) for year, path in RUBRICS.items()}
    rubrics = fix_rubrics(original_rubrics, evidence)
    rules = fix_rules(original_rules, rows, contracts)
    writes = {BENCHMARK: rows, **{f"data/rules/{CID}/{k}.json": v for k, v in rules.items()},
              **{RUBRICS[year]: v for year, v in rubrics.items()}}
    expected_hashes = {path: digest(ROOT / path) for path in writes}
    docs = "\n\n## IOAI historical source repair (2026-09-13)\n\n" + (
        "Both historical task texts now have page-labeled, whitespace-only repairs against unchanged PDFs. "
        "All 26 original 2024 contestant files match the official task ZIP. Edition-specific task contracts replace "
        "future-edition restrictions and incorrect code/prediction output defaults. The 2024 image and video each "
        "have 40 raw points, while their final-ranking weights are 40:60; 80 is not an official final-ranking scale. "
        "The archived 2025 rules cover says version 2.4 despite the URL's 2.3 filename. Current public simulator/referee "
        "metadata is pinned, but its historical version and restricted licensing remain unresolved; no implementation "
        "or baseline code enters contestant inputs. Both records remain not_ready, with no live execution performed. "
        "See `data/benchmarks/ioai_source_repair_20260913.json`.\n")
    for path in ("data/README.md", "data/benchmarks/README.md"):
        expected_hashes[path] = digest(ROOT / path)
        inline[path] = (ROOT / path).read_text(encoding="utf-8").rstrip() + docs
    plan = dict(before_rows=before, after_rows=rows, inline=inline, copies=copies, writes=writes,
        contracts=contracts, evidence=evidence, original_raw_hashes=raw_hashes,
        expected_hashes=expected_hashes, original_rules=original_rules, original_rubrics={str(k): v for k, v in original_rubrics.items()})
    store.save(CACHE + "/plan.json", plan)
    print(json.dumps(dict(records=len(rows), pages=sum(r["source_review"]["source_pdf_pages"] for r in rows),
        new_contestant_assets=sum(len(r["assets"]) - len(b["assets"]) for r, b in zip(rows, before)),
        rules_repaired=list(rules), rubric_maxima_unchanged=True), indent=2))


GENERATED_INPUTS = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
STALE_DEFAULTS = ("code_and_predictions", "Official deliverable: code and predictions", "notebooks and prediction files",
                  "translation_site_only_unless_team_task_guide_allows_more", "2026 Team Challenge", "2026_version_4")


def check_packages(rows, stage):
    checked = 0
    by_id = {CID + "/" + r["problem_id"]: r for r in rows}
    for layout in ("base", "last_exam"):
        root = stage / layout
        cards = [c for c in read(root / "task_cards.json")["tasks"] if c["task_id"].startswith(CID + "/")]
        manifest = [m for m in read(root / "input_asset_manifest.json")["files"] if m["task_id"] in by_id]
        if {c["task_id"] for c in cards} != set(by_id) or len(cards) != len(rows):
            raise ValueError("Task package membership differs")
        for card in cards:
            row = by_id[card["task_id"]]
            folder = root / card["source_repo_path"] / "base/input"
            entries = [m for m in manifest if m["task_id"] == card["task_id"]]
            public = {a["path"]: a["sha256"] for a in row["assets"] if a["role"] == "agent_visible"}
            if {m["source"]: m["sha256"] for m in entries} != public or len(entries) != len(public):
                raise ValueError("Derived input manifest differs from the explicit asset allowlist")
            paths = {(root / m["staged"]).relative_to(folder).as_posix() for m in entries}
            actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
            if actual != GENERATED_INPUTS | paths:
                raise ValueError("Unexpected or missing contestant files")
            for item in entries:
                if digest(root / item["staged"]) != item["sha256"]:
                    raise ValueError("Packaged source bytes differ")
                checked += 1
            if (folder / "problem.md").read_text(encoding="utf-8") != row["problem_description"] + "\n":
                raise ValueError("Packaged prompt differs")
            for filename in GENERATED_INPUTS - {"problem.md"}:
                content = (folder / filename).read_text(encoding="utf-8")
                if any(token in content for token in STALE_DEFAULTS):
                    raise ValueError("Stale future-edition or generic output rule remains in task input")
            if row["evaluation"]["deliverable"] not in (folder / "task_sop.md").read_text(encoding="utf-8"):
                raise ValueError("Task-specific deliverable was not propagated")
            if layout == "last_exam" and read(folder.parent.parent / "eval/reference.json")["evaluation"] != row["evaluation"]:
                raise ValueError("Hidden evaluation metadata differs")
    return checked


def verify(plan, report):
    rows = read(ROOT / BENCHMARK)
    for path, expected in plan["writes"].items():
        if read(ROOT / path) != expected:
            raise ValueError(f"JSON readback differs: {path}")
    for path, expected in plan["inline"].items():
        if (ROOT / path).read_text(encoding="utf-8") != expected:
            raise ValueError("Text readback differs")
    for path, source in plan["copies"].items():
        if digest(ROOT / path) != source["sha256"]:
            raise ValueError("Copied provenance source changed")
    for path, expected in {**plan["original_raw_hashes"], **report["unrelated_hashes"]}.items():
        if digest(ROOT / path) != expected:
            raise ValueError(f"Preserved source changed: {path}")
    for row, old in zip(rows, plan["before_rows"]):
        for field in ("problem_id", "year", "task_type", "team_size", "source_file", "solution_file", "total_points", "gold_label", "split", "license"):
            if row[field] != old[field]:
                raise ValueError(f"Preserved record field differs: {field}")
        if row["assets"][:len(old["assets"])] != old["assets"]:
            raise ValueError("Original assets or their visibility changed")
        if row["evaluation"]["status"] != "not_ready" or row["evaluation"]["evaluator_id"] is not None:
            raise ValueError("Source repair cannot promote readiness")
        for asset in row["assets"]:
            if digest(ROOT / asset["path"]) != asset["sha256"]:
                raise ValueError("Canonical asset hash differs")
        if extract_pages(old) != read(ROOT / CACHE / f"pages_{row['year']}.json"):
            raise ValueError("Source content changed on independent extraction")
    rubric24 = read(ROOT / RUBRICS[2024])
    if rubric24["criteria"] != plan["original_rubrics"]["2024"]["criteria"]:
        raise ValueError("Existing criterion maxima or anchors changed")
    if rubric24["task_weights"] != {"image_cover": 40, "music_video": 60}:
        raise ValueError("Final-ranking weight ratio is incorrect")
    for task, expected in rubric24["raw_task_maxima"].items():
        if sum(c["max_score"] for c in rubric24["criteria"] if c["task"] == task) != expected:
            raise ValueError("Raw rubric maximum differs")
    method = read(ROOT / f"data/rules/{CID}/collaboration.json")
    for field in ("agent_roles", "deliberation", "simulation", "communication", "information_policy"):
        if method[field] != plan["original_rules"]["collaboration"][field]:
            raise ValueError("Collaboration overlay changed")
    checked = check_packages(rows, ROOT / "data")
    index = read(ROOT / "data/benchmarks/index.json")
    for layout in ("base", "last_exam"):
        catalog = read(ROOT / f"data/{layout}/task_cards.json")
        if len(catalog["tasks"]) != index["total_records"] or catalog["n_tasks"] != index["total_records"]:
            raise ValueError("Global catalog count differs")
        for filename, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            other = [v for v in read(ROOT / f"data/{layout}/{filename}")[key] if not v["task_id"].startswith(CID + "/")]
            if stable(other) != report["unrelated_derived_hashes"][layout + "/" + filename]:
                raise ValueError("Unrelated derived records changed")
    if read(ROOT / f"data/rubrics/task_scorecards/{CID}.json")["records"] != [scorecard(r, ROOT) for r in rows]:
        raise ValueError("Scorecard projection differs")
    return dict(records_checked=len(rows), statement_pages_checked=28, original_raw_files_unchanged=len(plan["original_raw_hashes"]),
        publisher_2024_assets_matched=26, copied_contestant_assets_checked=checked,
        unrelated_canonical_tracks_unchanged=len(report["unrelated_canonical_paths"]),
        neighboring_rules_and_rubrics_unchanged=True, collaboration_overlays_unchanged=True,
        source_text_nonspacing_unchanged=True, readiness_promotions=0, global_records=index["total_records"],
        live_evaluation_performed=False)


def apply():
    store = Store(ROOT)
    plan = store.read(CACHE + "/plan.json")
    if store.path(REPORT).exists():
        raise ValueError("Repair already applied; use verify")
    for path, expected in {**plan["expected_hashes"], **plan["original_raw_hashes"]}.items():
        if digest(ROOT / path) != expected:
            raise ValueError("Concurrent edit detected before mutation")
    for path in [*plan["copies"], *(p for p in plan["inline"] if p not in plan["expected_hashes"])]:
        if store.path(path).exists():
            raise ValueError("New source destination is occupied")
    rows = plan["after_rows"]
    index = deepcopy(store.read("data/benchmarks/index.json"))
    track = next(t for t in index["olympiads"] if t["id"] == CID)
    unrelated_paths = [t["benchmark_path"] for t in index["olympiads"] if t["id"] != CID]
    preserve = list(unrelated_paths)
    for tree in ("data/rules", "data/rubrics"):
        preserve.extend(p.relative_to(ROOT).as_posix() for p in (ROOT / tree).rglob("*.json")
            if p.relative_to(ROOT).as_posix() not in plan["writes"] and p != ROOT / f"data/rubrics/task_scorecards/{CID}.json")
    report = dict(operation="ioai_historical_source_and_contract_repair", status="preparing", timestamp_utc=store.stamp,
        backup=store.backup.relative_to(ROOT).as_posix(), evidence=plan["evidence"],
        unrelated_canonical_paths=unrelated_paths, unrelated_hashes={p: digest(ROOT / p) for p in preserve},
        unrelated_derived_hashes={})
    catalogs, manifests = {}, {}
    for layout in ("base", "last_exam"):
        catalogs[layout] = deepcopy(store.read(f"data/{layout}/task_cards.json"))
        manifests[layout] = deepcopy(store.read(f"data/{layout}/input_asset_manifest.json"))
        for filename, values in (("task_cards.json", catalogs[layout]["tasks"]), ("input_asset_manifest.json", manifests[layout]["files"])):
            report["unrelated_derived_hashes"][layout + "/" + filename] = stable([v for v in values if not v["task_id"].startswith(CID + "/")])
    store.finish(report)
    try:
        for path, source in plan["copies"].items():
            if digest(ROOT / source["cache_path"]) != source["sha256"]:
                raise ValueError("Reviewed source copy changed")
            target = store.path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / source["cache_path"], target)
            store.changes.append(dict(path=path, before_sha256=None, after_sha256=source["sha256"]))
        for path, text in plan["inline"].items():
            if path not in plan["expected_hashes"]:
                store.save_text(path, text)
        rules = {k: plan["writes"][f"data/rules/{CID}/{k}.json"] for k in ("competition", "collaboration", "evaluation")}
        stage = store.path(CACHE + "/packages_" + store.stamp)
        report["packages"] = build_packages(ROOT, stage, {"olympiads": [track]}, {CID: rows}, {CID: rules}, store.sha)
        report["staged_asset_copies_checked"] = check_packages(rows, stage)
        for layout in catalogs:
            replacement = {c["task_id"]: c for c in read(stage / layout / "task_cards.json")["tasks"]}
            if set(replacement) != {c["task_id"] for c in catalogs[layout]["tasks"] if c["task_id"].startswith(CID + "/")}:
                raise ValueError("Canonical and derived membership disagree")
            catalogs[layout]["tasks"] = [replacement.get(c["task_id"], c) for c in catalogs[layout]["tasks"]]
            manifests[layout]["files"] = [m for m in manifests[layout]["files"] if not m["task_id"].startswith(CID + "/")] + read(stage / layout / "input_asset_manifest.json")["files"]
        report["status"] = "applying"
        store.finish(report)
        for path, value in plan["writes"].items():
            store.save(path, value)
        for path, text in plan["inline"].items():
            if path in plan["expected_hashes"]:
                store.save_text(path, text)
        store.save(f"data/rubrics/task_scorecards/{CID}.json", dict(schema_version="1.1", dataset=CID, visibility="judge_only",
            records=[scorecard(r, ROOT) for r in rows]))
        update_track_index(index, CID, rows)
        index["latest_source_repair_report"] = REPORT
        store.save("data/benchmarks/index.json", index)
        for name in (f"base/tasks/{CID}", f"last_exam/tasks/{CID}", f"last_exam/competitions/{CID}"):
            target = store.path("data/" + name)
            source = (stage / name).resolve()
            if not source.is_relative_to(stage.resolve()):
                raise ValueError("Staging path escapes the reviewed directory")
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
        print(json.dumps({k: report[k] for k in ("status", "backup", "validation")}, indent=2))
    except Exception as error:
        report.update(status="interrupted", error=str(error))
        store.finish(report)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("recover", "prepare", "apply", "verify"))
    arguments = parser.parse_args()
    if arguments.mode == "verify":
        print(json.dumps(verify(read(ROOT / CACHE / "plan.json"), read(ROOT / REPORT)), indent=2))
    else:
        {"recover": recover, "prepare": prepare, "apply": apply}[arguments.mode]()
