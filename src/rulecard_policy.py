"""Open Table Coach policy read from a competition rule card.

The ``otc`` baseline never hard-codes how the Coach behaves, how many private
think calls a contestant gets, how long a message may be, or how much memory
is projected. All of that lives in ``data/rules/<competition>/collaboration.json``
under ``simulation.open_table_coach`` plus the card's ``communication``,
``deliberation`` and ``agent_roles`` blocks. This module validates that block
once (the same guards the legacy ``--schema open_table_coach`` path used) and
exposes it as a typed object the contest engine can consult per turn.

Everything derived here is pure: no engine state, so it is trivially
checkpoint-safe and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from rules.models import RuleCard, RuleCardError
from tool_registry import DELIBERATION_ACTION_NAMES

# Rule-card action names -> contest-session typed actions. ``sleep`` is the
# legacy name of ``rest``; ``write_scratchpad`` was chat in the old stack and
# has no communication counterpart here (``work`` is an answer, not a message).
CARD_ACTION_ALIASES: Mapping[str, str] = {
    "sleep": "rest",
    "submit_final": "submit",
}
# Communication-budget accounting: every way a contestant can talk.
MESSAGE_ACTION_NAMES = frozenset({"speak", "direct_message", "share_note"})
# Machine actions the ICPC workstation lease guards.
WORKSTATION_ACTION_NAMES = frozenset({"execute_code", "submit_code"})

DEFAULT_REPAIR_BUDGET_AFTER_REJECTED_RUN = 2
DEFAULT_SILENT_WORK_TURNS = 2


class OpenTablePolicyError(ValueError):
    """The card cannot drive an open-table session."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OpenTablePolicyError(message)


@dataclass(frozen=True)
class DiscussionPolicy:
    report_after_work: bool = False
    silent_work_turn_requires_discussion: bool = False
    conflicts_require_targeted_speak: bool = False
    # Consecutive work-only turns tolerated before enforcement bites.
    silent_work_turns: int = DEFAULT_SILENT_WORK_TURNS


@dataclass(frozen=True)
class MemoryEntries:
    private_think_per_agent: int
    shared_work: int
    group_messages: int
    public_messages: int


@dataclass(frozen=True)
class OpenTablePolicy:
    """Validated ``simulation.open_table_coach`` plus the card blocks it leans on."""

    competition_id: str
    advice_scope: tuple[str, ...]
    opening_purpose: str
    # The only supported value is 0: one blind brief before the contest clock.
    brief_turn: int
    min_turns: int
    allowed_actions: frozenset[str]
    private_think_calls_per_turn: int
    max_chars_by_action: Mapping[str, int]
    memory_entries: MemoryEntries
    discussion: DiscussionPolicy
    communication: Mapping[str, Any]
    deliberation_mode: str
    min_challenges: int
    decision_maker: str
    submitters: frozenset[str]
    workstation_lease: bool
    run_judging_latency_turns: int
    repair_budget_after_rejected_run: int
    status: str = ""
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    # -- derived views -----------------------------------------------------

    @property
    def structured_deliberation(self) -> bool:
        return self.deliberation_mode == "structured"

    @property
    def communication_limited(self) -> bool:
        return self.communication.get("mode") == "limited"

    def may_submit(self, agent: str) -> bool:
        return agent in self.submitters

    def may_decide(self, agent: str) -> bool:
        if self.decision_maker == "submitter":
            return self.may_submit(agent)
        if self.decision_maker == "any":
            return True
        return agent == self.decision_maker

    def char_limit(self, action: str) -> int | None:
        """Card character cap for one contestant action, if the card sets one."""
        key = {
            "direct_message": "speak",
            "share_note": "speak",
            "propose": "work",
            "challenge": "speak",
            "provide_evidence": "work",
            "revise": "work",
            "decide": "speak",
        }.get(action, action)
        limit = self.max_chars_by_action.get(key)
        return int(limit) if limit else None

    def counted_message_actions(self) -> frozenset[str]:
        """Actions charged against the card's communication budget."""
        if not self.communication_limited:
            return frozenset()
        declared = {
            CARD_ACTION_ALIASES.get(str(name), str(name))
            for name in (self.communication.get("counted_actions") or ())
        }
        counted = set(MESSAGE_ACTION_NAMES)
        if "speak" not in declared and declared:
            counted = set()
        if self.structured_deliberation:
            counted |= DELIBERATION_ACTION_NAMES & (declared or DELIBERATION_ACTION_NAMES)
        return frozenset(counted)


