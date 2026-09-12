"""Private contest lifecycle: setup, coach, rounds, seat phases, and final result."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

import otc_runtime
from contest_actions import _is_answer_sheet_contest, _required_answer_sheet_task_ids, _set_work_assignment, _next_task, _task_has_independent_approval, _apply_action
from actions import parse_typed_action, validate_action_invocation
from contest_budget import estimate_tokens
from contest_manifest import ContestManifest
from contest_memory import ContestMemory
from contest_session import BudgetExceededError, ContestBudgetState, ContestSession, TaskUnit
from llm import LLMRequest, RequestFn
from programming_workflow import ProgrammingProgress
from rulecard_policy import WORKSTATION_ACTION_NAMES, clip_text
from rules.baseline import card_content_hash
from submission_policy import SubmissionPolicy
from strategy import StrategicPolicy
from tool_registry import ACTION_SET_VERSION, DESK_ACTION_NAMES, ActionSpec, render_function_tools

from contest_config import PROTOCOL_VERSION, CheckpointCallback, ContestRunConfig, QueryFn, TaskActionExecutor


from contest_prompts import _needs_programming_source, _shared_review_history, _reported_version_hashes, _system_prompt, _user_prompt

from contest_policy import _resolved_actions, _actions_for_agent, _leader_plan_prompts, _normalize_coach_plan, _card_focus_task, _scheduled_agent_task, _rejected_version_count

from contest_lifecycle import (
    _default_executor,
    _append_action_error,
    _record_scoreboard,
    _participation_metrics,
    _collect_programming_deadline,
)

@dataclass(slots=True)
class _AgentTurn:
    """State shared only by the phases of one seat's single action."""
    agent: str
    personal_assignment: dict[str, Any] | None = None
    work_task_ids: set[str] | None = None
    review_task_ids: set[str] | None = None
    programming_source_required: bool = False
    available_actions: frozenset[ActionSpec] = field(default_factory=frozenset)
    function_tools: tuple[dict[str, Any], ...] = ()
    system_prompt: str = ""
    user_prompt: str = ""
    action: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)

