"""Deterministic ICPC and LiveOIBench-style leaderboard utilities.

All scoring functions are pure.  The CLI is only a thin JSON/CSV I/O layer.
LiveOIBench candidate selection is deliberately labelled ``oracle_best_of_n``:
the winner is selected with hidden official scores, not by the model.

Codeforces-equivalent ratings use seed inversion over the closed interval
``[lower_bound, max(human_ratings) + upper_margin]``.  Empty ratings return
``None``; ranks outside ``[1, N + 1]`` are rejected.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

WRONG_VERDICTS = {"WA", "TLE", "MLE", "OLE", "RE", "CE"}
MEDALS = ("Gold", "Silver", "Bronze")


def _number(value: Any, *, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def compute_icpc_standings(
    submissions: Iterable[Mapping[str, Any]],
    *,
    wrong_penalty: int = 20,
) -> list[dict[str, Any]]:
    """Return ICPC standings from chronological submission records.

    Required fields are ``team`` (or ``model``), ``problem``
    (or ``problem_id``), ``minute`` and ``verdict``.  Wrong attempts count only
    before the first AC.  Ranking is solved descending, penalty ascending, then
    last accepted minute ascending.  Exact ties share a competition rank;
    ``team`` is the deterministic display-order tie breaker.
    """

    if wrong_penalty < 0:
        raise ValueError("wrong_penalty must be non-negative")
    ordered = sorted(
        enumerate(submissions),
        key=lambda item: (_number(item[1].get("minute")), item[0]),
    )
    states: dict[str, dict[str, Any]] = {}
    for sequence, row in ordered:
        team = str(row.get("team") or row.get("model") or "").strip()
        problem = str(row.get("problem") or row.get("problem_id") or "").strip()
        verdict = str(row.get("verdict") or row.get("status") or "").upper()
        minute = _number(row.get("minute"))
        if not team or not problem or minute < 0:
            raise ValueError("Each submission needs team, problem, and non-negative minute")
        team_state = states.setdefault(team, {"problems": {}})
        problem_state = team_state["problems"].setdefault(
            problem, {"attempts": 0, "wrong_before_ac": 0, "accepted_minute": None}
        )
        if problem_state["accepted_minute"] is not None:
            continue
        problem_state["attempts"] += 1
        if verdict in {"AC", "OK", "ACCEPTED"}:
            problem_state["accepted_minute"] = minute
        elif verdict in WRONG_VERDICTS:
            problem_state["wrong_before_ac"] += 1

    standings: list[dict[str, Any]] = []
    for team, state in states.items():
        solved_problems = [
            problem for problem in state["problems"].values()
            if problem["accepted_minute"] is not None
        ]
        penalty = sum(
            problem["accepted_minute"] + wrong_penalty * problem["wrong_before_ac"]
            for problem in solved_problems
        )
        accepted_minutes = [problem["accepted_minute"] for problem in solved_problems]
        standings.append(
            {
                "team": team,
                "solved": len(solved_problems),
                "penalty": penalty,
                "last_accept": max(accepted_minutes) if accepted_minutes else None,
                "attempts": sum(
                    problem["attempts"] for problem in state["problems"].values()
                ),
                "problems": {
                    key: dict(value) for key, value in sorted(state["problems"].items())
                },
            }
        )

    def order_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        last = row["last_accept"] if row["last_accept"] is not None else math.inf
        return (-row["solved"], row["penalty"], last, row["team"])

    standings.sort(key=order_key)
    prior_key: tuple[Any, ...] | None = None
    prior_rank = 0
    for position, row in enumerate(standings, start=1):
        tie_key = (row["solved"], row["penalty"], row["last_accept"])
        if tie_key != prior_key:
            prior_rank = position
            prior_key = tie_key
        row["rank"] = prior_rank
    return standings


def solution_ranking_key(item: tuple[str, Mapping[str, Any]]) -> tuple[Any, ...]:
    """Sort key for official score, relative score, tests, runtime, filename."""

    name, row = item
    runtime = _number(
        row.get("runtime", row.get("time", row.get("execution_time"))),
        default=math.inf,
    )
    return (
        -_number(row.get("official_score", row.get("score"))),
        -_number(row.get("relative_score")),
        -_number(row.get("tests_passed", row.get("tests_passed_pct"))),
        runtime,
        name,
    )


def select_best_solution(
    candidates: Mapping[str, Mapping[str, Any]] | Sequence[Mapping[str, Any]],
    *,
    expected_n: int | None = 8,
) -> dict[str, Any] | None:
    """Select and label the oracle best candidate for one problem."""

    if isinstance(candidates, Mapping):
        named = [(str(name), value) for name, value in candidates.items()]
    else:
        named = [
            (
                str(row.get("filename") or row.get("solution") or f"candidate_{index}"),
                row,
            )
            for index, row in enumerate(candidates)
        ]
    valid = [(name, row) for name, row in named if isinstance(row, Mapping)]
    if not valid:
        return None
    name, winner = min(valid, key=solution_ranking_key)
    label_n = expected_n if expected_n is not None else len(valid)
    return {
        **dict(winner),
        "best_solution": name,
        "candidate_count": len(valid),
        "expected_candidate_count": expected_n,
        "selection_protocol": f"oracle_best_of_{label_n}",
        "oracle_selected": True,
    }


def select_best_solutions(
    submissions: Mapping[str, Any], *, expected_n: int | None = 8
) -> dict[str, dict[str, Any]]:
    """Stage 1: select one oracle-best solution for each problem."""

    output: dict[str, dict[str, Any]] = {}
    for problem_id in sorted(submissions):
        selected = select_best_solution(submissions[problem_id], expected_n=expected_n)
        if selected is not None:
            selected["problem_id"] = problem_id
            output[problem_id] = selected
    return output


def aggregate_contest_scores(
    problem_results: Mapping[str, Mapping[str, Any]],
    problem_metadata: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Stage 2: sum official task/subtask scores within each contest.

    Every problem must identify a contest and a positive maximum score, either
    in metadata or the result.  A contest may have one ``score_scale`` only.
    """

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scales: dict[str, set[str]] = defaultdict(set)
    competitions: dict[str, str] = {}
    for problem_id, result in problem_results.items():
        metadata = problem_metadata.get(problem_id)
        if metadata is None:
            raise ValueError(f"Missing metadata for problem {problem_id}")
        contest = str(metadata.get("contest_id") or result.get("contest_id") or "").strip()
        if not contest:
            raise ValueError(f"Missing contest_id for problem {problem_id}")
        raw_score = result.get("official_score", result.get("score"))
        subtasks = dict(result.get("subtasks") or {})
        if raw_score is None and subtasks:
            raw_score = sum(
                _number(value.get("score") if isinstance(value, Mapping) else value)
                for value in subtasks.values()
            )
        score = _number(raw_score)
        maximum = _number(
            metadata.get("max_score", result.get("max_score")),
            default=-1,
        )
        if maximum <= 0 and subtasks:
            maxima = [
                _number(
                    value.get("max_score", value.get("points")),
                    default=-1,
                )
                for value in subtasks.values()
                if isinstance(value, Mapping)
            ]
            if maxima and all(value >= 0 for value in maxima):
                maximum = sum(maxima)
        if maximum <= 0 or not 0 <= score <= maximum:
            raise ValueError(f"Invalid score range for problem {problem_id}")
        scale = str(metadata.get("score_scale") or contest)
        scales[contest].add(scale)
        competition = str(metadata.get("competition") or contest.split("-", 1)[0])
        competitions[contest] = competition
        buckets[contest].append(
            {
                "problem_id": problem_id,
                "score": score,
                "max_score": maximum,
                "relative_score": 100.0 * score / maximum,
                "subtasks": subtasks,
            }
        )

    output: dict[str, dict[str, Any]] = {}
    for contest in sorted(buckets):
        if len(scales[contest]) != 1:
            raise ValueError(f"Contest {contest} mixes raw score scales")
        tasks = sorted(buckets[contest], key=lambda row: row["problem_id"])
        total = sum(row["score"] for row in tasks)
        maximum = sum(row["max_score"] for row in tasks)
        output[contest] = {
            "contest_id": contest,
            "competition": competitions[contest],
            "score_scale": next(iter(scales[contest])),
            "total_score": total,
            "max_score": maximum,
            "relative_score": 100.0 * total / maximum,
            "task_count": len(tasks),
            "tasks": tasks,
        }
    return output


