#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ -n "${PIPELINE_PYTHON:-}" ]]; then
  PY="$PIPELINE_PYTHON"
elif [[ -x ../.venv/bin/python ]]; then
  PY=../.venv/bin/python
elif [[ -f ../.venv/Scripts/python.exe ]]; then
  PY=../.venv/Scripts/python.exe
else
  PY=python3
fi
exec "$PY" -u scripts/run_pipeline.py "${@:-all}"
