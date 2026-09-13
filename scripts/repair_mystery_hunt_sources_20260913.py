"""Repair a reviewed Mystery Hunt packet subset without changing its answer targets.

This is an explicit 14-record migration, not a generic archive sanitizer. Original
HTML and media stay intact. No puzzle binaries are run and no readiness is granted.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from PIL import Image
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.repair_data_catalog import Store, provenance
from scripts.build_data_packages import build_packages
from dataset_catalog import scorecard, update_track_index

CID = "mystery_hunt"
BENCHMARK = f"data/benchmarks/{CID}/benchmark.json"
CACHE = "data/.cache/mystery_hunt_repair_20260913"
RAW = "data/raw/mystery_hunt/separated_20260913"
REPORT = "data/benchmarks/mystery_hunt_source_repair_20260913.json"
MANIFEST = RAW + "/manifest.json"
ORIGINAL_TREE = "data/raw/external/MIT_Mystery_Hunt"
ORIGIN = "https://puzzles.mit.edu/"
BRUNCH = "mystery_hunt_00819"
ATTACHMENTS = {
    "mystery_hunt_00002": ["freetown.pdf"],
    "mystery_hunt_00003": [],
    "mystery_hunt_00004": [],
    "mystery_hunt_00006": [],
    "mystery_hunt_00007": [],
    "mystery_hunt_00014": [],
    "mystery_hunt_00028": ["mice1.jpg", "maze3.jpg", "maze2.jpg", "maze4.jpg", "maze1.jpg", "maze5.jpg"],
    "mystery_hunt_00032": [],
    "mystery_hunt_00033": ["taipei.jpg"],
    "mystery_hunt_00035": [],
    "mystery_hunt_00036": [],
    "mystery_hunt_00038": [],
    "mystery_hunt_00044": ["pie.jpg", "nairobi-hunttime.pdf"],
}
SELECTED = set(ATTACHMENTS) | {BRUNCH}
BRUNCH_MEDIA = {
    "line.gif": "2006/puzzles/moscow/russian_brunch/line.gif",
    "name.gif": "2006/puzzles/moscow/russian_brunch/name.gif",
    "invitation.jpg": "2006/puzzles/moscow/russian_brunch/invitation.jpg",
    "puzzle.css": "2006/puzzles/moscow/puzzle.css",
    "marble-background.jpg": "2006/puzzles/moscow/marble-background.jpg",
    "line-background.jpg": "2006/puzzles/moscow/line-background.jpg",
    "name-background.gif": "2006/puzzles/moscow/name-background.gif",
    "logo.png": "2006/puzzles/logo.png",
}
LIMITS = {
    "mystery_hunt_00002": "The two PDF sides reproduce double-sided pentominoes, not a validated virtual manipulation environment.",
    "mystery_hunt_00003": "A live host Battleship interaction and hidden board state are not reproduced.",
    "mystery_hunt_00007": "A physical scavenger hunt requires actual objects and host judgments; its historical points are not the isolated answer-match score.",
    "mystery_hunt_00014": "The character stereogram requires original monospace geometry and visual validation by the solving/evaluation stack.",
    "mystery_hunt_00028": "Maze photographs and positional transcripts require image-aware solving/evaluation validation.",
    "mystery_hunt_00032": "A physical Edam cube and historical product/UPC information are not reproduced; the official solution notes missing historical product information.",
    "mystery_hunt_00033": "The tarot-card image requires image-aware solving/evaluation validation.",
    "mystery_hunt_00035": "A physical gingerbread sculpture and host acceptance are not reproduced.",
    "mystery_hunt_00036": "The official archive gives the final answer but explicitly lacks its solution explanation.",
    "mystery_hunt_00038": "This final meta needs other puzzle answers, historical ordering messages and hunt state; those are not injected as starting inputs.",
    "mystery_hunt_00044": "The archive says its HTML differs from the hunt-time PDF. Both source variants are preserved and labeled, without selecting a canonical ciphertext; the archive lacks a confirmed solution explanation.",
    BRUNCH: "The invitation is recovered, but the live brunch and sensory observations are absent. Its published solution ingredients remain judge-only; the invitation alone is not a complete reasoning task.",
}
BASE_LIMIT = "The reviewed contestant packet is separated from archive answer controls and solution pages. Historical per-puzzle rules, answer-mechanism semantics and end-to-end evaluation are not certified; the 2026 default rules are not asserted as the rules of this historical edition."


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def rel(path):
    return Path(path).relative_to(ROOT).as_posix()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_newlines(payload):
    return payload.replace(b"\r", b"")


def prompt_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def download(url):
    if not url.startswith(ORIGIN):
        raise ValueError("Only the reviewed publisher origin may be fetched")
    target = ROOT / CACHE / "publisher" / (hashlib.sha256(url.encode()).hexdigest() + ".bin")
    metadata = target.with_suffix(".json")
    if target.exists() and metadata.exists():
        record = read(metadata)
        if record["source_url"] != url or record["sha256"] != sha(target):
            raise ValueError("Cached publisher snapshot changed")
        return record
    response = requests.get(url, timeout=40)
    response.raise_for_status()
    if urlparse(response.url).netloc != "puzzles.mit.edu" or not response.content:
        raise ValueError("Unexpected publisher redirect/empty response")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(response.content)
    record = dict(source_url=url, final_url=response.url, path=rel(target), sha256=sha(target),
                  bytes=len(response.content), content_type=response.headers.get("Content-Type"),
                  retrieved_at_utc=Store(ROOT).stamp)
    save(metadata, record)
    return record


def sanitize(payload, pid):
    """Byte-preserving deletion/relinking of exactly reviewed archive elements."""
    edits = []

    def sub(pattern, replacement, expected, reason):
        nonlocal payload
        matches = list(re.finditer(pattern, payload, re.I | re.S))
        if len(matches) != expected:
            raise ValueError(f"Sanitizer source drift: {pid}: {reason}: {len(matches)}")
        for m in matches:
            edits.append(dict(reason=reason, removed=m.group().decode("ascii"), replacement=replacement.decode("ascii")))
        payload = re.sub(pattern, replacement, payload, flags=re.I | re.S)

    sub(rb'<script type="module" src="/checkanswer\.js"></script>', b"", 1, "archive answer-checking script")
    if pid != BRUNCH:
        sub(rb'<a href="solution\.html">Solution</a>', b"", 1, "archive solution navigation")
    else:
        sub(rb'<div id="nav">.*?</div>', b"", 1, "archive navigation and answer/solution controls")
        sub(rb'<p class="text"><b>This event has occured\.  The answer is SNIFF\.</b></p>', b"", 1, "post-event final-answer disclosure")
        sub(rb'href="\.\./puzzle\.css"', b'href="media/puzzle.css"', 1, "local stylesheet path")
        for name in ("line.gif", "name.gif", "invitation.jpg"):
            sub(rb'src="' + re.escape(name.encode()) + rb'"', ('src="media/' + name + '"').encode(), 1, "local image path")
    return payload, edits


def check_html(path, allowed):
    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    if soup.find_all(["script", "iframe", "object", "embed", "form", "base"]):
        raise ValueError(f"Active or off-packet content in {path}")
    for tag in soup.find_all():
        if any(k.lower().startswith("on") for k in tag.attrs):
            raise ValueError("Unexpected active HTML attribute")
        for attr in ("src", "href", "background"):
            if tag.get(attr):
                link = tag[attr]
                if urlparse(link).scheme or link.startswith(("/", "#")):
                    raise ValueError(f"Non-local contestant dependency: {link}")
                target = (path.parent / link).resolve()
                if target not in allowed or not target.is_file():
                    raise ValueError(f"Missing/non-allowlisted contestant dependency: {link}")
    return soup


def check_css(path, allowed):
    payload = path.read_text(encoding="ascii")
    if re.search(r"@import|expression\(|javascript:|https?://", payload, re.I):
        raise ValueError("Unexpected active/remote CSS")
    for name in re.findall(r"url\(['\"]?([^)'\"]+)", payload):
        if (path.parent / name).resolve() not in allowed:
            raise ValueError("Unpackaged CSS dependency")


def prepare():
    if (ROOT / REPORT).exists() or (ROOT / CACHE / "plan.json").exists():
        raise ValueError("Prepared or applied migration exists; do not overwrite")
    before = read(ROOT / BENCHMARK)
    chosen = [r for r in before if r["problem_id"] in SELECTED]
    if {r["problem_id"] for r in chosen} != SELECTED or len(before) != 261:
        raise ValueError("Unexpected subset membership")
    original_hashes = {rel(p): sha(p) for p in (ROOT / ORIGINAL_TREE).rglob("*") if p.is_file()}
    urls = set(ORIGIN + p for p in BRUNCH_MEDIA.values())
    sources = {}
    for row in chosen:
        pid = row["problem_id"]
        url = ORIGIN + row["puzzle_url"].rstrip("/") + ("/" if pid == BRUNCH else "")
        solution = urljoin(url, "answer/solution.html" if pid == BRUNCH else "solution.html")
        sources[pid] = (url, solution)
        urls.update((url, solution))
        urls.update(urljoin(url, name) for name in ATTACHMENTS.get(pid, []))
    with ThreadPoolExecutor(max_workers=4) as pool:
        snapshots = {r["source_url"]: r for r in pool.map(download, sorted(urls))}
    copies, reviews, changes = [], {}, []
    after = deepcopy(before)

    def stage_bytes(pid, name, payload, role, source, source_url, derivation=None):
        prepared = ROOT / CACHE / "prepared" / pid / name
        if prepared.exists():
            if prepared.read_bytes() != payload:
                raise ValueError("Existing prepared bytes differ")
        else:
            prepared.parent.mkdir(parents=True, exist_ok=True)
            prepared.write_bytes(payload)
        destination = RAW + "/" + pid + "/" + name
        asset = dict(path=destination, role=role, sha256=sha(prepared), source_url=source_url)
        copies.append(dict(source=rel(prepared), destination=destination, sha256=asset["sha256"],
                           original_source=source, source_url=source_url, derivation=derivation))
        return asset

    for row in after:
        pid = row["problem_id"]
        if pid not in SELECTED:
            continue
        old = deepcopy(row)
        url, solution_url = sources[pid]
        original = ROOT / row["source_file"]
        publisher = ROOT / snapshots[url]["path"]
        if normalize_newlines(original.read_bytes()) != normalize_newlines(publisher.read_bytes()):
            raise ValueError(f"Publisher HTML differs beyond CR line endings: {pid}")
        solution = ROOT / snapshots[solution_url]["path"]
        local_solution = original.parent / "solution.html"
        if local_solution.exists() and normalize_newlines(local_solution.read_bytes()) != normalize_newlines(solution.read_bytes()):
            raise ValueError(f"Publisher solution differs beyond CR line endings: {pid}")
        solution_text = BeautifulSoup(solution.read_bytes(), "html.parser").get_text(" ", strip=True)
        normalized = lambda s: re.sub(r"[^A-Z0-9]", "", s.upper())
        answer = row["gold_label"]["expected_answer"]
        if normalized(answer) not in normalized(solution_text):
            raise ValueError("Existing answer not supported by reviewed official solution")
        payload, edits = sanitize(original.read_bytes(), pid)
        assets = [stage_bytes(pid, "input/puzzle.html", payload, "agent_visible", old["source_file"], url, edits)]
        for name in ATTACHMENTS.get(pid, []):
            local = original.parent / name
            remote = ROOT / snapshots[urljoin(url, name)]["path"]
            if sha(local) != sha(remote):
                raise ValueError(f"Official media differs: {pid}/{name}")
            assets.append(stage_bytes(pid, "input/" + name, local.read_bytes(), "agent_visible", rel(local), urljoin(url, name)))
        if pid == BRUNCH:
            for name, source_path in BRUNCH_MEDIA.items():
                record = snapshots[ORIGIN + source_path]
                media = (ROOT / record["path"]).read_bytes()
                derivation = None
                if name == "puzzle.css":
                    if media.count(b"url(../logo.png)") != 1:
                        raise ValueError("Unexpected stylesheet")
                    media = media.replace(b"url(../logo.png)", b"url(logo.png)")
                    derivation = "Relink the original logo dependency within the local media directory; all style declarations retained."
                assets.append(stage_bytes(pid, "input/media/" + name, media, "agent_visible", record["path"], record["source_url"], derivation))
        assets.append(stage_bytes(pid, "judge/solution.html", solution.read_bytes(), "judge_only", snapshots[solution_url]["path"], solution_url))
        assets.append(dict(path=old["source_file"], role="judge_only", sha256=sha(original), source_url=url,
                           note="Unmodified archive HTML with answer controls or post-event disclosure; never a contestant input."))
        public_files = [ROOT / c["source"] for c in copies if c["destination"].startswith(RAW + "/" + pid + "/input/")]
        allowed = {p.resolve() for p in public_files}
        html = ROOT / CACHE / "prepared" / pid / "input/puzzle.html"
        clean = check_html(html, allowed)
        for path in public_files:
            if path.suffix == ".css":
                check_css(path, allowed)
            elif path.suffix in (".gif", ".jpg", ".png"):
                with Image.open(path) as img:
                    img.verify()
        # Keep the raw cleaned HTML as authoritative: pre/table/BR geometry is
        # part of these puzzles, and cannot be reconstructed from old flattened text.
        prompt = "# " + clean.title.get_text(strip=True) + "\n\n" if clean.title else "# Freetown\n\n"
        prompt += ("Open `puzzle.html` for the contestant puzzle, including its original table, line-break and monospace layout. "
                   "All links in that file resolve to the attached local materials. Do not treat the plain-text extraction below as a replacement for the original layout.\n\n")
        if pid == "mystery_hunt_00044":
            prompt += "The archive HTML and `nairobi-hunttime.pdf` are distinct published variants; the archive's own version warning is retained. No canonical variant is selected here.\n\n"
        prompt += "## Source text (layout is in puzzle.html)\n\n" + prompt_newlines(clean.body.get_text("\n", strip=True))
        row.update(source_url=url, source_file=RAW + "/" + pid + "/input/puzzle.html",
                   solution_file=RAW + "/" + pid + "/judge/solution.html", assets=assets,
                   problem_description=prompt, source_visibility="separated_contestant_packet_original_archive_judge_only",
                   asset_policy="Only the explicit agent_visible files are contestant inputs. Original archive pages, answer-checking scripts, solutions and their dependencies are excluded. Packet availability does not reproduce historical interaction or full-hunt state.")
        row["evaluation"]["limitations"] = BASE_LIMIT + (" " + LIMITS[pid] if pid in LIMITS else "")
        row["source_review"] = dict(repair_batch="20260913", packet_scope="reviewed_explicit_allowlist",
            original_source_file=old["source_file"], original_sha256=sha(original), official_puzzle_url=url,
            publisher_comparison="identical_after_removing_CR_line_ending_bytes",
            official_solution_url=solution_url, official_solution_sha256=sha(solution),
            answer_target_unchanged=True, removed_archive_elements=edits,
            remaining_limitations=LIMITS.get(pid, "Historical rule and evaluator semantics remain uncertified."),
            solution_completeness="answer_only_or_unconfirmed_explanation" if pid in {"mystery_hunt_00036", "mystery_hunt_00044"} else "published_explanation_or_answer",
            active_evaluator_unchanged=True)
        provenance(row)
        reviews[pid] = dict(puzzle_url=url, solution_url=solution_url, original_source=old["source_file"],
            answer_verified=True, edits=edits, public_files=len(public_files),
            direct_answer_disclosure_removed=pid == BRUNCH)
        changes.append(pid)
    plan = dict(before_rows=before, after_rows=after, changed_ids=changes, original_hashes=original_hashes,
                expected_benchmark_sha256=sha(ROOT / BENCHMARK), copies=copies, publisher_snapshots=snapshots,
                reviews=reviews, source_assets_unmodified=True,
                excluded_staged_puzzles={"mystery_hunt_00009": "Prague needs staged physical pickups and historical executable handling; not opened as an all-at-start packet.",
                                         "mystery_hunt_00015": "Charlotte Amalie gives each team one of five scripts; not flattened into a shared all-role packet."},
                preserved_answer_word_hits={"mystery_hunt_00112": "ISOLATION is a source clue word in the scrambled text.",
                                           "mystery_hunt_00113": "RISING is a source list entry, not a disclosed result."})
    save(ROOT / CACHE / "plan.json", plan)
    print(json.dumps(dict(changed_records=len(changes), untouched_records=len(before) - len(changes),
                         publisher_snapshots=len(snapshots), original_files=len(original_hashes),
                         public_assets=sum(a["role"] == "agent_visible" for r in after if r["problem_id"] in SELECTED for a in r["assets"])), indent=2))


def check_packages(rows, directory):
    checks = 0
    generated = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
    for layout in ("base", "last_exam"):
        cards = {c["task_id"]: c for c in read(directory / layout / "task_cards.json")["tasks"] if c["task_id"].startswith(CID + "/")}
        if set(cards) != {CID + "/" + r["problem_id"] for r in rows}:
            raise ValueError("Generated Mystery Hunt membership changed")
        for row in rows:
            card = cards[CID + "/" + row["problem_id"]]
            folder = directory / layout / card["source_repo_path"] / "base/input"
            if (folder / "problem.md").read_text(encoding="utf-8") != row["problem_description"] + "\n":
                raise ValueError("Prompt projection differs")
            if row["problem_id"] not in SELECTED:
                continue
            public = {Path(a["path"]).relative_to(Path(row["source_file"]).parent).as_posix(): a
                      for a in row["assets"] if a["role"] == "agent_visible"}
            actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
            if actual != generated | set(public):
                raise ValueError("Public packet differs from explicit allowlist")
            for name, asset in public.items():
                if sha(folder / name) != asset["sha256"]:
                    raise ValueError("Copied input hash differs")
                checks += 1
            allowed = {(folder / name).resolve() for name in public}
            check_html(folder / "puzzle.html", allowed)
            for css in folder.rglob("*.css"):
                check_css(css, allowed)
            for path in folder.rglob("*"):
                if path.suffix in {".md", ".html", ".css"}:
                    text = path.read_text(encoding="utf-8")
                    if any(s in text for s in ("/checkanswer.js", 'href="solution.html"', 'href="answer/', "The answer is SNIFF", "/judge/", "data/rubrics/")):
                        raise ValueError("Archive answer boundary leaked into public input")
            expected_list = card["input_files"] if layout == "base" else card["input"]["files"]
            prefix = "input/" if layout == "base" else "base/input/"
            if {f["path"].removeprefix(prefix) for f in expected_list} != actual:
                raise ValueError("Catalog input list differs")
            if layout == "last_exam":
                reference = read(directory / layout / card["source_repo_path"] / "eval/reference.json")
                if reference["solution_file"] != row["solution_file"] or reference["evaluation"] != row["evaluation"]:
                    raise ValueError("Hidden reference projection differs")
    return checks


def verify(plan, report):
    rows = read(ROOT / BENCHMARK)
    if rows != plan["after_rows"]:
        raise ValueError("Canonical readback differs")
    for path, expected in {**plan["original_hashes"], **report["preserved_hashes"]}.items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"Protected source/neighbor changed: {path}")
    protected = ("problem_id", "competition", "year", "title", "topic", "team_size", "split", "license", "status", "total_points", "gold_label", "puzzle_url")
    for old, row in zip(plan["before_rows"], rows):
        if row["problem_id"] not in SELECTED and row != old:
            raise ValueError("Unselected Mystery Hunt record changed")
        for key in protected:
            if row.get(key) != old.get(key):
                raise ValueError("Protected record field changed")
        if row["evaluation"]["status"] != old["evaluation"]["status"] or row["evaluation"]["evaluator_id"] != old["evaluation"]["evaluator_id"]:
            raise ValueError("Readiness/evaluator changed")
        if row["problem_id"] in SELECTED:
            for a in row["assets"]:
                if sha(ROOT / a["path"]) != a["sha256"]:
                    raise ValueError("Asset hash differs")
            expected, edits = sanitize((ROOT / old["source_file"]).read_bytes(), row["problem_id"])
            if (ROOT / row["source_file"]).read_bytes() != expected or edits != row["source_review"]["removed_archive_elements"]:
                raise ValueError("HTML changed outside reviewed edits")
    actual_files = {rel(p): sha(p) for p in (ROOT / RAW).rglob("*") if p.is_file() and rel(p) != MANIFEST}
    expected_files = {c["destination"]: c["sha256"] for c in plan["copies"]}
    if actual_files != expected_files:
        raise ValueError("Unexpected file in separated source packet")
    copies = check_packages(rows, ROOT / "data")
    index = read(ROOT / "data/benchmarks/index.json")
    ids = [t["id"] + "/" + r["problem_id"] for t in index["olympiads"] for r in read(ROOT / t["benchmark_path"])]
    if len(ids) != len(set(ids)) or len(ids) != report["global_records"] or index["total_records"] != len(ids):
        raise ValueError("Global membership/count differs")
    for layout in ("base", "last_exam"):
        for name, key in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            values = read(ROOT / f"data/{layout}/{name}")[key]
            if key == "tasks" and ({v["task_id"] for v in values} != set(ids) or len(values) != len(ids)):
                raise ValueError("Global generated task set differs")
            preserved = [v for v in values if v["task_id"] not in {CID + "/" + p for p in SELECTED}]
            if stable(preserved) != report["unrelated_derived_hashes"][layout + "/" + name]:
                raise ValueError("Unselected generated catalog entries changed")
            if key == "files":
                selected = [v for v in values if v["task_id"] in {CID + "/" + p for p in SELECTED}]
                if len(selected) != report["public_assets"]:
                    raise ValueError("Manifest count differs")
                for v in selected:
                    if sha(ROOT / f"data/{layout}" / v["staged"]) != v["sha256"]:
                        raise ValueError("Manifest file hash differs")
    if read(ROOT / f"data/rubrics/task_scorecards/{CID}.json")["records"] != [scorecard(r, ROOT) for r in rows]:
        raise ValueError("Scorecard projection differs")
    untouched_cards = [c for c in read(ROOT / f"data/rubrics/task_scorecards/{CID}.json")["records"] if c["problem_id"] not in SELECTED]
    if stable(untouched_cards) != report["unselected_scorecard_hash"]:
        raise ValueError("Unselected scorecard entries changed")
    for path, expected in report["unselected_packet_hashes"].items():
        if sha(ROOT / path) != expected:
            raise ValueError("Unselected generated packet file changed")
    for path, expected in report["visual_review"]["reviewed_asset_hashes"].items():
        if sha(ROOT / path) != expected:
            raise ValueError("Visually reviewed asset changed")
    return dict(canonical_records=261, repaired_records=14, unselected_records_unchanged=247,
                global_records=len(ids), official_answer_targets_verified=14, gold_labels_changed=0,
                direct_answer_disclosures_removed=1, public_assets=report["public_assets"],
                copied_assets_checked=copies, original_raw_files_unchanged=len(plan["original_hashes"]),
                neighboring_tracks_unchanged=42, exact_html_derivations_verified=14,
                broken_public_media_links=0, unexpected_public_files=0, readiness_promotions=0,
                live_evaluation_performed=False)


def apply():
    store = Store(ROOT)
    if store.path(REPORT).exists():
        raise ValueError("Already applied; use verify")
    plan = read(ROOT / CACHE / "plan.json")
    review = read(ROOT / CACHE / "visual_review.json")
    if sha(ROOT / BENCHMARK) != plan["expected_benchmark_sha256"]:
        raise ValueError("Canonical benchmark changed after preparation")
    for p, expected in plan["original_hashes"].items():
        if sha(ROOT / p) != expected:
            raise ValueError("Original source changed after preparation")
    existing = [c for c in plan["copies"] if (ROOT / c["destination"]).exists()]
    if existing:
        previous = read(store.path(plan["previous_attempt_manifest"]))
        if previous["report"]["operation"] != "mystery_hunt_reviewed_packet_boundary_repair" or previous["report"]["status"] != "interrupted" or previous["archived"]:
            raise ValueError("Previous attempt is not a pre-commit staging interruption")
        prior_files = {c["path"]: c for c in previous["changed_files"]}
        if set(prior_files) != {c["destination"] for c in existing}:
            raise ValueError("Existing targets not exactly covered by previous attempt manifest")
        for c in existing:
            prior = prior_files[c["destination"]]
            if prior["before_sha256"] is not None or prior["after_sha256"] != c["sha256"] or sha(ROOT / c["destination"]) != c["sha256"]:
                raise ValueError("Existing target is not an unchanged new file from the staging attempt")
    for c in plan["copies"]:
        if sha(ROOT / c["source"]) != c["sha256"]:
            raise ValueError("Prepared bytes changed")
    for p, expected in review["reviewed_asset_hashes"].items():
        prepared = ROOT / CACHE / "prepared" / Path(p).relative_to(RAW)
        if sha(prepared) != expected:
            raise ValueError("Prepared visual artifact changed")
    if set(review["html_records"]) != SELECTED or review["pdf_pages_inspected"] != 4:
        raise ValueError("Incomplete visual review")
    rows = plan["after_rows"]
    index = deepcopy(store.read("data/benchmarks/index.json"))
    track = next(t for t in index["olympiads"] if t["id"] == CID)
    rules = {k: deepcopy(store.read(f"data/rules/{CID}/{k}.json")) for k in ("competition", "collaboration", "evaluation")}
    changing = {f"data/rubrics/task_scorecards/{CID}.json"}
    preserve = [t["benchmark_path"] for t in index["olympiads"] if t["id"] != CID]
    for tree in ("data/rules", "data/rubrics"):
        preserve.extend(rel(p) for p in (ROOT / tree).rglob("*.json") if rel(p) not in changing)
    preserve.append("data/viz/summary.json")
    preserve.extend(rel(p) for p in (ROOT / f"data/last_exam/competitions/{CID}").rglob("*") if p.is_file())
    report = dict(operation="mystery_hunt_reviewed_packet_boundary_repair", status="preparing", timestamp_utc=store.stamp,
                  backup=rel(store.backup), global_records=index["total_records"], changed_ids=plan["changed_ids"],
                  public_assets=sum(a["role"] == "agent_visible" for r in rows if r["problem_id"] in SELECTED for a in r["assets"]),
                  preserved_hashes={p: store.sha(p) for p in preserve}, unrelated_derived_hashes={},
                  unselected_packet_hashes={}, visual_review=review,
                  resumed_from_precommit_attempt=plan.get("previous_attempt_manifest"),
                  unselected_scorecard_hash=stable([c for c in store.read(f"data/rubrics/task_scorecards/{CID}.json")["records"] if c["problem_id"] not in SELECTED]),
                  judge_reference_scope="Official solution HTML is preserved and its answer text checked. Linked solution illustrations and cross-puzzle documents are not a complete offline judge package.")
    catalogs, manifests = {}, {}
    selected_task_ids = {CID + "/" + p for p in SELECTED}
    for layout in ("base", "last_exam"):
        catalogs[layout] = deepcopy(store.read(f"data/{layout}/task_cards.json"))
        manifests[layout] = deepcopy(store.read(f"data/{layout}/input_asset_manifest.json"))
        for name, values in (("task_cards.json", catalogs[layout]["tasks"]), ("input_asset_manifest.json", manifests[layout]["files"])):
            report["unrelated_derived_hashes"][layout + "/" + name] = stable([v for v in values if v["task_id"] not in selected_task_ids])
        for c in catalogs[layout]["tasks"]:
            if c["task_id"].startswith(CID + "/") and c["task_id"] not in selected_task_ids:
                directory = ROOT / f"data/{layout}" / c["source_repo_path"]
                report["unselected_packet_hashes"].update({rel(p): sha(p) for p in directory.rglob("*") if p.is_file()})
    store.finish(report)
    try:
        for c in plan["copies"]:
            target = ROOT / c["destination"]
            if target.exists():
                continue  # Exact hash + previous-attempt ownership verified above.
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / c["source"], target)
            store.changes.append(dict(path=c["destination"], before_sha256=None, after_sha256=c["sha256"]))
        stage = ROOT / CACHE / ("packages_" + store.stamp)
        report["packages"] = build_packages(ROOT, stage, {"olympiads": [track]}, {CID: rows}, {CID: rules}, store.sha)
        report["staged_asset_checks"] = check_packages(rows, stage)
        for layout in catalogs:
            new = {c["task_id"]: c for c in read(stage / layout / "task_cards.json")["tasks"]}
            catalogs[layout]["tasks"] = [new[c["task_id"]] if c["task_id"] in selected_task_ids else c for c in catalogs[layout]["tasks"]]
            manifests[layout]["files"] = [f for f in manifests[layout]["files"] if f["task_id"] not in selected_task_ids] + [f for f in read(stage / layout / "input_asset_manifest.json")["files"] if f["task_id"] in selected_task_ids]
        report["status"] = "applying"
        store.finish(report)
        store.save(BENCHMARK, rows)
        store.save(f"data/rubrics/task_scorecards/{CID}.json", dict(schema_version="1.1", dataset=CID,
                    visibility="judge_only", records=[scorecard(r, ROOT) for r in rows]))
        update_track_index(index, CID, rows)
        index["latest_source_repair_report"] = REPORT
        store.save("data/benchmarks/index.json", index)
        store.save(MANIFEST, dict(visibility="maintainer_only", publisher_snapshots=plan["publisher_snapshots"],
            reviews=plan["reviews"], files=plan["copies"], excluded_staged_puzzles=plan["excluded_staged_puzzles"],
            preserved_answer_word_hits=plan["preserved_answer_word_hits"], visual_review=review))
        # Replace only selected task trees: leave 247 other Mystery Hunt tasks
        # and the unchanged shared competition pack byte-for-byte in place.
        for layout in catalogs:
            for pid in sorted(SELECTED):
                name = f"{layout}/tasks/{CID}/{pid}"
                destination = store.path("data/" + name)
                source = (stage / name).resolve()
                if not source.is_relative_to(stage.resolve()) or not source.is_dir():
                    raise ValueError("Invalid staged task path")
                if destination.exists():
                    store.archive(destination)
                shutil.copytree(source, destination)
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


def repair_prepared_line_endings():
    """Repair only the pending plan after the first pre-commit staging check."""
    path = ROOT / CACHE / "plan.json"
    plan = read(path)
    old_plan = ROOT / CACHE / "plan_before_prompt_newline_repair.json"
    if old_plan.exists() or (ROOT / REPORT).exists() or sha(ROOT / BENCHMARK) != plan["expected_benchmark_sha256"]:
        raise ValueError("Only the unchanged, pending first attempt may be repaired")
    previous = "data/excluded/integrity_repair_20260913T154007Z/manifest.json"
    manifest = read(ROOT / previous)
    if manifest["archived"] or manifest["report"].get("error") != "Prompt projection differs":
        raise ValueError("Unexpected prior interruption")
    shutil.copy2(path, old_plan)
    repaired = []
    for row in plan["after_rows"]:
        if row["problem_id"] in SELECTED:
            before = row["problem_description"]
            row["problem_description"] = prompt_newlines(before)
            if row["problem_description"] != before:
                repaired.append(row["problem_id"])
    plan["previous_attempt_manifest"] = previous
    plan["auxiliary_prompt_newline_repair"] = dict(records=repaired, original_plan=rel(old_plan),
        policy="CRLF to LF in extracted prompt strings only; no HTML, image or PDF bytes changed.")
    save(path, plan)
    print(json.dumps(dict(repaired_prompt_line_endings=repaired, previous_attempt_manifest=previous), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "apply", "verify", "repair-prepared-line-endings"))
    args = parser.parse_args()
    if args.mode == "verify":
        print(json.dumps(verify(read(ROOT / CACHE / "plan.json"), read(ROOT / REPORT)), indent=2))
    else:
        {"prepare": prepare, "apply": apply, "repair-prepared-line-endings": repair_prepared_line_endings}[args.mode]()
