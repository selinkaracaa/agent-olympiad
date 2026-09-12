"""Run fresh full-contest OTC/Vanilla pairs for every remaining ICPC WF year.

The batch is resumable: a run is skipped only when its contest_session.json
exists and matches the resolved experiment fingerprint. Generated manifests,
per-run logs, and batch_status.json live under the selected output root.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from run_competition_batch import inspect_contest_run
from contest_run_identity import RunCompatibilityError, inspect_contest_output
from contest_budget import resolve_contest_budget

BENCHMARK = REPO / "data" / "benchmarks" / "icpc" / "benchmark.json"
RUNNER = REPO / "src" / "run_competition_batch.py"
PYTHON = REPO.parent / ".venv" / "Scripts" / "python.exe"
GATEWAY_HEALTH = "http://127.0.0.1:8787/v1/health"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def gateway_ready() -> bool:
    try:
        with urllib.request.urlopen(GATEWAY_HEALTH, timeout=5) as response:
            payload = json.load(response)
        return response.status == 200 and payload.get("ok") is True
    except Exception:
        return False


def completed(run_dir: Path, expected_identity: dict) -> bool:
    return inspect_contest_output(run_dir, expected_identity) == "complete"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO / "results" / "icpc_all_full_pairs_v5",
    )
    parser.add_argument("--start-year", type=int, default=2012)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--skip-year",
        type=int,
        action="append",
        default=[],
        help="Year already covered by a separately verified pair.",
    )
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    manifest_dir = output_root / "manifests"
    log_dir = output_root / "logs"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "batch_status.json"

    tasks = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    by_year: dict[int, list[str]] = {}
    for task in tasks:
        year = int(task["year"])
        evaluation = task.get("evaluation") or {}
        if not (
            args.start_year <= year <= args.end_year
            and evaluation.get("status") == "remote_judge_ready"
            and evaluation.get("vjudge_prob_num")
        ):
            continue
        by_year.setdefault(year, []).append(task["problem_id"])

    jobs = []
    for year in sorted(by_year):
        if year in set(args.skip_year):
            continue
        session_id = f"icpc_wf_{year}"
        manifest_path = manifest_dir / f"{session_id}.json"
        write_json(
            manifest_path,
            {
                "session_id": session_id,
                "competition_id": "icpc",
                "problem_ids": by_year[year],
                "split_parts": False,
                "description": (
                    f"Full ICPC World Finals {year} contest: "
                    f"{len(by_year[year])} problems under one shared turn budget."
                ),
            },
        )
        for variant in ("otc", "decentralized"):
            short = "otc" if variant == "otc" else "vanilla"
            run_dir = output_root / "runs" / f"{session_id}_{short}"
            jobs.append((year, session_id, manifest_path, variant, run_dir))

    state = {
        "created_at": now(),
        "updated_at": now(),
        "status": "running",
        "configuration": {
            "provider": "perplexity",
            "model": "openai/gpt-5.4-mini",
            "team_size": 3,
            "max_turns": "registry (300 min / 5 min per turn = 60)",
            "max_simulated_minutes": 300,
            "programming_deadline_submit": True,
            "skipped_verified_years": sorted(set(args.skip_year)),
        },
        "total_jobs": len(jobs),
        "jobs": [],
    }
    if status_path.exists():
        try:
            previous = json.loads(status_path.read_text(encoding="utf-8"))
            state["created_at"] = previous.get("created_at", state["created_at"])
            state["jobs"] = previous.get("jobs", [])
        except Exception:
            pass
    job_state = {
        (entry.get("year"), entry.get("variant")): entry for entry in state["jobs"]
    }

    for year, session_id, manifest_path, variant, run_dir in jobs:
        key = (year, variant)
        entry = job_state.get(key, {"year": year, "variant": variant})
        log_path = log_dir / f"{session_id}_{variant}.log"
        runner_path = RUNNER
        command = [
            str(PYTHON),
            "-u",
            str(runner_path),
            "--live",
            "--provider",
            "perplexity",
            "--model",
            "openai/gpt-5.4-mini",
            "--contest-manifest",
            str(manifest_path),
            "--system-variant",
            variant,
            "--action-calling",
            "native",
            "--team-size",
            "3",
            # No --max-turns: registry derives 5h / 5 min = 60 turns.
            "--max-api-calls",
            str(resolve_contest_budget("icpc").max_turns * 3 * 2 + 2),
            "--start-seat",
            "0",
            "--max-simulated-minutes",
            "300",
            "--programming-deadline-submit",
            "--no-judge-collab",
            "--no-judge-task",
            "--no-judge-cce",
            "--output",
            str(run_dir),
        ]
        try:
            output_state, expected_identity = inspect_contest_run(command[3:])
        except (ValueError, SystemExit) as exc:
            entry.update(status="blocked", reason=str(exc), updated_at=now())
            job_state[key] = entry
            state.update(status="blocked", updated_at=now(), jobs=list(job_state.values()))
            write_json(status_path, state)
            return 2
        if output_state == "complete":
            entry.update(status="completed", skipped_on_resume=True, updated_at=now())
            job_state[key] = entry
            continue
        if not gateway_ready():
            entry.update(status="blocked", reason="gateway health check failed", updated_at=now())
            job_state[key] = entry
            state.update(status="blocked", updated_at=now(), jobs=list(job_state.values()))
            write_json(status_path, state)
            return 2
        run_dir.mkdir(parents=True, exist_ok=True)
        # Preserve a partially completed contest after a transient provider
        # failure. The contest runner validates checkpoint compatibility.
        if output_state == "resume":
            command.append("--resume")
        entry.update(
            status="running",
            started_at=now(),
            output=str(run_dir),
            log=str(log_path),
        )
        job_state[key] = entry
        state.update(updated_at=now(), jobs=list(job_state.values()))
        write_json(status_path, state)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n[{now()}] START {' '.join(command)}\n")
            log.flush()
            result = subprocess.run(command, cwd=REPO, stdout=log, stderr=subprocess.STDOUT)
            log.write(f"[{now()}] EXIT {result.returncode}\n")
        exit_code = result.returncode
        if exit_code == 0:
            try:
                if not completed(run_dir, expected_identity):
                    exit_code = 1
                    entry["reason"] = "Process exited without a verified complete result"
            except RunCompatibilityError as exc:
                exit_code = 1
                entry["reason"] = str(exc)
        entry.update(
            status="completed" if exit_code == 0 else "failed",
            exit_code=exit_code,
            finished_at=now(),
            updated_at=now(),
        )
        state.update(updated_at=now(), jobs=list(job_state.values()))
        write_json(status_path, state)
        if exit_code != 0:
            state["status"] = "failed"
            write_json(status_path, state)
            return exit_code
        time.sleep(15)

    state.update(status="completed", updated_at=now(), jobs=list(job_state.values()))
    write_json(status_path, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
