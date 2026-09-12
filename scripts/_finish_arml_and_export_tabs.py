#!/usr/bin/env python3
"""When ARML OTC protocol-v3 finishes: score power rubrics, then emit paste tabs."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PYTHON = Path(r"e:\agent_olympiad\.venv\Scripts\python.exe")
OTC = REPO / "results" / "arml_all_protocol_v3_otc_20260909"
VAN = REPO / "results" / "arml_all_protocol_v3_vanilla_20260909"


def batch_done(root: Path) -> bool:
    log = root / "batch.log"
    if not log.is_file():
        return False
    text = log.read_text(encoding="utf-8", errors="replace")
    return "DONE 43/43" in text or "DONE 43/" in text


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=str(REPO), check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> int:
    poll = "--wait" in sys.argv
    if poll:
        while not batch_done(OTC):
            print(f"waiting for OTC DONE… ({time.strftime('%H:%M:%S')})", flush=True)
            time.sleep(120)
    elif not batch_done(OTC):
        print(f"OTC not finished yet: {OTC / 'batch.log'}", flush=True)
        return 2

    if not batch_done(VAN):
        print("Vanilla batch missing DONE marker; continuing anyway if sessions exist.", flush=True)

    # Post-hoc rubric scores for power rounds (idempotent for already-scored sessions).
    for root in (VAN, OTC):
        run(
            [
                str(PYTHON),
                "-u",
                "scripts/score_power_rubrics.py",
                str(root),
            ]
        )

    run([str(PYTHON), "-u", "scripts/_export_paste_tabs_3_6.py"])
    print("paste tabs ready under results/gold_suite_sheets_20260903/paste_tabs/", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
