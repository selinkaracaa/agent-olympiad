"""Add post-hoc collaboration scores and export complete ICPC metrics."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from contest_manifest import load_contest_manifest  # noqa: E402
from env_config import load_repo_dotenv  # noqa: E402
from evaluation.collaboration_score import score_coordination  # noqa: E402
from llm import resolve_request_fn  # noqa: E402


def atomic_json(path: Path, payload: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=REPO / "results" / "icpc_all_full_pairs_20260909" / "runs",
    )
    parser.add_argument("--model", default="openai/gpt-5.4-mini")
    args = parser.parse_args()
    load_repo_dotenv(REPO / ".env")
    request_fn = resolve_request_fn(
        provider="perplexity",
        model=args.model,
        max_output_tokens=4096,
        temperature=0.0,
    )

    rows: list[dict[str, object]] = []
    for run_dir in sorted(args.runs_root.resolve().iterdir()):
        session_path = run_dir / "contest_session.json"
        checkpoint_path = run_dir / "contest_checkpoint.json"
        if not session_path.is_file() or not checkpoint_path.is_file():
            continue
        payload = json.loads(session_path.read_text(encoding="utf-8"))
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        manifest_path = Path(payload["run"]["manifest"])
        manifest = load_contest_manifest(
            manifest_path, benchmark_root=REPO / "data" / "benchmarks"
        )
        events = json.loads(checkpoint["memory"])["events"]
        agents = ["Agent_1", "Agent_2", "Agent_3"]
        chat_history = [
            {
                "sender": event["actor"],
                "content": str(
                    event.get("payload", {}).get("content")
                    or event.get("payload", {}).get("report")
                    or event.get("payload", {})
                ),
            }
            for event in events
            if event.get("actor") in agents
            and event.get("kind")
            in {"speak", "direct_message", "request_review", "review_answer"}
        ]
        action_log = [
            {
                "agent": event["actor"],
                "action": event["kind"],
                "payload": event.get("payload", {}),
            }
            for event in events
            if event.get("actor") in agents
        ]
        grade = payload.get("grade") or {}
        task_text = "\n\n".join(
            f"{task.task_id}\n{task.prompt}" for task in manifest.tasks
        )
        task_results = (
            f"submitted={any((payload.get('submissions') or {}).values())} "
            f"grade_method={grade.get('method')} "
            f"score={grade.get('score')}/{grade.get('max_score')}"
        )
        score_path = run_dir / "posthoc_collaboration.json"
        if score_path.is_file():
            coordination = json.loads(score_path.read_text(encoding="utf-8"))
        else:
            coordination = score_coordination(
                request_fn=request_fn,
                task_text=task_text,
                agents=agents,
                schema=f"{payload['run']['system_variant']}",
                chat_history=chat_history,
                action_log=action_log,
                task_results=task_results,
            ).to_dict()
            coordination["grading_temperature"] = 0.0
            coordination["source_session"] = str(session_path)
            atomic_json(score_path, coordination)

        tasks = list(checkpoint["session"]["tasks"])
        score = sum(bool(task.get("locked")) for task in tasks)
        valid_results = [
            submission
            for task in tasks
            for submission in task.get("submissions", [])
            if submission.get("valid")
        ]
        remote_attempts = sum(
            event.get("kind")
            in {"submit_code_result", "programming_deadline_submit_result"}
            and event.get("payload", {}).get("feedback", {}).get("test_scope")
            == "remote"
            for event in events
        )
        metrics = payload["metrics"]
        budget = payload["budget"]
        diagnostics = payload.get("diagnostics") or {}
        rows.append(
            {
                "model": args.model,
                "variant": payload["run"]["system_variant"],
                "contest": payload["session_id"].replace("icpc_wf_", "WF "),
                "Acc": round(score / len(tasks), 4),
                "score": score,
                "max_score": len(tasks),
                "CS": coordination["coordination_score"],
                "Comm": coordination["communication_score"],
                "Plan": coordination["planning_score"],
                "AAR": round(float(metrics["active_agent_rate"]), 4),
                "AB": round(float(metrics["action_balance"]), 4),
                "turns": budget["turns_used"],
                "api_calls": budget["api_calls_used"],
                "tokens": budget["tokens_used"],
                "penalty_min": budget["penalty_minutes"],
                "sec": round(float(metrics["elapsed_seconds"]), 3),
                "remote_attempts": remote_attempts,
                "valid_remote_results": len(valid_results),
                # contest_session_v4 desk-action counters; blank for older runs.
                "protocol": payload.get("protocol_version") or "",
                "inspect": diagnostics.get("inspect_count", ""),
                "notes": diagnostics.get("notes_recorded", ""),
                "notes_shared": diagnostics.get("notes_shared", ""),
                "recalls": diagnostics.get("recall_count", ""),
                "triage": diagnostics.get("triage_changes", ""),
                "hopeless": diagnostics.get("items_hopeless", ""),
                "repeat_drafts": diagnostics.get("repeat_draft_attempts", ""),
                "artifact": str(run_dir.relative_to(REPO)).replace("\\", "/"),
            }
        )

    output = args.runs_root.resolve().parent / "completed_metrics.tsv"
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(output)
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
