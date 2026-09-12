"""Environment execution defaults, checkpoint events, and deadline collection."""

from __future__ import annotations

from typing import Any, Callable

from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_session import ContestSession, TaskState
from programming_candidates import deadline_candidate, source_identity

from contest_config import TaskActionExecutor


from contest_prompts import (
    _task_rows,
)

def _default_executor(
    _task: ManifestTask,
    action: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    if action == "use_calculator":
        from env import OlympiadEnvironment

        return {
            "result": f"Calculator output: {OlympiadEnvironment._safe_calculate(arguments['expression'])}",
            "valid": True,
        }
    if action == "submit_code":
        return {
            "verdict": "SUBMIT_FAILED",
            "valid": False,
            "error": "No programming judge adapter configured.",
        }
    return {
        "result": f"{action} requires a task action adapter.",
        "valid": False,
    }


def _append_action_error(
    memory: ContestMemory,
    session: ContestSession,
    agent: str,
    error: str,
) -> None:
    memory.append(
        task_id=session.active_task.task_id if session.active_task else None,
        question_id=None,
        actor=agent,
        visibility="private",
        kind="action_error",
        payload={"error": error},
        turn=session.budget.turns_used,
    )


def _record_scoreboard(
    memory: ContestMemory,
    session: ContestSession,
) -> None:
    memory.append(
        task_id=None,
        question_id=None,
        actor="Contest_Control",
        visibility="public",
        kind="scoreboard",
        payload={"tasks": _task_rows(session)},
        turn=session.budget.turns_used,
    )


def _participation_metrics(
    memory: ContestMemory,
    manifest: ContestManifest,
    team_size: int,
) -> tuple[float, float]:
    substantive = {"speak", "direct_message", "work", "submit", "submit_code"}
    agent_names = [f"Agent_{index + 1}" for index in range(team_size)]
    aar_values: list[float] = []
    balance_values: list[float] = []
    events = memory.archival_snapshot()["events"]
    for task in manifest.tasks:
        counts = [
            sum(
                event["task_id"] == task.task_id
                and event["actor"] == agent
                and event["kind"] in substantive
                for event in events
            )
            for agent in agent_names
        ]
        active = sum(count > 0 for count in counts)
        aar_values.append(active / team_size)
        total = sum(counts)
        if total == 0:
            balance_values.append(0.0)
            continue
        ordered = sorted(counts)
        gini = sum(
            (2 * index - team_size - 1) * value
            for index, value in enumerate(ordered, start=1)
        ) / (team_size * total)
        max_gini = 1.0 - 1.0 / team_size if team_size > 1 else 1.0
        balance_values.append(max(0.0, 1.0 - gini / max_gini))
    return (
        sum(aar_values) / len(aar_values),
        sum(balance_values) / len(balance_values),
    )


def _collect_programming_deadline(
    manifest: ContestManifest,
    session: ContestSession,
    memory: ContestMemory,
    executor: TaskActionExecutor,
    persist: Callable[[], None],
    *, require_approval: bool = False,
) -> None:
    """One unattempted candidate per unsolved programming task, without LLM turns.

    Persist intent before external I/O. An interrupted/uncertain attempt is not
    retried automatically on resume, since the judge may already have received it.
    """
    events = memory.archival_snapshot()["events"]
    if not any(e["kind"] == "programming_deadline_started" for e in events):
        memory.append(
            task_id=None, question_id=None, actor="Contest_Control", visibility="public",
            kind="programming_deadline_started",
            payload={"accepted_before": [t.task_id for t in session.tasks if t.kind == "programming" and t.locked],
                     "officially_submitted_before": [t.task_id for t in session.tasks if t.kind == "programming" and t.latest_valid_submission]},
            turn=session.budget.turns_used,
        )
        persist()
    attempted = {e["task_id"] for e in events if e["kind"] == "programming_deadline_submit_started"}
    no_source = {e["task_id"] for e in events if e["kind"] == "programming_deadline_no_source"}
    task_by_id = {t.task_id: t for t in manifest.tasks}
    previous_id = session.active_task.task_id if session.active_task else None
    for task in session.tasks:
        if task.kind != "programming" or task.locked or task.task_id in attempted:
            continue
        source, selection_reason = deadline_candidate(task, events)
        if source is None:
            if selection_reason == "no_recorded_nonempty_source" and task.task_id not in no_source:
                memory.append(
                    task_id=task.task_id, question_id=None, actor="Contest_Control", visibility="public",
                    kind="programming_deadline_no_source", payload={"reason": "no_recorded_nonempty_source"},
                    turn=session.budget.turns_used,
                )
            continue  # Notes and empty drafts are never submitted as code.
        if task.state is TaskState.BLOCKED and session.budget.turns_used < (task.blocked_until_turn or 0):
            memory.append(task_id=task.task_id, question_id=None, actor="Contest_Control", visibility="public",
                          kind="programming_deadline_skipped", payload={"reason": "active_cooldown"},
                          turn=session.budget.turns_used)
            continue
        if require_approval:
            from contest_actions import _task_has_independent_approval
            if source is not task.versions[-1] or not _task_has_independent_approval(task) or not source.evidence_refs:
                memory.append(task_id=task.task_id, question_id=None, actor="Contest_Control",
                              visibility="public", kind="programming_deadline_skipped",
                              payload={"reason": "independent_approval_or_sample_evidence_required"},
                              turn=session.budget.turns_used)
                continue
        selected_version_hash = source.version_hash
        session.select_task(task.task_id)
        if source is not task.versions[-1]:
            source = session.create_answer(source.content, author=source.author,
                                           method_summary=source.method_summary, evidence_refs=source.evidence_refs)
        memory.append(
            task_id=task.task_id, question_id=None, actor="Contest_Control", visibility="public",
            kind="programming_deadline_submit_started",
            payload={"version_hash": source.version_hash, "selected_version_hash": selected_version_hash,
                     "source_identity": source_identity(source.content), "selection_reason": selection_reason,
                     "review_gate_waived": not require_approval, "sample_gate_waived": not require_approval},
            turn=session.budget.turns_used,
        )
        persist()
        try:
            deadline_executor = getattr(executor, "submit_at_deadline", None)
            result = (deadline_executor(task_by_id[task.task_id], source.content)
                      if deadline_executor is not None else
                      executor(task_by_id[task.task_id], "submit_code", {"code": source.content}))
        except Exception as exc:
            result = {"valid": False, "verdict": "SUBMIT_FAILED", "error": str(exc)}
        verdict = str(result.get("verdict") or "SUBMIT_FAILED").upper()
        valid = bool(result.get("valid", False)) and verdict not in {
            "SUBMIT_FAILED", "PENDING", "CHALLENGE", "NEEDS_HUMAN", "JUDGE_ERROR"
        } and not verdict.startswith("SAMPLE_")
        session.submit(verdict, valid=valid)
        if valid and not session.submission_policy.is_accepted(verdict):
            session.add_penalty(float(task_by_id[task.task_id].benchmark.get("wrong_submission_penalty_minutes", 20)))
        memory.append(
            task_id=task.task_id, question_id=None, actor="Contest_Control", visibility="public",
            kind="programming_deadline_submit_result",
            payload={**result, "valid": valid, "verdict": verdict, "version_hash": source.version_hash},
            turn=session.budget.turns_used,
        )
        persist()
    if previous_id is not None and not session.task(previous_id).locked and session.task(previous_id).state is not TaskState.BLOCKED:
        session.select_task(previous_id)
    elif session.active_task is not None:
        session.skip_task()
    persist()
