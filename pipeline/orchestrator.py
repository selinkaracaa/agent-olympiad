from __future__ import annotations

from pathlib import Path
from typing import Any

from .leaderboard import Leaderboard
from .llm import QueryFn, RequestFn
from .models import CompetitionPacket, TeamMember
from .rule_block import RuleBlock, parse_actions
from .scorers import score_submission
from .team import form_team


def _history(runtime: RuleBlock) -> str:
    if not runtime.chat_history:
        return "(no team discussion yet)"
    return "\n".join(f"[{item['sender']}]: {item['message']}" for item in runtime.chat_history)


def _action_instructions(runtime: RuleBlock) -> str:
    actions = "\n".join(f"- {action}" for action in runtime.available_actions())
    return f"""Respond using one or more actions:
ACTION: <action> | PAYLOAD: <content>

Available actions:
{actions}

Use speak to advise peers, write_scratchpad for shared working notes, skip when you have no
useful contribution, and submit_final only for a complete answer."""


def _agent_prompt(
    packet: CompetitionPacket,
    runtime: RuleBlock,
    member: TeamMember,
    members: list[TeamMember],
    round_number: int,
    total_rounds: int,
) -> tuple[str, str]:
    roster = "\n".join(f"- {item.name}: {item.role}" for item in members)
    system = f"""You are {member.name}, role: {member.role}.
You are working in a human-like multi-agent competition team.
Competition: {packet.rules.display_name}
Rules: {packet.rules.rules_text}
{_action_instructions(runtime)}"""
    user = f"""TEAM ROSTER:
{roster}

PROBLEM:
{packet.problem.problem_description}

DISCUSSION:
{_history(runtime)}

SHARED SCRATCHPAD:
{runtime.scratchpad or "(empty)"}

This is round {round_number}/{total_rounds}. Make one substantive contribution."""
    return system, user


def _synthesize(
    packet: CompetitionPacket,
    runtime: RuleBlock,
    members: list[TeamMember],
    query_fn: QueryFn,
) -> None:
    synthesizer = members[0]
    system = (
        f"You are {synthesizer.name}, the team's official final answer synthesizer. "
        "Output only the complete answer, without ACTION wrappers."
    )
    user = f"""PROBLEM:
{packet.problem.problem_description}

TEAM DISCUSSION:
{_history(runtime)}

SHARED SCRATCHPAD:
{runtime.scratchpad or "(empty)"}

Write the official final answer. Preserve all requested sub-parts and include enough reasoning
for rubric-based grading."""
    answer = query_fn(system, user).strip()
    runtime.execute(synthesizer.name, "submit_final", answer)


def run_problem(
    packet: CompetitionPacket,
    query_fn: QueryFn,
    judge_request_fn: RequestFn,
    leaderboard: Leaderboard,
    *,
    rounds: int = 2,
    requested_team_size: int | None = None,
    allow_noncomparable_team_size: bool = False,
    media: str = "text",
    work_dir: Path,
) -> dict[str, Any]:
    team = form_team(
        packet.problem,
        packet.rules,
        requested_team_size,
        allow_noncomparable=allow_noncomparable_team_size,
    )
    members = list(team.members)
    runtime = RuleBlock(packet=packet, leaderboard=leaderboard)

    for round_number in range(1, rounds + 1):
        runtime.start_round(round_number)
        for member in members:
            if runtime.submitted:
                break
            system, user = _agent_prompt(
                packet, runtime, member, members, round_number, rounds
            )
            response = query_fn(system, user)
            for action, payload in parse_actions(response):
                runtime.execute(member.name, action, payload)
                if runtime.submitted:
                    break

    if not runtime.submitted:
        _synthesize(packet, runtime, members, query_fn)

    score = score_submission(
        packet.problem,
        runtime.final_answer,
        judge_request_fn,
        work_dir=work_dir,
        media=media,
    )
    leaderboard_snapshot = leaderboard.update(
        score.normalized_100,
        packet.problem_id,
        score_scale_id="normalized_100",
        evaluator_id=score.method,
        team_comparable=team.officially_comparable,
    )
    return {
        "competition_id": packet.competition_id,
        "problem_id": packet.problem_id,
        "team": team.to_dict(),
        "rounds": rounds,
        "submitted": runtime.submitted,
        "submitted_by": runtime.submitted_by,
        "final_answer": runtime.final_answer,
        "score": score.to_dict(),
        "leaderboard": leaderboard_snapshot,
        "chat_history": runtime.chat_history,
        "action_log": runtime.action_log,
        "rule_violations": sum(
            1 for item in runtime.action_log if str(item["result"]).startswith("RULE VIOLATION")
        ),
    }
