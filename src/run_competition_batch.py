"""Competition-level batch: full turn budgets, task score + MultiAgentBench CS.

Defaults follow the 2026-08-21 meeting:
  - schema: centralized (best of ARML pilot)
  - turns: contest registry (usually 50)
  - beyond ARML: one representative year per family
  - signals: task grade + coordination/collaboration score

Usage:
  export PERPLEXITY_API_KEY=pplx-...
  python3 src/run_competition_batch.py --live
  python3 src/run_competition_batch.py --live --max-turns 10 --limit 3
  python3 src/run_competition_batch.py --live --competitions arml_local,wsc_writing,mcm
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import CollabConfig, SCHEMAS, run_collaboration
from contest_rules import get_contest_rules
from env import OlympiadEnvironment, ProblemNotFoundError
from evaluation.collaboration_score import score_coordination
from evaluation.finalize import apply_registered_judge
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
) -> list[tuple[str, str]]:
    selected = (
        [item.strip() for item in competitions.split(",") if item.strip()]
        if competitions
        else []
    )
    if problem_id:
        if len(selected) != 1:
            raise ValueError("--problem-id requires exactly one --competitions value.")
        cases = [(selected[0], problem_id)]
    else:
        wanted = set(selected)
        cases = [(c, p) for c, p in SMOKE_CASES if not wanted or c in wanted]
    return cases[:limit] if limit is not None else cases


def _resolve_model(provider: str, supplied_model: str | None) -> str:
    if supplied_model:
        return supplied_model
    if provider == "tinker":
        model = os.environ.get("TINKER_MODEL")
        return model or TINKER_DEFAULT_MODEL
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
    env = OlympiadEnvironment(
        competition,
        problem_id,
        max_turns=rounds,
        rules_mode=rules_mode,
        rules_root=rules_root,
        rules_strict=rules_strict,
    )
    baseline = env.rules_metadata()
    transcript_path = (
        out_dir
        / "transcripts"
        / f"{competition}__{problem_id}__{schema}__{env.rules_mode.value}.json"
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
                work_dir=out_dir / "judge" / problem_id,
                repo_root=REPO_ROOT,
            )
            result["grade"] = grade

        if judge_collab and request_fn is not None:
            agents = _agent_names(env, schema)
            # Prefer names observed in the chat log when available.
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
            coordination = score_coordination(
                request_fn=request_fn,
                task_text=str(
                    env.problem_data.get("problem_description") or env.problem_id
                ),
                agents=agents,
                schema=schema,
                chat_history=env.chat_history,
                action_log=env.action_log,
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
        "wrong_submissions": env.wrong_submissions,
        "penalty_minutes": env.penalty_minutes(),
        "rule_violations": list(env.rule_violations),
        "grade_method": grade.get("method"),
        "grade_score": grade.get("score"),
        "grade_max_score": grade.get("max_score"),
        "graded": grade.get("graded"),
        "coordination_score": (coordination or {}).get("coordination_score"),
        "communication_score": (coordination or {}).get("communication_score"),
        "planning_score": (coordination or {}).get("planning_score"),
        "coordination": coordination,
        "transcript_path": str(transcript_path),
        "final_answer": result.get("final_answer") or "",
        "final_answer_preview": (result.get("final_answer") or "")[-2000:],
        "chat_history": list(env.chat_history)[-80:],
        "action_log_tail": list(env.action_log)[-40:],
        "status": "error" if run_error else "ok",
        "error": run_error,
    }


def main() -> None:
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
    parser.add_argument("--output", type=Path, default=None)
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
    try:
        model = (
            _resolve_model(args.provider, args.model)
            if args.live
            else (args.model or DEFAULT_MODEL)
        )
        cases = _select_cases(args.competitions, args.problem_id, args.limit)
        if args.max_output_tokens <= 0:
            raise ValueError("--max-output-tokens must be positive.")
        if args.temperature < 0:
            raise ValueError("--temperature must be non-negative.")
    except ValueError as exc:
        parser.error(str(exc))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = args.output or (REPO_ROOT / "results" / "competition_batch" / timestamp)
    out_dir.mkdir(parents=True, exist_ok=True)

    need_request = args.live and (judge_task or judge_collab)
    if need_request and not os.environ.get("PERPLEXITY_API_KEY"):
        parser.error(
            "Set PERPLEXITY_API_KEY for task/collaboration judging, "
            "or disable both judges."
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
            provider="perplexity",
            model=model if args.provider == "perplexity" else DEFAULT_MODEL,
        )
        if need_request
        else None
    )

    print(
        f"Competition batch: {len(cases)} contests | schema={args.schema} | "
        f"max_turns={args.max_turns or 'registry(50)'} | "
        f"mode={'live' if args.live else 'mock'} | provider={args.provider} | "
        f"task_judge={'on' if judge_task else 'off'} | "
        f"collab_judge={'on' if judge_collab else 'off'}"
    )

    rows: list[dict] = []
    for competition, problem_id in cases:
        label = f"{competition}/{problem_id}"
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
                rows.append(row)
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
        rows.append(row)

    summary = {
        "timestamp": timestamp,
        "mode": "live" if args.live else "mock",
        "provider": args.provider,
        "model": model if args.live else "mock",
        "max_output_tokens": args.max_output_tokens if args.live else None,
        "temperature": args.temperature if args.live else None,
        "schema": args.schema,
        "rules_mode": args.rules_mode,
        "rules_coverage": {
            "covered": sum(1 for row in rows if row.get("rules_coverage") == "covered"),
            "missing_card": sum(
                1 for row in rows if row.get("rules_coverage") == "missing_card"
            ),
        },
        "max_turns": args.max_turns,
        "judge_task": judge_task,
        "judge_collab": judge_collab,
        "total": len(rows),
        "ok": sum(1 for r in rows if r.get("status") == "ok"),
        "errors": sum(1 for r in rows if r.get("status") == "error"),
        "rules_baseline_unavailable": sum(
            1 for r in rows if r.get("status") == "rules_baseline_unavailable"
        ),
        "submitted": sum(1 for r in rows if r.get("submitted")),
        "graded": sum(1 for r in rows if r.get("graded")),
        "with_coordination": sum(
            1 for r in rows if r.get("coordination_score") is not None
        ),
        "results": rows,
    }
    out_path = out_dir / "competition_batch.json"
    _write_json_atomic(out_path, summary)
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