def human_percentile(model_score: float, human_scores: Sequence[float]) -> float | None:
    """Strict percentile: ``100 * count(model > human) / N``."""

    scores = [_number(value, default=math.nan) for value in human_scores]
    scores = [value for value in scores if math.isfinite(value)]
    if not scores:
        return None
    return 100.0 * sum(float(model_score) > value for value in scores) / len(scores)


def medal_from_cutoffs(
    score: float,
    cutoffs: Mapping[str, float | None] | None,
) -> str | None:
    """Return Gold/Silver/Bronze/None, or ``None`` when no cutoff exists."""

    if not cutoffs:
        return None
    present = False
    for medal in MEDALS:
        raw = cutoffs.get(
            medal,
            cutoffs.get(medal.lower(), cutoffs.get(f"{medal.lower()}_cutoff")),
        )
        if raw is None:
            continue
        present = True
        if score >= float(raw):
            return medal
    return "None" if present else None


def codeforces_equivalent_rating(
    model_rank: int,
    human_ratings: Sequence[float],
    *,
    lower_bound: float = 500.0,
    upper_margin: float = 100.0,
    tolerance: float = 1.0,
) -> float | None:
    """Invert the Codeforces seed model for a rank.

    Bounds are ``lower_bound`` and ``max(human_ratings) + upper_margin``.
    Empty/non-finite input returns ``None``.  The highest admissible rank is
    ``N + 1`` because the seed includes the model itself.
    """

    ratings = [
        _number(value, default=math.nan) for value in human_ratings
        if math.isfinite(_number(value, default=math.nan))
    ]
    if not ratings:
        return None
    if not 1 <= model_rank <= len(ratings) + 1:
        raise ValueError("model_rank must be between 1 and N + 1")
    if tolerance <= 0 or upper_margin < 0:
        raise ValueError("Invalid rating inversion bounds")
    left = float(lower_bound)
    right = max(left, max(ratings) + float(upper_margin))
    while right - left > tolerance:
        middle = (left + right) / 2
        seed = 1.0 + sum(
            1.0 / (1.0 + 10 ** ((middle - rating) / 400.0))
            for rating in ratings
        )
        if seed < model_rank:
            right = middle
        else:
            left = middle
    return round(left, 2)


