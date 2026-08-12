"""Per-competition time / API / token budgets.

Defaults use 50 turns everywhere until we calibrate per contest from real
wall-clock rules. Token caps are optional and off by default for smoke runs.
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ContestBudget:
    """Budget knobs for one competition run."""

    max_turns: int = 50
    max_api_calls: int | None = None
    max_output_tokens_per_call: int | None = None
    max_total_tokens: int | None = None


DEFAULT_CONTEST_BUDGET = ContestBudget(max_turns=50)

# Per-competition overrides — tune after baseline smoke runs.
COMPETITION_BUDGET_REGISTRY: dict[str, ContestBudget] = {
    "arml_local": ContestBudget(max_turns=50),
    "arml_national_team": ContestBudget(max_turns=50),
    "arml_national_power": ContestBudget(max_turns=50),
    "arml_power": ContestBudget(max_turns=50),
    "icpc": ContestBudget(max_turns=50, max_output_tokens_per_call=4096),
    "iiot": ContestBudget(max_turns=50, max_output_tokens_per_call=4096),
    "ieo_business_case": ContestBudget(max_turns=50),
    "iol_team": ContestBudget(max_turns=50),
    "ioaa_group": ContestBudget(max_turns=50),
    "ijso_practical": ContestBudget(max_turns=50),
    "wsc_writing": ContestBudget(max_turns=50),
    "jessup": ContestBudget(max_turns=50),
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
    overrides: dict[str, int | None] = {}
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
