Param(
  [string]$Model = $env:CLI_MODEL,
  [string]$Endpoint = $env:OLLAMA_HOST,
  [int]$MaxHistoryChars = 8000,
  [switch]$Raw
)
$ErrorActionPreference = "Stop"

function Read-FileSafe([string]$Path){
  if(!(Test-Path $Path)){ return "[ERROR] NotFound: $Path" }
  $info=Get-Item $Path -ErrorAction SilentlyContinue
  if($info.PSIsContainer){
    $files=Get-ChildItem -Recurse -File $Path | Where-Object { $_.Length -lt (800*1024) }
    return ($files | ForEach-Object { "`n--- FILE: $($_.FullName) ---`n" + (Get-Content -Raw $_.FullName) }) -join "`n"
  } else {
    if($info.Length -gt (2*1024*1024)){ return "[WARN] Skipped large file: $Path ($($info.Length) bytes)" }
    try{ return Get-Content -Raw $Path }catch{ return "[ERROR] ReadFail: $Path :: $($_.Exception.Message)" }
  }
}

function Resolve-AtRefs([string]$Text){
  $pattern='(@\"[^\"]+\"|@\S+)'
  $result=$Text
  foreach($m in [regex]::Matches($Text,$pattern)){
    $token=$m.Value
    $raw=$token.TrimStart('@').Trim('"')
    $content=Read-FileSafe $raw
    $inj="`n<file name=\"$raw\">`n$content`n</file>`n"
    $result=$result.Replace($token,$inj)
  }
  return $result
}

function Load-Context(){ if(Test-Path "contexto_local.md"){ return Get-Content -Raw "contexto_local.md" } return "" }

function Load-History(){
  $f="memory/session.jsonl"; if(!(Test-Path $f)){ return @() }
  $arr=@(); Get-Content $f | ForEach-Object { if($_.Trim().Length -gt 0){ $arr+=($_ | ConvertFrom-Json) } }; return $arr
}

function Save-HistoryEntry([string]$role,[string]$content){
  $e=@{role=$role;content=$content;ts=(Get-Date).ToString("s")}
  ($e|ConvertTo-Json -Compress) | Add-Content -Encoding UTF8 memory/session.jsonl
}

function Trim-History(){
  $p="memory/session.jsonl"; if(!(Test-Path $p)){ return }
  $entries=Get-Content $p | ForEach-Object { $_ | ConvertFrom-Json }
  $acc=0; $kept=@()
  foreach($e in ($entries | Select-Object -Last 100)){
    $c = if($e.content){ [string]$e.content } else { "" }
    $len=$c.Length; $acc+=$len; $kept+=$e
    if($acc -gt $MaxHistoryChars){ break }
  }
  Remove-Item $p -ErrorAction SilentlyContinue
  foreach($k in $kept){ ($k|ConvertTo-Json -Compress) | Add-Content -Encoding UTF8 $p }
}

function Build-Prompt([string]$user){
  $ctx=Load-Context
  $hist=Load-History
  $histStr=($hist|ForEach-Object { "<"+$_.role+">"+$_.content+"</"+$_.role+">" }) -join "`n"
  $expanded=Resolve-AtRefs $user
  @"
<system>
$ctx
</system>
<history>
$histStr
</history>
<user>
$expanded
</user>

You may request a safe tool execution by returning:
<tool_code>YOUR_COMMAND_HERE</tool_code>
Do not run destructive commands. Keep outputs concise.
"@
}

function Is-ImagePath([string]$s){ return ($s -match '\.(png|jpg|jpeg|webp|bmp)$') }
function Extract-ImagePaths([string]$txt){
  $pattern='(@\"[^\"]+\"|@\S+)'; $list=@()
  foreach($m in [regex]::Matches($txt,$pattern)){ $p=$m.Value.TrimStart('@').Trim('"'); if(Is-ImagePath $p){ $list+=$p } }
  $list|Select-Object -Unique
}

function Call-Ollama([string]$model,[string]$prompt,[string[]]$images){
  $args=@('run',$model,'--prompt',$prompt)
  foreach($img in $images){ if(Test-Path $img){ $args+=@('--image',(Resolve-Path $img)) } }
  $psi=New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName='ollama'
  $psi.ArgumentList.AddRange($args)
  $psi.RedirectStandardOutput=$true
  $psi.RedirectStandardError=$true
  $psi.UseShellExecute=$false
  $p=New-Object System.Diagnostics.Process
  $p.StartInfo=$psi
  [void]$p.Start()
  $stdout=$p.StandardOutput.ReadToEnd()
  $stderr=$p.StandardError.ReadToEnd()
  $p.WaitForExit()
  if($stderr.Trim().Length -gt 0){ Write-Warning $stderr }
  return $stdout
}

function Maybe-Execute-Tool([string]$text){
  $m=[regex]::Match($text,'<tool_code>([\s\S]*?)</tool_code>')
  if(-not $m.Success){ return $text }
  $cmd=$m.Groups[1].Value.Trim()
  Write-Host "`nModel requests to run:" -ForegroundColor Yellow
  Write-Host "    $cmd" -ForegroundColor Yellow
  $ans=Read-Host "Allow execution? (y/n)"
  if($ans -ne 'y'){ return $text+"`n[USER] Denied tool execution." }
  try{
    $out=& powershell -NoProfile -ExecutionPolicy Bypass -Command $cmd 2>&1 | Out-String
    return $text+"`n<tool_result>`n"+$out+"`n</tool_result>"
  }catch{
    return $text+"`n<tool_result_error>"+$_.Exception.Message+"</tool_result_error>"
  }
}

if(-not $Model){ $Model='mylocal' }
if(-not (Test-Path 'memory')){ New-Item -ItemType Directory memory | Out-Null }

Write-Host "CLI+ Orchestrator ready. Model: $Model" -ForegroundColor Cyan
Write-Host "Type 'exit' to quit." -ForegroundColor DarkGray

while($true){
  $user=Read-Host "`nYou"
  if($user -eq 'exit'){ break }
  Save-HistoryEntry 'user' $user
  Trim-History
  $images=Extract-ImagePaths $user
  $prompt=Build-Prompt $user
  $out=Call-Ollama $Model $prompt $images
  $out2=Maybe-Execute-Tool $out
  $clean=$out2 -replace '.*<assistant>','<assistant>'
  Write-Host "`nAssistant:" -ForegroundColor Green
  Write-Host ($clean)
  Save-HistoryEntry 'assistant' $out2
}
Write-Host "Goodbye." -ForegroundColor Cyan
