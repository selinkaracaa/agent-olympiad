"""Deterministic Phase 2 analysis for run summaries and transcripts.

The CLI accepts one or more JSON files. Files may be phase/competition summaries,
individual transcript artifacts, or rich ``icpcrun.v1`` packets. It writes
``analysis.json`` and ``errors.csv`` atomically.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from evaluation.error_taxonomy import classify_errors
from evaluation.team_metrics import adapt_transcript, compute_team_metrics


def normalized_task_score(row: dict[str, Any]) -> float | None:
    """Return score/max_score in [0, 1], or null when unavailable/invalid."""

    grade = row.get("grade") if isinstance(row.get("grade"), dict) else {}
    score = row.get("grade_score", grade.get("score"))
    maximum = row.get("grade_max_score", grade.get("max_score"))
    if score is None and row.get("score") is not None:
        score = row.get("score")
        maximum = row.get("max_score", 1)
    try:
        score_value = float(score)
        maximum_value = float(maximum)
    except (TypeError, ValueError):
        return None
    if maximum_value <= 0:
        return None
    return min(max(score_value / maximum_value, 0.0), 1.0)


def _condition(row: dict[str, Any]) -> str | None:
    explicit = row.get("condition") or row.get("run_type") or row.get("cell")
    if explicit:
        value = str(explicit).lower()
        if value in {"solo", "single", "single_agent"}:
            return "solo"
        if value in {"subagent", "delegated", "division"}:
            return "subagent"
        if value in {"team", "multi_agent", "collaborative"}:
            return "team"
    schema = str(row.get("schema") or "").lower()
    if schema == "single_agent":
        return "solo"
    if schema in {"subagent", "delegated"}:
        return "subagent"
    if schema:
        return "team"
    return None


def _comparable_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(
        row.get(key)
        for key in ("competition", "problem_id", "task_id", "team", "model_label", "model")
    )


def compute_decompositions(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute three-way gains only for comparable cells.

    ``division_gain = subagent - solo`` and ``cohesion_gain = team - subagent``
    require normalized scores for all three conditions in the same comparison
    key. ``synthesis_loss = transcript_ceiling - team`` additionally requires a
    numeric normalized transcript ceiling in the team cell. Missing or duplicate
    cells yield null values with a machine-readable reason.
    """

    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_comparable_key(row)].append(row)
    output = []
    for key, group in grouped.items():
        cells: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in group:
            condition = _condition(row)
            if condition:
                cells[condition].append(row)

        missing = [name for name in ("solo", "subagent", "team") if len(cells[name]) != 1]
        scores = {
            name: normalized_task_score(cells[name][0]) if len(cells[name]) == 1 else None
            for name in ("solo", "subagent", "team")
        }
        unavailable = [name for name, score in scores.items() if score is None]
        if missing:
            reason = "missing_or_duplicate_cells:" + ",".join(missing)
            division = cohesion = None
        elif unavailable:
            reason = "missing_normalized_score:" + ",".join(unavailable)
            division = cohesion = None
        else:
            reason = None
            division = scores["subagent"] - scores["solo"]  # type: ignore[operator]
            cohesion = scores["team"] - scores["subagent"]  # type: ignore[operator]

        ceiling = None
        if len(cells["team"]) == 1:
            team_cell = cells["team"][0]
            raw_ceiling = team_cell.get("transcript_ceiling")
            if raw_ceiling is None and team_cell.get("transcript_ceiling_score") is not None:
                try:
                    raw_ceiling = float(team_cell["transcript_ceiling_score"]) / float(
                        team_cell["transcript_ceiling_max_score"]
                    )
                except (KeyError, TypeError, ValueError, ZeroDivisionError):
                    raw_ceiling = None
            try:
                ceiling = float(raw_ceiling) if raw_ceiling is not None else None
            except (TypeError, ValueError):
                ceiling = None
        if scores["team"] is None:
            synthesis_loss = None
            synthesis_reason = "missing_team_score"
        elif ceiling is None:
            synthesis_loss = None
            synthesis_reason = "missing_transcript_ceiling"
        elif not 0.0 <= ceiling <= 1.0:
            synthesis_loss = None
            synthesis_reason = "transcript_ceiling_not_normalized"
        else:
            synthesis_loss = ceiling - scores["team"]
            synthesis_reason = None

        output.append(
            {
                "comparison": dict(
                    zip(
                        ("competition", "problem_id", "task_id", "team", "model_label", "model"),
                        key,
                    )
                ),
                "scores": {**scores, "transcript_ceiling": ceiling},
                "division_gain": division,
                "cohesion_gain": cohesion,
                "gain_reason": reason,
                "synthesis_loss": synthesis_loss,
                "synthesis_loss_reason": synthesis_reason,
            }
        )
    return output


