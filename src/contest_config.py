"""Canonical contest presets and validated runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Literal

from contest_manifest import ManifestTask
from rulecard_policy import OpenTablePolicy, open_table_policy
from rules.models import RuleCard

PROTOCOL_VERSION = "contest_session_v6"
QueryFn = Callable[[str, str], str]
TaskActionExecutor = Callable[[ManifestTask, str, dict[str, Any]], dict[str, Any]]
CheckpointCallback = Callable[[dict[str, Any], str], None]

# ``card``: the turn-0 Open Table Coach (one blind brief, then exit).
CoachMode = Literal["none", "leader", "card"]
# ``off``: the engine ignores rule cards (non-OTC baselines).
# ``prompt_only``: the card's agent view is shown, nothing is enforced.
# ``enforced``: the card's open_table_coach / communication / deliberation /
# roles / simulation blocks drive prompts *and* action gating.
RuleCardMode = Literal["off", "prompt_only", "enforced"]

# The centralized baseline's coordinator seat. It is an ordinary contestant
# with two extra powers: it writes the opening plan and it alone submits.
LEADER_AGENT = "Agent_1"


@dataclass(frozen=True)
class BaselineFeatures:
    """Orthogonal switches that together define one contest baseline.

    Every behavioural difference between baselines lives here; the engine
    never branches on the baseline's name.
    """

    coach: CoachMode
    review_workflow: bool
    memory_actions: bool
    desk_actions: bool
    private_channel: bool
    structured_context: bool
    submission_cooldown: bool
    mechanical_switch: bool
    leader_submits: bool
    rule_card: RuleCardMode = "off"

    @property
    def basic_open_table(self) -> bool:
        return self.coach == "card" and not self.review_workflow and not self.memory_actions


_NO_COACH = BaselineFeatures(
    coach="none",
    review_workflow=False,
    memory_actions=False,
    desk_actions=False,
    private_channel=False,
    structured_context=False,
    submission_cooldown=False,
    mechanical_switch=True,
    leader_submits=False,
)
BASELINES: dict[str, BaselineFeatures] = {
    "vallina_otc": BaselineFeatures(
        coach="card", review_workflow=False, memory_actions=False,
        desk_actions=True, private_channel=False, structured_context=False,
        submission_cooldown=False, mechanical_switch=False,
        leader_submits=False, rule_card="enforced",
    ),
    # Same environment as decentralized; team_size is pinned to 1.
    "single_agent": _NO_COACH,
    "decentralized": _NO_COACH,
    "centralized": BaselineFeatures(
        coach="leader",
        review_workflow=False,
        memory_actions=False,
        desk_actions=True,
        private_channel=True,
        structured_context=True,
        submission_cooldown=True,
        mechanical_switch=False,
        leader_submits=True,
    ),
    # The rule-card Open Table Coach: the competition's card decides the coach
    # stages, the private think call, action set, character limits, message
    # budget, deliberation protocol, submission roles, workstation lease,
    # judging latency and repair budget. Independent approval is mandatory;
    # there are no enforced Coach assignments or later Coach calls.
    "otc": BaselineFeatures(
        coach="card",
        review_workflow=True,
        memory_actions=True,
        desk_actions=True,
        private_channel=True,
        structured_context=True,
        submission_cooldown=False,
        mechanical_switch=False,
        leader_submits=False,
        rule_card="enforced",
    ),
}
# Old spellings resolve to the sole current OTC implementation, not old protocols.
BASELINE_ALIASES: dict[str, str] = {
    "OTC": "otc",
    "vanilla_otc": "vallina_otc",
    "Vallina OTC": "vallina_otc",
    "vanilla": "decentralized",
    "vanilla_team": "decentralized",
    "strategic": "otc",
    "strategic_team": "otc",
    "open_table_coach": "otc",
    "open_table_coach_memory": "otc",
}
BASELINE_NAMES: tuple[str, ...] = tuple(BASELINES)


def canonical_baseline(name: str) -> str:
    canonical = BASELINE_ALIASES.get(name, name)
    if canonical not in BASELINES:
        raise ValueError(
            f"unknown system_variant {name!r}; expected one of "
            f"{', '.join(BASELINE_NAMES)} or an alias "
            f"{', '.join(BASELINE_ALIASES)}"
        )
    return canonical


@dataclass(frozen=True)
class ContestRunConfig:
    system_variant: str
    team_size: int
    max_turns: int
    max_api_calls: int | None = None
    max_tokens: int | None = None
    max_simulated_minutes: float | None = None
    minutes_per_turn: float = 5.0
    consecutive_non_ac_limit: int = 3
    cooldown_turns: int = 2
    stall_turns: int = 3
    require_review: bool | None = None
    require_final_review: bool | None = None
    start_seat: int = 0
    rule_guidance: str = ""
    programming_deadline_submit: bool = False
    # Filled from ``BASELINES[system_variant]`` unless given explicitly
    # (ablations may override single switches).
    features: BaselineFeatures | None = None
    # The competition's rule card; required when ``features.rule_card != "off"``.
    rule_card: RuleCard | None = None
    # Derived from ``rule_card`` for ``coach == "card"``; never set by callers.
    otc_policy: OpenTablePolicy | None = field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if self.team_size < 1 or self.max_turns < 1:
            raise ValueError("team_size and max_turns must be positive")
        canonical = canonical_baseline(self.system_variant)
        object.__setattr__(self, "system_variant", canonical)
        if self.features is None:
            object.__setattr__(self, "features", BASELINES[canonical])
        if self.features.coach not in {"none", "leader", "card"}:
            raise ValueError("unsupported coach mode; use the rule-card OTC implementation")
        if canonical == "otc" and self.features.coach != "card":
            raise ValueError("otc requires the rule-card Coach; use another baseline for ablations")
        if self.require_review is not None:
            object.__setattr__(
                self, "features", replace(self.features, review_workflow=self.require_review)
            )
        if canonical == "single_agent" and self.team_size != 1:
            raise ValueError("single_agent requires team_size=1")
        if self.features.coach == "leader" and self.team_size < 2:
            raise ValueError("a leader baseline needs at least one worker seat")
        if self.minutes_per_turn < 0 or self.stall_turns < 1:
            raise ValueError("invalid scheduling limits")
        if self.features.rule_card != "off" and self.rule_card is None:
            raise ValueError(
                f"baseline {canonical!r} needs the competition's rule card "
                "(features.rule_card is not 'off')"
            )
        if self.features.coach == "card":
            if self.features.rule_card != "enforced" or self.rule_card is None:
                raise ValueError("coach='card' requires an enforced rule card")
            if not self.review_required and not self.features.basic_open_table:
                raise ValueError("otc requires independent review approval")
            if self.team_size < 2:
                raise ValueError("otc independent review requires at least two contestants")
            # ``programming`` is checked against the manifest by the engine.
            object.__setattr__(
                self,
                "otc_policy",
                open_table_policy(
                    self.rule_card, team_size=self.team_size, programming=True
                ),
            )
            if self.features.basic_open_table:
                from basic_otc import basic_policy
                object.__setattr__(self, "otc_policy", basic_policy(self.otc_policy))
        if canonical == "otc" and not self.review_required:
            raise ValueError("otc requires review; use vallina_otc for the basic baseline")
        if canonical == "vallina_otc" and (
            self.features != BASELINES[canonical] or self.require_review is True
            or self.require_final_review is True
        ):
            raise ValueError("vallina_otc is a fixed basic Coach + rule-card baseline")

    @property
    def review_required(self) -> bool:
        return (
            self.features.review_workflow
            if self.require_review is None
            else self.require_review
        )

    @property
    def final_review_required(self) -> bool:
        return (
            (self.review_required and self.features.coach != "card")
            if self.require_final_review is None
            else self.require_final_review
        )

    @property
    def leader(self) -> str | None:
        return LEADER_AGENT if self.features.coach == "leader" else None
