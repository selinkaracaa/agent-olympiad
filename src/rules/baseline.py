from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .loader import DEFAULT_RULES_ROOT, load_rule_card
from .models import RuleCard
from .views import agent_view, assert_agent_view_hides_eval


class RulesMode(str, Enum):
    OFF = "off"
    PROMPT_ONLY = "prompt_only"
    ENFORCED = "enforced"


class RuleCardResolutionError(LookupError):
    """Raised when a requested rule-aware baseline has no canonical card."""

    def __init__(self, competition_id: str, rules_root: Path):
        self.competition_id = competition_id
        self.rules_root = rules_root
        super().__init__(
            f"rules_baseline_unavailable: no canonical rule card for "
            f"{competition_id!r} under {rules_root}"
        )


def coerce_rules_mode(value: RulesMode | str) -> RulesMode:
    if isinstance(value, RulesMode):
        return value
    try:
        return RulesMode(value)
    except ValueError as exc:
        raise ValueError(
            f"Unknown rules_mode {value!r}; choose from "
            + ", ".join(mode.value for mode in RulesMode)
        ) from exc


def card_content_hash(card: RuleCard) -> str:
    canonical = json.dumps(
        card.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class RulesBaseline:
    mode: RulesMode
    competition_id: str
    available: bool
    card: RuleCard | None
    content_hash: str | None
    rules_root: Path

    @classmethod
    def resolve(
        cls,
        competition_id: str,
        *,
        mode: RulesMode | str = RulesMode.OFF,
        rules_root: Path | str | None = None,
        strict: bool = False,
    ) -> "RulesBaseline":
        resolved_mode = coerce_rules_mode(mode)
        root = Path(rules_root) if rules_root is not None else DEFAULT_RULES_ROOT
        if resolved_mode is RulesMode.OFF:
            return cls(resolved_mode, competition_id, True, None, None, root)
        card = load_rule_card(competition_id, rules_root=root)
        if card is None:
            if strict:
                raise RuleCardResolutionError(competition_id, root)
            return cls(resolved_mode, competition_id, False, None, None, root)
        visible = agent_view(card, team_size=card.team_size_default)
        assert_agent_view_hides_eval(visible)
        return cls(
            resolved_mode,
            competition_id,
            True,
            card,
            card_content_hash(card),
            root,
        )

    def capabilities(self) -> dict[str, str]:
        names = (
            "prompt_rules",
            "roster_roles",
            "communication_budgets",
            "submission_authority",
            "tool_allowlist",
            "private_notes",
            "structured_deliberation",
        )
        if not self.available:
            return {name: "unavailable" for name in names}
        if self.mode is RulesMode.OFF:
            return {name: "unavailable" for name in names}
        values = {name: "prompt_only" for name in names}
        if self.mode is RulesMode.ENFORCED:
            for name in names[2:]:
                values[name] = "enforced"
        return values

    def metadata(self) -> dict[str, Any]:
        card = self.card
        requested = self.mode is not RulesMode.OFF
        return {
            "rules_mode": self.mode.value,
            "rules_available": self.available if requested else None,
            "rules_coverage": (
                "not_requested"
                if not requested
                else "covered"
                if self.available
                else "missing_card"
            ),
            "rule_card_schema_version": card.schema_version if card else None,
            "rule_card_version": card.rule_id if card else None,
            "rule_card_competition_id": card.competition_id if card else self.competition_id,
            "rule_card_content_hash": self.content_hash,
            "rule_capabilities": self.capabilities(),
        }
