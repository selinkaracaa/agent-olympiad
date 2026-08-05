from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass, field
from collections.abc import Callable
from typing import Any

from .loader import query_rules
from .models import CompetitionPacket

ACTION_RE = re.compile(
    r"^\s*ACTION:\s*(?P<action>[\w_]+)\s*\|\s*PAYLOAD:\s*(?P<payload>.*?)(?=^\s*ACTION:|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
BASE_ACTIONS = {"speak", "write_scratchpad", "submit_final", "skip"}
BUILTIN_TOOLS = {"query_rules", "view_leaderboard", "use_calculator"}
ToolAdapter = Callable[[str], str]
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def parse_actions(response: str) -> list[tuple[str, str]]:
    matches = list(ACTION_RE.finditer((response or "").strip()))
    if not matches:
        return [("speak", (response or "(empty response)").strip())]
    return [
        (match.group("action").lower(), match.group("payload").strip())
        for match in matches
    ]


def _calculate(expression: str) -> str:
    def evaluate(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
            return float(SAFE_OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right)))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        raise ValueError("Only basic arithmetic is supported")

    return str(evaluate(ast.parse(expression, mode="eval").body))


@dataclass
class RuleBlock:
    packet: CompetitionPacket
    leaderboard: Any
    tool_adapters: dict[str, ToolAdapter] = field(default_factory=dict)
    max_turns: int | None = None
    chat_history: list[dict[str, str]] = field(default_factory=list)
    action_log: list[dict[str, Any]] = field(default_factory=list)
    scratchpad: str = ""
    final_answer: str = ""
    submitted_by: str | None = None
    current_turn: int = 0
    current_round: int = 0
    exclusive_usage: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.max_turns = self.max_turns or self.packet.rules.max_turns
        unavailable = set(self.packet.rules.allowed_tools) - BUILTIN_TOOLS - set(
            self.tool_adapters
        )
        if unavailable:
            raise ValueError(
                "Rule card advertises tools without adapters: "
                + ", ".join(sorted(unavailable))
            )

    @property
    def submitted(self) -> bool:
        return bool(self.submitted_by)

    def start_round(self, number: int) -> None:
        self.current_round = number
        self.exclusive_usage.clear()

    def available_actions(self) -> list[str]:
        return sorted(BASE_ACTIONS | set(self.packet.rules.allowed_tools))

    def _validate(self, action: str) -> str | None:
        if action not in self.available_actions():
            return f"RULE VIOLATION: action '{action}' is not allowed."
        exclusive = self.packet.rules.exclusive_tools
        limit = exclusive.get(action)
        if limit is not None and self.exclusive_usage.get(action, 0) >= int(limit):
            return (
                f"RULE VIOLATION: '{action}' has {limit} seat(s) this round. "
                "Provide advice with speak or skip."
            )
        if action == "submit_final" and self.submitted:
            return "Submission is already finalized."
        return None

    def execute(self, agent: str, action: str, payload: str) -> str:
        if self.current_turn >= int(self.max_turns):
            return f"RULE VIOLATION: turn limit {self.max_turns} reached."
        self.current_turn += 1
        violation = self._validate(action)
        if violation:
            result = violation
        elif action == "speak":
            self.chat_history.append({"sender": agent, "message": payload})
            result = "Message broadcast."
        elif action == "write_scratchpad":
            self.scratchpad = payload
            result = "Shared scratchpad updated."
        elif action == "submit_final":
            if not payload.strip():
                result = "Submission rejected: empty answer."
            else:
                self.final_answer = payload.strip()
                self.submitted_by = agent
                result = "Submission finalized."
        elif action == "skip":
            result = "Turn skipped."
        elif action == "query_rules":
            result = query_rules(self.packet.rules, payload)
        elif action == "view_leaderboard":
            result = self.leaderboard.view()
        elif action == "use_calculator":
            try:
                result = f"Calculator output: {_calculate(payload)}"
            except (SyntaxError, ValueError, ZeroDivisionError, OverflowError) as exc:
                result = f"Calculator error: {exc}"
        elif action in self.tool_adapters:
            result = self.tool_adapters[action](payload)
        else:
            result = f"RULE VIOLATION: action '{action}' has no implementation."

        if action in self.packet.rules.exclusive_tools and not violation:
            self.exclusive_usage[action] = self.exclusive_usage.get(action, 0) + 1
        self.action_log.append(
            {
                "turn": self.current_turn,
                "round": self.current_round,
                "agent": agent,
                "action": action,
                "payload": payload,
                "result": result,
            }
        )
        return result
