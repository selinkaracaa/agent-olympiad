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
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import CollabConfig, SCHEMAS, run_collaboration
from contest_rules import get_contest_rules
from env import OlympiadEnvironment, ProblemNotFoundError
from evaluation.collaboration_score import (
    score_coordination,
    score_interaction_helpfulness,
)
from evaluation.finalize import apply_registered_judge
from env_config import load_repo_dotenv
from llm import (
    make_perplexity_caller,
    make_tinker_caller,
    resolve_query_fn,
    resolve_request_fn,
)
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
        "scratchpad_count": counts.get("write_scratchpad", 0),
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


def _row_is_complete(row: dict, *, judge_task: bool, judge_collab: bool) -> bool:
    return (
        row.get("status") == "ok"
        and (not judge_task or row.get("graded") is True)
        and (not judge_collab or row.get("coordination_score") is not None)
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
    if schema == "open_table_coach":
        return [*agents, "Coach"]
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


def main() -> None:
    load_repo_dotenv(REPO_ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--provider", choices=PROVIDERS, default="perplexity")
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=TINKER_DEFAULT_MAX_TOKENS,
        help="Maximum generated tokens per Tinker sample (default: 8192)",
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
        help="Override contest turn budget (default: registry, usually 50)",
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
        default=RulesMode.OFF.value,
        choices=[mode.value for mode in RulesMode],
    )
    parser.add_argument("--rules-root", type=Path, default=None)
    parser.add_argument("--rules-strict", action="store_true")
    args = parser.parse_args()

    judge_task = args.judge_task if args.judge_task is not None else bool(args.live)
    judge_collab = args.judge_collab if args.judge_collab is not None else bool(args.live)
    judge_provider = _resolve_judge_provider(args.provider, args.judge_provider)
    try:
        model = (
            _resolve_model(args.provider, args.model)
            if args.live
            else (args.model or DEFAULT_MODEL)
        )
        cases = _select_cases(
            args.competitions,
            args.problem_id,
            args.limit,
            structured_gold=args.structured_gold,
            benchmark_suite=args.benchmark_suite,
            rules_root=args.rules_root,
            require_rule_card=not args.allow_missing_rule_card,
        )
        if args.resume and args.output is None:
            raise ValueError("--resume requires an explicit --output directory.")
        if args.max_output_tokens <= 0:
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
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "competition_batch.json"
    tsv_path = out_dir / "competition_batch.tsv"
    summary_tsv_path = out_dir / "competition_summary.tsv"

    need_request = args.live and (judge_task or judge_collab)
    if need_request:
        key_name = _judge_api_key_name(judge_provider)
        if not os.environ.get(key_name):
            parser.error(
                f"Set {key_name} for task/collaboration judging with "
                f"--judge-provider {judge_provider}, or disable both judges."
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

    print(
        f"Competition batch: {len(cases)} contests | schema={args.schema} | "
        f"max_turns={args.max_turns or 'standard(30)'} | "
        f"mode={'live' if args.live else 'mock'} | provider={args.provider} | "
        f"judge_provider={judge_provider} | "
        f"task_judge={'on' if judge_task else 'off'} | "
        f"collab_judge={'on' if judge_collab else 'off'}"
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
        f"{summary['with_coordination']} with CS"
    )
    print(f"  Saved: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
