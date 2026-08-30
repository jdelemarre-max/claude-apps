$ErrorActionPreference = "Stop"
$raw  = [Console]::In.ReadToEnd()
$data = $raw | ConvertFrom-Json
$path = [string]$data.tool_input.file_path
$content = [string]$data.tool_input.content

$forbiddenPaths = @(
  '\.env($|\.)',
  'secrets[\\/]',
  'client_secret',
  'credentials\.json',
  'token(_\w+)?\.json',
  'id_rsa',
  '\.git-credentials'
)
$forbiddenContent = @(
  'ghp_[A-Za-z0-9]{20,}',
  'AKIA[0-9A-Z]{16}',
  'sk-[A-Za-z0-9]{20,}'
)

foreach ($pat in $forbiddenPaths) {
  if ($path -match $pat) {
    $out = @{ hookSpecificOutput = @{
      hookEventName = "PreToolUse"
      permissionDecision = "deny"
      permissionDecisionReason = "Geblokkeerd door guard: bestandspad '$path' matcht secrets-patroon '$pat'."
    } } | ConvertTo-Json -Depth 5 -Compress
    Write-Output $out
    exit 0
  }
}
foreach ($pat in $forbiddenContent) {
  if ($content -match $pat) {
    $out = @{ hookSpecificOutput = @{
      hookEventName = "PreToolUse"
      permissionDecision = "deny"
      permissionDecisionReason = "Geblokkeerd door guard: content matcht secret-patroon '$pat'."
    } } | ConvertTo-Json -Depth 5 -Compress
    Write-Output $out
    exit 0
  }
}
exit 0
