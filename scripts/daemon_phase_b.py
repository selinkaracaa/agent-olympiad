#!/usr/bin/env python3
"""Fully detach Phase B matrix from the parent terminal (macOS-safe daemon)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / "results" / "phase_b_live_run.log"
PID_FILE = REPO / "results" / "phase_b_live_run.pid"
ENV_FILE = REPO / ".env"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def daemonize() -> None:
    if os.fork() > 0:
        sys.exit(0)
    os.setsid()
    if os.fork() > 0:
        sys.exit(0)
    os.chdir(REPO)
    os.umask(0)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as log:
        log.write(f"\n===== DAEMON START {os.getpid()} =====\n")
        log.flush()
    devnull = open(os.devnull, "r")
    log_f = open(LOG, "a", encoding="utf-8", buffering=1)
    os.dup2(devnull.fileno(), sys.stdin.fileno())
    os.dup2(log_f.fileno(), sys.stdout.fileno())
    os.dup2(log_f.fileno(), sys.stderr.fileno())


def main() -> None:
    _load_dotenv(ENV_FILE)
    if not os.environ.get("PERPLEXITY_API_KEY"):
        print("PERPLEXITY_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Extra CLI args after script name, e.g.:
    #   python3 scripts/daemon_phase_b.py --competitions arml_local --output ...
    extra = sys.argv[1:]
    daemonize()
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    os.environ["PYTHONUNBUFFERED"] = "1"
    cmd = [
        sys.executable,
        "-u",
        str(REPO / "src" / "run_phase_b_matrix.py"),
        "--live",
        *extra,
    ]
    os.execv(sys.executable, cmd)


if __name__ == "__main__":
    main()
