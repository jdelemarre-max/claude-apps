$ErrorActionPreference = "Stop"
$raw  = [Console]::In.ReadToEnd()
$data = $raw | ConvertFrom-Json
$cmd  = [string]$data.tool_input.command

# --- VERBODEN PATRONEN (bewerk deze lijst) ---
$forbidden = @(
  'authuser',
  'rm\s+-rf\s+/',
  'git\s+push\s+.*--force',
  'git\s+push\s+.*-f\b',
  'git\s+reset\s+--hard',
  'Remove-Item\s+.*-Recurse\s+.*-Force'
)

foreach ($pat in $forbidden) {
  if ($cmd -match $pat) {
    $out = @{ hookSpecificOutput = @{
      hookEventName = "PreToolUse"
      permissionDecision = "deny"
      permissionDecisionReason = "Geblokkeerd door guard: patroon '$pat' is een harde regel."
    } } | ConvertTo-Json -Depth 5 -Compress
    Write-Output $out
    exit 0
  }
}
exit 0
