"""OTC programming repair progress, separate from official verdict penalties.

Worker/task visits are counted, not movements of the team's active cursor.
Rotation records live in contest memory so restoring a checkpoint preserves
both unfinished repair budgets and the order in which tasks yielded.
"""
from __future__ import annotations

from dataclasses import dataclass

from contest_memory import ContestMemory


@dataclass
class WorkerProgress:
    unproductive_actions: int = 0
    yielded_at: int = 0
    actions_without_source: int = 0


class ProgrammingProgress:
    def __init__(self, memory: ContestMemory, *, stall_actions: int):
        self.memory = memory
        self.stall_actions = stall_actions
        self.workers: dict[tuple[str, str], WorkerProgress] = {}
        self.sequence = 0
        for event in memory.archival_snapshot()["events"]:
            if event["kind"] == "programming_worker_progress":
                row = event["payload"]
                self.workers[(event["actor"], event["task_id"])] = WorkerProgress(
                    row["unproductive_actions"], row["yielded_at"],
                    row.get("actions_without_source", 0),
                )
                self.sequence = max(self.sequence, row["yielded_at"])

    def ordered_tasks(self, agent: str, task_ids: list[str]) -> list[str]:
        # Stable sort retains Coach ordering until a worker exhausts a repair
        # budget. Yielded tasks move behind alternatives and remain revisitable.
        return sorted(task_ids, key=lambda task_id: self.workers.get(
            (agent, task_id), WorkerProgress()
        ).yielded_at)

    def source_required(self, agent: str, task_id: str) -> bool:
        return self.workers.get((agent, task_id), WorkerProgress()).actions_without_source >= 2

    def record(self, agent: str, task_id: str, *, turn: int, progressed: bool,
               source_attempted: bool = False) -> bool:
        state = self.workers.setdefault((agent, task_id), WorkerProgress())
        state.actions_without_source = (
            0 if source_attempted or progressed else state.actions_without_source + 1
        )
        state.unproductive_actions = 0 if progressed else state.unproductive_actions + 1
        yielded = state.unproductive_actions >= self.stall_actions
        if yielded:
            self.sequence += 1
            state.yielded_at = self.sequence
            state.unproductive_actions = 0
        self.memory.append(
            task_id=task_id, question_id=None, actor=agent, visibility="private",
            recipients=(agent,), kind="programming_worker_progress",
            payload={"unproductive_actions": state.unproductive_actions,
                     "yielded_at": state.yielded_at, "progressed": progressed,
                     "yielded": yielded,
                     "actions_without_source": state.actions_without_source}, turn=turn,
        )
        if yielded:
            self.memory.append(
                task_id=task_id, question_id=None, actor="Contest_Scheduler",
                visibility="private", recipients=(agent,),
                kind="programming_repair_yield",
                payload={"agent": agent, "reason": "no_programming_progress",
                         "action_limit": self.stall_actions,
                         "message": "Repair budget used; try another assigned task before revisiting."},
                turn=turn,
            )
        return yielded
