"""
Show how ground-truth rule cards are injected into every agent.

Usage:
  python src/run_rulebased_demo.py
  python src/run_rulebased_demo.py --competition arml_local --problem arml_local_2009
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collaboration import CollabConfig, _system_prompt, run_round_table
from env import OlympiadEnvironment
from llm import mock_agent_llm


DEFAULTS = {
    "arml_local": "arml_local_2009",
    "purple_comet": "purple_comet_2005_hs",
    "science_bowl": "science_bowl_sample_set_10_10a_hs_reg_2016_bonus_13",
    "qanta": "qanta_train_52729",
    "wmtc": "wmtc_2018_advanced",
}


def _default_problem(competition: str) -> str:
    preset = DEFAULTS.get(competition)
    if preset:
        return preset
    env_probe = OlympiadEnvironment.__dict__  # keep import side effects local
    del env_probe
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "data" / "benchmarks" / competition / "benchmark.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("problems") or []
    if not items:
        raise SystemExit(f"No problems found for {competition}")
    return str(items[0]["problem_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--competition", default="arml_local")
    parser.add_argument("--problem", default="")
    parser.add_argument("--rounds", type=int, default=1)
    args = parser.parse_args()

    problem_id = args.problem or _default_problem(args.competition)
    env = OlympiadEnvironment(args.competition, problem_id)
    meta = env.get_metadata()
    rule = meta.get("rule")
    if not rule:
        raise SystemExit(
            f"{args.competition} has no rule card yet. "
            "Ground-truth cards currently cover arml_local, purple_comet, wmtc, qanta, science_bowl."
        )

    print("=" * 72)
    print(f"RULE-BASED DEMO  {args.competition} / {problem_id}")
    print("=" * 72)
    print(f"rule_id:     {rule['rule_id']}")
    print(f"profile:     {rule['profile']}")
    print(f"scoring:     {rule.get('scoring')}")
    print(f"team_size:   {meta['team_size']}")
    print(f"tools:       {meta['allowed_tools']}")
    print(f"has_gold:    {meta['has_gold_answer']}")
    print("\nHuman constraints:")
    for item in rule.get("human_constraints") or []:
        print(f"  - {item}")
    print("\nRoster:")
    for role in rule.get("agent_roles") or []:
        print(f"  - {role['name']}: {role['title']} (submit={role['may_submit']})")
        for duty in role.get("duties") or []:
            print(f"      * {duty}")

    sample_agent = (rule.get("agent_roles") or [{"name": "Agent_1"}])[0]["name"]
    print("\n" + "-" * 72)
    print(f"Sample system prompt for {sample_agent}:")
    print("-" * 72)
    print(_system_prompt(env, sample_agent))

    print("\n" + "-" * 72)
    print("Running mock round-table...")
    print("-" * 72)
    result = run_round_table(
        env,
        mock_agent_llm,
        CollabConfig(rounds=args.rounds, synthesize=True, progress=print),
    )
    print(json.dumps(
        {
            "submitted": result["submitted"],
            "submitted_by": result["submitted_by"],
            "turns_used": result["turns_used"],
            "grade": result["grade"],
            "final_answer_preview": (result["final_answer"] or "")[:240],
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
