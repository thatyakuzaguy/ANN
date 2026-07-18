param(
  [string]$InstallRoot = "D:\ANN",
  [switch]$RemoveProjects,
  [switch]$RemoveModels,
  [switch]$RemoveOutputs
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
if ($root -match '^[Cc]:\\') { throw "C:\ uninstall roots are blocked by default." }
if ($root -notmatch '^[DdEe]:\\' -or $root.Length -lt 6) { throw "Unsafe ANN uninstall root: $root" }

$remove = @(
  "agentic_network", "apps", "packages", "scripts", "config", "installer", "desktop",
  "runtime", "adapters", "pyproject.toml", "README.md", "start.ps1", "stop.ps1",
  "install_manifest.json", "install_log.txt"
)
if ($RemoveProjects) { $remove += "projects" }
if ($RemoveModels) { $remove += "models" }
if ($RemoveOutputs) { $remove += @("outputs", "data", "logs") }

foreach ($name in $remove) {
  $target = Join-Path $root $name
  if (-not (Test-Path -LiteralPath $target)) { continue }
  $full = [System.IO.Path]::GetFullPath($target)
  if (-not $full.StartsWith("$root\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove outside install root: $target"
  }
  Remove-Item -LiteralPath $target -Recurse -Force
}
Write-Host "ANN application removed. Projects, models, outputs, data, and logs were preserved unless explicitly selected."
