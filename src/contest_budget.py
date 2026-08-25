"""Per-competition time / API / token budgets.

Turns approximate wall-clock using:
  max_turns ≈ ceil(duration_minutes / minutes_per_turn)

Default minutes_per_turn=5 (one collaboration round ≈ 5 contest minutes).
Override with explicit max_turns for smoke / ablation runs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ContestBudget:
    """Budget knobs for one competition run."""

    duration_minutes: int | None = None
    minutes_per_turn: float = 5.0
    max_turns: int = 50
    max_api_calls: int | None = None
    max_output_tokens_per_call: int | None = None
    max_total_tokens: int | None = None
    # ICPC-style: each turn advances simulated contest clock by this many minutes
    # (defaults to minutes_per_turn).
    clock_minutes_per_turn: float | None = None

    def simulated_minutes_for_turns(self, turns: int) -> float:
        step = self.clock_minutes_per_turn or self.minutes_per_turn
        return turns * step


def _turns_from_duration(duration_minutes: int, minutes_per_turn: float) -> int:
    if minutes_per_turn <= 0:
        return 50
    return max(1, int(math.ceil(duration_minutes / minutes_per_turn)))


def _budget(
    *,
    duration_minutes: int,
    minutes_per_turn: float = 5.0,
    max_api_calls: int | None = None,
    max_output_tokens_per_call: int | None = None,
    max_total_tokens: int | None = None,
) -> ContestBudget:
    return ContestBudget(
        duration_minutes=duration_minutes,
        minutes_per_turn=minutes_per_turn,
        max_turns=_turns_from_duration(duration_minutes, minutes_per_turn),
        max_api_calls=max_api_calls,
        max_output_tokens_per_call=max_output_tokens_per_call,
        max_total_tokens=max_total_tokens,
        clock_minutes_per_turn=minutes_per_turn,
    )


DEFAULT_CONTEST_BUDGET = ContestBudget(duration_minutes=60, max_turns=12)

# Durations from docs/DATA_COLLECTION.md (official contest clocks).
COMPETITION_BUDGET_REGISTRY: dict[str, ContestBudget] = {
    "arml_local": _budget(duration_minutes=60),  # ~1h team round → 12 turns
    "arml_national_team": _budget(duration_minutes=20),  # ~20 min → 4 turns
    "arml_national_power": _budget(duration_minutes=60),
    "arml_power": _budget(duration_minutes=60),
    "icpc": _budget(duration_minutes=300, max_output_tokens_per_call=4096),  # 5h → 60
    "iiot": _budget(duration_minutes=180, max_output_tokens_per_call=4096),  # 3h → 36
    "ieo_business_case": _budget(duration_minutes=24 * 60, minutes_per_turn=30),  # ~24h prep
    "iol_team": _budget(duration_minutes=240),  # 4h → 48
    "ioaa_group": _budget(duration_minutes=90),  # 90m → 18
    "ijso_practical": _budget(duration_minutes=180),
    "wsc_writing": _budget(duration_minutes=75, minutes_per_turn=5),  # 15 turns
    "jessup": _budget(duration_minutes=30 * 24 * 60, minutes_per_turn=120),  # long prep proxy
    "iypt": _budget(duration_minutes=12 * 60, minutes_per_turn=30),
    "hmmt_team": _budget(duration_minutes=60),
    "hmmt_guts": _budget(duration_minutes=80),
    "mcm": _budget(duration_minutes=99 * 60, minutes_per_turn=60),  # 99h → 99 turns
    "icm": _budget(duration_minutes=99 * 60, minutes_per_turn=60),
    "fyziklani": _budget(duration_minutes=180),
    "purple_comet": _budget(duration_minutes=90),  # HS 90m → 18
    "itym": _budget(duration_minutes=12 * 60, minutes_per_turn=30),
}


def resolve_contest_budget(
    competition_id: str,
    *,
    max_turns: int | None = None,
    max_api_calls: int | None = None,
    max_output_tokens_per_call: int | None = None,
    max_total_tokens: int | None = None,
) -> ContestBudget:
    """Merge registry defaults with explicit run-time overrides."""
    base = COMPETITION_BUDGET_REGISTRY.get(competition_id, DEFAULT_CONTEST_BUDGET)
    overrides: dict[str, int | float | None] = {}
    if max_turns is not None:
        overrides["max_turns"] = max_turns
    if max_api_calls is not None:
        overrides["max_api_calls"] = max_api_calls
    if max_output_tokens_per_call is not None:
        overrides["max_output_tokens_per_call"] = max_output_tokens_per_call
    if max_total_tokens is not None:
        overrides["max_total_tokens"] = max_total_tokens
    return replace(base, **overrides) if overrides else base


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token). Good enough for budget caps."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def truncate_to_token_budget(text: str, max_tokens: int) -> str:
    if max_tokens <= 0:
        return ""
    if estimate_tokens(text) <= max_tokens:
        return text

    suffix = "\n\n[truncated: output token budget reached]"
    suffix_tokens = estimate_tokens(suffix)
    body_budget = max_tokens - suffix_tokens
    if body_budget <= 0:
        return suffix[: max_tokens * 4]

    clipped = text[: body_budget * 4].rstrip()
    while clipped and estimate_tokens(clipped + suffix) > max_tokens:
        clipped = clipped[:-4]
    return (clipped + suffix) if clipped else suffix[: max_tokens * 4]
