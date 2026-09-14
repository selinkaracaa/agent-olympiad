param(
    [ValidateSet('register','run','report','all')][string]$Stage = 'all',
    [string]$Output = 'results/otc_pipeline',
    [string]$Model = 'openai/gpt-5.4-mini',
    [string]$Competitions = ''
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $repoRoot
$pipelinePython = Join-Path (Split-Path $repoRoot -Parent) '.venv/Scripts/python.exe'
if ($env:PIPELINE_PYTHON) { $pipelinePython = $env:PIPELINE_PYTHON }
$pipelineArgs = @('-u','scripts/run_pipeline.py',$Stage,'--output',$Output,'--model',$Model)
if ($Competitions) { $pipelineArgs += @('--competitions',$Competitions) }
& $pipelinePython @pipelineArgs
exit $LASTEXITCODE
