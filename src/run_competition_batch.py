"""Competition-level batch: full turn budgets, task score + MultiAgentBench CS.

Defaults follow the 2026-08-21 meeting:
  - schema: centralized (best of ARML pilot)
  - turns: contest registry (usually 50)
  - beyond ARML: one representative year per family
  - signals: task grade + coordination/collaboration score

Usage:
  cp .env.example .env   # then fill in API keys
  python3 src/run_competition_batch.py --live
  python3 src/run_competition_batch.py --live --provider tinker --judge-collab
  python3 src/run_competition_batch.py --live --max-turns 10 --limit 3
  python3 src/run_competition_batch.py --live --competitions arml_local,wsc_writing,mcm
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
import traceback
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import CollabConfig, SCHEMAS, run_collaboration
from contest_adapters import EnvironmentTaskExecutor, grade_contest_result
from contest_budget import resolve_contest_budget
from contest_run_identity import build_run_identity, inspect_contest_output, RunCompatibilityError
from contest_manifest import load_contest_manifest
from contest_runner import (
    BASELINE_ALIASES,
    BASELINE_NAMES,
    BASELINES,
    PROTOCOL_VERSION,
    ContestRunConfig,
    canonical_baseline,
)
from rulecard_policy import open_table_policy
from rules.loader import load_rule_card
from rules.views import agent_view, assert_agent_view_hides_eval
from tool_registry import ACTION_SET_VERSION
from contest_rules import get_contest_rules
from env import OlympiadEnvironment, ProblemNotFoundError
from evaluation.collaboration_score import (
    score_coordination,
    score_interaction_helpfulness,
)
from evaluation.cce import score_cce
from evaluation.finalize import apply_registered_judge
from env_config import load_repo_dotenv
from llm import (
    make_perplexity_caller,
    make_tinker_caller,
    provider_action_transport,
    resolve_query_fn,
    resolve_request_fn,
)
from strategic_contest_runner import run_strategic_contest
from vanilla_contest_runner import run_vanilla_contest
from rules import RulesMode
from run_smoke_batch import SMOKE_CASES

DEFAULT_MODEL = "openai/gpt-5.4-mini"
TINKER_DEFAULT_MODEL = "Qwen/Qwen3.6-35B-A3B"
TINKER_DEFAULT_MAX_TOKENS = 8192
TINKER_DEFAULT_TEMPERATURE = 0.2
PROVIDERS = ("perplexity", "tinker")
JUDGE_PROVIDERS = ("perplexity", "tinker", "openai")

TRACKED_TOOLS = (
    "execute_code",
    "submit_code",
    "use_calculator",
    "web_search",
    "read_lab_equipment",
    "read_star_chart",
    "query_rules",
)

MATH_CONTESTS = frozenset(
    {
        "arml_local",
        "arml_national_team",
        "arml_national_power",
        "arml_power",
        "purple_comet",
        "hmmt_guts",
        "hmmt_team",
        "hmmt_nov",
        "putnam",
        "imo_shortlist",
        "aime",
        "amc",
        "science_bowl",
        "qanta",
        "mystery_hunt",
        "nyu_ctf_bench",
        "history_olympiad",
        "cfa_research_challenge",
        "wmtc",
    }
)
DEFAULT_RULES_ROOT = REPO_ROOT / "data" / "rules"
DEFAULT_BENCHMARK_ROOT = REPO_ROOT / "data" / "benchmarks"


class ContestRulesUnavailable(ValueError):
    """A non-strict rule request cannot run because its card is missing."""

    def __init__(self, competition: str, mode: str, root: Path):
        self.metadata = {
            "status": "rules_baseline_unavailable", "competition_id": competition,
            "rules_mode": mode, "rules_root": str(root), "rules_available": False,
        }
        super().__init__(f"rules_baseline_unavailable: no rule card for {competition!r} under {root}")


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _sanitize_exception(exc: Exception) -> str:
    message = str(exc)
    for name in ("TINKER_API_KEY", "PERPLEXITY_API_KEY", "OPENAI_API_KEY"):
        secret = os.environ.get(name)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    message = re.sub(
        r"(?i)(authorization[\"']?\s*[:=]\s*[\"']?bearer\s+)\S+",
        r"\1[REDACTED]",
        message,
    )
    return f"{type(exc).__name__}: {message}"


def _select_cases(
    competitions: str | None,
    problem_id: str | None,
    limit: int | None,
    *,
    structured_gold: bool = False,
    benchmark_suite: str | None = None,
    benchmark_root: Path | None = None,
    rules_root: Path | None = None,
    require_rule_card: bool = True,
) -> list[tuple[str, str]]:
    selected = (
        [item.strip() for item in competitions.split(",") if item.strip()]
        if competitions
        else []
    )
    if structured_gold and problem_id:
        raise ValueError("--structured-gold cannot be combined with --problem-id.")
    if benchmark_suite and (structured_gold or problem_id):
        raise ValueError("--benchmark-suite cannot be combined with --structured-gold or --problem-id.")
    if benchmark_suite:
        cases = _discover_benchmark_suite_cases(
            benchmark_suite,
            benchmark_root or DEFAULT_BENCHMARK_ROOT,
            rules_root or DEFAULT_RULES_ROOT,
            selected or None,
            require_rule_card=require_rule_card,
        )
    elif structured_gold:
        cases = _discover_structured_gold_cases(
            benchmark_root or DEFAULT_BENCHMARK_ROOT,
            selected or None,
        )
    elif problem_id:
        if len(selected) != 1:
            raise ValueError("--problem-id requires exactly one --competitions value.")
        cases = [(selected[0], problem_id)]
    else:
        wanted = set(selected)
        cases = [(c, p) for c, p in SMOKE_CASES if not wanted or c in wanted]
    return cases[:limit] if limit is not None else cases


def _has_structured_gold(problem: dict) -> bool:
    gold = problem.get("gold_label")
    if not isinstance(gold, dict):
        return False
    parts = gold.get("parts")
    if not isinstance(parts, list):
        return False
    for part in parts:
        if not isinstance(part, dict):
            continue
        expected = part.get("expected")
        if (
            isinstance(expected, str)
            and expected.strip()
            and part.get("match_mode") != "reference_llm"
            and float(part.get("points") or 0) > 0
        ):
            return True
    return False


def _has_rule_card(competition: str, rules_root: Path) -> bool:
    return (rules_root / competition / "competition.json").exists()


def _discover_benchmark_suite_cases(
    suite: str,
    benchmark_root: Path,
    rules_root: Path,
    competitions: list[str] | None,
    *,
    require_rule_card: bool,
) -> list[tuple[str, str]]:
    if suite == "non_math":
        wanted = {
            path.parent.name
            for path in sorted(benchmark_root.glob("*/benchmark.json"))
            if path.parent.name not in MATH_CONTESTS
        }
    elif suite == "math":
        wanted = set(MATH_CONTESTS) & {
            path.parent.name for path in benchmark_root.glob("*/benchmark.json")
        }
    elif suite == "all":
        wanted = {path.parent.name for path in benchmark_root.glob("*/benchmark.json")}
    else:
        raise ValueError(f"Unknown benchmark suite {suite!r}")
    if competitions:
        wanted &= set(competitions)
    cases: list[tuple[str, str]] = []
    skipped_no_card: list[str] = []
    for competition in sorted(wanted):
        if require_rule_card and not _has_rule_card(competition, rules_root):
            skipped_no_card.append(competition)
            continue
        benchmark_path = benchmark_root / competition / "benchmark.json"
        if not benchmark_path.exists():
            continue
        problems = json.loads(benchmark_path.read_text(encoding="utf-8"))
        if not isinstance(problems, list):
            continue
        for problem in problems:
            if not isinstance(problem, dict):
                continue
            problem_id = problem.get("problem_id")
            if isinstance(problem_id, str) and problem_id:
                cases.append((competition, problem_id))
    if skipped_no_card:
        print(
            "Skipping contests without rule cards: " + ", ".join(skipped_no_card),
            flush=True,
        )
    if not cases:
        raise ValueError(f"No benchmark cases discovered for suite={suite!r}")
    return cases


def _discover_structured_gold_cases(
    benchmark_root: Path,
    competitions: list[str] | None = None,
) -> list[tuple[str, str]]:
    wanted = set(competitions or ())
    cases: list[tuple[str, str]] = []
    for benchmark_path in sorted(benchmark_root.glob("*/benchmark.json")):
        competition = benchmark_path.parent.name
        if wanted and competition not in wanted:
            continue
        problems = json.loads(benchmark_path.read_text(encoding="utf-8"))
        if not isinstance(problems, list):
            continue
        for problem in problems:
            if not isinstance(problem, dict) or not _has_structured_gold(problem):
                continue
            problem_id = problem.get("problem_id")
            if isinstance(problem_id, str) and problem_id:
                cases.append((competition, problem_id))
    return cases


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize_action_log(action_log: list[dict] | None) -> dict[str, int | str]:
    counts: dict[str, int] = {}
    tool_errors = 0
    for entry in action_log or []:
        action = entry.get("action")
        if not isinstance(action, str) or not action:
            continue
        counts[action] = counts.get(action, 0) + 1
        if action in TRACKED_TOOLS:
            result = str(entry.get("result") or "")
            if "error" in result.lower():
                tool_errors += 1
    used_bits = [
        f"{tool}×{counts[tool]}"
        for tool in TRACKED_TOOLS
        if counts.get(tool)
    ]
    return {
        **{f"tool_{tool}": counts.get(tool, 0) for tool in TRACKED_TOOLS},
        "tool_errors": tool_errors,
        "tool_usage_summary": "; ".join(used_bits) if used_bits else "",
        "speak_count": counts.get("speak", 0),
        # Canonical ``work`` since action set v5; older logs say ``write_scratchpad``.
        "scratchpad_count": counts.get("work", 0) + counts.get("write_scratchpad", 0),
    }


def enrich_row_tool_usage(row: dict, *, repo_root: Path = REPO_ROOT) -> dict:
    if any(key.startswith("tool_") and key not in {"tool_errors", "tool_usage_summary"} for key in row):
        return row
    action_log = row.get("action_log") or row.get("action_log_tail")
    if not action_log:
        transcript_path = row.get("transcript_path")
        if transcript_path:
            path = Path(transcript_path)
            if not path.is_absolute():
                path = repo_root / path
            if path.exists():
                try:
                    transcript = json.loads(path.read_text(encoding="utf-8"))
                    action_log = transcript.get("action_log") or []
                except (OSError, json.JSONDecodeError):
                    action_log = []
    row = dict(row)
    row.update(summarize_action_log(action_log if isinstance(action_log, list) else None))
    return row


def _board_row_fields(board: dict | None) -> dict:
    """Flatten workboard metrics onto the row so they reach the TSV sheets.

    ``board_repeat_rate`` is the stubbornness number: the share of answer
    attempts that re-recorded an answer the team already had for that item.
    """
    if not board:
        return {
            "board_items": None,
            "board_items_answered": None,
            "board_items_reviewed": None,
            "board_attempts": None,
            "board_repeat_attempts": None,
            "board_repeat_rate": None,
        }
    return {
        "board_items": board.get("items_total"),
        "board_items_answered": board.get("items_answered"),
        "board_items_reviewed": board.get("items_reviewed"),
        "board_attempts": board.get("attempts_recorded"),
        "board_repeat_attempts": board.get("repeat_attempts_rejected"),
        "board_repeat_rate": board.get("repeat_rate"),
    }


def _aggregate_metrics(rows: list[dict]) -> dict:
    graded = [
        row
        for row in rows
        if row.get("status") == "ok"
        and isinstance(row.get("grade_score"), (int, float))
        and isinstance(row.get("grade_max_score"), (int, float))
        and row["grade_max_score"] > 0
    ]
    total_score = sum(float(row["grade_score"]) for row in graded)
    total_max_score = sum(float(row["grade_max_score"]) for row in graded)
    accuracies = [
        max(0.0, min(1.0, float(row["grade_score"]) / float(row["grade_max_score"])))
        for row in graded
    ]
    full_credit = sum(
        1
        for row in graded
        if float(row["grade_score"]) >= float(row["grade_max_score"])
    )

    def scores(field: str) -> list[float]:
        return [
            float(row[field])
            for row in rows
            if isinstance(row.get(field), (int, float))
        ]

    return {
        "graded_tasks": len(graded),
        "total_task_score": total_score,
        "total_task_max_score": total_max_score,
        "answer_accuracy_micro": (
            total_score / total_max_score if total_max_score else None
        ),
        "answer_accuracy_macro": _mean(accuracies),
        "full_credit_tasks": full_credit,
        "full_credit_task_rate": full_credit / len(graded) if graded else None,
        "mean_communication_score": _mean(scores("communication_score")),
        "mean_planning_score": _mean(scores("planning_score")),
        "mean_coordination_score": _mean(scores("coordination_score")),
        "mean_cce": _mean(scores("cce")),
        "mean_causal_efficiency": _mean(scores("causal_efficiency")),
        "mean_utility_weighted_cce": _mean(scores("utility_weighted_cce")),
        "total_api_calls": sum(
            int(row.get("api_calls") or 0)
            for row in rows
            if row.get("status") == "ok"
        ),
        "total_tokens_used": sum(
            int(row.get("tokens_used") or 0)
            for row in rows
            if row.get("status") == "ok"
        ),
        "total_elapsed_seconds": sum(
            float(row.get("elapsed_seconds") or 0) for row in rows
        ),
        "board_runs": sum(1 for row in rows if row.get("board_items")),
        "mean_board_repeat_rate": _mean(scores("board_repeat_rate")),
        "total_board_repeat_attempts": sum(
            int(row.get("board_repeat_attempts") or 0) for row in rows
        ),
        "mean_board_answered_fraction": _mean(
            [
                float(row["board_items_answered"]) / float(row["board_items"])
                for row in rows
                if row.get("board_items")
                and isinstance(row.get("board_items_answered"), (int, float))
            ]
        ),
    }


def _build_summary(rows: list[dict], metadata: dict) -> dict:
    aggregate_by_competition = {
        competition: _aggregate_metrics(
            [row for row in rows if row.get("competition") == competition]
        )
        for competition in sorted(
            {
                str(row["competition"])
                for row in rows
                if isinstance(row.get("competition"), str)
            }
        )
    }
    return {
        **metadata,
        "total": len(rows),
        "ok": sum(1 for row in rows if row.get("status") == "ok"),
        "errors": sum(1 for row in rows if row.get("status") == "error"),
        "rules_baseline_unavailable": sum(
            1 for row in rows if row.get("status") == "rules_baseline_unavailable"
        ),
        "submitted": sum(1 for row in rows if row.get("submitted")),
        "graded": sum(1 for row in rows if row.get("graded")),
        "with_coordination": sum(
            1 for row in rows if row.get("coordination_score") is not None
        ),
        "with_cce": sum(1 for row in rows if row.get("cce") is not None),
        "aggregate_metrics": _aggregate_metrics(rows),
        "aggregate_by_competition": aggregate_by_competition,
        "results": rows,
    }


def _write_results_tsv(path: Path, rows: list[dict]) -> None:
    enriched = [enrich_row_tool_usage(row) for row in rows]
    fields = [
        "competition",
        "problem_id",
        "status",
        "grade_score",
        "grade_max_score",
        "answer_accuracy",
        "communication_score",
        "planning_score",
        "coordination_score",
        "cce",
        "causal_efficiency",
        "utility_weighted_cce",
        "tool_usage_summary",
        * [f"tool_{tool}" for tool in TRACKED_TOOLS],
        "tool_errors",
        "speak_count",
        "scratchpad_count",
        "board_items",
        "board_items_answered",
        "board_items_reviewed",
        "board_attempts",
        "board_repeat_attempts",
        "board_repeat_rate",
        "turns_used",
        "max_turns",
        "api_calls",
        "tokens_used",
        "elapsed_seconds",
        "error",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
            writer.writeheader()
            for row in enriched:
                maximum = row.get("grade_max_score")
                score = row.get("grade_score")
                accuracy = (
                    float(score) / float(maximum)
                    if isinstance(score, (int, float))
                    and isinstance(maximum, (int, float))
                    and maximum > 0
                    else None
                )
                writer.writerow(
                    {
                        field: accuracy if field == "answer_accuracy" else row.get(field)
                        for field in fields
                    }
                )
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _write_summary_tsv(path: Path, summary: dict) -> None:
    fields = [
        "scope",
        "graded_tasks",
        "total_task_score",
        "total_task_max_score",
        "answer_accuracy_micro",
        "answer_accuracy_macro",
        "full_credit_tasks",
        "full_credit_task_rate",
        "mean_communication_score",
        "mean_planning_score",
        "mean_coordination_score",
        "mean_cce",
        "mean_causal_efficiency",
        "mean_utility_weighted_cce",
        "board_runs",
        "mean_board_repeat_rate",
        "total_board_repeat_attempts",
        "mean_board_answered_fraction",
        "total_api_calls",
        "total_tokens_used",
        "total_elapsed_seconds",
    ]
    aggregates = [
        ("overall", summary["aggregate_metrics"]),
        *list((summary.get("aggregate_by_competition") or {}).items()),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
            writer.writeheader()
            for scope, metrics in aggregates:
                writer.writerow(
                    {
                        field: scope if field == "scope" else metrics.get(field)
                        for field in fields
                    }
                )
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _load_resume_rows(path: Path, metadata: dict) -> tuple[list[dict], str | None]:
    if not path.exists():
        return [], None
    prior = json.loads(path.read_text(encoding="utf-8"))
    for field in ("mode", "provider", "model", "schema", "rules_mode"):
        if prior.get(field) != metadata[field]:
            raise ValueError(
                f"Cannot resume: {field} changed from "
                f"{prior.get(field)!r} to {metadata[field]!r}."
            )
    return list(prior.get("results") or []), prior.get("timestamp")


def _row_is_complete(
    row: dict,
    *,
    judge_task: bool,
    judge_collab: bool,
    judge_cce: bool = False,
) -> bool:
    return (
        row.get("status") == "ok"
        and (not judge_task or row.get("graded") is True)
        and (not judge_collab or row.get("coordination_score") is not None)
        and (
            not judge_cce
            or row.get("cce") is not None
            or row.get("cce_unavailable") is True
        )
    )


def _resolve_model(provider: str, supplied_model: str | None) -> str:
    if supplied_model:
        return supplied_model
    if provider == "tinker":
        model = os.environ.get("TINKER_MODEL")
        return model or TINKER_DEFAULT_MODEL
    return DEFAULT_MODEL


def _resolve_judge_provider(agent_provider: str, judge_provider: str | None) -> str:
    if judge_provider:
        return judge_provider
    if agent_provider == "tinker":
        return "tinker"
    return "perplexity"


def _judge_api_key_name(provider: str) -> str:
    if provider == "tinker":
        return "TINKER_API_KEY"
    if provider in {"openai", "oai"}:
        return "OPENAI_API_KEY"
    return "PERPLEXITY_API_KEY"


def _resolve_judge_model(
    judge_provider: str,
    agent_provider: str,
    agent_model: str,
    supplied_model: str | None,
) -> str:
    if supplied_model:
        return supplied_model
    if judge_provider == agent_provider:
        return agent_model
    if judge_provider == "tinker":
        return _resolve_model("tinker", None)
    if judge_provider in {"openai", "oai"}:
        return "gpt-4.1"
    return DEFAULT_MODEL


def _make_live_query(
    provider: str,
    model: str,
    *,
    max_output_tokens: int = TINKER_DEFAULT_MAX_TOKENS,
    temperature: float = TINKER_DEFAULT_TEMPERATURE,
):
    if provider == "tinker":
        return make_tinker_caller(
            model=model,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
    return make_perplexity_caller(model=model)


def _agent_names(env: OlympiadEnvironment, schema: str) -> list[str]:
    if schema in {"single_agent", "self_consistency", "memory_solo", "liveoi_best_of_8"}:
        return ["Solo"]
    if schema == "subagent":
        return ["Orchestrator", *[f"Worker_{i}" for i in range(1, env.team_size + 1)]]
    if schema == "centralized":
        workers = [f"Agent_{i}" for i in range(2, env.team_size + 1)]
        return ["Group_Leader", *workers]
    agents = [f"Agent_{i}" for i in range(1, env.team_size + 1)]
    return agents


def run_one(
    competition: str,
    problem_id: str,
    *,
    schema: str,
    query_fn,
    request_fn,
    rounds: int | None,
    synthesize: bool,
    judge_task: bool,
    judge_collab: bool,
    out_dir: Path,
    progress=None,
    rules_mode: RulesMode | str = RulesMode.OFF,
    rules_root: Path | None = None,
    rules_strict: bool = False,
    provider: str = "perplexity",
    model: str = "mock",
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    judge_cce: bool = False,
    cce_request_fn=None,
) -> dict:
    started_at = time.perf_counter()
    env = OlympiadEnvironment(
        competition,
        problem_id,
        max_turns=rounds,
        rules_mode=rules_mode,
        rules_root=rules_root,
        rules_strict=rules_strict,
    )
    baseline = env.rules_metadata()
    # Layout: <out>/<competition>/transcripts/<problem>__<schema>__<rules_mode>.json
    transcript_path = (
        out_dir
        / competition
        / "transcripts"
        / f"{problem_id}__{schema}__{env.rules_mode.value}.json"
    )
    if not env.rules_baseline.available:
        row = {
            "competition": competition,
            "problem_id": problem_id,
            "provider": provider,
            "model": model,
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
            "schema": schema,
            "status": "rules_baseline_unavailable",
            "error": (
                f"rules_baseline_unavailable: no canonical card for {competition!r}"
            ),
            "elapsed_seconds": time.perf_counter() - started_at,
            **baseline,
        }
        transcript = env.to_transcript()
        transcript["run"] = dict(row)
        _write_json_atomic(transcript_path, transcript)
        row["transcript_path"] = str(transcript_path)
        return row
    rules = get_contest_rules(competition)
    config = CollabConfig(
        max_turns=rounds,
        rounds=rounds,
        decentralized_events=rounds,
        synthesize=synthesize,
        progress=progress,
    )
    result: dict = {}
    grade: dict = {}
    coordination = None
    interaction = None
    cce = None
    cce_error = None
    cce_unavailable = False
    run_error = None
    try:
        result = run_collaboration(schema, env, query_fn, config)
        grade = result.get("grade") or {}

        if judge_task and result.get("submitted") and request_fn is not None:
            grade = apply_registered_judge(
                env.problem_data,
                result.get("final_answer") or "",
                grade,
                request_fn=request_fn,
                work_dir=out_dir / competition / "judge" / problem_id,
                repo_root=REPO_ROOT,
            )
            result["grade"] = grade

        if judge_collab and request_fn is not None:
            agents = _agent_names(env, schema)
            seen = []
            for msg in env.chat_history:
                name = msg.get("sender")
                if name and name not in seen:
                    seen.append(name)
            if seen:
                agents = seen
            task_results = (
                f"submitted={result.get('submitted')} "
                f"grade_method={grade.get('method')} "
                f"score={grade.get('score')}/{grade.get('max_score')}"
            )
            task_text = str(
                env.problem_data.get("problem_description") or env.problem_id
            )
            coordination = score_coordination(
                request_fn=request_fn,
                task_text=task_text,
                agents=agents,
                schema=schema,
                chat_history=env.chat_history,
                action_log=env.action_log,
                task_results=task_results,
            ).to_dict()
            interaction = score_interaction_helpfulness(
                request_fn=request_fn,
                task_text=task_text,
                agents=agents,
                schema=schema,
                chat_history=env.chat_history,
                action_log=env.action_log,
                final_answer=str(result.get("final_answer") or ""),
                task_results=task_results,
            ).to_dict()
    except Exception as exc:
        run_error = _sanitize_exception(exc)
        if not grade:
            try:
                grade = env.grade_submission()
            except Exception as grade_exc:
                grade = {
                    "graded": False,
                    "method": None,
                    "reason": _sanitize_exception(grade_exc),
                }
        result = {
            "submitted": env.submitted,
            "submitted_by": env.submitted_by,
            "turns_used": env.current_turn,
            "max_turns": env.max_turns,
            "api_calls": env.api_calls,
            "tokens_used": env.tokens_used,
            "tokens_by_turn": env.token_usage_by_turn(),
            "final_answer": env.workspace.get("final_answer", ""),
            "grade": grade,
        }

    # Isolate CCE so a judge failure does not rewrite an otherwise successful run.
    if judge_cce and run_error is None:
        cce_judge = cce_request_fn or request_fn
        has_grade = (
            isinstance(grade.get("score"), (int, float))
            and isinstance(grade.get("max_score"), (int, float))
            and float(grade["max_score"]) > 0
        )
        if cce_judge is None:
            cce_unavailable = True
            cce_error = "cce_judge_unavailable"
        elif not has_grade:
            cce_unavailable = True
            cce_error = "ungraded_or_pending"
        else:
            try:
                task_utility = max(
                    0.0,
                    min(1.0, float(grade["score"]) / float(grade["max_score"])),
                )
                contestant_agents = [
                    name
                    for name in _agent_names(env, schema)
                    if name not in {"Coach", "Contest_Control"}
                ]
                cce = score_cce(
                    request_fn=cce_judge,
                    task_text=str(
                        env.problem_data.get("problem_description") or env.problem_id
                    ),
                    action_log=list(env.action_log),
                    task_utility=task_utility,
                    task_outcome=json.dumps(grade, ensure_ascii=False, default=str),
                    agents=contestant_agents,
                ).to_dict()
            except Exception as exc:
                cce_error = _sanitize_exception(exc)

    transcript = env.to_transcript()
    transcript["run"] = {
        "provider": provider,
        "model": model,
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "schema": schema,
        "rules_mode": env.rules_mode.value,
        "task_type": env.problem_data.get("task_type"),
        "grade": grade,
        "coordination": coordination,
        "interaction": interaction,
        "cce": cce,
        "cce_error": cce_error,
        "cce_unavailable": cce_unavailable,
        "status": "error" if run_error else "ok",
        "error": run_error,
        "final_result": result,
        **baseline,
    }
    _write_json_atomic(transcript_path, transcript)

    return {
        "competition": competition,
        "problem_id": problem_id,
        "provider": provider,
        "model": model,
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "schema": schema,
        **baseline,
        "task_type": env.problem_data.get("task_type"),
        "team_size": env.team_size,
        "search_policy": rules.search_policy if rules else None,
        "rules_gap_count": len(rules.gaps()) if rules else None,
        "submitted": result["submitted"],
        "submitted_by": result.get("submitted_by"),
        "turns_used": result["turns_used"],
        "max_turns": result.get("max_turns"),
        "api_calls": result.get("api_calls"),
        "tokens_used": result.get("tokens_used"),
        "tokens_by_turn": result.get("tokens_by_turn") or [],
        "wrong_submissions": env.wrong_submissions,
        "penalty_minutes": env.penalty_minutes(),
        **_board_row_fields(result.get("workboard")),
        "rule_violations": list(env.rule_violations),
        "grade_method": grade.get("method"),
        "grade_score": grade.get("score"),
        "grade_max_score": grade.get("max_score"),
        "graded": grade.get("graded"),
        "coordination_score": (coordination or {}).get("coordination_score"),
        "communication_score": (coordination or {}).get("communication_score"),
        "planning_score": (coordination or {}).get("planning_score"),
        "coordination": coordination,
        "cce": (cce or {}).get("cce"),
        "causal_efficiency": (cce or {}).get("causal_efficiency"),
        "utility_weighted_cce": (cce or {}).get("utility_weighted_cce"),
        "cce_result": cce,
        "cce_error": cce_error,
        "cce_unavailable": cce_unavailable,
        "interaction_helpfulness_score": (interaction or {}).get(
            "interaction_helpfulness_score"
        ),
        "interaction_helpful_fraction": (interaction or {}).get("helpful_fraction"),
        "interaction": interaction,
        "transcript_path": str(transcript_path),
        "final_answer": result.get("final_answer") or "",
        "final_answer_preview": (result.get("final_answer") or "")[-2000:],
        "chat_history": list(env.chat_history)[-80:],
        "action_log_tail": list(env.action_log)[-40:],
        **summarize_action_log(env.action_log),
        "elapsed_seconds": time.perf_counter() - started_at,
        "status": "error" if run_error else "ok",
        "error": run_error,
    }


def _prepare_contest_run(args: argparse.Namespace) -> tuple:
    """Resolve the same effective contest settings for execution and reuse."""
    system_variant = canonical_baseline(args.system_variant)
    transport = (
        provider_action_transport(args.provider)
        if args.live
        else "prompt_json"
    )
    if args.action_calling == "prompt-json":
        transport = "prompt_json"
    elif args.action_calling == "native" and transport != "native":
        raise ValueError(
            f"--provider {args.provider} does not expose native tool calling; "
            "use --action-calling auto or emulated."
        )
    elif args.action_calling == "emulated":
        if not args.live:
            raise ValueError("--action-calling emulated requires --live.")
        if provider_action_transport(args.provider) != "emulated":
            raise ValueError(
                f"--provider {args.provider} has no emulated tool adapter."
            )
        transport = "emulated"
    manifest = load_contest_manifest(
        args.contest_manifest,
        benchmark_root=REPO_ROOT / "data" / "benchmarks",
    )
    contest_budget = resolve_contest_budget(
        manifest.competition_id,
        max_turns=args.max_turns,
        max_api_calls=args.max_api_calls,
        max_total_tokens=args.max_total_tokens,
    )
    if args.max_output_tokens is None:
        args.max_output_tokens = contest_budget.max_output_tokens_per_call or TINKER_DEFAULT_MAX_TOKENS
    if args.max_output_tokens <= 0:
        raise ValueError("--max-output-tokens must be positive.")
    contest_rules = get_contest_rules(manifest.competition_id)
    encoded_team_size = (
        int(contest_rules.team_size)
        if contest_rules and contest_rules.team_size.isdigit()
        else 0
    )
    team_size = args.team_size or encoded_team_size or int(
        manifest.tasks[0].benchmark.get("team_size") or 3
    )
    if system_variant == "single_agent":
        team_size = 1
    # Rule-card baselines: the card is mandatory and it also fixes the
    # roster. Without --team-size the card's default roster is used; an
    # explicit size outside the card's range is a configuration error.
    contest_rule_card = None
    baseline_features = BASELINES[system_variant]
    rules_mode = args.rules_mode or baseline_features.rule_card
    if baseline_features.coach == "card" and rules_mode != "enforced":
        raise ValueError("otc requires --rules-mode enforced; off/prompt_only would change its protocol")
    if rules_mode == "enforced" and baseline_features.coach != "card":
        raise ValueError("--rules-mode enforced is supported only by the otc contest baseline; use prompt_only for other baselines")
    if rules_mode == "off" and (args.rules_root is not None or args.rules_strict):
        raise ValueError("--rules-root/--rules-strict require an enabled --rules-mode")
    baseline_features = replace(baseline_features, rule_card=rules_mode)
    if baseline_features.rule_card != "off":
        contest_rule_card = load_rule_card(manifest.competition_id, rules_root=args.rules_root)
        if contest_rule_card is None:
            unavailable = ContestRulesUnavailable(
                manifest.competition_id, rules_mode, args.rules_root or DEFAULT_RULES_ROOT
            )
            if args.rules_strict:
                raise ValueError(str(unavailable))
            raise unavailable
        if not args.team_size and rules_mode == "enforced":
            team_size = contest_rule_card.team_size_default
        elif rules_mode == "enforced" and not (
            contest_rule_card.team_size_min
            <= team_size
            <= contest_rule_card.team_size_max
        ):
            raise SystemExit(
                f"--team-size {team_size} is outside the {manifest.competition_id} "
                f"rule card range {contest_rule_card.team_size_min}-"
                f"{contest_rule_card.team_size_max}."
            )
        if args.max_api_calls is None and baseline_features.coach == "card":
            # Card turn = private think call(s) + one action per seat, plus
            # the Coach's single turn-0 brief.
            policy_probe = open_table_policy(
                contest_rule_card, team_size=team_size, programming=True
            )
            contest_budget = resolve_contest_budget(
                manifest.competition_id,
                max_turns=args.max_turns,
                max_api_calls=(
                    contest_budget.max_turns
                    * team_size
                    * (1 + policy_probe.private_think_calls_per_turn)
                    + 1
                ),
                max_total_tokens=args.max_total_tokens,
            )
    rule_guidance = ""
    if contest_rules:
        rule_guidance = (
            f"Team: {contest_rules.team_size}; duration: {contest_rules.duration}; "
            f"tools: {contest_rules.tools_official}; scoring: "
            f"{contest_rules.scoring_official}; penalties: "
            f"{contest_rules.penalties_official}; search: "
            f"{contest_rules.search_policy}."
        )
    if rules_mode == "prompt_only":
        # Prompt-only exposes the card's roster without enforcing its size on
        # the experiment's active seats.
        visible = agent_view(contest_rule_card)
        assert_agent_view_hides_eval(visible)
        # The selected card is authoritative for this condition; do not append
        # the legacy static guidance, which may describe different constraints.
        rule_guidance = "RULE CARD (prompt_only)\n" + json.dumps(visible, ensure_ascii=False)
    run_config = ContestRunConfig(
        system_variant=system_variant,
        team_size=team_size,
        max_turns=contest_budget.max_turns,
        max_api_calls=contest_budget.max_api_calls,
        max_tokens=contest_budget.max_total_tokens,
        max_simulated_minutes=(
            args.max_simulated_minutes
            if args.max_simulated_minutes is not None
            else max(
                contest_budget.duration_minutes or 0,
                contest_budget.max_turns * contest_budget.minutes_per_turn,
            )
        ),
        minutes_per_turn=contest_budget.minutes_per_turn,
        require_review=args.require_review,
        require_final_review=args.require_final_review,
        start_seat=args.start_seat,
        rule_guidance=rule_guidance,
        programming_deadline_submit=args.programming_deadline_submit,
        rule_card=contest_rule_card,
        features=baseline_features,
    )
    if run_config.otc_policy is not None:
        from artifact_contract import delivery_route
        route = delivery_route(contest_rule_card)
        if route in {"slides", "document", "artifact_bundle"}:
            raise ValueError(f"{manifest.competition_id} requires the {route} delivery pipeline; "
                             "use src/run_otc_artifact.py, not a text-only contest run")
    model = _resolve_model(args.provider, args.model) if args.live else "mock"
    judge_provider = _resolve_judge_provider(args.provider, args.judge_provider)
    judge_model = _resolve_judge_model(judge_provider, args.provider, model, args.judge_model)
    judge_collab = bool(args.live and (args.judge_collab if args.judge_collab is not None else True))
    judge_cce = bool(args.live and args.judge_cce)
    identity = build_run_identity(
        manifest, run_config,
        execution={
            "mode": "live" if args.live else "mock",
            "provider": args.provider if args.live else "mock",
            "model": model,
            "action_calling": transport,
            "max_output_tokens": args.max_output_tokens if args.live else None,
            "temperature": args.temperature if args.live else None,
        },
        evaluation={
            "judge_collab": judge_collab,
            "judge_cce": judge_cce,
            "provider": judge_provider if judge_collab or judge_cce else None,
            "model": judge_model if judge_collab or judge_cce else None,
        },
    )
    return manifest, run_config, transport, identity


def inspect_contest_run(argv: list[str]) -> tuple[str, dict]:
    """Read-only batch preflight using the CLI's parser and resolved defaults."""
    load_repo_dotenv(REPO_ROOT / ".env")
    args = _build_parser().parse_args(argv)
    if args.output is None or args.contest_manifest is None:
        raise ValueError("Contest reuse checks require --output and --contest-manifest")
    _manifest, _config, _transport, identity = _prepare_contest_run(args)
    return inspect_contest_output(args.output, identity), identity


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--provider", choices=PROVIDERS, default="perplexity")
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=None,
        help="Maximum generated tokens per model call: explicit value, else contest registry (ICPC/IIOT 4096), else 8192. Legacy per-problem default: 8192.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=TINKER_DEFAULT_TEMPERATURE,
        help="Tinker sampling temperature (default: 0.2)",
    )
    parser.add_argument("--schema", default="centralized", choices=list(SCHEMAS.keys()))
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help=(
            "Override contest turn budget (default: official duration / 5 min "
            "per turn, e.g. ARML 1h = 12 turns; hard cap 90)"
        ),
    )
    parser.add_argument("--no-synthesize", action="store_true")
    parser.add_argument(
        "--judge-task",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Run registered task judge after submit (default: on for --live)",
    )
    parser.add_argument(
        "--judge-collab",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Run MultiAgentBench coordination score (default: on for --live)",
    )
    parser.add_argument(
        "--judge-cce",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Run AgentWorld-style causal action graph judge "
            "(opt-in; may add up to one judge call per turn)"
        ),
    )
    parser.add_argument(
        "--judge-provider",
        choices=JUDGE_PROVIDERS,
        default=None,
        help="LLM provider for task/collab judges (default: tinker when --provider tinker, else perplexity)",
    )
    parser.add_argument(
        "--judge-model",
        default=None,
        help="Override judge model (default: same as --model when judge provider matches agent provider)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only first N contests")
    parser.add_argument(
        "--competitions",
        default=None,
        help="Comma-separated competition ids (default: all smoke representatives)",
    )
    parser.add_argument(
        "--problem-id",
        default=None,
        help="Exact benchmark problem id; requires exactly one competition",
    )
    parser.add_argument(
        "--contest-manifest",
        type=Path,
        default=None,
        help="Run one explicit multi-problem contest manifest under a shared budget.",
    )
    parser.add_argument(
        "--system-variant",
        choices=(*BASELINE_NAMES, *BASELINE_ALIASES),
        default="otc",
        help=(
            "Contest-session baseline: single_agent, decentralized, centralized, "
            "otc (rule-card Open Table "
            "Coach: data/rules/<competition>/collaboration.json drives the coach "
            "stages, think call, limits, budgets and roster; team size defaults to "
            "the card's) (legacy aliases: vanilla[_team] -> decentralized, "
            "strategic[_team] and open_table_coach[_memory] -> otc)."
        ),
    )
    parser.add_argument(
        "--action-calling",
        choices=("auto", "native", "emulated", "prompt-json"),
        default="auto",
        help=(
            "Contest action transport: provider-native functions, schema-validated "
            "emulation, or strict prompt JSON fallback (default: auto)."
        ),
    )
    parser.add_argument(
        "--team-size",
        type=int,
        default=None,
        help="Override contest-session team size.",
    )
    parser.add_argument(
        "--max-api-calls",
        type=int,
        default=None,
        help="Shared contest-session API-call limit.",
    )
    parser.add_argument(
        "--max-total-tokens",
        type=int,
        default=None,
        help="Shared contest-session output-token limit.",
    )
    parser.add_argument(
        "--max-simulated-minutes",
        type=float,
        default=None,
        help="Override the contest-session simulated clock limit.",
    )
    parser.add_argument(
        "--start-seat",
        type=int,
        default=0,
        help="Rotate the first acting seat for matched-pair repetitions.",
    )
    parser.add_argument(
        "--programming-deadline-submit",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "At contest end, submit one eligible recorded source per "
            "never-officially-submitted programming task. OTC still requires "
            "current independent approval and sample evidence; other variants "
            "may waive those gates. May incur WA penalties."
        ),
    )
    parser.add_argument(
        "--require-review",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override review workflow and, unless separately specified, final review.",
    )
    parser.add_argument(
        "--require-final-review",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Contest-session final-review override (default: follows --require-review / baseline).",
    )
    parser.add_argument(
        "--structured-gold",
        action="store_true",
        help="Run every benchmark problem with at least one deterministic scored gold part",
    )
    parser.add_argument(
        "--benchmark-suite",
        choices=["non_math", "math", "all"],
        default=None,
        help="Run every benchmark problem in a suite (non_math = all collected non-math contests)",
    )
    parser.add_argument(
        "--allow-missing-rule-card",
        action="store_true",
        help="With --benchmark-suite, include contests that lack data/rules/<id>/ cards",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a prior --output directory and skip fully completed cases",
    )
    parser.add_argument(
        "--rules-mode",
        default=None,
        choices=[mode.value for mode in RulesMode],
        help="Default: enforced for otc; off otherwise. Contest enforcement is supported only by otc.",
    )
    parser.add_argument("--rules-root", type=Path, default=None)
    parser.add_argument("--rules-strict", action="store_true")
    return parser


