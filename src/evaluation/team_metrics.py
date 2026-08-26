"""Deterministic, lexical team-process metrics.

These metrics describe observable transcript structure, not semantic correctness.
Every content-sensitive metric is therefore named as a ``lexical_proxy`` in
``METRIC_DEFINITIONS``. Values are in [0, 1] unless explicitly noted, and empty
inputs return the documented neutral value instead of raising.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PART_RE = re.compile(
    r"\bpart\s*(\d+|[a-z])\b|(?:^|\s)(\d+|[a-z])[\).:]",
    re.IGNORECASE,
)
_VERIFY_RE = re.compile(
    r"\b(check(?:ed|ing)?|verif(?:y|ied|ication)|test(?:ed|ing)?|proof|confirm(?:ed)?)\b",
    re.IGNORECASE,
)
_DISAGREE_RE = re.compile(r"\b(disagree|but|however|challenge|objection|wrong)\b", re.IGNORECASE)
_RESOLVE_RE = re.compile(r"\b(resolve[sd]?|agree[sd]?|accept(?:ed)?|decid(?:e|ed)|consensus)\b", re.IGNORECASE)
_ERROR_RE = re.compile(
    r"(action error|parse error|malformed|invalid json|unrecognized action|operational error)",
    re.IGNORECASE,
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


@dataclass(frozen=True)
class Message:
    """One normalized public team message."""

    agent: str
    text: str
    turn: int | None = None
    kind: str = "speak"


@dataclass(frozen=True)
class Action:
    """One normalized action or tool event."""

    agent: str
    action: str
    payload: str = ""
    result: str = ""
    turn: int | None = None


@dataclass
class TeamTranscript:
    """Schema-independent transcript consumed by all deterministic metrics."""

    messages: list[Message] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    final_answer: str = ""
    required_parts: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    budget_used: dict[str, float] = field(default_factory=dict)
    budget_limits: dict[str, float] = field(default_factory=dict)
    rule_violations: list[Any] = field(default_factory=list)
    wrong_submissions: int = 0
    penalty_minutes: float | None = None
    source_schema: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "messages": [asdict(item) for item in self.messages],
            "actions": [asdict(item) for item in self.actions],
        }


METRIC_DEFINITIONS: dict[str, dict[str, Any]] = {
    "talk_share_gini": {
        "formula": "sum_i sum_j |words_i-words_j| / (2*n*sum_i words_i)",
        "range": [0, 1],
        "empty": 0.0,
    },
    "silence_rate": {
        "formula": "roster agents with zero public messages / roster size",
        "range": [0, 1],
        "empty": 0.0,
    },
    "redundancy": {
        "formula": "mean maximum token-bigram Jaccard versus earlier messages",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "lexical_proxy; similarity does not imply semantic duplication",
    },
    "addressed_rate": {
        "formula": "messages naming another roster agent / non-empty messages",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "lexical_proxy",
    },
    "question_answered_rate": {
        "formula": "questions with a later other-agent message sharing a content token / questions",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "lexical_proxy; topical follow-up is not proof of an answer",
    },
    "observation_use_rate": {
        "formula": "tool observations lexically reused later in public/final text / tool observations",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "lexical_proxy",
    },
    "parse_failure_rate": {
        "formula": "actions with parse/action-error markers / actions",
        "range": [0, 1],
        "empty": 0.0,
    },
    "numbered_part_coverage": {
        "formula": "required numbered parts mentioned in team/final text / required parts",
        "range": [0, 1],
        "empty": 1.0,
        "proxy": "lexical label coverage; not answer correctness",
    },
    "duplicated_effort": {
        "formula": "mean maximum token-bigram Jaccard against earlier other-agent messages",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "lexical_proxy",
    },
    "budget_utilization": {
        "formula": "mean min(used/limit, 1) over available positive limits",
        "range": [0, 1],
        "empty": 0.0,
    },
    "premature_submit": {
        "formula": "1 if first submit precedes any verification or complete part coverage, else 0",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "lexical verification/coverage proxy",
    },
    "verification_rate": {
        "formula": "messages/actions containing verification markers / messages/actions",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "lexical_proxy; mentions do not prove valid verification",
    },
    "answer_churn": {
        "formula": "changed consecutive answer/submission payloads / comparable transitions",
        "range": [0, 1],
        "empty": 0.0,
    },
    "unresolved_disagreement": {
        "formula": "disagreement events without a later resolution marker / disagreements",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "lexical_proxy",
    },
    "synthesis_fidelity": {
        "formula": "team-message content tokens present in final answer / team-message content tokens",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "lexical_proxy; retention is not correctness",
    },
    "leader_bottleneck": {
        "formula": "designated leader's public words / all public words",
        "range": [0, 1],
        "empty": 0.0,
        "proxy": "participation concentration proxy",
    },
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)


def _turn(item: dict[str, Any], fallback: int) -> int | None:
    raw = item.get("turn", fallback)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _message(item: Any, fallback: int, *, default_agent: str = "unknown") -> Message:
    if isinstance(item, str):
        return Message(default_agent, item, fallback)
    item = item if isinstance(item, dict) else {}
    return Message(
        agent=_text(item.get("sender") or item.get("agent") or item.get("speaker") or default_agent),
        text=_text(item.get("message") or item.get("content") or item.get("text") or item.get("utterance")),
        turn=_turn(item, fallback),
        kind=_text(item.get("kind") or item.get("action") or "speak"),
    )


def _action(item: Any, fallback: int) -> Action:
    item = item if isinstance(item, dict) else {}
    command = item.get("command") if isinstance(item.get("command"), dict) else {}
    return Action(
        agent=_text(item.get("agent") or item.get("sender") or item.get("actor") or "unknown"),
        action=_text(item.get("action") or command.get("action") or item.get("kind")),
        payload=_text(
            item.get("payload")
            or item.get("content")
            or command.get("content")
            or command.get("code")
        ),
        result=_text(item.get("result") or item.get("observation") or item.get("detail")),
        turn=_turn(item, fallback),
    )


def _parts(data: dict[str, Any]) -> list[str]:
    candidates = (
        data.get("required_parts")
        or (data.get("metadata") or {}).get("required_parts")
        or (data.get("task") or {}).get("required_parts")
        or []
    )
    if isinstance(candidates, int):
        return [str(index) for index in range(1, candidates + 1)]
    return [
        _text(item.get("id") if isinstance(item, dict) else item).strip().lower()
        for item in candidates
        if _text(item.get("id") if isinstance(item, dict) else item).strip()
    ]


def _adapt_icpcrun(data: dict[str, Any]) -> TeamTranscript:
    session = data.get("session") or {}
    messages = [
        _message(event, index)
        for index, event in enumerate(session.get("team_events") or [], start=1)
    ]
    actions = [
        _action(event, index)
        for index, event in enumerate(session.get("action_events") or [], start=1)
    ]
    scoreboard = session.get("scoreboard") or {}
    wrong = int(scoreboard.get("penalized_rejections") or 0)
    return TeamTranscript(
        messages=messages,
        actions=actions,
        agents=list((session.get("focus") or {}).keys()),
        final_answer=_text(data.get("final_answer")),
        required_parts=_parts(data),
        allowed_tools=["execute_code"],
        budget_used={"turns": float(len(actions))},
        budget_limits={"turns": float(data.get("max_turns") or 0)},
        rule_violations=list(data.get("rule_violations") or []),
        wrong_submissions=wrong,
        penalty_minutes=float(scoreboard.get("penalty") or 0),
        source_schema="icpcrun.v1",
    )


def adapt_transcript(data: dict[str, Any]) -> TeamTranscript:
    """Adapt env, legacy ARML/Science Bowl, or ``icpcrun.v1`` data.

    Adapters intentionally accept sparse artifacts. Unknown fields are ignored,
    and absent budgets/parts produce the metric-level safe defaults.
    """

    if data.get("schema_version") == "icpcrun.v1":
        return _adapt_icpcrun(data)

    source = "env.to_transcript"
    raw_messages = data.get("chat_history")
    if raw_messages is None and "discussion" in data:
        raw_messages = data.get("discussion")
        source = "science_bowl.discussion"
    elif "metadata" not in data:
        source = "legacy_arml"
    if isinstance(raw_messages, dict):
        raw_messages = [
            (
                {"speaker": speaker, "text": text}
                if not isinstance(text, dict)
                else {"speaker": speaker, **text}
            )
            for speaker, text in raw_messages.items()
        ]
    messages = [
        _message(item, index)
        for index, item in enumerate(raw_messages or [], start=1)
    ]
    raw_actions = data.get("action_log") or data.get("action_log_tail") or []
    actions = [_action(item, index) for index, item in enumerate(raw_actions, start=1)]
    metadata = data.get("metadata") or {}
    run = data.get("run") or {}
    budget = data.get("budget_turn_summary") or {}
    submission = data.get("submission") or {}
    roster = data.get("agents") or metadata.get("agents") or []
    if not roster:
        roster = list(dict.fromkeys(item.agent for item in [*messages, *actions] if item.agent))
    limits = {
        "turns": budget.get("max_turns", data.get("max_turns")),
        "api_calls": budget.get("max_api_calls"),
        "tokens": budget.get("max_total_tokens"),
        "minutes": budget.get("duration_minutes"),
    }
    used = {
        "turns": budget.get("turns_used", data.get("turns_used")),
        "api_calls": budget.get("api_calls"),
        "tokens": budget.get("tokens_used"),
        "minutes": budget.get("simulated_minutes"),
    }
    return TeamTranscript(
        messages=messages,
        actions=actions,
        agents=[_text(item) for item in roster],
        final_answer=_text(
            submission.get("final_answer")
            or data.get("final_answer")
            or (data.get("workspace") or {}).get("final_answer")
        ),
        required_parts=_parts(data),
        allowed_tools=list(metadata.get("allowed_tools") or data.get("allowed_tools") or []),
        budget_used={key: float(value) for key, value in used.items() if value is not None},
        budget_limits={key: float(value) for key, value in limits.items() if value is not None},
        rule_violations=list(data.get("rule_violations") or []),
        wrong_submissions=int(budget.get("wrong_submissions") or data.get("wrong_submissions") or 0),
        penalty_minutes=budget.get("penalty_minutes", data.get("penalty_minutes")),
        source_schema=source if not run.get("schema") else f"{source}:{run['schema']}",
    )


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _content_tokens(text: str) -> set[str]:
    return {token for token in _tokens(text) if len(token) >= 4}


def _ngrams(text: str, n: int = 2) -> set[tuple[str, ...]]:
    tokens = _tokens(text)
    if len(tokens) < n:
        return {(token,) for token in tokens}
    return {tuple(tokens[index : index + n]) for index in range(len(tokens) - n + 1)}


def _jaccard(left: set[Any], right: set[Any]) -> float:
    return len(left & right) / len(left | right) if left or right else 0.0


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _ordered_events(transcript: TeamTranscript) -> list[tuple[int, str, str, str]]:
    events = []
    for index, message in enumerate(transcript.messages):
        events.append((message.turn if message.turn is not None else index + 1, "message", message.agent, message.text))
    for index, action in enumerate(transcript.actions):
        text = f"{action.payload} {action.result}".strip()
        events.append((action.turn if action.turn is not None else index + 1, action.action, action.agent, text))
    return sorted(events, key=lambda item: item[0])


def compute_team_metrics(value: TeamTranscript | dict[str, Any]) -> dict[str, Any]:
    """Compute all deterministic metrics and carried contest counters."""

    transcript = value if isinstance(value, TeamTranscript) else adapt_transcript(value)
    messages = [item for item in transcript.messages if item.text.strip()]
    counts = Counter(item.agent for item in messages)
    word_counts = Counter()
    for item in messages:
        word_counts[item.agent] += len(_tokens(item.text))
    agents = list(dict.fromkeys([*transcript.agents, *word_counts.keys()]))
    total_words = sum(word_counts.values())
    n = len(agents)
    gini = (
        sum(abs(word_counts[a] - word_counts[b]) for a in agents for b in agents)
        / (2 * n * total_words)
        if n and total_words
        else 0.0
    )
    silence = sum(1 for agent in agents if counts[agent] == 0) / n if n else 0.0

    prior: list[tuple[str, set[tuple[str, ...]]]] = []
    redundancy_values: list[float] = []
    duplicate_values: list[float] = []
    for item in messages:
        grams = _ngrams(item.text)
        if prior:
            redundancy_values.append(max(_jaccard(grams, old) for _, old in prior))
        other = [old for agent, old in prior if agent != item.agent]
        if other:
            duplicate_values.append(max(_jaccard(grams, old) for old in other))
        prior.append((item.agent, grams))

    agent_names = [agent.lower() for agent in agents]
    addressed = 0
    for item in messages:
        lower = item.text.lower()
        addressed += int(
            any(name != item.agent.lower() and (f"@{name}" in lower or re.search(rf"\b{re.escape(name)}\b", lower)) for name in agent_names)
        )

    questions = [(index, item) for index, item in enumerate(messages) if "?" in item.text]
    answered = 0
    for index, question in questions:
        terms = _content_tokens(question.text)
        answered += int(
            any(
                later.agent != question.agent
                and bool(terms & _content_tokens(later.text))
                for later in messages[index + 1 :]
            )
        )

    observations = [
        action
        for action in transcript.actions
        if action.action in _TOOL_ACTIONS and action.result.strip() and not _ERROR_RE.search(action.result)
    ]
    used_observations = 0
    for observation in observations:
        later_public = " ".join(
            message.text
            for message in messages
            if observation.turn is None
            or message.turn is None
            or message.turn > observation.turn
        )
        later_public += " " + transcript.final_answer
        used_observations += int(
            bool(_content_tokens(observation.result) & _content_tokens(later_public))
        )
    parse_failures = sum(
        1
        for action in transcript.actions
        if not action.action.strip() or _ERROR_RE.search(f"{action.payload} {action.result}")
    )

    all_text = " ".join(item.text for item in messages) + " " + transcript.final_answer
    found_parts = {
        next(group for group in match.groups() if group).lower()
        for match in _PART_RE.finditer(all_text)
    }
    required = {part.lower().removeprefix("part ").strip(" .):") for part in transcript.required_parts}
    coverage = len(required & found_parts) / len(required) if required else 1.0

    ratios = [
        min(max(transcript.budget_used[key] / limit, 0.0), 1.0)
        for key, limit in transcript.budget_limits.items()
        if limit > 0 and key in transcript.budget_used
    ]
    event_texts = [text for _, _, _, text in _ordered_events(transcript)]
    verification_flags = [bool(_VERIFY_RE.search(text)) for text in event_texts if text.strip()]
    verification = _mean(float(flag) for flag in verification_flags)

    submissions = [
        action.payload.strip()
        for action in transcript.actions
        if action.action in {"submit_final", "submit", "answer", "revise_answer"} and action.payload.strip()
    ]
    if transcript.final_answer.strip() and (not submissions or submissions[-1] != transcript.final_answer.strip()):
        submissions.append(transcript.final_answer.strip())
    churn = (
        sum(left != right for left, right in zip(submissions, submissions[1:])) / (len(submissions) - 1)
        if len(submissions) > 1
        else 0.0
    )

    events = _ordered_events(transcript)
    submit_index = next(
        (index for index, (_, kind, _, _) in enumerate(events) if kind in {"submit", "submit_final", "submit_run"}),
        None,
    )
    verified_before_submit = submit_index is not None and any(
        _VERIFY_RE.search(text) for _, _, _, text in events[:submit_index]
    )
    premature = float(
        submit_index is not None and (not verified_before_submit or coverage < 1.0)
    )

    disagreements = [index for index, text in enumerate(event_texts) if _DISAGREE_RE.search(text)]
    unresolved = sum(
        1 for index in disagreements if not any(_RESOLVE_RE.search(text) for text in event_texts[index + 1 :])
    )
    unresolved_rate = unresolved / len(disagreements) if disagreements else 0.0

    team_terms = set().union(*(_content_tokens(item.text) for item in messages)) if messages else set()
    final_terms = _content_tokens(transcript.final_answer)
    fidelity = len(team_terms & final_terms) / len(team_terms) if team_terms else 0.0

    leader = next(
        (agent for agent in agents if "leader" in agent.lower() or "captain" in agent.lower()),
        None,
    )
    bottleneck = word_counts[leader] / total_words if leader and total_words else 0.0

    return {
        "source_schema": transcript.source_schema,
        "heuristic_notice": (
            "Content-sensitive values are deterministic lexical proxies and must not "
            "be interpreted as semantic correctness."
        ),
        "communication": {
            "talk_share_gini": gini,
            "silence_rate": silence,
            "redundancy": _mean(redundancy_values),
            "addressed_rate": addressed / len(messages) if messages else 0.0,
            "question_answered_rate": answered / len(questions) if questions else 0.0,
            "observation_use_rate": used_observations / len(observations) if observations else 0.0,
            "parse_failure_rate": parse_failures / len(transcript.actions) if transcript.actions else 0.0,
        },
        "strategy": {
            "numbered_part_coverage": coverage,
            "duplicated_effort": _mean(duplicate_values),
            "budget_utilization": _mean(ratios),
            "premature_submit": premature,
            "verification_rate": verification,
            "answer_churn": churn,
            "unresolved_disagreement": unresolved_rate,
            "synthesis_fidelity": fidelity,
            "leader_bottleneck": bottleneck,
        },
        "carried": {
            "rule_violations": transcript.rule_violations,
            "wrong_submissions": transcript.wrong_submissions,
            "penalty_minutes": transcript.penalty_minutes,
        },
        "definitions": METRIC_DEFINITIONS,
    }


__all__ = [
    "Action",
    "METRIC_DEFINITIONS",
    "Message",
    "TeamTranscript",
    "adapt_transcript",
    "compute_team_metrics",
]
