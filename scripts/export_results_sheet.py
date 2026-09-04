"""Export Phase B matrix or competition_batch results as spreadsheet TSVs.

Usage:
  python3 scripts/export_results_sheet.py results/phase_b/wave2_domains_enforced/phase_b_matrix.json
  python3 scripts/export_results_sheet.py --batch results/non_math_gpt54mini/competition_batch.json
  python3 scripts/export_results_sheet.py MATRIX.json --output-dir results/phase_b/wave2_domains_enforced/sheet
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from run_competition_batch import (  # noqa: E402
    TRACKED_TOOLS,
    _aggregate_metrics,
    enrich_row_tool_usage,
)

CONTEST_TITLES = {
    "ieo_business_case": "IEO Business Case",
    "iol_team": "IOL Team",
    "ioaa_group": "IOAA Group",
    "icpc": "ICPC Programming",
    "codeforces": "Codeforces",
    "wsc_writing": "WSC Writing",
    "iiot": "IIOT",
    "ijso_practical": "IJSO Practical",
    "fyziklani": "Fyziklani",
    "jessup": "Jessup Moot",
}


def _enriched_rows(rows: list[dict]) -> list[dict]:
    return [enrich_row_tool_usage(row) for row in rows]


def _accuracy(score: float | int | None, maximum: float | int | None) -> float | None:
    if not isinstance(score, (int, float)) or not isinstance(maximum, (int, float)) or maximum <= 0:
        return None
    return float(score) / float(maximum)


def _matrix_rows(data: dict) -> list[dict]:
    return [row for row in data.get("results") or [] if row.get("status") == "ok"]


def _detail_row(data: dict, row: dict, *, run_label: str) -> dict:
    row = enrich_row_tool_usage(row)
    score = row.get("grade_score")
    maximum = row.get("grade_max_score")
    accuracy = _accuracy(score, maximum)
    out = {
        "run_dir": run_label,
        "provider": row.get("provider") or data.get("provider") or "",
        "model": row.get("model") or "",
        "team": row.get("team") or "",
        "schema": row.get("schema") or data.get("schema") or "",
        "rules_mode": row.get("rules_mode") or data.get("rules_mode") or "",
        "competition": row.get("competition") or "",
        "contest_title": CONTEST_TITLES.get(row.get("competition", ""), row.get("competition", "")),
        "problem_id": row.get("problem_id") or "",
        "score": score,
        "max_score": maximum,
        "accuracy_pct": round(accuracy * 100, 2) if accuracy is not None else "",
        "Communication": row.get("communication_score"),
        "Planning": row.get("planning_score"),
        "CS": row.get("coordination_score"),
        "IHS": row.get("interaction_helpfulness_score"),
        "tool_usage_summary": row.get("tool_usage_summary") or "",
        "tool_errors": row.get("tool_errors", ""),
        "turns_used": row.get("turns_used"),
        "max_turns": row.get("max_turns"),
        "api_calls": row.get("api_calls"),
        "tokens": row.get("tokens_used"),
        "elapsed_sec": row.get("elapsed_seconds"),
        "wrong_subs": row.get("wrong_submissions"),
        "submitted": int(bool(row.get("submitted"))),
        "grade_method": row.get("grade_method") or "",
        "board_items": row.get("board_items"),
        "board_answered": row.get("board_items_answered"),
        "board_reviewed": row.get("board_items_reviewed"),
        "board_repeats": row.get("board_repeat_attempts"),
        "board_repeat_rate": row.get("board_repeat_rate"),
    }
    for tool in TRACKED_TOOLS:
        out[f"tool_{tool}"] = row.get(f"tool_{tool}", 0)
    return out


def _summary_scope_row(scope: str, metrics: dict) -> dict:
    micro = metrics.get("answer_accuracy_micro")
    macro = metrics.get("answer_accuracy_macro")
    elapsed = metrics.get("total_elapsed_seconds") or 0
    return {
        "competition": scope,
        "tasks": metrics.get("graded_tasks"),
        "score": round(metrics.get("total_task_score") or 0, 2),
        "max_score": round(metrics.get("total_task_max_score") or 0, 2),
        "accuracy_micro": round(micro, 4) if micro is not None else "",
        "accuracy_macro": round(macro, 4) if macro is not None else "",
        "full_credit_tasks": metrics.get("full_credit_tasks"),
        "full_credit_rate": metrics.get("full_credit_task_rate"),
        "Communication": metrics.get("mean_communication_score"),
        "Planning": metrics.get("mean_planning_score"),
        "CS": metrics.get("mean_coordination_score"),
        "board_repeat_rate": metrics.get("mean_board_repeat_rate"),
        "board_answered_frac": metrics.get("mean_board_answered_fraction"),
        "api_calls": metrics.get("total_api_calls"),
        "tokens": metrics.get("total_tokens_used"),
        "elapsed_sec": round(elapsed, 1),
        "elapsed_min": round(elapsed / 60, 1) if elapsed else "",
    }


def _run_group_row(run_label: str, group_rows: list[dict], data: dict) -> dict:
    metrics = _aggregate_metrics(group_rows)
    micro = metrics.get("answer_accuracy_micro")
    macro = metrics.get("answer_accuracy_macro")
    sample = group_rows[0] if group_rows else {}
    return {
        "run_dir": run_label,
        "provider": sample.get("provider") or "",
        "model": sample.get("model") or "",
        "team": sample.get("team") or "",
        "schema": sample.get("schema") or "",
        "rules_mode": sample.get("rules_mode") or data.get("rules_mode") or "",
        "tasks": f"{metrics.get('graded_tasks')}/{len(group_rows)}",
        "graded": metrics.get("graded_tasks"),
        "score": round(metrics.get("total_task_score") or 0, 2),
        "max_score": round(metrics.get("total_task_max_score") or 0, 2),
        "micro_pct": round(micro * 100, 2) if micro is not None else "",
        "macro_pct": round(macro * 100, 2) if macro is not None else "",
        "mean_CS": metrics.get("mean_coordination_score"),
        "api_calls": metrics.get("total_api_calls"),
        "tokens": metrics.get("total_tokens_used"),
        "elapsed_sec": round(metrics.get("total_elapsed_seconds") or 0, 1),
        "note": "",
    }


def _write_tsv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def export_results_sheet_from_rows(
    rows: list[dict],
    *,
    data: dict,
    run_label: str,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _enriched_rows(rows)
    if not rows:
        raise SystemExit("No ok rows to export.")

    by_competition: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_competition[str(row.get("competition"))].append(row)

    summary_rows = [_summary_scope_row("overall", _aggregate_metrics(rows))]
    for competition in sorted(by_competition):
        title = CONTEST_TITLES.get(competition, competition)
        summary_rows.append(_summary_scope_row(title, _aggregate_metrics(by_competition[competition])))

    problem_rows: list[dict] = []
    for row in rows:
        score = row.get("grade_score")
        maximum = row.get("grade_max_score")
        accuracy = _accuracy(score, maximum)
        problem_rows.append(
            {
                "competition": row.get("competition"),
                "problem_id": row.get("problem_id"),
                "score": score,
                "max_score": maximum,
                "accuracy": round(accuracy, 4) if accuracy is not None else "",
                "Communication": row.get("communication_score"),
                "Planning": row.get("planning_score"),
                "CS": row.get("coordination_score"),
                "tool_usage_summary": row.get("tool_usage_summary") or "",
                "board_repeat_rate": row.get("board_repeat_rate"),
                "api_calls": row.get("api_calls"),
                "tokens": row.get("tokens_used"),
                "sec": round(float(row.get("elapsed_seconds") or 0), 1),
            }
        )

    sheet1_path = output_dir / "sheet1_summary.tsv"
    with sheet1_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(list(summary_rows[0].keys()))
        for item in summary_rows:
            writer.writerow([item[k] for k in item])
        writer.writerow([])
        # Header and body both come from the row keys so they cannot drift apart.
        problem_fields = list(problem_rows[0].keys()) if problem_rows else []
        writer.writerow(problem_fields)
        for item in problem_rows:
            writer.writerow([item.get(field) for field in problem_fields])

    run_summary_rows = [_run_group_row(f"{run_label}__TOTAL", rows, data)]

    detail_rows = [_detail_row(data, row, run_label=run_label) for row in rows]
    detail_fields = list(detail_rows[0].keys())

    _write_tsv(
        output_dir / "sheet2_run_summaries.tsv",
        run_summary_rows,
        list(run_summary_rows[0].keys()),
    )
    _write_tsv(output_dir / "sheet2_detail.tsv", detail_rows, detail_fields)

    _write_tsv(output_dir / "competition_summary.tsv", summary_rows, list(summary_rows[0].keys()))
    batch_fields = [
        "competition",
        "problem_id",
        "schema",
        "status",
        "grade_score",
        "grade_max_score",
        "answer_accuracy",
        "communication_score",
        "planning_score",
        "coordination_score",
        "tool_usage_summary",
        *[f"tool_{tool}" for tool in TRACKED_TOOLS],
        "tool_errors",
        "turns_used",
        "max_turns",
        "api_calls",
        "tokens_used",
        "elapsed_seconds",
        "grade_method",
    ]
    _write_tsv(
        output_dir / "competition_batch.tsv",
        [
            {
                "competition": row["competition"],
                "problem_id": row["problem_id"],
                "schema": row["schema"],
                "status": "ok",
                "grade_score": row["score"],
                "grade_max_score": row["max_score"],
                "answer_accuracy": _accuracy(row["score"], row["max_score"]),
                "communication_score": row["Communication"],
                "planning_score": row["Planning"],
                "coordination_score": row["CS"],
                "tool_usage_summary": row["tool_usage_summary"],
                **{f"tool_{tool}": row.get(f"tool_{tool}", 0) for tool in TRACKED_TOOLS},
                "tool_errors": row["tool_errors"],
                "turns_used": row["turns_used"],
                "max_turns": row["max_turns"],
                "api_calls": row["api_calls"],
                "tokens_used": row["tokens"],
                "elapsed_seconds": row["elapsed_sec"],
                "grade_method": row["grade_method"],
            }
            for row in detail_rows
        ],
        batch_fields,
    )

    print(f"Wrote result sheets under {output_dir}/")
    print(f"  sheet1_summary.tsv       — overall + per-contest + per-problem (with tools)")
    print(f"  sheet2_detail.tsv        — full detail incl. tool_* columns")
    print(f"  competition_batch.tsv    — import this to Google Sheets")


def export_results_sheet(data: dict, *, run_label: str, output_dir: Path) -> None:
    rows = _matrix_rows(data)
    if not rows:
        raise SystemExit("No ok rows in matrix JSON.")
    export_results_sheet_from_rows(rows, data=data, run_label=run_label, output_dir=output_dir)


def export_batch_results_sheet(data: dict, *, run_label: str, output_dir: Path) -> None:
    rows = [r for r in data.get("results") or [] if r.get("status") == "ok"]
    if not rows:
        raise SystemExit("No ok rows in competition_batch.json yet.")
    export_results_sheet_from_rows(rows, data=data, run_label=run_label, output_dir=output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input_path",
        type=Path,
        nargs="?",
        help="phase_b_matrix.json or competition_batch.json",
    )
    parser.add_argument(
        "--batch",
        type=Path,
        default=None,
        help="competition_batch.json (alias for input_path)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: <input_dir>/results_sheet)",
    )
    parser.add_argument(
        "--run-label",
        default=None,
        help="run_dir label prefix (default: parent folder name)",
    )
    args = parser.parse_args()

    path = args.batch or args.input_path
    if path is None:
        parser.error("Provide input_path or --batch")
    data = json.loads(path.read_text(encoding="utf-8"))
    output_dir = args.output_dir or (path.parent / "results_sheet")
    run_label = args.run_label or path.parent.name
    if args.batch or path.name == "competition_batch.json":
        export_batch_results_sheet(data, run_label=run_label, output_dir=output_dir)
    else:
        export_results_sheet(data, run_label=run_label, output_dir=output_dir)


if __name__ == "__main__":
    main()
