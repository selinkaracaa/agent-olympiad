import ast
import json
import math
import operator
import os
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
from deliberation import DELIBERATION_ACTIONS, DeliberationLedger
from rules import RulesBaseline, RulesMode
from tools_search import live_web_search, looks_like_answer_lookup

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
    "codeforces": 1,
}

COMPETITION_TOOL_REGISTRY = {
    "purple_comet": ["use_calculator"],
    "fyziklani": ["use_calculator", "web_search"],
    "iiot": ["execute_code"],
    "icpc": ["execute_code"],
    "codeforces": ["execute_code"],
    "mcm": ["execute_code", "web_search"],
    "icm": ["execute_code", "web_search"],
    "ieo_business_case": ["web_search"],
    "jessup": ["web_search"],
    "iypt": ["web_search", "execute_code", "use_calculator"],
    "ijso_practical": ["use_calculator", "read_lab_equipment"],
    "ioaa_group": ["use_calculator", "read_star_chart"],
    "iol_team": [],
    "arml_power": [],
    "arml_national_team": [],
    "arml_national_power": [],
    "arml_local": [],
    "hmmt_team": [],
    "hmmt_guts": [],
    "wsc_writing": [],
}

COMPETITION_ACTION_REGISTRY = {
    "icpc": ["submit_code"],
    "iiot": ["submit_code"],
    "codeforces": ["submit_code"],
}

ALL_ACTIONS = {
    "speak",
    "write_scratchpad",
    "write_private_notes",
    "submit_final",
    "submit_code",
    "sleep",
    "use_calculator",
    "execute_code",
    "web_search",
    "read_lab_equipment",
    "read_star_chart",
    "query_rules",
} | DELIBERATION_ACTIONS

