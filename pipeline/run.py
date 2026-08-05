from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .leaderboard import build_leaderboard
from .llm import (
    bind_problem_assets,
    make_request_caller,
    mock_query,
    mock_request,
)
from .loader import load_rules, select_problems
from .models import CompetitionPacket
from .orchestrator import run_problem

PIPELINE_ROOT = Path(__file__).resolve().parent
RESULTS_ROOT = PIPELINE_ROOT / "results"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a multi-agent competition dataset")
    parser.add_argument("--competition", default="iol_team")
    parser.add_argument("--problems", default="all", help="'all' or one problem_id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--team-size", type=int)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--provider", choices=["openai", "perplexity"], default="openai")
    parser.add_argument("--media", choices=["text", "pdf", "images", "both"], default="both")
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--codeforces-contest", type=int)
    parser.add_argument(
        "--allow-noncomparable-team-size",
        action="store_true",
        help="Allow an experimental team size that differs from the official benchmark.",
    )
    parser.add_argument(
        "--allow-missing-gold",
        action="store_true",
        help="Deprecated compatibility flag; evaluator metadata now controls eligibility.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.rounds < 1:
        raise ValueError("--rounds must be >= 1")

    rules = load_rules(args.competition)
    problems = select_problems(
        args.competition,
        args.problems,
        limit=args.limit,
    )
    if not problems:
        raise ValueError("No problems matched the selection")

    agent_request_fn = (
        mock_request
        if args.mock
        else make_request_caller(
            args.provider,
            args.model,
            base_url=args.base_url,
        )
    )
    judge_request_fn = (
        mock_request
        if args.mock
        else make_request_caller(
            args.provider,
            args.judge_model or args.model,
            base_url=args.base_url,
        )
    )
    leaderboard = build_leaderboard(rules, args.codeforces_contest)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RESULTS_ROOT / run_id
    results = []

    print(
        f"Running {len(problems)} {args.competition} problem(s), "
        f"model={'mock' if args.mock else args.model}, rounds={args.rounds}"
    )
    for index, problem in enumerate(problems, 1):
        packet = CompetitionPacket(args.competition, problem, rules)
        problem_dir = run_dir / packet.problem_id
        query_fn = (
            mock_query
            if args.mock
            else bind_problem_assets(
                agent_request_fn,
                packet.problem.assets,
                media=args.media,
                work_dir=problem_dir / "agent_inputs",
            )
        )
        print(f"[{index}/{len(problems)}] {packet.problem_id}", flush=True)
        result = run_problem(
            packet,
            query_fn,
            judge_request_fn,
            leaderboard,
            rounds=args.rounds,
            requested_team_size=args.team_size,
            allow_noncomparable_team_size=args.allow_noncomparable_team_size,
            media=args.media,
            work_dir=problem_dir,
        )
        results.append(result)
        _write_json(run_dir / f"{packet.problem_id}.json", result)
        rank = result["leaderboard"].get("rank")
        comparison = (
            f"rank={rank}/{result['leaderboard']['participants']}"
            if rank is not None
            else f"comparison={result['leaderboard']['comparison_status']}"
        )
        print(f"  score={result['score']['normalized_100']:.2f}/100 {comparison}")

    scores = [result["score"]["normalized_100"] for result in results]
    summary = {
        "run_id": run_id,
        "competition_id": args.competition,
        "model": "mock" if args.mock else args.model,
        "judge_model": "mock" if args.mock else (args.judge_model or args.model),
        "provider": "mock" if args.mock else args.provider,
        "media": args.media,
        "problem_count": len(results),
        "mean_score_100": round(statistics.fmean(scores), 4),
        "min_score_100": min(scores),
        "max_score_100": max(scores),
        "total_rule_violations": sum(item["rule_violations"] for item in results),
        "leaderboard_history": leaderboard.history,
        "result_files": [f"{item['problem_id']}.json" for item in results],
    }
    _write_json(run_dir / "summary.json", summary)
    print(f"Completed: mean={summary['mean_score_100']:.2f}/100; results={run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