def group_summaries(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mean normalized score by competition/schema/team over available scores."""

    groups: dict[tuple[Any, Any, Any], list[float]] = defaultdict(list)
    counts: dict[tuple[Any, Any, Any], int] = defaultdict(int)
    for row in rows:
        key = (row.get("competition"), row.get("schema"), row.get("team"))
        counts[key] += 1
        score = normalized_task_score(row)
        if score is not None:
            groups[key].append(score)
    return [
        {
            "competition": key[0],
            "schema": key[1],
            "team": key[2],
            "runs": counts[key],
            "scored_runs": len(groups[key]),
            "mean_normalized_task_score": (
                sum(groups[key]) / len(groups[key]) if groups[key] else None
            ),
        }
        for key in sorted(counts, key=lambda value: tuple(str(item or "") for item in value))
    ]


def _is_transcript(payload: dict[str, Any]) -> bool:
    return any(key in payload for key in ("chat_history", "discussion", "action_log")) or (
        payload.get("schema_version") == "icpcrun.v1"
    )


def _rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("results"), list):
        return [item for item in payload["results"] if isinstance(item, dict)]
    return [payload]


def _load_transcript(row: dict[str, Any], source_path: Path) -> dict[str, Any] | None:
    if _is_transcript(row):
        return row
    raw_path = row.get("transcript_path")
    if not raw_path:
        return None
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = source_path.parent / path
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def analyze_files(paths: Iterable[Path]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Pure analysis entry point; performs reads but no output writes."""

    analyzed_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []
    for source_path in paths:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        for index, row in enumerate(_rows_from_payload(payload)):
            transcript_payload = _load_transcript(row, source_path)
            metrics = None
            occurrences: list[dict[str, Any]] = []
            transcript_schema = None
            if transcript_payload is not None:
                transcript = adapt_transcript(transcript_payload)
                transcript_schema = transcript.source_schema
                metrics = compute_team_metrics(transcript)
                occurrences = classify_errors(transcript)
            analyzed = {
                **row,
                "source_file": str(source_path),
                "source_index": index,
                "normalized_task_score": normalized_task_score(row),
                "transcript_schema": transcript_schema,
                "team_metrics": metrics,
                "error_count": len(occurrences),
            }
            analyzed_rows.append(analyzed)
            for occurrence in occurrences:
                error_rows.append(
                    {
                        "source_file": str(source_path),
                        "source_index": index,
                        "competition": row.get("competition") or row.get("competition_id"),
                        "problem_id": row.get("problem_id"),
                        "schema": row.get("schema"),
                        **occurrence,
                    }
                )
    analysis = {
        "schema_version": "team-analysis.v1",
        "heuristic_notice": (
            "Content-sensitive transcript metrics and taxonomy triggers are lexical "
            "proxies, not semantic correctness judgments."
        ),
        "runs": analyzed_rows,
        "groups": group_summaries(analyzed_rows),
        "decompositions": compute_decompositions(analyzed_rows),
        "error_count": len(error_rows),
    }
    return analysis, error_rows


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temp = Path(handle.name)
        os.replace(temp, path)
        temp = None
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def _atomic_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source_file",
        "source_index",
        "competition",
        "problem_id",
        "schema",
        "code",
        "name",
        "severity",
        "evidence",
        "turn",
        "agent",
        "heuristic",
    ]
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows({field: row.get(field) for field in fields} for row in rows)
            handle.flush()
            os.fsync(handle.fileno())
            temp = Path(handle.name)
        os.replace(temp, path)
        temp = None
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def write_outputs(
    output_dir: Path, analysis: dict[str, Any], errors: list[dict[str, Any]]
) -> tuple[Path, Path]:
    """Atomically write the two Phase 2 output artifacts."""

    analysis_path = output_dir / "analysis.json"
    errors_path = output_dir / "errors.csv"
    _atomic_json(analysis_path, analysis)
    _atomic_csv(errors_path, errors)
    return analysis_path, errors_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    analysis, errors = analyze_files(args.inputs)
    analysis_path, errors_path = write_outputs(args.output_dir, analysis, errors)
    print(f"Wrote {analysis_path}")
    print(f"Wrote {errors_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
