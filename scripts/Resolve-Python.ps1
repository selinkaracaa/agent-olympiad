# Resolve the monorepo .venv Python (never py -3.14).
# Dot-source from other scripts: . "$PSScriptRoot\Resolve-Python.ps1"

function Get-AgentOlympiadPython {
    $candidates = @()
    if ($PSScriptRoot) {
        $featuresRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
        $monoRoot = (Resolve-Path (Join-Path $featuresRoot "..")).Path
        $candidates += (Join-Path $monoRoot ".venv\Scripts\python.exe")
        $candidates += (Join-Path $featuresRoot ".venv\Scripts\python.exe")
    }
    if ($env:VIRTUAL_ENV) {
        $candidates += (Join-Path $env:VIRTUAL_ENV "Scripts\python.exe")
    }

    foreach ($path in $candidates) {
        if ($path -and (Test-Path $path)) {
            $null = & $path -c "import tinker, jinja2" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $path
            }
        }
    }

    throw @"
No usable .venv Python found.
Expected: e:\agent_olympiad\.venv\Scripts\python.exe
See docs/PYTHON_ENV.md. Do not use py -3.14.
"@
}
