#!/usr/bin/env python3
"""Score completed power-round sessions against their per-contest rubrics.

Power rounds are graded by ``reference_llm``, so ``grade_contest_result`` marks
every task ``status="unavailable"`` and the session finishes with no
``task_utility``. The contest-session path in ``run_competition_batch`` never
calls ``apply_registered_judge``, so nothing consumes ``evaluation.rubric_path``
during a batch.

This pass closes that gap after the fact: it reads finished
``contest_session.json`` files, runs the registered rubric judge on each
unavailable task, and folds the result back into the session's grade. Running it
over both arms with the same rubrics keeps OTC and Vanilla comparable, which an
in-batch judge would not have done for batches that were already part-way
through when the rubrics landed.

    python scripts/score_power_rubrics.py results/<otc_batch> results/<vanilla_batch>

Use ``--limit 1`` for a costed smoke test before scoring a whole batch.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_manifest import load_contest_manifest  # noqa: E402
from env_config import load_repo_dotenv  # noqa: E402
from evaluation.finalize import apply_registered_judge  # noqa: E402
from evaluation.models import EvaluationError  # noqa: E402
from llm import resolve_request_fn  # noqa: E402

MANIFEST_ROOT = REPO_ROOT / "data" / "contest_manifests" / "generated"
BENCH_ROOT = REPO_ROOT / "data" / "benchmarks"
# Grade rows that grade_contest_result could not score deterministically.
UNAVAILABLE = "unavailable"

FIELDS = [
    "problem_id",
    "status",
    "score",
    "max_score",
    "task_utility",
    "criteria_scored",
    "criteria_nonzero",
    "submission_chars",
    "rubric_id",
    "attempts",
    "reason",
]
# These rubrics run to 30 criteria, and the judge sometimes slips on the output
# contract (mis-summed total, duplicate ids, missing evidence) rather than on
# the scoring itself. Validation rejects those, so re-roll at rising
# temperature; a retry at 0.0 would just reproduce the same response.
RETRY_TEMPERATURES = (0.3, 0.6)


def _needs_rubric(row: dict, *, force: bool) -> bool:
    if row.get("status") != UNAVAILABLE:
        return False
    return force or not row.get("method")


def _aggregate(rows: dict[str, dict]) -> dict[str, Any]:
    scored = [row for row in rows.values() if row.get("graded")]
    utilities = [float(row["utility"]) for row in scored if row.get("utility") is not None]
    return {
        "graded": bool(rows) and len(scored) == len(rows),
        "evaluation_coverage": len(scored) / len(rows) if rows else 0.0,
        "graded_tasks": len(scored),
        "ungraded_tasks": len(rows) - len(scored),
        "method": "contest_session_rubric_v1",
        "score": sum(float(row["score"]) for row in scored) if scored else None,
        "max_score": sum(float(row["max_score"]) for row in scored) if scored else None,
        "task_utility": sum(utilities) / len(utilities) if utilities else None,
        "tasks": rows,
    }


def _stored_row(base: dict, row: dict, task, submission: str) -> dict[str, Any]:
    """Summarise a task this pass did not need to judge."""
    if row.get("status") != "rubric_scored":
        return {**base, "problem_id": task.task_id, "status": "no_rubric_needed"}
    criteria = (row.get("evaluation") or {}).get("criteria") or []
    rubric_path = ((task.benchmark.get("evaluation") or {}).get("rubric_path")) or ""
    return {
        **base,
        "problem_id": task.task_id,
        "status": "already_scored",
        "submission_chars": len(submission),
        "score": row.get("score"),
        "max_score": row.get("max_score"),
        "task_utility": row.get("utility"),
        "criteria_scored": len(criteria),
        "criteria_nonzero": sum(1 for item in criteria if float(item.get("score") or 0) > 0),
        "rubric_id": Path(rubric_path).stem,
    }


def _judge_with_retries(problem: dict, submission: str, *, request_fns, work_dir: Path):
    """Run the rubric judge, re-rolling when it breaks the output contract."""
    last_error: EvaluationError | None = None
    for attempt, request_fn in enumerate(request_fns, start=1):
        try:
            judged = apply_registered_judge(
                problem,
                submission,
                {"graded": False, "method": "llm_judge_required"},
                request_fn=request_fn,
                work_dir=work_dir,
                repo_root=REPO_ROOT,
            )
        except EvaluationError as exc:
            last_error = exc
            continue
        return judged, attempt, None
    return None, len(request_fns), last_error


def score_session(
    session_path: Path,
    *,
    request_fns,
    force: bool,
    dry_run: bool,
) -> list[dict[str, Any]]:
    problem_id = session_path.parent.name
    manifest_path = MANIFEST_ROOT / f"{problem_id}.json"
    base = {field: "" for field in FIELDS}
    base["problem_id"] = problem_id

    if not manifest_path.is_file():
        return [{**base, "status": "missing_manifest"}]

    payload = json.loads(session_path.read_text(encoding="utf-8"))
    manifest = load_contest_manifest(manifest_path, benchmark_root=BENCH_ROOT)
    grade = dict(payload.get("grade") or {})
    task_rows = dict(grade.get("tasks") or {})
    submissions = payload.get("submissions") or {}

    pending = [task for task in manifest.tasks if _needs_rubric(task_rows.get(task.task_id) or {}, force=force)]
    if not pending:
        # Report stored scores so the summary stays a full picture of the batch
        # even when this pass only had a few sessions left to judge.
        return [
            _stored_row(
                base,
                task_rows.get(task.task_id) or {},
                task,
                str(submissions.get(task.task_id) or ""),
            )
            for task in manifest.tasks
        ]

    out_rows: list[dict[str, Any]] = []
    changed = False
    for task in pending:
        problem = dict(task.benchmark)
        submission = str(submissions.get(task.task_id) or "")
        rubric_path = (problem.get("evaluation") or {}).get("rubric_path") or ""
        row = {
            **base,
            "problem_id": task.task_id,
            "submission_chars": len(submission),
            "rubric_id": Path(rubric_path).stem,
        }
        if not submission.strip():
            out_rows.append({**row, "status": "empty_submission"})
            continue
        if dry_run:
            out_rows.append({**row, "status": "would_score"})
            continue

        judged, attempts, error = _judge_with_retries(
            problem,
            submission,
            request_fns=request_fns,
            work_dir=session_path.parent / "rubric_judge",
        )
        row["attempts"] = attempts
        if judged is None:
            out_rows.append(
                {**row, "status": "invalid_judge_output", "reason": str(error)[:160]}
            )
            continue
        if not judged.get("graded"):
            out_rows.append(
                {**row, "status": "not_graded", "reason": str(judged.get("reason") or judged.get("method") or "")}
            )
            continue

        score = float(judged["score"])
        maximum = float(judged["max_score"])
        evaluation = judged.get("evaluation") or {}
        criteria = evaluation.get("criteria") or []
        task_rows[task.task_id] = {
            "graded": True,
            "status": "rubric_scored",
            "score": score,
            "max_score": maximum,
            "utility": score / maximum if maximum > 0 else 0.0,
            "method": judged.get("method"),
            "evaluation": evaluation,
        }
        changed = True
        out_rows.append(
            {
                **row,
                "status": "ok",
                "score": score,
                "max_score": maximum,
                "task_utility": score / maximum if maximum > 0 else 0.0,
                "criteria_scored": len(criteria),
                "criteria_nonzero": sum(1 for item in criteria if float(item.get("score") or 0) > 0),
            }
        )

    if changed:
        payload.setdefault("grade_pre_rubric", grade)
        updated = _aggregate(task_rows)
        payload["grade"] = updated
        metrics = dict(payload.get("metrics") or {})
        metrics["task_utility"] = updated["task_utility"]
        payload["metrics"] = metrics
        session_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return out_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path, help="Batch output directories.")
    parser.add_argument("--competition-prefix", default="arml_", help="Only score sessions whose id starts with this.")
    parser.add_argument("--provider", default="perplexity")
    parser.add_argument("--model", default="openai/gpt-5.4-mini")
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=None, help="Score at most N sessions per root.")
    parser.add_argument(
        "--retries",
        type=int,
        default=len(RETRY_TEMPERATURES),
        choices=range(len(RETRY_TEMPERATURES) + 1),
        help="Re-rolls at rising temperature when the judge breaks the output contract.",
    )
    parser.add_argument("--force", action="store_true", help="Re-judge tasks that already carry a rubric score.")
    parser.add_argument("--dry-run", action="store_true", help="List what would be scored without calling the judge.")
    args = parser.parse_args()

    request_fns: list = []
    if not args.dry_run:
        load_repo_dotenv()
        temperatures = [args.temperature, *RETRY_TEMPERATURES[: args.retries]]
        request_fns = [
            resolve_request_fn(
                provider=args.provider,
                model=args.model,
                max_output_tokens=args.max_output_tokens,
                temperature=temperature,
            )
            for temperature in temperatures
        ]

    exit_code = 0
    for root in args.roots:
        sessions = sorted(
            path
            for path in root.glob("*/contest_session.json")
            if path.parent.name.startswith(args.competition_prefix)
        )
        if args.limit is not None:
            sessions = sessions[: args.limit]

        rows: list[dict[str, Any]] = []
        for session_path in sessions:
            try:
                rows.extend(
                    score_session(
                        session_path,
                        request_fns=request_fns,
                        force=args.force,
                        dry_run=args.dry_run,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                exit_code = 1
                rows.append(
                    {
                        **{field: "" for field in FIELDS},
                        "problem_id": session_path.parent.name,
                        "status": f"error:{type(exc).__name__}",
                        "reason": str(exc)[:160],
                    }
                )
            print(f"  {rows[-1]['problem_id']}: {rows[-1]['status']} {rows[-1].get('score', '')}", flush=True)

        if rows and not args.dry_run:
            summary = root / "rubric_scores.tsv"
            with summary.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)

        scored = [row for row in rows if row["status"] in {"ok", "already_scored"}]
        power = [row for row in rows if row["status"] != "no_rubric_needed"]
        mean = (
            sum(float(row["task_utility"]) for row in scored) / len(scored) if scored else 0.0
        )
        print(
            f"{root}: {len(scored)}/{len(power)} power sessions scored "
            f"| mean utility {mean:.1%}",
            flush=True,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
