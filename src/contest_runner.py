"""Compatibility facade for contest variants and existing helper imports."""

from __future__ import annotations

from typing import Any, Literal
from contest_manifest import ContestManifest
from llm import RequestFn
from tool_registry import ACTION_SET_VERSION
from contest_config import (
    BASELINES, BASELINE_ALIASES, BASELINE_NAMES, LEADER_AGENT, PROTOCOL_VERSION,
    BaselineFeatures, CheckpointCallback, CoachMode, ContestRunConfig,
    QueryFn, RuleCardMode, TaskActionExecutor, canonical_baseline,
)
from contest_actions import (
    _is_answer_sheet_contest,
    _required_answer_sheet_task_ids,
    _local_run_reports,
    _sample_reports,
    _set_work_assignment,
    _next_task,
    _task_complete,
    _task_has_independent_approval,
    _contest_complete,
    _clip,
    _inspect_problem_payload,
    _share_note,
    _apply_card_rules,
    _apply_action,
)
from contest_prompts import (
    _task_rows,
    _needs_programming_source,
    _programming_gate_guidance,
    _shared_review_history,
    _pending_review_queue,
    _reported_version_hashes,
    _sample_failure_text,
    _remote_failure_guidance,
    _system_prompt,
    _user_prompt,
)

from contest_policy import (
    _resolved_actions,
    _trim_to_baseline,
    _card_submission_blocks,
    _card_gate,
    _actions_for_agent,
    _actions_for_agent_base,
    _leader_plan_prompts,
    _strip_coach_response,
    _normalize_task_ids,
    _default_coach_plan,
    _normalize_coach_plan,
    _card_task_claimed_this_turn,
    _card_task_settled,
    _card_focus_task,
    _scheduled_agent_task,
    _task_has_independent_review,
    _rejected_version_count,
)

from contest_lifecycle import (
    _default_executor,
    _append_action_error,
    _record_scoreboard,
    _participation_metrics,
    _collect_programming_deadline,
)

from contest_engine import _run_contest_engine


def run_contest(
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
    """Compatibility facade dispatching to one explicit variant module."""
    kwargs = {
        "action_request_fn": action_request_fn,
        "action_transport": action_transport,
        "task_action_executor": task_action_executor,
        "session_checkpoint": session_checkpoint,
        "memory_checkpoint": memory_checkpoint,
        "checkpoint_callback": checkpoint_callback,
    }
    if config.features.coach == "none":
        from vanilla_contest_runner import run_vanilla_contest

        return run_vanilla_contest(manifest, query_llm_fn, config, **kwargs)

    from strategic_contest_runner import run_strategic_contest

    return run_strategic_contest(
        manifest,
        query_llm_fn,
        config,
        coach_query_fn=coach_query_fn,
        **kwargs,
    )
