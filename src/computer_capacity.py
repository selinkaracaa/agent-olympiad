"""Opt-in per-turn computer slots shared by the two contest runtimes.

This is an execution-count limit, separate from the existing workstation
lease. None preserves the current contest protocol. Resource events contain
no source code or tool output and survive session checkpoint restoration.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from contest_memory import ContestMemory

COMPUTER_ACTIONS = frozenset({"use_calculator", "execute_code"})
COMPUTER_USE_EVENT = "computer_capacity_used"


def validate_computer_capacity(capacity: int | None) -> None:
    if capacity is not None and (type(capacity) is not int or capacity < 1):
        raise ValueError("computer_capacity must be a positive integer or None")


def parse_computer_capacity(value: str) -> int:
    capacity = int(value)
    validate_computer_capacity(capacity)
    return capacity


def computer_capacity_state(capacity: int | None, used: int = 0) -> dict[str, Any]:
    if capacity is None:
        return {}
    return {
        "computer_capacity_mode": "per_turn",
        "computer_capacity": capacity,
        "computers_used_this_turn": used,
        "computers_available_this_turn": max(0, capacity - used),
    }


def require_computer_slot(capacity: int | None, used: int) -> None:
    if capacity is not None and used >= capacity:
        raise ValueError(
            f"Resource error: all {capacity} computer slot(s) are occupied "
            "this turn; try again next turn."
        )


def session_computer_state(
    memory: ContestMemory, turn: int, capacity: int | None,
) -> dict[str, Any]:
    if capacity is None:
        return {}
    used = sum(
        1 for event in memory.archival_snapshot()["events"]
        if event["kind"] == COMPUTER_USE_EVENT and event["turn"] == turn
    )
    return computer_capacity_state(capacity, used)

