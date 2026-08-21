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
import sys
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
from llm import make_perplexity_caller, resolve_query_fn, resolve_request_fn
from run_smoke_batch import SMOKE_CASES

DEFAULT_MODEL = "openai/gpt-5.4-mini"


def _agent_names(env: OlympiadEnvironment, schema: str) -> list[str]:
    if schema == "centralized":
        workers = [f"Agent_{i}" for i in range(2, env.team_size + 1)]
        return ["Group_Leader", *workers]
    return [f"Agent_{i}" for i in range(1, env.team_size + 1)]


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
) -> dict:
    env = OlympiadEnvironment(competition, problem_id, max_turns=rounds)
    rules = get_contest_rules(competition)
    config = CollabConfig(
        max_turns=rounds,
        rounds=rounds,
        decentralized_events=rounds,
        synthesize=synthesize,
        progress=progress,
    )
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

    coordination = None
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
            task_text=str(env.problem_data.get("problem_description") or env.problem_id),
            agents=agents,
            schema=schema,
            chat_history=env.chat_history,
            action_log=env.action_log,
            task_results=task_results,
        ).to_dict()

    return {
        "competition": competition,
        "problem_id": problem_id,
        "schema": schema,
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
        "final_answer": result.get("final_answer") or "",
        "final_answer_preview": (result.get("final_answer") or "")[:2000],
        "chat_history": list(env.chat_history)[-80:],
        "action_log_tail": list(env.action_log)[-40:],
        "status": "ok",
        "error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
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
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.live and not os.environ.get("PERPLEXITY_API_KEY"):
        raise SystemExit("Set PERPLEXITY_API_KEY for --live runs.")

    judge_task = args.judge_task if args.judge_task is not None else bool(args.live)
    judge_collab = args.judge_collab if args.judge_collab is not None else bool(args.live)

    cases = list(SMOKE_CASES)
    if args.competitions:
        wanted = {c.strip() for c in args.competitions.split(",") if c.strip()}
        cases = [(c, p) for c, p in cases if c in wanted]
    if args.limit is not None:
        cases = cases[: args.limit]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = args.output or (REPO_ROOT / "results" / "competition_batch" / timestamp)
    out_dir.mkdir(parents=True, exist_ok=True)

    query_fn = (
        make_perplexity_caller(model=args.model)
        if args.live
        else resolve_query_fn(use_mock=True)
    )
    need_request = args.live and (judge_task or judge_collab)
    request_fn = (
        resolve_request_fn(provider="perplexity", model=args.model) if need_request else None
    )

    print(
        f"Competition batch: {len(cases)} contests | schema={args.schema} | "
        f"max_turns={args.max_turns or 'registry(50)'} | "
        f"mode={'live' if args.live else 'mock'} | "
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
            )
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
                "status": "error",
                "error": str(exc),
            }
            print(f"  FAIL: {exc}", flush=True)
        except Exception as exc:
            row = {
                "competition": competition,
                "problem_id": problem_id,
                "status": "error",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            print(f"  FAIL: {exc}", flush=True)
        rows.append(row)

    summary = {
        "timestamp": timestamp,
        "mode": "live" if args.live else "mock",
        "model": args.model if args.live else "mock",
        "schema": args.schema,
        "max_turns": args.max_turns,
        "judge_task": judge_task,
        "judge_collab": judge_collab,
        "total": len(rows),
        "ok": sum(1 for r in rows if r.get("status") == "ok"),
        "errors": sum(1 for r in rows if r.get("status") == "error"),
        "submitted": sum(1 for r in rows if r.get("submitted")),
        "graded": sum(1 for r in rows if r.get("graded")),
        "with_coordination": sum(
            1 for r in rows if r.get("coordination_score") is not None
        ),
        "results": rows,
    }
    out_path = out_dir / "competition_batch.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
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
