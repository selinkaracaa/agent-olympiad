"""Summarize Phase B matrix JSON file(s) as tables (terminal or markdown).

Usage:
  python3 scripts/summarize_phase_b_matrix.py results/phase_b/wave2_domains_enforced/phase_b_matrix.json
  python3 scripts/summarize_phase_b_matrix.py --markdown report.md MATRIX.json
  python3 scripts/summarize_phase_b_matrix.py --combined --markdown results/phase_b/meeting_combined.md
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMAS = ["single_agent", "centralized", "round_table", "decentralized"]
DEFAULT_TEAMS = ["gpt", "claude", "gemini", "hetero"]
SHORT = {
    "single_agent": "single",
    "centralized": "centr.",
    "round_table": "round",
    "decentralized": "decen.",
}

COMBINED_SECTIONS: list[tuple[str, Path]] = [
    (
        "Wave 1 — Math & programming (rules off)",
        REPO / "results/phase_b/full_matrix/phase_b_matrix.json",
    ),
    (
        "Wave 2 — Non-math domains (rules enforced)",
        REPO / "results/phase_b/wave2_domains_enforced/phase_b_matrix.json",
    ),
]

CONTEST_DESCRIPTIONS: dict[str, str] = {
    "ieo_business_case": (
        "International Economics Olympiad — **Business Case** (2021 RAF2021). "
        "Team of 5 recommends what vehicle/strategy a revived Latvian automaker should "
        "pursue and defends it as a slide deck; web search allowed; graded by slide rubric."
    ),
    "iol_team": (
        "International Linguistics Olympiad — **Team Contest** (Figuig 2005). "
        "Team of 4 reverse-engineers a Berber language from sentence translations: "
        "orthography, transcriptions, and translations; graded by rubric LLM on worked answers."
    ),
    "ioaa_group": (
        "International Olympiad on Astronomy and Astrophysics — **Group round** (2025). "
        "Team of 5 runs a radio-telescope HI-line lab to estimate Galactic rotation and "
        "dark matter; real contest needs instrument CSVs (text-only proxy here)."
    ),
    "icpc": (
        "ICPC World Finals sample — **Programming** (bottles). "
        "Team implements an algorithm; judged locally against public sample tests "
        "(secret tests deferred)."
    ),
    "arml_local": (
        "ARML Local Team Round — short-answer math sheet for a six-person school team "
        "(10 problems, gold **/40**); no calculators or outside help."
    ),
    "arml_national_team": (
        "ARML National Team Round — harder national-meet short answers "
        "(team **/50**); denser olympiad-style problems under time pressure."
    ),
    "purple_comet": (
        "Purple Comet HS — online team math packet (**30** short numeric answers, **/30**); "
        "broad HS contest math suited to splitting work."
    ),
    "hmmt_guts": (
        "HMMT Guts — among the hardest US HS team contests; timed guts short answers (**/50**), "
        "team of 8."
    ),
}

READ_ME = """\
### How to read a cell

Each cell is **task · CS · IHS** (when scored).

| Symbol | Meaning |
|---|---|
| **task** | Correctness vs gold (scale in section title) |
| **CS** | MultiAgentBench coordination (0–5): communication/planning *process* |
| **IHS** | Interaction helpfulness (0–5): whether chat helped the *final answers* |