class _ContestEngine:
    """One run's mutable state; callers use the existing run function."""

    def __init__(
        self,
        manifest: ContestManifest,
        query_llm_fn: QueryFn,
        config: ContestRunConfig,
        *,
        action_request_fn: RequestFn | None = None,
        action_transport: Literal["native", "emulated", "prompt_json"] | None = None,
        coach_query_fn: QueryFn | None = None,
        task_action_executor: TaskActionExecutor | None = None,
        session_checkpoint: dict[str, Any] | None = None,
        memory_checkpoint: str | None = None,
        checkpoint_callback: CheckpointCallback | None = None,
    ) -> None:
        self.manifest = manifest
        self.query_llm_fn = query_llm_fn
        self.config = config
        self.action_request_fn = action_request_fn
        self.action_transport = action_transport
        self.coach_query_fn = coach_query_fn
        self.checkpoint_callback = checkpoint_callback
        self.wall_t0 = time.perf_counter()
        self.segment_started_at = datetime.now(timezone.utc).isoformat()
        if self.config.programming_deadline_submit and session_checkpoint and session_checkpoint.get("final_summary") is not None:
            raise ValueError("Cannot force-submit from a finalized checkpoint; start a fresh run")
        self.session = (
            ContestSession.from_checkpoint(session_checkpoint)
            if session_checkpoint is not None
            else ContestSession(
                [
                    TaskUnit(
                        task.task_id,
                        kind="programming" if task.programming else "non_programming",
                    )
                    for task in self.manifest.tasks
                ],
                ContestBudgetState(
                    max_turns=self.config.max_turns,
                    max_api_calls=self.config.max_api_calls,
                    max_tokens=self.config.max_tokens,
                    max_simulated_minutes=self.config.max_simulated_minutes,
                ),
                SubmissionPolicy(
                    consecutive_non_ac_limit=(
                        self.config.consecutive_non_ac_limit
                        if self.config.features.submission_cooldown
                        else (
                            (self.config.max_api_calls or self.config.max_turns * self.config.team_size)
                            + 1
                        )
                    ),
                    cooldown_turns=self.config.cooldown_turns,
                ),
            )
        )
        if not self.session.budget.wall_started_at:
            self.session.budget.wall_started_at = self.segment_started_at
        self.prior_wall_seconds = float(self.session.budget.wall_seconds_used or 0.0)

        if {task.task_id for task in self.session.tasks} != {
            task.task_id for task in self.manifest.tasks
        }:
            raise ValueError("session checkpoint task set does not match manifest")
        self.memory = (
            ContestMemory.from_checkpoint_json(
                memory_checkpoint,
                expected_run_id=f"{self.manifest.session_id}:{self.config.system_variant}",
                expected_session_id=self.manifest.session_id,
                expected_competition_id=self.manifest.competition_id,
            )
            if memory_checkpoint is not None
            else ContestMemory(
                run_id=f"{self.manifest.session_id}:{self.config.system_variant}",
                session_id=self.manifest.session_id,
                competition_id=self.manifest.competition_id,
            )
        )
        self.actions = _resolved_actions(self.manifest, self.config)
        self.action_transport_log: list[dict[str, Any]] = []
        self.transport_api_calls = 0
        self.transport_retries = 0
        self.transport_failures = 0
        self.executor = task_action_executor or _default_executor
        self.strategic_policy = StrategicPolicy(stall_turns=self.config.stall_turns)
        self.archived_events = self.memory.archival_snapshot()["events"]
        self.final_review_started = any(
            event["kind"] == "final_review_started" for event in self.archived_events
        )
        self.final_review_completed = any(
            event["kind"] == "final_review_completed" for event in self.archived_events
        )
        self.final_review_approvals = {
            str(event["task_id"]): str(event["payload"]["version_hash"])
            for event in self.archived_events
            if event["kind"] == "final_review_approved"
            and event.get("task_id")
            and event["payload"].get("version_hash")
        }
        coach_event = next(
            (
                event
                for event in reversed(self.archived_events)
                if event["kind"] == "precontest_coach_guidance"
            ),
            None,
        )
        self.coach_plan: dict[str, Any] = (
            dict(coach_event["payload"].get("plan") or {})
            if coach_event is not None
            else {}
        )
        self.coach_guidance = (
            str(coach_event["payload"].get("guidance") or "")
            if coach_event is not None
            else ""
        )
        self.coach_budget_exhausted = False

        self.policy = self.config.otc_policy
        self.card = self.config.rule_card if self.policy is not None else None
        if self.card is not None and self.config.features.basic_open_table:
            from basic_otc import basic_prompt_card
            self.card = basic_prompt_card(self.card)
        self.programming_contest = any(task.programming for task in self.manifest.tasks)
        if self.policy is not None and "submit_code" in self.policy.allowed_actions and not self.programming_contest:
            raise ValueError(
                f"rule card for {self.manifest.competition_id} allows submit_code but the "
                "manifest has no programming task"
            )
        self.opening_summary = ""
        self.opening_turn: int | None = None

    def _persist_checkpoint(self) -> None:
        self.session.budget.wall_seconds_used = self.prior_wall_seconds + (
            time.perf_counter() - self.wall_t0
        )
        if self.checkpoint_callback:
            self.checkpoint_callback(self.session.checkpoint(), self.memory.to_checkpoint_json())

    def _charge_tokens(self, text: str) -> bool:
        """Charge estimated tokens; False when the token budget ran dry."""
        count = estimate_tokens(text)
        remaining = (
            None
            if self.session.budget.max_tokens is None
            else max(0, self.session.budget.max_tokens - self.session.budget.tokens_used)
        )
        charged = count if remaining is None else min(count, remaining)
        self.session.consume_budget(tokens=charged)
        return charged >= count

    def final_review_pending(self) -> list[TaskUnit]:
        required_ids = _required_answer_sheet_task_ids(self.manifest)
        return [
            task
            for task in self.session.tasks
            if task.kind != "programming"
            and (
                not _is_answer_sheet_contest(self.manifest)
                or task.task_id in required_ids
            )
            and task.versions
            and self.final_review_approvals.get(task.task_id)
            != task.versions[-1].version_hash
        ]

    def answer_sheet_ready_for_final_review(self) -> bool:
        required_ids = _required_answer_sheet_task_ids(self.manifest)
        return _is_answer_sheet_contest(self.manifest) and all(
            task.versions
            and (not self.config.review_required or _task_has_independent_approval(task))
            for task in self.session.tasks
            if task.task_id in required_ids
        )

    def _prepare_coach(self) -> None:
        if self.policy is not None and self.card is not None:
            brief_event = otc_runtime.coach_event(self.memory, otc_runtime.BRIEF_EVENT)
            if brief_event is None:
                # One blind turn-0 brief: one API call, no contest time.
                try:
                    self.session.consume_budget(api_calls=1)
                except BudgetExceededError:
                    self.coach_budget_exhausted = True
                else:
                    brief_system, brief_user = otc_runtime.coach_brief_prompts(
                        self.card,
                        self.policy,
                        self.manifest,
                        team_size=self.config.team_size,
                        max_turns=self.config.max_turns,
                        max_api_calls=self.config.max_api_calls,
                    )
                    brief_response = (self.coach_query_fn or self.query_llm_fn)(brief_system, brief_user)
                    if not self._charge_tokens(brief_response):
                        self.coach_budget_exhausted = True
                    self.coach_guidance, _ = clip_text(
                        brief_response.strip(), self.policy.char_limit("work")
                    )
                    self.memory.append(
                        task_id=None,
                        question_id=None,
                        actor=otc_runtime.COACH_AGENT,
                        visibility="public",
                        kind=otc_runtime.BRIEF_EVENT,
                        payload={
                            "guidance": self.coach_guidance,
                            "plan": None,
                            "author": otc_runtime.COACH_AGENT,
                            "stage": "precontest_brief",
                        },
                        turn=self.session.budget.turns_used,
                    )
                    brief_event = otc_runtime.coach_event(self.memory, otc_runtime.BRIEF_EVENT)
                    self._persist_checkpoint()


        # Who writes the opening plan: the exiting Coach seat, or the leader who
        # then stays in the contest as an ordinary (submitting) contestant.
        self.planner: str | None = None
        plan_query: QueryFn | None = None
        if self.config.features.coach == "leader":
            self.planner, plan_query = self.config.leader, self.query_llm_fn
        elif self.config.features.coach == "card":
            self.planner = otc_runtime.COACH_AGENT
        if self.planner is not None and plan_query is not None and not self.coach_guidance:
            try:
                self.session.consume_budget(api_calls=1)
            except BudgetExceededError:
                self.coach_budget_exhausted = True
            else:
                coach_system, coach_user = _leader_plan_prompts(self.manifest, self.config)
                coach_response = plan_query(coach_system, coach_user)
                coach_tokens = estimate_tokens(coach_response)
                remaining_tokens = (
                    None
                    if self.session.budget.max_tokens is None
                    else max(
                        0,
                        self.session.budget.max_tokens - self.session.budget.tokens_used,
                    )
                )
                charged_tokens = (
                    coach_tokens
                    if remaining_tokens is None
                    else min(coach_tokens, remaining_tokens)
                )
                self.session.consume_budget(tokens=charged_tokens)
                self.coach_budget_exhausted = charged_tokens < coach_tokens
                self.coach_plan = _normalize_coach_plan(coach_response, self.manifest, self.config)
                if self.config.leader is not None:
                    # The leader may touch every problem; workers keep their lists.
                    # No review workflow: review routes would only pull workers
                    # onto problems they cannot act on.
                    self.coach_plan["work_assignments"][self.config.leader] = [
                        task.task_id for task in self.manifest.tasks
                    ]
                    if not (self.config.review_required or self.config.final_review_required):
                        self.coach_plan["review_assignments"] = {
                            agent: [] for agent in self.coach_plan["review_assignments"]
                        }
                self.coach_guidance = json.dumps(self.coach_plan, ensure_ascii=False, indent=2)
                self.memory.append(
                    task_id=None,
                    question_id=None,
                    actor=self.planner,
                    visibility="public",
                    kind="precontest_coach_guidance",
                    payload={"guidance": self.coach_guidance, "plan": self.coach_plan, "author": self.planner},
                    turn=self.session.budget.turns_used,
                )
                for index in range(1, self.config.team_size + 1):
                    agent = f"Agent_{index}"
                    self.memory.append(
                        task_id=None,
                        question_id=None,
                        actor=self.planner,
                        visibility="private",
                        recipients=(agent,),
                        kind="coach_personal_assignment",
                        payload={
                            "agent": agent,
                            "work_tasks": list(
                                self.coach_plan["work_assignments"].get(agent, [])
                            ),
                            "review_tasks": list(
                                self.coach_plan["review_assignments"].get(agent, [])
                            ),
                            "summary": self.coach_plan["summary"],
                            "switch_conditions": self.coach_plan["switch_conditions"],
                            "final_check": self.coach_plan["final_check"],
                        },
                        turn=self.session.budget.turns_used,
                    )
                self._persist_checkpoint()

        self.personal_assignments: dict[str, dict[str, Any]] = {}
        if self.coach_plan:
            order = list(self.coach_plan.get("task_order") or [])
            work_by_agent = self.coach_plan.get("work_assignments") or {}
            review_by_agent = self.coach_plan.get("review_assignments") or {}
            for index in range(1, self.config.team_size + 1):
                agent = f"Agent_{index}"
                assigned_work = list(work_by_agent.get(agent, []))
                ordered_work = [
                    task_id for task_id in order if task_id in assigned_work
                ] + [
                    task_id for task_id in assigned_work if task_id not in order
                ]
                self.personal_assignments[agent] = {
                    "agent": agent,
                    "work_tasks": ordered_work,
                    "review_tasks": list(review_by_agent.get(agent, [])),
                    "summary": str(self.coach_plan.get("summary") or ""),
                    "switch_conditions": list(
                        self.coach_plan.get("switch_conditions") or []
                    ),
                    "final_check": list(self.coach_plan.get("final_check") or []),
                }
            # Leader reassignments are ordinary public action events; replaying
            # them over the opening plan makes the table resume-safe.
            for event in self.archived_events:
                if event["kind"] == "assign_problem" and event["actor"] == self.config.leader:
                    _set_work_assignment(
                        self.personal_assignments,
                        str(event["payload"]["agent"]),
                        [str(task_id) for task_id in event["payload"]["problem_ids"]],
                    )

    def run(self) -> dict[str, Any]:
        self._prepare_coach()
        self.finished = self.coach_budget_exhausted
        self.switches = 0
        self.stalled_turns = 0
        self.last_progress_turn: dict[str, int] = {}
        self.programming_progress = ProgrammingProgress(self.memory, stall_actions=self.config.stall_turns)
        self.deadline_submission_used = False
        self.baseline_mechanical_switches = 0
        for _ in range(self.config.max_turns):
            if not self._run_round():
                break
        self._collect_deadline()
        return self._build_result()

    def _run_round(self) -> bool:
        if self.finished:
            return False
        switches_at_turn_start = self.switches
        progress_at_turn_start = sum(
            len(task.versions) + len(task.submissions) for task in self.session.tasks
        )
        try:
            self.session.consume_budget(
                turns=1,
                simulated_minutes=self.config.minutes_per_turn,
            )
        except BudgetExceededError:
            return False
        from contest_judging import deliver_verdicts
        deliver_verdicts(self.session, self.memory)
        if (
            self.config.features.submission_cooldown
            and self.session.active_task is None
            and all(task.versions or task.submissions for task in self.session.tasks)
        ):
            revisit = _next_task(self.session, self.strategic_policy)
            if revisit is not None:
                self.session.revisit_task(revisit.task_id)
                self.switches += 1
                self.memory.append(
                    task_id=revisit.task_id,
                    question_id=None,
                    actor="Contest_Control",
                    visibility="public",
                    kind="problem_switched",
                    payload={
                        "from": None,
                        "to": revisit.task_id,
                        "reason": "cooldown_revisit",
                    },
                    turn=self.session.budget.turns_used,
                )
        _record_scoreboard(self.memory, self.session)
        start = self.config.start_seat % self.config.team_size
        agents = [
            f"Agent_{(start + offset) % self.config.team_size + 1}"
            for offset in range(self.config.team_size)
        ]
        if self.config.leader is not None:
            # The leader opens every round; workers keep the rotating order.
            agents.remove(self.config.leader)
            agents.insert(0, self.config.leader)
        for agent in agents:
            if self.finished:
                break
            self._run_agent_turn(_AgentTurn(agent))
        active = self.session.active_task
        if (
            not self.finished
            and active is not None
            and not (active.kind == "programming" and self.config.review_required)
            and self.switches == switches_at_turn_start
            and self.strategic_policy.switch_reason(
                active,
                current_turn=self.session.budget.turns_used,
                last_progress_turn=self.last_progress_turn.get(active.task_id, 0),
            )
            == "stalled_turns"
        ):
            previous_id = active.task_id
            next_task = _next_task(
                self.session,
                self.strategic_policy,
                exclude_task_id=previous_id,
            )
            if next_task is not None:
                self.memory.create_problem_digest(active.task_id, viewer="Agent_1")
                self.session.skip_task()
                self.session.select_task(next_task.task_id)
                self.switches += 1
                if self.config.features.mechanical_switch:
                    self.baseline_mechanical_switches += 1
                self.memory.append(
                    task_id=previous_id,
                    question_id=None,
                    actor="Contest_Control",
                    visibility="public",
                    kind="problem_switched",
                    payload={
                        "from": previous_id,
                        "to": next_task.task_id,
                        "reason": "stalled_turns",
                    },
                    turn=self.session.budget.turns_used,
                )
        self._persist_checkpoint()
        progress_at_turn_end = sum(
            len(task.versions) + len(task.submissions) for task in self.session.tasks
        )
        if progress_at_turn_end == progress_at_turn_start and self.switches == switches_at_turn_start:
            self.stalled_turns += 1
        return True

    def _run_agent_turn(self, turn: _AgentTurn) -> None:
        if not self._prepare_agent(turn):
            return
        if not self._build_agent_prompts(turn):
            return
        if not self._request_action(turn):
            return
        self._apply_agent_action(turn)

    def _prepare_agent(self, turn: _AgentTurn) -> bool:
        turn.personal_assignment = self.personal_assignments.get(turn.agent)
        rescue_task_ids = {
            task.task_id
            for task in self.session.tasks
            if not task.locked
            and task.versions
            and not _task_has_independent_approval(task)
            and _rejected_version_count(task) >= 2
        }
        # Under the rule card the coach's assignment is advice only.
        turn.work_task_ids = (
            set(turn.personal_assignment["work_tasks"]) | rescue_task_ids
            if turn.personal_assignment is not None and self.policy is None
            else None
        )
        turn.review_task_ids = (
            set(turn.personal_assignment["review_tasks"]) | rescue_task_ids
            if turn.personal_assignment is not None and self.policy is None
            else None
        )
        scheduled_work_ids = (
            [
                *sorted(rescue_task_ids),
                *[
                    task_id
                    for task_id in turn.personal_assignment["work_tasks"]
                    if task_id not in rescue_task_ids
                ],
            ]
            if turn.personal_assignment is not None
            else []
        )
        if self.config.review_required:
            # Only reorder programming slots; mixed/non-programming tasks
            # retain their original assignment order and workflow.
            code_ids = self.programming_progress.ordered_tasks(turn.agent, [
                task_id for task_id in scheduled_work_ids
                if self.session.task(task_id).kind == "programming"
            ])
            ordered_code = iter(code_ids)
            scheduled_work_ids = [
                next(ordered_code) if self.session.task(task_id).kind == "programming" else task_id
                for task_id in scheduled_work_ids
            ]
        if self.policy is not None:
            # Each seat keeps its own focus: the problem it last selected,
            # else the coach's first suggestion, else the scheduler's pick.
            focus = _card_focus_task(
                self.session, self.memory, turn.agent, turn.personal_assignment, self.strategic_policy
            )
            if focus is not None and (
                self.session.active_task is None
                or self.session.active_task.task_id != focus.task_id
            ):
                previous_id = (
                    self.session.active_task.task_id
                    if self.session.active_task is not None
                    else None
                )
                self.session.select_task(focus.task_id)
                self.switches += int(previous_id is not None)
        elif (
            turn.personal_assignment is not None
            and not self.final_review_started
        ):
            scheduled = _scheduled_agent_task(
                self.session,
                agent=turn.agent,
                work_task_ids=scheduled_work_ids,
                review_task_ids=turn.review_task_ids or set(),
                reported_version_hashes=_reported_version_hashes(self.memory),
            )
            if scheduled is not None and (
                self.session.active_task is None
                or self.session.active_task.task_id != scheduled.task_id
            ):
                previous_id = (
                    self.session.active_task.task_id
                    if self.session.active_task is not None
                    else None
                )
                self.session.select_task(scheduled.task_id)
                self.switches += int(previous_id is not None)
                self.memory.append(
                    task_id=scheduled.task_id,
                    question_id=None,
                    actor="Contest_Scheduler",
                    visibility="private",
                    recipients=(turn.agent,),
                    kind="assignment_task_scheduled",
                    payload={
                        "from": previous_id,
                        "to": scheduled.task_id,
                    },
                    turn=self.session.budget.turns_used,
                )
        if self.final_review_started and not self.final_review_completed:
            pending = self.final_review_pending()
            if not pending:
                self.memory.append(
                    task_id=None,
                    question_id=None,
                    actor="Contest_Control",
                    visibility="public",
                    kind="final_review_completed",
                    payload={"approved_tasks": len(self.final_review_approvals)},
                    turn=self.session.budget.turns_used,
                )
                self.final_review_completed = True
                if not _is_answer_sheet_contest(self.manifest):
                    self.finished = True
                    return False
            else:
                eligible = [
                    task
                    for task in pending
                    if not task.versions[-1].author
                    or task.versions[-1].author != turn.agent
                    if (
                        turn.review_task_ids is None
                        or task.task_id in turn.review_task_ids
                    )
                ]
                if eligible and (
                    self.session.active_task is None
                    or self.session.active_task.task_id != eligible[0].task_id
                ):
                    self.session.select_task(eligible[0].task_id)
        turn.programming_source_required = bool(
            self.config.review_required
            and self.session.active_task is not None
            and _needs_programming_source(self.session.active_task)
            and (turn.work_task_ids is None or self.session.active_task.task_id in turn.work_task_ids)
            and self.programming_progress.source_required(turn.agent, self.session.active_task.task_id)
        )
        turn.available_actions = _actions_for_agent(
            self.actions,
            self.session,
            self.config,
            turn.agent,
            answer_sheet_contest=_is_answer_sheet_contest(self.manifest),
            required_answer_task_ids=_required_answer_sheet_task_ids(self.manifest),
            reported_version_hashes=_reported_version_hashes(self.memory),
            work_task_ids=turn.work_task_ids,
            review_task_ids=turn.review_task_ids,
            answer_sheet_submit_ready=(
                self.final_review_completed
                and self.answer_sheet_ready_for_final_review()
            ),
            programming_source_required=turn.programming_source_required,
            review_targets=(
                [
                    {
                        "problem_id": task.task_id,
                        "version_hash": task.versions[-1].version_hash,
                        "author": task.versions[-1].author,
                    }
                    for task in self.final_review_pending()
                    if task.versions[-1].author != turn.agent
                    and (
                        turn.review_task_ids is None
                        or task.task_id in turn.review_task_ids
                    )
                ]
                if self.final_review_started and not self.final_review_completed
                else None
            ),
            memory=self.memory,
        )
        turn.programming_source_required = turn.programming_source_required and (
            {spec.name for spec in turn.available_actions} == {"execute_code"}
        )
        return True

    def _build_agent_prompts(self, turn: _AgentTurn) -> bool:
        turn.function_tools = tuple(render_function_tools(turn.available_actions))
        card_protocol = ""
        card_block_text = ""
        think_ledger: list[dict[str, Any]] | None = None
        if self.policy is not None and self.card is not None:
            communication = otc_runtime.communication_budget(self.memory, self.policy)
            active_now = self.session.active_task
            card_protocol = otc_runtime.protocol_text(
                self.card,
                self.policy,
                agent=turn.agent,
                team_size=self.config.team_size,
                current_turn=self.session.budget.turns_used,
                communication=communication,
                lease_holder=(
                    otc_runtime.workstation_holder(
                        self.memory,
                        active_now.task_id,
                        current_turn=self.session.budget.turns_used,
                    )
                    if active_now is not None and self.policy.workstation_lease
                    else None
                ),
                pending_verdict=bool(
                    active_now is not None
                    and otc_runtime.submission_pending(
                        active_now,
                        current_turn=self.session.budget.turns_used,
                        latency_turns=self.policy.run_judging_latency_turns,
                    )
                ),
                silent_streak=otc_runtime.silent_work_streak(self.memory, turn.agent),
                programming=self.programming_contest,
                open_proposals=(
                    tuple(otc_runtime.deliberation_ledger(self.memory).report()["open_proposals"])
                    if self.policy.structured_deliberation
                    else ()
                ),
                review_required=self.config.review_required,
            )
            card_block_text = otc_runtime.card_block(self.card, self.config.team_size)
            # Card turn structure: private deliberation call(s), then one
            # action. Each think is its own API call and private event.
            think_ok = True
            for _ in range(self.policy.private_think_calls_per_turn):
                try:
                    self.session.consume_budget(api_calls=1)
                except BudgetExceededError:
                    think_ok = False
                    break
                think_prompt = _user_prompt(
                    self.manifest,
                    self.session,
                    self.memory,
                    self.config,
                    turn.agent,
                    personal_assignment=turn.personal_assignment,
                    think_ledger=otc_runtime.private_think_ledger(
                        self.memory,
                        turn.agent,
                        limit=(0 if self.config.features.basic_open_table else self.policy.memory_entries.private_think_per_agent),
                    ),
                )
                think_system = otc_runtime.think_system_prompt(
                    self.card,
                    self.policy,
                    turn.agent,
                    team_size=self.config.team_size,
                    action_names=(spec.name for spec in turn.available_actions),
                    retain_history=not self.config.features.basic_open_table,
                ) + "\n" + card_protocol
                if self.coach_guidance:
                    think_system += f"\nPRE-CONTEST COACH BRIEF\n{self.coach_guidance}"
                if self.opening_summary:
                    think_system += f"\nCOACH OPENING SUMMARY\n{self.opening_summary}"
                think_response = self.query_llm_fn(think_system, think_prompt)
                if not self._charge_tokens(think_response):
                    think_ok = False
                thought, cut = clip_text(
                    think_response.strip(), self.policy.char_limit("think")
                )
                self.memory.append(
                    task_id=(
                        self.session.active_task.task_id if self.session.active_task else None
                    ),
                    question_id=None,
                    actor=turn.agent,
                    visibility="private",
                    recipients=(turn.agent,),
                    kind=otc_runtime.THINK_EVENT,
                    payload={"content": thought, "compacted": cut},
                    turn=self.session.budget.turns_used,
                )
                if not think_ok:
                    break
            if not think_ok:
                self.finished = True
                return False
            think_ledger = otc_runtime.private_think_ledger(
                self.memory,
                turn.agent,
                limit=self.policy.memory_entries.private_think_per_agent,
            )
        try:
            self.session.consume_budget(api_calls=1)
        except BudgetExceededError:
            self.finished = True
            return False
        if turn.programming_source_required:
            self.memory.append(
                task_id=self.session.active_task.task_id, question_id=None,
                actor="Contest_Control", visibility="private", recipients=(turn.agent,),
                kind="programming_source_required",
                payload={"agent": turn.agent, "note_action_limit": 2},
                turn=self.session.budget.turns_used,
            )
        turn.system_prompt = _system_prompt(
            self.config,
            turn.agent,
            turn.available_actions,
            native_actions=self.action_request_fn is not None,
            answer_sheet_contest=_is_answer_sheet_contest(self.manifest),
            task_family=self.manifest.task_family,
            coach_guidance=self.coach_guidance,
            card_protocol=card_protocol,
            card_block=card_block_text,
            opening_summary=self.opening_summary,
        )
        turn.user_prompt = _user_prompt(
            self.manifest,
            self.session,
            self.memory,
            self.config,
            turn.agent,
            final_review_phase=self.final_review_started
            and not self.final_review_completed,
            personal_assignment=turn.personal_assignment,
            programming_source_required=turn.programming_source_required,
            think_ledger=think_ledger,
        )
        return True

    def _request_action(self, turn: _AgentTurn) -> bool:
        if self.action_request_fn is not None:
            max_transport_attempts = (
                None
                if self.session.budget.max_api_calls is None
                else 1
                + max(
                    0,
                    self.session.budget.max_api_calls
                    - self.session.budget.api_calls_used,
                )
            )
            response = self.action_request_fn(
                LLMRequest(
                    system_prompt=turn.system_prompt,
                    user_prompt=turn.user_prompt,
                    purpose="contest_action",
                    metadata={
                        "agent": turn.agent,
                        "session_id": self.manifest.session_id,
                        "task_id": (
                            self.session.active_task.task_id
                            if self.session.active_task
                            else None
                        ),
                        "max_transport_attempts": max_transport_attempts,
                    },
                    tools=turn.function_tools,
                    tool_choice="required",
                )
            )
            reported_api_calls = max(
                1,
                int(response.usage.get("api_calls") or 1),
            )
            self.transport_api_calls += reported_api_calls
            self.transport_retries += max(
                0,
                int(response.usage.get("tool_retries") or 0),
            )
            self.transport_failures += int(
                not response.tool_calls
                and bool(response.usage.get("tool_error"))
            )
            if reported_api_calls > 1:
                try:
                    self.session.consume_budget(api_calls=reported_api_calls - 1)
                except BudgetExceededError:
                    self.finished = True
                    return False
            self.action_transport_log.extend(
                {
                    "turn": self.session.budget.turns_used,
                    "agent": turn.agent,
                    "call_id": call.call_id,
                    "name": call.name,
                    "arguments": call.arguments,
                    "executed": index == 0,
                }
                for index, call in enumerate(response.tool_calls)
            )
            serialized_calls = json.dumps(
                [
                    {
                        "name": call.name,
                        "arguments": call.arguments,
                    }
                    for call in response.tool_calls
                ],
                ensure_ascii=False,
            )
            token_count = int(
                response.usage.get("output_tokens")
                or response.usage.get("completion_tokens")
                or estimate_tokens(serialized_calls or response.text)
            )
        else:
            response = self.query_llm_fn(turn.system_prompt, turn.user_prompt)
            token_count = estimate_tokens(response)
        remaining_tokens = (
            None
            if self.session.budget.max_tokens is None
            else max(
                0,
                self.session.budget.max_tokens - self.session.budget.tokens_used,
            )
        )
        charged_tokens = (
            token_count
            if remaining_tokens is None
            else min(token_count, remaining_tokens)
        )
        self.session.consume_budget(tokens=charged_tokens)
        if charged_tokens < token_count:
            self.finished = True
            return False
        if self.action_request_fn is not None:
            if not response.tool_calls:
                turn.action, turn.arguments, error = (
                    None,
                    {},
                    "response must contain at least one native function call",
                )
            else:
                call = response.tool_calls[0]
                if len(response.tool_calls) > 1:
                    self.memory.append(
                        task_id=(
                            self.session.active_task.task_id
                            if self.session.active_task
                            else None
                        ),
                        question_id=None,
                        actor="Contest_Control",
                        visibility="private",
                        recipients=(turn.agent,),
                        kind="extra_function_calls_ignored",
                        payload={
                            "executed_call_id": call.call_id,
                            "ignored_call_ids": [
                                extra.call_id
                                for extra in response.tool_calls[1:]
                            ],
                        },
                        turn=self.session.budget.turns_used,
                    )
                turn.action, turn.arguments, error = validate_action_invocation(
                    call.name,
                    call.arguments,
                    turn.available_actions,
                )
        else:
            turn.action, turn.arguments, error = parse_typed_action(
                response, turn.available_actions
            )
        if error:
            _append_action_error(self.memory, self.session, turn.agent, error)
            return False
        assert turn.action is not None
        return True

    def _apply_agent_action(self, turn: _AgentTurn) -> bool:
        acted_task = self.session.active_task
        before_versions = len(acted_task.versions) if acted_task else 0
        before_source = acted_task.versions[-1] if acted_task and acted_task.versions else None
        before_events = len(self.memory.archival_snapshot()["events"])
        try:
            action_finished, switch_delta = _apply_action(
                action=turn.action,
                arguments=turn.arguments,
                agent=turn.agent,
                manifest=self.manifest,
                session=self.session,
                memory=self.memory,
                config=self.config,
                strategic_policy=self.strategic_policy,
                task_action_executor=self.executor,
                work_task_ids=turn.work_task_ids,
                review_task_ids=turn.review_task_ids,
                final_review_complete=self.final_review_completed,
                personal_assignments=self.personal_assignments,
            )
            self.switches += switch_delta
        except (KeyError, RuntimeError, ValueError) as exc:
            _append_action_error(self.memory, self.session, turn.agent, str(exc))
            self._persist_checkpoint()
            return False
        if (
            self.final_review_started
            and not self.final_review_completed
            and turn.action == "review_answer"
        ):
            reviewed = self.session.task(str(turn.arguments["problem_id"]))
            if reviewed is not None and reviewed.reviews:
                review = reviewed.reviews[-1]
                review_kind = (
                    "final_review_approved"
                    if review.decision == "approve"
                    else "final_review_rejected"
                )
                self.memory.append(
                    task_id=reviewed.task_id,
                    question_id=None,
                    actor=turn.agent,
                    visibility="public",
                    kind=review_kind,
                    payload={
                        "version_hash": review.version_hash,
                        "body": review.body,
                    },
                    turn=self.session.budget.turns_used,
                )
                if review.decision == "approve":
                    self.final_review_approvals[reviewed.task_id] = review.version_hash
                else:
                    self.final_review_approvals.pop(reviewed.task_id, None)
        if (
            self.config.final_review_required
            and not self.final_review_started
            and any(task.kind != "programming" for task in self.session.tasks)
            and (
                self.answer_sheet_ready_for_final_review()
                or action_finished
            )
        ):
            self.final_review_started = True
            action_finished = False
            self.memory.append(
                task_id=None,
                question_id=None,
                actor="Pre_Contest_Coach",
                visibility="public",
                kind="final_review_started",
                payload={
                    "reason": "Initial answer sheet complete; begin reserved final audit."
                },
                turn=self.session.budget.turns_used,
            )
        self.finished = action_finished
        created_version = bool(
            acted_task is not None and len(acted_task.versions) > before_versions
        )
        programming_visit = bool(
            self.config.review_required
            and acted_task is not None and acted_task.kind == "programming"
            and (turn.work_task_ids is None or acted_task.task_id in turn.work_task_ids)
            and (
                turn.action in {"work", "execute_code", "rest", "speak", "submit_code",
                           "select_problem", "skip_problem", "direct_message"}
                or turn.action in DESK_ACTION_NAMES
            )
        )
        if programming_visit:
            new_events = self.memory.archival_snapshot()["events"][before_events:]
            latest = acted_task.versions[-1] if acted_task.versions else None
            sample_events = [e for e in new_events if e["kind"] == "sample_judge_result"]
            infrastructure_error = any(
                e["payload"].get("sample_verdict") == "JUDGE_ERROR"
                for e in sample_events
            ) or any(
                e["kind"] == "execute_code_result" and not e["payload"].get("valid", True)
                for e in new_events
            )
            progressed = bool(
                latest and latest.evidence_refs and (
                    before_source is None or not before_source.evidence_refs
                    or latest.content != before_source.content
                )
            ) or any(
                e["kind"] == "local_run_report"
                or (e["kind"] == "submit_code_result" and e["payload"].get("valid"))
                for e in new_events
            )
            if not infrastructure_error:
                yielded = self.programming_progress.record(
                    turn.agent, acted_task.task_id, turn=self.session.budget.turns_used,
                    progressed=progressed,
                    source_attempted=turn.action == "execute_code" and not any(
                        e["kind"] == "execute_code_result" and e["payload"].get("execution_reused")
                        for e in new_events
                    ),
                )
                if yielded and turn.personal_assignment is None and not (
                    latest and latest.evidence_refs
                ):
                    next_task = _next_task(self.session, self.strategic_policy, exclude_task_id=acted_task.task_id)
                    if next_task is not None:
                        self.session.skip_task()
                        self.session.select_task(next_task.task_id)
                        self.switches += 1
            if progressed:
                self.last_progress_turn[acted_task.task_id] = self.session.budget.turns_used
        elif created_version and acted_task is not None:
            self.last_progress_turn[acted_task.task_id] = self.session.budget.turns_used
        if (
            self.policy is not None
            and acted_task is not None
            and acted_task.kind == "programming"
            and turn.action in WORKSTATION_ACTION_NAMES
            and acted_task.priority not in {"low", "hopeless"}
            and otc_runtime.repair_budget_exhausted(
                self.memory,
                acted_task,
                repair_budget=self.policy.repair_budget_after_rejected_run,
            )
        ):
            # Card repair budget: after an official rejection, progress means
            # a better verdict; churning past the budget demotes the problem.
            self.session.set_triage(
                acted_task.task_id,
                "low",
                reason=(
                    f"{self.policy.repair_budget_after_rejected_run} executions after "
                    "the last rejected official run without a sample-AC on new source"
                ),
                actor="Contest_Control",
                turn=self.session.budget.turns_used,
            )
            self.memory.append(
                task_id=acted_task.task_id,
                question_id=None,
                actor="Contest_Control",
                visibility="public",
                kind="programming_repair_budget_exhausted",
                payload={
                    "problem_id": acted_task.task_id,
                    "repair_budget": self.policy.repair_budget_after_rejected_run,
                    "priority": "low",
                    "note": (
                        "Priority lowered by the rule card's repair budget; switch "
                        "to another problem and revisit with a new idea."
                    ),
                },
                turn=self.session.budget.turns_used,
            )
        if (
            not self.finished
            and self.config.features.mechanical_switch
            and _is_answer_sheet_contest(self.manifest)
            and turn.action == "work"
            and created_version
            and acted_task is not None
        ):
            next_unseen = next(
                iter(
                    sorted(
                        (
                            task
                            for task in self.session.tasks
                            if task.task_id != acted_task.task_id
                            and not task.locked
                            and not task.versions
                            and not task.submissions
                        ),
                        key=lambda task: task.priority_rank,
                    )
                ),
                None,
            )
            if next_unseen is not None:
                self.memory.create_problem_digest(acted_task.task_id, viewer=turn.agent)
                self.session.skip_task()
                self.session.select_task(next_unseen.task_id)
                self.switches += 1
                self.baseline_mechanical_switches += 1
                self.memory.append(
                    task_id=next_unseen.task_id,
                    question_id=None,
                    actor="Contest_Control",
                    visibility="public",
                    kind="baseline_next_unseen_scheduled",
                    payload={
                        "from": acted_task.task_id,
                        "to": next_unseen.task_id,
                        "reason": "draft_recorded",
                    },
                    turn=self.session.budget.turns_used,
                )
        if (
            self.config.features.coach == "none"
            and turn.action == "select_problem"
            and self.session.active_task is not None
        ):
            self.last_progress_turn.setdefault(
                self.session.active_task.task_id,
                self.session.budget.turns_used,
            )
        self._persist_checkpoint()
        return True

    def _collect_deadline(self) -> None:
        from contest_judging import deliver_verdicts
        deliver_verdicts(self.session, self.memory, final=True)
        if self.config.programming_deadline_submit and any(t.programming for t in self.manifest.tasks):
            _collect_programming_deadline(self.manifest, self.session, self.memory, self.executor, self._persist_checkpoint,
                                          require_approval=self.config.review_required and self.policy is not None)

        # Deadline collection is an environment policy shared by both variants.
        if any(task.kind != "programming" for task in self.session.tasks):
            deadline_active_task_id = (
                self.session.active_task.task_id if self.session.active_task is not None else None
            )
            deadline_task_ids = []
            for task in self.session.tasks:
                if (
                    task.kind == "programming"
                    or not task.versions
                    or task.latest_valid_submission is not None
                    or (self.config.review_required and self.policy is not None and not _task_has_independent_approval(task))
                ):
                    continue
                self.session.select_task(task.task_id)
                self.session.submit("SUBMITTED", score=0.0, valid=True)
                deadline_task_ids.append(task.task_id)
            if deadline_task_ids:
                self.deadline_submission_used = True
                self.memory.append(
                    task_id=None,
                    question_id=None,
                    actor="Contest_Control",
                    visibility="public",
                    kind="deadline_drafts_submitted",
                    payload={
                        "submitted_task_ids": deadline_task_ids,
                        "review_gate_waived": self.config.review_required and self.policy is None,
                        "final_review_gate_waived": self.config.final_review_required,
                    },
                    turn=self.session.budget.turns_used,
                )
                if deadline_active_task_id is None:
                    self.session.skip_task()
                else:
                    self.session.select_task(deadline_active_task_id)
                self._persist_checkpoint()

    def _build_result(self) -> dict[str, Any]:
        deadline_events = self.memory.archival_snapshot()["events"]
        deadline_attempts = [e for e in deadline_events if e["kind"] == "programming_deadline_submit_started"]
        deadline_results = [e for e in deadline_events if e["kind"] == "programming_deadline_submit_result"]
        deadline_accepted = [e["task_id"] for e in deadline_results if e["payload"].get("valid") and e["payload"].get("verdict") == "AC"]
        deadline_before = next((e["payload"] for e in deadline_events if e["kind"] == "programming_deadline_started"), {})
        self.deadline_submission_used = self.deadline_submission_used or bool(deadline_attempts)
        summary = self.session.finalize()
        submissions = {
            task.task_id: (
                task.latest_submitted_answer.content
                if task.latest_submitted_answer is not None
                else ""
            )
            for task in self.session.tasks
        }
        submitted = [task for task in self.session.tasks if task.latest_valid_submission]
        reviewed = [
            task
            for task in submitted
            if any(
                not review.stale
                and review.decision == "approve"
                and task.latest_submitted_answer is not None
                and review.version_hash == task.latest_submitted_answer.version_hash
                and review.reviewer != task.latest_submitted_answer.author
                for review in task.reviews
            )
        ]
        if _is_answer_sheet_contest(self.manifest):
            required_ids = _required_answer_sheet_task_ids(self.manifest)
            final_reviewable = [
                task
                for task in self.session.tasks
                if task.task_id in required_ids and task.versions
            ]
        else:
            final_reviewable = [
                task
                for task in submitted
                if task.kind != "programming"
                and task.latest_submitted_answer is not None
            ]
        final_reviewed = [
            task
            for task in final_reviewable
            if self.final_review_approvals.get(task.task_id)
            == task.versions[-1].version_hash
        ]
        final_review_coverage = (
            len(final_reviewed) / len(final_reviewable) if final_reviewable else 0.0
        )
        final_review_status = (
            "completed"
            if self.final_review_started
            and (not final_reviewable or len(final_reviewed) == len(final_reviewable))
            else "in_progress"
            if self.final_review_started
            else "not_started"
        )
        active_agent_rate, action_balance = _participation_metrics(
            self.memory, self.manifest, self.config.team_size
        )
        attempts_to_ac = {
            task.task_id: next(
                (
                    index
                    for index, submission in enumerate(task.submissions, start=1)
                    if submission.verdict == "AC"
                ),
                None,
            )
            for task in self.session.tasks
            if task.kind == "programming"
        }
        all_events = self.memory.archival_snapshot()["events"]
        event_kind_counts: dict[str, int] = {}
        for event in all_events:
            event_kind_counts[event["kind"]] = event_kind_counts.get(event["kind"], 0) + 1
        desk_diagnostics = {
            "inspect_count": event_kind_counts.get("inspect_problem", 0),
            "notes_recorded": event_kind_counts.get("note", 0),
            "notes_shared": event_kind_counts.get("note_shared", 0),
            "recall_count": event_kind_counts.get("recall", 0),
            "triage_changes": event_kind_counts.get("task_triaged", 0),
            "items_hopeless": sum(task.hopeless for task in self.session.tasks),
            "repeat_draft_attempts": event_kind_counts.get("work_duplicate", 0),
        }
        if self.policy is not None:
            desk_diagnostics["otc"] = {
                "think_calls": event_kind_counts.get(otc_runtime.THINK_EVENT, 0),
                "content_clipped": event_kind_counts.get("card_content_clipped", 0),
                "coach_brief": bool(self.coach_guidance),
                "coach_calls": event_kind_counts.get(otc_runtime.BRIEF_EVENT, 0),
                "review_required": self.config.review_required,
                "final_review_required": self.config.final_review_required,
                "coach_opening_summary": bool(self.opening_summary),
                "communication": otc_runtime.communication_budget(self.memory, self.policy).report(),
                "deliberation": (
                    otc_runtime.deliberation_ledger(self.memory).report()
                    if self.policy.structured_deliberation
                    else None
                ),
                "repair_budget_exhausted": event_kind_counts.get(
                    "programming_repair_budget_exhausted", 0
                ),
                "speak": event_kind_counts.get("speak", 0),
                "direct_messages": event_kind_counts.get("direct_message", 0),
            }
        segment_seconds = time.perf_counter() - self.wall_t0
        ended_at = datetime.now(timezone.utc).isoformat()
        self.session.budget.wall_seconds_used = self.prior_wall_seconds + segment_seconds
        timing = {
            "started_at": self.session.budget.wall_started_at,
            "ended_at": ended_at,
            "elapsed_seconds": self.session.budget.wall_seconds_used,
            "segment_seconds": segment_seconds,
            "segment_started_at": self.segment_started_at,
        }
        return {
            "session_id": self.manifest.session_id,
            "competition_id": self.manifest.competition_id,
            "system_variant": self.config.system_variant,
            "action_calling": self.action_transport
            or ("native" if self.action_request_fn is not None else "prompt_json"),
            "manifest": {
                "session_id": self.manifest.session_id,
                "competition_id": self.manifest.competition_id,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "parent_problem_id": task.parent_problem_id,
                        "question_id": task.question_id,
                        "task_type": task.task_type,
                        "max_score": task.max_score,
                        "programming": task.programming,
                    }
                    for task in self.manifest.tasks
                ],
            },
            "action_names": sorted(spec.name for spec in self.actions),
            "action_transport_log": self.action_transport_log,
            "precontest_coach_guidance": self.coach_guidance,
            "precontest_coach_plan": self.coach_plan,
            "coach_opening_summary": self.opening_summary,
            "rule_card": (
                {
                    "rule_id": self.config.rule_card.rule_id,
                    "competition_id": self.config.rule_card.competition_id,
                    "content_hash": card_content_hash(self.config.rule_card),
                    "mode": self.config.features.rule_card,
                }
                if self.config.rule_card is not None
                else None
            ),
            "active_task_id": self.session.active_task.task_id if self.session.active_task else None,
            "tasks": summary["tasks"],
            "submissions": submissions,
            "shared_review_history": _shared_review_history(self.session),
            "budget": asdict(self.session.budget),
            "protocol_version": PROTOCOL_VERSION,
            "action_set_version": ACTION_SET_VERSION,
            "baseline": asdict(self.config.features),
            "review_required": self.config.review_required,
            "final_review_required": self.config.final_review_required,
            "plan_author": self.planner,
            "programming_workflow_version": (
                "programming_workflow_v4" if self.config.review_required and any(task.programming for task in self.manifest.tasks)
                else None
            ),
            "deadline_policy": ("collect_pending_non_programming_drafts_and_unsubmitted_candidates_v2"
                                if self.config.programming_deadline_submit else "collect_pending_non_programming_drafts"),
            "programming_deadline_submit": self.config.programming_deadline_submit,
            "programming_deadline": {
                "enabled": self.config.programming_deadline_submit,
                **deadline_before,
                "attempted_task_ids": [e["task_id"] for e in deadline_attempts],
                "accepted_task_ids": deadline_accepted,
                "no_source_task_ids": [e["task_id"] for e in deadline_events if e["kind"] == "programming_deadline_no_source"],
                "unconfirmed_task_ids": [e["task_id"] for e in deadline_attempts if not any(r["task_id"] == e["task_id"] and r["payload"].get("valid") for r in deadline_results)],
            },
            "timing": timing,
            "session_checkpoint": self.session.checkpoint(),
            "memory": self.memory.archival_snapshot(),
            "diagnostics": {
                "review_coverage": len(reviewed) / len(submitted) if submitted else 0.0,
                "final_review_coverage": final_review_coverage,
                "final_review_status": final_review_status,
                "deadline_submission": self.deadline_submission_used,
                "programming_deadline_attempts": len(deadline_attempts),
                "programming_deadline_accepted": len(deadline_accepted),
                "switch_count": self.switches,
                "baseline_mechanical_switches": self.baseline_mechanical_switches,
                "attempts": sum(len(task.submissions) for task in self.session.tasks),
                "attempts_to_ac": attempts_to_ac,
                "stalled_turns": self.stalled_turns,
                "programming_repair_yields": event_kind_counts.get("programming_repair_yield", 0),
                "programming_source_required_actions": event_kind_counts.get(
                    "programming_source_required", 0
                ),
                "programming_duplicate_executions_avoided": sum(
                    e["kind"] == "execute_code_result" and bool(e["payload"].get("execution_reused"))
                    for e in all_events
                ),
                **desk_diagnostics,
                "active_agent_rate": active_agent_rate,
                "action_balance": action_balance,
                "transport_api_calls": self.transport_api_calls,
                "transport_retries": self.transport_retries,
                "transport_failures": self.transport_failures,
                "elapsed_seconds": self.session.budget.wall_seconds_used,
                "cce": None,
                "cce_status": "not_run",
            },
            "metrics": {
                "task_utility": None,
                "cce": None,
                "active_agent_rate": active_agent_rate,
                "action_balance": action_balance,
                "review_coverage": len(reviewed) / len(submitted) if submitted else 0.0,
                "final_review_coverage": final_review_coverage,
                "elapsed_seconds": self.session.budget.wall_seconds_used,
            },
        }


def _run_contest_engine(
    manifest: ContestManifest,
    query_llm_fn: QueryFn,
    config: ContestRunConfig,
    *,
    action_request_fn: RequestFn | None = None,
    action_transport: Literal["native", "emulated", "prompt_json"] | None = None,
    coach_query_fn: QueryFn | None = None,
    task_action_executor: TaskActionExecutor | None = None,
    session_checkpoint: dict[str, Any] | None = None,
    memory_checkpoint: str | None = None,
    checkpoint_callback: CheckpointCallback | None = None,
) -> dict[str, Any]:
    """Run one lifecycle with isolated mutable state and ordered phases."""
    return _ContestEngine(
        manifest, query_llm_fn, config,
        action_request_fn=action_request_fn, action_transport=action_transport,
        coach_query_fn=coach_query_fn, task_action_executor=task_action_executor,
        session_checkpoint=session_checkpoint, memory_checkpoint=memory_checkpoint,
        checkpoint_callback=checkpoint_callback,
    ).run()
