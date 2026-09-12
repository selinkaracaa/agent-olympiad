"""Run scoped ARML Local / ICPC WF 2012 checks through the official CLI."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from contest_run_identity import read_completed_contest_result
from run_competition_batch import inspect_contest_run


def write_json(path, payload):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def gateway_ready():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8787/v1/health", timeout=3) as response:
            return json.load(response).get("ok") is True
    except (OSError, ValueError):
        return False


def commands(output, paired):
    jobs = []
    for contest, manifest, size, turns, calls, minutes in (
        ("arml_local_2012", "data/contest_manifests/generated/arml_local_2012.json", 6, 9, 109, 45),
        ("icpc_wf_2012", "data/contest_manifests/icpc_wf_2012.json", 3, 60, 361, 300),
    ):
        for variant in (("otc", "decentralized") if paired else ("otc",)):
            dest = output / f"{contest}_{variant}"
            command = [
                sys.executable, "-B", "-u", str(ROOT / "src/run_competition_batch.py"),
                "--live", "--provider", "perplexity", "--model", "openai/gpt-5.4-mini",
                "--contest-manifest", str(ROOT / manifest), "--system-variant", variant,
                "--action-calling", "native", "--team-size", str(size),
                "--max-turns", str(turns), "--max-api-calls", str(calls),
                "--max-total-tokens", "220000", "--max-simulated-minutes", str(minutes),
                "--start-seat", "0", "--no-judge-task", "--no-judge-cce",
                "--output", str(dest),
            ]
            if contest.startswith("icpc"):
                command.append("--programming-deadline-submit")
            state, identity = inspect_contest_run(command[4:])
            if state != "new":
                raise RuntimeError(f"Fresh validation output required: {dest} ({state})")
            jobs.append(dict(contest=contest, variant=variant, output=str(dest),
                             command=command, identity=identity))
    return jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--paired", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--gateway-worker", action="store_true")
    args = parser.parse_args()
    if args.gateway_worker:
        import vjudge_gateway
        client = vjudge_gateway._remote_client("kattis")
        client.min_submit_interval = 20.0
        client._login()
        return vjudge_gateway.main(["serve", "--host", "127.0.0.1", "--port", "8787"])
    if args.output is None:
        parser.error("--output is required")
    output = args.output.resolve()
    jobs = commands(output, args.paired)
    for job in jobs:
        settings = job["identity"]["settings"]
        config = settings["config"]
        print(json.dumps(dict(
            contest=job["contest"], variant=job["variant"], tasks=len(settings["task_ids"]),
            team_size=config["team_size"], max_turns=config["max_turns"],
            max_api_calls=config["max_api_calls"], max_tokens=config["max_tokens"],
            fingerprint=job["identity"]["fingerprint"], output=job["output"],
        )), flush=True)
    if args.prepare_only:
        return 0
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"Refusing to overwrite nonempty validation directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "src").rglob("*.py"):
        dest = output / "source_snapshot" / source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    shutil.copy2(__file__, output / Path(__file__).name)
    write_json(output / "run_plan.json", {
        "started_at": datetime.now(timezone.utc).isoformat(), "jobs": jobs,
        "arml_scope": "9 automatically gradeable questions; question 6 excluded by existing manifest",
        "icpc_scope": "12 problems, full World Finals 2012",
        "gateway_min_submit_interval_seconds": 20,
    })
    gateway = None
    gateway_log = None
    try:
        if not gateway_ready():
            gateway_log = (output / "gateway.log").open("a", encoding="utf-8")
            gateway = subprocess.Popen(
                [sys.executable, "-B", "-u", str(Path(__file__).resolve()), "--gateway-worker"],
                cwd=ROOT, stdout=gateway_log, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            for _ in range(30):
                if gateway_ready():
                    break
                if gateway.poll() is not None:
                    raise RuntimeError("Gateway startup failed; see gateway.log")
                time.sleep(0.5)
            else:
                raise RuntimeError("Gateway did not become healthy")
        env = dict(os.environ, VJUDGE_GATEWAY_URL="http://127.0.0.1:8787")

        def run_contest_jobs(contest):
            results = []
            # Only one ICPC variant may use the gateway at a time.
            for job in [item for item in jobs if item["contest"] == contest]:
                dest = Path(job["output"])
                dest.mkdir(exist_ok=True)
                write_json(dest / "command.json", job["command"])
                print(f"START {dest.name}", flush=True)
                with (dest / "run.log").open("a", encoding="utf-8") as log:
                    process = subprocess.run(job["command"], cwd=ROOT, env=env,
                                             stdout=log, stderr=subprocess.STDOUT)
                row = {"contest": contest, "variant": job["variant"],
                       "exit_code": process.returncode, "output": str(dest)}
                try:
                    if process.returncode:
                        raise RuntimeError(f"CLI exited {process.returncode}; see run.log")
                    result = read_completed_contest_result(dest, job["identity"])
                    row.update(status="complete", grade=result["grade"], budget=result["budget"],
                               diagnostics=result["diagnostics"], metrics=result["metrics"])
                except (ValueError, RuntimeError, OSError) as exc:
                    row.update(status="failed", error=str(exc))
                results.append(row)
                write_json(output / f"{contest}_status.json", results)
                print(f"END {dest.name}: {row['status']}", flush=True)
                if row["status"] != "complete":
                    break
            return results

        with ThreadPoolExecutor(max_workers=2) as pool:
            groups = list(pool.map(run_contest_jobs, ("arml_local_2012", "icpc_wf_2012")))
        results = [row for group in groups for row in group]
        write_json(output / "validation_summary.json", results)
        return 0 if len(results) == len(jobs) and all(row["status"] == "complete" for row in results) else 1
    finally:
        if gateway is not None:
            gateway.terminate()
            gateway.wait(timeout=10)
        if gateway_log is not None:
            gateway_log.close()


if __name__ == "__main__":
    raise SystemExit(main())
