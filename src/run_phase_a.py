"""Phase A: gold-verified contests × single_agent + 3 collaboration schemas.

Contests (verifiable graders):
  arml_local, arml_national_team, purple_comet, hmmt_guts, icpc

Usage:
  export PERPLEXITY_API_KEY=pplx-...
  python3 src/run_phase_a.py --live
  python3 src/run_phase_a.py --live --max-turns 8
  python3 src/run_phase_a.py --live --schemas single_agent,centralized
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

from collaboration import SCHEMAS
from run_competition_batch import run_one
from llm import make_perplexity_caller, resolve_query_fn, resolve_request_fn

DEFAULT_MODEL = "openai/gpt-5.4-mini"

PHASE_A_CASES: list[tuple[str, str]] = [
    ("arml_local", "arml_local_2009"),
    ("arml_national_team", "arml_national_team_2009"),
    ("purple_comet", "purple_comet_hs_2024"),
    ("hmmt_guts", "hmmt_guts_2024"),
    ("icpc", "icpc_wf_2012_bottles"),
]

DEFAULT_SCHEMAS = [
    "single_agent",
    "centralized",
    "round_table",
    "decentralized",
    "open_table_coach",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--schemas",
        default=",".join(DEFAULT_SCHEMAS),
        help="Comma-separated schemas",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Override duration-derived turns (default: registry)",
    )
    parser.add_argument("--no-synthesize", action="store_true")
    parser.add_argument(
        "--judge-collab",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also compute MultiAgentBench CS (default: on for --live)",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.live and not os.environ.get("PERPLEXITY_API_KEY"):
        raise SystemExit("Set PERPLEXITY_API_KEY for --live runs.")

    schemas = [s.strip() for s in args.schemas.split(",") if s.strip()]
    for schema in schemas:
        if schema not in SCHEMAS:
            raise SystemExit(f"Unknown schema {schema}; choose from {list(SCHEMAS)}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = args.output or (REPO_ROOT / "results" / "phase_a" / timestamp)
    out_dir.mkdir(parents=True, exist_ok=True)

    query_fn = (
        make_perplexity_caller(model=args.model)
        if args.live
        else resolve_query_fn(use_mock=True)
    )
    request_fn = (
        resolve_request_fn(provider="perplexity", model=args.model) if args.live else None
    )

    print(
        f"Phase A: {len(PHASE_A_CASES)} contests × {len(schemas)} schemas | "
        f"mode={'live' if args.live else 'mock'} | model={args.model if args.live else 'mock'} | "
        f"max_turns={args.max_turns or 'registry'}"
    )

    rows: list[dict] = []
    for competition, problem_id in PHASE_A_CASES:
        for schema in schemas:
            label = f"{competition}/{problem_id} [{schema}]"
            print(f"\n=== {label} ===", flush=True)
            try:
                row = run_one(
                    competition,
                    problem_id,
                    schema=schema,
                    query_fn=query_fn,
                    request_fn=request_fn,
                    rounds=args.max_turns,
                    synthesize=not args.no_synthesize,
                    judge_task=True,
                    judge_collab=bool(args.judge_collab and args.live),
                    out_dir=out_dir,
                )
                score = ""
                if row.get("grade_score") is not None and row.get("grade_max_score") is not None:
                    score = f" task={row['grade_score']:g}/{row['grade_max_score']:g}"
                cs = ""
                if row.get("coordination_score") is not None:
                    cs = f" CS={row['coordination_score']:.2f}"
                print(
                    f"  ok turns={row['turns_used']}/{row['max_turns']} "
                    f"api={row['api_calls']} grade={row['grade_method']}{score}{cs}",
                    flush=True,
                )
            except Exception as exc:
                row = {
                    "competition": competition,
                    "problem_id": problem_id,
                    "schema": schema,
                    "status": "error",
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
                print(f"  FAIL: {exc}", flush=True)
            rows.append(row)

    summary = {
        "timestamp": timestamp,
        "phase": "A",
        "mode": "live" if args.live else "mock",
        "model": args.model if args.live else "mock",
        "schemas": schemas,
        "max_turns": args.max_turns,
        "judge_collab": bool(args.judge_collab and args.live),
        "cases": [{"competition": c, "problem_id": p} for c, p in PHASE_A_CASES],
        "total": len(rows),
        "ok": sum(1 for r in rows if r.get("status") == "ok"),
        "errors": sum(1 for r in rows if r.get("status") == "error"),
        "with_coordination": sum(
            1 for r in rows if r.get("coordination_score") is not None
        ),
        "results": rows,
    }
    out_path = out_dir / "phase_a.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Compact score table
    print("\n" + "=" * 72)
    print(f"{'contest':22} {'schema':14} {'task':12} {'CS':6} {'method'}")
    for r in rows:
        if r.get("status") != "ok":
            print(f"{r.get('competition','?'):22} {r.get('schema','?'):14} ERROR {r.get('error')}")
            continue
        task = "—"
        if r.get("grade_score") is not None and r.get("grade_max_score") is not None:
            task = f"{r['grade_score']:g}/{r['grade_max_score']:g}"
        cs = (
            f"{r['coordination_score']:.2f}"
            if r.get("coordination_score") is not None
            else "—"
        )
        print(
            f"{r['competition']:22} {r['schema']:14} {task:12} {cs:6} {r.get('grade_method')}"
        )
    print(f"Saved: {out_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
