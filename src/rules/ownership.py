"""Explicit field ownership for the three rule-card files.

Competition owns official/public contest facts. Collaboration owns the
benchmark method, including simulation. Evaluation owns hidden judge state.
"""

from __future__ import annotations

# Runner/method fields that must not live in competition.execution.
SIMULATION_OWNED_KEYS = frozenset(
    {
        "max_turns",
        "scheduler",
        "draft",
        "turn_budget_basis",
        "exclusive_workstation_lease",
        "run_judging_latency_turns",
        "run_judging_latency_basis",
        "pending_run_policy",
    }
)

AGENT_VISIBLE_RULE_KEYS = (
    "rule_id",
    "competition_id",
    "profile",
    "protocol",
    "rules_text",
    "human_constraints",
    "agent_constraints",
    "answer_format",
    "deliverable",
    "resources",
    "allowed_tools",
    "information_policy",
    "rule_sections",
    "deliberation",
    "communication",
    "simulation",
)

HIDDEN_EVAL_KEYS = (
    "evaluation_guidance",
    "scoring",
    "submission",
)
