param(
  [int[]] $Budgets = @(512, 832, 1344, 2176, 3520),
  [string] $EvalSet = "AIME24"
)

# Optional venv activation if present
$venv = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venv) { . $venv }

New-Item -ItemType Directory -Force -Path runs | Out-Null

# Adjust this to your real inference entrypoint if different
$cmd = 'python .\infer_reasoning.py --max-think {budget} --min-think {budget} --force-continue Wait --evalset {eval} --out runs\aime_b{budget}.json'
$cmd = $cmd -replace '{eval}', $EvalSet

Write-Host "[sesamawake] budgets: $($Budgets -join ', ')"
Write-Host "[sesamawake] template: $cmd"

if ($Budgets.Count -gt 0) {
  $args = @('--cmd', $cmd, '--budgets') + ($Budgets | ForEach-Object { "$_" }) + @('--out', 'runs\fib_summary.json')
} else {
  $args = @('--cmd', $cmd, '--out', 'runs\fib_summary.json')
}
python .\tools\bench_fibonacci.py @args

if (Test-Path 'runs\fib_summary.json') {
  Write-Host "[sesamawake] OK -> runs\fib_summary.json"
} else {
  Write-Host "[sesamawake] finished with no summary file"
}
