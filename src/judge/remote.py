"""Remote programming-judge submission protocol (platform-agnostic)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

RemoteStatus = Literal[
    "queued",
    "submitted",
    "polling",
    "final",
    "needs_human",
    "failed",
]

NormalizedVerdict = Literal[
    "AC",
    "WA",
    "TLE",
    "MLE",
    "OLE",
    "RE",
    "CE",
    "PENDING",
    "SUBMIT_FAILED",
    "LOGIN_FAILED",
    "CHALLENGE",
    "UNKNOWN",
]


@dataclass(frozen=True)
class RemoteSubmitRequest:
    """Remote submit payload.

    - Problem mode (preferred): ``contest_id=""``, ``oj="CodeForces"``,
      ``problem="4A"`` → VJudge ``/problem/submit/CodeForces-4A``.
    - Contest mode: ``contest_id="845103"``, ``problem="A"`` → contest letter.
    """

    problem: str
    language: str
    source: str
    contest_id: str = ""
    oj: str = "CodeForces"
    idempotency_key: str = ""
    open_source: bool = False


@dataclass
class RemoteRun:
    run_id: str
    status: RemoteStatus
    verdict: NormalizedVerdict = "PENDING"
    remote_run_id: str | None = None
    time_ms: int | None = None
    memory_kb: int | None = None
    message: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    poll_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


class SubmissionProvider(Protocol):
    def submit(self, request: RemoteSubmitRequest) -> RemoteRun: ...

    def get_result(self, run_id: str) -> RemoteRun: ...
