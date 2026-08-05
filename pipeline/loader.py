from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

from .models import BenchmarkProblem, CompetitionPacket, RuleCard

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPO_ROOT / "data" / "benchmarks"
RULES_ROOT = Path(__file__).resolve().parent / "rules"


def load_rules(competition_id: str) -> RuleCard:
    path = RULES_ROOT / f"{competition_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"No rule card for '{competition_id}': {path}")
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    return RuleCard.from_dict(raw, competition_id=competition_id)


def _load_raw_problems(competition_id: str) -> list[dict[str, Any]]:
    path = BENCHMARK_ROOT / competition_id / "benchmark.json"
    if not path.exists():
        raise FileNotFoundError(f"No benchmark for '{competition_id}': {path}")
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    raw_problems = payload.get("problems") if isinstance(payload, dict) else payload
    if not isinstance(raw_problems, list):
        raise ValueError(f"Benchmark must contain a list or problems list: {path}")
    return raw_problems


def _parse_problems(
    competition_id: str,
    raw_problems: list[dict[str, Any]],
    *,
    skip_invalid: bool = False,
) -> list[BenchmarkProblem]:
    problems: list[BenchmarkProblem] = []
    for item in raw_problems:
        try:
            problems.append(
                BenchmarkProblem.from_dict(
                    item,
                    competition_id=competition_id,
                    repository_root=REPO_ROOT,
                )
            )
        except ValueError as exc:
            if not skip_invalid:
                raise
            warnings.warn(
                f"Skipping non-runnable benchmark row "
                f"{item.get('problem_id', '(missing id)')}: {exc}",
                stacklevel=2,
            )
    ids = [problem.problem_id for problem in problems]
    if len(ids) != len(set(ids)):
        raise ValueError(
            f"Benchmark contains duplicate problem_id values for {competition_id}"
        )
    return problems


def load_problems(competition_id: str) -> list[BenchmarkProblem]:
    return _parse_problems(competition_id, _load_raw_problems(competition_id))


def select_problems(
    competition_id: str,
    selector: str,
    *,
    limit: int | None = None,
) -> list[BenchmarkProblem]:
    raw_problems = _load_raw_problems(competition_id)
    if selector != "all":
        raw_problems = [
            problem
            for problem in raw_problems
            if str(problem.get("problem_id")) == selector
        ]
        if not raw_problems:
            raise ValueError(f"Problem '{selector}' not found in {competition_id}")
    problems = _parse_problems(
        competition_id,
        raw_problems,
        skip_invalid=selector == "all",
    )
    return problems[:limit] if limit is not None else problems


def load_packet(competition_id: str, problem_id: str) -> CompetitionPacket:
    problems = select_problems(competition_id, problem_id)
    return CompetitionPacket(competition_id, problems[0], load_rules(competition_id))


def query_rules(rules: RuleCard, query: str = "") -> str:
    summary = {
        "competition": rules.display_name,
        "team_size": {
            "default": rules.team_size_default,
            "min": rules.team_size_min,
            "max": rules.team_size_max,
        },
        "allowed_tools": list(rules.allowed_tools),
        "exclusive_tools": rules.exclusive_tools,
        "rules": rules.rules_text,
    }
    prefix = f"Rule query: {query}\n" if query else ""
    return prefix + json.dumps(summary, ensure_ascii=False, indent=2)
