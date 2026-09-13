"""Repair audited dataset defects and rebuild derived catalogs without losing originals.

Run normally for the September 2026 migration, or --derived-only after curated
record changes. No split assignments, license grants, or missing gold answers
are invented. Every replaced file/tree has an immutable backup and manifest.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from dataset_catalog import complete_metadata, scorecard, update_track_index
from scripts.build_data_packages import build_packages


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.backup = self.root / "data/excluded" / f"integrity_repair_{self.stamp}"
        self.raw, self.parsed, self.hashes = {}, {}, {}
        self.changes, self.archived = [], []

    def path(self, name) -> Path:
        p = (self.root / name).resolve()
        if not p.is_relative_to(self.root):
            raise ValueError(f"Write outside repository rejected: {p}")
        return p

    def read(self, name):
        p = self.path(name)
        if p not in self.parsed:
            self.raw[p] = p.read_bytes()
            self.parsed[p] = json.loads(self.raw[p].decode("utf-8-sig"))
        return self.parsed[p]

    def sha(self, name) -> str:
        p = self.path(name)
        if p not in self.hashes:
            with p.open("rb") as stream:
                self.hashes[p] = hashlib.file_digest(stream, "sha256").hexdigest()
        return self.hashes[p]

    def save_text(self, name, text: str):
        p = self.path(name)
        payload = text.encode("utf-8")
        old = self.raw.get(p)
        if old is None and p.exists():
            old = p.read_bytes()
        if old == payload:
            return
        if p.exists():
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual != hashlib.sha256(old).hexdigest():
                raise RuntimeError(f"Concurrent edit detected; stopped before overwriting {p}")
            backup = self.backup / p.relative_to(self.root)
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                backup.write_bytes(old)
        p.parent.mkdir(parents=True, exist_ok=True)
        temporary = p.with_name(p.name + ".repair-tmp")
        temporary.write_bytes(payload)
        os.replace(temporary, p)
        self.raw[p] = payload
        self.hashes[p] = hashlib.sha256(payload).hexdigest()
        self.changes.append(dict(path=p.relative_to(self.root).as_posix(),
                                 before_sha256=hashlib.sha256(old).hexdigest() if old is not None else None,
                                 after_sha256=self.hashes[p]))

    def save(self, name, value):
        self.save_text(name, json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        self.parsed[self.path(name)] = value

    def archive(self, name):
        p = self.path(name)
        destination = (self.backup / p.relative_to(self.root)).resolve()
        if not destination.is_relative_to(self.backup.resolve()) or destination.exists():
            raise ValueError(f"Unsafe or occupied archive destination: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        record = dict(path=p.relative_to(self.root).as_posix(), backup=destination.relative_to(self.root).as_posix())
        if p.is_file():
            record["sha256"] = self.sha(name)
        os.replace(p, destination)
        self.archived.append(record)

    def finish(self, report):
        self.backup.mkdir(parents=True, exist_ok=True)
        (self.backup / "manifest.json").write_text(json.dumps(dict(
            created_at_utc=self.stamp, changed_files=self.changes, archived=self.archived,
            report=report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def provenance(row):
    p = row.setdefault("provenance", {})
    p.update(status="source_linked", source_url=row.get("source_url"),
             source_file=row.get("source_file"), solution_file=row.get("solution_file"),
             files=[{k: a[k] for k in ("path", "role", "sha256") if k in a} for a in row.get("assets", [])],
             verification_scope="Source locations, content edition and asset hashes; licensing remains separate.")


def repair_iypt(store, rows, report):
    from collectors.iypt_sources import title_year
    manifest = store.read("data/raw/iypt/verified/manifest.json")
    if manifest["errors"]:
        raise ValueError("Finish edition-verified IYPT collection before migrating")
    sources = {s["year"]: s for s in manifest["sources"]}
    if set(sources) != {r["year"] for r in rows}:
        raise ValueError("IYPT source/record year sets differ")
    wrong, displaced = [], []
    for row in rows:
        source = sources[row["year"]]
        if title_year(source["problem_description"]) != row["year"]:
            raise ValueError(f"IYPT wrong edition: {row['problem_id']}")
        old_path = row.get("source_file")
        if title_year(row.get("problem_description", "")) != row["year"]:
            wrong.append(row["problem_id"])
        if old_path and old_path != source["source_file"] and "/verified/" not in old_path.replace("\\", "/"):
            displaced.append(old_path)
        row.update(source_url=source["source_url"], source_file=source["source_file"],
                   problem_description=source["problem_description"],
                   assets=deepcopy(source["assets"]), status="collected")
        for a in row["assets"]:
            if store.sha(a["path"]) != a["sha256"]:
                raise ValueError(f"IYPT source hash mismatch: {a['path']}")
        row["source_review"] = dict(edition_page=source["edition_page"],
                                   title_year=source["title_year"], source_format=source["format"],
                                   publisher_snapshot=source["publisher_snapshot"],
                                   legacy_assignment_corrected=True)
        provenance(row)
        row["provenance"]["edition_page"] = source["edition_page"]
    report["iypt"] = dict(records=len(rows), corrected_year_assignments=len(wrong),
                           unique_sources=len({r["assets"][0]["sha256"] for r in rows}),
                           source_formats=dict(Counter(s["format"] for s in sources.values())))
    return displaced


def pdf_text(path: Path) -> str:
    import fitz
    with fitz.open(path) as doc:
        if not doc.page_count:
            raise ValueError(f"Empty PDF: {path}")
        return "\n\n".join(page.get_text(sort=True) for page in doc).strip()


def repair_hmmt(store, original, report):
    manifest = store.read("data/raw/hmmt_guts/manifest.json")
    files = {(f["season"], f["year"], f["type"]): f for f in manifest["files"]}
    old = {(r.get("season", "feb"), r["year"]): r for r in original}
    output, matched = [], 0
    for (season, year, kind), source in sorted(files.items()):
        if kind != "problems":
            continue
        solution = files[(season, year, "solutions")]
        problem_path = "data/raw/hmmt_guts/" + source["path"]
        solution_path = "data/raw/hmmt_guts/" + solution["path"]
        for p, expected in [(problem_path, source), (solution_path, solution)]:
            if store.sha(p) != expected["sha256"]:
                raise ValueError(f"HMMT archive mismatch: {p}")
        previous = old.get((season, year))
        if previous and store.sha(previous["source_file"]) != source["sha256"]:
            raise ValueError(f"Existing HMMT record is a different packet: {previous['problem_id']}")
        matched += previous is not None
        row = deepcopy(previous) if previous else dict(
            problem_id=f"hmmt_guts_{year}" if season == "feb" else f"hmmt_guts_nov_{year}",
            competition="HMMT - Guts Round", competition_id="hmmt_guts", task_type="team_contest",
            eval_unit="session", is_multi_agent=True, gold_label=dict(expected_answer=None, human_baseline=None))
        row.update(year=year, season=season, team_size=8 if season == "feb" else 6,
                   topic=f"HMMT Guts {season} {year}", source_url=source["source_url"],
                   source_file=problem_path, solution_file=solution_path,
                   problem_description=pdf_text(store.path(problem_path)), status="collected", total_points=None,
                   season_evidence="Edition identified by the publisher archive manifest and exact problem-file SHA-256.",
                   team_size_basis="Benchmark roster from the existing season rule variant; historical official roster equivalence is not asserted.",
                   assets=[dict(path=problem_path, mime_type="application/pdf", role="agent_visible", sha256=source["sha256"]),
                           dict(path=solution_path, mime_type="application/pdf", role="judge_only", sha256=solution["sha256"])])
        e = row.setdefault("evaluation", {})
        if previous and e.get("evaluator_id") == "gold_answer_v1" and row["gold_label"].get("parts"):
            weights = {m.group(1): int(m.group(2)) for m in re.finditer(r"(?m)^\s*(\d+)\.\s*\[(\d+)\]", row["problem_description"])}
            parts = row["gold_label"]["parts"]
            if set(weights) != {str(p["id"]) for p in parts}:
                raise ValueError(f"HMMT gold/printed-weight coverage differs: {row['problem_id']}")
            for p in parts:
                p["points"] = weights[str(p["id"])]
            total = sum(weights.values())
            rubric_path = f"data/rubrics/{row['problem_id']}_official_weights_v1.json"
            store.save(rubric_path, dict(rubric_id=f"{row['problem_id']}_official_weights_v1",
                title=f"{row['topic']}: printed problem weights", total_points=total,
                source_file=problem_path, source_sha256=source["sha256"],
                criteria=[dict(id=str(p["id"]), name=f"Problem {p['id']}", max_score=p["points"],
                               min_score=0, description="Correct official short answer earns the printed problem weight.") for p in parts]))
            row["total_points"] = total
            e.update(evaluator_id="gold_answer_v1", status="ready", rubric_path=rubric_path,
                     score_basis="Sum of printed per-problem weights for correct curated answers; static packet only.",
                     limitations="Static weighted answer grading; progressive release, hand-in timing, and live standings are not reproduced.")
        else:
            row["gold_label"] = dict(expected_answer=pdf_text(store.path(solution_path)),
                                      grading_rubric="Same-edition official solutions anchor the worked-answer rubric.", human_baseline=None)
            e.update(evaluator_id="rubric_llm_v1", status="ready_with_limitations",
                     rubric_path="data/rubrics/worked_answer_100_v1.json",
                     score_basis="Normalized 100-point written-answer rubric anchored to same-edition official solutions; not official Guts points.",
                     limitations="Official solutions are archived, but complete curated short-answer keys and edition-specific live scoring are not reconstructed. Rubric assessment only; do not compare this directly with official weighted contest scores.")
        e.update(judge_assets=[solution_path], deliverable="numbered_worked_answers" if e["evaluator_id"] == "rubric_llm_v1" else "numbered_answer_sheet")
        provenance(row)
        output.append(row)
    if matched != len(original) or len(output) != 45:
        raise ValueError("HMMT original-record preservation or archive coverage failed")
    report["hmmt_guts"] = dict(before=len(original), after=len(output), added=len(output)-len(original),
                                paired_official_solutions=len(output), status_counts=dict(Counter(r["evaluation"]["status"] for r in output)))
    return sorted(output, key=lambda r: (r["year"], r["season"]))


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)


def external_path(value):
    return isinstance(value, str) and value.replace("\\", "/").startswith("../benchmark/") and "\n" not in value


def relocate(value):
    if external_path(value):
        return "data/raw/external/" + value.replace("\\", "/")[len("../benchmark/"):]
    if isinstance(value, dict):
        return {k: relocate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [relocate(v) for v in value]
    return value


def import_external(store, payloads, report):
    references = sorted({s for value in payloads for s in strings(value) if external_path(s)})
    source_root = (store.root.parent / "benchmark").resolve()
    roots = set()
    for ref in references:
        p = (store.root / ref).resolve()
        if not p.is_relative_to(source_root) or not p.exists():
            raise ValueError(f"Unresolvable external source: {ref}")
        roots.add(p.parent if p.is_file() and p.suffix.lower() in (".html", ".htm") else p)
    roots = [p for p in sorted(roots, key=lambda p: len(p.parts)) if not any(p != q and p.is_relative_to(q) for q in roots)]
    files, total = [], 0
    for source in roots:
        candidates = [source] if source.is_file() else (p for p in source.rglob("*") if p.is_file() and ".git" not in p.parts)
        for p in candidates:
            if not p.resolve().is_relative_to(source_root):
                raise ValueError(f"External archive contains an escaping symlink: {p}")
            destination = store.path(Path("data/raw/external") / p.relative_to(source_root))
            with p.open("rb") as stream:
                original_hash = hashlib.file_digest(stream, "sha256").hexdigest()
            if destination.exists():
                if store.sha(destination) != original_hash:
                    raise ValueError(f"Imported source collision; not overwriting: {destination}")
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, destination)
            if store.sha(destination) != original_hash:
                raise ValueError(f"Imported file hash mismatch: {destination}")
            size = p.stat().st_size
            total += size
            files.append(dict(path=destination.relative_to(store.root).as_posix(), sha256=original_hash, bytes=size))
            if len(files) % 2000 == 0:
                print(f"External sources verified: {len(files)} files", flush=True)
    store.save("data/raw/external/import_manifest.json", dict(
        policy="Referenced source files and HTML sibling assets copied without modifying originals; challenge readiness unchanged.",
        original_reference_map={p: relocate(p) for p in references}, files=files))
    report["external_import"] = dict(references=len(references), files=len(files), bytes=total)


def sync_rules(cid, rule, rows):
    scoring = rule.setdefault("scoring", {})
    live = [r for r in rows if r.get("evaluation", {}).get("evaluator_id")]
    ids = Counter(r["evaluation"]["evaluator_id"] for r in live)
    default = ids.most_common(1)[0][0] if ids else None
    rubric_counts = Counter(r["evaluation"]["rubric_path"] for r in live if r["evaluation"].get("rubric_path"))
    statuses = Counter(r.get("evaluation", {}).get("status", "unknown") for r in rows)
    availability = next(iter(statuses)) if len(statuses) == 1 else "per_record"
    scoring.update(evaluator_id=default, evaluator_status=availability,
                   benchmark_readiness_source=f"data/benchmarks/{cid}/benchmark.json",
                   evaluation_status_counts=dict(statuses),
                   evaluator_selection="Use each benchmark record's evaluation; rule values are defaults only.",
                   record_evaluator_overrides={r["problem_id"]: r["evaluation"]["evaluator_id"] for r in live if r["evaluation"]["evaluator_id"] != default})
    if rubric_counts:
        scoring["rubric_path"] = rubric_counts.most_common(1)[0][0]
    scoring["record_rubric_overrides"] = {r["problem_id"]: r["evaluation"].get("rubric_path") for r in live
                                         if r["evaluation"].get("rubric_path") != scoring.get("rubric_path")}
    official = scoring.get("official_performance", {})
    if official:
        official.update(repository_evaluator_id=default, repository_evaluator_status=availability)
        official["criteria"] = [c for c in official.get("criteria", []) if not str(c).startswith("Repository evaluation status:")]
    current = scoring.get("current_repository_availability", {})
    if current:
        current.update(evaluator_ready=bool(live), evaluator_status=availability,
                       readiness_scope="Per-record metadata; evaluator availability does not imply official-environment reproduction.")
    guidance = rule.get("evaluation_guidance", "")
    sentences = re.split(r"(?<=[.!?])\s+", guidance)
    retained = [s for s in sentences if not ("repository" in s.lower() and
                 any(w in s.lower() for w in ("unassigned", "deferred_benchmark_metadata_missing", "evaluator is unavailable")))]
    prefix = "Resolve readiness, evaluator, rubric, and score basis from the selected benchmark record. "
    rule["evaluation_guidance"] = prefix + " ".join(s for s in retained if not s.startswith("Resolve readiness, evaluator, rubric, and score basis"))


def summary_and_figures(store, index, benchmarks):
    sys.path.insert(0, str(store.root / "data/.cache/catalog_repair_deps"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = [(cid, r) for cid, records in benchmarks.items() for r in records]
    status = Counter(r["evaluation"]["status"] for _, r in rows)
    units = Counter(r["eval_unit"] for _, r in rows)
    domains = {}
    math = {"ijso_practical", "iol_team", "ioaa_group", "arml_power", "arml_national_team", "arml_national_power", "arml_local", "iypt", "hmmt_team", "hmmt_guts", "mcm", "icm", "fyziklani", "purple_comet", "itym", "eoes", "ichto", "pumac_power", "science_olympiad", "wmtc", "wro"}
    coding = {"iiot", "icpc", "codeforces", "cybench", "nyu_ctf_bench", "ccdc", "ioai_team"}
    business = {"ieo_business_case", "gcch_harvard", "cfa_research_challenge", "wharton_investment"}
    for cid in benchmarks:
        domains[cid] = "Math & sciences" if cid in math else "Coding" if cid in coding else "Business & economics" if cid in business else "Humanities & society"
    names = list(benchmarks)
    record_counts = {cid: len(rs) for cid, rs in benchmarks.items()}
    years = [r["year"] for _, r in rows if isinstance(r.get("year"), int)]
    question_counts = {cid: sum(r.get("question_count") if isinstance(r.get("question_count"), int) and r["question_count"] > 0 else 1 for r in rs) for cid, rs in benchmarks.items()}
    summary = dict(schema_version="3.0", generated_at_utc=datetime.now(timezone.utc).isoformat(),
        sources=dict(primary="data/benchmarks/index.json"), n_primary_dataset_ids=len(benchmarks),
        n_total_catalog_ids=len(benchmarks), n_primary_records=len(rows),
        n_question_level_tracks=sum(any(r["eval_unit"] == "question" for r in rs) for rs in benchmarks.values()),
        evaluation_status_counts=dict(status), eval_unit_counts=dict(units), split_counts=dict(Counter(r["split"] for _, r in rows)),
        license_status_counts=dict(Counter(r["license"]["status"] for _, r in rows)),
        record_status_primary=dict(Counter(r.get("status", "unknown") for _, r in rows)),
        coarse_domains_primary_equal_ids=dict(Counter(domains.values())),
        coarse_domains_primary_raw_rows=dict(Counter(domains[cid] for cid, _ in rows)),
        year_min=min(years), year_max=max(years), records_by_track=record_counts,
        primary_question_unit_distribution=dict(by_dataset=question_counts,
             counting_rule="Positive declared question_count; otherwise one record unit. Mixed units are not equal contest sessions."),
        guardrails=["Readiness is record-specific metadata, not end-to-end validation.",
                    "Official points, normalized rubric points and sample-only verdicts must not be pooled as one score.",
                    "Unspecified splits and unverified licenses remain unresolved."])
    store.save("data/viz/summary.json", summary)
    palette = ["#206674", "#d29342", "#d26350", "#7c8e69", "#7e8ba0"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "#f7f5ef", "axes.facecolor": "#f7f5ef", "font.size": 10})
    def save_fig(filename, fig):
        target = store.path("data/viz/" + filename)
        if target.exists():
            store.archive(target)
        fig.savefig(target, dpi=150, bbox_inches="tight")
        plt.close(fig)
    def bars(filename, values, title, xlabel="Records"):
        pairs = sorted(values.items(), key=lambda p: p[1])
        fig, ax = plt.subplots(figsize=(12, max(4, len(pairs)*0.25)))
        ax.barh([p[0] for p in pairs], [p[1] for p in pairs], color=palette[0])
        ax.set(title=title, xlabel=xlabel)
        save_fig(filename, fig)
    bars("01_overview.png", status, "Evaluation status in the canonical catalog")
    bars("02_scale_by_track.png", record_counts, "Records per track (mixed evaluation units)")
    fig, ax = plt.subplots(figsize=(9, 5))
    cats = list(summary["coarse_domains_primary_equal_ids"])
    matrix = [[sum(domains[cid] == d and r["eval_unit"] == u for cid, r in rows) for u in units] for d in cats]
    ax.imshow(matrix, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(len(units)), list(units)); ax.set_yticks(range(len(cats)), cats)
    for i, row in enumerate(matrix):
        for j, count in enumerate(row):
            ax.text(j, i, str(count), ha="center", va="center")
    ax.set_title("Domain and evaluation unit: record counts")
    save_fig("03_domain_type_heatmap.png", fig)
    fig, ax = plt.subplots(figsize=(10, 6))
    for cid, records in benchmarks.items():
        numeric = [r["team_size"] for r in records if isinstance(r.get("team_size"), (int, float))]
        if numeric:
            x = sum(numeric)/len(numeric)
            ax.scatter(x, len(records), color=palette[0], alpha=.7)
            ax.annotate(cid, (x, len(records)), fontsize=6)
    ax.set(xlabel="Mean declared numeric team size", ylabel="Records", title="Declared team size and track scale")
    save_fig("04_teamsize_scale_scatter.png", fig)
    for filename in ("05_year_coverage.png", "11_editions_timeline.png"):
        fig, ax = plt.subplots(figsize=(14, 12))
        for i, cid in enumerate(names):
            ys = sorted({r["year"] for r in benchmarks[cid] if isinstance(r.get("year"), int)})
            ax.scatter(ys, [i]*len(ys), s=12, color=palette[0])
        ax.set_yticks(range(len(names)), names, fontsize=8)
        ax.set(xlabel="Declared edition year", title="Canonical year coverage (dots do not imply continuity)")
        save_fig(filename, fig)
    bars("06_task_types.png", Counter(r.get("task_type", "unknown") for _, r in rows), "Task types")
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    for ax, (label, value) in zip(axes, [("Tracks", len(benchmarks)), ("Records", len(rows)), ("Not ready", status.get("not_ready", 0))]):
        ax.axis("off"); ax.text(.5, .6, f"{value:,}", ha="center", fontsize=44, color=palette[0]); ax.text(.5, .3, label, ha="center", fontsize=17)
    fig.suptitle("Agent Olympiad data inventory")
    save_fig("07_storyboard.png", fig)
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.pie(summary["coarse_domains_primary_raw_rows"].values(), labels=summary["coarse_domains_primary_raw_rows"].keys(), colors=palette, autopct="%1.1f%%")
    ax.set_title("Record composition by domain")
    save_fig("08_domains_pie.png", fig)
    bars("09_question_distribution.png", question_counts, "Declared question counts or single record units", "Question / record units (mixed)")
    return summary


def validate(store, index, benchmarks, rules, stage):
    from collectors.iypt_sources import title_year
    expected = {f"{cid}/{r['problem_id']}" for cid, rs in benchmarks.items() for r in rs}
    assert len(expected) == sum(map(len, benchmarks.values())), "Duplicate problem IDs"
    for cid, rows in benchmarks.items():
        cards = {r["problem_id"]: r for r in store.read(f"data/rubrics/task_scorecards/{cid}.json")["records"]}
        assert set(cards) == {r["problem_id"] for r in rows}
        sc = rules[cid]["evaluation"]["scoring"]
        for r in rows:
            assert all(k in r for k in ("eval_unit", "split", "license", "provenance")), r["problem_id"]
            e = r["evaluation"]
            assert cards[r["problem_id"]]["evaluation_status"] == e["status"]
            assert e["scorecard_key"] == r["problem_id"]
            if e.get("evaluator_id"):
                assert sc.get("record_evaluator_overrides", {}).get(r["problem_id"], sc["evaluator_id"]) == e["evaluator_id"]
                assert sc.get("record_rubric_overrides", {}).get(r["problem_id"], sc.get("rubric_path")) == e.get("rubric_path")
            assert not any(external_path(v) for v in strings(r)), r["problem_id"]
            for key in ("source_file", "solution_file"):
                assert not r.get(key) or store.path(r[key]).exists(), (r["problem_id"], key)
            for a in r.get("assets", []):
                assert store.path(a["path"]).exists(), a["path"]
                if a.get("role") == "agent_visible":
                    assert a["path"] != r.get("solution_file"), r["problem_id"]
            if cid == "iypt":
                assert title_year(r["problem_description"]) == r["year"]
    for layout in ("base", "last_exam"):
        cards = json.loads((stage / layout / "task_cards.json").read_text(encoding="utf-8"))
        catalog = json.loads((stage / layout / "index.json").read_text(encoding="utf-8"))
        assert {r["task_id"] for r in cards["tasks"]} == expected
        assert cards["n_tasks"] == catalog["n_tasks"] == len(expected)
        assert catalog["n_competitions"] == len(benchmarks)
        manifest = json.loads((stage / layout / "input_asset_manifest.json").read_text(encoding="utf-8"))
        for asset in manifest["files"]:
            with (stage / layout / asset["staged"]).open("rb") as stream:
                assert hashlib.file_digest(stream, "sha256").hexdigest() == asset["sha256"], asset["staged"]
    from evaluation.gold import GoldAnswerEvaluator, load_gold_parts
    row = next(r for r in benchmarks["hmmt_guts"] if r["problem_id"] == "hmmt_guts_2024")
    parts = load_gold_parts(row["gold_label"])
    perfect = "\n".join(f"{p.id}. {p.expected}" for p in parts)
    result = GoldAnswerEvaluator(parts=parts, submission_text=perfect).evaluate()
    assert result.total_score == result.max_score == 400
    return dict(records=len(expected), tracks=len(benchmarks), scorecards="matched", package_ids="matched",
                input_assets="hash_verified", iypt_years="matched", hmmt_2024_perfect_score=result.total_score)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--derived-only", action="store_true")
    args = parser.parse_args()
    store = Store(ROOT)
    report = dict(operation="dataset_integrity_repair", timestamp_utc=store.stamp,
                  split_policy="Preserve all existing splits; no random split invented.",
                  license_policy="Preserve unverified licensing; do not infer permission.")
    try:
        index = deepcopy(store.read("data/benchmarks/index.json"))
        benchmarks = {t["id"]: deepcopy(store.read(t["benchmark_path"])) for t in index["olympiads"]}
        rules = {t["id"]: {k: deepcopy(store.read(f"{t['rule_card_path']}/{k}.json")) for k in ("competition", "collaboration", "evaluation")} for t in index["olympiads"]}
        report["before_records"] = sum(map(len, benchmarks.values()))
        displaced = []
        if not args.derived_only:
            displaced = repair_iypt(store, benchmarks["iypt"], report)
            # A previous interrupted run may already have rewired benchmark rows.
            # Keep unused legacy edition filenames out of future raw-file scans.
            active_sources = {store.path(r["source_file"]) for r in benchmarks["iypt"]}
            displaced.extend(p.relative_to(ROOT).as_posix() for p in (ROOT / "data/raw/iypt").glob("*/iypt_*_problems.pdf")
                             if p.resolve() not in active_sources and "verified" not in p.parts)
            benchmarks["hmmt_guts"] = repair_hmmt(store, benchmarks["hmmt_guts"], report)
        # Include rubric answer maps in path relocation, not only benchmark rows.
        rubric_paths = list((ROOT / "data/rubrics").glob("*.json"))
        rubric_payloads = {p: deepcopy(store.read(p)) for p in rubric_paths}
        if any(external_path(s) for value in [benchmarks, rules, rubric_payloads] for s in strings(value)):
            import_external(store, [benchmarks, rules, rubric_payloads], report)
            benchmarks, rules = relocate(benchmarks), relocate(rules)
            for p, data in rubric_payloads.items():
                store.save(p, relocate(data))
        for row in benchmarks["codeforces"]:
            package = row["evaluation"]["official_bundle_path"]
            statement = package + "/statement.html"
            row.setdefault("source_file", statement)
            if not row.get("assets"):
                row["assets"] = [dict(path=statement, mime_type="text/html", role="agent_visible", sha256=store.sha(statement))]
            row["evaluation"].setdefault("rubric_path", "data/rubrics/codeforces_programming_judge_v1.json")
            row["evaluation"].setdefault("test_scope", "sample_only_local")
            row["evaluation"].setdefault("official_verdict_requires", "Remote authoritative verdict or authorized secret tests; public samples alone do not establish acceptance.")
            row["evaluation"].setdefault("deliverable", "source_code")
        for track in index["olympiads"]:
            cid = track["id"]
            rows = benchmarks[cid]
            for row in rows:
                complete_metadata(row, cid, ROOT)
                provenance(row)
            sync_rules(cid, rules[cid]["evaluation"], rows)
            store.save(track["benchmark_path"], rows)
            store.save(f"{track['rule_card_path']}/evaluation.json", rules[cid]["evaluation"])
            store.save(f"data/rubrics/task_scorecards/{cid}.json", dict(schema_version="1.1", dataset=cid, visibility="judge_only",
                       records=[scorecard(r, ROOT, read_json=store.read, hash_file=store.sha) for r in rows]))
            update_track_index(index, cid, rows)
        index["description"] = f"Agent Olympiad - {len(benchmarks)} tracks; mixed-unit team-task corpus. Readiness is per record."
        store.save("data/benchmarks/index.json", index)
        collection_path = "data/raw/collection_manifest.json"
        if not args.derived_only and store.path(collection_path).exists():
            collection = deepcopy(store.read(collection_path))
            if isinstance(collection.get("entries"), list):
                collection["entries"] = [e for e in collection["entries"] if e.get("comp") not in ("iypt", "hmmt_guts")]
                collection["entries"] += [dict(comp=cid, year=r["year"], season=r.get("season"), file=r["source_file"], url=r["source_url"],
                                               questions=r.get("question_count", 0)) for cid in ("iypt", "hmmt_guts") for r in benchmarks[cid]]
                for cid in ("iypt", "hmmt_guts"):
                    collection.setdefault("summary", {})[cid] = dict(sessions=len(benchmarks[cid]), questions=None,
                        note="Session coverage repaired; no unverified internal question count inferred.")
                store.save(collection_path, collection)
        summary = summary_and_figures(store, index, benchmarks)
        stage = ROOT / "data/.cache" / f"packages_{store.stamp}"
        if stage.exists():
            raise ValueError(f"Staging directory already exists: {stage}")
        report["packages"] = build_packages(ROOT, stage, index, benchmarks, rules, store.sha)
        report["validation"] = validate(store, index, benchmarks, rules, stage)
        for layout in ("base", "last_exam"):
            target = store.path("data/" + layout)
            if target.exists():
                store.archive(target)
            source = (stage / layout).resolve()
            assert source.is_relative_to((ROOT / "data/.cache").resolve())
            os.replace(source, target)
        for p in dict.fromkeys(displaced):
            if store.path(p).exists():
                store.archive(p)
        readme = ROOT / "data/benchmarks/README.md"
        text = readme.read_text(encoding="utf-8")
        text = text.split("\n## Integrity repair (September 2026)")[0].rstrip() + "\n"
        text = text.replace("1,738 records", f"{index['total_records']:,} records")
        text += ("\n## Integrity repair (September 2026)\n\n"
                 "IYPT sources use publisher edition headings and retain local illustrations. HMMT Guts includes both seasons of the verified 45-session archive. "
                 "HMMT 2024 uses printed weights; other Guts records use an explicitly normalized reference-anchored rubric. "
                 "Rule scoring defaults have explicit per-record overrides. Generated task inputs contain only agent-visible assets. "
                 "External source references are materialized under data/raw/external. Unspecified splits and unverified licenses remain unresolved.\n\n"
                 "Repair report: `integrity_repair_report.json`. Regenerate packages and figures with `python scripts/repair_data_catalog.py --derived-only`.\n")
        store.save_text(readme, text)
        store.save_text("data/README.md", "# Agent Olympiad data\n\n"
            f"Canonical catalog: `benchmarks/index.json` ({len(benchmarks)} tracks, {index['total_records']:,} records).\n\n"
            "`benchmarks/` and `rules/` are canonical. `base/`, `last_exam/`, and `viz/` are synchronized derived artifacts. "
            "`raw/` preserves source material; `rubrics/` and `evaluators/` are judge-side inputs. `excluded/` contains historical backups.\n\n"
            "Only assets explicitly labeled `agent_visible` enter task inputs. Read each record's `evaluation.status`, limitations, and score basis before use. "
            "Raw source trees can contain answers and must not be exposed wholesale to contestants.\n\n"
            "Run `python scripts/repair_data_catalog.py --derived-only` after curated changes. "
            "Current counts are in `viz/summary.json`; readiness labels are not end-to-end validation. "
            "Existing split assignments are preserved; `unspecified` is unresolved. `not_verified` licenses do not grant redistribution rights.\n")
        report.update(after_records=index["total_records"], evaluation_status_counts=summary["evaluation_status_counts"],
                      unresolved=dict(splits=summary["split_counts"], licenses=summary["license_status_counts"],
                                      not_ready=summary["evaluation_status_counts"].get("not_ready", 0)),
                      backup=store.backup.relative_to(ROOT).as_posix(), status="completed")
        store.save("data/benchmarks/integrity_repair_report.json", report)
        store.finish(report)
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    except Exception as exc:
        report.update(status="interrupted", error=str(exc))
        store.finish(report)
        raise


if __name__ == "__main__":
    main()
