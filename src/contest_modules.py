"""Resolved module selection, separate from roles and workflow policy."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from action_modules.contracts import ActionSpec

MODULE_VERSION = 3


@dataclass(frozen=True)
class ContestModules:
    """Common and competition interfaces are mandatory; assistance is opt-in."""

    memory: bool = False
    coach: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {
            "common": True,
            "memory": self.memory,
            "coach": self.coach,
            "task_specific": True,
        }

    def allows(self, module: str) -> bool:
        return self.as_dict().get(module, False)

    def select(self, actions: Iterable[ActionSpec]) -> set[ActionSpec]:
        return {spec for spec in actions if self.allows(spec.module)}
