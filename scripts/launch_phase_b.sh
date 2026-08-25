#!/bin/zsh
# Detached Phase B matrix launcher (macOS-safe).
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
if [[ -z "${PERPLEXITY_API_KEY:-}" ]]; then
  echo "PERPLEXITY_API_KEY not set" >&2
  exit 1
fi
RESUME="${1:-results/phase_b/20260821-165143/phase_b_matrix.json}"
LOG="${2:-results/phase_b_live_run.log}"
mkdir -p results/phase_b
{
  echo ""
  echo "===== RESTART $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
} >> "$LOG"
export PYTHONUNBUFFERED=1
nohup python3 -u src/run_phase_b_matrix.py --live --resume "$RESUME" >> "$LOG" 2>&1 &
PID=$!
echo "$PID" > results/phase_b_live_run.pid
echo "started pid=$PID resume=$RESUME log=$LOG"
