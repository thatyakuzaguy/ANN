param(
  [string]$PartsRoot = $PSScriptRoot,
  [string]$OutputRoot = "D:\ANN-Release",
  [string]$InstallRoot = "D:\ANN",
  [switch]$RunInstaller,
  [switch]$SkipShortcut
)

$ErrorActionPreference = "Stop"

function Resolve-SafeReleaseRoot {
  param([string]$PathValue, [string]$Label)
  $full = [System.IO.Path]::GetFullPath($PathValue).TrimEnd('\')
  if ($full -match '^[Cc]:\\') { throw "$Label on C:\ is blocked by ANN release policy." }
  if ($full -notmatch '^[DdEe]:\\' -or $full.Length -lt 6) { throw "Unsafe $Label path: $full" }
  return $full
}

$parts = Resolve-SafeReleaseRoot $PartsRoot "parts root"
$output = Resolve-SafeReleaseRoot $OutputRoot "output root"
$install = Resolve-SafeReleaseRoot $InstallRoot "install root"
$manifestPath = Join-Path $parts "ANN_RELEASE_PARTS.json"
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
  throw "ANN_RELEASE_PARTS.json was not found: $manifestPath"
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$manifest.status -ne "OFFLINE_RELEASE_BUNDLE_READY") {
  throw "ANN release parts manifest is not ready."
}
if (Test-Path -LiteralPath $output) {
  if (@(Get-ChildItem -LiteralPath $output -Force -ErrorAction Stop).Count -gt 0) {
    throw "OutputRoot must be empty: $output"
  }
} else {
  New-Item -ItemType Directory -Path $output | Out-Null
}

$archivePath = Join-Path $output ([string]$manifest.archive_name)
$target = [System.IO.File]::Open($archivePath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
try {
  foreach ($entry in @($manifest.parts | Sort-Object index)) {
    $name = [string]$entry.file_name
    if (-not $name -or [System.IO.Path]::GetFileName($name) -ne $name) { throw "Unsafe release part name: $name" }
    $path = Join-Path $parts $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Release part missing: $name" }
    $file = Get-Item -LiteralPath $path
    if ([int64]$file.Length -ne [int64]$entry.size_bytes) { throw "Release part size mismatch: $name" }
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne ([string]$entry.sha256).ToLowerInvariant()) { throw "Release part SHA256 mismatch: $name" }
    $source = [System.IO.File]::OpenRead($path)
    try { $source.CopyTo($target) } finally { $source.Dispose() }
  }
} finally {
  $target.Dispose()
}

$archive = Get-Item -LiteralPath $archivePath
if ([int64]$archive.Length -ne [int64]$manifest.archive_size_bytes) { throw "Reconstructed archive size mismatch." }
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($archiveHash -ne ([string]$manifest.archive_sha256).ToLowerInvariant()) { throw "Reconstructed archive SHA256 mismatch." }

Expand-Archive -LiteralPath $archivePath -DestinationPath $output -Force
Remove-Item -LiteralPath $archivePath -Force
$setup = Join-Path $output "installer\ANN_Setup.exe"
if (-not (Test-Path -LiteralPath $setup -PathType Leaf)) { throw "ANN_Setup.exe missing after extraction." }
Write-Host "ANN release assembled and hash verified at $output"

if ($RunInstaller) {
  $arguments = @("-InstallRoot", $install)
  if ($SkipShortcut) { $arguments += "-SkipShortcut" }
  & $setup @arguments
  if ($LASTEXITCODE -ne 0) { throw "ANN_Setup.exe failed with exit code $LASTEXITCODE" }
}
