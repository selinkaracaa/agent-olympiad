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


# --- Interaction-level helpfulness (second collab metric) ---
# Scores whether each chat/action helped the *final answer*, not global process quality.

INTERACTION_HELPFULNESS_PROMPT = """Task (summary):
{task}

Final submitted answer (truncated):
{final_answer}

Task outcome: {task_results}

Schema / protocol: {schema}

Agent profiles:
{agent_profiles}

Interactions (numbered). Each is a chat message or logged action during the run:
{interactions}

[System] You evaluate whether each interaction helped the team produce a *correct*
final answer for this contest. This is different from judging overall communication
style: focus on contribution to the submitted answers.

For EVERY numbered interaction, assign:
- "helpful" — clearly advanced a correct answer, fixed an error, or usefully divided work
- "neutral" — filler, repetition, unrelated tool use, or no clear effect on the final sheet
- "hurt" — pushed a wrong answer, wasted budget, or blocked progress toward a correct sheet

Then give an overall score from 0 to 5:
- 5: almost all substantive interactions helped the correct final answers
- 4: mostly helpful with few neutrals/hurts
- 3: mixed; some help, substantial noise
- 2: little help relative to volume; many neutrals or several hurts
- 1: collaboration mostly failed to aid the answer
- 0: no interactions, or interactions actively undermined the answer / empty submit

Return JSON only:
```json
{{
  "score": 3,
  "helpful": 4,
  "neutral": 6,
  "hurt": 2,
  "labels": ["helpful", "neutral", "hurt"],
  "justification": "2-4 sentences"
}}
```
`labels` must have one entry per numbered interaction, same order.
`helpful` / `neutral` / `hurt` must count those labels.
"""


@dataclass
class InteractionHelpfulnessResult:
    """Per-interaction collaboration metric tied to the final answer."""

    interaction_helpfulness_score: float
    helpful_count: int
    neutral_count: int
    hurt_count: int
    n_interactions: int
    helpful_fraction: float
    labels: list[str] = field(default_factory=list)
    justification: str = ""
    model: str = ""
    warnings: list[str] = field(default_factory=list)
    source: str = "interaction_helpfulness_v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def format_interactions(
    chat_history: list[dict[str, Any]],
    action_log: list[dict[str, Any]] | None = None,
    *,
    limit: int = 24,
) -> list[str]:
    """Build a short numbered list of chat + key actions for the judge."""
    items: list[str] = []
    for msg in chat_history or []:
        speaker = (
            msg.get("sender")
            or msg.get("speaker")
            or msg.get("agent")
            or "?"
        )
        content = str(
            msg.get("message") or msg.get("content") or msg.get("payload") or ""
        ).strip()
        if content:
            items.append(f"CHAT {speaker}: {content[:500]}")
    for action in action_log or []:
        kind = str(action.get("action") or "")
        if kind in {"speak", "sleep"}:
            continue
        agent = action.get("agent") or "?"
        detail = str(
            action.get("payload") or action.get("content") or action.get("args") or ""
        )[:300]
        items.append(f"ACTION {agent} {kind}: {detail}")
    if len(items) > limit:
        head = limit // 2
        tail = limit - head
        items = items[:head] + [f"...[{len(items) - limit} interactions omitted]..."] + items[-tail:]
    return items


def score_interaction_helpfulness(
    *,
    request_fn: RequestFn,
    task_text: str,
    agents: list[str],
    schema: str,
    chat_history: list[dict[str, Any]],
    action_log: list[dict[str, Any]] | None = None,
    final_answer: str = "",
    task_results: str = "",
) -> InteractionHelpfulnessResult:
    """Score whether interactions helped the final answer (0–5 + counts)."""
    action_log = action_log or []
    raw_items = format_interactions(chat_history, action_log)
    warnings: list[str] = []

    if not raw_items:
        return InteractionHelpfulnessResult(
            interaction_helpfulness_score=0.0,
            helpful_count=0,
            neutral_count=0,
            hurt_count=0,
            n_interactions=0,
            helpful_fraction=0.0,
            justification="No interactions logged; IHS=0.",
            warnings=["no_interactions"],
        )

    numbered = "\n".join(f"{i+1}. {line}" for i, line in enumerate(raw_items))
    profiles = format_agent_profiles(agents, schema)
    resp = request_fn(
        LLMRequest(
            system_prompt=(
                "You are an expert multi-agent collaboration evaluator. "
                "Judge each interaction by whether it helped the final answers. "
                "Return JSON only."
            ),
            user_prompt=INTERACTION_HELPFULNESS_PROMPT.format(
                task=_truncate(task_text, 6000),
                final_answer=_truncate(final_answer or "(empty)", 4000),
                task_results=_truncate(task_results or "(none)", 2000),
                schema=schema,
                agent_profiles=profiles,
                interactions=_truncate(numbered, 14000),
            ),
            purpose="collaboration_interaction_helpfulness",
        )
    )
    text = resp.text.strip()
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
            raise ValueError(f"Could not parse IHS JSON: {resp.text[:200]}")
        payload = json.loads(text[start : end + 1])

    score = float(payload["score"])
    if score < 0 or score > 5:
        raise ValueError(f"IHS out of range: {score}")

    labels = [str(x).lower().strip() for x in (payload.get("labels") or [])]
    # Prefer explicit counts; fall back to label tallies.
    helpful = int(payload.get("helpful") if payload.get("helpful") is not None else labels.count("helpful"))
    neutral = int(payload.get("neutral") if payload.get("neutral") is not None else labels.count("neutral"))
    hurt = int(payload.get("hurt") if payload.get("hurt") is not None else labels.count("hurt"))
    n = helpful + neutral + hurt
    if n == 0:
        n = len(raw_items)
        warnings.append("missing_counts")
    helpful_fraction = (helpful / n) if n else 0.0

    if abs(len(labels) - len(raw_items)) > 1 and "..." not in numbered:
        warnings.append("label_count_mismatch")

    return InteractionHelpfulnessResult(
        interaction_helpfulness_score=score,
        helpful_count=helpful,
        neutral_count=neutral,
        hurt_count=hurt,
        n_interactions=n,
        helpful_fraction=helpful_fraction,
        labels=labels,
        justification=str(payload.get("justification") or ""),
        model=resp.model,
        warnings=warnings,
    )