TOOL_ACTIONS = ALL_ACTIONS - {
    "speak",
    "write_scratchpad",
    "write_private_notes",
    "submit_final",
    "submit_code",
    "sleep",
    *DELIBERATION_ACTIONS,
}

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
        self.action_log: list[dict[str, Any]] = []
        self.agent_observations: dict[str, list[dict[str, Any]]] = {}
        self.code_submissions: list[dict[str, Any]] = []
        self.budget_snapshots: list[dict[str, Any]] = []
        self.deliberation = DeliberationLedger()
        self.communication = CommunicationBudget(
            self.rule_card.communication
            if self.rule_card is not None and self.rules_mode is RulesMode.ENFORCED
            else {}
        )
        self.private_notes: dict[str, str] = {}
        self.workspace = {"scratchpad": "", "final_answer": ""}
        self.current_turn = 0  # collaboration turns completed
        self.action_count = 0  # env actions executed (speak/tools/etc.)
        self.api_calls = 0  # LLM calls made by collaboration layer
        self.tokens_used = 0  # estimated output tokens consumed
        self.submitted = False
        self.submitted_by: Optional[str] = None
        self.wrong_submissions = 0
        self.submission_attempts = 0
        self.rule_violations: list[str] = []
        self.contest_rules = get_contest_rules(competition_id)

        if self.rule_card is not None and self.rules_mode is RulesMode.ENFORCED:
            self.unavailable_declared_tools = sorted(
                set(self.rule_card.allowed_tools) - TOOL_ACTIONS
            )
            self.allowed_tools = [
                tool for tool in self.rule_card.allowed_tools if tool in TOOL_ACTIONS
            ]
        else:
            self.unavailable_declared_tools = []
            self.allowed_tools = list(COMPETITION_TOOL_REGISTRY.get(competition_id, []))
        # Prefer tools declared in the rules audit when registry is empty but
        # rules list encoded tools (keeps DATA_COLLECTION + contest_rules aligned).
        if (
            self.rules_mode is not RulesMode.ENFORCED
            and not self.allowed_tools
            and self.contest_rules
            and self.contest_rules.encoded_tools
        ):
            self.allowed_tools = list(self.contest_rules.encoded_tools)
        self.problem_data = self._load_problem()

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

    def _shared_team_state_keys(self) -> set[str]:
        if self.rules_mode is not RulesMode.ENFORCED or self.rule_card is None:
            return set()
        simulation = self.rule_card.simulation or {}
        raw = simulation.get("shared_team_state") or ()
        return {str(item) for item in raw}

    def submit_code_is_team_visible(self) -> bool:
        """ICPC card shares pending_run_status with the whole team."""
        return "pending_run_status" in self._shared_team_state_keys()

    def _action_visibility(self, action_type: str) -> str:
        if action_type in {"write_private_notes", *TOOL_ACTIONS}:
            return "private"
        if action_type == "submit_code":
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
        entry = {
            "turn": self.current_turn,
            "agent": agent_name,
            "verdict": feedback.get("verdict"),
            "test_scope": feedback.get("test_scope"),
            "grading_scope_label": feedback.get("grading_scope_label"),
            "reason": feedback.get("reason"),
            "passed": feedback.get("passed"),
            "total": feedback.get("total"),
            "finalized": bool(feedback.get("finalized")),
            "code": payload.strip(),
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
            "rule_violations": list(self.rule_violations),
            "deliberation": self.deliberation.report(),
            "communication": self.communication.report(),
            "rules_baseline": self.rules_metadata(),
        }

    def turns_exhausted(self) -> bool:
        """True when no further collaboration turns may be started."""
        return self.current_turn >= self.max_turns

    def can_begin_turn(self) -> bool:
        if self.current_turn >= self.max_turns:
            return False
        # WA penalties burn remaining contest clock; stop when duration is spent.
        if (
            self.duration_minutes is not None
            and self.simulated_minutes >= float(self.duration_minutes)
        ):
            return False
        return True

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
        self.tokens_used += estimate_tokens(capped)
        return capped

    def begin_turn(self) -> int:
        """Start a collaboration turn (time step). Raises if turn budget is spent."""
        if not self.can_begin_turn():
            raise TurnLimitExceededError(
                f"Turn limit reached ({self.max_turns}) for {self.problem_id}"
            )
        self.current_turn += 1
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
        self.record_budget_snapshot("api_call")

    def _log_action(self, agent_name: str, action_type: str, payload: str, result: str) -> None:
        visibility = self._action_visibility(action_type)
        entry = {
            "turn": self.current_turn,
            "agent": agent_name,
            "sender": agent_name,
            "action": action_type,
            "payload": payload,
            "result": result,
            "visibility": visibility,
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
        elif action_type == "submit_code":
            roster = (
                [role.name for role in self.rule_card.agent_roles]
                if self.rule_card is not None
                else [agent_name]
            )
            for peer in roster:
                self.agent_observations.setdefault(peer, []).append(observation)

    def validate_action(self, action_type: str, agent_name: str | None = None) -> Optional[str]:
        if action_type not in ALL_ACTIONS:
            return f"Unrecognized action '{action_type}'."
        if (
            self.rules_mode is not RulesMode.ENFORCED
            and action_type in DELIBERATION_ACTIONS | {"write_private_notes"}
        ):
            return f"Unrecognized action '{action_type}'."
        if (
            self.rules_mode is not RulesMode.PROMPT_ONLY
            and action_type in TOOL_ACTIONS
            and action_type not in self.allowed_tools
        ):
            return (
                f"RULE VIOLATION: Tool '{action_type}' is banned in {self.competition_id}. "
                f"Allowed tools: {self.allowed_tools or 'none (paper and pencil only)'}"
            )
        if action_type == "submit_code" and action_type not in COMPETITION_ACTION_REGISTRY.get(
            self.competition_id, []
        ):
            return f"RULE VIOLATION: submit_code is unavailable in {self.competition_id}."
        if (
            self.rules_mode is RulesMode.ENFORCED
            and action_type in DELIBERATION_ACTIONS
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
            and action_type == "submit_final"
            and agent_name is not None
            and self.rule_card is not None
        ):
            role = self.rule_card.role_for(agent_name)
            if role is None or not role.may_submit:
                return f"RULE VIOLATION: {agent_name} is not authorized to submit."
        if action_type == "submit_final" and self.submitted:
            return "Submission already finalized; further submit_final actions are ignored."
        return None

    def execute_action(self, agent_name: str, action_type: str, payload: str) -> str:
        self.action_count += 1

        violation = self.validate_action(action_type, agent_name)
        if violation:
            self.rule_violations.append(violation)
            self._log_action(agent_name, action_type, payload, violation)
            return violation

        communication_violation = self.communication.check(
            agent_name=agent_name,
            action_type=action_type,
            payload=payload,
            turn=self.current_turn,
        )
        if communication_violation:
            self.rule_violations.append(communication_violation)
            self._log_action(agent_name, action_type, payload, communication_violation)
            return communication_violation

        if action_type == "speak":
            self.chat_history.append({"sender": agent_name, "message": payload})
            result = "Message broadcast to all agents."
        elif action_type == "write_scratchpad":
            self.workspace["scratchpad"] = payload
            result = "Shared scratchpad updated."
        elif action_type == "write_private_notes":
            self.private_notes[agent_name] = payload
            result = "Private notes updated; no communication budget used."
        elif action_type in DELIBERATION_ACTIONS:
            role = self.rule_card.role_for(agent_name) if self.rule_card else None
            result = self.deliberation.record(
                agent_name=agent_name,
                action_type=action_type,
                payload=payload,
                turn=self.current_turn,
                may_decide=bool(role and role.may_submit),
            )
        elif action_type == "sleep":
            reason = payload.strip() or "passing this turn"
            result = f"{agent_name} sleeps ({reason})."
        elif action_type == "submit_final":
            error = self._validate_submission(payload)
            if error:
                result = error
            else:
                self.workspace["final_answer"] = payload.strip()
                self.submitted = True
                self.submitted_by = agent_name
                result = f"Submission finalized by {agent_name}."
        elif action_type == "submit_code":
            result = self._submit_code(payload)
            if not result.startswith("RULE VIOLATION"):
                self._record_shared_code_submission(agent_name, payload, result)
        elif action_type == "use_calculator":
            result = self._run_calculator(payload)
        elif action_type == "execute_code":
            result = self._run_code(payload)
        elif action_type == "web_search":
            result = self._run_web_search(payload)
        elif action_type == "read_lab_equipment":
            loaded = self._tool_asset_text("lab", payload)
            result = (
                f"[read_lab_equipment]\n{loaded}"
                if loaded
                else (
                    f"[read_lab_equipment] No fixture for {payload!r}. "
                    "Add problem assets/tool_fixtures with lab readings."
                )
            )
        elif action_type == "read_star_chart":
            loaded = self._tool_asset_text("star", payload)
            result = (
                f"[read_star_chart]\n{loaded}"
                if loaded
                else (
                    f"[read_star_chart] No fixture for {payload!r}. "
                    "Add problem assets/tool_fixtures with chart data."
                )
            )
        elif action_type == "query_rules":
            result = self.query_rules(agent_name)
        else:
            result = f"Operational error: action '{action_type}' not implemented."

        if not result.startswith("Deliberation error:"):
            self.communication.record(agent_name=agent_name, action_type=action_type)
        else:
            self.rule_violations.append(result)
        self._log_action(agent_name, action_type, payload, result)
        return result

    def get_private_notes(self, agent_name: str) -> str:
        return self.private_notes.get(agent_name, "")

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

    def _submit_code(self, payload: str) -> str:
        """Judge a non-final programming attempt on public sample tests."""
        from evaluation.programming_judge import judge_programming_submission

        self.submission_attempts += 1
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
                "finalized": False,
                "penalty_minutes": self.penalty_minutes(),
                "simulated_minutes": self.simulated_minutes,
                "continue_allowed": self.can_begin_turn(),
            }
        )
        if judged.verdict == "AC":
            feedback["note"] = (
                "Sample AC only; final hidden tests may still reject this solution."
            )
        return json.dumps(feedback, sort_keys=True)

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

    def _validate_submission(self, payload: str) -> Optional[str]:
        if not payload or not payload.strip():
            return "Submission rejected: final answer cannot be empty."
        if len(payload.strip()) < 10:
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
        try:
            proc = subprocess.run(
                [sys.executable, "-c", payload],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=REPO_ROOT,
            )
            if proc.returncode == 0:
                output = (proc.stdout or "").strip() or "(no stdout)"
                return f"Code output:\n{output}"
            stderr = (proc.stderr or proc.stdout or "unknown error").strip()
            return f"Code error (exit {proc.returncode}):\n{stderr}"
        except subprocess.TimeoutExpired:
            return "Code error: execution timed out after 5 seconds."
        except OSError as exc:
            return f"Code error: {exc}"

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
        self.action_log.clear()
        self.agent_observations.clear()
        self.code_submissions.clear()
        self.budget_snapshots.clear()
        self.deliberation.reset()
        self.communication.reset()
        self.private_notes.clear()
        self.workspace = {"scratchpad": "", "final_answer": ""}
        self.current_turn = 0
        self.simulated_minutes = 0.0
        self.action_count = 0
        self.api_calls = 0
        self.tokens_used = 0
        self.submitted = False
        self.submitted_by = None
        self.wrong_submissions = 0
        self.submission_attempts = 0
        self.rule_violations.clear()
        self.record_budget_snapshot("reset")