def main() -> None:
    load_repo_dotenv(REPO_ROOT / ".env")
    parser = _build_parser()
    args = parser.parse_args()

    if not args.contest_manifest:
        args.max_output_tokens = args.max_output_tokens if args.max_output_tokens is not None else TINKER_DEFAULT_MAX_TOKENS
        args.rules_mode = args.rules_mode or RulesMode.OFF.value
        if args.require_review is not None or args.require_final_review is not None:
            parser.error("--require-review/--require-final-review require --contest-manifest")

    judge_task = args.judge_task if args.judge_task is not None else bool(args.live)
    judge_collab = args.judge_collab if args.judge_collab is not None else bool(args.live)
    judge_provider = _resolve_judge_provider(args.provider, args.judge_provider)
    try:
        model = (
            _resolve_model(args.provider, args.model)
            if args.live
            else (args.model or DEFAULT_MODEL)
        )
        cases = (
            []
            if args.contest_manifest
            else _select_cases(
                args.competitions,
                args.problem_id,
                args.limit,
                structured_gold=args.structured_gold,
                benchmark_suite=args.benchmark_suite,
                rules_root=args.rules_root,
                require_rule_card=not args.allow_missing_rule_card,
            )
        )
        if args.contest_manifest and (
            args.problem_id or args.competitions or args.structured_gold
        ):
            raise ValueError(
                "--contest-manifest cannot be combined with --problem-id, "
                "--competitions, or --structured-gold."
            )
        if args.resume and args.output is None:
            raise ValueError("--resume requires an explicit --output directory.")
        if args.max_output_tokens is not None and args.max_output_tokens <= 0:
            raise ValueError("--max-output-tokens must be positive.")
        if args.temperature < 0:
            raise ValueError("--temperature must be non-negative.")
        judge_model = _resolve_judge_model(
            judge_provider,
            args.provider,
            model if args.live else DEFAULT_MODEL,
            args.judge_model,
        )
    except ValueError as exc:
        parser.error(str(exc))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = args.output or (REPO_ROOT / "results" / "competition_batch" / timestamp)
    prepared_contest = None
    output_state = "new"
    if args.contest_manifest:
        try:
            prepared_contest = _prepare_contest_run(args)
            output_state = inspect_contest_output(out_dir, prepared_contest[3])
            if output_state != "new" and not args.resume:
                raise RunCompatibilityError(
                    f"{out_dir} already contains a matching {output_state} run. "
                    "Use --resume to reuse it or choose a fresh --output directory."
                )
        except ContestRulesUnavailable as exc:
            if any((out_dir / name).exists() for name in (
                "run_config.json", "contest_checkpoint.json", "contest_session.json"
            )):
                parser.error(f"{exc}. Use a fresh --output directory for this unavailable condition.")
            _write_json_atomic(out_dir / "rules_status.json", exc.metadata)
            print(json.dumps(exc.metadata, ensure_ascii=False))
            return
        except ValueError as exc:
            parser.error(str(exc))
        if output_state == "complete":
            print(f"Skipped verified complete contest: {out_dir}")
            return
    out_dir.mkdir(parents=True, exist_ok=True)
    if prepared_contest is not None:
        _write_json_atomic(out_dir / "run_config.json", prepared_contest[3])
    out_path = out_dir / "competition_batch.json"
    tsv_path = out_dir / "competition_batch.tsv"
    summary_tsv_path = out_dir / "competition_summary.tsv"

    need_request = (
        args.live
        and (
            args.judge_cce
            or judge_collab
            or (
                not args.contest_manifest
                and judge_task
            )
        )
    )
    if need_request:
        key_name = _judge_api_key_name(judge_provider)
        if not os.environ.get(key_name):
            parser.error(
                f"Set {key_name} for task/collaboration judging with "
                f"--judge-provider {judge_provider}, or disable the enabled judges."
            )
    try:
        query_fn = (
            _make_live_query(
                args.provider,
                model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
            )
            if args.live
            else resolve_query_fn(use_mock=True)
        )
    except ValueError as exc:
        parser.error(str(exc))
    request_fn = (
        resolve_request_fn(
            provider=judge_provider,
            model=judge_model,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
        )
        if need_request
        else None
    )
    cce_request_fn = (
        resolve_request_fn(
            provider=judge_provider,
            model=judge_model,
            max_output_tokens=args.max_output_tokens,
            temperature=0.0,
        )
        if args.live and args.judge_cce
        else None
    )

    if args.contest_manifest:
        manifest, run_config, transport, run_identity = prepared_contest
        system_variant = run_config.system_variant
        team_size = run_config.team_size
        request_actions = transport in {"native", "emulated"}
        action_request_fn = (
            resolve_request_fn(
                provider=args.provider,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
            )
            if request_actions
            else None
        )
        checkpoint_path = out_dir / "contest_checkpoint.json"
        session_checkpoint = None
        memory_checkpoint = None
        if output_state == "resume":
            restored = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            session_checkpoint = restored["session"]
            memory_checkpoint = restored["memory"]

        def persist_contest_checkpoint(
            session_state: dict,
            memory_state: str,
        ) -> None:
            _write_json_atomic(
                checkpoint_path,
                {
                    "run_identity": run_identity,
                    "protocol_version": PROTOCOL_VERSION,
                    "action_set_version": ACTION_SET_VERSION,
                    "session": session_state,
                    "memory": memory_state,
                },
            )

        run_kwargs = {
            "action_request_fn": action_request_fn,
            "action_transport": transport,
            "task_action_executor": EnvironmentTaskExecutor(
                manifest,
                benchmark_root=REPO_ROOT / "data" / "benchmarks",
            ),
            "session_checkpoint": session_checkpoint,
            "memory_checkpoint": memory_checkpoint,
            "checkpoint_callback": persist_contest_checkpoint,
        }
        if run_config.features.coach == "none":
            result = run_vanilla_contest(
                manifest,
                query_fn,
                run_config,
                **run_kwargs,
            )
        else:
            result = run_strategic_contest(
                manifest,
                query_fn,
                run_config,
                coach_query_fn=query_fn,
                **run_kwargs,
            )
        result["grade"] = grade_contest_result(manifest, result)
        result["metrics"]["task_utility"] = result["grade"]["task_utility"]
        if judge_collab and request_fn is not None:
            events = result["memory"]["events"]
            agents = [f"Agent_{index + 1}" for index in range(team_size)]
            chat_history = [
                {
                    "sender": event["actor"],
                    "content": str(
                        event.get("payload", {}).get("content")
                        or event.get("payload", {}).get("report")
                        or event.get("payload", {})
                    ),
                }
                for event in events
                if event.get("actor") in agents
                and event.get("kind")
                in {
                    "speak",
                    "direct_message",
                    "request_review",
                    "review_answer",
                }
            ]
            action_log = [
                {
                    "agent": event["actor"],
                    "action": event["kind"],
                    "payload": event.get("payload", {}),
                }
                for event in events
                if event.get("actor") in agents
            ]
            task_text = "\n\n".join(
                f"{task.task_id}\n{task.prompt}" for task in manifest.tasks
            )
            task_results = (
                f"submitted={any(result['submissions'].values())} "
                f"grade_method={result['grade']['method']} "
                f"score={result['grade']['score']}/{result['grade']['max_score']}"
            )
            try:
                coordination = score_coordination(
                    request_fn=request_fn,
                    task_text=task_text,
                    agents=agents,
                    schema=system_variant,
                    chat_history=chat_history,
                    action_log=action_log,
                    task_results=task_results,
                ).to_dict()
                interaction = score_interaction_helpfulness(
                    request_fn=request_fn,
                    task_text=task_text,
                    agents=agents,
                    schema=system_variant,
                    chat_history=chat_history,
                    action_log=action_log,
                    final_answer=json.dumps(
                        result["submissions"],
                        ensure_ascii=False,
                    ),
                    task_results=task_results,
                ).to_dict()
                result["coordination"] = coordination
                result["interaction"] = interaction
                result["metrics"].update(
                    {
                        "communication_score": coordination[
                            "communication_score"
                        ],
                        "planning_score": coordination["planning_score"],
                        "coordination_score": coordination[
                            "coordination_score"
                        ],
                    }
                )
            except Exception as exc:
                result["coordination_error"] = _sanitize_exception(exc)
        if cce_request_fn is not None:
            cce_rows = {}
            events = result["memory"]["events"]
            agents = [f"Agent_{index + 1}" for index in range(team_size)]
            for task in manifest.tasks:
                utility = result["grade"]["tasks"][task.task_id]["utility"]
                if utility is None:
                    continue
                action_log = [
                    {
                        "turn": event["turn"],
                        "agent": event["actor"],
                        "action": event["kind"],
                        "payload": event["payload"],
                    }
                    for event in events
                    if event.get("task_id") == task.task_id
                ]
                cce_rows[task.task_id] = score_cce(
                    request_fn=cce_request_fn,
                    task_text=task.prompt,
                    action_log=action_log,
                    task_utility=utility,
                    task_outcome=json.dumps(
                        result["grade"]["tasks"][task.task_id],
                        ensure_ascii=False,
                    ),
                    agents=agents,
                    trace_partial_credit=0 < utility < 1,
                ).to_dict()
            result["cce"] = cce_rows
            result["metrics"]["cce"] = (
                sum(row["cce"] for row in cce_rows.values()) / len(cce_rows)
                if cce_rows
                else None
            )
            result["diagnostics"]["cce"] = result["metrics"]["cce"]
            result["diagnostics"]["cce_status"] = "scored" if cce_rows else "grading_unavailable"
        result["run_identity"] = run_identity
        result["run"] = {
            "mode": "live" if args.live else "mock",
            "provider": args.provider,
            "model": model if args.live else "mock",
            "system_variant": system_variant,
            "requested_variant": args.system_variant,
            "baseline": result["baseline"],
            "action_calling": result["action_calling"],
            "max_output_tokens": args.max_output_tokens if args.live else None,
            "temperature": args.temperature if args.live else None,
            "rules_mode": run_config.features.rule_card,
            "rules_root": str(args.rules_root or DEFAULT_RULES_ROOT) if run_config.rule_card else None,
            "rules_strict": args.rules_strict,
            "review_required": run_config.review_required,
            "final_review_required": run_config.final_review_required,
            "manifest": str(args.contest_manifest),
            "start_seat": args.start_seat,
            "elapsed_seconds": (result.get("timing") or {}).get("elapsed_seconds"),
            "started_at": (result.get("timing") or {}).get("started_at"),
            "ended_at": (result.get("timing") or {}).get("ended_at"),
        }
        persist_contest_checkpoint(
            result["session_checkpoint"],
            json.dumps(result["memory"], ensure_ascii=False),
        )
        _write_json_atomic(out_dir / "contest_session.json", result)
        elapsed = (result.get("timing") or {}).get("elapsed_seconds")
        elapsed_text = (
            f"{float(elapsed):.1f}s" if elapsed is not None else "N/A"
        )
        utility = result["grade"]["task_utility"]
        utility_text = f"{utility:.3f}" if utility is not None else "unavailable"
        print(
            f"Contest session: {manifest.session_id} | "
            f"variant={system_variant} | tasks={len(manifest.tasks)} | "
            f"utility={utility_text} | "
            f"api={result['budget']['api_calls_used']} | "
            f"tokens={result['budget']['tokens_used']} | "
            f"wall={elapsed_text} | "
            f"CS={result.get('metrics', {}).get('coordination_score', 'N/A')}"
        )
        print(f"Saved: {out_dir / 'contest_session.json'}")
        return

    print(
        f"Competition batch: {len(cases)} contests | schema={args.schema} | "
        f"max_turns={args.max_turns or 'duration/5min (cap 90)'} | "
        f"mode={'live' if args.live else 'mock'} | provider={args.provider} | "
        f"judge_provider={judge_provider} | "
        f"task_judge={'on' if judge_task else 'off'} | "
        f"collab_judge={'on' if judge_collab else 'off'} | "
        f"cce_judge={'on' if args.judge_cce else 'off'}"
    )

    metadata = {
        "timestamp": timestamp,
        "mode": "live" if args.live else "mock",
        "provider": args.provider,
        "model": model if args.live else "mock",
        "max_output_tokens": args.max_output_tokens if args.live else None,
        "temperature": args.temperature if args.live else None,
        "schema": args.schema,
        "rules_mode": args.rules_mode,
        "max_turns": args.max_turns,
        "structured_gold": args.structured_gold,
        "benchmark_suite": args.benchmark_suite,
        "selected_cases": [
            {"competition": competition, "problem_id": problem_id}
            for competition, problem_id in cases
        ],
        "judge_task": judge_task,
        "judge_collab": judge_collab,
        "judge_cce": args.judge_cce,
        "cce_judge_temperature": 0.0 if args.judge_cce else None,
        "judge_provider": judge_provider if need_request else None,
        "judge_model": judge_model if need_request else None,
    }
    rows: list[dict] = []
    if args.resume and out_path.exists():
        try:
            rows, prior_timestamp = _load_resume_rows(out_path, metadata)
        except ValueError as exc:
            parser.error(str(exc))
        metadata["timestamp"] = prior_timestamp or timestamp

    def current_summary(current_rows: list[dict]) -> dict:
        return _build_summary(
            current_rows,
            {
                **metadata,
                "rules_coverage": {
                    "covered": sum(
                        1
                        for row in current_rows
                        if row.get("rules_coverage") == "covered"
                    ),
                    "missing_card": sum(
                        1
                        for row in current_rows
                        if row.get("rules_coverage") == "missing_card"
                    ),
                },
            },
        )

    row_by_case = {
        (row.get("competition"), row.get("problem_id")): row for row in rows
    }
    for competition, problem_id in cases:
        label = f"{competition}/{problem_id}"
        existing = row_by_case.get((competition, problem_id))
        if existing and _row_is_complete(
            existing,
            judge_task=judge_task,
            judge_collab=judge_collab,
            judge_cce=args.judge_cce,
        ):
            print(f"\n--- {label} ---\n  resume: already complete", flush=True)
            continue
        print(f"\n--- {label} ---", flush=True)
        try:
            row = run_one(
                competition,
                problem_id,
                schema=args.schema,
                query_fn=query_fn,
                request_fn=request_fn,
                rounds=args.max_turns,
                synthesize=not args.no_synthesize,
                judge_task=judge_task,
                judge_collab=judge_collab,
                out_dir=out_dir,
                rules_mode=args.rules_mode,
                rules_root=args.rules_root,
                rules_strict=args.rules_strict,
                provider=args.provider,
                model=model if args.live else "mock",
                max_output_tokens=args.max_output_tokens if args.live else None,
                temperature=args.temperature if args.live else None,
                judge_cce=args.judge_cce,
                cce_request_fn=cce_request_fn,
            )
            if row.get("status") == "rules_baseline_unavailable":
                print(f"  UNAVAILABLE: {row['error']}", flush=True)
                row_by_case[(competition, problem_id)] = row
                rows = [
                    row_by_case[case] for case in cases if case in row_by_case
                ]
                checkpoint = current_summary(rows)
                _write_json_atomic(out_path, checkpoint)
                _write_results_tsv(tsv_path, rows)
                _write_summary_tsv(summary_tsv_path, checkpoint)
                continue
            bits = [
                f"turns={row['turns_used']}/{row['max_turns']}",
                f"api={row['api_calls']}",
                f"grade={row['grade_method']}",
            ]
            if row.get("grade_score") is not None:
                bits.append(f"task={row['grade_score']:g}/{row['grade_max_score']:g}")
            if row.get("coordination_score") is not None:
                bits.append(f"CS={row['coordination_score']:.2f}")
            if row.get("cce") is not None:
                bits.append(f"CCE={row['cce']:.3f}")
            print("  ok " + " ".join(bits), flush=True)
        except ProblemNotFoundError as exc:
            row = {
                "competition": competition,
                "problem_id": problem_id,
                "provider": args.provider,
                "model": model if args.live else "mock",
                "schema": args.schema,
                "rules_mode": args.rules_mode,
                "status": "error",
                "error": _sanitize_exception(exc),
            }
            print(f"  FAIL: {exc}", flush=True)
        except Exception as exc:
            row = {
                "competition": competition,
                "problem_id": problem_id,
                "provider": args.provider,
                "model": model if args.live else "mock",
                "schema": args.schema,
                "rules_mode": args.rules_mode,
                "status": "error",
                "error": _sanitize_exception(exc),
            }
            print(f"  FAIL: {row['error']}", flush=True)
        row_by_case[(competition, problem_id)] = row
        rows = [row_by_case[case] for case in cases if case in row_by_case]
        checkpoint = current_summary(rows)
        _write_json_atomic(out_path, checkpoint)
        _write_results_tsv(tsv_path, rows)
        _write_summary_tsv(summary_tsv_path, checkpoint)

    summary = current_summary(rows)
    _write_json_atomic(out_path, summary)
    _write_results_tsv(tsv_path, rows)
    _write_summary_tsv(summary_tsv_path, summary)
    print("\n" + "=" * 60)
    print(
        f"  DONE: {summary['ok']}/{summary['total']} ok | "
        f"{summary['submitted']} submitted | {summary['graded']} graded | "
        f"{summary['with_coordination']} with CS | "
        f"{summary['with_cce']} with CCE"
    )
    print(f"  Saved: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
