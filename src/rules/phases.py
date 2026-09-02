"""Contest phase schedules from collaboration rule cards.

When ``simulation.phases`` is present and rules are enforced, actions are gated
by the active phase (e.g. IEO prep day vs slide-lock day).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContestPhase:
    phase_id: str
    label: str
    turn_start: int
    turn_end: int
    allowed_actions: frozenset[str] | None
    banned_actions: frozenset[str]
    allow_submit_final: bool
    prompt: str

    def contains_turn(self, turn: int) -> bool:
        return self.turn_start <= turn <= self.turn_end


class PhaseSchedule:
    def __init__(self, phases: list[ContestPhase]):
        if not phases:
            raise ValueError("PhaseSchedule requires at least one phase")
        self.phases = phases

    @classmethod
    def from_simulation(cls, simulation: dict[str, Any] | None) -> PhaseSchedule | None:
        if not simulation:
            return None
        raw_phases = simulation.get("phases")
        if not raw_phases:
            return None
        if not isinstance(raw_phases, list):
            raise ValueError("simulation.phases must be a list")
        phases: list[ContestPhase] = []
        for item in raw_phases:
            if not isinstance(item, dict):
                raise ValueError("Each simulation.phases entry must be an object")
            phase_id = str(item.get("id") or "").strip()
            label = str(item.get("label") or phase_id).strip()
            if not phase_id:
                raise ValueError("simulation.phases entry missing id")
            try:
                turn_start = int(item["turn_start"])
                turn_end = int(item["turn_end"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"simulation.phases[{phase_id!r}] needs integer turn_start/turn_end"
                ) from exc
            if turn_start <= 0 or turn_end < turn_start:
                raise ValueError(
                    f"simulation.phases[{phase_id!r}] has invalid turn range"
                )
            allowed_raw = item.get("allowed_actions")
            allowed = (
                frozenset(str(action) for action in allowed_raw)
                if allowed_raw is not None
                else None
            )
            banned_raw = item.get("banned_actions") or ()
            banned = frozenset(str(action) for action in banned_raw)
            allow_submit_final = bool(item.get("allow_submit_final", True))
            prompt = str(item.get("prompt") or "").strip()
            phases.append(
                ContestPhase(
                    phase_id=phase_id,
                    label=label,
                    turn_start=turn_start,
                    turn_end=turn_end,
                    allowed_actions=allowed,
                    banned_actions=banned,
                    allow_submit_final=allow_submit_final,
                    prompt=prompt,
                )
            )
        return cls(phases)

    def phase_at(self, turn: int) -> ContestPhase | None:
        if turn <= 0:
            return None
        for phase in self.phases:
            if phase.contains_turn(turn):
                return phase
        return None

    def validate_action(self, turn: int, action_type: str) -> str | None:
        phase = self.phase_at(turn)
        if phase is None:
            return None
        if action_type == "submit_final" and not phase.allow_submit_final:
            return (
                f"RULE VIOLATION: {phase.label} — submit_final is locked until "
                f"the slide-lock phase begins."
            )
        if action_type in phase.banned_actions:
            return (
                f"RULE VIOLATION: {phase.label} — action '{action_type}' is banned "
                f"during this phase."
            )
        if phase.allowed_actions is not None and action_type not in phase.allowed_actions:
            return (
                f"RULE VIOLATION: {phase.label} — action '{action_type}' is not "
                f"permitted during this phase."
            )
        return None

    def prompt_block(self, turn: int) -> str:
        phase = self.phase_at(turn)
        if phase is None:
            return ""
        lines = [
            "=== CURRENT CONTEST PHASE ===",
            f"Phase: {phase.label} (turns {phase.turn_start}-{phase.turn_end})",
        ]
        if phase.prompt:
            lines.append(phase.prompt)
        if not phase.allow_submit_final:
            lines.append("Final submission is locked in this phase.")
        return "\n".join(lines) + "\n"

    def phase_transition_message(self, turn: int, previous_turn: int) -> str | None:
        current = self.phase_at(turn)
        previous = self.phase_at(previous_turn) if previous_turn > 0 else None
        if current is None or current is previous:
            return None
        return (
            f"[Contest control] Entering phase: {current.label} "
            f"(turns {current.turn_start}-{current.turn_end})."
        )
