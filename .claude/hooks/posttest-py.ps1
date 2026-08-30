$ErrorActionPreference = "Stop"
$raw  = [Console]::In.ReadToEnd()
$data = $raw | ConvertFrom-Json
$path = [string]$data.tool_input.file_path

if ($path -match '\.py$' -and (Test-Path $path)) {
  $prevPref = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  $result = & python -m py_compile $path 2>&1 | Out-String
  $exitCode = $LASTEXITCODE
  $ErrorActionPreference = $prevPref
  if ($exitCode -ne 0) {
    $out = @{
      decision = "block"
      reason = "Syntax-fout na edit in $path`:`n$result"
    } | ConvertTo-Json -Depth 5 -Compress
    Write-Output $out
    exit 0
  }
}
exit 0
