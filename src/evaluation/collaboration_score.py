"""MultiAgentBench-style coordination / collaboration score.

Adapted from Zhu et al., MultiAgentBench (arXiv:2503.01935):

  Communication Score (Cscore) ∈ {0,1..5}   (0 if no communication)
  Planning Score (Pscore)       ∈ {1..5}
  Coordination Score (CS)       = mean(Cscore, Pscore)

Prompts follow Appendix A.12 (Communication / Planning Evaluation).
We map olympiad chat + action logs into their aggregated communication /
planning fields so CS is a second signal beside task accuracy.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from llm import LLMRequest, RequestFn


def _truncate(text: str, limit: int = 12000) -> str:
    text = text or ""
    return text if len(text) <= limit else text[: limit - 20] + "\n...[truncated]"


def format_agent_profiles(agents: list[str], schema: str) -> str:
    if schema == "centralized" and "Group_Leader" in agents:
        lines = []
        for name in agents:
            role = "group leader / coordinator" if name == "Group_Leader" else "worker"
            lines.append(f"- {name}: {role}")
        return "\n".join(lines)
    if schema == "open_table_coach" and "Coach" in agents:
        return "\n".join(
            (
                "- Coach: pre-contest and opening-turn adviser; cannot use tools or submit"
                if name == "Coach"
                else f"- {name}: contestant; collaborates and may submit after Coach exits"
            )
            for name in agents
        )
    return "\n".join(
        f"- {name}: team member in `{schema}` collaboration protocol" for name in agents
    ) or "(no agents listed)"


def format_communications(chat_history: list[dict[str, Any]]) -> str:
    if not chat_history:
        return "(no communication)"
    lines = []
    for item in chat_history:
        speaker = (
            item.get("sender")
            or item.get("speaker")
            or item.get("agent")
            or "?"
        )
        content = str(
            item.get("message") or item.get("content") or item.get("payload") or ""
        ).strip()
        if content:
            lines.append(f"{speaker}: {content}")
    return _truncate("\n".join(lines) if lines else "(no communication)")


def format_planning(action_log: list[dict[str, Any]], chat_history: list[dict[str, Any]]) -> str:
    """Proxy for MultiAgentBench aggregated planning data from env logs."""
    chunks: list[str] = []
    for action in action_log[-80:]:
        agent = action.get("agent") or "?"
        kind = action.get("action") or "?"
        detail = str(action.get("payload") or action.get("content") or action.get("args") or "")[:400]
        chunks.append(f"[{agent}] {kind}: {detail}")
    if not chunks and chat_history:
        return format_communications(chat_history)
    return _truncate("\n".join(chunks) if chunks else "(no planning actions logged)")


COMMUNICATION_PROMPT = """Task: {task}

Agent Profiles:
{agent_profiles}

Social Relationship: teammates in an olympiad team contest ({schema} protocol)

Aggregated Task Results:
{task_results}

Aggregated Communication Data:
{communications}

[System] You are tasked with evaluating the quality of communication among
agents operating within a multiagent system. Evaluate whether agents made
effective decisions based on the provided task results and whether their
communication aligns with their agent profiles and social relationships.
Consider the following:
1. Effective Decision-Making: Did agents use task results to guide their
decisions effectively?
2. Clarity and Precision: Were communications clear and unambiguous?
3. Adherence to Social Relationships: Did communications reflect the expected
interactions based on the agents' social relationships?
4. Alignment with Agent Profiles: Were the messages consistent with the
defined agent profiles?
5. Overall Effectiveness: Did the communication facilitate task progress,
considering both cooperative and competitive aspects?

Scoring Criteria (Communication):
- 5 (Exceptional): Outstanding communication with clear, precise messages
fully aligned with agent profiles and social relationships.
- 4 (Very Good): Mostly effective communication with only minor lapses
and slight ambiguities.
- 3 (Adequate): Acceptable communication with moderate ambiguities or
inconsistencies.
- 2 (Poor): Frequent unclear or misaligned communications causing significant
miscommunication.
- 1 (Very Poor): Largely ineffective communication with confusing messages and
complete misalignment.

Please provide your answer in a JSON code block in the following format:
```json
{{
  "score": 5,
  "justification": "2-4 sentences"
}}
```
"""


PLANNING_PROMPT = """Agent Profiles:
{agent_profiles}

Aggregated Planning Data from All Iterations:
{planning}

