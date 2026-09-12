#!/usr/bin/env python3
"""Derive per-contest ARML power-round rubrics from the benchmark problem text.

ARML power packets are proof/exploration contests (40 official points for
``arml_power``, 50 for ``arml_national_power``), and the extracted PDF text
keeps each award inline as a bracketed weight in one of two shapes:

    Problem 5. State and prove a conjecture ...[4]      (2018-2020 packets)
    5. Prove that E2(n) satisfies ... [3 pts.]           (2021+ packets)
    1b. Find and justify formulas for m and j ... [2]    (national power packets)

Every bracketed weight is one thing the graders award points for, so each marker
becomes one rubric criterion: the statement text running up to the marker, worth
the marker's points. Headings are tracked alongside so criteria carry the
contest's own labels where the packet numbers its parts (``problem_01b``), and a
synthesised suffix where it does not (``problem_09a`` / ``problem_09b``).
Summing the recovered weights reproduces the official total for 13 of the 15
``arml_power`` contests, which is the check that the split is faithful.

``finalize.apply_registered_judge`` rescales the rubric to the problem's
``total_points``, so a packet whose markers were partly lost in PDF extraction
gets its remaining criteria inflated. Contests below ``--min-coverage`` are
therefore left on their generic rubric instead.

Writes ``data/rubrics/<problem_id>_v1.json``; pass ``--link-benchmark`` to point
each problem's ``evaluation.rubric_path`` at its derived rubric.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import string
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPO_ROOT / "data" / "benchmarks"
RUBRIC_DIR = REPO_ROOT / "data" / "rubrics"
DEFAULT_MIN_COVERAGE = 0.8

# "[4]", "[3 pts.]", "[1 pt.]", "[2 points]"
POINT_MARKER = re.compile(r"\[\s*(\d{1,2})\s*(?:pts?\.?|points?)?\s*\]", re.IGNORECASE)
# Where the numbered problems begin; everything before is background prose.
PROBLEM_SECTION = re.compile(r"The Problems\b", re.IGNORECASE)
# Headings look like "Problem 7." (2018-2020) or a bare "7." / "7b." (2021+ and
# national power). Bare digits also occur inside formulas, so only fall back to
# them when the packet has no labelled headings at all.
LABELLED_HEADING = re.compile(r"Problem\s+(\d{1,2})\s*([a-z]?)\s*[.:]", re.IGNORECASE)
BARE_HEADING = re.compile(r"(?<![\d.])(\d{1,2})\s*([a-z]?)\s*\.\s")
MIN_LABELLED_HEADINGS = 3
# How far the problem number may jump forward within a single scored segment.
MAX_NUMBER_LOOKAHEAD = 3
STATEMENT_LIMIT = 700


@dataclass(frozen=True)
class Award:
    """One bracketed point award and the statement text it terminates."""

    criterion_id: str
    label: str
    number: int
    points: int
    text: str


# A heading is ordered by (number, letter); "1b" follows "1a" and precedes "2".
Heading = tuple[int, str]


def _latest_heading(segment: str, current: Heading, *, labelled: bool) -> Heading:
    """Return the furthest heading in the segment that advances past `current`."""
    pattern = LABELLED_HEADING if labelled else BARE_HEADING
    best = current
    for match in pattern.finditer(segment):
        number = int(match.group(1))
        if not current[0] <= number <= current[0] + MAX_NUMBER_LOOKAHEAD:
            continue
        candidate = (number, (match.group(2) or "").lower())
        if candidate > best:
            best = candidate
    return best


def _statement_offset(description: str) -> int:
    """Skip the background prose, but never skip past a scored problem."""
    first_marker = POINT_MARKER.search(description)
    if first_marker is None:
        return 0
    for section in PROBLEM_SECTION.finditer(description):
        if section.end() < first_marker.start():
            return section.end()
    return 0


def _trim_to_heading(segment: str, heading: Heading, *, labelled: bool) -> str:
    """Drop lead-in prose so the criterion quotes the problem statement itself."""
    pattern = LABELLED_HEADING if labelled else BARE_HEADING
    starts = [
        match.start()
        for match in pattern.finditer(segment)
        if (int(match.group(1)), (match.group(2) or "").lower()) == heading
    ]
    return segment[starts[-1] :] if starts else segment


def _name(heading: Heading, part: int, parts_total: int) -> tuple[str, str]:
    """Build the criterion id and human label for one award under a heading."""
    number, letter = heading
    if parts_total > 1 and not letter:
        # The packet gave one heading several awards; synthesise (a)/(b)/(c).
        letter = string.ascii_lowercase[part]
    elif parts_total > 1:
        # The packet already lettered the part and still split the award.
        return (
            f"problem_{number:02d}{letter}_{part + 1}",
            f"Problem {number}{letter} (award {part + 1})",
        )
    return f"problem_{number:02d}{letter}", f"Problem {number}{letter}"


def _disambiguate(awards: list[Award]) -> list[Award]:
    """Keep criterion ids unique within a rubric.

    A packet can label some parts itself ("3a.", "3b.") while other awards land
    on the bare heading ("3"), and the synthesised a/b/c suffixes then collide
    with the packet's own letters.
    """
    seen: dict[str, int] = {}
    unique: list[Award] = []
    for award in awards:
        count = seen.get(award.criterion_id, 0) + 1
        seen[award.criterion_id] = count
        if count == 1:
            unique.append(award)
            continue
        unique.append(
            Award(
                criterion_id=f"{award.criterion_id}_{count}",
                label=f"{award.label} (award {count})",
                number=award.number,
                points=award.points,
                text=award.text,
            )
        )
    return unique


def parse_awards(description: str) -> list[Award]:
    labelled = len(LABELLED_HEADING.findall(description)) >= MIN_LABELLED_HEADINGS
    cursor = _statement_offset(description)
    parsed: list[tuple[Heading, int, int, str]] = []
    heading: Heading = (0, "")
    part_counts: dict[Heading, int] = {}

    for marker in POINT_MARKER.finditer(description, cursor):
        segment = description[cursor : marker.start()]
        cursor = marker.end()
        heading = _latest_heading(segment, heading, labelled=labelled)
        if heading[0] == 0:
            heading = (1, heading[1])
        part = part_counts.get(heading, 0)
        part_counts[heading] = part + 1
        text = _trim_to_heading(segment, heading, labelled=labelled) if part == 0 else segment
        parsed.append((heading, part, int(marker.group(1)), re.sub(r"\s+", " ", text).strip()))

    awards: list[Award] = []
    for heading, part, points, text in parsed:
        criterion_id, label = _name(heading, part, part_counts[heading])
        awards.append(
            Award(
                criterion_id=criterion_id,
                label=label,
                number=heading[0],
                points=points,
                text=text,
            )
        )
    return _disambiguate(awards)


def build_rubric(problem: dict, awards: list[Award], *, default_total: float) -> dict:
    problem_id = str(problem["problem_id"])
    official_total = float(problem.get("total_points") or default_total)
    parsed_total = float(sum(award.points for award in awards))
    criteria = [
        {
            "id": award.criterion_id,
            "name": award.label,
            "max_score": float(award.points),
            "observable": True,
            "description": (
                f"Correct, justified solution to {award.label} "
                f"({award.points} pt{'s' if award.points != 1 else ''}). "
                f"Statement: {award.text[-STATEMENT_LIMIT:]}"
            ),
        }
        for award in awards
    ]
    return {
        "rubric_id": f"{problem_id}_v1",
        "title": f"{problem.get('topic') or problem_id} — ARML Power sub-problem rubric",
        "total_points": parsed_total,
        "criteria": criteria,
        "not_observable_from_deck": [
            "oral defense",
            "diagrams that were not recovered from the source PDF",
        ],
        "provenance": {
            "competition_id": problem.get("competition_id"),
            "problem_id": problem_id,
            "year": problem.get("year"),
            "source_file": problem.get("source_file"),
            "solution_file": problem.get("solution_file"),
            "official_total_points": official_total,
            "parsed_total_points": parsed_total,
            "points_coverage": round(parsed_total / official_total, 4)
            if official_total
            else None,
            "awards_parsed": len(awards),
            "problems_parsed": len({award.number for award in awards}),
            "derived_by": "scripts/build_arml_power_rubrics.py",
        },
    }


def _replace_json_atomic(path: Path, payload: object) -> None:
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False, suffix=".tmp"
    )
    try:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        handle.close()
    os.replace(handle.name, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--competition",
        default="arml_power",
        choices=["arml_power", "arml_national_power"],
        help="Which power-round benchmark to parse.",
    )
    parser.add_argument(
        "--link-benchmark",
        action="store_true",
        help="Point each problem's evaluation.rubric_path at its derived rubric.",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=DEFAULT_MIN_COVERAGE,
        help="Skip contests whose recovered points fall below this share of the official total.",
    )
    args = parser.parse_args()

    benchmark = BENCHMARK_ROOT / args.competition / "benchmark.json"
    default_total = 50.0 if args.competition == "arml_national_power" else 40.0
    problems = json.loads(benchmark.read_text(encoding="utf-8"))
    RUBRIC_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    linked = 0
    low_coverage: list[str] = []
    no_markers: list[str] = []

    for problem in problems:
        problem_id = str(problem["problem_id"])
        awards = parse_awards(str(problem.get("problem_description") or ""))
        if not awards:
            no_markers.append(problem_id)
            continue
        rubric = build_rubric(problem, awards, default_total=default_total)
        path = RUBRIC_DIR / f"{rubric['rubric_id']}.json"
        path.write_text(json.dumps(rubric, indent=2) + "\n", encoding="utf-8")
        written += 1

        meta = rubric["provenance"]
        coverage = meta["points_coverage"] or 0.0
        usable = coverage >= args.min_coverage
        print(
            f"{problem_id:30s} {meta['awards_parsed']:2d} awards / "
            f"{meta['problems_parsed']:2d} problems  "
            f"{meta['parsed_total_points']:g}/{meta['official_total_points']:g} pts "
            f"({coverage:.0%})"
            f"{'' if usable else '  [below --min-coverage, not linked]'}"
        )
        if not usable:
            low_coverage.append(problem_id)
            continue
        if args.link_benchmark:
            evaluation = dict(problem.get("evaluation") or {})
            evaluation["evaluator_id"] = evaluation.get("evaluator_id") or "rubric_llm_v1"
            evaluation["rubric_path"] = path.relative_to(REPO_ROOT).as_posix()
            evaluation["deliverable"] = evaluation.get("deliverable") or "proof_packet"
            problem["evaluation"] = evaluation
            linked += 1

    if args.link_benchmark and linked:
        _replace_json_atomic(benchmark, problems)
        print(f"linked {linked} rubric paths into {benchmark.relative_to(REPO_ROOT)}")

    print(f"\nwrote {written}/{len(problems)} rubrics into {RUBRIC_DIR.relative_to(REPO_ROOT)}")
    if low_coverage:
        print(f"left on generic rubric (low coverage): {', '.join(low_coverage)}")
    if no_markers:
        print(f"no point markers recovered: {', '.join(no_markers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
