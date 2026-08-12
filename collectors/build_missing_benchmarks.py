#!/usr/bin/env python3
"""Build benchmark.json for contests that already have PDFs under data/raw/.

Covers the 8 DATA_COLLECTION families missing from data/benchmarks/:
  iypt, hmmt_team, hmmt_guts, mcm, icm, fyziklani, purple_comet, itym

Usage:
  python3 collectors/build_missing_benchmarks.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BENCH = ROOT / "data" / "benchmarks"


def extract_pdf_text(path: Path, max_pages: int | None = None) -> str:
    try:
        reader = PdfReader(str(path))
    except Exception:
        return ""
    chunks: list[str] = []
    pages = reader.pages if max_pages is None else reader.pages[:max_pages]
    for page in pages:
        text = page.extract_text() or ""
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        chunks.append(text.strip())
    return "\n\n".join(c for c in chunks if c).strip()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_benchmark(competition_id: str, entries: list[dict]) -> None:
    out_dir = BENCH / competition_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "benchmark.json"
    entries = sorted(entries, key=lambda e: (e.get("year") or 0, e.get("problem_id") or ""))
    for item in entries:
        item.setdefault("competition_id", competition_id)
        item.setdefault("status", "collected")
    out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {len(entries):3d} → {rel(out_path)}")


def build_iypt() -> None:
    entries = []
    for pdf in sorted((RAW / "iypt").rglob("iypt_*_problems.pdf")):
        m = re.search(r"iypt_(\d{4})_problems", pdf.name)
        if not m:
            continue
        year = int(m.group(1))
        text = extract_pdf_text(pdf)
        if len(text) < 200:
            print(f"  iypt {year}: skip (thin text)")
            continue
        entries.append(
            {
                "problem_id": f"iypt_{year}",
                "competition": "International Young Physicists' Tournament",
                "year": year,
                "topic": f"IYPT Problems {year}",
                "task_type": "open_research",
                "team_size": 5,
                "source_url": "https://www.iypt.org/",
                "source_file": rel(pdf),
                "total_points": None,
                "problem_description": text,
                "gold_label": {
                    "expected_answer": None,
                    "grading_rubric": (
                        "IYPT Physics Fight: Reporter / Opponent / Reviewer. "
                        "Score presentation quality, physics depth, and debate."
                    ),
                    "human_baseline": None,
                },
                "assets": [
                    {"path": rel(pdf), "mime_type": "application/pdf", "role": "agent_visible"}
                ],
            }
        )
    write_benchmark("iypt", entries)


def build_hmmt(kind: str) -> None:
    """kind = team | guts"""
    competition_id = f"hmmt_{kind}"
    name = (
        "HMMT — Team Round"
        if kind == "team"
        else "HMMT — Guts Round"
    )
    pattern = f"hmmt_{kind}_*.pdf"
    entries = []
    for pdf in sorted((RAW / "hmmt").rglob(pattern)):
        m = re.search(rf"hmmt_{kind}_(\d{{4}})", pdf.name)
        if not m:
            continue
        year = int(m.group(1))
        text = extract_pdf_text(pdf)
        if len(text) < 100:
            print(f"  {competition_id} {year}: skip (thin text)")
            continue
        entries.append(
            {
                "problem_id": f"hmmt_{kind}_{year}",
                "competition": name,
                "year": year,
                "topic": f"{name} {year}",
                "task_type": "team_contest",
                "team_size": 8,
                "source_url": "https://hmmt.co/",
                "source_file": rel(pdf),
                "total_points": None,
                "problem_description": text,
                "gold_label": {
                    "expected_answer": None,
                    "grading_rubric": (
                        "HMMT team/guts answers; official solutions published after contest."
                    ),
                    "human_baseline": None,
                },
                "assets": [
                    {"path": rel(pdf), "mime_type": "application/pdf", "role": "agent_visible"}
                ],
            }
        )
    write_benchmark(competition_id, entries)


def build_mcm_icm() -> None:
    mcm_entries: list[dict] = []
    icm_entries: list[dict] = []
    # COMAP: A–C = MCM, D–F = ICM typically
    mcm_letters = set("ABC")
    icm_letters = set("DEF")
    for pdf in sorted((RAW / "mcm_icm").rglob("mcm_icm_*.pdf")):
        m = re.search(r"mcm_icm_([A-F])_(\d{4})", pdf.name, re.I)
        if not m:
            continue
        letter = m.group(1).upper()
        year = int(m.group(2))
        text = extract_pdf_text(pdf)
        if len(text) < 200:
            print(f"  mcm/icm {year} {letter}: skip (thin text)")
            continue
        if letter in mcm_letters:
            competition_id = "mcm"
            competition = "Mathematical Contest in Modeling (MCM)"
            bucket = mcm_entries
        elif letter in icm_letters:
            competition_id = "icm"
            competition = "Interdisciplinary Contest in Modeling (ICM)"
            bucket = icm_entries
        else:
            continue
        bucket.append(
            {
                "problem_id": f"{competition_id}_{year}_{letter}",
                "competition": competition,
                "year": year,
                "topic": f"Problem {letter} ({year})",
                "task_type": "modeling_report",
                "team_size": 3,
                "source_url": "https://www.contest.comap.org/",
                "source_file": rel(pdf),
                "total_points": 100,
                "problem_description": text,
                "gold_label": {
                    "expected_answer": None,
                    "grading_rubric": (
                        "COMAP MCM/ICM report rubric: modeling, analysis, "
                        "communication; ≤25 page PDF report."
                    ),
                    "human_baseline": None,
                },
                "assets": [
                    {"path": rel(pdf), "mime_type": "application/pdf", "role": "agent_visible"}
                ],
            }
        )
    write_benchmark("mcm", mcm_entries)
    write_benchmark("icm", icm_entries)


def build_fyziklani() -> None:
    entries = []
    for pdf in sorted((RAW / "fyziklani").rglob("fyziklani_*_en.pdf")):
        m = re.search(r"fyziklani_(\d{4})", pdf.name)
        if not m:
            continue
        year = int(m.group(1))
        text = extract_pdf_text(pdf)
        if len(text) < 200:
            print(f"  fyziklani {year}: skip (thin text)")
            continue
        entries.append(
            {
                "problem_id": f"fyziklani_{year}",
                "competition": "Physics Brawl Online (Fyziklání)",
                "year": year,
                "topic": f"Physics Brawl Online {year}",
                "task_type": "team_contest",
                "team_size": 5,
                "source_url": "https://physicsbrawl.org/",
                "source_file": rel(pdf),
                "total_points": None,
                "problem_description": text,
                "gold_label": {
                    "expected_answer": None,
                    "grading_rubric": "Physics Brawl online judge / published solutions.",
                    "human_baseline": None,
                },
                "assets": [
                    {"path": rel(pdf), "mime_type": "application/pdf", "role": "agent_visible"}
                ],
            }
        )
    write_benchmark("fyziklani", entries)


def build_purple_comet() -> None:
    entries = []
    for pdf in sorted((RAW / "purple_comet").rglob("purple_comet_*.pdf")):
        m = re.search(r"purple_comet_(hs|ms)_(\d{4})", pdf.name, re.I)
        if not m:
            continue
        level = m.group(1).lower()
        year = int(m.group(2))
        text = extract_pdf_text(pdf)
        if len(text) < 200:
            print(f"  purple_comet {level} {year}: skip (thin text)")
            continue
        entries.append(
            {
                "problem_id": f"purple_comet_{level}_{year}",
                "competition": "Purple Comet! Math Meet",
                "year": year,
                "topic": f"Purple Comet {level.upper()} {year}",
                "task_type": "team_contest",
                "team_size": 6,
                "source_url": "https://purplecomet.org/",
                "source_file": rel(pdf),
                "total_points": 30 if level == "hs" else 20,
                "problem_description": text,
                "gold_label": {
                    "expected_answer": None,
                    "grading_rubric": "Non-negative integer answers; official answer key.",
                    "human_baseline": None,
                },
                "assets": [
                    {"path": rel(pdf), "mime_type": "application/pdf", "role": "agent_visible"}
                ],
            }
        )
    write_benchmark("purple_comet", entries)


def build_itym() -> None:
    entries = []
    for pdf in sorted((RAW / "itym").rglob("itym_*_problems.pdf")):
        m = re.search(r"itym_(\d{4})_problems", pdf.name)
        if not m:
            continue
        year = int(m.group(1))
        text = extract_pdf_text(pdf)
        if len(text) < 200:
            print(f"  itym {year}: skip (thin text)")
            continue
        entries.append(
            {
                "problem_id": f"itym_{year}",
                "competition": "International Tournament of Young Mathematicians",
                "year": year,
                "topic": f"ITYM Problems {year}",
                "task_type": "open_research",
                "team_size": 6,
                "source_url": "https://www.itym.org/",
                "source_file": rel(pdf),
                "total_points": None,
                "problem_description": text,
                "gold_label": {
                    "expected_answer": None,
                    "grading_rubric": (
                        "ITYM research problems; oral presentation + written quiz scoring."
                    ),
                    "human_baseline": None,
                },
                "assets": [
                    {"path": rel(pdf), "mime_type": "application/pdf", "role": "agent_visible"}
                ],
            }
        )
    write_benchmark("itym", entries)


def main() -> None:
    print("Building missing benchmarks from existing data/raw PDFs…")
    build_iypt()
    build_hmmt("team")
    build_hmmt("guts")
    build_mcm_icm()
    build_fyziklani()
    build_purple_comet()
    build_itym()
    print("Done.")


if __name__ == "__main__":
    main()
