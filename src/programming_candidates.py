"""Programming-only candidate identity, failed-run reuse and deadline selection."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from contest_session import AnswerVersion, TaskUnit
from evaluation.programming_judge import _extract_source


def source_identity(code: str) -> str:
    # Match the actual judge's fence/whitespace/language extraction. Parent hashes
    # and commentary metadata are not program identity. Do not strip comments.
    source, language = _extract_source(code)
    return hashlib.sha256((language + "\0" + source).encode("utf-8")).hexdigest()


def execution_key(task, arguments: dict[str, Any], executor) -> str | None:
    context_fn = getattr(executor, "execution_context_key", None)
    context = context_fn(task) if callable(context_fn) else "injected-executor"
    if context is None:
        return None  # Executor cannot establish a stable test identity.
    payload = ["failed-execution-v1", task.task_id, task.benchmark, context,
               source_identity(str(arguments.get("code") or "")), arguments.get("language")]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def failed_execution(events: list[dict], task_id: str, key: str | None) -> dict | None:
    if key is None:
        return None
    for event in reversed(events):
        payload = event["payload"]
        if (event["task_id"] == task_id and event["kind"] == "sample_judge_result"
                and payload.get("execution_key") == key):
            # Only the latest result for this exact test context is reusable.
            if payload.get("execution_valid") and payload.get("sample_verdict") in {"WA", "RE", "CE", "TLE", "MLE", "OLE"}:
                return {"valid": True, "sample_verdict": payload["sample_verdict"],
                        "sample_cases": payload.get("sample_cases") or [],
                        "sample_summary": payload.get("sample_summary"),
                        "execution_reused": True,
                        "result": "Identical source already failed these tests; execution was not repeated. "
                                  "Revise the source to address the recorded failure. The active candidate is unchanged."}
            return None
    return None


def deadline_candidate(task: TaskUnit, events: list[dict]) -> tuple[AnswerVersion | None, str]:
    """Select one unattempted source: sample AC first, then approval, then recency."""
    recorded = set()
    samples = {}
    for event in events:
        if event["task_id"] != task.task_id:
            continue
        if event["kind"] in {"programming_source_recorded", "sample_judge_result"}:
            recorded.add(event["payload"].get("version_hash"))
        if event["kind"] == "sample_judge_result":
            samples[event["payload"].get("version_hash")] = event["payload"].get("sample_verdict")
    attempted_hashes = {s.version_hash for s in task.submissions
                        if s.valid or not s.verdict.upper().startswith("SAMPLE_")}
    attempted_sources = {source_identity(v.content) for v in task.versions if v.version_hash in attempted_hashes}
    sources = [(i, v) for i, v in enumerate(task.versions) if v.content.strip() and v.version_hash in recorded]
    candidates = [(i, v) for i, v in sources if source_identity(v.content) not in attempted_sources]
    if not candidates:
        return None, "no_unsubmitted_source" if sources else "no_recorded_nonempty_source"

    def rank(item):
        index, version = item
        sample_ac = samples.get(version.version_hash) == "AC"
        reviews = [r for r in task.reviews if r.version_hash == version.version_hash and r.reviewer != version.author]
        # Stale means not-current, not invalid: reviews still describe this exact
        # historical version. Approval is only a tiebreaker among sample peers.
        approved = any(r.decision == "approve" for r in reviews) and not any(r.decision == "reject" for r in reviews)
        return sample_ac, approved, index

    chosen = max(candidates, key=rank)
    return chosen[1], "sample_ac" if rank(chosen)[0] else "latest_best_effort"
