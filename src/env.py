import ast
import hashlib
import json
import math
import operator
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from communication import CommunicationBudget
from contest_budget import (
    ContestBudget,
    estimate_tokens,
    resolve_contest_budget,
    truncate_to_token_budget,
)
from contest_rules import get_contest_rules
from deliberation import DELIBERATION_ACTIONS, DeliberationLedger, deliberation_payload
from memory import MemoryStore
from rules import PhaseSchedule, RuleCardError, RulesBaseline, RulesMode
from action_wire import Invocation, normalize_invocation
from tool_registry import (
    ACTION_REGISTRY,
    COMPETITION_ACTION_REGISTRY,
    COMPETITION_TOOL_REGISTRY,
    LEGACY_ACTION_ALIASES,
    PACK_ACTION_NAMES,
    TOOL_PACKS,
    action_matches,
    actions_for_runtime,
    canonical_action_name,
    dispatch_environment_action,
)
from tools_search import live_web_search, looks_like_answer_lookup
from workboard import Workboard

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BENCHMARK_PATH = os.path.join(REPO_ROOT, "data", "benchmarks")

TEAM_SIZE_MATRIX = {
    "iol_team": 4,
    "ioaa_group": 5,
    "arml_power": 15,
    "arml_national_team": 15,
    "arml_national_power": 15,
    "arml_local": 6,
    "ijso_practical": 3,
    "ieo_business_case": 5,
    "iypt": 5,
    "fyziklani": 5,
    "hmmt_team": 8,
    "hmmt_guts": 8,
    "mcm": 3,
    "icm": 3,
    "purple_comet": 6,
    "itym": 6,
    "wsc_writing": 3,
    "jessup": 5,
    "iiot": 4,
    "icpc": 3,
    "codeforces": 3,
}

# COMPETITION_TOOL_REGISTRY / COMPETITION_ACTION_REGISTRY live in tool_registry.

# Every set below is derived from the registry: the environment implements
# the canonical actions tagged ``runtimes={"env"}`` (or both) and accepts the
# legacy spellings in ``LEGACY_ACTION_ALIASES`` at its boundary.
ENV_ACTIONS = actions_for_runtime("env")

# Per-item board: pick a problem, record an answer, review a teammate's.
BOARD_ACTIONS = frozenset(
    {
        "select_problem",
        "skip_problem",
        "work",
        "triage_problem",
        "review_answer",
        "verify_problem",
    }
)

# Structured recall, so history survives outside the chat transcript.
MEMORY_ACTIONS = frozenset({"remember", "recall", "share_note"})

TEAM_ACTIONS = frozenset({"direct_message", "check_budget"})

# Available in every contest and every mode, including the vanilla baseline:
# these are the desk and the answer sheet, not contest-specific instruments.
CORE_WORKSPACE_ACTIONS = BOARD_ACTIONS | MEMORY_ACTIONS | TEAM_ACTIONS | {"inspect_problem"}

# Prefixes that mean "the environment refused this", as opposed to a rule break.
OPERATIONAL_ERROR_PREFIXES = (
    "Deliberation error:",
    "Board error:",
    "Memory error:",
    "Board unavailable:",
)

# Contest instruments: gated by the competition's tool allowlist. Submissions
# (``submit_code``) live in a tool pack but are gated by the competition's
# action registry instead.
TOOL_ACTIONS = frozenset(
    name
    for pack in TOOL_PACKS
    for name in PACK_ACTION_NAMES[pack]
    if not ACTION_REGISTRY[name].submission
) & ENV_ACTIONS

# Every spelling the wire may carry: canonical env actions plus their aliases.
ALL_ACTIONS = ENV_ACTIONS | frozenset(
    alias
    for alias, canonical in LEGACY_ACTION_ALIASES.items()
    if canonical in ENV_ACTIONS
)

_SAFE_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_SAFE_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class ProblemNotFoundError(ValueError):
    pass


class TurnLimitExceededError(RuntimeError):
    pass


