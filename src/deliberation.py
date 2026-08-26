from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DELIBERATION_ACTIONS = {
    "propose",
    "challenge",
    "provide_evidence",
    "revise",
    "decide",
}


def _targeted_payload(payload: str, parts: int = 2) -> list[str] | None:
    values = [value.strip() for value in payload.split("|", parts - 1)]
    if len(values) != parts or any(not value for value in values):
        return None
    return values


@dataclass
class DeliberationLedger:
    proposals: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(
        self,
        *,
        agent_name: str,
        action_type: str,
        payload: str,
        turn: int,
        may_decide: bool,
    ) -> str:
        if action_type == "propose":
            claim = payload.strip()
            if not claim:
                return "Deliberation error: propose requires a substantive claim."
            proposal_id = f"P{len(self.proposals) + 1}"
            proposal = {
                "proposal_id": proposal_id,
                "author": agent_name,
                "original_claim": claim,
                "current_claim": claim,
                "status": "open",
                "events": [],
            }
            self.proposals[proposal_id] = proposal
            self._append(proposal, turn, agent_name, action_type, claim)
            return f"{proposal_id} proposed by {agent_name}: {claim}"

        values = _targeted_payload(payload)
        if values is None:
            return (
                f"Deliberation error: {action_type} payload must be "
                "'P<number> | <content>'."
            )
        proposal_id, content = values
        proposal = self.proposals.get(proposal_id.upper())
        if proposal is None:
            return f"Deliberation error: unknown proposal {proposal_id!r}."
        if proposal["status"] != "open":
            return f"Deliberation error: {proposal['proposal_id']} is already decided."

        proposal_id = proposal["proposal_id"]
        if action_type == "challenge":
            if proposal["author"] == agent_name:
                return "Deliberation error: an author cannot challenge their own proposal."
        elif action_type == "revise":
            if proposal["author"] != agent_name:
                return "Deliberation error: only the proposal author may revise it."
            proposal["current_claim"] = content
        elif action_type == "decide":
            if not may_decide:
                return "Deliberation error: only a designated submitter may decide."
            decision = _targeted_payload(content)
            if decision is None:
                return (
                    "Deliberation error: decide payload must be "
                    "'P<number> | accept/reject/defer | reason'."
                )
            outcome, reason = decision
            outcome = outcome.lower()
            if outcome not in {"accept", "reject", "defer"}:
                return "Deliberation error: decision must be accept, reject, or defer."
            content = f"{outcome} | {reason}"
            proposal["status"] = "open" if outcome == "defer" else outcome
            proposal["decision_reason"] = reason
            proposal["decided_by"] = agent_name

        self._append(proposal, turn, agent_name, action_type, content)
        return f"{action_type} on {proposal_id} by {agent_name}: {content}"

    def _append(
        self,
        proposal: dict[str, Any],
        turn: int,
        agent_name: str,
        action_type: str,
        content: str,
    ) -> None:
        event = {
            "turn": turn,
            "proposal_id": proposal["proposal_id"],
            "agent": agent_name,
            "action": action_type,
            "content": content,
        }
        proposal["events"].append(event)
        self.events.append(event)

    def report(self) -> dict[str, Any]:
        counts = {
            action: sum(event["action"] == action for event in self.events)
            for action in sorted(DELIBERATION_ACTIONS)
        }
        decisions_after_evidence = 0
        evidence_led_revisions = 0
        for proposal in self.proposals.values():
            actions = [event["action"] for event in proposal["events"]]
            if "decide" in actions and "provide_evidence" in actions:
                decisions_after_evidence += 1
            if "revise" in actions and "provide_evidence" in actions:
                first_evidence = actions.index("provide_evidence")
                if "revise" in actions[first_evidence + 1 :]:
                    evidence_led_revisions += 1
        return {
            "counts": counts,
            "decisions_after_evidence": decisions_after_evidence,
            "evidence_led_revisions": evidence_led_revisions,
            "open_proposals": [
                proposal_id
                for proposal_id, proposal in self.proposals.items()
                if proposal["status"] == "open"
            ],
            "proposals": list(self.proposals.values()),
            "events": list(self.events),
        }

    def reset(self) -> None:
        self.proposals.clear()
        self.events.clear()
