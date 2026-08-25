"""
Pipeline diagnostics for OlympiadEnvironment + collaboration schemas.

Usage:
  python3 src/main.py              # offline mock LLM
  python3 src/main.py --live       # requires PERPLEXITY_API_KEY
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collaboration import CollabConfig, run_centralized, run_decentralized, run_round_table
from env import OlympiadEnvironment, ProblemNotFoundError
from llm import resolve_query_fn


def _print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def _print_result(label: str, result: dict) -> None:
    print(f"\n[{label}]")
    print(f"  schema:       {result['schema']}")
    print(f"  submitted:    {result['submitted']} (by {result['submitted_by']})")
    print(f"  turns used:   {result['turns_used']}/{result.get('max_turns', '?')}")
    print(f"  api calls:    {result.get('api_calls', '?')}")
    print(f"  chat msgs:    {result['chat_messages']}")
    grade = result["grade"]
    print(f"  grade:        {json.dumps(grade, indent=2)}")


def test_environment_basics() -> None:
    _print_section("ENV: load problem + metadata")
    env = OlympiadEnvironment(competition_id="arml_local", problem_id="arml_local_2009")
    meta = env.get_metadata()
    print(f"  title:     {meta.get('title') or meta['problem_id']}")
    print(f"  team_size: {meta['team_size']}")
    print(f"  tools:     {meta['allowed_tools']}")
    print(f"  has_gold:  {meta['has_gold_answer']}")

    _print_section("ENV: tool gatekeeper (ARML = no calculator)")
    blocked = env.execute_action("Agent_1", "use_calculator", "2+2")
    print(f"  calculator attempt: {blocked}")

    calc = OlympiadEnvironment._safe_calculate("2 + 3 * 4")
    print(f"  safe_calculate (2+3*4): {calc}")

    _print_section("ENV: code execution (ICPC)")
    env_icpc = OlympiadEnvironment(
        competition_id="icpc",
        problem_id="icpc_wf_2012_bottles",
    )
    code_result = env_icpc.execute_action("Agent_1", "execute_code", "print(sum(range(10)))")
    print(f"  execute_code: {code_result}")

    _print_section("ENV: submission validation")
    env_icpc.reset()
    rejected = env_icpc.execute_action("Agent_1", "submit_final", "short")
    print(f"  short answer: {rejected}")
    accepted = env_icpc.execute_action("Agent_1", "submit_final", "Case 1: 263.89\n0.51 1.06 1.66")
    print(f"  valid answer: {accepted}")
    print(f"  grade: {json.dumps(env_icpc.grade_submission(), indent=2)}")


def test_collaboration_schemas(query_llm_fn) -> None:
    config = CollabConfig(rounds=1, decentralized_events=1, synthesize=True)

    _print_section("SCHEMA A: Round Table (ARML Local)")
    env_rt = OlympiadEnvironment(competition_id="arml_local", problem_id="arml_local_2009")
    result_rt = run_round_table(env_rt, query_llm_fn, config)
    _print_result("round_table", result_rt)

    _print_section("SCHEMA B: Centralized (ICPC)")
    env_c = OlympiadEnvironment(competition_id="icpc", problem_id="icpc_wf_2012_bottles")
    result_c = run_centralized(env_c, query_llm_fn, config)
    _print_result("centralized", result_c)
    if env_c.chat_history:
        print("  last chat:", env_c.chat_history[-1]["message"][:120])

    _print_section("SCHEMA C: Decentralized (ARML Local)")
    env_d = OlympiadEnvironment(competition_id="arml_local", problem_id="arml_local_2010")
    result_d = run_decentralized(env_d, query_llm_fn, config)
    _print_result("decentralized", result_d)


def test_error_handling() -> None:
    _print_section("ENV: error handling")
    try:
        OlympiadEnvironment(competition_id="icpc", problem_id="nonexistent_problem_id")
        print("  ERROR: should have raised ProblemNotFoundError")
    except ProblemNotFoundError as exc:
        print(f"  ProblemNotFoundError caught: {exc}")


def run_diagnostics(use_mock: bool = True) -> None:
    print("\n" + "=" * 60)
    print("       OLYMPIAD PIPELINE — ENV + COLLABORATION DIAGNOSTICS")
    print("=" * 60)
    print(f"  LLM mode: {'mock' if use_mock else 'live (Perplexity)'}")

    test_environment_basics()
    test_error_handling()

    query_llm_fn = resolve_query_fn(use_mock=use_mock)
    test_collaboration_schemas(query_llm_fn)

    print("\n" + "=" * 60)
    print("  SUCCESS: Environment + all 3 collaboration schemas verified")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Use Perplexity API instead of mock")
    args = parser.parse_args()
    run_diagnostics(use_mock=not args.live)
