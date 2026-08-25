"""
Run ARML Local exam(s) through env + collaboration pipeline.

Usage:
  python3 src/run_exam.py
  python3 src/run_exam.py --all-schemas
  python3 src/run_exam.py --schema centralized --rounds 2

Requires PERPLEXITY_API_KEY.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collaboration import CollabConfig, run_collaboration, SCHEMAS
from env import OlympiadEnvironment
from llm import make_perplexity_caller

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO_ROOT, "results")

DEFAULT_PROBLEM = "arml_local_2009"
DEFAULT_COMPETITION = "arml_local"
AGENT_MODEL = "openai/gpt-5.4-mini"
JUDGE_MODEL = "anthropic/claude-sonnet-4-6"
ALL_SCHEMAS = list(SCHEMAS.keys())


def build_judge_prompt(problem: dict, final_answer: str) -> tuple[str, str]:
    gold = problem.get("gold_label", {})
    expected = gold.get("expected_answer") or "(not provided)"
    rubric = gold.get("grading_rubric") or ""
    max_pts = problem.get("total_points") or 40
    system = "You are an expert olympiad grader for team contest problems. Score fairly against the official solution."
    user = f"""=== PROBLEM ===
{problem["problem_description"]}

=== OFFICIAL SOLUTION ===
{expected}

=== GRADING NOTES ===
{rubric}

=== TEAM'S FINAL ANSWER ===
{final_answer}

