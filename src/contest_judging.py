"""Checkpointed remote verdict delivery for rule-card judging latency."""
from __future__ import annotations

from dataclasses import replace
from typing import Any
from contest_memory import ContestMemory
from contest_session import ContestSession, TaskUnit


def queue_verdict(session: ContestSession, memory: ContestMemory, task: TaskUnit,
                  result: dict[str, Any], latency: int, penalty: float) -> None:
    """Keep the actual verdict controller-private until the next eligible turn."""
    session.submit("PENDING", valid=False)
    memory.append(
        task_id=task.task_id, question_id=None, actor="Contest_Control",
        visibility="private", recipients=("Contest_Control",),
        kind="verdict_queued",
        payload={"result": result, "version_hash": task.versions[-1].version_hash,
                 "available_turn": session.budget.turns_used + latency, "penalty": penalty},
        turn=session.budget.turns_used,
    )


def deliver_verdicts(session: ContestSession, memory: ContestMemory, *, final: bool = False) -> None:
    """Deliver each queued result once; final delivery has no contestant observers."""
    events = memory.archival_snapshot()["events"]
    delivered = {e["payload"]["queued_event_id"] for e in events if e["kind"] == "verdict_delivered"}
    previous = session.active_task.task_id if session.active_task else None
    changed = False
    for event in events:
        if event["kind"] != "verdict_queued" or event["event_id"] in delivered:
            continue
        payload = event["payload"]
        if not final and session.budget.turns_used < payload["available_turn"]:
            continue
        task = session.task(event["task_id"])
        changed = True
        if not task.versions or task.versions[-1].version_hash != payload["version_hash"]:
            raise RuntimeError("Pending submission source changed before verdict delivery")
        session.select_task(task.task_id)
        if task.submissions and task.submissions[-1].verdict == "PENDING":
            task.submissions.pop()
        result = payload["result"]
        verdict = str(result.get("verdict") or "SUBMIT_FAILED").upper()
        valid = bool(result.get("valid", True))
        submission = session.submit(verdict, valid=valid)
        # Rank by when the code was sent, not when its delayed verdict arrived.
        task.submissions[-1] = replace(submission, turn=event['turn'])
        memory.append(task_id=task.task_id, question_id=None, actor="Judge",
                      visibility="public", kind="submit_code_result", payload=result,
                      turn=session.budget.turns_used)
        if valid and verdict != "AC":
            memory.append(task_id=task.task_id, question_id=None, actor="Judge",
                          visibility="public", kind="reopen",
                          payload={"verdict": verdict, "version_hash": payload["version_hash"]},
                          turn=session.budget.turns_used)
        if valid and verdict not in {"AC", "SUBMIT_FAILED", "PENDING"}:
            session.add_penalty(float(payload["penalty"]))
        memory.append(task_id=task.task_id, question_id=None, actor="Contest_Control",
                      visibility="private", recipients=("Contest_Control",),
                      kind="verdict_delivered", payload={"queued_event_id": event["event_id"]},
                      turn=session.budget.turns_used)
    if changed and previous is not None:
        task = session.task(previous)
        if not task.locked and task.state.value != "blocked":
            session.select_task(previous)
        else:
            session.skip_task()
    elif changed and session.active_task is not None:
        session.skip_task()
