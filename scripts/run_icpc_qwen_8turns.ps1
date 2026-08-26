# Qwen · ICPC WF 2012 Bottles · centralized · 8 turns · enforced rule card
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not $env:TINKER_API_KEY) {
    Write-Error "Set TINKER_API_KEY before running (same key as prior Tinker runs)."
}

python src/run_competition_batch.py `
    --live `
    --provider tinker `
    --model Qwen/Qwen3.6-35B-A3B `
    --max-output-tokens 8192 `
    --temperature 0.2 `
    --competitions icpc `
    --problem-id icpc_wf_2012_bottles `
    --schema centralized `
    --max-turns 8 `
    --rules-mode enforced `
    --no-judge-task `
    --no-judge-collab `
    --output results/icpc_tinker_qwen_8turns

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "DONE -> results/icpc_tinker_qwen_8turns/competition_batch.json" -ForegroundColor Green
