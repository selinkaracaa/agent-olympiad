"""Smoke one representative problem per competition through the agent pipeline.

Usage:
  export PERPLEXITY_API_KEY=pplx-...
  python3 src/run_smoke_batch.py --live
  python3 src/run_smoke_batch.py              # offline mock
  python3 src/run_smoke_batch.py --live --rounds 1 --schema round_table
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

from collaboration import CollabConfig, run_collaboration, SCHEMAS
from env import OlympiadEnvironment, ProblemNotFoundError
from llm import make_perplexity_caller, resolve_query_fn

BENCHMARK_ROOT = REPO_ROOT / "data" / "benchmarks"

# One representative problem per collected competition.
SMOKE_CASES: list[tuple[str, str]] = [
    ("arml_local", "arml_local_2009"),
    ("arml_national_team", "arml_national_team_2009"),
    ("arml_national_power", "arml_national_power_2009"),
    ("arml_power", "arml_power_fall_2018"),
    ("icpc", "icpc_wf_2012_bottles"),
    ("iiot", "iiot_2017_01"),
    ("ieo_business_case", "ieo_business_case_2021"),
    ("iol_team", "iol_team_2003"),
    ("ioaa_group", "ioaa_group_2025"),
    ("ijso_practical", "ijso_practical_2004_team_practical_2004"),
    ("wsc_writing", "wsc_writing_gq_001"),
    ("jessup", "jessup_2024"),
    ("iypt", "iypt_2024"),
    ("hmmt_team", "hmmt_team_2024"),
    ("hmmt_guts", "hmmt_guts_2024"),
    ("mcm", "mcm_2024_A"),
    ("icm", "icm_2024_D"),
    ("fyziklani", "fyziklani_2024"),
    ("purple_comet", "purple_comet_hs_2024"),
    ("itym", "itym_2024"),
]

DEFAULT_MODEL = "openai/gpt-5.4-mini"


def run_one(
    competition: str,
    problem_id: str,
    schema: str,
    query_fn,
    *,
    rounds: int,
    synthesize: bool,
) -> dict:
    env = OlympiadEnvironment(competition, problem_id, max_turns=rounds)
    evaluation = dict(env.problem_data.get("evaluation") or {})
    config = CollabConfig(
        max_turns=rounds,
        rounds=rounds,
        decentralized_events=rounds,
        synthesize=synthesize,
    )
    result = run_collaboration(schema, env, query_fn, config)
    grade = result.get("grade") or {}
    return {
        "competition": competition,
        "problem_id": problem_id,
        "schema": schema,
        "task_type": env.problem_data.get("task_type"),
        "evaluator_id": evaluation.get("evaluator_id"),
        "evaluation_status": evaluation.get("status"),
        "submitted": result["submitted"],
        "submitted_by": result.get("submitted_by"),
        "turns_used": result["turns_used"],
        "max_turns": result.get("max_turns"),
        "api_calls": result.get("api_calls"),
        "tokens_used": result.get("tokens_used"),
        "chat_messages": result.get("chat_messages"),
        "grade_method": grade.get("method"),
        "grade_reason": grade.get("reason"),
        "final_answer_preview": (result.get("final_answer") or "")[:300],
        "status": "ok",
        "error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Use Perplexity API")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--schema", default="round_table", choices=list(SCHEMAS.keys()))
    parser.add_argument("--rounds", type=int, default=1, help="Collaboration turns per run")
    parser.add_argument("--no-synthesize", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.live and not os.environ.get("PERPLEXITY_API_KEY"):
        raise SystemExit("Set PERPLEXITY_API_KEY for --live runs.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = args.output or (REPO_ROOT / "results" / "smoke_batch" / timestamp)
    out_dir.mkdir(parents=True, exist_ok=True)

    query_fn = (
        make_perplexity_caller(model=args.model)
        if args.live
        else resolve_query_fn(use_mock=True)
    )

    rows: list[dict] = []
    print(f"Smoke batch: {len(SMOKE_CASES)} competitions | schema={args.schema} | rounds={args.rounds}")
    print(f"Mode: {'live' if args.live else 'mock'} | model={args.model if args.live else 'mock'}")

    for competition, problem_id in SMOKE_CASES:
        label = f"{competition}/{problem_id}"
        print(f"\n--- {label} ---", flush=True)
        try:
            row = run_one(
                competition,
                problem_id,
                args.schema,
                query_fn,
                rounds=args.rounds,
                synthesize=not args.no_synthesize,
            )
            print(
                f"  ok submitted={row['submitted']} turns={row['turns_used']} "
                f"api={row['api_calls']} grade={row['grade_method'] or row['grade_reason']}",
                flush=True,
            )
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
        "rounds": args.rounds,
        "total": len(rows),
        "ok": sum(1 for r in rows if r.get("status") == "ok"),
        "errors": sum(1 for r in rows if r.get("status") == "error"),
        "submitted": sum(1 for r in rows if r.get("submitted")),
        "results": rows,
    }
    out_path = out_dir / "smoke_batch.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"  DONE: {summary['ok']}/{summary['total']} ok | {summary['submitted']} submitted")
    print(f"  Saved: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
