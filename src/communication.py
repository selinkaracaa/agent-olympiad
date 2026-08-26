from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_COUNTED_ACTIONS = {
    "speak",
    "write_scratchpad",
    "propose",
    "challenge",
    "provide_evidence",
    "revise",
    "decide",
}


@dataclass
class CommunicationBudget:
    policy: dict[str, Any]
    team_used: int = 0
    by_agent: dict[str, int] = field(default_factory=dict)
    rejected: list[dict[str, Any]] = field(default_factory=list)

    @property
    def enabled(self) -> bool:
        return self.policy.get("mode") == "limited"

    def is_counted(self, action_type: str) -> bool:
        actions = set(
            self.policy.get("counted_actions") or DEFAULT_COUNTED_ACTIONS
        )
        return self.enabled and action_type in actions

    def check(
        self, *, agent_name: str, action_type: str, payload: str, turn: int
    ) -> str | None:
        if not self.is_counted(action_type):
            return None

        max_chars = int(self.policy.get("max_message_chars", 0))
        if max_chars and len(payload) > max_chars:
            return self._reject(
                agent_name,
                action_type,
                turn,
                f"message has {len(payload)} characters; limit is {max_chars}",
            )

        team_budget = int(self.policy.get("team_message_budget", 0))
        if team_budget and self.team_used >= team_budget:
            return self._reject(
                agent_name,
                action_type,
                turn,
                f"team communication budget exhausted ({team_budget}/{team_budget})",
            )

        per_agent = int(self.policy.get("per_agent_message_budget", 0))
        agent_used = self.by_agent.get(agent_name, 0)
        if per_agent and agent_used >= per_agent:
            return self._reject(
                agent_name,
                action_type,
                turn,
                f"{agent_name} communication budget exhausted ({per_agent}/{per_agent})",
            )
        return None

    def record(self, *, agent_name: str, action_type: str) -> None:
        if not self.is_counted(action_type):
            return
        self.team_used += 1
        self.by_agent[agent_name] = self.by_agent.get(agent_name, 0) + 1

    def _reject(
        self, agent_name: str, action_type: str, turn: int, reason: str
    ) -> str:
        self.rejected.append(
            {
                "turn": turn,
                "agent": agent_name,
                "action": action_type,
                "reason": reason,
            }
        )
        return f"COMMUNICATION LIMIT: {reason}. Work privately or use a non-communication tool."

    def status_for(self, agent_name: str) -> str:
        if not self.enabled:
            return "unlimited"
        team_budget = int(self.policy["team_message_budget"])
        per_agent = int(self.policy["per_agent_message_budget"])
        return (
            f"team {self.team_used}/{team_budget} messages used; "
            f"you {self.by_agent.get(agent_name, 0)}/{per_agent} used"
        )

    def report(self) -> dict[str, Any]:
        if not self.enabled:
            return {"mode": "unlimited"}
        team_budget = int(self.policy["team_message_budget"])
        return {
            "mode": "limited",
            "team_used": self.team_used,
            "team_budget": team_budget,
            "team_remaining": max(0, team_budget - self.team_used),
            "per_agent_budget": int(self.policy["per_agent_message_budget"]),
            "by_agent": dict(self.by_agent),
            "rejected": list(self.rejected),
        }

    def reset(self) -> None:
        self.team_used = 0
        self.by_agent.clear()
        self.rejected.clear()
