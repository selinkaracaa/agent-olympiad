"""AgentWorld-style Causal Collaboration Effectiveness (CCE).

CCE builds a causal action graph by tracing backward from actions that directly
produce a successful outcome.  Each committed contestant action is one node,
including communication and rest actions.  Private model deliberation is not a
node because it is not an observable team action.

The original AgentWorld definition assigns CCE=0 to failed tasks.  For
partial-credit domains this module also reports ``causal_efficiency`` and
``utility_weighted_cce`` so useful partial progress is not discarded.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from llm import LLMRequest, RequestFn

_SUBMISSION_ACTIONS = {"submit", "submit_code", "submit_final", "submit_run"}
_EXCLUDED_AGENTS = {"coach", "contest_control", "contest control", "judge", "official"}


@dataclass(frozen=True)
class CCEAction:
    """One observable action node in the causal action graph."""

    action_id: int
    turn: int
    agent: str
    action: str
    description: str


@dataclass
class CCEResult:
    """CCE values and the auditable causal graph used to compute them."""

    cce: float
    causal_efficiency: float
    utility_weighted_cce: float
    task_utility: float
    contributing_count: int
    total_actions: int
    success_action_ids: list[int] = field(default_factory=list)
    contributing_action_ids: list[int] = field(default_factory=list)
    causal_edges: list[dict[str, int]] = field(default_factory=list)
    per_agent_contribution: dict[str, float] = field(default_factory=dict)
    actions: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    warnings: list[str] = field(default_factory=list)
    source: str = "AgentWorld_COLM_2026_CCE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _truncate(text: str, limit: int) -> str:
    text = text or ""
    return text if len(text) <= limit else text[: limit - 20] + "\n...[truncated]"


def _parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError(f"Could not parse CCE judge JSON: {raw[:200]}")
        value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("CCE judge must return a JSON object")
    return value


def normalize_actions(
    action_log: list[dict[str, Any]],
    *,
    agents: list[str] | None = None,
) -> list[CCEAction]:
    """Convert an environment action log into stable CCE graph nodes."""

    allowed = set(agents or [])
    nodes: list[CCEAction] = []
    for item in action_log:
        agent = str(item.get("agent") or item.get("sender") or "").strip()
        action = str(item.get("action") or item.get("kind") or "").strip()
        if not agent or not action or action in {"think", "private_think"}:
            continue
        if agent.lower() in _EXCLUDED_AGENTS:
            continue
        if allowed and agent not in allowed:
            continue
        try:
            turn = int(item.get("turn") or 0)
        except (TypeError, ValueError):
            turn = 0
        payload = str(
            item.get("payload")
            or item.get("content")
            or item.get("message")
            or item.get("result")
            or ""
        ).strip()
        nodes.append(
            CCEAction(
                action_id=len(nodes),
                turn=turn,
                agent=agent,
                action=action,
                description=_truncate(payload, 500),
            )
        )
    return nodes


def _format_actions(actions: list[CCEAction]) -> str:
    return "\n".join(
        f"[{item.action_id}] turn={item.turn} agent={item.agent} "
        f"action={item.action}: {item.description or '(empty)'}"
        for item in actions
    )


_IDENTIFY_SUCCESS_PROMPT = """You are identifying terminal success actions in a
multi-agent trajectory.

TASK:
{task}

TASK OUTCOME / VERIFIER RESULT:
{outcome}

ACTIONS:
{actions}

Return only the IDs of the final actions that directly achieved a verified
success criterion. Do not include prerequisites. If no criterion was achieved,
return an empty list.

JSON only:
{{"success_action_ids": [1, 2], "reasoning": "brief explanation"}}
"""


_TRACE_ROUND_PROMPT = """You are tracing an AgentWorld-style Causal Action Graph.
Use an inclusive but causal standard: an action contributes when it produced a
resource/result, moved work forward, supplied necessary information, corrected
an error, verified a decision, or coordinated an agent in a way that enabled a
downstream contributing action. Mere temporal precedence, repetition, and idle
actions are not causal.

TASK:
{task}

TASK OUTCOME / VERIFIER RESULT:
{outcome}

ALREADY IDENTIFIED DOWNSTREAM CONTRIBUTING ACTIONS:
{targets}

CANDIDATE ACTIONS FROM TURN {turn}:
{candidates}

For every contributing candidate, identify one or more downstream target IDs
that it enabled. Source IDs must come from CANDIDATE ACTIONS and target IDs must
come from DOWNSTREAM CONTRIBUTING ACTIONS. Return every candidate exactly once
through either `links` or `not_contributing_ids`.

