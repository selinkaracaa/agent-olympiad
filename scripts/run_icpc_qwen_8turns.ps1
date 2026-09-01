# Qwen · ICPC WF 2012 Bottles · centralized · 8 turns · enforced rule card
$ErrorActionPreference = "Stop"
$RepoRoot = Join-Path $PSScriptRoot ".."
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot "Resolve-Python.ps1")

function Import-LocalEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or $line -notmatch "=") { return }
        $name, $value = $line.Split("=", 2)
        $name = $name.Trim()
        $value = $value.Trim().Trim('"').Trim("'")
        if ($name -and -not [string]::IsNullOrWhiteSpace($value)) {
            Set-Item -Path "env:$name" -Value $value
        }
    }
}

Import-LocalEnv (Join-Path $RepoRoot ".env")
if (-not $env:TINKER_API_KEY) {
    Write-Error "Set TINKER_API_KEY before running (same key as prior Tinker runs)."
}

$PythonExe = Get-AgentOlympiadPython
Write-Host "Using: $PythonExe" -ForegroundColor DarkGray

& $PythonExe src/run_competition_batch.py `
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
