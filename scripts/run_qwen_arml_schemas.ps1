# Qwen · ARML Local 2009 · centralized + decentralized · enforced rule card
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
foreach ($scope in @("Process", "User", "Machine")) {
    if (-not $env:TINKER_API_KEY) {
        $value = [Environment]::GetEnvironmentVariable("TINKER_API_KEY", $scope)
        if ($value) { $env:TINKER_API_KEY = $value }
    }
}

if (-not $env:TINKER_API_KEY) {
    Write-Error "TINKER_API_KEY not found. Set it in .env or your shell."
}

$PythonExe = Get-AgentOlympiadPython
Write-Host "Using: $PythonExe" -ForegroundColor DarkGray

$common = @(
    "src/run_competition_batch.py",
    "--live",
    "--provider", "tinker",
    "--model", "Qwen/Qwen3.6-35B-A3B",
    "--max-output-tokens", "8192",
    "--temperature", "0.2",
    "--competitions", "arml_local",
    "--problem-id", "arml_local_2009",
    "--max-turns", "12",
    "--rules-mode", "enforced",
    "--no-judge-task",
    "--no-judge-collab"
)

function Invoke-Batch {
    param([string]$Schema, [string]$Output)
    Write-Host "=== $Schema ===" -ForegroundColor Cyan
    & $PythonExe @common --schema $Schema --output $Output
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Invoke-Batch -Schema "centralized" -Output "results/qwen_arml_centralized_enforced"
Invoke-Batch -Schema "decentralized" -Output "results/qwen_arml_decentralized_enforced"
Write-Host "DONE both runs" -ForegroundColor Green
