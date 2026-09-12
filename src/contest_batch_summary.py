"""Export only final results verified for the current batch invocation."""
from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

from contest_run_identity import RunCompatibilityError, read_completed_contest_result


FIELDS = (
    "competition_id", "problem_id", "status", "batch_status", "reason",
    "run_fingerprint", "score", "max_score", "task_utility", "coordination_score",
    "turns_used", "api_calls_used", "wall_seconds", "started_at", "ended_at",
    "deadline_submission",
)


def _summary_row(out_root: Path, problem_id: str, job: dict[str, Any]) -> dict[str, Any]:
    row = dict.fromkeys(FIELDS, "")
    status = job.get("status", "pending")
    row.update(problem_id=problem_id, status=status, batch_status=status,
               reason=job.get("reason", ""))
    # Presence on disk is not evidence that this invocation verified the run.
    if status not in {"ok", "skipped_complete"}:
        return row
    identity = job.get("run_identity")
    if not isinstance(identity, dict) or not isinstance(identity.get("settings"), dict):
        row.update(status="unverified", reason="Completed job has no expected run identity")
        return row
    try:
        payload = read_completed_contest_result(out_root / problem_id, identity)
        sections = {}
        for name in ("grade", "metrics", "diagnostics", "budget", "timing"):
            section = payload.get(name, {})
            if not isinstance(section, dict):
                raise ValueError(f"Invalid {name} section")
            sections[name] = section
        grade, metrics = sections["grade"], sections["metrics"]
        diag, budget, timing = sections["diagnostics"], sections["budget"], sections["timing"]
        wall = timing.get("elapsed_seconds")
        if wall is None:
            wall = budget.get("wall_seconds_used", "")
        row.update(
            competition_id=payload["competition_id"],
            status="ok" if grade.get("graded") else "ungraded",
            run_fingerprint=identity["fingerprint"],
            score=grade.get("score", ""),
            max_score=grade.get("max_score", ""),
            task_utility=metrics.get("task_utility", ""),
            coordination_score=metrics.get("coordination_score", ""),
            turns_used=budget.get("turns_used", ""),
            api_calls_used=budget.get("api_calls_used", ""),
            wall_seconds=wall,
            started_at=timing.get("started_at") or budget.get("wall_started_at") or "",
            ended_at=timing.get("ended_at") or "",
            deadline_submission=diag.get("deadline_submission", ""),
        )
    except (RunCompatibilityError, OSError, ValueError, TypeError, KeyError) as exc:
        row.update(status="invalid", reason=str(exc))
    return row


def summarize(
    out_root: Path,
    problem_ids: list[str],
    *,
    run_results: Sequence[dict[str, Any]] = (),
) -> Path:
    """Unvisited jobs stay pending; failed/unverified jobs contribute no scores.

    Each successful job carries the expected identity resolved by run_one.
    Revalidate it at export time, including skips and ungraded completions.
    """
    jobs = {job["problem_id"]: job for job in run_results}
    rows = [_summary_row(out_root, problem_id, jobs.get(problem_id, {}))
            for problem_id in problem_ids]
    path = out_root / "summary.tsv"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=out_root,
            prefix=".summary-", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path