=== SCORING ===
Compare the team's answer to the official solution. Award partial credit per sub-part (10 problems, 4 points each).
For each problem: state points earned and brief justification.
End with: TOTAL: X/{max_pts}"""
    return system, user


def extract_total_score(judge_feedback: str) -> str:
    for line in reversed(judge_feedback.splitlines()):
        if "TOTAL:" in line.upper():
            return line.strip()
    return "TOTAL: ?"


def run_judge(problem: dict, final_answer: str) -> tuple[str, str]:
    system, user = build_judge_prompt(problem, final_answer)
    for candidate in (JUDGE_MODEL, AGENT_MODEL):
        print(f"  Judge scoring with {candidate}...", flush=True)
        try:
            feedback = make_perplexity_caller(model=candidate)(system, user)
            return feedback, candidate
        except Exception as exc:
            print(f"    failed: {exc}")
    return "", JUDGE_MODEL


def run_one_schema(
    competition: str,
    problem_id: str,
    schema: str,
    rounds: int | None,
    agent_fn,
    batch_stamp: str,
    max_api_calls: int | None = None,
    max_output_tokens_per_call: int | None = None,
    max_total_tokens: int | None = None,
) -> dict:
    env = OlympiadEnvironment(
        competition,
        problem_id,
        max_turns=rounds,
        max_api_calls=max_api_calls,
        max_output_tokens_per_call=max_output_tokens_per_call,
        max_total_tokens=max_total_tokens,
    )
    meta = env.get_metadata()

    print("\n" + "=" * 60)
    print(f"  {problem_id} — {schema}")
    print("=" * 60)
    print(
        f"  Year: {meta.get('year')}  |  Team: {meta['team_size']}  |  "
        f"Turns: {env.max_turns}  |  Out/call: {env.max_output_tokens_per_call or '∞'}"
    )

    def progress(msg: str) -> None:
        print(f"  {msg}", flush=True)

    config = CollabConfig(
        max_turns=rounds,
        rounds=rounds,
        decentralized_events=rounds,
        max_api_calls=max_api_calls,
        max_output_tokens_per_call=max_output_tokens_per_call,
        max_total_tokens=max_total_tokens,
        synthesize=True,
        progress=progress,
    )

    result = run_collaboration(schema, env, agent_fn, config)
    parts = len(re.findall(r"(?:^|\n)\s*\d+\s*[\.\)]", result.get("final_answer", "")))

    print(f"\n  Submitted:    {result['submitted']} (by {result['submitted_by']})")
    print(f"  Turns used:   {result['turns_used']}/{result.get('max_turns', '?')}")
    print(f"  API calls:    {result.get('api_calls', '?')}")
    print(f"  Tokens used:  {result.get('tokens_used', '?')}")
    print(f"  Answer parts: {parts} numbered problems")
    print(f"  Chat msgs:    {result['chat_messages']}")

    judge_feedback = ""
    judge_model_used = JUDGE_MODEL
    if result["submitted"]:
        judge_feedback, judge_model_used = run_judge(env.problem_data, result["final_answer"])
        if judge_feedback:
            print(f"\n  {extract_total_score(judge_feedback)}")
            print("\n" + "-" * 60)
            print(judge_feedback)
            print("-" * 60)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, f"{problem_id}_{schema}_{batch_stamp}.json")
    payload = {
        **result,
        "agent_model": AGENT_MODEL,
        "judge_model": judge_model_used,
        "rounds": rounds,
        "max_turns": result.get("max_turns"),
        "api_calls": result.get("api_calls"),
        "max_api_calls": result.get("max_api_calls"),
        "tokens_used": result.get("tokens_used"),
        "max_total_tokens": result.get("max_total_tokens"),
        "max_output_tokens_per_call": result.get("max_output_tokens_per_call"),
        "numbered_parts": parts,
        "chat_history": env.chat_history,
        "action_log": env.action_log,
        "judge_feedback": judge_feedback,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\n  Saved → {out_path}")
    return payload


def main():
    parser = argparse.ArgumentParser(description="Run ARML Local exam")
    parser.add_argument("--problem", default=DEFAULT_PROBLEM)
    parser.add_argument("--competition", default=DEFAULT_COMPETITION)
    parser.add_argument("--schema", default="round_table", choices=ALL_SCHEMAS)
    parser.add_argument("--all-schemas", action="store_true", help="Run round_table, centralized, decentralized")
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Max collaboration turns (default: per-competition registry, usually 50)",
    )
    parser.add_argument("--max-api-calls", type=int, default=None, help="Optional API call budget")
    parser.add_argument(
        "--max-output-tokens-per-call",
        type=int,
        default=None,
        help="Cap model output tokens per agent call (e.g. 4096 for ICPC)",
    )
    parser.add_argument(
        "--max-total-tokens",
        type=int,
        default=None,
        help="Optional team-wide output token budget for the whole run",
    )
    args = parser.parse_args()

    if not os.environ.get("PERPLEXITY_API_KEY"):
        print("Error: set PERPLEXITY_API_KEY in your environment.")
        sys.exit(1)

    schemas = ALL_SCHEMAS if args.all_schemas else [args.schema]
    agent_fn = make_perplexity_caller(model=AGENT_MODEL)
    batch_stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    print("=" * 60)
    print(f"  ARML Local batch: {args.problem}")
    print("=" * 60)
    print(f"  Schemas:  {', '.join(schemas)}")
    print(f"  Agents:   {AGENT_MODEL}")
    print(f"  Judge:    {JUDGE_MODEL} (fallback {AGENT_MODEL})")

    summaries = []
    for schema in schemas:
        payload = run_one_schema(
            args.competition,
            args.problem,
            schema,
            args.rounds,
            agent_fn,
            batch_stamp,
            max_api_calls=args.max_api_calls,
            max_output_tokens_per_call=args.max_output_tokens_per_call,
            max_total_tokens=args.max_total_tokens,
        )
        summaries.append(payload)

    print("\n" + "=" * 60)
    print("  BATCH SUMMARY")
    print("=" * 60)
    for s in summaries:
        total = extract_total_score(s.get("judge_feedback", ""))
        print(
            f"  {s['schema']:<16} parts={s.get('numbered_parts', '?'):>2}  "
            f"turns={s['turns_used']:>2}  api={s.get('api_calls', '?'):>3}  {total}"
        )


if __name__ == "__main__":
    main()
