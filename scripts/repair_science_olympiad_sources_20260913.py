"""Separate the Solar System sample's contestant pages and official answer key."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import numpy as np
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.repair_data_catalog import Store, provenance, sync_rules
from scripts.build_data_packages import build_packages
from dataset_catalog import scorecard, update_track_index

CID = "science_olympiad"
PID = "science_olympiad_ss1718_annotated_example"
BENCHMARK = f"data/benchmarks/{CID}/benchmark.json"
ORIGINAL = "data/raw/science_olympiad/samples/082317_SS1718_AnnotatedExampleExam.pdf"
SOURCE_URL = "https://www.soinc.org/sites/default/files/uploaded_files/082317_SS1718_AnnotatedExampleExam.pdf"
SOURCE_SHA = "f99c10143552aa71d98333852a86faed7ac2cf82821c5803503de6e28c212b55"
CACHE = "data/.cache/science_olympiad_repair_20260913"
RAW = "data/raw/science_olympiad/separated_20260913"
PUBLIC = RAW + "/input/solar_system_2017_2018_contestant.pdf"
KEY = RAW + "/judge/solar_system_2017_2018_answer_key.pdf"
ANSWERS = RAW + "/judge/answer_reference.json"
RUBRIC = "data/rubrics/science_olympiad_ss1718_answer_key_v1.json"
PROTOCOL = "data/rubrics/science_olympiad_official_scoring_protocol_v1.json"
REPORT = "data/benchmarks/science_olympiad_source_repair_20260913.json"
MANIFEST = RAW + "/manifest.json"
PUBLIC_PAGES = [0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16]
KEY_PAGES = [13, 14]
RED = 16721408


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def spans(page):
    return [s for b in page.get_text("dict")["blocks"] if "lines" in b for line in b["lines"] for s in line["spans"]]


def omitted_span(s, source_page):
    # Retain the official cover title; remove only the distinct author guidance.
    return s["color"] == RED and not (source_page == 0 and s["bbox"][1] < 200)


def answer_reference(original):
    entries = []
    for page_index in KEY_PAGES:
        page = original[page_index]
        for column, clip in enumerate((pymupdf.Rect(72, 85, 306, 710), pymupdf.Rect(306, 85, 548, 710))):
            words = page.get_text("words", clip=clip)
            for row_index in range(25):
                expected = (1 if page_index == 13 else 51) + column * 25 + row_index
                top = 85 + row_index * 25
                selected = sorted([w for w in words if top <= w[1] < top + 25], key=lambda w: w[0])
                if not selected or selected[0][4] != str(expected):
                    raise ValueError(f"Answer cell identity differs: {expected}")
                answer = " ".join(w[4] for w in selected[1:])
                if not answer:
                    raise ValueError("Empty answer cell")
                semantics = ("unordered_set" if "(any order)" in answer else
                             "ordered_sequence" if "(correct order)" in answer else "printed_reference")
                entries.append(dict(question_id=str(expected), printed_answer=answer, points=1,
                    response_semantics=semantics, source_page=page_index + 1, source_column=column + 1,
                    source_row=row_index + 1, cell_bbox=[clip.x0, top, clip.x1, top + 25]))
    entries.sort(key=lambda e: int(e["question_id"]))
    if [int(e["question_id"]) for e in entries] != list(range(1, 101)):
        raise ValueError("Answer coverage is not 1 through 100")
    return dict(visibility="judge_only", source=ORIGINAL, source_sha256=SOURCE_SHA,
        source_url=SOURCE_URL, total_points=100, question_count=100,
        score_basis="Cover says all questions have equal value; answer pages 14 and 15 each contain 50 distinct numbered answers and a 50/50 header. Together they support 100 one-point items for this sample.",
        reference_policy="Preserve printed historical answers, including parenthetical alternatives, ranges and set/order requirements. No aliases or scientific corrections are invented.",
        answers=entries)


def pixel_check(original, public, removals):
    results = []
    for output_page, source_page in enumerate(PUBLIC_PAGES):
        before = original[source_page].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
        after = public[output_page].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
        a = np.frombuffer(before.samples, np.uint8).reshape(before.height, before.width, before.n)
        b = np.frombuffer(after.samples, np.uint8).reshape(after.height, after.width, after.n)
        mask = np.zeros(a.shape[:2], dtype=bool)
        for r in removals[str(source_page)]:
            x0, y0, x1, y1 = r["rect"]
            mask[max(0, int(y0 * 1.5) - 3):int(y1 * 1.5) + 4,
                 max(0, int(x0 * 1.5) - 3):int(x1 * 1.5) + 4] = True
        changed = np.any(a != b, axis=2)
        outside = int(np.count_nonzero(changed & ~mask))
        if outside:
            raise ValueError(f"Pixels changed outside reviewed guidance regions: page {source_page + 1}: {outside}")
        kept = [s["text"] for s in spans(original[source_page]) if not omitted_span(s, source_page)]
        actual = [s["text"] for s in spans(public[output_page])]
        normalized = lambda text: re.sub(r"\s+", "", "".join(text))
        if normalized(kept) != normalized(actual):
            raise ValueError(f"Retained text changed: original page {source_page + 1}")
        if any(omitted_span(s, source_page) for s in spans(public[output_page])):
            raise ValueError("Author guidance remains in PDF text")
        results.append(dict(source_page=source_page + 1, contestant_page=output_page + 1,
                            pixels_changed_outside_guidance=outside, retained_text_unchanged=True))
    return results


def render(pdf, folder):
    folder.mkdir(parents=True, exist_ok=True)
    executable = next((ROOT / CACHE / "poppler").rglob("pdftoppm.exe"))
    subprocess.run([str(executable), "-r", "110", "-png", str(pdf), str(folder / "page")], check=True)


def prepare():
    store = Store(ROOT)
    if store.path(REPORT).exists():
        raise ValueError("Already repaired; use verify")
    if digest(ROOT / ORIGINAL) != SOURCE_SHA or digest(ROOT / CACHE / "publisher.pdf") != SOURCE_SHA:
        raise ValueError("Official and local source differ")
    original = pymupdf.open(ROOT / ORIGINAL)
    if len(original) != 18:
        raise ValueError("Unexpected source page count")
    prepared = store.path(CACHE + "/prepared")
    if prepared.exists():
        raise ValueError("Prepared output already exists")
    (prepared / "input").mkdir(parents=True)
    (prepared / "judge").mkdir()
    removals = {}
    public = pymupdf.open()
    for i in PUBLIC_PAGES:
        public.insert_pdf(original, from_page=i, to_page=i)
        page = public[-1]
        removals[str(i)] = []
        for s in spans(original[i]):
            if omitted_span(s, i):
                rect = pymupdf.Rect(s["bbox"]) + (-0.2, -0.2, 0.2, 0.2)
                removals[str(i)].append(dict(rect=list(rect), text=s["text"]))
                page.add_redact_annot(rect, fill=(1, 1, 1))
        if removals[str(i)]:
            page.apply_redactions(images=0, graphics=0)
    public.set_metadata({"title": "Solar System 2017-2018 - contestant copy", "subject": "Source-preserving sample with author guidance and answer pages removed"})
    public_path = prepared / "input" / Path(PUBLIC).name
    public.save(public_path, garbage=4, deflate=True, clean=True)
    public.close()
    key = pymupdf.open()
    for i in KEY_PAGES:
        key.insert_pdf(original, from_page=i, to_page=i)
    key.set_metadata({"title": "Solar System 2017-2018 - judge-only original answer key"})
    key_path = prepared / "judge" / Path(KEY).name
    key.save(key_path, garbage=4, deflate=True, clean=True)
    key.close()
    public = pymupdf.open(public_path)
    invariants = pixel_check(original, public, removals)
    for i, name in ((0, "cover.png"), (1, "image_sheet_A.png"), (2, "image_sheet_B.png"), (3, "image_sheet_C.png")):
        public[i].get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).save(prepared / "input" / name)
    references = answer_reference(original)
    store.save(relative(prepared / "judge/answer_reference.json"), references)
    question_text = "\n\n".join(public[i].get_text(sort=True) for i in range(4, 10))
    qids = [int(n) for n in re.findall(r"(?m)^\s*(\d{1,3})\.\s", question_text)]
    if qids != list(range(1, 101)):
        raise ValueError(f"Question text coverage differs: {qids}")
    prompt = ("Solar System - Division B, 2017-2018 example exam.\n\n"
        "Use the attached contestant packet, cover image and Image Sheets A, B and C. "
        "Submit answers numbered 1-100. This is a historical sample, so interpret date-dependent questions in its original context.\n\n"
        + public[0].get_text(sort=True) + "\n\n" + question_text)
    for marker in ("ANSWER KEY PAGE", "Advice to Event Supervisors", "With regards to Answer Sheets"):
        if marker in prompt or marker in "\n".join(p.get_text() for p in public):
            raise ValueError("Judge/instructor content remains in contestant input")
    public.close()
    render(public_path, ROOT / CACHE / "contestant_renders")
    render(key_path, ROOT / CACHE / "key_renders")
    rows = deepcopy(store.read(BENCHMARK))
    if len(rows) != 1 or rows[0]["problem_id"] != PID:
        raise ValueError("Unexpected canonical subset")
    before = deepcopy(rows[0])
    row = rows[0]
    limitations = [
        "The complete contestant packet and 100 printed answer references are separated; image-aware end-to-end delivery and grading have not been validated.",
        "Set/sequence answers, numeric ranges and free-text alternatives require a compatible grader; a single normalized string comparison does not implement the printed key.",
        "This is a 2017-2018 Division B Solar System example, not a tournament. Binding season rules, active event team size, timing and permitted-reference limits are not fully archived.",
        "The existing 15-agent research roster is retained as an adaptation, not asserted to be the official active event team size.",
        "Original question wording, image labels, historical claims and printed answer variants are retained; source typos and ambiguous prompts are not silently rewritten.",
    ]
    row.update(source_file=PUBLIC, solution_file=KEY, source_url=SOURCE_URL, problem_description=prompt,
        total_points=100, season="2017-2018", division="B", event="Solar System",
        source_visibility="contestant_packet_separated_from_answer_key",
        source_review=dict(source_pdf=ORIGINAL, source_sha256=SOURCE_SHA, publisher_bytes_verified=True,
            manifest_path=MANIFEST, contestant_source_pages=[i + 1 for i in PUBLIC_PAGES],
            judge_answer_source_pages=[14, 15], excluded_instructor_pages=[2, 3, 4], excluded_blank_pages=[18],
            author_guidance_removal="Only reviewed red text spans outside the official title; raster image labels and all retained page content preserved.",
            score_basis=references["score_basis"], source_typo_examples=[
                "Section B heading says questions 35-48 although the section continues through 52.",
                "Questions 49-52 refer to A-F although the printed object list has A-E.",
                "Section E introduction calls itself Section D."],
            calculator_evidence="Instructor guidance on original page 3 says that this year's rules allow calculators; a binding historical rules manual was not recovered."),
        gold_label=dict(expected_answer=None, human_baseline=before["gold_label"].get("human_baseline"),
            grading_rubric="100 one-point items from the two original 50-point key pages; reference-based grading is not yet validated.",
            parts=[dict(id=e["question_id"], expected=e["printed_answer"], points=1,
                        reference=f"Original PDF page {e['source_page']}, column {e['source_column']}, row {e['source_row']}: {e['printed_answer']}",
                        match_mode="reference_llm", response_semantics=e["response_semantics"], aliases=[]) for e in references["answers"]]))
    row["evaluation"].update(status="not_ready", evaluator_id=None, rubric_path=RUBRIC,
        answer_key_path=ANSWERS, score_basis=references["score_basis"], limitations=limitations,
        answer_contract="Per-question semantic reference; preserve printed unordered-set, ordered-sequence and numeric-range requirements.")
    copies = []
    for file in prepared.rglob("*"):
        if file.is_file():
            copies.append(dict(source=relative(file), destination=RAW + "/" + file.relative_to(prepared).as_posix(), sha256=digest(file)))
    row["assets"] = [dict(path=f["destination"], sha256=f["sha256"],
        role="agent_visible" if "/input/" in f["destination"] else "judge_only",
        mime_type="application/pdf" if f["destination"].endswith(".pdf") else "image/png" if f["destination"].endswith(".png") else "application/json") for f in copies]
    row["assets"].append(dict(path=ORIGINAL, sha256=SOURCE_SHA, role="judge_only", mime_type="application/pdf"))
    provenance(row)
    rubric = dict(rubric_id="science_olympiad_ss1718_answer_key_v1", dataset=CID,
        title="Solar System 2017-2018 example exam - original 100-item answer key", visibility="judge_only",
        total_points=100, rubric_type="source_anchored_sample_answer_key", answer_key_path=ANSWERS,
        scoring_basis=references["score_basis"], grading_validation_status="not_validated",
        criteria=[dict(id=e["question_id"], title="Question " + e["question_id"], max_score=1,
            description="Grade only this numbered response against the printed reference: " + e["printed_answer"],
            reference_answer=e["printed_answer"], response_semantics=e["response_semantics"],
            source_page=e["source_page"]) for e in references["answers"]],
        provenance=dict(source_file=ORIGINAL, source_url=SOURCE_URL, source_sha256=SOURCE_SHA), limitations=limitations)
    protocol = deepcopy(store.read(PROTOCOL))
    for source in protocol.get("provenance", []):
        if "supports" in source:
            source["supports"] = ["two 50-point key pages, 100 numbered answers" if x == "50-point answer key" else x for x in source["supports"]]
    protocol["limitations"] = [x for x in protocol["limitations"] if "50/50 for 100" not in x]
    protocol["archived_sample_raw_score"] = dict(max_score=100, question_count=100, points_per_question=1,
        source_pages=[1, 14, 15], basis=references["score_basis"], scope="Only this archived example, not universal event scoring.")
    rules = {k: deepcopy(store.read(f"data/rules/{CID}/{k}.json")) for k in ("competition", "collaboration", "evaluation")}
    competition = rules["competition"]
    competition["execution"].update(selected_packet=dict(season="2017-2018", division="B", event="Solar System", kind="annotated_example_exam"),
        event_rules="binding_historical_rules_not_archived", event_score_sheet="blank_answer_sheets_in_contestant_packet")
    competition["provenance"]["proxy_limitations"] = [
        "The row now identifies its historical season, division and event; the binding 2017-2018 event rules remain unarchived."
        if "current row lacks season" in x else x for x in competition["provenance"]["proxy_limitations"]]
    sync_rules(CID, rules["evaluation"], rows)
    writes = {BENCHMARK: rows, RUBRIC: rubric, PROTOCOL: protocol,
              f"data/rules/{CID}/competition.json": competition, f"data/rules/{CID}/evaluation.json": rules["evaluation"]}
    expected = {path: digest(ROOT / path) for path in writes if (ROOT / path).exists()}
    original_hashes = {relative(p): digest(p) for p in (ROOT / "data/raw/science_olympiad/samples").rglob("*") if p.is_file()}
    plan = dict(before_row=before, after_rows=rows, writes=writes, copies=copies, expected_hashes=expected,
        original_hashes=original_hashes, original_page_count=18, pixel_checks=invariants, guidance_removals=removals,
        references=references, question_ids=qids, rules=rules)
    store.save(CACHE + "/plan.json", plan)
    print(json.dumps(dict(public_pages=12, judge_pages=2, question_count=len(qids), answers=len(references["answers"]),
        points=100, public_attachments=sum(a["role"] == "agent_visible" for a in row["assets"]),
        pages_with_guidance_removed=sum(bool(v) for v in removals.values()), pixel_checks=invariants), indent=2))


def check_printed_answers(references):
    """Independent Poppler extraction checks the MuPDF coordinate-based mapping."""
    executable = next((ROOT / CACHE / "poppler").rglob("pdftotext.exe"))
    text = subprocess.check_output([str(executable), "-f", "14", "-l", "15", "-layout", str(ROOT / ORIGINAL), "-"]).decode("utf-8")
    recovered = {}
    for line in text.splitlines():
        match = re.fullmatch(r"\s*(\d{1,3})\s+(.+?)\s{2,}(\d{1,3})\s+(.+?)\s*", line)
        if match:
            for number, answer in ((match[1], match[2]), (match[3], match[4])):
                if number in recovered:
                    raise ValueError("Duplicate independently extracted answer")
                recovered[number] = " ".join(answer.split())
    expected = {e["question_id"]: e["printed_answer"] for e in references["answers"]}
    if recovered != expected:
        raise ValueError(f"Independent answer extraction differs: {[n for n in expected if recovered.get(n) != expected[n]]}")
    return len(recovered)


def check_packages(row, directory):
    copies = 0
    sources = {Path(a["path"]).name: a for a in row["assets"] if a["role"] == "agent_visible"}
    generated = {"problem.md", "task_sop.md", "input_environment_spec.md", "ground_rules.md", "collaboration.md"}
    forbidden = ("ANSWER KEY PAGE", "Advice to Event Supervisors", "With regards to Answer Sheets",
                 "/judge/", "data/rubrics/", "C D A E B (correct order)", "EE, HH, GG (any order)")
    for layout in ("base", "last_exam"):
        cards = read(directory / layout / "task_cards.json")["tasks"]
        selected = [c for c in cards if c["task_id"].startswith(CID + "/")]
        if len(selected) != 1 or selected[0]["task_id"] != CID + "/" + PID:
            raise ValueError("Unexpected generated task membership")
        card = selected[0]
        folder = directory / layout / card["source_repo_path"] / "base/input"
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
        if actual != generated | set(sources):
            raise ValueError("Unexpected/missing contestant files")
        for name in generated:
            text = (folder / name).read_text(encoding="utf-8")
            if any(marker in text for marker in forbidden):
                raise ValueError(f"Hidden reference exposed in {layout}/{name}")
        if (folder / "problem.md").read_text(encoding="utf-8") != row["problem_description"] + "\n":
            raise ValueError("Prompt projection differs")
        for name, source in sources.items():
            if digest(folder / name) != source["sha256"]:
                raise ValueError("Copied contestant attachment differs")
            copies += 1
        paths = card["input_files"] if layout == "base" else card["input"]["files"]
        prefix = "input/" if layout == "base" else "base/input/"
        if {f["path"].removeprefix(prefix) for f in paths} != actual:
            raise ValueError("Input file listing differs from disk")
        if layout == "last_exam":
            reference = read(directory / layout / card["source_repo_path"] / "eval/reference.json")
            if reference["evaluation"] != row["evaluation"] or reference["solution_file"] != KEY:
                raise ValueError("Judge reference projection differs")
            for file in (directory / layout / f"competitions/{CID}/input").glob("*.md"):
                if any(marker in file.read_text(encoding="utf-8") for marker in forbidden):
                    raise ValueError("Hidden reference exposed by competition pack")
    return copies


def verify(plan, report):
    for path, expected in {**plan["original_hashes"], **report["preserved_hashes"]}.items():
        if digest(ROOT / path) != expected:
            raise ValueError(f"Protected source or neighboring file changed: {path}")
    rows = read(ROOT / BENCHMARK)
    if rows != plan["after_rows"]:
        raise ValueError("Canonical readback differs")
    row = rows[0]
    for name in ("problem_id", "year", "competition", "team_size", "split", "license", "status"):
        if row[name] != plan["before_row"][name]:
            raise ValueError(f"Protected record field changed: {name}")
    if row["evaluation"]["status"] != "not_ready" or row["evaluation"]["evaluator_id"] is not None:
        raise ValueError("Unexpected readiness promotion")
    for path, value in plan["writes"].items():
        if read(ROOT / path) != value:
            raise ValueError(f"Written metadata differs: {path}")
    for asset in row["assets"]:
        if digest(ROOT / asset["path"]) != asset["sha256"]:
            raise ValueError("Canonical asset hash differs")
    reference = read(ROOT / ANSWERS)
    checked_answers = check_printed_answers(reference)
    parts = row["gold_label"]["parts"]
    if len(parts) != 100 or sum(p["points"] for p in parts) != row["total_points"] or row["total_points"] != 100:
        raise ValueError("Gold coverage or weight sum differs")
    if reference != plan["references"]:
        raise ValueError("Reference answer map differs")
    original = pymupdf.open(ROOT / ORIGINAL)
    public = pymupdf.open(ROOT / PUBLIC)
    key = pymupdf.open(ROOT / KEY)
    if len(public) != 12 or len(key) != 2:
        raise ValueError("PDF page counts differ")
    checked_pixels = pixel_check(original, public, plan["guidance_removals"])
    if checked_pixels != plan["pixel_checks"]:
        raise ValueError("Page preservation checks differ")
    for i, source_page in enumerate(KEY_PAGES):
        if original[source_page].get_text() != key[i].get_text():
            raise ValueError("Original answer page text changed")
        if original[source_page].get_pixmap().samples != key[i].get_pixmap().samples:
            raise ValueError("Original answer page appearance changed")
    if public.embfile_count() or public.get_toc() or any(list(p.annots()) for p in public):
        raise ValueError("Unexpected hidden document objects in contestant PDF")
    actual_public = {relative(p): digest(p) for p in (ROOT / RAW / "input").iterdir() if p.is_file()}
    if actual_public != {a["path"]: a["sha256"] for a in row["assets"] if a["role"] == "agent_visible"}:
        raise ValueError("Raw contestant directory differs from allowlist")
    for i, name in ((0, "cover.png"), (1, "image_sheet_A.png"), (2, "image_sheet_B.png"), (3, "image_sheet_C.png")):
        rendered = public[i].get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        png = pymupdf.Pixmap(str(ROOT / RAW / "input" / name))
        if rendered.samples != png.samples:
            raise ValueError("Public PNG differs from the checked contestant page")
    copied = check_packages(row, ROOT / "data")
    index = read(ROOT / "data/benchmarks/index.json")
    canonical_ids = {t["id"] + "/" + r["problem_id"] for t in index["olympiads"] for r in read(ROOT / t["benchmark_path"])}
    if len(canonical_ids) != index["total_records"] or len(canonical_ids) != report["global_records"]:
        raise ValueError("Global canonical membership/count differs")
    for layout in ("base", "last_exam"):
        for filename, key_name in (("task_cards.json", "tasks"), ("input_asset_manifest.json", "files")):
            catalog = read(ROOT / f"data/{layout}/{filename}")
            values = catalog[key_name]
            if key_name == "tasks" and ({v["task_id"] for v in values} != canonical_ids or len(values) != len(canonical_ids)):
                raise ValueError("Global generated task membership differs")
            others = [v for v in values if not v["task_id"].startswith(CID + "/")]
            if stable(others) != report["unrelated_derived_hashes"][layout + "/" + filename]:
                raise ValueError("Neighboring derived entries changed")
            if key_name == "files":
                ours = [v for v in values if v["task_id"] == CID + "/" + PID]
                if len(ours) != 5:
                    raise ValueError("Input manifest count differs")
                for file in ours:
                    if digest(ROOT / f"data/{layout}" / file["staged"]) != file["sha256"]:
                        raise ValueError("Input manifest hash differs")
    if read(ROOT / f"data/rubrics/task_scorecards/{CID}.json")["records"] != [scorecard(row, ROOT)]:
        raise ValueError("Scorecard projection differs")
    review = report["visual_review"]
    if digest(ROOT / PUBLIC) != review["contestant_pdf_sha256"] or digest(ROOT / KEY) != review["answer_key_pdf_sha256"]:
        raise ValueError("Final PDFs differ from visually inspected versions")
    original.close()
    public.close()
    key.close()
    return dict(canonical_records=1, global_records=len(canonical_ids), questions=100,
        independently_verified_answer_cells=checked_answers, source_anchored_max_score=100,
        contestant_pages=12, judge_answer_pages=2, visually_inspected_pages=14,
        unchanged_pixels_outside_guidance_regions=True, copied_contestant_assets_checked=copied,
        original_raw_files_unchanged=len(plan["original_hashes"]), neighboring_tracks_unchanged=42,
        generated_instruction_answer_key_leaks=0, unexpected_public_files=0,
        readiness_promotions=0, live_evaluation_performed=False)


def apply():
    store = Store(ROOT)
    if store.path(REPORT).exists():
        raise ValueError("Already applied; use verify")
    plan = store.read(CACHE + "/plan.json")
    review = store.read(CACHE + "/visual_review.json")
    for path, expected in {**plan["expected_hashes"], **plan["original_hashes"]}.items():
        if digest(ROOT / path) != expected:
            raise ValueError("Source changed during review")
    check_printed_answers(plan["references"])
    for file in plan["copies"]:
        if digest(ROOT / file["source"]) != file["sha256"] or store.path(file["destination"]).exists():
            raise ValueError("Prepared source changed or destination occupied")
    if digest(ROOT / CACHE / "prepared/input" / Path(PUBLIC).name) != review["contestant_pdf_sha256"]:
        raise ValueError("Contestant PDF changed after visual review")
    if digest(ROOT / CACHE / "prepared/judge" / Path(KEY).name) != review["answer_key_pdf_sha256"]:
        raise ValueError("Judge PDF changed after visual review")
    rows = plan["after_rows"]
    index = deepcopy(store.read("data/benchmarks/index.json"))
    track = next(t for t in index["olympiads"] if t["id"] == CID)
    preserve = [t["benchmark_path"] for t in index["olympiads"] if t["id"] != CID]
    changing = set(plan["writes"]) | {f"data/rubrics/task_scorecards/{CID}.json"}
    for tree in ("data/rules", "data/rubrics"):
        preserve.extend(relative(p) for p in (ROOT / tree).rglob("*.json") if relative(p) not in changing)
    report = dict(operation="science_olympiad_sample_answer_boundary_and_scoring_repair", status="preparing",
        timestamp_utc=store.stamp, backup=relative(store.backup), global_records=index["total_records"],
        preserved_hashes={p: store.sha(p) for p in preserve}, unrelated_derived_hashes={},
        original_pdf_sha256=SOURCE_SHA, publisher_bytes_matched=True, visual_review=review,
        source_page_map=dict(contestant=[i + 1 for i in PUBLIC_PAGES], judge_answers=[14, 15], instructors=[2, 3, 4], blank=[18]),
        scoring_correction=plan["references"]["score_basis"], question_and_answer_count=100,
        source_typo_policy="Preserve source wording; record known defects without inventing corrections.",
        original_prompt_contained_answer_key="ANSWER KEY PAGE" in plan["before_row"]["problem_description"])
    catalogs, manifests = {}, {}
    for layout in ("base", "last_exam"):
        catalogs[layout] = deepcopy(store.read(f"data/{layout}/task_cards.json"))
        manifests[layout] = deepcopy(store.read(f"data/{layout}/input_asset_manifest.json"))
        for filename, values in (("task_cards.json", catalogs[layout]["tasks"]), ("input_asset_manifest.json", manifests[layout]["files"])):
            report["unrelated_derived_hashes"][layout + "/" + filename] = stable([v for v in values if not v["task_id"].startswith(CID + "/")])
    store.finish(report)
    try:
        for file in plan["copies"]:
            target = store.path(file["destination"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / file["source"], target)
            store.changes.append(dict(path=file["destination"], before_sha256=None, after_sha256=file["sha256"]))
        stage = store.path(CACHE + "/packages_" + store.stamp)
        report["packages"] = build_packages(ROOT, stage, {"olympiads": [track]}, {CID: rows}, {CID: plan["rules"]}, store.sha)
        report["staged_asset_checks"] = check_packages(rows[0], stage)
        for layout in catalogs:
            new_cards = {c["task_id"]: c for c in read(stage / layout / "task_cards.json")["tasks"]}
            if set(new_cards) != {CID + "/" + PID}:
                raise ValueError("Staged task membership differs")
            catalogs[layout]["tasks"] = [new_cards.get(c["task_id"], c) for c in catalogs[layout]["tasks"]]
            manifests[layout]["files"] = [f for f in manifests[layout]["files"] if not f["task_id"].startswith(CID + "/")] + read(stage / layout / "input_asset_manifest.json")["files"]
        report["status"] = "applying"
        store.finish(report)
        for path, content in plan["writes"].items():
            store.save(path, content)
        store.save(f"data/rubrics/task_scorecards/{CID}.json", dict(schema_version="1.1", dataset=CID,
            visibility="judge_only", records=[scorecard(rows[0], ROOT)]))
        update_track_index(index, CID, rows)
        index["latest_source_repair_report"] = REPORT
        store.save("data/benchmarks/index.json", index)
        store.save(MANIFEST, dict(visibility="maintainer_only", source_pdf=ORIGINAL, source_sha256=SOURCE_SHA,
            source_url=SOURCE_URL, files=plan["copies"], source_page_map=report["source_page_map"],
            removed_guidance=plan["guidance_removals"], pixel_checks=plan["pixel_checks"], visual_review=review))
        for name in (f"base/tasks/{CID}", f"last_exam/tasks/{CID}", f"last_exam/competitions/{CID}"):
            destination = store.path("data/" + name)
            source = (stage / name).resolve()
            if not source.is_relative_to(stage.resolve()):
                raise ValueError("Staging path escapes the reviewed directory")
            if destination.exists():
                store.archive(destination)
            shutil.copytree(source, destination)
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
    parser.add_argument("mode", choices=("prepare", "apply", "verify"))
    args = parser.parse_args()
    if args.mode == "verify":
        print(json.dumps(verify(read(ROOT / CACHE / "plan.json"), read(ROOT / REPORT)), indent=2))
    else:
        {"prepare": prepare, "apply": apply}[args.mode]()
