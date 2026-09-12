# Python environment

Canonical interpreter for `agent-team-features-main` is the monorepo virtualenv:

```text
e:\agent_olympiad\.venv\Scripts\python.exe
```

- Runtime: **Python 3.12** (not 3.14)
- Do **not** use `py -3.14` or the user-site Python 3.14 install
- Required packages for live Tinker runs include at least `tinker` and `jinja2`

## Activate (PowerShell)

From this repo:

```powershell
cd e:\agent_olympiad\agent-team-features-main
e:\agent_olympiad\.venv\Scripts\Activate.ps1
python -c "import sys, tinker, jinja2; print(sys.version)"
```

Or call the interpreter directly without activating:

```powershell
e:\agent_olympiad\.venv\Scripts\python.exe src\run_competition_batch.py --help
e:\agent_olympiad\.venv\Scripts\python.exe src\vjudge_gateway.py serve --port 8787
```

## Scripts

PowerShell launchers under `scripts/` resolve Python in this order:

1. `e:\agent_olympiad\.venv\Scripts\python.exe` (preferred)
2. `agent-team-features-main\.venv\Scripts\python.exe` (optional local copy)
3. `$env:VIRTUAL_ENV\Scripts\python.exe` if already activated

They fail closed if none of the above work. There is no fallback to `py -3.14`.

## Why not 3.14

Earlier experiments used `py -3.14` when the venv looked incomplete. That path triggers Pydantic v1 warnings under 3.14 and diverges from the shared project env. Stick to `.venv` (3.12) for reproducible agent / VJudge gateway runs.

## Docker isolation image

Local sample execution and isolated Python judging require Docker Desktop (or
another Docker daemon) to be running before the contest starts. The runner uses
`--pull=never` against the pinned `PYTHON_IMAGE` in `src/isolated_python.py`;
opening Docker alone is not sufficient until that image is present locally.

```powershell
docker pull python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534
docker info
e:\agent_olympiad\.venv\Scripts\python.exe -c "from isolated_python import run_python_isolated; print(run_python_isolated('print(42)').stdout)"
```

Expected smoke output: `42`. For remote ICPC / Kattis sessions, also start the
VJudge gateway (`serve --port 8787`) and confirm `http://127.0.0.1:8787/v1/health`
returns `ok`. Full isolation contract: `docs/contest-systems.md`.
