"""Phase B matrix: gold suite × schemas × model teams + MultiAgentBench CS.

Default schedule is **contest-first** (finish all model/schema combos on one
contest before moving on) so a meeting demo can prioritize ARML Local diversity
over GPT-only breadth.

Teams:
  gpt / claude / gemini  — homogeneous
  hetero                 — cycle GPT → Claude → Gemini across roster seats

Usage:
  export PERPLEXITY_API_KEY=pplx-...
  # Meeting slice: ARML Local × all models × all schemas
  python3 src/run_phase_b_matrix.py --live --competitions arml_local
  python3 src/run_phase_b_matrix.py --live --teams gpt,hetero --schemas single_agent,centralized
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
from env import OlympiadEnvironment, TEAM_SIZE_MATRIX
from llm import make_perplexity_caller, make_roster_caller, resolve_request_fn
from run_competition_batch import run_one
from run_phase_a import PHASE_A_CASES

# Mid-cost frontier models via Perplexity Agent API.
TEAM_MODELS: dict[str, str] = {
    "gpt": "openai/gpt-5.4-mini",
    "claude": "anthropic/claude-sonnet-4-6",
    "gemini": "google/gemini-3.5-flash",
}
HETERO_CYCLE = ["gpt", "claude", "gemini"]
DEFAULT_TEAMS = ["gpt", "claude", "gemini", "hetero"]
DEFAULT_SCHEMAS = [
    "single_agent",
    "centralized",
    "round_table",
    "decentralized",
    "open_table_coach",
]
JUDGE_MODEL = "openai/gpt-5.4-mini"


def agent_roster(schema: str, team_size: int) -> list[str]:
    if schema == "single_agent":
        return ["Solo"]
    if schema == "centralized":
        return ["Group_Leader", *[f"Agent_{i}" for i in range(2, team_size + 1)]]
    agents = [f"Agent_{i}" for i in range(1, team_size + 1)]
    if schema == "open_table_coach":
        return [*agents, "Coach"]
    return agents


def team_size_for(competition: str, problem_id: str) -> int:
    try:
        return OlympiadEnvironment(competition, problem_id).team_size
    except Exception:
        return TEAM_SIZE_MATRIX.get(competition, 3)


def models_for_team(
    team: str, schema: str, competition: str, problem_id: str
) -> dict[str, str]:
    agents = agent_roster(schema, team_size_for(competition, problem_id))
    if team == "hetero":
        cycle = [TEAM_MODELS[k] for k in HETERO_CYCLE]
        roster = {
            name: cycle[i % len(cycle)]
            for i, name in enumerate(agent for agent in agents if agent != "Coach")
        }
        if "Coach" in agents:
            roster["Coach"] = roster["Agent_1"]
        return roster
    model = TEAM_MODELS[team]
    return {name: model for name in agents}


def build_query_fn(team: str, schema: str, competition: str, problem_id: str):
    roster = models_for_team(team, schema, competition, problem_id)
    default = TEAM_MODELS.get(team, TEAM_MODELS["gpt"])
    if team == "hetero":
        default = TEAM_MODELS["gpt"]
    if len(set(roster.values())) == 1:
        return make_perplexity_caller(model=next(iter(roster.values()))), roster
    return make_roster_caller(roster, default_model=default), roster


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--teams",
        default=",".join(DEFAULT_TEAMS),
        help="Comma-separated: gpt,claude,gemini,hetero",
    )
    parser.add_argument(
        "--schemas",
        default=",".join(DEFAULT_SCHEMAS),
        help="Comma-separated collaboration schemas",
    )
    parser.add_argument(
        "--competitions",
        default=None,
        help="Comma-separated competition ids (default: full Phase A gold suite)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Override registry turns (omit for real contest budgets)",
    )
    parser.add_argument(
        "--judge-collab",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="MultiAgentBench CS after each run (default: on)",
    )
    parser.add_argument("--no-synthesize", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="Resume from an existing phase_b_matrix.json (skip completed cells)",
    )
    args = parser.parse_args()

    if args.live and not os.environ.get("PERPLEXITY_API_KEY"):
        raise SystemExit("Set PERPLEXITY_API_KEY for --live runs.")

    teams = [t.strip() for t in args.teams.split(",") if t.strip()]
    schemas = [s.strip() for s in args.schemas.split(",") if s.strip()]
    cases = list(PHASE_A_CASES)
    if args.competitions:
        wanted = {c.strip() for c in args.competitions.split(",") if c.strip()}
        cases = [(c, p) for c, p in cases if c in wanted]
        if not cases:
            raise SystemExit(f"No cases match --competitions {args.competitions}")
    for team in teams:
        if team not in TEAM_MODELS and team != "hetero":
            raise SystemExit(f"Unknown team {team}; choose from {list(TEAM_MODELS)} or hetero")
    for schema in schemas:
        if schema not in SCHEMAS:
            raise SystemExit(f"Unknown schema {schema}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = args.output or (REPO_ROOT / "results" / "phase_b" / timestamp)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase_b_matrix.json"

    rows: list[dict] = []
    done_keys: set[tuple[str, str, str, str]] = set()
    if args.resume and args.resume.exists():
        prior = json.loads(args.resume.read_text(encoding="utf-8"))
        rows = list(prior.get("results") or [])
        for r in rows:
            if r.get("status") == "ok":
                done_keys.add(
                    (r["team"], r["competition"], r["problem_id"], r["schema"])
                )
        out_path = args.resume
        out_dir = out_path.parent
        print(f"Resuming: {len(done_keys)} completed cells from {args.resume}")

    request_fn = (
        resolve_request_fn(provider="perplexity", model=JUDGE_MODEL) if args.live else None
    )

    total_cells = len(cases) * len(teams) * len(schemas)
    print(
        f"Phase B matrix: {len(cases)} contests × {len(teams)} teams × "
        f"{len(schemas)} schemas = {total_cells} cells | "
        f"order=contest→team→schema | "
        f"turns={args.max_turns or 'registry'} | "
        f"collab_CS={'on' if args.judge_collab and args.live else 'off'} | "
        f"mode={'live' if args.live else 'mock'}",
        flush=True,
    )
    print(f"Models: {TEAM_MODELS} | hetero cycles {HETERO_CYCLE}", flush=True)
    print(f"Output: {out_path}", flush=True)

    cell_i = 0
    # Contest-first: model diversity on one contest before breadth.
    for competition, problem_id in cases:
        for team in teams:
            for schema in schemas:
                cell_i += 1
                key = (team, competition, problem_id, schema)
                label = (
                    f"[{cell_i}/{total_cells}] {competition}/{problem_id} · "
                    f"{team} · {schema}"
                )
                if key in done_keys:
                    print(f"\n=== {label} (skip) ===", flush=True)
                    continue
                print(f"\n=== {label} ===", flush=True)

                def _progress(msg: str, _label=label) -> None:
                    print(f"  .. {_label}: {msg}", flush=True)

                try:
                    if not args.live:
                        raise SystemExit("Phase B matrix is live-only (needs API models).")
                    query_fn, roster = build_query_fn(
                        team, schema, competition, problem_id
                    )
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
                        progress=_progress,
                    )
                    row["team"] = team
                    row["agent_models"] = roster
                    row["model_label"] = (
                        "hetero:" + ",".join(HETERO_CYCLE)
                        if team == "hetero"
                        else TEAM_MODELS[team]
                    )
                    bits = [
                        f"turns={row['turns_used']}/{row['max_turns']}",
                        f"api={row['api_calls']}",
                        f"grade={row.get('grade_method')}",
                    ]
                    if row.get("grade_score") is not None:
                        bits.append(
                            f"task={row['grade_score']:g}/{row['grade_max_score']:g}"
                        )
                    if row.get("coordination_score") is not None:
                        bits.append(f"CS={row['coordination_score']:.2f}")
                    print("  ok " + " ".join(bits), flush=True)
                except Exception as exc:
                    row = {
                        "team": team,
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
                    "phase": "B",
                    "mode": "live" if args.live else "mock",
                    "schedule": "contest_first",
                    "teams": teams,
                    "team_models": TEAM_MODELS,
                    "hetero_cycle": HETERO_CYCLE,
                    "schemas": schemas,
                    "max_turns": args.max_turns,
                    "judge_collab": bool(args.judge_collab and args.live),
                    "cases": [
                        {"competition": c, "problem_id": p} for c, p in cases
                    ],
                    "total": len(rows),
                    "ok": sum(1 for r in rows if r.get("status") == "ok"),
                    "errors": sum(1 for r in rows if r.get("status") == "error"),
                    "with_coordination": sum(
                        1 for r in rows if r.get("coordination_score") is not None
                    ),
                    "results": rows,
                }
                out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "=" * 88)
    print(f"{'contest':22} {'team':8} {'schema':14} {'task':12} {'CS':6}")
    for r in rows:
        if r.get("status") != "ok":
            print(
                f"{r.get('competition','?'):22} {r.get('team','?'):8} "
                f"{r.get('schema','?'):14} ERROR"
            )
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
            f"{r['competition']:22} {r.get('team','?'):8} {r['schema']:14} "
            f"{task:12} {cs:6}"
        )
    print(f"Saved: {out_path}")
    print("=" * 88)


if __name__ == "__main__":
    main()
