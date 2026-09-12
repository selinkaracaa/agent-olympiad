"""Deterministic matched-pair smoke runs for contest-session plumbing."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from contest_adapters import grade_contest_result
from contest_manifest import ContestManifest, load_contest_manifest
from contest_runner import ContestRunConfig, run_contest
from llm import LLMRequest, LLMResponse, LLMToolCall
from rules.loader import load_rule_card
from run_competition_batch import _write_json_atomic

REPO_ROOT = Path(__file__).resolve().parent.parent


class DeterministicContestAgent:
    """Exercise only currently offered actions, without gold or hidden data."""

    def __init__(self, manifest: ContestManifest) -> None:
        self.manifest = manifest
        self.revisions: dict[str, int] = {}

    def __call__(self, request: LLMRequest) -> LLMResponse:
        offered = {tool["name"]: tool for tool in request.tools}
        status_match = re.search(r"TASK STATUS (.+?)\nBUDGET", request.user_prompt, re.DOTALL)
        status = json.loads(status_match.group(1)) if status_match else []
        active_match = re.search(r"ACTIVE TASK ([^\n]+)", request.user_prompt)
        active = active_match.group(1).strip() if active_match else None
        row = next((item for item in status if item["task_id"] == active), {})
        name, arguments = "rest", {"reason": "No pending action"}
        review_marker = "YOUR ELIGIBLE PENDING REVIEWS\n"
        pending = (json.JSONDecoder().raw_decode(request.user_prompt.split(review_marker)[1])[0]
                   if review_marker in request.user_prompt else [])
        if "review_answer" in offered and pending:
            candidate = pending[0]
            name, arguments = "review_answer", {
                "problem_id": candidate["problem_id"], "version_hash": candidate["version_hash"],
                "decision": "approve", "content": "Mock review of complete source and sample evidence.",
            }
        elif active and row.get("independent_approval") and "submit_code" in offered:
            name, arguments = "submit_code", {}
        elif active and row.get("state") == "candidate" and "speak" in offered and "review_answer" in offered:
            name, arguments = "speak", {"content": "Samples pass; please independently review."}
        elif active and row.get("state") == "candidate" and "submit_code" in offered:
            name, arguments = "submit_code", {"code": f"# {active}\nprint(0)"}
        elif "execute_code" in offered and active:
            self.revisions[active] = self.revisions.get(active, 0) + 1
            name, arguments = "execute_code", {"code": f"# {active} v{self.revisions[active]}\nprint(0)"}
        elif "work" in offered and active:
            name, arguments = "work", {"content": f"Mock candidate for {active}"}
        elif "select_problem" in offered:
            choices = offered["select_problem"]["parameters"]["properties"]["problem_id"].get("enum", [])
            if choices:
                name, arguments = "select_problem", {"problem_id": choices[0]}
        elif "speak" in offered:
            name, arguments = "speak", {"content": "Checking the current task."}
        # Frozen-source submission accepts no code in reviewed configurations.
        props = offered.get(name, {}).get("parameters", {}).get("properties", {})
        arguments = {key: value for key, value in arguments.items() if key in props}
        return LLMResponse("", "mock", "deterministic", tool_calls=(LLMToolCall(name, arguments),))


class MockProgrammingJudge:
    def __init__(self, first_task_id: str) -> None:
        self.first_task_id = first_task_id
        self.attempts: dict[str, int] = {}

    def __call__(
        self,
        task,
        action: str,
        _arguments: dict[str, Any],
    ) -> dict[str, Any]:
        if action == "execute_code":
            return {"valid": True, "sample_verdict": "AC", "result": "local sample evidence"}
        self.attempts[task.task_id] = self.attempts.get(task.task_id, 0) + 1
        attempt = self.attempts[task.task_id]
        verdict = "WA" if task.task_id == self.first_task_id else "AC"
        return {"valid": True, "verdict": verdict}


def run_pair(
    manifest: ContestManifest,
    *,
    max_turns: int,
    max_api_calls: int,
    max_tokens: int,
) -> dict[str, Any]:
    outputs = {}
    card = load_rule_card(manifest.competition_id)
    if card is None:
        raise ValueError(f"OTC requires a rule card for {manifest.competition_id}")
    team_size = card.team_size_default
    for variant in ("decentralized", "otc"):
        agent = DeterministicContestAgent(manifest)
        executor = (
            MockProgrammingJudge(manifest.tasks[0].task_id)
            if any(task.programming for task in manifest.tasks)
            else None
        )
        result = run_contest(
            manifest,
            lambda _system, _user: "Check the statement and coordinate next actions.",
            ContestRunConfig(
                system_variant=variant,
                rule_card=card if variant == "otc" else None,
                team_size=team_size,
                max_turns=max_turns,
                max_api_calls=max_api_calls,
                max_tokens=max_tokens,
                max_simulated_minutes=300,
                minutes_per_turn=0,
                start_seat=0,
            ),
            action_request_fn=agent,
            action_transport="native",
            coach_query_fn=lambda _system, _user: "{}",
            task_action_executor=executor,
        )
        result["grade"] = grade_contest_result(manifest, result)
        result["metrics"]["task_utility"] = result["grade"]["task_utility"]
        outputs[variant] = result
    return {
        "manifest": manifest.session_id,
        "matched_constraints": {
            "team_size": team_size,
            "max_turns": max_turns,
            "max_api_calls": max_api_calls,
            "max_tokens": max_tokens,
            "start_seat": 0,
            "action_sets": {name: result["action_names"] for name, result in outputs.items()},
        },
        "results": outputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "contest_matched_smoke",
    )
    args = parser.parse_args()
    root = REPO_ROOT / "data" / "benchmarks"
    manifests = {
        "arml": load_contest_manifest(
            REPO_ROOT / "data" / "contest_manifests" / "arml_local_2009.json",
            benchmark_root=root,
        ),
        "icpc": load_contest_manifest(
            REPO_ROOT / "data" / "contest_manifests" / "icpc_wf_2012_5.json",
            benchmark_root=root,
        ),
    }
    payload = {
        "protocol": "deterministic_mock_matched_pair_v2",
        "gold_visible_to_agent": False,
        "pairs": {
            "arml": run_pair(
                manifests["arml"],
                max_turns=12,
                max_api_calls=36,
                max_tokens=12000,
            ),
            "icpc": run_pair(
                manifests["icpc"],
                max_turns=18,
                max_api_calls=54,
                max_tokens=18000,
            ),
        },
    }
    args.output.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(args.output / "matched_pair.json", payload)
    print(f"Saved: {args.output / 'matched_pair.json'}")


if __name__ == "__main__":
    main()
