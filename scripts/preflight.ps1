Param()
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Preflight starting..."

try { $py = & python --version; Write-Host "Python: $py" }
catch { Write-Error "Python not found in PATH or venv not activated."; exit 1 }

$envPath = ".env.local"
if (Test-Path $envPath) { Write-Host ".env.local present" } else { Write-Warning ".env.local missing. Copy .env.example" }

$ollamaHost = $env:OLLAMA_HOST; if (-not $ollamaHost) { $ollamaHost = "http://127.0.0.1:11434" }
try {
  $resp = Invoke-WebRequest -Method Get -Uri "$ollamaHost/api/tags" -TimeoutSec 5
  Write-Host "Ollama reachable. Models:"; ($resp.Content | ConvertFrom-Json).models | ForEach-Object { " - " + $_.name } | Write-Host
} catch { Write-Warning "Ollama not reachable at $ollamaHost" }

Write-Host "Preflight done."
