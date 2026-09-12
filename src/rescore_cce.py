#!/usr/bin/env python3
"""Post-hoc AgentWorld-style CCE scoring for saved contest transcripts.

This does not rerun agents. It reads complete action logs, constructs causal
action graphs with an LLM judge, and writes a checkpointed ``cce_results.json``
beside the input run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from env import OlympiadEnvironment  # noqa: E402
from env_config import load_repo_dotenv  # noqa: E402
from evaluation.cce import score_cce  # noqa: E402
from llm import resolve_request_fn  # noqa: E402


def _write_json(path: Path, value: dict[str, Any]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def _grade(transcript: dict[str, Any]) -> dict[str, Any]:
    run = transcript.get("run") or {}
    grade = run.get("grade")
    if isinstance(grade, dict):
        return grade
    final_result = run.get("final_result") or {}
    grade = final_result.get("grade")
    return grade if isinstance(grade, dict) else {}


def _task_utility(grade: dict[str, Any]) -> float:
    score, maximum = grade.get("score"), grade.get("max_score")
    if (
        isinstance(score, (int, float))
        and isinstance(maximum, (int, float))
        and maximum > 0
    ):
        return max(0.0, min(1.0, float(score) / float(maximum)))
    return 0.0


def _agents(transcript: dict[str, Any]) -> list[str]:
    metadata = transcript.get("metadata") or {}
    return [
        str(name)
        for name in metadata.get("agents") or []
        if str(name) not in {"Coach", "Contest_Control"}
    ]


def _task_text(competition: str, problem_id: str) -> str:
    try:
        env = OlympiadEnvironment(competition, problem_id)
        return str(env.problem_data.get("problem_description") or problem_id)
    except Exception:
        return problem_id


def _mean(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [
        float(row[field])
        for row in rows
        if isinstance(row.get(field), (int, float))
    ]
    return sum(values) / len(values) if values else None


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "transcripts": len(rows),
        "mean_cce": _mean(rows, "cce"),
        "mean_causal_efficiency": _mean(rows, "causal_efficiency"),
        "mean_utility_weighted_cce": _mean(rows, "utility_weighted_cce"),
        "total_contributing_actions": sum(
            int(row.get("contributing_count") or 0) for row in rows
        ),
        "total_actions": sum(int(row.get("total_actions") or 0) for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Run directory or one transcript JSON")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--provider", default="perplexity")
    parser.add_argument("--model", default="openai/gpt-5.4-mini")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--trace-partial-credit",
        action="store_true",
        help="Also build graphs for incomplete partial-credit tasks (not strict AgentWorld CCE)",
    )
    args = parser.parse_args()

    load_repo_dotenv(REPO_ROOT / ".env")
    request_fn = resolve_request_fn(
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
    )
    source = args.input.resolve()
    paths = (
        [source]
        if source.is_file()
        else sorted(source.glob("**/transcripts/*__*.json"))
    )
    if args.limit:
        paths = paths[: args.limit]
    output = args.output or (
        source.with_name(source.stem + "_cce.json")
        if source.is_file()
        else source / "cce_results.json"
    )

    existing: dict[str, Any] = {}
    if output.exists() and not args.force:
        existing = json.loads(output.read_text(encoding="utf-8"))
    rows_by_path = {
        str(row.get("transcript_path")): row
        for row in existing.get("results") or []
        if row.get("transcript_path")
    }

    print(f"CCE scoring: {len(paths)} transcripts -> {output}", flush=True)
    for index, path in enumerate(paths, start=1):
        key = str(path)
        if key in rows_by_path and not args.force:
            print(f"[{index}/{len(paths)}] skip {path.name}", flush=True)
            continue
        transcript = json.loads(path.read_text(encoding="utf-8"))
        metadata = transcript.get("metadata") or {}
        competition = str(metadata.get("competition_id") or "")
        problem_id = str(metadata.get("problem_id") or path.stem.split("__", 1)[0])
        grade = _grade(transcript)
        utility = _task_utility(grade)
        print(
            f"[{index}/{len(paths)}] {competition}/{problem_id} "
            f"utility={utility:.3f}",
            flush=True,
        )
        result = score_cce(
            request_fn=request_fn,
            task_text=_task_text(competition, problem_id),
            action_log=list(transcript.get("action_log") or []),
            task_utility=utility,
            task_outcome=json.dumps(grade, ensure_ascii=False, default=str),
            agents=_agents(transcript),
            trace_partial_credit=args.trace_partial_credit,
        ).to_dict()
        rows_by_path[key] = {
            "competition": competition,
            "problem_id": problem_id,
            "transcript_path": key,
            **result,
        }
        rows = list(rows_by_path.values())
        _write_json(
            output,
            {
                "source": "AgentWorld_COLM_2026_CCE",
                "provider": args.provider,
                "model": args.model,
                "temperature": args.temperature,
                "input": str(source),
                "summary": _summary(rows),
                "results": rows,
            },
        )
        print(
            f"  CCE={result['cce']:.3f} "
            f"raw={result['causal_efficiency']:.3f} "
            f"weighted={result['utility_weighted_cce']:.3f} "
            f"C={result['contributing_count']}/{result['total_actions']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
