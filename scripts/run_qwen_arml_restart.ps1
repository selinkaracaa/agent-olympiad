# Open a separate PowerShell window for long Tinker runs (won't die with Cursor agent).
$RepoRoot = "e:\agent_olympiad\agent-team-features-main"
$RunScript = Join-Path $RepoRoot "scripts\run_qwen_arml_schemas.ps1"
$LogPath = Join-Path $RepoRoot "results\qwen_arml_run.log"

"===== RESTART $(Get-Date -Format o) =====" | Out-File -FilePath $LogPath -Encoding utf8

Start-Process powershell `
    -WorkingDirectory $RepoRoot `
    -ArgumentList @(
        "-NoExit",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "& '$RunScript' *>&1 | Tee-Object -FilePath '$LogPath' -Append"
    )

Write-Host "Started in new window. Log: $LogPath"
