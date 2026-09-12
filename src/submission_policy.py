"""Configurable submission rules for contest sessions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SubmissionPolicy:
    """Controls programming verdict lockout behavior."""

    consecutive_non_ac_limit: int = 3
    cooldown_turns: int = 2
    non_programming_mode: Literal["latest_valid", "final_sheet_lock"] = "latest_valid"

    def __post_init__(self) -> None:
        if self.consecutive_non_ac_limit < 1:
            raise ValueError("consecutive_non_ac_limit must be positive")
        if self.cooldown_turns < 0:
            raise ValueError("cooldown_turns cannot be negative")
        if self.non_programming_mode not in {"latest_valid", "final_sheet_lock"}:
            raise ValueError("unsupported non-programming submission mode")

    @staticmethod
    def is_accepted(verdict: str) -> bool:
        return verdict.upper() == "AC"

    def should_block(self, consecutive_non_ac: int) -> bool:
        return consecutive_non_ac >= self.consecutive_non_ac_limit