JSON only:
{{
  "links": [{{"source_id": 1, "target_ids": [5]}}],
  "not_contributing_ids": [2]
}}
"""


def _empty_result(
    *,
    task_utility: float,
    actions: list[CCEAction],
    warning: str,
) -> CCEResult:
    agents = sorted({item.agent for item in actions})
    return CCEResult(
        cce=0.0,
        causal_efficiency=0.0,
        utility_weighted_cce=0.0,
        task_utility=task_utility,
        contributing_count=0,
        total_actions=len(actions),
        per_agent_contribution={agent: 0.0 for agent in agents},
        actions=[asdict(item) for item in actions],
        warnings=[warning],
    )


def score_cce(
    *,
    request_fn: RequestFn,
    task_text: str,
    action_log: list[dict[str, Any]],
    task_utility: float,
    task_outcome: str,
    agents: list[str] | None = None,
    trace_partial_credit: bool = False,
) -> CCEResult:
    """Construct a causal action graph and compute strict and partial CCE.

    ``cce`` follows AgentWorld exactly: incomplete tasks receive zero.
    ``causal_efficiency`` is ``|C|/|T|`` whenever any verified partial credit
    exists, while ``utility_weighted_cce`` multiplies it by normalized utility.
    """

    utility = max(0.0, min(1.0, float(task_utility)))
    actions = normalize_actions(action_log, agents=agents)
    if not actions:
        return _empty_result(
            task_utility=utility,
            actions=actions,
            warning="no_observable_actions",
        )
    if utility <= 0:
        return _empty_result(
            task_utility=utility,
            actions=actions,
            warning="no_verified_success_criteria",
        )
    if utility < 1.0 - 1e-12 and not trace_partial_credit:
        return _empty_result(
            task_utility=utility,
            actions=actions,
            warning="incomplete_task_strict_cce_zero",
        )

    model = ""
    warnings: list[str] = []
    submission_ids = [
        item.action_id for item in actions if item.action in _SUBMISSION_ACTIONS
    ]
    if submission_ids:
        success_ids = [submission_ids[-1]]
        warnings.append("terminal_submission_used_as_success_action")
    else:
        response = request_fn(
            LLMRequest(
                system_prompt=(
                    "You are a causal-graph evaluator. Return valid JSON only."
                ),
                user_prompt=_IDENTIFY_SUCCESS_PROMPT.format(
                    task=_truncate(task_text, 6000),
                    outcome=_truncate(task_outcome, 6000),
                    actions=_truncate(_format_actions(actions), 30000),
                ),
                purpose="cce_identify_success_actions",
            )
        )
        model = response.model
        payload = _parse_json_object(response.text)
        valid_ids = {item.action_id for item in actions}
        success_ids = sorted(
            {
                int(value)
                for value in payload.get("success_action_ids", [])
                if isinstance(value, (int, float, str))
                and str(value).lstrip("-").isdigit()
                and int(value) in valid_ids
            }
        )
    if not success_ids:
        return _empty_result(
            task_utility=utility,
            actions=actions,
            warning="no_success_actions_identified",
        )

    by_id = {item.action_id: item for item in actions}
    contributing = set(success_ids)
    edges: set[tuple[int, int]] = set()
    rounds = sorted({item.turn for item in actions}, reverse=True)

    for turn in rounds:
        candidates = [
            item
            for item in actions
            if item.turn == turn
            and item.action_id not in contributing
            and any(item.action_id < target for target in contributing)
        ]
        targets = [
            by_id[action_id]
            for action_id in sorted(contributing)
            if any(candidate.action_id < action_id for candidate in candidates)
        ]
        if not candidates or not targets:
            continue
        response = request_fn(
            LLMRequest(
                system_prompt=(
                    "You are a causal-graph evaluator making binary causal "
                    "judgments. Return valid JSON only."
                ),
                user_prompt=_TRACE_ROUND_PROMPT.format(
                    task=_truncate(task_text, 6000),
                    outcome=_truncate(task_outcome, 6000),
                    targets=_truncate(_format_actions(targets), 18000),
                    turn=turn,
                    candidates=_truncate(_format_actions(candidates), 18000),
                ),
                purpose="cce_trace_round",
            )
        )
        model = model or response.model
        payload = _parse_json_object(response.text)
        candidate_ids = {item.action_id for item in candidates}
        target_ids = {item.action_id for item in targets}
        for link in payload.get("links") or []:
            if not isinstance(link, dict):
                continue
            try:
                source_id = int(link.get("source_id"))
            except (TypeError, ValueError):
                continue
            if source_id not in candidate_ids:
                warnings.append("judge_returned_invalid_source_id")
                continue
            linked = False
            for raw_target in link.get("target_ids") or []:
                try:
                    target_id = int(raw_target)
                except (TypeError, ValueError):
                    continue
                if target_id in target_ids and source_id < target_id:
                    edges.add((source_id, target_id))
                    linked = True
            if linked:
                contributing.add(source_id)

    total = len(actions)
    causal_efficiency = len(contributing) / total
    per_agent: dict[str, float] = {}
    for agent in sorted({item.agent for item in actions}):
        own = [item.action_id for item in actions if item.agent == agent]
        per_agent[agent] = (
            sum(action_id in contributing for action_id in own) / len(own)
            if own
            else 0.0
        )

    complete = utility >= 1.0 - 1e-12
    if not complete:
        warnings.append("partial_success_strict_cce_zero")
    return CCEResult(
        cce=causal_efficiency if complete else 0.0,
        causal_efficiency=causal_efficiency,
        utility_weighted_cce=utility * causal_efficiency,
        task_utility=utility,
        contributing_count=len(contributing),
        total_actions=total,
        success_action_ids=success_ids,
        contributing_action_ids=sorted(contributing),
        causal_edges=[
            {"source_id": source, "target_id": target}
            for source, target in sorted(edges)
        ],
        per_agent_contribution=per_agent,
        actions=[asdict(item) for item in actions],
        model=model,
        warnings=list(dict.fromkeys(warnings)),
    )


__all__ = ["CCEAction", "CCEResult", "normalize_actions", "score_cce"]
