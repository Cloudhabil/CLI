param(
  [int[]] $Budgets = @(512, 832, 1344, 2176, 3520),
  [string] $EvalSet = "AIME24"
)
New-Item -ItemType Directory -Force -Path runs | Out-Null
$cmd = 'python .\infer_reasoning.py --max-think {budget} --min-think {budget} --force-continue Wait --evalset {eval} --out runs\aime_b{budget}.json'
$cmd = $cmd -replace '{eval}', $EvalSet
Write-Host "[bench] budgets: $($Budgets -join ', ')"
Write-Host "[bench] cmd template: $cmd"
if ($Budgets.Count -gt 0) {
  $args = @('--cmd', $cmd, '--budgets') + ($Budgets | ForEach-Object { "$_" }) + @('--out', 'runs\fib_summary.json')
} else {
  $args = @('--cmd', $cmd, '--out', 'runs\fib_summary.json')
}
python .\tools\bench_fibonacci.py @args
Write-Host "[bench] done. See runs\fib_summary.json"
