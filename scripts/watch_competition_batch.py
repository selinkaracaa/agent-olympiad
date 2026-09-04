#!/usr/bin/env python3
"""Supervise a single-config competition_batch run: caffeinate, resume, stall-kill.

Usage:
  python3 scripts/watch_competition_batch.py --output results/non_math_gpt54mini \\
    -- --live --benchmark-suite non_math --schema centralized \\
    --rules-mode enforced --model openai/gpt-5.4-mini --max-turns 30 --resume
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "src" / "run_competition_batch.py"
ENV_FILE = REPO / ".env"
BATCH_JSON = "competition_batch.json"
LOG = REPO / "results" / "non_math_batch_watch.log"
PID_FILE = REPO / "results" / "non_math_batch_watch.pid"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _completed_ok(batch_path: Path) -> int:
    if not batch_path.exists():
        return 0
    try:
        data = json.loads(batch_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    return sum(1 for row in data.get("results") or [] if row.get("status") == "ok")


def _expected_cases(batch_path: Path) -> int | None:
    if not batch_path.exists():
        return None
    try:
        data = json.loads(batch_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    selected = data.get("selected_cases") or []
    return len(selected) if selected else data.get("total")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Batch output directory")
    parser.add_argument("--stall-minutes", type=int, default=120)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("runner_args", nargs=argparse.REMAINDER, help="Args after --")
    args = parser.parse_args()
    runner_args = args.runner_args
    if runner_args and runner_args[0] == "--":
        runner_args = runner_args[1:]
    if not runner_args:
        parser.error("Provide runner args after --")

    _load_dotenv(ENV_FILE)
    args.output.mkdir(parents=True, exist_ok=True)
    batch_path = args.output / BATCH_JSON
    LOG.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    cmd_base = [sys.executable, "-u", str(RUNNER), *runner_args, "--output", str(args.output)]
    if "--resume" not in runner_args:
        cmd_base.append("--resume")

    stall_seconds = max(60, args.stall_minutes * 60)
    last_ok = _completed_ok(batch_path)
    last_progress = time.monotonic()
    proc: subprocess.Popen | None = None

    def start() -> subprocess.Popen:
        wrapped = ["caffeinate", "-dimsu", *cmd_base] if sys.platform == "darwin" else cmd_base
        with LOG.open("a", encoding="utf-8") as log_handle:
            log_handle.write(
                f"\n[{datetime.now(timezone.utc).isoformat()}] starting: {' '.join(wrapped)}\n"
            )
            log_handle.flush()
            return subprocess.Popen(
                wrapped,
                cwd=REPO,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )

    try:
        proc = start()
        while True:
            time.sleep(args.poll_seconds)
            ok = _completed_ok(batch_path)
            expected = _expected_cases(batch_path)
            if ok > last_ok:
                last_ok = ok
                last_progress = time.monotonic()
                print(f"[watch] progress {ok}/{expected or '?'}", flush=True)
            if proc.poll() is not None:
                # Re-read progress after process exits to get final state.
                ok = _completed_ok(batch_path)
                expected = _expected_cases(batch_path)
                if expected and ok >= expected:
                    print(f"[watch] complete {ok}/{expected}", flush=True)
                    break
                print(f"[watch] runner exited ({proc.returncode}); restarting", flush=True)
                proc = start()
                last_progress = time.monotonic()
                continue
            if time.monotonic() - last_progress >= stall_seconds:
                print(f"[watch] stall kill after {args.stall_minutes}m at {ok}/{expected or '?'}", flush=True)
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill()
                proc = start()
                last_progress = time.monotonic()
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
        PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
