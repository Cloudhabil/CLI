param([switch]$NoTUI)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$venv = "$root/.venv"
if (!(Test-Path $venv)) { python -m venv $venv }
. "$venv/Scripts/Activate.ps1"
pip install -r requirements.txt
if (!(Test-Path '.env.local')) { Copy-Item '.env.example' '.env.local' }
$env:PYTHONPATH = $root
$env:AGENT_SERVER_SECRET = $env:AGENT_SERVER_SECRET
if (!(Test-Path 'data/google/token.json')) { powershell -ExecutionPolicy Bypass -File scripts/google_auth.ps1 }
Start-Process -FilePath python -ArgumentList 'orchestrator.py','boot'
if (-not $NoTUI) { python orchestrator.py shell }
