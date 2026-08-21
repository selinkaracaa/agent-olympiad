"""Single resolver for agent-visible vs grader-visible rule views."""

from __future__ import annotations

from typing import Any

from .models import RuleCard
from .ownership import AGENT_VISIBLE_RULE_KEYS, HIDDEN_EVAL_KEYS


def _role_payload(role: Any, *, include_access: bool = False) -> dict[str, Any]:
    payload = {
        "name": role.name,
        "title": role.title,
        "duties": list(role.duties),
        "may_submit": role.may_submit,
    }
    if include_access:
        payload["information_access"] = list(role.information_access)
        payload["rule_expertise"] = list(role.rule_expertise)
    return payload


def public_deliverable(card: RuleCard) -> dict[str, Any]:
    """Contestant-facing answer contract. Adaptation and judge internals stay hidden."""
    deliverable = dict(card.deliverable)
    deliverable.setdefault("answer_format", card.answer_format)
    return deliverable


def agent_view(card: RuleCard, *, team_size: int | None = None) -> dict[str, Any]:
    """What an agent may see at start: official input plus collaboration method."""
    roster = card.roster(team_size) if team_size is not None else card.agent_roles
    return {
        "rule_id": card.rule_id,
        "competition_id": card.competition_id,
        "profile": card.profile,
        "protocol": card.protocol,
        "rules_text": card.rules_text,
        "human_constraints": list(card.human_constraints),
        "agent_constraints": list(card.agent_constraints),
        "answer_format": card.answer_format,
        "deliverable": public_deliverable(card),
        "resources": dict(card.resources),
        "allowed_tools": list(card.allowed_tools),
        "information_policy": dict(card.information_policy),
        "rule_sections": dict(card.rule_sections),
        "deliberation": dict(card.deliberation),
        "communication": dict(card.communication),
        "simulation": dict(card.simulation),
        "comparability": {
            key: card.comparability[key]
            for key in ("overall",)
            if key in card.comparability
        },
        "agent_roles": [_role_payload(role, include_access=True) for role in roster],
    }


def grader_view(card: RuleCard, *, team_size: int | None = None) -> dict[str, Any]:
    """Full card view for graders. Includes hidden evaluation configuration."""
    view = agent_view(card, team_size=team_size)
    view["evaluation_guidance"] = card.evaluation_guidance
    view["scoring"] = dict(card.scoring)
    view["submission"] = dict(card.submission)
    view["comparability"] = dict(card.comparability)
    return view


def assert_agent_view_hides_eval(view: dict[str, Any]) -> None:
    leaked = [key for key in HIDDEN_EVAL_KEYS if key in view]
    if leaked:
        raise ValueError("agent view leaked hidden evaluation keys: " + ", ".join(leaked))
    scoring_text = str(view).lower()
    for needle in ("rubric_path", "evaluator_id", "gold_label", "evaluation_guidance"):
        if needle in scoring_text:
            raise ValueError(f"agent view leaked {needle}")
    _ = AGENT_VISIBLE_RULE_KEYS
