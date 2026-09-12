"""Scoped, append-only memory for a single contest session."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Literal

Visibility = Literal["public", "private", "group", "judge"]
_VISIBILITIES = {"public", "private", "group", "judge"}
_FORBIDDEN_KINDS = {
    "answer_key",
    "gold",
    "gold_answer",
    "hidden_test",
    "hidden_tests",
    "judge_feedback",
    "oracle",
}
# Personal (``note``) and team-published (``note_shared``) bookkeeping events
# written by the ``remember`` / ``share_note`` actions.
_NOTE_KINDS = {"note", "note_shared"}
# Public team talk surfaced by ``strategic_projection(max_team_messages=...)``.
_TEAM_MESSAGE_KINDS = {
    "speak",
    "note_shared",
    "propose",
    "challenge",
    "provide_evidence",
    "revise",
    "decide",
    "coach_opening_summary",
}
_FORBIDDEN_KEYS = {
    "answer_key",
    "expected_output",
    "gold",
    "gold_answer",
    "gold_solution",
    "hidden_test",
    "hidden_tests",
    "judge_only",
    "oracle",
    "secret",
}


def _json_copy(value: Any) -> Any:
    """Validate and detach a JSON value from caller-owned mutable objects."""
    try:
        return json.loads(json.dumps(value, ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise TypeError("Contest memory payloads must be JSON-serializable.") from exc


def _normalise_label(value: str) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _sanitise(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _sanitise(item)
            for key, item in value.items()
            if _normalise_label(str(key)) not in _FORBIDDEN_KEYS
        }
    if isinstance(value, list):
        return [_sanitise(item) for item in value]
    return value


@dataclass(frozen=True)
class ContestEvent:
    event_id: str
    run_id: str
    session_id: str
    competition_id: str
    task_id: str | None
    question_id: str | None
    actor: str
    visibility: Visibility
    recipients: tuple[str, ...]
    kind: str
    payload: Any
    turn: int

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["recipients"] = list(self.recipients)
        return row


@dataclass(frozen=True)
class ProblemDigest:
    digest_id: str
    task_id: str
    created_turn: int
    created_by: str
    source_event_ids: tuple[str, ...]
    entries: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["source_event_ids"] = list(self.source_event_ids)
        row["entries"] = _json_copy(list(self.entries))
        return row


class ContestMemory:
    """An append-only event ledger bounded to one run and session."""

    CHECKPOINT_VERSION = 1

    def __init__(self, *, run_id: str, session_id: str, competition_id: str):
        self.run_id = self._required_id("run_id", run_id)
        self.session_id = self._required_id("session_id", session_id)
        self.competition_id = self._required_id("competition_id", competition_id)
        self._events: list[ContestEvent] = []
        self._digests: list[ProblemDigest] = []

    @staticmethod
    def _required_id(name: str, value: str) -> str:
        result = str(value).strip()
        if not result:
            raise ValueError(f"{name} cannot be empty.")
        return result

    @property
    def scope(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "competition_id": self.competition_id,
        }

    def append(
        self,
        *,
        task_id: str | None,
        question_id: str | None,
        actor: str,
        visibility: Visibility,
        kind: str,
        payload: Any,
        turn: int,
        recipients: Iterable[str] = (),
    ) -> ContestEvent:
        """Append one immutable event and return its detached value."""
        actor = self._required_id("actor", actor)
        kind = self._required_id("kind", kind)
        if visibility not in _VISIBILITIES:
            raise ValueError(f"Unsupported visibility: {visibility!r}.")
        recipient_tuple = tuple(
            dict.fromkeys(
                self._required_id("recipient", recipient) for recipient in recipients
            )
        )
        if visibility == "group" and not recipient_tuple:
            raise ValueError("Group events require at least one recipient group.")
        if isinstance(turn, bool) or not isinstance(turn, int) or turn < 0:
            raise ValueError("turn must be a non-negative integer.")

        event = ContestEvent(
            event_id=f"event-{len(self._events) + 1:06d}",
            **self.scope,
            task_id=None if task_id is None else str(task_id),
            question_id=None if question_id is None else str(question_id),
            actor=actor,
            visibility=visibility,
            recipients=recipient_tuple,
            kind=kind,
            payload=_json_copy(payload),
            turn=turn,
        )
        self._events.append(event)
        return self._copy_event(event)

    @staticmethod
    def _copy_event(event: ContestEvent) -> ContestEvent:
        row = event.to_dict()
        row["recipients"] = tuple(row["recipients"])
        return ContestEvent(**row)

    @staticmethod
    def _can_view(
        event: ContestEvent,
        viewer: str,
        groups: set[str],
        is_judge: bool,
    ) -> bool:
        if event.visibility == "public":
            return True
        if event.visibility == "private":
            return viewer == event.actor or viewer in event.recipients
        if event.visibility == "group":
            return viewer == event.actor or bool(groups.intersection(event.recipients))
        return is_judge

    def view(
        self,
        viewer: str,
        *,
        groups: Iterable[str] = (),
        is_judge: bool = False,
        task_id: str | None = None,
    ) -> list[ContestEvent]:
        """Return the events visible to a contestant or judge."""
        viewer = self._required_id("viewer", viewer)
        group_set = {str(group) for group in groups}
        return [
            self._copy_event(event)
            for event in self._events
            if (task_id is None or event.task_id == task_id)
            and self._can_view(event, viewer, group_set, is_judge)
        ]

    def archival_snapshot(self) -> dict[str, Any]:
        """Return the complete, unfiltered archive for durable storage."""
        return {
            "version": self.CHECKPOINT_VERSION,
            "scope": dict(self.scope),
            "events": [event.to_dict() for event in self._events],
            "digests": [digest.to_dict() for digest in self._digests],
        }

    def to_checkpoint_json(self) -> str:
        return json.dumps(
            self.archival_snapshot(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_checkpoint_json(
        cls,
        checkpoint: str,
        *,
        expected_run_id: str | None = None,
        expected_session_id: str | None = None,
        expected_competition_id: str | None = None,
    ) -> "ContestMemory":
        try:
            data = json.loads(checkpoint)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid contest memory checkpoint JSON.") from exc
        if data.get("version") != cls.CHECKPOINT_VERSION:
            raise ValueError("Unsupported contest memory checkpoint version.")
        scope = data.get("scope")
        if not isinstance(scope, dict):
            raise ValueError("Checkpoint is missing its contest scope.")
        expected = {
            "run_id": expected_run_id,
            "session_id": expected_session_id,
            "competition_id": expected_competition_id,
        }
        for key, value in expected.items():
            if value is not None and scope.get(key) != value:
                raise ValueError(f"Checkpoint {key} does not match expected scope.")

        memory = cls(
            run_id=scope.get("run_id", ""),
            session_id=scope.get("session_id", ""),
            competition_id=scope.get("competition_id", ""),
        )
        events = data.get("events")
        digests = data.get("digests")
        if not isinstance(events, list) or not isinstance(digests, list):
            raise ValueError("Checkpoint events and digests must be lists.")
        for index, row in enumerate(events, start=1):
            if not isinstance(row, dict):
                raise ValueError("Checkpoint contains an invalid event.")
            if row.get("event_id") != f"event-{index:06d}":
                raise ValueError("Checkpoint event IDs are not a stable sequence.")
            for key, value in memory.scope.items():
                if row.get(key) != value:
                    raise ValueError("Checkpoint event escapes its declared scope.")
            restored = dict(row)
            restored["recipients"] = tuple(restored.get("recipients", ()))
            restored["payload"] = _json_copy(restored.get("payload"))
            try:
                event = ContestEvent(**restored)
            except TypeError as exc:
                raise ValueError("Checkpoint contains an invalid event.") from exc
            if event.visibility not in _VISIBILITIES:
                raise ValueError("Checkpoint contains an invalid visibility.")
            memory._events.append(event)
        for index, row in enumerate(digests, start=1):
            if not isinstance(row, dict) or row.get("digest_id") != f"digest-{index:06d}":
                raise ValueError("Checkpoint digest IDs are not a stable sequence.")
            restored = dict(row)
            restored["source_event_ids"] = tuple(restored.get("source_event_ids", ()))
            restored["entries"] = tuple(_json_copy(restored.get("entries", ())))
            try:
                memory._digests.append(ProblemDigest(**restored))
            except TypeError as exc:
                raise ValueError("Checkpoint contains an invalid digest.") from exc
        return memory

    def create_problem_digest(
        self,
        task_id: str,
        *,
        viewer: str,
        groups: Iterable[str] = (),
        is_judge: bool = False,
        max_events: int = 12,
    ) -> ProblemDigest:
        """Create a compact task digest without evaluation-only material."""
        task_id = self._required_id("task_id", task_id)
        if max_events < 1:
            raise ValueError("max_events must be positive.")
        candidates = [
            event
            for event in self.view(
                viewer, groups=groups, is_judge=is_judge, task_id=task_id
            )
            if event.visibility != "judge"
            and _normalise_label(event.kind) not in _FORBIDDEN_KINDS
        ][-max_events:]
        entries = tuple(
            {
                "event_id": event.event_id,
                "turn": event.turn,
                "actor": event.actor,
                "kind": event.kind,
                "payload": _sanitise(event.payload),
            }
            for event in candidates
        )
        digest = ProblemDigest(
            digest_id=f"digest-{len(self._digests) + 1:06d}",
            task_id=task_id,
            created_turn=max((event.turn for event in candidates), default=0),
            created_by=self._required_id("viewer", viewer),
            source_event_ids=tuple(event.event_id for event in candidates),
            entries=entries,
        )
        self._digests.append(digest)
        return ProblemDigest(**{
            **digest.to_dict(),
            "source_event_ids": tuple(digest.source_event_ids),
            "entries": tuple(_json_copy(digest.entries)),
        })

    def strategic_projection(
        self,
        *,
        viewer: str,
        current_task_id: str,
        groups: Iterable[str] = (),
        is_judge: bool = False,
        max_current_events: int = 8,
        max_recent_digests: int = 4,
        max_procedural_lessons: int = 6,
        max_direct_messages: int = 8,
        max_recent_notes: int = 4,
        max_team_messages: int = 0,
        max_chars: int = 8000,
    ) -> dict[str, Any]:
        """Build a bounded working-memory view, never the full archive.

        ``max_team_messages`` (off by default) adds a ``team_messages`` slice:
        the latest public ``speak`` / shared-note / deliberation events across
        every task, so a rule card's ``public_messages`` allowance can be
        honoured without widening the per-task event window.
        """
        limits = (
            max_current_events,
            max_recent_digests,
            max_procedural_lessons,
            max_direct_messages,
            max_recent_notes,
            max_team_messages,
        )
        if any(limit < 0 for limit in limits) or max_chars < 256:
            raise ValueError("Projection limits must be non-negative; max_chars >= 256.")
        visible = self.view(viewer, groups=groups, is_judge=is_judge)
        capsule = next(
            (event.payload for event in reversed(visible) if event.kind == "contest_capsule"),
            None,
        )
        scoreboard = next(
            (event.payload for event in reversed(visible) if event.kind == "scoreboard"),
            None,
        )
        current = [
            {
                "event_id": event.event_id,
                "question_id": event.question_id,
                "turn": event.turn,
                "actor": event.actor,
                "kind": event.kind,
                "payload": event.payload,
            }
            for event in visible
            if event.task_id == current_task_id
            and event.kind not in {
                "contest_capsule",
                "scoreboard",
                "procedural_lesson",
                "direct_message",
                "programming_worker_progress",
                "programming_source_recorded",
                "programming_source_required",
                # Private deliberation is surfaced through its own ledger.
                "think",
            }
        ][-max_current_events:] if max_current_events else []
        team_messages = [
            {
                "event_id": event.event_id,
                "task_id": event.task_id,
                "turn": event.turn,
                "actor": event.actor,
                "kind": event.kind,
                "payload": event.payload,
            }
            for event in visible
            if event.visibility == "public" and event.kind in _TEAM_MESSAGE_KINDS
        ][-max_team_messages:] if max_team_messages else []
        lessons = [
            {
                "event_id": event.event_id,
                "turn": event.turn,
                "payload": event.payload,
            }
            for event in visible
            if event.kind == "procedural_lesson"
        ][-max_procedural_lessons:] if max_procedural_lessons else []
        direct_messages = [
            {
                "event_id": event.event_id,
                "task_id": event.task_id,
                "turn": event.turn,
                "actor": event.actor,
                "recipients": list(event.recipients),
                "payload": event.payload,
            }
            for event in visible
            if event.kind == "direct_message"
        ][-max_direct_messages:] if max_direct_messages else []
        digests = [
            digest.to_dict()
            for digest in self._digests
            if digest.created_by == viewer and digest.task_id != current_task_id
        ][-max_recent_digests:] if max_recent_digests else []
        # Notes on the current task already appear in current_task_events;
        # recent_notes carries the viewer's notes from elsewhere so cross-task
        # reminders survive without a recall call.
        current_ids = {row["event_id"] for row in current}
        notes = [
            self._note_row(event)
            for event in visible
            if self._is_note(event) and event.event_id not in current_ids
        ][-max_recent_notes:] if max_recent_notes else []
        projection = {
            "scope": dict(self.scope),
            "contest_capsule": _json_copy(capsule),
            "scoreboard": _json_copy(scoreboard),
            "current_task_id": current_task_id,
            "current_task_events": current,
            "recent_digests": digests,
            "recent_notes": notes,
            "procedural_lessons": lessons,
            "direct_messages": direct_messages,
        }
        if max_team_messages:
            projection["team_messages"] = team_messages
        self._shrink_to_budget(projection, max_chars)
        return projection

    @staticmethod
    def _is_note(event: ContestEvent) -> bool:
        """True for ``remember`` / ``share_note`` events (dict payload with content)."""
        return (
            event.kind in _NOTE_KINDS
            and isinstance(event.payload, dict)
            and bool(str(event.payload.get("content") or "").strip())
        )

    @staticmethod
    def _note_row(event: ContestEvent) -> dict[str, Any]:
        payload = event.payload if isinstance(event.payload, dict) else {}
        return {
            "note_id": event.event_id,
            "kind": event.kind,
            "task_id": event.task_id,
            "turn": event.turn,
            "author": str(payload.get("author") or event.actor),
            "shared": event.kind == "note_shared",
            "content": str(payload.get("content") or ""),
        }

    def recall(
        self,
        viewer: str,
        *,
        query: str = "",
        problem_id: str | None = None,
        groups: Iterable[str] = (),
        top_k: int | None = 8,
    ) -> list[dict[str, Any]]:
        """Rank the viewer's own notes and team-shared notes.

        Ordering mirrors the legacy ``MemoryStore.recall``: exact problem tag
        first, then query-term hits, then recency; identical contents are
        collapsed so a shared copy does not shadow its private original.
        """
        viewer = self._required_id("viewer", viewer)
        terms = {term.lower() for term in str(query or "").split() if len(term) > 1}
        wanted = str(problem_id or "").strip().lower()
        candidates = [
            self._note_row(event)
            for event in self.view(viewer, groups=groups)
            if self._is_note(event)
        ]
        candidates.sort(
            key=lambda row: (
                bool(wanted) and str(row["task_id"] or "").lower() == wanted,
                sum(term in row["content"].lower() for term in terms),
                row["turn"],
                row["note_id"],
            ),
            reverse=True,
        )
        selected: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in candidates:
            key = row["content"].strip()
            if key in seen:
                continue
            seen.add(key)
            selected.append(row)
            if top_k is not None and len(selected) >= max(1, int(top_k)):
                break
        return selected

    @staticmethod
    def _shrink_to_budget(projection: dict[str, Any], max_chars: int) -> None:
        def size() -> int:
            return len(json.dumps(projection, ensure_ascii=False, sort_keys=True))

        lists = (
            projection["current_task_events"],
            projection["recent_digests"],
            projection["recent_notes"],
            projection["procedural_lessons"],
            projection["direct_messages"],
            projection.get("team_messages", []),
        )
        while size() > max_chars and any(lists):
            largest = max((items for items in lists if items), key=lambda items: len(
                json.dumps(items[0], ensure_ascii=False)
            ))
            largest.pop(0)
        if size() > max_chars:
            projection["contest_capsule"] = {"truncated": True}
            projection["scoreboard"] = {"truncated": True}
        if size() > max_chars:
            raise ValueError("max_chars is too small for the projection envelope.")