def compare_with_humans(
    contest_result: Mapping[str, Any],
    baseline: Mapping[str, Any] | None,
    *,
    include_rating: bool = False,
) -> dict[str, Any]:
    """Attach human percentile, medal and optional rating to one contest."""

    output = dict(contest_result)
    if baseline is None:
        output.update(
            {
                "human_data_status": "missing",
                "human_percentile": None,
                "medal": None,
                "codeforces_rating": None,
            }
        )
        return output
    human_scores = baseline.get("scores") or baseline.get("human_scores") or []
    total = float(contest_result["total_score"])
    output["human_data_status"] = "available"
    output["human_percentile"] = human_percentile(total, human_scores)
    output["medal"] = medal_from_cutoffs(total, baseline.get("medal_cutoffs"))
    output["codeforces_rating"] = None
    ratings = baseline.get("ratings") or baseline.get("codeforces_ratings") or []
    if include_rating and ratings:
        rank = 1 + sum(_number(score) > total for score in human_scores)
        output["codeforces_rating"] = codeforces_equivalent_rating(rank, ratings)
    return output


def build_global_table(
    model_contests: Mapping[str, Mapping[str, Mapping[str, Any]]],
    *,
    aggregation_level: str = "competition",
) -> list[dict[str, Any]]:
    """Stage 3: aggregate normalized metrics without summing raw score scales."""

    if aggregation_level not in {"contest", "competition"}:
        raise ValueError("aggregation_level must be contest or competition")
    rows: list[dict[str, Any]] = []
    for model, contests in sorted(model_contests.items()):
        grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for contest_id, result in contests.items():
            key = (
                contest_id
                if aggregation_level == "contest"
                else str(result.get("competition") or contest_id.split("-", 1)[0])
            )
            grouped[key].append(result)

        metrics: dict[str, list[float]] = defaultdict(list)
        for group in grouped.values():
            for key in ("relative_score", "human_percentile", "codeforces_rating"):
                values = [
                    float(item[key]) for item in group
                    if item.get(key) is not None and math.isfinite(float(item[key]))
                ]
                if values:
                    metrics[key].append(sum(values) / len(values))
        medals = Counter(
            str(item.get("medal")) for item in contests.values()
            if item.get("medal") in MEDALS
        )
        row = {
            "model": model,
            "aggregation_level": aggregation_level,
            "raw_score_status": "not_aggregated_across_contests",
            "global_relative_score": (
                sum(metrics["relative_score"]) / len(metrics["relative_score"])
                if metrics["relative_score"] else None
            ),
            "average_human_percentile": (
                sum(metrics["human_percentile"]) / len(metrics["human_percentile"])
                if metrics["human_percentile"] else None
            ),
            "average_codeforces_rating": (
                sum(metrics["codeforces_rating"]) / len(metrics["codeforces_rating"])
                if metrics["codeforces_rating"] else None
            ),
            "gold_medals": medals["Gold"],
            "silver_medals": medals["Silver"],
            "bronze_medals": medals["Bronze"],
            "contest_count": len(contests),
            "group_count": len(grouped),
        }
        rows.append(row)
    rows.sort(
        key=lambda row: (
            -(row["global_relative_score"] or 0.0),
            -(row["average_human_percentile"] or 0.0),
            row["model"],
        )
    )
    prior: tuple[Any, ...] | None = None
    rank = 0
    for position, row in enumerate(rows, 1):
        key = (row["global_relative_score"], row["average_human_percentile"])
        if key != prior:
            rank = position
            prior = key
        row["global_rank"] = rank
    return rows