`—` = cell not run yet. **Hetero × single_agent** uses GPT mini only (one Solo seat).
"""


def _contest_description(competition: str, problem_id: str, rows: list[dict]) -> str:
    if competition in CONTEST_DESCRIPTIONS:
        return CONTEST_DESCRIPTIONS[competition]
    topic = next((r.get("topic") for r in rows if r.get("topic")), None)
    task_type = next((r.get("task_type") for r in rows if r.get("task_type")), None)
    bits = [competition]
    if problem_id and problem_id != "?":
        bits.append(problem_id)
    if topic:
        bits.append(str(topic))
    elif task_type:
        bits.append(str(task_type))
    return " — ".join(bits)


def _contest_order(data: dict, by_contest: dict[str, list[dict]]) -> list[str]:
    ordered: list[str] = []
    for case in data.get("cases") or []:
        competition = case.get("competition")
        if isinstance(competition, str) and competition in by_contest:
            if competition not in ordered:
                ordered.append(competition)
    for competition in sorted(by_contest):
        if competition not in ordered:
            ordered.append(competition)
    return ordered


def _cell_text(row: dict | None) -> str:
    if row is None or row.get("status") != "ok":
        return "—"
    score = row.get("grade_score")
    max_score = row.get("grade_max_score")
    cs = row.get("coordination_score")
    ihs = row.get("interaction_helpfulness_score")
    if score is None or max_score is None:
        return "ok"
    parts = [f"{float(score):g}/{float(max_score):g}"]
    if isinstance(cs, (int, float)):
        parts.append(f"CS {cs:.1f}")
    if isinstance(ihs, (int, float)):
        parts.append(f"IHS {ihs:.1f}")
    return " · ".join(parts)


def _lookup(
    results: list[dict],
    *,
    competition: str,
    team: str,
    schema: str,
) -> dict | None:
    for row in results:
        if (
            row.get("competition") == competition
            and row.get("team") == team
            and row.get("schema") == schema
        ):
            return row
    return None


def _matrix_section(
    data: dict,
    *,
    markdown: bool,
    section_title: str | None = None,
) -> list[str]:
    results = [r for r in data.get("results") or [] if r.get("status") == "ok"]
    schemas = data.get("schemas") or DEFAULT_SCHEMAS
    teams = data.get("teams") or DEFAULT_TEAMS
    by_contest: dict[str, list[dict]] = defaultdict(list)
    for row in results:
        by_contest[row["competition"]].append(row)

    lines: list[str] = []
    rules = data.get("rules_mode", "off")
    expected = len(data.get("cases") or []) * len(teams) * len(schemas)

    if section_title:
        if markdown:
            lines.append(f"# {section_title}")
        else:
            lines.append(f"=== {section_title} ===")
        lines.append(
            f"_{len(results)}/{expected or '?'} cells complete · rules={rules}_"
            if markdown
            else f"{len(results)}/{expected or '?'} cells · rules={rules}"
        )
        lines.append("")

    for competition in _contest_order(data, by_contest):
        rows = by_contest[competition]
        problem_id = rows[0].get("problem_id", "?")
        max_score = next(
            (r.get("grade_max_score") for r in rows if r.get("grade_max_score")),
            None,
        )
        scale = f"/{max_score:g}" if max_score else ""
        title = (
            f"## {competition} ({problem_id}) task{scale}"
            if markdown
            else f"--- {competition} ({problem_id}) task{scale} ---"
        )
        lines.append(title)
        blurb = _contest_description(competition, problem_id, rows)
        if markdown:
            lines.append("")
            lines.append(blurb)
        else:
            lines.append(blurb)

        if markdown:
            lines.append("")
            lines.append("| Team | " + " | ".join(SHORT.get(s, s) for s in schemas) + " |")
            lines.append("|---|" + "|".join("---:" for _ in schemas) + "|")
            for team in teams:
                cells = [
                    _cell_text(_lookup(results, competition=competition, team=team, schema=schema))
                    for schema in schemas
                ]
                lines.append("| " + team + " | " + " | ".join(cells) + " |")
            lines.append("")
        else:
            header_line = f"{'':12}" + "".join(f"{SHORT.get(s, s):>18}" for s in schemas)
            lines.append(header_line)
            for team in teams:
                cells = [
                    _cell_text(_lookup(results, competition=competition, team=team, schema=schema))
                    for schema in schemas
                ]
                lines.append(team.ljust(12) + "".join(f"{c:>18}" for c in cells))
            lines.append("")

        deltas: list[str] = []
        for team in teams:
            solo = _lookup(results, competition=competition, team=team, schema="single_agent")
            if not solo or solo.get("grade_score") is None:
                continue
            solo_score = float(solo["grade_score"])
            multi_scores = []
            for schema in schemas:
                if schema == "single_agent":
                    continue
                row = _lookup(results, competition=competition, team=team, schema=schema)
                if row and row.get("grade_score") is not None:
                    multi_scores.append(float(row["grade_score"]))
            if multi_scores:
                best = max(multi_scores)
                deltas.append(f"{team}: {solo_score:g} → {best:g} (Δ {best - solo_score:+.1f})")
        if deltas:
            label = "**Solo → best multi:** " if markdown else "Solo → best multi:"
            lines.append(label + "; ".join(deltas))
            lines.append("")

    return lines


def _single_matrix_report(data: dict, *, markdown: bool) -> list[str]:
    results = [r for r in data.get("results") or [] if r.get("status") == "ok"]
    rules = data.get("rules_mode", "off")
    teams = data.get("teams") or DEFAULT_TEAMS
    schemas = data.get("schemas") or DEFAULT_SCHEMAS
    expected = len(data.get("cases") or []) * len(teams) * len(schemas)
    lines: list[str] = []
    if markdown:
        lines.append(f"# Phase B summary ({len(results)}/{expected or '?'} cells, rules={rules})")
        lines.append("")
    else:
        lines.append(f"=== Phase B summary ({len(results)}/{expected or '?'} cells, rules={rules}) ===")
        lines.append("")
    lines.extend(_matrix_section(data, markdown=markdown))
    return lines


def combined_report(
    sections: list[tuple[str, dict]],
    *,
    markdown: bool = True,
) -> str:
    lines: list[str] = []
    if markdown:
        lines.append("# Phase B — combined meeting summary")
        lines.append("")
        lines.append(READ_ME.strip())
        lines.append("")
    for index, (title, data) in enumerate(sections):
        if index:
            lines.append("---")
            lines.append("")
        lines.extend(_matrix_section(data, markdown=markdown, section_title=title))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "matrix",
        type=Path,
        nargs="?",
        help="phase_b_matrix.json path (omit with --combined)",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=None,
        help="Write markdown report to this path",
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Merge math full_matrix + wave2 enforced into one report",
    )
    args = parser.parse_args()

    if args.combined:
        sections: list[tuple[str, dict]] = []
        for title, path in COMBINED_SECTIONS:
            if not path.exists():
                raise SystemExit(f"Missing matrix for combined report: {path}")
            sections.append((title, json.loads(path.read_text(encoding="utf-8"))))
        text = combined_report(sections, markdown=bool(args.markdown))
    else:
        if args.matrix is None:
            parser.error("Provide MATRIX.json or use --combined")
        data = json.loads(args.matrix.read_text(encoding="utf-8"))
        text = "\n".join(_single_matrix_report(data, markdown=bool(args.markdown))).rstrip() + "\n"

    print(text, end="")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(text, encoding="utf-8")
        print(f"Wrote {args.markdown}", flush=True)


if __name__ == "__main__":
    main()
