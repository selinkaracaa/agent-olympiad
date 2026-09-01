"""Deterministic error taxonomy over normalized team transcripts.

Taxonomy occurrences are observable rule/lexical triggers, not claims about
semantic correctness. Each occurrence includes a stable code, severity,
evidence, and turn/agent when the source schema exposes them.
"""

from __future__ import annotations

import re
from typing import Any

from .team_metrics import TeamTranscript, adapt_transcript, compute_team_metrics

ERROR_CODES: dict[str, dict[str, str]] = {
    "COMM-1": {"name": "no-op", "severity": "warning"},
    "COMM-2": {"name": "echo/redundancy", "severity": "warning"},
    "COMM-3": {"name": "unanswered question", "severity": "warning"},
    "COMM-4": {"name": "information dropped", "severity": "warning"},
    "COMM-5": {"name": "malformed action", "severity": "error"},
    "STRAT-1": {"name": "premature submit", "severity": "error"},
    "STRAT-2": {"name": "budget underuse", "severity": "info"},
    "STRAT-3": {"name": "coverage gap", "severity": "error"},
    "STRAT-4": {"name": "duplicated effort", "severity": "warning"},
    "STRAT-5": {"name": "no verification", "severity": "warning"},
    "STRAT-6": {"name": "synthesis loss", "severity": "warning"},
    "STRAT-7": {"name": "leader bottleneck", "severity": "warning"},
    "STRAT-8": {"name": "tool-blind", "severity": "warning"},
}

_NOOP_RE = re.compile(r"^\s*(?:pass|skip|wait(?:ing)?|no contribution|nothing|done)\s*[.!]?\s*$", re.I)
_ERROR_RE = re.compile(
    r"(action error|parse error|malformed|invalid json|unrecognized action|operational error)",
    re.I,
)
_TOOL_ACTIONS = {
    "execute_code",
    "use_calculator",
    "web_search",
    "inspect_environment",
    "read_official_materials",
    "read_lab_equipment",
    "read_star_chart",
    "submit_run",
}


def _occurrence(
    code: str,
    evidence: str,
    *,
    turn: int | None = None,
    agent: str | None = None,
) -> dict[str, Any]:
    spec = ERROR_CODES[code]
    return {
        "code": code,
        "name": spec["name"],
        "severity": spec["severity"],
        "evidence": evidence[:500],
        "turn": turn,
        "agent": agent,
        "heuristic": "lexical_proxy" if code not in {"COMM-5"} else "structural_rule",
    }


def classify_errors(value: TeamTranscript | dict[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic, machine-readable taxonomy occurrences.

    Aggregate thresholds are intentionally conservative: redundancy and
    duplicated effort trigger at >=0.8 Jaccard, budget underuse below 0.25,
    synthesis loss below 0.5 retention, and leader bottleneck above 0.75.
    Empty transcripts do not produce aggregate strategy errors.
    """

    transcript = value if isinstance(value, TeamTranscript) else adapt_transcript(value)
    report = compute_team_metrics(transcript)
    communication = report["communication"]
    strategy = report["strategy"]
    occurrences: list[dict[str, Any]] = []

    for message in transcript.messages:
        if _NOOP_RE.match(message.text):
            occurrences.append(
                _occurrence("COMM-1", message.text, turn=message.turn, agent=message.agent)
            )
    for action in transcript.actions:
        if action.action in {"sleep", "noop"} or _NOOP_RE.match(action.payload):
            occurrences.append(
                _occurrence(
                    "COMM-1",
                    f"{action.action}: {action.payload}",
                    turn=action.turn,
                    agent=action.agent,
                )
            )
        if not action.action.strip() or _ERROR_RE.search(f"{action.payload} {action.result}"):
            occurrences.append(
                _occurrence(
                    "COMM-5",
                    f"{action.action or '<missing action>'}: {action.result}",
                    turn=action.turn,
                    agent=action.agent,
                )
            )

    if communication["redundancy"] >= 0.8:
        occurrences.append(
            _occurrence("COMM-2", f"redundancy={communication['redundancy']:.3f}")
        )
    if any("?" in message.text for message in transcript.messages) and communication[
        "question_answered_rate"
    ] < 1.0:
        occurrences.append(
            _occurrence(
                "COMM-3",
                f"question_answered_rate={communication['question_answered_rate']:.3f}",
            )
        )
    if any(action.action in _TOOL_ACTIONS and action.result.strip() for action in transcript.actions) and communication[
        "observation_use_rate"
    ] < 1.0:
        occurrences.append(
            _occurrence(
                "COMM-4",
                f"observation_use_rate={communication['observation_use_rate']:.3f}",
            )
        )

    has_activity = bool(transcript.messages or transcript.actions)
    if strategy["premature_submit"]:
        occurrences.append(
            _occurrence("STRAT-1", "submission preceded complete lexical coverage/verification")
        )
    if transcript.budget_limits and strategy["budget_utilization"] < 0.25:
        occurrences.append(
            _occurrence("STRAT-2", f"budget_utilization={strategy['budget_utilization']:.3f}")
        )
    if transcript.required_parts and strategy["numbered_part_coverage"] < 1.0:
        occurrences.append(
            _occurrence(
                "STRAT-3",
                f"numbered_part_coverage={strategy['numbered_part_coverage']:.3f}",
            )
        )
    if strategy["duplicated_effort"] >= 0.8:
        occurrences.append(
            _occurrence("STRAT-4", f"duplicated_effort={strategy['duplicated_effort']:.3f}")
        )
    if has_activity and strategy["verification_rate"] == 0.0:
        occurrences.append(_occurrence("STRAT-5", "verification_rate=0.000"))
    if transcript.final_answer.strip() and strategy["synthesis_fidelity"] < 0.5:
        occurrences.append(
            _occurrence(
                "STRAT-6",
                f"synthesis_fidelity={strategy['synthesis_fidelity']:.3f}",
            )
        )
    if len(transcript.agents) > 1 and strategy["leader_bottleneck"] > 0.75:
        occurrences.append(
            _occurrence("STRAT-7", f"leader_bottleneck={strategy['leader_bottleneck']:.3f}")
        )
    used_tools = {action.action for action in transcript.actions} & _TOOL_ACTIONS
    if has_activity and transcript.allowed_tools and not used_tools:
        occurrences.append(
            _occurrence(
                "STRAT-8",
                "available tools unused: " + ", ".join(sorted(transcript.allowed_tools)),
            )
        )
    return occurrences


__all__ = ["ERROR_CODES", "classify_errors"]