def load_human_baselines(
    directory: str | Path = Path("data") / "human_baselines",
) -> dict[str, Any]:
    """Load local JSON/CSV baselines and return an explicit availability status."""

    root = Path(directory)
    if not root.is_dir():
        return {
            "status": "missing",
            "reason": f"Human baseline directory not found: {root}",
            "contests": {},
        }
    contests: dict[str, dict[str, Any]] = {}
    files = sorted([*root.glob("*.json"), *root.glob("*.csv")])
    for path in files:
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, Mapping) and isinstance(payload.get("contests"), Mapping):
                for key, value in payload["contests"].items():
                    contests[str(key)] = dict(value)
            elif isinstance(payload, Mapping):
                contest_id = str(payload.get("contest_id") or path.stem)
                contests[contest_id] = dict(payload)
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                contest_id = str(row.get("contest_id") or path.stem)
                entry = contests.setdefault(contest_id, {"scores": [], "ratings": []})
                score = row.get("score") or row.get("total")
                rating = row.get("rating") or row.get("cf_rating")
                if score not in (None, ""):
                    entry["scores"].append(float(score))
                if rating not in (None, ""):
                    entry["ratings"].append(float(rating))
                cutoffs = entry.setdefault("medal_cutoffs", {})
                for medal in MEDALS:
                    raw = row.get(f"{medal.lower()}_cutoff")
                    if raw not in (None, ""):
                        cutoffs[medal] = float(raw)
    if not contests:
        return {
            "status": "missing",
            "reason": f"No JSON or CSV human baselines found under {root}",
            "contests": {},
        }
    return {"status": "available", "reason": None, "contests": contests}


def write_json_atomic(path: str | Path, payload: Any) -> None:
    _atomic_write(Path(path), lambda handle: json.dump(payload, handle, indent=2))


def write_csv_atomic(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> None:
    destination = Path(path)
    fieldnames = sorted({key for row in rows for key in row})

    def write(handle: Any) -> None:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    _atomic_write(destination, write, newline="")


def _atomic_write(path: Path, writer: Any, **kwargs: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False,
            prefix=f".{path.name}.", suffix=".tmp", **kwargs
        ) as handle:
            writer(handle)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    icpc = subparsers.add_parser("icpc", help="Build ICPC standings from submissions JSON")
    icpc.add_argument("input", type=Path)
    icpc.add_argument("output", type=Path)

    problem = subparsers.add_parser("liveoi-problem", help="Run LiveOIBench stage 1")
    problem.add_argument("input", type=Path)
    problem.add_argument("output", type=Path)
    problem.add_argument("--best-of", type=int, default=8)

    contest = subparsers.add_parser("liveoi-contest", help="Run LiveOIBench stage 2")
    contest.add_argument("problem_results", type=Path)
    contest.add_argument("problem_metadata", type=Path)
    contest.add_argument("output", type=Path)

    final = subparsers.add_parser("liveoi-final", help="Run LiveOIBench stage 3")
    final.add_argument("input", type=Path)
    final.add_argument("output", type=Path)
    final.add_argument("--aggregation-level", choices=("contest", "competition"), default="competition")

    baselines = subparsers.add_parser("human-status", help="Report local human baseline status")
    baselines.add_argument("--directory", type=Path, default=Path("data") / "human_baselines")
    baselines.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    if args.command == "icpc":
        write_json_atomic(args.output, compute_icpc_standings(_read_json(args.input)))
    elif args.command == "liveoi-problem":
        write_json_atomic(
            args.output, select_best_solutions(_read_json(args.input), expected_n=args.best_of)
        )
    elif args.command == "liveoi-contest":
        write_json_atomic(
            args.output,
            aggregate_contest_scores(
                _read_json(args.problem_results), _read_json(args.problem_metadata)
            ),
        )
    elif args.command == "liveoi-final":
        rows = build_global_table(
            _read_json(args.input), aggregation_level=args.aggregation_level
        )
        if args.output.suffix.lower() == ".csv":
            write_csv_atomic(args.output, rows)
        else:
            write_json_atomic(args.output, rows)
    else:
        status = load_human_baselines(args.directory)
        if args.output:
            write_json_atomic(args.output, status)
        else:
            print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
