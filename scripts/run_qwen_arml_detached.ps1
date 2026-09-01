# Detached launcher: survives Cursor agent shell timeouts.
$ErrorActionPreference = "Stop"
$RepoRoot = "e:\agent_olympiad\agent-team-features-main"
$LogPath = Join-Path $RepoRoot "results\qwen_arml_run.log"
$PidPath = Join-Path $RepoRoot "results\qwen_arml_run.pid"
$RunScript = Join-Path $RepoRoot "scripts\run_qwen_arml_schemas.ps1"

New-Item -ItemType Directory -Force -Path (Split-Path $LogPath) | Out-Null
"===== START $(Get-Date -Format o) =====" | Out-File -FilePath $LogPath -Encoding utf8

$proc = Start-Process powershell `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Hidden `
    -PassThru `
    -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "& '$RunScript' *>&1 | Tee-Object -FilePath '$LogPath' -Append"
    )

$proc.Id | Out-File -FilePath $PidPath -Encoding ascii -NoNewline
Write-Host "Detached PID $($proc.Id). Log: $LogPath"
