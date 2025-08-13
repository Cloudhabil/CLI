param(
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $repo
\.venv\Scripts\Activate.ps1
python agent/auto_dev_agent.py @(@{""="$null"}[$false]) $(if($DryRun){"--dry-run"})

