"""One-axis-at-a-time solo handicap sweep with atomic JSON output."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from collaboration import CollabConfig, run_collaboration
from env import OlympiadEnvironment
from llm import make_perplexity_caller, resolve_query_fn


DEFAULT_AXES: dict[str, list[Any]] = {
    "turns": [1, 2, 4, 8],
    "output_tokens": [256, 512, 1024, 2048],
    "visible_context_window": [2000, 8000, 32000],
    "calls_per_turn": [1, 2, 4],
    "model_label": ["mock-small", "mock-medium", "mock-large"],
}


def build_handicap_cells(
    base: dict[str, Any] | None = None,
    axes: dict[str, Iterable[Any]] | None = None,
) -> list[dict[str, Any]]:
    """Create cells where exactly one solo resource axis differs from base."""
    baseline = {
        "turns": 1,
        "output_tokens": 512,
        "visible_context_window": 8000,
        "calls_per_turn": 1,
        "model_label": "mock-medium",
        **(base or {}),
    }
    cells: list[dict[str, Any]] = []
    for axis, values in (axes or DEFAULT_AXES).items():
        for value in values:
            config = dict(baseline)
            config[axis] = value
            cells.append({"axis": axis, "value": value, "solo_config": config})
    return cells


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("results", "cells", "rows"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return [payload]


def _score(row: dict[str, Any]) -> float | None:
    for key in ("grade_score", "score", "task_score"):
        value = row.get(key)
        if isinstance(value, (int, float)):
            maximum = row.get("grade_max_score")
            if key == "grade_score" and isinstance(maximum, (int, float)) and maximum:
                return float(value) / float(maximum)
            return float(value)
    grade = row.get("grade")
    return _score(grade) if isinstance(grade, dict) else None


def analyze_crossovers(
    cells: list[dict[str, Any]],
    team_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Find the first tested value on each axis that meets the best team score."""
    team_scores = [value for row in team_rows if (value := _score(row)) is not None]
    target = max(team_scores) if team_scores else None
    analysis: dict[str, Any] = {}
    for axis in dict.fromkeys(cell["axis"] for cell in cells):
        axis_cells = [cell for cell in cells if cell["axis"] == axis]
        crossover = next(
            (
                cell["value"]
                for cell in axis_cells
                if target is not None
                and _score(cell) is not None
                and _score(cell) >= target
            ),
            None,
        )
        analysis[axis] = {
            "team_target": target,
            "crossover_value": crossover,
            "tested_values": [cell["value"] for cell in axis_cells],
        }
    return {"team_target": target, "axes": analysis}


def _context_limited(query: Callable[[str, str], str], limit: int):
    def call(system: str, user: str) -> str:
        available = max(0, limit - len(system))
        return query(system, user[-available:] if available else "")

    return call


def run_cell(
    competition: str,
    problem_id: str,
    cell: dict[str, Any],
    query_factory: Callable[[str], Callable[[str, str], str]],
) -> dict[str, Any]:
    config = cell["solo_config"]
    env = OlympiadEnvironment(competition, problem_id)
    query = query_factory(str(config["model_label"]))
    query = _context_limited(query, int(config["visible_context_window"]))
    result = run_collaboration(
        "single_agent",
        env,
        query,
        CollabConfig(
            max_turns=int(config["turns"]),
            max_output_tokens_per_call=int(config["output_tokens"]),
            solo_calls_per_turn=int(config["calls_per_turn"]),
        ),
    )
    grade = result.get("grade") or {}
    return {
        **cell,
        "schema": "single_agent",
        "submitted": result["submitted"],
        "api_calls": result["api_calls"],
        "tokens_used": result["tokens_used"],
        "grade": grade,
        "grade_score": grade.get("score"),
        "grade_max_score": grade.get("max_score"),
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--competition", default="arml_local")
    parser.add_argument("--problem", default="arml_local_2009")
    parser.add_argument("--team-results", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, default=Path("results/handicap_sweep.json"))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default="openai/gpt-5.4-mini")
    args = parser.parse_args()
    if args.live and not os.environ.get("PERPLEXITY_API_KEY"):
        raise SystemExit("--live requires PERPLEXITY_API_KEY")

    team_rows: list[dict[str, Any]] = []
    for path in args.team_results:
        team_rows.extend(_rows(json.loads(path.read_text(encoding="utf-8"))))

    if args.live:
        query_factory = lambda label: make_perplexity_caller(
            model=args.model if label.startswith("mock-") else label
        )
    else:
        mock = resolve_query_fn(use_mock=True)
        query_factory = lambda _label: mock

    cells = [
        run_cell(args.competition, args.problem, cell, query_factory)
        for cell in build_handicap_cells()
    ]
    payload = {
        "schema_version": "handicap_sweep.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live" if args.live else "mock",
        "competition": args.competition,
        "problem_id": args.problem,
        "cells": cells,
        "team_artifacts": [str(path) for path in args.team_results],
        "crossover_analysis": analyze_crossovers(cells, team_rows),
    }
    write_json_atomic(args.output, payload)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
