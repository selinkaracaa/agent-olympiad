#!/usr/bin/env python3
"""Aggregate gold-suite contest-session results into a markdown report."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))


def _comp(row: dict) -> str:
    if row.get("competition_id"):
        return str(row["competition_id"])
    pid = row.get("problem_id") or ""
    if pid.startswith("arml_local"):
        return "arml_local"
    if pid.startswith("arml_national"):
        return "arml_national_team"
    if pid.startswith("science_bowl"):
        return "science_bowl"
    if pid.startswith("qanta"):
        return "qanta"
    if pid.startswith("mystery_hunt"):
        return "mystery_hunt"
    if pid.startswith("history_olympiad"):
        return "history_olympiad"
    if pid.startswith("purple_comet"):
        return "purple_comet"
    if pid.startswith("hmmt_guts"):
        return "hmmt_guts"
    if pid.startswith("wmtc"):
        return "wmtc"
    return "unknown"


def _f(row: dict, key: str) -> float | None:
    raw = row.get(key)
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _stats(rows: list[dict]) -> dict:
    ok = [r for r in rows if r.get("status") == "ok"]
    utils = [v for v in (_f(r, "task_utility") for r in ok) if v is not None]
    css = [v for v in (_f(r, "coordination_score") for r in ok) if v is not None]
    return {
        "n": len(rows),
        "ok": len(ok),
        "nonzero": sum(1 for v in utils if v > 0),
        "mean_util": (sum(utils) / len(utils)) if utils else 0.0,
        "mean_cs": (sum(css) / len(css)) if css else 0.0,
    }


def section(title: str, roots: list[tuple[str, Path]]) -> list[str]:
    lines = [f"## {title}", ""]
    lines.append("| Variant | Competition | N ok | Nonzero util | Mean util | Mean CS |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for variant, root in roots:
        rows = _load(root / "summary.tsv")
        if not rows:
            lines.append(f"| {variant} | *(pending / empty)* | 0 | 0 | — | — |")
            continue
        by = defaultdict(list)
        for row in rows:
            by[_comp(row)].append(row)
        for comp in sorted(by):
            s = _stats(by[comp])
            lines.append(
                f"| {variant} | `{comp}` | {s['ok']}/{s['n']} | {s['nonzero']} | "
                f"{s['mean_util']:.3f} | {s['mean_cs']:.2f} |"
            )
        all_s = _stats(rows)
        lines.append(
            f"| {variant} | **ALL** | {all_s['ok']}/{all_s['n']} | {all_s['nonzero']} | "
            f"{all_s['mean_util']:.3f} | {all_s['mean_cs']:.2f} |"
        )
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO / "results" / "gold_suite_results_20260903.md",
    )
    args = parser.parse_args()

    wave1 = [
        ("OTC", REPO / "results" / "otc_arml_science_bowl_20260903"),
        ("Vanilla", REPO / "results" / "vanilla_arml_science_bowl_20260903"),
    ]
    remaining = [
        ("OTC", REPO / "results" / "otc_gold_remaining_20260903"),
        ("Vanilla", REPO / "results" / "vanilla_gold_remaining_20260903"),
    ]

    lines = [
        "# Gold Suite Contest-Session Results",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Scope: deterministic structured-gold competitions on contest-session path "
        "(`strategic_team` = open_table_coach / OTC, `vanilla_team` = rules+tools only).",
        "",
        "**Excluded:** `nyu_ctf_bench`, CTF/cyber (`cybench`, `ccdc`), programming "
        "(`icpc`, `codeforces`, `iiot`, …), and CFA research labels.",
        "",
        "Model: Perplexity `openai/gpt-5.4-mini`, native function calling, team size 3.",
        "",
        "## Notes",
        "",
        "- Wave 1 Science Bowl initially scored all zeros due to single-part grading "
          "requiring numbered sheets; sessions were **regraded** after the fix.",
        "- Vanilla ARML Local still shows 0 utility after regrade (likely empty/wrong "
          "submissions, not just parsing).",
        "- Remaining suite: ARML National Team, Qanta, Mystery Hunt, History Olympiad, "
          "Purple Comet, HMMT Guts, WMTC (625 sessions × OTC + vanilla).",
        "",
    ]
    lines.extend(section("Wave 1 — ARML Local + Science Bowl (regraded)", wave1))
    lines.extend(section("Remaining gold competitions", remaining))
    lines.extend(
        [
            "## Paths",
            "",
            "- `results/otc_arml_science_bowl_20260903/`",
            "- `results/vanilla_arml_science_bowl_20260903/`",
            "- `results/otc_gold_remaining_20260903/`",
            "- `results/vanilla_gold_remaining_20260903/`",
            "",
            "Regenerate this file:",
            "",
            "```bash",
            "python scripts/write_gold_suite_report.py",
            "```",
            "",
        ]
    )
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
