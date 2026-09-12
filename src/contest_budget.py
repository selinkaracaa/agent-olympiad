"""Per-competition time / API / token budgets.

The turn budget is derived from the official contest clock: one turn stands
for ``minutes_per_turn`` (5 min by default) of contest time, so ARML Local
(45 minutes) is 9 turns and a 5-hour ICPC is 60 turns. The result is clamped to
``[1, MAX_TURNS_CAP]`` (90) so multi-day events do not run unbounded.
An explicit ``max_turns`` override still wins.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

MAX_TURNS_CAP = 90
DEFAULT_MINUTES_PER_TURN = 5.0


def turns_for_duration(
    duration_minutes: int | float | None,
    minutes_per_turn: float = DEFAULT_MINUTES_PER_TURN,
    *,
    cap: int = MAX_TURNS_CAP,
) -> int:
    """Convert an official contest duration into a turn budget.

    ``duration / minutes_per_turn`` rounded to the nearest whole turn, then
    clamped to ``[1, cap]``. ``None`` or a non-positive step falls back to
    the cap.
    """
    if duration_minutes is None or minutes_per_turn <= 0:
        return cap
    turns = int(round(duration_minutes / minutes_per_turn))
    return max(1, min(cap, turns))


@dataclass(frozen=True)
class ContestBudget:
    """Budget knobs for one competition run."""

    duration_minutes: int | None = None
    minutes_per_turn: float = DEFAULT_MINUTES_PER_TURN
    max_turns: int = MAX_TURNS_CAP
    max_api_calls: int | None = None
    max_output_tokens_per_call: int | None = None
    max_total_tokens: int | None = None
    # ICPC-style: each turn advances simulated contest clock by this many minutes
    # (defaults to minutes_per_turn).
    clock_minutes_per_turn: float | None = None

    def simulated_minutes_for_turns(self, turns: int) -> float:
        step = self.clock_minutes_per_turn or self.minutes_per_turn
        return turns * step


def _budget(
    *,
    duration_minutes: int,
    minutes_per_turn: float = DEFAULT_MINUTES_PER_TURN,
    max_api_calls: int | None = None,
    max_output_tokens_per_call: int | None = None,
    max_total_tokens: int | None = None,
) -> ContestBudget:
    return ContestBudget(
        duration_minutes=duration_minutes,
        minutes_per_turn=minutes_per_turn,
        max_turns=turns_for_duration(duration_minutes, minutes_per_turn),
        max_api_calls=max_api_calls,
        max_output_tokens_per_call=max_output_tokens_per_call,
        max_total_tokens=max_total_tokens,
        clock_minutes_per_turn=minutes_per_turn,
    )


# Competitions without a registry entry are treated as a 1-hour round.
DEFAULT_CONTEST_BUDGET = _budget(duration_minutes=60)  # → 12 turns

# Durations from docs/DATA_COLLECTION.md (official contest clocks).
# Turn counts in the comments assume the default 5 min/turn unless a
# different minutes_per_turn is given; everything is capped at 90.
COMPETITION_BUDGET_REGISTRY: dict[str, ContestBudget] = {
    "arml_local": _budget(duration_minutes=45),  # rule card: 45 min → 9 turns
    "arml_national_team": _budget(duration_minutes=20),  # 20 min → 4 turns
    "arml_national_power": _budget(duration_minutes=60),  # → 12
    "arml_power": _budget(duration_minutes=60),  # → 12
    "icpc": _budget(duration_minutes=300, max_output_tokens_per_call=4096),  # 5h → 60
    "iiot": _budget(duration_minutes=180, max_output_tokens_per_call=4096),  # 3h → 36
    "ieo_business_case": _budget(duration_minutes=24 * 60, minutes_per_turn=30),  # 24h/30 → 48
    "iol_team": _budget(duration_minutes=240),  # 4h → 48
    "ioaa_group": _budget(duration_minutes=90),  # 90m → 18
    "ijso_practical": _budget(duration_minutes=180),  # → 36
    "wsc_writing": _budget(duration_minutes=75),  # → 15
    "jessup": _budget(duration_minutes=30 * 24 * 60, minutes_per_turn=120),  # 360 → cap 90
    "iypt": _budget(duration_minutes=12 * 60, minutes_per_turn=30),  # → 24
    "hmmt_team": _budget(duration_minutes=60),  # → 12
    "hmmt_guts": _budget(duration_minutes=80),  # → 16
    "mcm": _budget(duration_minutes=99 * 60, minutes_per_turn=60),  # 99 → cap 90
    "icm": _budget(duration_minutes=99 * 60, minutes_per_turn=60),  # 99 → cap 90
    "fyziklani": _budget(duration_minutes=180),  # → 36
    "purple_comet": _budget(duration_minutes=90),  # HS 90m → 18
    "itym": _budget(duration_minutes=12 * 60, minutes_per_turn=30),  # → 24
}


def resolve_contest_budget(
    competition_id: str,
    *,
    max_turns: int | None = None,
    max_api_calls: int | None = None,
    max_output_tokens_per_call: int | None = None,
    max_total_tokens: int | None = None,
) -> ContestBudget:
    """Merge registry defaults with explicit run-time overrides.

    ``max_turns`` defaults to the duration-derived value and an explicit
    override is still clamped to ``[1, MAX_TURNS_CAP]``.
    """
    base = COMPETITION_BUDGET_REGISTRY.get(competition_id, DEFAULT_CONTEST_BUDGET)
    overrides: dict[str, int | float | None] = {}
    if max_turns is not None:
        overrides["max_turns"] = max(1, min(MAX_TURNS_CAP, int(max_turns)))
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