[System] You are tasked with evaluating the effectiveness of the planning process in a multiagent
system. Evaluate whether the planning across all iterations demonstrates clear
role definitions, effective task assignments, and a rational workload distribution
that aligns with each agent's profile. Consider the following:
1. Clarity of Task Assignment: Were tasks assigned in a clear and unambiguous manner?
2. Definition of Roles: Were roles and responsibilities clearly defined in each iteration?
3. Workload Distribution: Was the distribution of tasks reasonable and aligned
with each agent's profile?
4. Effectiveness of Outcomes: Did the planning lead to successful progress in task
advancement across iterations?
5. Overall Strategic Coordination: Did the planning incorporate effective
cooperation and competition strategies?

Scoring Criteria (Planning):
- 5 (Exceptional Planning): Planning is exemplary; every iteration shows clear, well-structured task
assignments with roles perfectly defined and workloads optimally distributed.
- 4 (Very Good Planning): Planning is mostly effective with only minor ambiguities.
- 3 (Adequate Planning): Planning is acceptable but shows moderate ambiguities or inefficiencies.
- 2 (Poor Planning): Frequent ambiguities in task assignments and role definitions.
- 1 (Very Poor Planning): Planning was severely flawed; roles undefined, progress hindered.

Please provide your answer in a JSON code block in the following format:
```json
{{
  "score": 5,
  "justification": "2-4 sentences"
}}
```
"""


def _parse_score(raw: str) -> tuple[float, str]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            match = re.search(r'"?score"?\s*[:=]\s*([0-5](?:\.\d+)?)', raw, re.I)
            if not match:
                raise ValueError(f"Could not parse collaboration score JSON: {raw[:200]}")
            return float(match.group(1)), ""
        payload = json.loads(text[start : end + 1])
    score = float(payload["score"])
    if score < 0 or score > 5:
        raise ValueError(f"Score out of range: {score}")
    return score, str(payload.get("justification") or "")


@dataclass
class CoordinationScoreResult:
    """MultiAgentBench Coordination Score (aka Collaboration Score)."""

    communication_score: float
    planning_score: float
    coordination_score: float
    communication_justification: str = ""
    planning_justification: str = ""
    model: str = ""
    warnings: list[str] = field(default_factory=list)
    source: str = "multiagentbench_arXiv:2503.01935"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_coordination(
    *,
    request_fn: RequestFn,
    task_text: str,
    agents: list[str],
    schema: str,
    chat_history: list[dict[str, Any]],
    action_log: list[dict[str, Any]] | None = None,
    task_results: str = "",
) -> CoordinationScoreResult:
    """Compute CS = mean(Cscore, Pscore) à la MultiAgentBench."""
    action_log = action_log or []
    communications = format_communications(chat_history)
    profiles = format_agent_profiles(agents, schema)
    planning = format_planning(action_log, chat_history)
    warnings: list[str] = []
    model = ""

    if communications.strip() in {"", "(no communication)"}:
        cscore, c_just = 0.0, "No communication observed; Cscore=0 per MultiAgentBench."
        warnings.append("no_communication")
    else:
        c_resp = request_fn(
            LLMRequest(
                system_prompt=(
                    "You are an expert multi-agent collaboration evaluator. "
                    "Return JSON only."
                ),
                user_prompt=COMMUNICATION_PROMPT.format(
                    task=_truncate(task_text, 8000),
                    agent_profiles=profiles,
                    schema=schema,
                    task_results=_truncate(task_results or "(none)", 4000),
                    communications=communications,
                ),
                purpose="collaboration_communication_score",
            )
        )
        cscore, c_just = _parse_score(c_resp.text)
        model = c_resp.model

    p_resp = request_fn(
        LLMRequest(
            system_prompt=(
                "You are an expert multi-agent collaboration evaluator. "
                "Return JSON only."
            ),
            user_prompt=PLANNING_PROMPT.format(
                agent_profiles=profiles,
                planning=planning,
            ),
            purpose="collaboration_planning_score",
        )
    )
    pscore, p_just = _parse_score(p_resp.text)
    model = model or p_resp.model

    return CoordinationScoreResult(
        communication_score=cscore,
        planning_score=pscore,
        coordination_score=(cscore + pscore) / 2.0,
        communication_justification=c_just,
        planning_justification=p_just,
        model=model,
        warnings=warnings,
    )