class OlympiadEnvironment:
    def __init__(
        self,
        competition_id: str,
        problem_id: str,
        base_path: str = DEFAULT_BENCHMARK_PATH,
        max_turns: int | None = None,
        max_api_calls: int | None = None,
        max_output_tokens_per_call: int | None = None,
        max_total_tokens: int | None = None,
        rules_mode: RulesMode | str = RulesMode.OFF,
        rules_root: str | Path | None = None,
        rules_strict: bool = False,
    ):
        self.competition_id = competition_id
        self.problem_id = problem_id
        self.base_path = base_path
        self.rules_baseline = RulesBaseline.resolve(
            competition_id,
            mode=rules_mode,
            rules_root=rules_root,
            strict=rules_strict,
        )
        self.rules_mode = self.rules_baseline.mode
        self.rule_card = self.rules_baseline.card

        budget = resolve_contest_budget(
            competition_id,
            max_turns=(
                max_turns
                if max_turns is not None
                else self.rule_card.max_turns
                if self.rule_card is not None
                else None
            ),
            max_api_calls=max_api_calls,
            max_output_tokens_per_call=max_output_tokens_per_call,
            max_total_tokens=max_total_tokens,
        )
        self.budget = budget
        self.max_turns = budget.max_turns
        self.max_api_calls = budget.max_api_calls
        self.max_output_tokens_per_call = budget.max_output_tokens_per_call
        self.max_total_tokens = budget.max_total_tokens
        self.duration_minutes = budget.duration_minutes
        self.minutes_per_turn = budget.minutes_per_turn
        self.simulated_minutes = 0.0

        self.chat_history: list[dict[str, str]] = []
        self.group_messages: list[dict[str, Any]] = []
        self.action_log: list[dict[str, Any]] = []
        self.agent_observations: dict[str, list[dict[str, Any]]] = {}
        self.code_submissions: list[dict[str, Any]] = []
        self.private_thoughts: dict[str, list[dict[str, Any]]] = {}
        self.protocol_action_counts: dict[str, dict[str, int]] = {}
        self.budget_snapshots: list[dict[str, Any]] = []
        self.deliberation = DeliberationLedger()
        self.communication = CommunicationBudget(
            self.rule_card.communication
            if self.rule_card is not None and self.rules_mode is RulesMode.ENFORCED
            else {}
        )
        self.private_notes: dict[str, str] = {}
        self.workspace = {
            "scratchpad": "",
            "final_answer": "",
            "work_artifacts": [],
            "answer_sheet": "",
        }
        self.current_turn = 0  # collaboration turns completed
        self.action_count = 0  # env actions executed (speak/tools/etc.)
        self.api_calls = 0  # LLM calls made by collaboration layer
        self.tokens_used = 0  # estimated output tokens consumed
        self.api_calls_by_turn: dict[int, int] = {}
        self.tokens_by_turn: dict[int, int] = {}
        self.submitted = False
        self.submitted_by: Optional[str] = None
        self.wrong_submissions = 0
        self.submission_attempts = 0
        self.remote_submission: dict[str, Any] | None = None
        self.remote_submission_source: str | None = None
        self.rule_violations: list[str] = []
        self.contest_rules = get_contest_rules(competition_id)
        self.phase_schedule = (
            PhaseSchedule.from_simulation(self.rule_card.simulation)
            if self.rule_card is not None and self.rules_mode is RulesMode.ENFORCED
            else None
        )
        # Loaded before tool resolution: runtime-resource checks read fixtures.
        self.problem_data = self._load_problem()

        if self.rule_card is not None and self.rules_mode is RulesMode.ENFORCED:
            self.unavailable_declared_tools = sorted(
                {
                    tool
                    for tool in self.rule_card.allowed_tools
                    if tool not in TOOL_ACTIONS
                    or not self._tool_has_runtime_resource(tool)
                }
            )
            self.allowed_tools = [
                tool
                for tool in self.rule_card.allowed_tools
                if tool in TOOL_ACTIONS and self._tool_has_runtime_resource(tool)
            ]
        else:
            self.unavailable_declared_tools = []
            candidates = list(COMPETITION_TOOL_REGISTRY.get(competition_id, ()))
            self.allowed_tools = [
                tool for tool in candidates if self._tool_has_runtime_resource(tool)
            ]
            self.unavailable_declared_tools = sorted(
                set(candidates) - set(self.allowed_tools)
            )
        # Prefer tools declared in the rules audit when registry is empty but
        # rules list encoded tools (keeps DATA_COLLECTION + contest_rules aligned).
        if (
            self.rules_mode is not RulesMode.ENFORCED
            and not self.allowed_tools
            and self.contest_rules
            and self.contest_rules.encoded_tools
        ):
            encoded = list(self.contest_rules.encoded_tools)
            self.allowed_tools = [
                tool for tool in encoded if self._tool_has_runtime_resource(tool)
            ]
            self.unavailable_declared_tools = sorted(
                set(encoded) - set(self.allowed_tools)
            )
        # Multi-item contests get a board; single-deliverable ones stay as they
        # were, and the board actions report themselves unavailable.
        self.workboard = Workboard.from_problem(self.problem_data)
        self.memory = MemoryStore([])
        self.agent_names: list[str] = []

        problem_team_size = self.problem_data.get("team_size")
        self.team_size = self._resolve_team_size(
            problem_team_size,
            competition_id,
            default_size=self.rule_card.team_size_default if self.rule_card else None,
        )
        if self.rule_card is not None and not (
            self.rule_card.team_size_min <= self.team_size <= self.rule_card.team_size_max
        ):
            raise RuleCardError(
                f"Problem {problem_id!r} team_size={self.team_size} is outside rule-card "
                f"range {self.rule_card.team_size_min}-{self.rule_card.team_size_max}."
            )
        self.record_budget_snapshot("initialized")

    @staticmethod
    def _resolve_team_size(
        raw: Any, competition_id: str, *, default_size: int | None = None
    ) -> int:
        if raw is None:
            return default_size or TEAM_SIZE_MATRIX.get(competition_id, 3)
        if isinstance(raw, int):
            return raw
        text = str(raw).strip()
        if not text:
            return default_size or TEAM_SIZE_MATRIX.get(competition_id, 3)
        if "-" in text:
            # Ranges like "2-5" → use upper bound for agent count.
            parts = text.split("-", 1)
            try:
                return int(parts[1].strip())
            except ValueError:
                return default_size or TEAM_SIZE_MATRIX.get(competition_id, 3)
        try:
            return int(text)
        except ValueError:
            return default_size or TEAM_SIZE_MATRIX.get(competition_id, 3)

    def _problem_statement(self) -> str:
        for key in ("problem_description", "description", "prompt", "topic"):
            value = self.problem_data.get(key)
            if value and str(value).strip():
                return str(value).strip()
        return f"Problem {self.problem_id} ({self.competition_id})"

    def _benchmark_file(self) -> str:
        return os.path.join(self.base_path, self.competition_id, "benchmark.json")

    def _load_problem(self) -> dict:
        target_file = self._benchmark_file()
        if not os.path.exists(target_file):
            raise ProblemNotFoundError(
                f"No benchmark file for competition '{self.competition_id}' at {target_file}"
            )

        with open(target_file, "r", encoding="utf-8") as f:
            problems = json.load(f)

        problem = next((p for p in problems if p.get("problem_id") == self.problem_id), None)
        if problem is None:
            available = [p.get("problem_id") for p in problems[:5]]
            suffix = f" (first ids: {available})" if available else ""
            raise ProblemNotFoundError(
                f"Problem '{self.problem_id}' not found in {target_file}{suffix}"
            )
        return problem

    def get_available_tools(self) -> list[str]:
        return list(self.allowed_tools)

    def _tool_has_runtime_resource(self, tool: str) -> bool:
        role = {
            "read_lab_equipment": "lab",
            "read_star_chart": "star",
        }.get(tool)
        if role is None:
            return True
        fixtures = self.problem_data.get("tool_fixtures") or {}
        if role in fixtures or any(role in str(key).lower() for key in fixtures):
            return True
        for asset in self.problem_data.get("assets") or []:
            if not isinstance(asset, dict):
                continue
            path_text = str(asset.get("path") or "")
            label = f"{asset.get('role', '')} {path_text}".lower()
            path = Path(path_text)
            if not path.is_absolute():
                path = Path(REPO_ROOT) / path
            if role in label and path.is_file():
                return True
        return False

    def rules_metadata(self) -> dict[str, Any]:
        metadata = self.rules_baseline.metadata()
        metadata["declared_tool_availability"] = {
            tool: (
                "unavailable"
                if tool in self.unavailable_declared_tools
                else "enforced"
                if self.rules_mode is RulesMode.ENFORCED
                else "prompt_only"
            )
            for tool in (self.rule_card.allowed_tools if self.rule_card else ())
        }
        return metadata

    def query_rules(self, agent_name: str | None = None) -> str:
        if self.rule_card is None:
            return json.dumps(
                {
                    "competition_id": self.competition_id,
                    "allowed_tools": self.get_available_tools(),
                    "note": "No rule-aware baseline card is active.",
                },
                ensure_ascii=False,
                indent=2,
            )
        from rules import agent_view

        visible = agent_view(self.rule_card, team_size=self.team_size)
        if agent_name:
            role = self.rule_card.role_for(agent_name)
            if role:
                visible["your_role"] = {
                    "name": role.name,
                    "title": role.title,
                    "duties": list(role.duties),
                    "may_submit": role.may_submit,
                    "rule_expertise": list(role.rule_expertise),
                }
        return json.dumps(visible, ensure_ascii=False, indent=2)

    def get_metadata(self) -> dict:
        rules = self.contest_rules
        metadata = {
            "competition_id": self.competition_id,
            "problem_id": self.problem_id,
            "title": self.problem_data.get("title"),
            "year": self.problem_data.get("year"),
            "task_type": self.problem_data.get("task_type"),
            "team_size": self.team_size,
            "allowed_tools": self.get_available_tools(),
            "has_gold_answer": bool(self.problem_data.get("gold_label", {}).get("expected_answer")),
            "search_policy": rules.search_policy if rules else None,
            "wrong_submission_penalty_minutes": (
                rules.wrong_submission_penalty_minutes if rules else None
            ),
            "rules_gap_count": len(rules.gaps()) if rules else None,
            "duration_minutes": self.duration_minutes,
            "max_turns": self.max_turns,
            "minutes_per_turn": self.minutes_per_turn,
            **self.rules_metadata(),
        }
        if self.rule_card is not None:
            from rules import agent_view

            metadata["rule"] = agent_view(self.rule_card, team_size=self.team_size)
        return metadata

    def get_state(self) -> dict:
        api_status = (
            f"{self.api_calls}/{self.max_api_calls}"
            if self.max_api_calls is not None
            else f"{self.api_calls}/∞"
        )
        token_status = (
            f"{self.tokens_used}/{self.max_total_tokens}"
            if self.max_total_tokens is not None
            else f"{self.tokens_used}/∞"
        )
        per_call_cap = (
            str(self.max_output_tokens_per_call)
            if self.max_output_tokens_per_call is not None
            else "∞"
        )
        return {
            "competition_id": self.competition_id,
            "problem_id": self.problem_id,
            "team_size": self.team_size,
            "allowed_tools": self.get_available_tools(),
            "problem_statement": self._problem_statement(),
            "chat_logs": list(self.chat_history),
            "shared_workspace": dict(self.workspace),
            "deliberation": self.deliberation.report(),
            "communication": self.communication.report(),
            "turn_status": f"{self.current_turn}/{self.max_turns}",
            "api_call_status": api_status,
            "token_status": token_status,
            "output_token_cap_per_call": per_call_cap,
            "submitted": self.submitted,
            "wrong_submissions": self.wrong_submissions,
            "board_enabled": self.workboard is not None,
            "board_overview": self.board_overview(),
            "answer_sheet": self.board_answer_sheet(),
            "search_policy": self.contest_rules.search_policy if self.contest_rules else None,
            "duration_minutes": self.duration_minutes,
            "simulated_minutes": self.simulated_minutes,
            "clock_status": (
                f"{self.simulated_minutes:g}/{self.duration_minutes} min"
                if self.duration_minutes is not None
                else f"{self.simulated_minutes:g} min"
            ),
        }

    def record_budget_snapshot(self, event: str) -> None:
        self.budget_snapshots.append(
            {
                "event": event,
                "turn": self.current_turn,
                "api_calls": self.api_calls,
                "tokens_used": self.tokens_used,
                "simulated_minutes": self.simulated_minutes,
                "wrong_submissions": self.wrong_submissions,
            }
        )

    def consume_agent_observations(self, agent_name: str) -> list[dict[str, Any]]:
        return self.agent_observations.pop(agent_name, [])

    def _count_protocol_action(self, agent_name: str, action_type: str) -> None:
        by_action = self.protocol_action_counts.setdefault(agent_name, {})
        by_action[action_type] = by_action.get(action_type, 0) + 1

    def record_private_thought(
        self,
        agent_name: str,
        payload: str,
        *,
        metadata: dict[str, Any] | None = None,
        count_as_action: bool = True,
    ) -> str:
        """Store explicit private reasoning outside public action history."""
        if count_as_action:
            self.action_count += 1
        self._count_protocol_action(agent_name, "think")
        entry = {
            "turn": self.current_turn,
            "agent": agent_name,
            "content": payload,
            "visibility": "private",
            **(metadata or {}),
        }
        self.private_thoughts.setdefault(agent_name, []).append(entry)
        return "Private thought stored for this contestant only."

    def record_work_artifact(
        self,
        agent_name: str,
        payload: str,
        *,
        recipients: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Append durable work to public or recipient-scoped team state."""
        self.action_count += 1
        self._count_protocol_action(agent_name, "work")
        audience = sorted(set(recipients or []))
        visibility = "group" if audience else "team"
        entry = {
            "turn": self.current_turn,
            "agent": agent_name,
            "content": payload,
            "visibility": visibility,
            "recipients": audience,
            **(metadata or {}),
        }
        artifacts = self.workspace.setdefault("work_artifacts", [])
        artifacts.append(entry)
        result = (
            f"Work shared with {', '.join(audience)}."
            if audience
            else "Public written work appended."
        )
        self._log_action(
            agent_name,
            "work",
            payload,
            result,
            metadata={
                **(metadata or {}),
                "visibility": visibility,
                "recipients": audience,
            },
        )
        return result

    def record_scoped_message(
        self,
        agent_name: str,
        payload: str,
        *,
        recipients: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Send one message visible only to its sender and named recipients."""
        self.action_count += 1
        max_chars = self.communication.max_message_chars
        if max_chars and len(payload) > max_chars:
            payload, compacted = self.communication.compact_payload(
                agent_name=agent_name,
                action_type="speak",
                payload=payload,
                turn=self.current_turn,
                max_chars=max_chars,
            )
            metadata = {**(metadata or {}), **compacted}
        violation = self.communication.check(
            agent_name=agent_name,
            action_type="speak",
            payload=payload,
            turn=self.current_turn,
        )
        audience = sorted(set(recipients))
        scoped_metadata = {
            **(metadata or {}),
            "visibility": "group",
            "recipients": audience,
        }
        if violation:
            self.rule_violations.append(violation)
            self._log_action(
                agent_name,
                "speak",
                payload,
                violation,
                metadata=scoped_metadata,
            )
            return violation
        self.communication.record(agent_name=agent_name, action_type="speak")
        entry = {
            "turn": self.current_turn,
            "sender": agent_name,
            "recipients": audience,
            "message": payload,
            "visibility": "group",
        }
        self.group_messages.append(entry)
        result = f"Message sent to {', '.join(audience)}."
        self._log_action(
            agent_name,
            "speak",
            payload,
            result,
            metadata=scoped_metadata,
        )
        return result

    def record_rest(
        self,
        agent_name: str,
        reason: str = "",
        *,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Record a private one-turn rest decision."""
        self.action_count += 1
        self._count_protocol_action(agent_name, "rest")
        payload = reason.strip()
        result = f"{agent_name} rests" + (f" ({payload})." if payload else ".")
        self._log_action(
            agent_name,
            "rest",
            payload,
            result,
            metadata=metadata,
        )
        return result

    def record_protocol_speak(self, agent_name: str) -> None:
        self._count_protocol_action(agent_name, "speak")

    def format_private_thoughts(
        self,
        agent_name: str,
        *,
        max_entries: int | None = None,
    ) -> str:
        entries = self.private_thoughts.get(agent_name, [])
        if max_entries is not None and max_entries > 0:
            entries = entries[-max_entries:]
        if not entries:
            return ""
        lines = ["=== YOUR PRIVATE THINK LEDGER ==="]
        for item in entries:
            lines.append(f"Turn {item['turn']}: {item['content']}")
        return "\n".join(lines)

    def format_shared_work(
        self,
        *,
        agent_name: str | None = None,
        max_entries: int | None = None,
    ) -> str:
        entries = list(self.workspace.get("work_artifacts") or [])
        if agent_name is None:
            entries = [item for item in entries if not item.get("recipients")]
        else:
            entries = [
                item
                for item in entries
                if not item.get("recipients")
                or item.get("agent") == agent_name
                or agent_name in item.get("recipients", [])
            ]
        if max_entries is not None and max_entries > 0:
            entries = entries[-max_entries:]
        if not entries:
            return ""
        lines = ["=== SHARED WRITTEN WORK ==="]
        for item in entries:
            audience = item.get("recipients") or []
            scope = f" | private group: {', '.join(audience)}" if audience else ""
            lines.append(
                f"Turn {item['turn']} | {item['agent']}{scope}:\n{item['content']}"
            )
        return "\n\n".join(lines)

    def format_group_memory(
        self,
        agent_name: str,
        *,
        max_entries: int | None = None,
    ) -> str:
        """Render only private-group/direct messages this agent may read."""
        entries = [
            item
            for item in self.group_messages
            if item.get("sender") == agent_name
            or agent_name in item.get("recipients", [])
        ]
        if max_entries is not None and max_entries > 0:
            entries = entries[-max_entries:]
        if not entries:
            return ""
        lines = ["=== YOUR GROUP / DIRECT MEMORY ==="]
        for item in entries:
            lines.append(
                f"Turn {item['turn']} | {item['sender']} -> "
                f"{', '.join(item['recipients'])}: {item['message']}"
            )
        return "\n".join(lines)

    def _shared_team_state_keys(self) -> set[str]:
        if self.rules_mode is not RulesMode.ENFORCED or self.rule_card is None:
            return set()
        simulation = self.rule_card.simulation or {}
        raw = simulation.get("shared_team_state") or ()
        return {str(item) for item in raw}

    def submit_code_is_team_visible(self) -> bool:
        """ICPC card shares pending_run_status with the whole team."""
        return "pending_run_status" in self._shared_team_state_keys()

    # Reads and personal bookkeeping: the result goes back to the actor only.
    # The mutating board actions stay team-visible — a board nobody else can
    # see would not coordinate anything.
    PRIVATE_WORKSPACE_ACTIONS = frozenset(
        {"inspect_problem", "check_budget", "query_rules", "remember", "recall"}
    )

    def _action_visibility(self, action_type: str) -> str:
        canonical = canonical_action_name(action_type)
        if canonical in {
            "write_private_notes",
            "rest",
            *TOOL_ACTIONS,
            *self.PRIVATE_WORKSPACE_ACTIONS,
        }:
            return "private"
        if canonical == "submit_code":
            return "team" if self.submit_code_is_team_visible() else "private"
        return "team"

    def _record_shared_code_submission(
        self, agent_name: str, payload: str, result: str
    ) -> None:
        if not self.submit_code_is_team_visible():
            return
        try:
            feedback = json.loads(result)
        except json.JSONDecodeError:
            return
        remote = feedback.get("remote") or {}
        effective_verdict = remote.get("verdict") or feedback.get("verdict")
        effective_reason = (
            remote.get("message")
            or remote.get("status")
            or feedback.get("reason")
        )
        entry = {
            "turn": self.current_turn,
            "agent": agent_name,
            "verdict": effective_verdict,
            "test_scope": feedback.get("test_scope"),
            "grading_scope_label": feedback.get("grading_scope_label"),
            "reason": effective_reason,
            "passed": feedback.get("passed"),
            "total": feedback.get("total"),
            "finalized": bool(feedback.get("finalized")),
            "code": payload.strip(),
            "source_hash": self._source_hash(payload),
        }
        cases = feedback.get("cases") or feedback.get("tests") or []
        if cases:
            entry["case_detail"] = cases[0].get("detail") or ""
        self.code_submissions.append(entry)
        scope = entry.get("grading_scope_label") or entry.get("test_scope") or "tests"
        summary = (
            f"[Contest control] {agent_name} submitted a programming run "
            f"({scope}): verdict={entry.get('verdict')} "
            f"({entry.get('reason') or 'no detail'}). "
            "The full source is available in TEAM CODE SUBMISSIONS."
        )
        self.chat_history.append({"sender": "Contest_Control", "message": summary})

    @staticmethod
    def _source_hash(payload: str) -> str:
        normalized = "\n".join(
            line.rstrip() for line in payload.strip().splitlines()
        )
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _unchanged_failed_source_error(self, payload: str) -> str | None:
        if not self.code_submissions:
            return None
        latest = self.code_submissions[-1]
        verdict = str(latest.get("verdict") or "").upper()
        if verdict in {"", "AC", "PENDING", "SUBMIT_FAILED"}:
            return None
        prior_hash = latest.get("source_hash")
        if prior_hash is None and latest.get("code"):
            prior_hash = self._source_hash(str(latest["code"]))
        if prior_hash != self._source_hash(payload):
            return None
        return (
            f"SUBMISSION BLOCKED: unchanged source after {verdict}. "
            "Diagnose the verdict, change the implementation, and validate it "
            "before submitting again."
        )

    def format_team_code_submissions(self, *, include_source: bool = True) -> str:
        if not self.code_submissions:
            return ""
        lines = ["=== TEAM CODE SUBMISSIONS (contest control) ==="]
        for item in self.code_submissions:
            scope = item.get("grading_scope_label") or item.get("test_scope") or "tests"
            header = (
                f"Turn {item['turn']} | {item['agent']} | verdict={item.get('verdict')} "
                f"| scope={scope} | {item.get('reason') or ''}".strip()
            )
            lines.append(header)
            if include_source and item.get("code"):
                lines.append(str(item["code"]))
        return "\n".join(lines) + "\n"

    def to_transcript(self) -> dict[str, Any]:
        agents = sorted(
            {
                str(item.get("sender") or item.get("agent"))
                for item in [*self.chat_history, *self.action_log]
                if item.get("sender") or item.get("agent")
            }
        )
        return {
            "schema_version": "agent-olympiad.transcript/v1",
            "metadata": {
                **self.get_metadata(),
                "agents": agents,
            },
            "chat_history": list(self.chat_history),
            "group_messages": list(self.group_messages),
            "action_log": list(self.action_log),
            "budget_snapshots": list(self.budget_snapshots),
            "budget": {
                "used": {
                    "turns": self.current_turn,
                    "api_calls": self.api_calls,
                    "tokens": self.tokens_used,
                },
                "limits": {
                    "turns": self.max_turns,
                    "api_calls": self.max_api_calls,
                    "tokens": self.max_total_tokens,
                },
            },
            "submission": {
                "submitted": self.submitted,
                "submitted_by": self.submitted_by,
                "final_answer": self.workspace.get("final_answer", ""),
                "attempts": self.submission_attempts,
                "wrong_submissions": self.wrong_submissions,
            },
            "workspace": dict(self.workspace),
            "code_submissions": list(self.code_submissions),
            "private_thoughts": {
                agent: list(entries)
                for agent, entries in self.private_thoughts.items()
            },
            "protocol_action_counts": {
                agent: dict(counts)
                for agent, counts in self.protocol_action_counts.items()
            },
            "rule_violations": list(self.rule_violations),
            "deliberation": self.deliberation.report(),
            "communication": self.communication.report(),
            "workboard": (
                self.workboard.snapshot() if self.workboard is not None else None
            ),
            "memory": self.memory.snapshot(),
            "rules_baseline": self.rules_metadata(),
        }

    def turns_exhausted(self) -> bool:
        """True when no further collaboration turns may be started."""
        return self.current_turn >= self.max_turns

    def can_begin_turn(self) -> bool:
        return self.current_turn < self.max_turns

    def api_budget_exhausted(self) -> bool:
        return self.max_api_calls is not None and self.api_calls >= self.max_api_calls

    def token_budget_exhausted(self) -> bool:
        return self.max_total_tokens is not None and self.tokens_used >= self.max_total_tokens

    def apply_output_token_budget(self, text: str) -> str:
        """Enforce per-call and team-wide output token caps."""
        capped = text
        if self.max_output_tokens_per_call is not None:
            capped = truncate_to_token_budget(capped, self.max_output_tokens_per_call)
        if self.max_total_tokens is not None:
            remaining = self.max_total_tokens - self.tokens_used
            capped = truncate_to_token_budget(capped, remaining)
        used = estimate_tokens(capped)
        self.tokens_used += used
        turn = self.current_turn
        self.tokens_by_turn[turn] = self.tokens_by_turn.get(turn, 0) + used
        return capped

    def token_usage_by_turn(self) -> list[dict[str, int]]:
        """Per-turn estimated output tokens and API calls (sorted by turn)."""
        turns = sorted(set(self.tokens_by_turn) | set(self.api_calls_by_turn))
        return [
            {
                "turn": turn,
                "tokens": self.tokens_by_turn.get(turn, 0),
                "api_calls": self.api_calls_by_turn.get(turn, 0),
            }
            for turn in turns
        ]

    def begin_turn(self) -> int:
        """Start a collaboration turn (time step). Raises if turn budget is spent."""
        if not self.can_begin_turn():
            raise TurnLimitExceededError(
                f"Turn limit reached ({self.max_turns}) for {self.problem_id}"
            )
        self.current_turn += 1
        if self.phase_schedule is not None:
            message = self.phase_schedule.phase_transition_message(
                self.current_turn,
                self.current_turn - 1,
            )
            if message:
                self.chat_history.append(
                    {"sender": "Contest_Control", "message": message}
                )
        # Advance by turn schedule, but never rewind time already burned by WA.
        turn_clock = self.budget.simulated_minutes_for_turns(self.current_turn)
        self.simulated_minutes = max(self.simulated_minutes, turn_clock)
        self.record_budget_snapshot("turn_started")
        return self.current_turn

    def record_api_call(self) -> None:
        """Count one LLM call against the cost budget."""
        if self.api_budget_exhausted():
            raise TurnLimitExceededError(
                f"API call budget reached ({self.max_api_calls}) for {self.problem_id}"
            )
        self.api_calls += 1
        turn = self.current_turn
        self.api_calls_by_turn[turn] = self.api_calls_by_turn.get(turn, 0) + 1
        self.record_budget_snapshot("api_call")

    def _log_action(
        self,
        agent_name: str,
        action_type: str,
        payload: str,
        result: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        visibility = self._action_visibility(action_type)
        entry = {
            "turn": self.current_turn,
            "agent": agent_name,
            "sender": agent_name,
            "action": action_type,
            "payload": payload,
            "result": result,
            "visibility": visibility,
            **(metadata or {}),
        }
        self.action_log.append(entry)
        observation = {
            "turn": self.current_turn,
            "action": action_type,
            "result": result,
            "visibility": visibility,
        }
        if visibility == "private":
            self.agent_observations.setdefault(agent_name, []).append(observation)
        elif canonical_action_name(action_type) in CORE_WORKSPACE_ACTIONS:
            # Team-visible board work still needs its result to reach the actor:
            # the rejection notice is the whole point of recording a repeat.
            self.agent_observations.setdefault(agent_name, []).append(observation)
        elif action_type == "submit_code":
            roster = (
                [role.name for role in self.rule_card.agent_roles]
                if self.rule_card is not None
                else [agent_name]
            )
            for peer in roster:
                self.agent_observations.setdefault(peer, []).append(observation)

    def validate_action(self, action_type: str, agent_name: str | None = None) -> Optional[str]:
        """Contest-rule gate. Accepts canonical names and legacy aliases alike."""
        invoked = str(action_type or "").strip().lower()
        canonical = canonical_action_name(invoked)
        if invoked not in ALL_ACTIONS:
            return f"Unrecognized action '{action_type}'."
        if (
            self.rules_mode is not RulesMode.ENFORCED
            and canonical in DELIBERATION_ACTIONS | {"write_private_notes"}
        ):
            return f"Unrecognized action '{action_type}'."
        if (
            self.rules_mode is not RulesMode.PROMPT_ONLY
            and canonical in TOOL_ACTIONS
            and canonical not in self.allowed_tools
        ):
            return (
                f"RULE VIOLATION: Tool '{action_type}' is banned in {self.competition_id}. "
                f"Allowed tools: {self.allowed_tools or 'none (paper and pencil only)'}"
            )
        if canonical == "submit_code" and canonical not in COMPETITION_ACTION_REGISTRY.get(
            self.competition_id, []
        ):
            return f"RULE VIOLATION: submit_code is unavailable in {self.competition_id}."
        if (
            self.rules_mode is RulesMode.ENFORCED
            and canonical in DELIBERATION_ACTIONS
            and not (
                self.rule_card
                and self.rule_card.deliberation.get("mode") == "structured"
            )
        ):
            return (
                f"RULE VIOLATION: Structured deliberation action '{action_type}' "
                f"is not enabled for {self.competition_id}."
            )
        if (
            self.rules_mode is RulesMode.ENFORCED
            and canonical == "submit"
            and agent_name is not None
            and self.rule_card is not None
        ):
            role = self.rule_card.role_for(agent_name)
            if role is None or not role.may_submit:
                return f"RULE VIOLATION: {agent_name} is not authorized to submit."
        if canonical == "submit" and self.submitted:
            return "Submission already finalized; further submit_final actions are ignored."
        if self.phase_schedule is not None:
            phase_violation = self.phase_schedule.validate_action(
                self.current_turn, invoked
            )
            if phase_violation:
                return phase_violation
        return None

    # Handler table: canonical action name -> bound-method name. Legacy
    # spellings never appear here; ``normalize_invocation`` maps them first.
    _HANDLERS: dict[str, str] = {
        "speak": "_act_speak",
        "work": "_act_work",
        "write_private_notes": "_act_write_private_notes",
        "rest": "_act_rest",
        "select_problem": "_act_select_problem",
        "skip_problem": "_act_skip_problem",
        "inspect_problem": "_act_inspect_problem",
        "triage_problem": "_act_triage_problem",
        "verify_problem": "_act_verify_problem",
        "review_answer": "_act_review_answer",
        "remember": "_act_remember",
        "recall": "_act_recall",
        "share_note": "_act_share_note",
        "direct_message": "_act_direct_message",
        "check_budget": "_act_check_budget",
        "query_rules": "_act_query_rules",
        "submit": "_act_submit",
        **{name: "_act_deliberation" for name in DELIBERATION_ACTIONS},
        **{name: "_act_tool" for name in TOOL_ACTIONS | {"submit_code"}},
    }

    @classmethod
    def unimplemented_actions(cls) -> frozenset[str]:
        """Registry env actions this runtime has no handler for (should be empty)."""
        return ENV_ACTIONS - set(cls._HANDLERS)

    def execute_action(
        self,
        agent_name: str,
        action_type: str,
        payload: str | dict[str, Any],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Run one action given in either wire encoding.

        ``payload`` is the legacy text after ``PAYLOAD:`` or a typed argument
        mapping; both are normalized onto the registry before dispatch.
        """
        self.action_count += 1
        invocation = normalize_invocation(action_type, payload)
        invoked = invocation.invoked_as or str(action_type)
        # The log records the canonical name; the spelling the agent used is
        # kept alongside so legacy transcripts stay diagnosable.
        canonical = invocation.action
        log_payload = (
            payload
            if isinstance(payload, str)
            else json.dumps(invocation.arguments, ensure_ascii=False)
        )
        if invocation.is_alias:
            metadata = {**(metadata or {}), "invoked_as": invoked}

        violation = self.validate_action(invoked, agent_name)
        if violation:
            self.rule_violations.append(violation)
            self._log_action(agent_name, canonical, log_payload, violation, metadata=metadata)
            return violation

        arguments, errors = (
            self._fill_text_defaults(invocation)
            if isinstance(payload, str)
            else (dict(invocation.arguments), invocation.errors)
        )
        if errors:
            result = f"Usage error: {invoked}: " + "; ".join(errors)
            self._log_action(agent_name, canonical, log_payload, result, metadata=metadata)
            return result

        message_key = self._message_argument(canonical)
        message = str(arguments.get(message_key) or "") if message_key else log_payload
        max_message_chars = self.communication.max_message_chars
        if (
            self.communication.is_counted(canonical)
            and max_message_chars
            and len(message.strip()) > max_message_chars
        ):
            message, compacted_metadata = self.communication.compact_payload(
                agent_name=agent_name,
                action_type=invoked,
                payload=message,
                turn=self.current_turn,
                max_chars=max_message_chars,
            )
            metadata = {**(metadata or {}), **compacted_metadata}
            if message_key:
                arguments[message_key] = message
                if isinstance(payload, str):
                    log_payload = message

        communication_violation = self.communication.check(
            agent_name=agent_name,
            action_type=canonical,
            payload=message,
            turn=self.current_turn,
        )
        if communication_violation:
            self.rule_violations.append(communication_violation)
            self._log_action(
                agent_name, canonical, log_payload, communication_violation, metadata=metadata
            )
            return communication_violation

        handler = getattr(self, self._HANDLERS[canonical], None)
        if handler is None:
            result: str = f"Operational error: action '{invoked}' not implemented."
        else:
            outcome = handler(agent_name, arguments, invocation)
            if isinstance(outcome, tuple):
                result, extra = outcome
                metadata = {**(metadata or {}), **extra}
            else:
                result = str(outcome)

        if result.startswith(OPERATIONAL_ERROR_PREFIXES):
            # A refused board/memory call is a no-op, not a broken contest rule.
            if result.startswith("Deliberation error:"):
                self.rule_violations.append(result)
        else:
            self.communication.record(agent_name=agent_name, action_type=canonical)
        self._log_action(agent_name, canonical, log_payload, result, metadata=metadata)
        return result

    @staticmethod
    def _message_argument(canonical: str) -> str | None:
        """Which argument carries the communication-budgeted text, if any."""
        spec = ACTION_REGISTRY.get(canonical)
        if spec is None:
            return None
        for candidate in ("content", "answer", "code", "reason"):
            if any(argument.name == candidate for argument in spec.arguments):
                return candidate
        return None

    @staticmethod
    def _fill_text_defaults(invocation: Invocation) -> tuple[dict[str, Any], tuple[str, ...]]:
        """Text protocol: an empty payload is the handler's problem, not a schema error.

        The legacy prompts let ``submit_final`` with nothing attached fail with
        the environment's own message ("final answer cannot be empty"), so
        missing required free-text arguments are filled with ``""`` and the
        matching validation errors dropped; type and enum errors stand.
        """
        arguments = dict(invocation.arguments)
        if invocation.spec is None:
            return arguments, invocation.errors
        filled: set[str] = set()
        for argument in invocation.spec.arguments:
            if (
                argument.required
                and argument.name not in arguments
                and argument.type == "string"
                and not argument.enum
            ):
                arguments[argument.name] = ""
                filled.add(f"missing required argument: {argument.name}")
        errors = tuple(error for error in invocation.errors if error not in filled)
        return arguments, errors

    # ------------------------------------------------------------ handlers

    def _act_speak(self, agent_name: str, arguments: dict[str, Any], _: Invocation) -> str:
        self.chat_history.append({"sender": agent_name, "message": arguments["content"]})
        return "Message broadcast to all agents."

    def _act_work(self, agent_name: str, arguments: dict[str, Any], invocation: Invocation) -> str:
        content = str(arguments.get("content") or "")
        problem_id = str(arguments.get("problem_id") or "").strip()
        if invocation.invoked_as == "write_scratchpad" or self.workboard is None and not problem_id:
            self.workspace["scratchpad"] = content
            return "Shared scratchpad updated."
        if self.workboard is None:
            return self._board_unavailable()
        if not problem_id:
            held = self._held_item(agent_name)
            if held is None:
                # No current problem: the note is team work, not an answer.
                self.workspace["scratchpad"] = content
                return (
                    "Shared scratchpad updated. To record an answer for an item, "
                    "pass problem_id (or claim the item first)."
                )
            problem_id = held.item_id
        item = self.workboard.resolve(problem_id)
        if item is None:
            return self.workboard.unknown_ref_message(problem_id)
        result = self.workboard.record_answer(agent_name, item, content, turn=self.current_turn)
        self._sync_answer_sheet()
        self._broadcast_board_event(agent_name, "work", item, result)
        return result

    def _act_write_private_notes(
        self, agent_name: str, arguments: dict[str, Any], _: Invocation
    ) -> str:
        self.private_notes[agent_name] = str(arguments.get("content") or "")
        return "Private notes updated; no communication budget used."

    def _act_deliberation(
        self, agent_name: str, arguments: dict[str, Any], invocation: Invocation
    ) -> str:
        role = self.rule_card.role_for(agent_name) if self.rule_card else None
        return self.deliberation.record(
            agent_name=agent_name,
            action_type=invocation.action,
            payload=deliberation_payload(invocation.action, arguments),
            turn=self.current_turn,
            may_decide=bool(role and role.may_submit),
        )

    def _act_rest(self, agent_name: str, arguments: dict[str, Any], _: Invocation) -> str:
        reason = str(arguments.get("reason") or "").strip() or "passing this turn"
        return f"{agent_name} sleeps ({reason})."

    def _act_select_problem(
        self, agent_name: str, arguments: dict[str, Any], _: Invocation
    ) -> str:
        item, error = self._board_item(arguments.get("problem_id"))
        if error:
            return error
        result = self.workboard.claim(agent_name, item, turn=self.current_turn)
        self._broadcast_board_event(agent_name, "select_problem", item, result)
        return result

    def _act_skip_problem(
        self, agent_name: str, arguments: dict[str, Any], _: Invocation
    ) -> str:
        if self.workboard is None:
            return self._board_unavailable()
        # ``release_problem <item>`` arrives with the item in ``reason``.
        reason = str(arguments.get("reason") or "").strip()
        item = self.workboard.resolve(reason) if reason else None
        if item is None:
            item = self._held_item(agent_name)
        if item is None:
            return "Board error: you hold no item to release; name one, e.g. P3."
        result = self.workboard.release(agent_name, item, turn=self.current_turn)
        self._broadcast_board_event(agent_name, "skip_problem", item, result)
        return result

    def _act_inspect_problem(
        self, agent_name: str, arguments: dict[str, Any], _: Invocation
    ) -> str:
        problem_id = str(arguments.get("problem_id") or "").strip()
        focus = str(arguments.get("focus") or "").strip()
        if self.workboard is not None:
            if not problem_id:
                return self.workboard.overview(turn=self.current_turn, agent_name=agent_name)
            item = self.workboard.resolve(problem_id)
            if item is None:
                return self.workboard.unknown_ref_message(problem_id)
            return self.workboard.detail(item, turn=self.current_turn)
        if "execute_code" in self.allowed_tools:
            return self._code_history(agent_name, focus or problem_id)
        # Single-deliverable, no sandbox: show the team's current draft.
        return "\n".join(
            [
                self._board_unavailable(),
                "=== WORKSPACE ===",
                f"Scratchpad: {self.workspace.get('scratchpad') or '(empty)'}",
                f"Final answer: {self.workspace.get('final_answer') or '(not submitted)'}",
            ]
        )

    def _code_history(self, agent_name: str, focus: str) -> str:
        """Legacy ``verify``: latest code plus the visible run/submission history."""
        visible_history = [
            {
                "turn": item.get("turn"),
                "agent": item.get("agent"),
                "action": item.get("action"),
                "payload": item.get("payload"),
                "result": item.get("result"),
            }
            for item in self.action_log
            if item.get("visibility") != "private" or item.get("agent") == agent_name
        ][-20:]
        latest_code = next(
            (
                str(item.get("payload") or "")
                for item in reversed(visible_history)
                if canonical_action_name(str(item.get("action") or ""))
                in {"execute_code", "submit_code", "submit"}
                and str(item.get("payload") or "").strip()
            ),
            str(self.workspace.get("final_answer") or ""),
        )
        return json.dumps(
            {
                "focus": focus,
                "latest_code": latest_code,
                "history": visible_history,
                "note": (
                    "Self-verification context only; this does not count as an "
                    "independent review approval."
                ),
            },
            ensure_ascii=False,
        )

    def _act_triage_problem(
        self, agent_name: str, arguments: dict[str, Any], invocation: Invocation
    ) -> str:
        item, error = self._board_item(arguments.get("problem_id"))
        if error:
            return error
        priority = str(arguments.get("priority") or "").strip().lower()
        reason = str(arguments.get("reason") or "").strip()
        if priority == "hopeless":
            result = self.workboard.mark_hopeless(item, reason, hopeless=True)
            self._broadcast_board_event(agent_name, "mark_hopeless", item, result)
            return result
        if item.hopeless:
            result = self.workboard.mark_hopeless(item, "", hopeless=False)
            self._broadcast_board_event(agent_name, "mark_hopeless", item, result)
            if invocation.invoked_as == "mark_hopeless" or priority == "normal" and item.priority == "normal":
                return result
        result = self.workboard.set_priority(item, priority)
        self._broadcast_board_event(agent_name, "set_priority", item, result)
        return result

    def _act_verify_problem(
        self, agent_name: str, arguments: dict[str, Any], _: Invocation
    ) -> str:
        item, error = self._board_item(arguments.get("problem_id"))
        if error:
            return error
        verdict, _, comment = str(arguments.get("content") or "").strip().partition(" ")
        result = self.workboard.review(agent_name, item, verdict, comment, turn=self.current_turn)
        self._broadcast_board_event(agent_name, "verify_problem", item, result)
        return result

    def _act_review_answer(
        self, agent_name: str, arguments: dict[str, Any], _: Invocation
    ) -> str:
        item, error = self._board_item(arguments.get("problem_id"))
        if error:
            return error
        if not item.attempts:
            return f"Board error: {item.item_id} has no recorded answer to review yet."
        expected = self.workboard.answer_hash(item)
        given = str(arguments.get("version_hash") or "").strip().lower()
        if given and not expected.startswith(given):
            return (
                f"Board error: version_hash {given!r} does not match the answer "
                f"currently recorded for {item.item_id} (version {expected}). "
                "Re-open the item and review the current version."
            )
        verdict = "agree" if arguments.get("decision") == "approve" else "disagree"
        result = self.workboard.review(
            agent_name, item, verdict, str(arguments.get("content") or ""), turn=self.current_turn
        )
        self._broadcast_board_event(agent_name, "verify_problem", item, result)
        return result

    def _act_remember(self, agent_name: str, arguments: dict[str, Any], _: Invocation) -> str:
        problem_ref, text = self._memory_scope(arguments.get("problem_id"), arguments.get("content"))
        if not text:
            return "Memory error: nothing to remember."
        item = self.memory.add(agent_name, text, turn=self.current_turn, problem_ref=problem_ref)
        scope = f" against item {problem_ref}" if problem_ref else ""
        return (
            f"Stored {item.memory_id}{scope} (private). "
            f"Publish it with: share_note | {item.memory_id}"
        )

    def _act_recall(self, agent_name: str, arguments: dict[str, Any], _: Invocation) -> str:
        problem_ref, query = self._memory_scope(arguments.get("problem_id"), arguments.get("query"))
        items = self.memory.recall(agent_name, query, problem_ref=problem_ref, top_k=8)
        if not items:
            return "Recall: nothing stored yet."
        return f"Recall ({len(items)} item(s)):\n{MemoryStore.render(items)}"

    def _act_share_note(self, agent_name: str, arguments: dict[str, Any], _: Invocation) -> str:
        text = str(arguments.get("note_id") or "")
        ids = [chunk for chunk in re.split(r"[,\s]+", text) if chunk]
        if not ids:
            return "Memory error: name the memory ids to publish, e.g. M1, M2."
        try:
            published = self.memory.publish(agent_name, ids, turn=self.current_turn)
        except KeyError as exc:
            return f"Memory error: {exc}"
        names = ", ".join(item.memory_id for item in published)
        return f"Published to the team as {names}."

    def _memory_scope(self, problem_id: Any, text: Any) -> tuple[str, str]:
        """Resolve an optional board reference; an unresolvable one is just text."""
        text = str(text or "").strip()
        ref = str(problem_id or "").strip()
        if not ref:
            return "", text
        item = self.workboard.resolve(ref) if self.workboard is not None else None
        if item is None:
            return "", f"{ref} {text}".strip()
        return item.item_id, text

    def _act_direct_message(
        self, agent_name: str, arguments: dict[str, Any], _: Invocation
    ) -> str | tuple[str, dict[str, Any]]:
        audience, message, error = self._resolve_recipients(
            arguments.get("recipients") or [], str(arguments.get("content") or "")
        )
        if error:
            return error
        self.group_messages.append(
            {
                "turn": self.current_turn,
                "sender": agent_name,
                "recipients": audience,
                "message": message,
                "visibility": "group",
            }
        )
        return (
            f"Message sent to {', '.join(audience)}.",
            {"visibility": "group", "recipients": audience},
        )

    def _act_check_budget(self, agent_name: str, _: dict[str, Any], __: Invocation) -> str:
        return self._check_budget(agent_name)

    def _act_query_rules(self, agent_name: str, _: dict[str, Any], __: Invocation) -> str:
        return self.query_rules(agent_name)

    def _act_submit(self, agent_name: str, arguments: dict[str, Any], _: Invocation) -> str:
        payload = self._resolve_final_payload(str(arguments.get("answer") or ""))
        error = self._validate_submission(payload)
        if error:
            return error
        evaluation = self.problem_data.get("evaluation") or {}
        is_programming = self.problem_data.get("task_type") in {
            "algorithmic_programming",
            "programming",
        } or evaluation.get("evaluator_id") == "programming_judge"
        from judge.vjudge_gateway_client import gateway_enabled

        if is_programming and gateway_enabled():
            result = self._submit_code(payload, agent_name=agent_name)
            self._record_shared_code_submission(agent_name, payload, result)
            return result
        self.workspace["final_answer"] = payload.strip()
        self.submitted = True
        self.submitted_by = agent_name
        return f"Submission finalized by {agent_name}.{self._board_submission_note()}"

    def _act_tool(self, agent_name: str, arguments: dict[str, Any], invocation: Invocation) -> str:
        key = invocation.spec.primary_argument if invocation.spec else None
        payload = str(arguments.get(key) or "") if key else invocation.text_payload
        dispatched = dispatch_environment_action(
            self, agent_name=agent_name, action_name=invocation.action, payload=payload
        )
        if dispatched is NotImplemented:
            return f"Operational error: action '{invocation.action}' not implemented."
        return str(dispatched)

    def get_private_notes(self, agent_name: str) -> str:
        return self.private_notes.get(agent_name, "")

    # ------------------------------------------------------------- workboard

    def register_agents(self, names: list[str]) -> None:
        """Record the roster so claims and direct messages can be checked."""
        self.agent_names = [str(name) for name in names if str(name).strip()]
        for name in self.agent_names:
            self.memory.private.setdefault(name, {})

    def board_enabled(self) -> bool:
        return self.workboard is not None

    def board_answer_sheet(self) -> str:
        """Recorded per-item answers, rendered as a numbered sheet."""
        return self.workboard.answer_sheet() if self.workboard is not None else ""

    def board_overview(self, agent_name: str | None = None) -> str:
        if self.workboard is None:
            return ""
        return self.workboard.overview(
            turn=self.current_turn, agent_name=agent_name
        )

    def _sync_answer_sheet(self) -> None:
        """Keep the shared workspace showing what the board currently holds."""
        if self.workboard is None:
            return
        self.workspace["answer_sheet"] = self.workboard.answer_sheet()

    def _board_unavailable(self) -> str:
        return (
            "Board unavailable: this contest is graded as a single "
            "deliverable, so there are no separate items to pick up. "
            "Use submit for the team's answer."
        )

    def _board_item(self, problem_id: Any) -> tuple[Any, str]:
        """Resolve a board reference into (item, "") or (None, error)."""
        if self.workboard is None:
            return None, self._board_unavailable()
        ref = str(problem_id or "").strip()
        item = self.workboard.resolve(ref)
        if item is None:
            return None, self.workboard.unknown_ref_message(ref)
        return item, ""

    def _held_item(self, agent_name: str) -> Any:
        """The board item this agent currently holds a live claim on, if any."""
        if self.workboard is None:
            return None
        for item in self.workboard.items.values():
            if item.holder(self.current_turn, self.workboard.claim_ttl_turns) == agent_name:
                return item
        return None

    def _broadcast_board_event(
        self, agent_name: str, event: str, item: Any, result: str
    ) -> None:
        """Put board changes in the shared log; a private board coordinates nothing."""
        if result.startswith("Board error:"):
            return
        if event == "work":
            summary = (
                f"{agent_name} recorded an answer for {item.item_id}: "
                f"{item.answer} (attempt {len(item.attempts)})."
            )
        elif event == "select_problem":
            summary = f"{agent_name} is now working on {item.item_id}."
        elif event == "skip_problem":
            summary = f"{agent_name} released {item.item_id}."
        elif event == "verify_problem":
            review = item.reviews[-1]
            summary = (
                f"{agent_name} reviewed {item.item_id} ({review.verdict})"
                + (f": {review.comment}" if review.comment else ".")
            )
        elif event == "mark_hopeless":
            summary = (
                f"{agent_name} marked {item.item_id} hopeless."
                if item.hopeless
                else f"{agent_name} put {item.item_id} back in play."
            )
        elif event == "set_priority":
            summary = f"{agent_name} set {item.item_id} priority to {item.priority}."
        else:
            return
        self.chat_history.append(
            {"sender": "Contest_Control", "message": f"[board] {summary}"}
        )

    def _check_budget(self, agent_name: str) -> str:
        state = self.get_state()
        lines = [
            "=== BUDGET ===",
            f"Turns (time): {state['turn_status']}",
            f"API calls (cost): {state['api_call_status']}",
            f"Team output tokens: {state['token_status']}",
            f"Clock: {state['clock_status']}",
        ]
        if self.wrong_submissions:
            lines.append(
                f"Wrong submissions: {self.wrong_submissions} "
                f"(penalty {self.penalty_minutes()} min)"
            )
        if self.workboard is not None:
            metrics = self.workboard.metrics()
            remaining = self.max_turns - self.current_turn
            unanswered = metrics["items_unanswered"]
            lines.append(
                f"Board: {metrics['items_answered']}/{metrics['items_total']} "
                f"answered, {unanswered} blank, "
                f"{metrics['repeat_attempts_rejected']} repeat attempt(s) rejected"
            )
            if unanswered:
                lines.append(
                    f"{remaining} turn(s) left for {unanswered} unanswered item(s) "
                    "across the whole team. A blank item scores zero."
                )
        return "\n".join(lines)

    def _resolve_recipients(
        self, recipients: list[str], message: str
    ) -> tuple[list[str], str, str]:
        """Check a direct message's audience against the roster."""
        requested = [str(name).strip() for name in recipients if str(name).strip()]
        message = str(message or "").strip()
        if not requested:
            return (
                [],
                "",
                "Board error: direct_message needs "
                "'<recipients> | <message>', e.g. Agent_2, Agent_3 | ...",
            )
        if not message:
            return [], "", "Board error: the message body is empty."
        if self.agent_names:
            lookup = {name.lower(): name for name in self.agent_names}
            resolved, unknown = [], []
            for name in requested:
                match = lookup.get(name.lower())
                (resolved if match else unknown).append(match or name)
            if unknown:
                return (
                    [],
                    "",
                    f"Board error: unknown recipient(s) {', '.join(unknown)}. "
                    f"Team: {', '.join(self.agent_names)}",
                )
            requested = resolved
        return sorted(set(requested)), message, ""

    def _run_web_search(self, payload: str) -> str:
        """Live search with contest policy + answer-key anti-cheat."""
        policy = self.contest_rules.search_policy if self.contest_rules else "forbidden"
        query = (payload or "").strip()
        if policy == "forbidden":
            msg = "RULE VIOLATION: web_search is banned for this contest."
            self.rule_violations.append(msg)
            return msg
        if policy == "judge_only":
            msg = (
                "RULE VIOLATION: only the online judge network is allowed "
                "(no open web search)."
            )
            self.rule_violations.append(msg)
            return msg
        if looks_like_answer_lookup(query):
            msg = (
                "RULE VIOLATION: search query looks like an answer-key lookup "
                f"(policy={policy}). Query blocked."
            )
            self.rule_violations.append(msg)
            return msg
        try:
            report = live_web_search(query)
            if policy == "no_solution_lookup":
                report += (
                    "\n[policy=no_solution_lookup] Do not search solution methods "
                    "or official answers."
                )
            return report
        except Exception as exc:
            return f"web_search error: {exc}"

    def _tool_asset_text(self, role_substring: str, payload: str) -> str | None:
        """Load text/JSON assets from problem metadata for lab/star tools."""
        needle = role_substring.lower()
        for asset in self.problem_data.get("assets") or []:
            role = str(asset.get("role") or "").lower()
            path_text = str(asset.get("path") or "")
            if needle not in role and needle not in path_text.lower():
                continue
            path = Path(path_text)
            if not path.is_absolute():
                path = Path(REPO_ROOT) / path
            if path.is_file():
                return path.read_text(encoding="utf-8", errors="replace")[:8000]
        fixtures = self.problem_data.get("tool_fixtures") or {}
        key = payload.strip() or role_substring
        if key in fixtures:
            return str(fixtures[key])[:8000]
        if role_substring in fixtures:
            return str(fixtures[role_substring])[:8000]
        return None

    def _submit_code(self, payload: str, *, agent_name: str) -> str:
        """Use the remote judge when configured, otherwise fall back locally."""
        from judge.vjudge_gateway_client import gateway_enabled

        self.submission_attempts += 1
        if gateway_enabled():
            remote = self._maybe_vjudge_remote_submit(
                payload,
                local_language="python3",
            ) or {"status": "failed", "verdict": "SUBMIT_FAILED"}
            self.remote_submission = remote
            self.remote_submission_source = payload.strip()
            remote_status = str(remote.get("status") or "")
            remote_verdict = str(remote.get("verdict") or "")
            if remote_status == "final" and remote_verdict == "AC":
                self.workspace["final_answer"] = payload.strip()
                self.submitted = True
                self.submitted_by = agent_name
            elif remote_status == "final":
                self.record_wrong_submission()
            elif remote_status == "needs_human":
                self.workspace["final_answer"] = payload.strip()
                self.submitted = True
                self.submitted_by = agent_name

            feedback = {
                "action": "submit_code",
                "attempt": self.submission_attempts,
                "verdict": remote_verdict or "PENDING",
                "test_scope": "remote",
                "grading_scope_label": "remote official judge",
                "passed": 1 if remote_verdict == "AC" else 0,
                "total": 1,
                "finalized": self.submitted,
                "penalty_minutes": self.penalty_minutes(),
                "simulated_minutes": self.simulated_minutes,
                "continue_allowed": not self.submitted and self.can_begin_turn(),
                "remote": remote,
            }
            if self.submitted and remote_verdict == "AC":
                feedback["note"] = "Remote judge AC; submission finalized."
            elif self.submitted and remote_status == "needs_human":
                feedback["note"] = (
                    "Remote judge requires human verification; run paused with this "
                    "candidate preserved."
                )
            return json.dumps(feedback, sort_keys=True)

        from evaluation.programming_judge import judge_programming_submission

        judged = judge_programming_submission(
            self.problem_data,
            payload,
            competition_id=self.competition_id,
            repo_root=Path(REPO_ROOT),
            fetch_kattis=False,
            test_scope="sample",
        )
        if judged.wrong_submission:
            self.record_wrong_submission()
        feedback = judged.to_dict()
        feedback.update(
            {
                "action": "submit_code",
                "attempt": self.submission_attempts,
                "finalized": self.submitted,
                "penalty_minutes": self.penalty_minutes(),
                "simulated_minutes": self.simulated_minutes,
                "continue_allowed": not self.submitted and self.can_begin_turn(),
            }
        )
        if judged.verdict == "AC":
            feedback["note"] = (
                "Sample AC only; final hidden tests may still reject this solution."
            )
        return json.dumps(feedback, sort_keys=True)

    def _maybe_vjudge_remote_submit(
        self, answer: str, *, local_language: str
    ) -> dict[str, Any] | None:
        """Optionally forward the final source to the local VJudge gateway."""
        from judge.vjudge_gateway_client import (
            extract_source_and_language,
            gateway_enabled,
            submit_via_gateway,
        )

        if not gateway_enabled():
            return None
        evaluation = self.problem_data.get("evaluation") or {}
        mode = (
            os.environ.get("VJUDGE_SUBMIT_MODE")
            or str(evaluation.get("vjudge_submit_mode") or "problem")
        ).strip().lower()
        oj = (
            str(evaluation.get("vjudge_oj") or "").strip()
            or os.environ.get("VJUDGE_OJ", "").strip()
        )
        prob_num = (
            str(evaluation.get("vjudge_prob_num") or "").strip()
            or str(self.problem_data.get("codeforces_id") or "").strip()
            or str(self.problem_data.get("kattis_id") or "").strip()
        )
        if not oj:
            if self.problem_data.get("codeforces_id"):
                oj = "CodeForces"
            elif self.problem_data.get("kattis_id"):
                oj = "Kattis"
            else:
                oj = "CodeForces"
        contest_id = (
            str(evaluation.get("vjudge_contest_id") or "").strip()
            or os.environ.get("VJUDGE_CONTEST_ID", "").strip()
        )
        contest_letter = (
            str(evaluation.get("vjudge_problem") or "").strip()
            or os.environ.get("VJUDGE_PROBLEM", "").strip()
        )
        # Default: submit by OJ problem id (no private contest).
        use_contest = mode == "contest" and bool(contest_id)
        if use_contest:
            problem = contest_letter or "A"
            oj_for_request = oj
            contest_for_request = contest_id
        else:
            problem = prob_num or contest_letter
            oj_for_request = oj
            contest_for_request = ""
            if not problem:
                return {
                    "status": "failed",
                    "error": (
                        "VJudge problem-mode needs evaluation.vjudge_prob_num "
                        "or codeforces_id on the benchmark record"
                    ),
                }
        source, language = extract_source_and_language(answer, fallback=local_language)
        key = (
            f"{id(self)}:{self.competition_id}:{self.problem_id}:"
            f"{self.submission_attempts}"
        )
        return submit_via_gateway(
            contest_id=contest_for_request,
            oj=oj_for_request,
            problem=problem,
            language=language,
            source=source,
            idempotency_key=key,
            poll=True,
        )

    def record_wrong_submission(self) -> None:
        """WA/TLE/RE: burn contest clock (remove remaining time), don't stack a bonus.

        Real ICPC ranking adds 20 min to the time score; in this simulator we model
        the cost as consuming 20 minutes of the remaining shared contest clock so
        teams have less time left to keep working.
        """
        self.wrong_submissions += 1
        rules = self.contest_rules
        if not rules or rules.wrong_submission_penalty_minutes is None:
            self.record_budget_snapshot("wrong_submission")
            return
        burn = float(rules.wrong_submission_penalty_minutes)
        self.simulated_minutes += burn
        step = float(
            self.budget.clock_minutes_per_turn
            or self.minutes_per_turn
            or 5.0
        )
        if step > 0:
            turns_burned = max(1, int(math.ceil(burn / step)))
            self.current_turn = min(self.max_turns, self.current_turn + turns_burned)
        self.record_budget_snapshot("wrong_submission")

    def penalty_minutes(self) -> int | None:
        """Minutes of contest clock burned by wrong submissions so far."""
        rules = self.contest_rules
        if not rules or rules.wrong_submission_penalty_minutes is None:
            return None
        return self.wrong_submissions * rules.wrong_submission_penalty_minutes

    def _resolve_final_payload(self, payload: str) -> str:
        """Back the submitted answer with what the team recorded on the board.

        The submitter's own text wins — synthesis is asked to recompute, not to
        copy. But an item the team recorded and the submitter dropped would
        score zero for no reason, and a submitter that returns commentary or a
        stray ACTION line would throw the whole board away.
        """
        from evaluation.gold import parse_numbered_answers

        text = str(payload or "").strip()
        if self.workboard is None:
            return payload
        recorded = {
            item.item_id: item.answer
            for item in self.workboard.items.values()
            if item.answered
        }
        if not recorded:
            return payload
        sheet = self.workboard.answer_sheet()
        if len(text) < 10 or text.lower() in {"submit", "final", "done", "ready"}:
            return sheet
        written = parse_numbered_answers(text)
        if not written:
            return sheet
        missing = [
            f"{item_id}. {answer}"
            for item_id, answer in recorded.items()
            if not str(written.get(item_id) or "").strip()
        ]
        if not missing:
            return payload
        return (
            f"{text.rstrip()}\n\nRecorded on the board and not covered above:\n"
            + "\n".join(missing)
        )

    def _board_submission_note(self) -> str:
        if self.workboard is None:
            return ""
        blank = [
            item.item_id
            for item in self.workboard.items.values()
            if not item.answered
        ]
        if not blank:
            return " All board items have a recorded answer."
        listed = ", ".join(blank[:10]) + ("..." if len(blank) > 10 else "")
        return f" Board items with no recorded answer: {listed}."

    def _validate_submission(self, payload: str) -> Optional[str]:
        if not payload or not payload.strip():
            return "Submission rejected: final answer cannot be empty."
        if len(payload.strip()) < 10:
            # The floor exists to reject "ok" / "done", not a short answer
            # sheet: "1. 268" is a complete submission on a one-item board.
            from evaluation.gold import parse_numbered_answers

            if self.workboard is not None and parse_numbered_answers(payload):
                return None
            return "Submission rejected: final answer is too short (minimum 10 characters)."
        return None

    @staticmethod
    def _safe_calculate(expression: str) -> str:
        try:
            node = ast.parse(expression.strip(), mode="eval")
            value = OlympiadEnvironment._eval_ast(node.body)
            return str(value)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
            return f"Calculator error: {exc}"

    @staticmethod
    def _eval_ast(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_BINOPS:
            left = OlympiadEnvironment._eval_ast(node.left)
            right = OlympiadEnvironment._eval_ast(node.right)
            return float(_SAFE_BINOPS[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_UNARYOPS:
            return float(_SAFE_UNARYOPS[type(node.op)](OlympiadEnvironment._eval_ast(node.operand)))
        raise ValueError("Only basic arithmetic expressions are allowed.")

    def _run_calculator(self, payload: str) -> str:
        return f"Calculator output: {self._safe_calculate(payload)}"

    def _run_code(self, payload: str) -> str:
        from isolated_python import IsolationUnavailable, run_python_isolated
        try:
            proc = run_python_isolated(payload)
            if proc.timed_out:
                return "Code error: execution timed out after 5 seconds."
            if proc.output_limited:
                return "Code error: output limit exceeded."
            if proc.returncode == 0:
                output = (proc.stdout or "").strip() or "(no stdout)"
                return f"Code output:\n{output}"
            stderr = (proc.stderr or proc.stdout or "unknown error").strip()
            return f"Code error (exit {proc.returncode}):\n{stderr}"
        except IsolationUnavailable as exc:
            return f"Operational error: {exc}"

    @staticmethod
    def _normalize_answer(text: str) -> str:
        return " ".join(text.lower().split())

    def grade_submission(self) -> dict:
        if not self.submitted:
            return {
                "graded": False,
                "reason": "No submission yet.",
                "score": None,
                "max_score": None,
            }

        answer = self.workspace["final_answer"]
        gold = self.problem_data.get("gold_label", {}) or {}
        expected = gold.get("expected_answer")
        rubric = gold.get("grading_rubric") or ""
        evaluation = self.problem_data.get("evaluation") or {}

        # Prefer structured curated short answers when present.
        parts = gold.get("parts") or []
        if any(str(p.get("expected") or "").strip() for p in parts):
            try:
                from evaluation.gold import GoldAnswerEvaluator, load_gold_parts

                result = GoldAnswerEvaluator(
                    parts=load_gold_parts(gold),
                    submission_text=answer,
                ).evaluate()
                return {
                    "graded": True,
                    "method": "gold_answer_v1",
                    "score": result.total_score,
                    "max_score": result.max_score,
                    "correct": result.total_score >= result.max_score,
                    "evaluation": result.to_dict(),
                    "submitted_by": self.submitted_by,
                }
            except Exception as exc:
                # Fall through to other graders.
                gold_error = str(exc)
        else:
            gold_error = None

        task_type = self.problem_data.get("task_type", "")
        if task_type in {"algorithmic_programming", "programming"} or evaluation.get(
            "evaluator_id"
        ) == "programming_judge":
            from judge.vjudge_gateway_client import gateway_enabled

            remote = (
                self.remote_submission
                if self.remote_submission_source == answer.strip()
                else self._maybe_vjudge_remote_submit(
                    answer,
                    local_language="python3",
                )
                if gateway_enabled()
                else None
            )
            if remote is not None:
                status = str(remote.get("status") or "")
                verdict = str(remote.get("verdict") or "")
                is_final = status == "final"
                is_ac = is_final and verdict == "AC"
                return {
                    "graded": is_final,
                    "method": "vjudge_remote",
                    "score": 1.0 if is_ac else 0.0 if is_final else None,
                    "max_score": 1.0,
                    "correct": is_ac,
                    "verdict": verdict,
                    "remote": remote,
                    "penalty_minutes": self.penalty_minutes(),
                    "simulated_minutes": self.simulated_minutes,
                    "submitted_by": self.submitted_by,
                }

            from evaluation.programming_judge import judge_programming_submission

            judged = judge_programming_submission(
                self.problem_data,
                answer,
                competition_id=self.competition_id,
                repo_root=Path(REPO_ROOT),
                fetch_kattis=True,
            )
            if judged.wrong_submission:
                self.record_wrong_submission()
            grade = judged.to_grade_dict(submitted_by=self.submitted_by)
            grade["penalty_minutes"] = self.penalty_minutes()
            grade["simulated_minutes"] = self.simulated_minutes
            grade["clock_burned_by_wa"] = bool(judged.wrong_submission)
            if judged.verdict == "AC":
                # Clock already includes any prior WA burns; do not add again.
                grade["icpc_time_score"] = int(self.simulated_minutes)
            return grade

        if expected:
            norm_answer = self._normalize_answer(answer)
            norm_gold = self._normalize_answer(str(expected))
            if norm_gold in norm_answer or norm_answer in norm_gold:
                return {
                    "graded": True,
                    "method": "gold_substring_match",
                    "score": 1.0,
                    "max_score": 1.0,
                    "correct": True,
                    "submitted_by": self.submitted_by,
                }
            return {
                "graded": True,
                "method": "gold_substring_match",
                "score": 0.0,
                "max_score": 1.0,
                "correct": False,
                "submitted_by": self.submitted_by,
                "note": "Answer did not match gold via substring check; use LLM judge for partial credit.",
            }

        payload = {
            "graded": False,
            "method": "llm_judge_required",
            "score": None,
            "max_score": None,
            "reason": "No exact gold answer on file; use LLM or human judge.",
            "grading_rubric": rubric,
            "submitted_by": self.submitted_by,
        }
        if gold_error:
            payload["gold_error"] = gold_error
        return payload

    def reset(self) -> None:
        self.chat_history.clear()
        self.group_messages.clear()
        self.action_log.clear()
        self.agent_observations.clear()
        self.code_submissions.clear()
        self.private_thoughts.clear()
        self.protocol_action_counts.clear()
        self.budget_snapshots.clear()
        self.deliberation.reset()
        self.communication.reset()
        self.private_notes.clear()
        self.workspace = {
            "scratchpad": "",
            "final_answer": "",
            "work_artifacts": [],
            "answer_sheet": "",
        }
        self.current_turn = 0
        self.simulated_minutes = 0.0
        self.action_count = 0
        self.api_calls = 0
        self.tokens_used = 0
        self.api_calls_by_turn.clear()
        self.tokens_by_turn.clear()
        self.submitted = False
        self.submitted_by = None
        self.wrong_submissions = 0
        self.submission_attempts = 0
        self.remote_submission = None
        self.remote_submission_source = None
        self.rule_violations.clear()
        self.workboard = Workboard.from_problem(self.problem_data)
        self.memory = MemoryStore(self.agent_names)
        self.record_budget_snapshot("reset")
