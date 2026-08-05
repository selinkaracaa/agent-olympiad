"""Recreate the sparse Cybench runtime checkout used by Agent Olympiad."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
UPSTREAM = HERE / "upstream"
BENCHMARK = REPO_ROOT / "data" / "benchmarks" / "cybench" / "benchmark.json"
REMOTE = "https://github.com/andyzorigin/cybench.git"


def run(*args: str, input_text: str | None = None) -> None:
    subprocess.run(
        list(args),
        input=input_text,
        text=True,
        check=True,
    )


def main() -> None:
    if not UPSTREAM.exists():
        run(
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            "--no-checkout",
            REMOTE,
            str(UPSTREAM),
        )

    with BENCHMARK.open(encoding="utf-8") as handle:
        records = json.load(handle)
    task_paths = sorted(
        {
            str(record["source_file"]).removeprefix("benchmark/Cybench/")
            for record in records
        }
    )

    run("git", "-C", str(UPSTREAM), "sparse-checkout", "init", "--cone")
    run(
        "git",
        "-C",
        str(UPSTREAM),
        "sparse-checkout",
        "set",
        "--stdin",
        input_text="\n".join(task_paths) + "\n",
    )
    run(
        "git",
        "-C",
        str(UPSTREAM),
        "sparse-checkout",
        "add",
        "tools",
        "agent",
        "grading",
    )
    run("git", "-C", str(UPSTREAM), "checkout", "main")
    revision = subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    print(f"Cybench runtime ready at {UPSTREAM}\nrevision={revision}")


if __name__ == "__main__":
    main()
