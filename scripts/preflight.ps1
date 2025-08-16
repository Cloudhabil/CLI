Param()
Write-Host "Preflight checks..." -ForegroundColor Cyan

if (-not (Test-Path ".env.local")) {
  Write-Host "Creating .env.local from .env.example (if present)" -ForegroundColor Yellow
  Copy-Item .env.example .env.local -ErrorAction SilentlyContinue
}

$envVars = @("BUS_TOKEN","AGENT_SHARED_SECRET")
$missing = @()
foreach ($v in $envVars) {
  if (-not $env:$v) { $missing += $v }
}

if ($missing.Count -gt 0) {
  Write-Host "Warning: Missing secrets: $($missing -join ', '). Set them in your environment or .env.local." -ForegroundColor Yellow
}

Write-Host "Preflight complete." -ForegroundColor Green
