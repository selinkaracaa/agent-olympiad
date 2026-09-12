"""Stateful public seam for a multi-task contest."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Literal

from submission_policy import SubmissionPolicy


class TaskState(str, Enum):
    UNSEEN = "unseen"
    ACTIVE = "active"
    CANDIDATE = "candidate"
    REVIEW = "review"
    SUBMITTED = "submitted"
    BLOCKED = "blocked"
    SOLVED = "solved"


class BudgetExceededError(RuntimeError):
    """Raised before a budget operation would exceed any shared limit."""


class TaskBlockedError(RuntimeError):
    """Raised while a programming task is cooling down."""


class TaskLockedError(RuntimeError):
    """Raised after a programming task has been accepted."""


@dataclass
class ContestBudgetState:
    max_turns: int | None = None
    max_api_calls: int | None = None
    max_tokens: int | None = None
    max_simulated_minutes: float | None = None
    turns_used: int = 0
    api_calls_used: int = 0
    tokens_used: int = 0
    simulated_minutes_used: float = 0.0
    penalty_minutes: float = 0.0
    # Wall-clock accounting (not a hard budget limit; survives resume checkpoints).
    wall_started_at: str | None = None
    wall_seconds_used: float = 0.0

    def consume(
        self,
        *,
        turns: int = 0,
        api_calls: int = 0,
        tokens: int = 0,
        simulated_minutes: float = 0.0,
    ) -> None:
        increments = (turns, api_calls, tokens, simulated_minutes)
        if any(value < 0 for value in increments):
            raise ValueError("budget consumption cannot be negative")
        proposed = (
            self.turns_used + turns,
            self.api_calls_used + api_calls,
            self.tokens_used + tokens,
            self.simulated_minutes_used + simulated_minutes,
        )
        limits = (
            self.max_turns,
            self.max_api_calls,
            self.max_tokens,
            self.max_simulated_minutes,
        )
        if any(limit is not None and used > limit for used, limit in zip(proposed, limits)):
            raise BudgetExceededError("contest budget exceeded")
        (
            self.turns_used,
            self.api_calls_used,
            self.tokens_used,
            self.simulated_minutes_used,
        ) = proposed

    def add_penalty(self, minutes: float) -> None:
        if minutes < 0:
            raise ValueError("penalty minutes cannot be negative")
        self.penalty_minutes += minutes


TaskPriority = Literal["high", "normal", "low", "hopeless"]
PRIORITY_RANK: dict[str, int] = {"high": 0, "normal": 1, "low": 2, "hopeless": 3}


@dataclass(frozen=True)
class AnswerVersion:
    task_id: str
    content: str
    version_hash: str
    parent_hash: str | None = None
    part: str | None = None
    author: str = ""
    method_summary: str = ""
    evidence_refs: tuple[str, ...] = ()


@dataclass
class ReviewRecord:
    reviewer: str
    body: str
    version_hash: str
    decision: Literal["approve", "reject"] = "approve"
    stale: bool = False


@dataclass(frozen=True)
class SubmissionRecord:
    task_id: str
    version_hash: str
    verdict: str
    score: float
    valid: bool
    turn: int
    part: str | None = None


@dataclass
class TaskUnit:
    task_id: str
    kind: Literal["programming", "non_programming"] = "programming"
    parts: tuple[str, ...] = ()
    state: TaskState = TaskState.UNSEEN
    versions: list[AnswerVersion] = field(default_factory=list)
    reviews: list[ReviewRecord] = field(default_factory=list)
    submissions: list[SubmissionRecord] = field(default_factory=list)
    consecutive_non_ac: int = 0
    blocked_until_turn: int | None = None
    locked: bool = False
    # Team triage set during the contest via ``triage_problem``. ``hopeless``
    # only demotes scheduling; the latest draft is still collected at deadline.
    priority: TaskPriority = "normal"
    triage_reason: str = ""
    triaged_by: str | None = None
    triaged_turn: int | None = None

    @property
    def hopeless(self) -> bool:
        return self.priority == "hopeless"

    @property
    def priority_rank(self) -> int:
        return PRIORITY_RANK[self.priority]

    def find_duplicate_answer(
        self, content: str, *, part: str | None = None
    ) -> AnswerVersion | None:
        """Return the earliest version whose content already equals ``content``."""
        return next(
            (
                version
                for version in self.versions
                if version.content == content and version.part == part
            ),
            None,
        )

    @property
    def latest_valid_submission(self) -> SubmissionRecord | None:
        return next(
            (submission for submission in reversed(self.submissions) if submission.valid),
            None,
        )

    @property
    def part_scores(self) -> dict[str, float]:
        latest: dict[str, float] = {}
        for submission in self.submissions:
            if submission.valid and submission.part is not None:
                latest[submission.part] = submission.score
        return latest

    @property
    def score(self) -> float:
        if self.parts:
            return sum(self.part_scores.values())
        latest = self.latest_valid_submission
        return latest.score if latest is not None else 0.0

    def version(self, version_hash: str) -> AnswerVersion:
        return next(version for version in self.versions if version.version_hash == version_hash)

    @property
    def latest_submitted_answer(self) -> AnswerVersion | None:
        submission = self.latest_valid_submission
        return self.version(submission.version_hash) if submission is not None else None


class ContestSession:
    def __init__(
        self,
        tasks: list[TaskUnit],
        budget: ContestBudgetState,
        submission_policy: SubmissionPolicy | None = None,
    ) -> None:
        if not tasks:
            raise ValueError("a contest session needs at least one task")
        if len({task.task_id for task in tasks}) != len(tasks):
            raise ValueError("task ids must be unique")
        self._tasks = {task.task_id: task for task in tasks}
        self.budget = budget
        self.submission_policy = submission_policy or SubmissionPolicy()
        self._active_task_id: str | None = None
        self._events: list[dict[str, Any]] = []
        self._final_summary: dict[str, Any] | None = None

    @property
    def active_task(self) -> TaskUnit | None:
        if self._active_task_id is None:
            return None
        return self._tasks[self._active_task_id]

    @property
    def tasks(self) -> tuple[TaskUnit, ...]:
        return tuple(self._tasks.values())

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(event) for event in self._events)

    def task(self, task_id: str) -> TaskUnit:
        return self._tasks[task_id]

    def consume_budget(
        self,
        *,
        turns: int = 0,
        api_calls: int = 0,
        tokens: int = 0,
        simulated_minutes: float = 0.0,
    ) -> None:
        self.budget.consume(
            turns=turns,
            api_calls=api_calls,
            tokens=tokens,
            simulated_minutes=simulated_minutes,
        )
        self._append_event(
            "budget_consumed",
            turns=turns,
            api_calls=api_calls,
            tokens=tokens,
            simulated_minutes=simulated_minutes,
        )

    def add_penalty(self, minutes: float) -> None:
        """Record ranking penalty without consuming elapsed contest time."""
        self.budget.add_penalty(minutes)
        self._append_event("penalty_added", minutes=minutes)

    def select_task(self, task_id: str) -> TaskUnit:
        selected = self.task(task_id)
        if selected.locked:
            raise TaskLockedError(f"task {task_id!r} is locked")
        if selected.state is TaskState.BLOCKED:
            blocked_until = selected.blocked_until_turn or 0
            if self.budget.turns_used < blocked_until:
                raise TaskBlockedError(
                    f"task {task_id!r} is blocked until turn {blocked_until}"
                )
            selected.blocked_until_turn = None
            selected.consecutive_non_ac = 0
        if self.active_task is not None and self.active_task is not selected:
            previous = self.active_task
            if previous.state is TaskState.ACTIVE:
                previous.state = self._inactive_state(previous)
        if selected.state in {TaskState.UNSEEN, TaskState.ACTIVE}:
            selected.state = TaskState.ACTIVE
        self._active_task_id = task_id
        self._append_event("task_selected", task_id=task_id)
        return selected

    def revisit_task(self, task_id: str) -> TaskUnit:
        return self.select_task(task_id)

    def skip_task(self) -> TaskUnit:
        task = self._require_active_task()
        if task.state is TaskState.ACTIVE:
            task.state = self._inactive_state(task)
        self._active_task_id = None
        self._append_event("task_skipped", task_id=task.task_id)
        return task

    def set_triage(
        self,
        task_id: str,
        priority: TaskPriority,
        *,
        reason: str = "",
        actor: str | None = None,
        turn: int | None = None,
    ) -> tuple[TaskUnit, TaskPriority]:
        """Record team triage for a task; returns the task and its previous priority."""
        if priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)!r}")
        task = self.task(task_id)
        previous = task.priority
        task.priority = priority
        task.triage_reason = reason
        task.triaged_by = actor
        task.triaged_turn = turn
        self._append_event(
            "task_triaged",
            task_id=task_id,
            priority=priority,
            previous_priority=previous,
            actor=actor,
        )
        return task, previous

    def create_answer(
        self,
        content: str,
        *,
        part: str | None = None,
        author: str = "",
        method_summary: str = "",
        evidence_refs: tuple[str, ...] = (),
    ) -> AnswerVersion:
        task = self._require_active_task()
        if task.locked:
            raise TaskLockedError(f"task {task.task_id!r} is locked")
        self._validate_part(task, part)
        if task.versions:
            latest = task.versions[-1]
            if (
                latest.content == content
                and latest.part == part
                and latest.method_summary == method_summary
                and latest.evidence_refs == tuple(evidence_refs)
            ):
                return latest
        parent = task.versions[-1].version_hash if task.versions else None
        digest_input = "\0".join((task.task_id, part or "", parent or "", content))
        version = AnswerVersion(
            task_id=task.task_id,
            content=content,
            version_hash=hashlib.sha256(digest_input.encode("utf-8")).hexdigest(),
            parent_hash=parent,
            part=part,
            author=author,
            method_summary=method_summary,
            evidence_refs=tuple(evidence_refs),
        )
        for review in task.reviews:
            review.stale = True
        task.versions.append(version)
        task.state = TaskState.CANDIDATE
        self._append_event(
            "answer_created",
            task_id=task.task_id,
            version_hash=version.version_hash,
            parent_hash=version.parent_hash,
            part=part,
        )
        return version

    def record_review(
        self,
        reviewer: str,
        body: str,
        *,
        decision: Literal["approve", "reject"] = "approve",
    ) -> ReviewRecord:
        task = self._require_active_task()
        return self.record_task_review(
            task.task_id,
            reviewer,
            body,
            decision=decision,
        )

    def record_task_review(
        self,
        task_id: str,
        reviewer: str,
        body: str,
        *,
        decision: Literal["approve", "reject"] = "approve",
        version_hash: str | None = None,
    ) -> ReviewRecord:
        task = self.task(task_id)
        if task.locked:
            raise TaskLockedError(f"task {task.task_id!r} is locked")
        if not task.versions:
            raise ValueError("an answer version is required before review")
        version = task.versions[-1]
        if version_hash is not None and version.version_hash != version_hash:
            raise ValueError("review must target the current answer version")
        if version.author and reviewer == version.author:
            raise ValueError("reviewer must differ from answer author")
        review = ReviewRecord(
            reviewer=reviewer,
            body=body,
            version_hash=version.version_hash,
            decision=decision,
        )
        task.reviews.append(review)
        task.state = TaskState.REVIEW
        self._append_event(
            "review_recorded",
            task_id=task.task_id,
            reviewer=reviewer,
            version_hash=review.version_hash,
            decision=decision,
        )
        return review

    def has_independent_approval(self) -> bool:
        task = self._require_active_task()
        if not task.versions:
            return False
        version = task.versions[-1]
        current_reviews = [
            review
            for review in task.reviews
            if not review.stale and review.version_hash == version.version_hash
        ]
        if any(review.decision == "reject" for review in current_reviews):
            return False
        return any(
            review.decision == "approve"
            and review.reviewer != version.author
            for review in current_reviews
        )

    def has_independent_review(self) -> bool:
        """True when a different agent reviewed the current version (any decision)."""
        task = self._require_active_task()
        if not task.versions:
            return False
        version = task.versions[-1]
        return any(
            not review.stale
            and review.version_hash == version.version_hash
            and review.reviewer != version.author
            for review in task.reviews
        )

    def submit(
        self,
        verdict: str,
        *,
        score: float | None = None,
        valid: bool = True,
        part: str | None = None,
    ) -> SubmissionRecord:
        task = self._require_active_task()
        if task.locked:
            raise TaskLockedError(f"task {task.task_id!r} is locked")
        if task.state is TaskState.BLOCKED:
            raise TaskBlockedError(f"task {task.task_id!r} is blocked")
        if not task.versions:
            raise ValueError("an answer version is required before submission")
        self._validate_part(task, part)
        if task.versions[-1].part != part:
            raise ValueError("submission part must match the latest answer version")
        accepted = self.submission_policy.is_accepted(verdict)
        submission = SubmissionRecord(
            task_id=task.task_id,
            version_hash=task.versions[-1].version_hash,
            verdict=verdict.upper(),
            score=float(1.0 if score is None and accepted else score or 0.0),
            valid=valid,
            turn=self.budget.turns_used,
            part=part,
        )
        task.submissions.append(submission)
        if task.kind == "programming":
            task.state = TaskState.SUBMITTED
            if accepted and valid:
                task.locked = True
                task.consecutive_non_ac = 0
                task.state = TaskState.SOLVED
            elif valid:
                task.consecutive_non_ac += 1
                if self.submission_policy.should_block(task.consecutive_non_ac):
                    task.state = TaskState.BLOCKED
                    task.blocked_until_turn = (
                        self.budget.turns_used + self.submission_policy.cooldown_turns
                    )
        elif task.parts:
            task.state = (
                TaskState.SOLVED
                if set(task.part_scores) == set(task.parts)
                else TaskState.SUBMITTED
            )
        elif valid:
            task.state = TaskState.SOLVED
        elif task.latest_valid_submission is not None:
            task.state = TaskState.SOLVED
        self._append_event(
            "submission_recorded",
            task_id=task.task_id,
            verdict=submission.verdict,
            score=submission.score,
            valid=submission.valid,
            version_hash=submission.version_hash,
            part=part,
        )
        return submission

    def finalize(self) -> dict[str, Any]:
        if self._final_summary is None:
            tasks: dict[str, dict[str, Any]] = {}
            for task_id, task in self._tasks.items():
                if task.kind == "programming":
                    score = task.score if task.state is TaskState.SOLVED else 0.0
                else:
                    score = task.score
                tasks[task_id] = {
                    "kind": task.kind,
                    "state": task.state.value,
                    "score": float(score),
                    "part_scores": task.part_scores,
                    "terminal_verdict": (
                        task.submissions[-1].verdict
                        if task.submissions
                        else "NO_AC"
                        if task.kind == "programming"
                        else "NO_VALID_SUBMISSION"
                    ),
                }
            self._final_summary = {
                "tasks": tasks,
                "total_score": sum(row["score"] for row in tasks.values()),
            }
            self._append_event("finalized", total_score=self._final_summary["total_score"])
        return {
            "tasks": {
                task_id: dict(row)
                for task_id, row in self._final_summary["tasks"].items()
            },
            "total_score": self._final_summary["total_score"],
        }

    def checkpoint(self) -> dict[str, Any]:
        return {
            "budget": asdict(self.budget),
            "submission_policy": asdict(self.submission_policy),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "kind": task.kind,
                    "parts": list(task.parts),
                    "state": task.state.value,
                    "versions": [
                        {
                            **asdict(version),
                            "evidence_refs": list(version.evidence_refs),
                        }
                        for version in task.versions
                    ],
                    "reviews": [asdict(review) for review in task.reviews],
                    "submissions": [
                        asdict(submission) for submission in task.submissions
                    ],
                    "consecutive_non_ac": task.consecutive_non_ac,
                    "blocked_until_turn": task.blocked_until_turn,
                    "locked": task.locked,
                    "priority": task.priority,
                    "triage_reason": task.triage_reason,
                    "triaged_by": task.triaged_by,
                    "triaged_turn": task.triaged_turn,
                }
                for task in self._tasks.values()
            ],
            "active_task_id": self._active_task_id,
            "events": [dict(event) for event in self._events],
            "final_summary": self._final_summary,
        }

    @classmethod
    def from_checkpoint(cls, checkpoint: dict[str, Any]) -> ContestSession:
        tasks: list[TaskUnit] = []
        for data in checkpoint["tasks"]:
            task = TaskUnit(
                task_id=data["task_id"],
                kind=data["kind"],
                parts=tuple(data["parts"]),
                state=TaskState(data["state"]),
                versions=[
                    AnswerVersion(
                        **{
                            **version,
                            "evidence_refs": tuple(version.get("evidence_refs", ())),
                        }
                    )
                    for version in data["versions"]
                ],
                reviews=[ReviewRecord(**review) for review in data["reviews"]],
                submissions=[
                    SubmissionRecord(**submission)
                    for submission in data["submissions"]
                ],
                consecutive_non_ac=data["consecutive_non_ac"],
                blocked_until_turn=data["blocked_until_turn"],
                locked=data["locked"],
                priority=data.get("priority", "normal"),
                triage_reason=data.get("triage_reason", ""),
                triaged_by=data.get("triaged_by"),
                triaged_turn=data.get("triaged_turn"),
            )
            tasks.append(task)
        session = cls(
            tasks=tasks,
            budget=ContestBudgetState(**checkpoint["budget"]),
            submission_policy=SubmissionPolicy(**checkpoint["submission_policy"]),
        )
        session._active_task_id = checkpoint["active_task_id"]
        session._events = [dict(event) for event in checkpoint["events"]]
        session._final_summary = checkpoint["final_summary"]
        return session

    def _require_active_task(self) -> TaskUnit:
        task = self.active_task
        if task is None:
            raise RuntimeError("select a task first")
        return task

    @staticmethod
    def _validate_part(task: TaskUnit, part: str | None) -> None:
        if task.parts and part not in task.parts:
            raise ValueError(f"part must be one of {task.parts!r}")
        if not task.parts and part is not None:
            raise ValueError("this task has no parts")

    @staticmethod
    def _inactive_state(task: TaskUnit) -> TaskState:
        if task.locked:
            return TaskState.SOLVED
        if task.blocked_until_turn is not None:
            return TaskState.BLOCKED
        if task.submissions:
            if task.kind == "non_programming":
                complete = not task.parts or set(task.part_scores) == set(task.parts)
                if complete and task.latest_valid_submission is not None:
                    return TaskState.SOLVED
            return TaskState.SUBMITTED
        if task.reviews and not task.reviews[-1].stale:
            return TaskState.REVIEW
        if task.versions:
            return TaskState.CANDIDATE
        return TaskState.UNSEEN

    def _append_event(self, event_type: str, **payload: Any) -> None:
        self._events.append(
            {
                "event_id": f"session-event-{len(self._events) + 1:06d}",
                "sequence": len(self._events) + 1,
                "type": event_type,
                **payload,
            }
        )
