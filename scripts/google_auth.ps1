$venv = Join-Path $PSScriptRoot '..\.venv'
if (-Not (Test-Path $venv)) { python -m venv $venv }
& "$venv\Scripts\Activate.ps1"
python -m integrations.google_oauth
