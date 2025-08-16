param([switch]$NoTUI)
$venv = Join-Path $PSScriptRoot '.venv'
if (-Not (Test-Path $venv)) { python -m venv $venv }
& "$venv\Scripts\Activate.ps1"
pip install -r requirements.txt | Out-Null
if (-Not (Test-Path '.env.local') -and (Test-Path '.env.example')) { Copy-Item '.env.example' '.env.local' }
foreach ($line in Get-Content .env.local) { if ($line -and $line -notmatch '^#'){ $parts=$line -split '=',2; if($parts.Length -eq 2){ set-item -path env:$parts[0] -value $parts[1] } } }
python -m integrations.google_oauth | Out-Null
$boot = Start-Process -PassThru python -ArgumentList 'orchestrator.py','boot'
if (-Not $NoTUI) { python orchestrator.py shell }
