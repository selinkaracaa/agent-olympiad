"""Summarize a Phase B matrix JSON as tables (terminal or markdown).

Usage:
  python3 scripts/summarize_phase_b_matrix.py results/phase_b/wave2_domains_enforced/phase_b_matrix.json
  python3 scripts/summarize_phase_b_matrix.py --markdown report.md results/phase_b/wave2_domains_enforced/phase_b_matrix.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

DEFAULT_SCHEMAS = ["single_agent", "centralized", "round_table", "decentralized"]
DEFAULT_TEAMS = ["gpt", "claude", "gemini", "hetero"]
SHORT = {
    "single_agent": "single",
    "centralized": "centr.",
    "round_table": "round",
    "decentralized": "decen.",
}


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


def _contest_tables(
    data: dict,
    *,
    markdown: bool,
) -> list[str]:
    results = [r for r in data.get("results") or [] if r.get("status") == "ok"]
    schemas = data.get("schemas") or DEFAULT_SCHEMAS
    teams = data.get("teams") or DEFAULT_TEAMS
    by_contest: dict[str, list[dict]] = defaultdict(list)
    for row in results:
        by_contest[row["competition"]].append(row)

    lines: list[str] = []
    rules = data.get("rules_mode", "?")
    expected = len(data.get("cases") or []) * len(teams) * len(schemas)
    header = (
        f"# Phase B summary ({len(results)}/{expected or '?'} cells, rules={rules})"
        if markdown
        else f"=== Phase B summary ({len(results)}/{expected or '?'} cells, rules={rules}) ==="
    )
    lines.append(header)
    lines.append("")

    for competition in sorted(by_contest):
        rows = by_contest[competition]
        problem_id = rows[0].get("problem_id", "?")
        max_score = next(
            (r.get("grade_max_score") for r in rows if r.get("grade_max_score")),
            None,
        )
        scale = f"/{max_score:g}" if max_score else ""
        title = f"## {competition} ({problem_id}) task{scale}" if markdown else f"--- {competition} ({problem_id}) task{scale} ---"
        lines.append(title)

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

        # Solo vs best multi-agent delta per team
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path, help="phase_b_matrix.json path")
    parser.add_argument(
        "--markdown",
        type=Path,
        default=None,
        help="Write markdown report to this path",
    )
    args = parser.parse_args()

    data = json.loads(args.matrix.read_text(encoding="utf-8"))
    lines = _contest_tables(data, markdown=bool(args.markdown))
    text = "\n".join(lines).rstrip() + "\n"
    print(text, end="")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(text, encoding="utf-8")
        print(f"Wrote {args.markdown}", flush=True)


if __name__ == "__main__":
    main()
