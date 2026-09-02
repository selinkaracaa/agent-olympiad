#!/usr/bin/env python3
"""Supervise a Phase B matrix: prevent sleep, auto-resume, kill stalled cells.

Usage:
  python3 scripts/watch_phase_b.py --matrix results/phase_b/wave2_domains_enforced/phase_b_matrix.json -- \\
    --suite wave2 --rules-mode enforced \\
    --schemas single_agent,centralized,round_table,decentralized \\
    --output results/phase_b/wave2_domains_enforced

Loads .env from the repo root. On macOS, wraps the runner with ``caffeinate``.
If no new completed cell appears within ``--stall-minutes``, kills the runner
and restarts from the last saved checkpoint.
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
RUNNER = REPO / "src" / "run_phase_b_matrix.py"
ENV_FILE = REPO / ".env"
PID_FILE = REPO / "results" / "phase_b_live_run.pid"
WATCH_PID_FILE = REPO / "results" / "phase_b_watch.pid"
LOG = REPO / "results" / "phase_b_live_run.log"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _read_matrix(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _expected_cells(data: dict | None) -> int | None:
    if not data:
        return None
    cases = data.get("cases") or []
    teams = data.get("teams") or []
    schemas = data.get("schemas") or []
    if cases and teams and schemas:
        return len(cases) * len(teams) * len(schemas)
    return None


def _completed_ok(data: dict | None) -> int:
    if not data:
        return 0
    return sum(1 for row in data.get("results") or [] if row.get("status") == "ok")


def _matrix_mtime(path: Path) -> float:
    if not path.exists():
        return 0.0
    return path.stat().st_mtime


def _log_size() -> int:
    if not LOG.exists():
        return 0
    return LOG.stat().st_size


def _build_cmd(
    matrix_path: Path,
    runner_args: list[str],
    *,
    use_caffeinate: bool,
) -> list[str]:
    cmd = [sys.executable, "-u", str(RUNNER), "--live"]
    if matrix_path.exists():
        cmd.extend(["--resume", str(matrix_path)])
    cmd.extend(runner_args)
    if use_caffeinate and sys.platform == "darwin":
        return ["caffeinate", "-dims", *cmd]
    return cmd


def _terminate_tree(pid: int, *, reason: str) -> None:
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"===== WATCH KILL pid={pid} reason={reason} =====\n")
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except ProcessLookupError:
        return
    except PermissionError:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.5)
    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _run_once(
    matrix_path: Path,
    runner_args: list[str],
    *,
    use_caffeinate: bool,
    poll_seconds: float,
    stall_seconds: float,
) -> int:
    cmd = _build_cmd(matrix_path, runner_args, use_caffeinate=use_caffeinate)
    proc = subprocess.Popen(
        cmd,
        cwd=REPO,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        start_new_session=True,
    )
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")

    data = _read_matrix(matrix_path)
    last_done = _completed_ok(data)
    last_mtime = _matrix_mtime(matrix_path)
    last_log_size = _log_size()
    last_progress = time.monotonic()
    started = time.monotonic()

    while True:
        rc = proc.poll()
        if rc is not None:
            return int(rc)

        now = time.monotonic()
        data = _read_matrix(matrix_path)
        done = _completed_ok(data)
        mtime = _matrix_mtime(matrix_path)
        log_size = _log_size()

        if done > last_done or mtime > last_mtime + 0.5 or log_size > last_log_size + 200:
            last_done = done
            last_mtime = mtime
            last_log_size = log_size
            last_progress = now

        if now - last_progress >= stall_seconds:
            _terminate_tree(
                proc.pid,
                reason=f"no_progress_for_{int(stall_seconds)}s_cells={last_done}",
            )
            return 124

        if now - started >= stall_seconds * 3 and done == last_done:
            # First cell after resume can take a while; only hard-cap if truly frozen.
            pass

        time.sleep(poll_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix",
        type=Path,
        required=True,
        help="phase_b_matrix.json to resume and monitor",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=15.0,
        help="Seconds to wait before restarting after a crash",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=30.0,
        help="How often to check for progress",
    )
    parser.add_argument(
        "--stall-minutes",
        type=float,
        default=90.0,
        help="Kill runner if no new cell saved within this many minutes",
    )
    parser.add_argument(
        "--no-caffeinate",
        action="store_true",
        help="Do not wrap the runner with caffeinate (macOS)",
    )
    parser.add_argument(
        "runner_args",
        nargs=argparse.REMAINDER,
        help="Arguments for run_phase_b_matrix.py (prefix with --)",
    )
    args = parser.parse_args()
    runner_args = [a for a in args.runner_args if a != "--"]
    if not runner_args:
        parser.error("Pass runner args after -- (see script docstring)")

    _load_dotenv(ENV_FILE)
    if not os.environ.get("PERPLEXITY_API_KEY"):
        raise SystemExit("PERPLEXITY_API_KEY not set (use .env or export)")

    matrix_path = args.matrix if args.matrix.is_absolute() else REPO / args.matrix
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    WATCH_PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    stall_seconds = max(60.0, args.stall_minutes * 60.0)
    attempt = 0
    while True:
        data = _read_matrix(matrix_path)
        done = _completed_ok(data)
        expected = _expected_cells(data)
        if expected is not None and done >= expected:
            print(f"Complete: {done}/{expected} ok cells in {matrix_path}", flush=True)
            return

        attempt += 1
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        progress = f"{done}/{expected}" if expected is not None else str(done)
        with LOG.open("a", encoding="utf-8") as log:
            log.write(
                f"\n===== WATCH START attempt={attempt} {stamp} progress={progress} "
                f"stall_min={args.stall_minutes} =====\n"
            )

        print(
            f"[watch] attempt {attempt} | progress {progress} | "
            f"stall={args.stall_minutes}m",
            flush=True,
        )
        rc = _run_once(
            matrix_path,
            runner_args,
            use_caffeinate=not args.no_caffeinate,
            poll_seconds=args.poll_seconds,
            stall_seconds=stall_seconds,
        )

        data = _read_matrix(matrix_path)
        done = _completed_ok(data)
        expected = _expected_cells(data)
        if expected is not None and done >= expected:
            print(f"Complete: {done}/{expected} ok cells in {matrix_path}", flush=True)
            return

        reason = "stalled" if rc == 124 else f"rc={rc}"
        with LOG.open("a", encoding="utf-8") as log:
            log.write(f"===== WATCH RESTART {reason} progress={done}/{expected or '?'} =====\n")
        print(
            f"[watch] runner stopped ({reason}); {done}/{expected or '?'} ok — "
            f"retrying in {args.sleep:.0f}s",
            flush=True,
        )
        time.sleep(args.sleep)


if __name__ == "__main__":
    main()