def open_table_policy(
    card: RuleCard,
    *,
    team_size: int,
    programming: bool,
) -> OpenTablePolicy:
    """Validate and extract the open-table policy; raise if the card cannot run it."""
    raw = (card.simulation or {}).get("open_table_coach")
    _require(
        isinstance(raw, dict) and raw.get("enabled") is True,
        f"rule card for {card.competition_id!r} does not enable open_table_coach",
    )
    assert isinstance(raw, dict)
    for field_name, expected in {
        "may_submit": False,
        "allowed_tools": [],
        "counts_toward_shared_api_and_token_budget": True,
        "after_opening_access": False,
    }.items():
        _require(
            raw.get(field_name) == expected,
            f"unsafe open_table_coach policy: {field_name} must be {expected!r}",
        )
    precontest = raw.get("precontest_brief")
    opening = raw.get("opening_discussion")
    _require(
        isinstance(precontest, dict) and isinstance(opening, dict),
        "open_table_coach requires precontest_brief and opening_discussion",
    )
    assert isinstance(precontest, dict) and isinstance(opening, dict)
    brief_turn = precontest.get("turn")
    _require(
        brief_turn == 0
        and precontest.get("problem_access") is False
        and set(precontest.get("allowed_actions") or ()) == {"speak", "sleep"},
        "unsafe open_table_coach precontest_brief policy",
    )
    assert isinstance(brief_turn, int)
    _require(
        opening.get("enabled") is False
        and opening.get("problem_access") is False
        and opening.get("allowed_actions") == [],
        "unsafe open_table_coach opening_discussion policy",
    )
    advice_scope = precontest.get("advice_scope")
    _require(
        isinstance(advice_scope, list)
        and bool(advice_scope)
        and all(isinstance(item, str) and item.strip() for item in advice_scope),
        "precontest advice_scope must be a non-empty string list",
    )
    _require(raw.get("review_required") is True, "otc card requires independent review")
    _require(raw.get("action_surface") == "registry_bundles_v1", "otc card must declare registry action bundles")
    purpose = str(opening.get("purpose") or "").strip()
    _require(bool(purpose), "opening_discussion.purpose must be a non-empty string")

    turn_policy = raw.get("contestant_turn_policy")
    _require(isinstance(turn_policy, dict), "open_table_coach requires contestant_turn_policy")
    assert isinstance(turn_policy, dict)
    mode = turn_policy.get("mode")
    _require(
        mode == "private_deliberation_then_single_action",
        "otc baseline supports only private_deliberation_then_single_action",
    )
    allowed = {
        CARD_ACTION_ALIASES.get(str(name), str(name))
        for name in (turn_policy.get("allowed_actions") or ())
    }
    _require(
        {"work", "speak", "rest"}.issubset(allowed)
        and allowed.issubset({"work", "speak", "rest", "submit_code"}),
        "contestant allowed_actions must be work/speak/rest with optional submit_code",
    )
    _require(
        turn_policy.get("exactly_one_action") is True
        and turn_policy.get("final_submission") == "reviewed_answer_sheet",
        "unsafe contestant_turn_policy",
    )
    _require(
        "submit_code" not in allowed or programming,
        "submit_code is only allowed for programming contests",
    )
    _require(raw.get("protocol_version") == "otc_turn0_review_v1",
             "unsupported OTC protocol version")
    _require(raw.get("action_bundles") == [
        "common", "desk", "memory", "independent_review", "competition_tools",
        "deliberation_if_structured"], "unsupported OTC action bundles")
    private_calls = int(turn_policy.get("private_think_calls_per_turn", 0))
    _require(1 <= private_calls <= 2, "private_think_calls_per_turn must be 1 or 2")

    max_chars = turn_policy.get("max_chars_by_action")
    expected_limits = allowed | {"think"}
    _require(
        isinstance(max_chars, dict)
        and set(max_chars) == expected_limits
        and all(
            isinstance(max_chars[action], int) and max_chars[action] > 0
            for action in expected_limits
        ),
        "max_chars_by_action must give a positive integer for think and every allowed action",
    )
    assert isinstance(max_chars, dict)
    entries = turn_policy.get("memory_entries")
    _require(isinstance(entries, dict), "contestant_turn_policy.memory_entries is required")
    assert isinstance(entries, dict)
    for key in ("private_think_per_agent", "shared_work", "group_messages", "public_messages"):
        _require(
            isinstance(entries.get(key), int) and entries[key] > 0,
            f"memory_entries.{key} must be a positive integer",
        )
    discussion_raw = turn_policy.get("discussion_policy") or {}
    _require(isinstance(discussion_raw, dict), "discussion_policy must be an object")
    discussion = DiscussionPolicy(
        report_after_work=bool(discussion_raw.get("report_after_work")),
        silent_work_turn_requires_discussion=bool(
            discussion_raw.get("silent_work_turn_requires_discussion")
        ),
        conflicts_require_targeted_speak=bool(
            discussion_raw.get("conflicts_require_targeted_speak")
        ),
        silent_work_turns=int(
            discussion_raw.get("silent_work_turns") or DEFAULT_SILENT_WORK_TURNS
        ),
    )

    min_turns = int(raw.get("min_turns") or 0)
    _require(min_turns <= int(card.simulation.get("max_turns") or min_turns),
             "card min_turns exceeds max_turns")
    _require(min_turns >= 0, "min_turns must be non-negative")

    deliberation = dict(card.deliberation or {})
    deliberation_mode = str(deliberation.get("mode") or "unstructured")
    _require(
        deliberation_mode in {"structured", "unstructured"},
        f"unknown deliberation mode {deliberation_mode!r}",
    )
    min_challenges = int(deliberation.get("min_challenges") or 0)
    decision_maker = str(deliberation.get("decision_maker") or "submitter")

    roster = card.roster(team_size)
    submitters = frozenset(role.name for role in roster if role.may_submit)
    _require(bool(submitters), "at least one contestant must be allowed to submit")

    simulation = card.simulation or {}
    latency = int(simulation.get("run_judging_latency_turns") or 0)
    _require(latency >= 0, "run_judging_latency_turns must be non-negative")
    repair_budget = int(
        simulation.get("repair_budget_after_rejected_run")
        or DEFAULT_REPAIR_BUDGET_AFTER_REJECTED_RUN
    )
    _require(repair_budget >= 1, "repair_budget_after_rejected_run must be positive")

    return OpenTablePolicy(
        competition_id=card.competition_id,
        advice_scope=tuple(str(item).strip() for item in advice_scope),
        opening_purpose=purpose,
        brief_turn=brief_turn,
        min_turns=min_turns,
        allowed_actions=frozenset(allowed),
        private_think_calls_per_turn=private_calls,
        max_chars_by_action={str(k): int(v) for k, v in max_chars.items()},
        memory_entries=MemoryEntries(
            private_think_per_agent=int(entries["private_think_per_agent"]),
            shared_work=int(entries["shared_work"]),
            group_messages=int(entries["group_messages"]),
            public_messages=int(entries["public_messages"]),
        ),
        discussion=discussion,
        communication=dict(card.communication or {}),
        deliberation_mode=deliberation_mode,
        min_challenges=min_challenges,
        decision_maker=decision_maker,
        submitters=submitters,
        workstation_lease=simulation.get("exclusive_workstation_lease") == "enforced",
        run_judging_latency_turns=latency,
        repair_budget_after_rejected_run=repair_budget,
        status=str(raw.get("status") or ""),
        raw=dict(raw),
    )


def clip_text(text: str, limit: int | None) -> tuple[str, bool]:
    """Cut ``text`` to ``limit`` characters at a sentence/line boundary when possible."""
    if limit is None or len(text) <= limit:
        return text, False
    prefix = text[: max(0, limit - 1)].rstrip()
    cut = max(
        prefix.rfind("\n"),
        prefix.rfind(". "),
        prefix.rfind("。"),
    )
    if cut >= limit // 2:
        prefix = prefix[: cut + 1].rstrip()
    return (prefix + "…")[:limit], True


__all__ = [
    "CARD_ACTION_ALIASES",
    "DELIBERATION_ACTION_NAMES",
    "MESSAGE_ACTION_NAMES",
    "WORKSTATION_ACTION_NAMES",
    "DiscussionPolicy",
    "MemoryEntries",
    "OpenTablePolicy",
    "OpenTablePolicyError",
    "RuleCardError",
    "clip_text",
    "open_table_policy",
]
