"""Small, deterministic scheduling policy for the strategic contest runner."""

from __future__ import annotations

from dataclasses import dataclass

from contest_session import TaskState, TaskUnit


@dataclass(frozen=True)
class StrategicPolicy:
    stall_turns: int = 3

    def __post_init__(self) -> None:
        if self.stall_turns < 1:
            raise ValueError("stall_turns must be positive")

    def switch_reason(
        self,
        task: TaskUnit,
        *,
        current_turn: int,
        last_progress_turn: int,
    ) -> str | None:
        if task.state is TaskState.BLOCKED:
            return "three_consecutive_non_ac"
        if (
            task.state is not TaskState.SOLVED
            and current_turn - last_progress_turn >= self.stall_turns
        ):
            return "stalled_turns"
        return None

    @staticmethod
    def can_revisit(task: TaskUnit, *, current_turn: int) -> bool:
        return (
            not task.locked
            and task.state is TaskState.BLOCKED
            and current_turn >= (task.blocked_until_turn or 0)
        )
