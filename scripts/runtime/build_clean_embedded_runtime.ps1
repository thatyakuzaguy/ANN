param(
  [string]$BasePythonRoot = "D:\ANN\runtime\python",
  [string]$ExistingWheelhouse = "D:\ANN\runtime\wheels",
  [string]$OutputRoot = "",
  [switch]$AcquireMissingWheels,
  [switch]$Materialize,
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$Builder = Join-Path $PSScriptRoot "build_clean_embedded_runtime.py"
$Python = Join-Path $BasePythonRoot "python.exe"
if (-not $OutputRoot) {
  $OutputRoot = Join-Path $RepoRoot "outputs\release_build\runtime_clean"
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
  throw "Release builder Python is missing: $Python"
}

$Arguments = @(
  $Builder,
  "--base-python", $BasePythonRoot,
  "--existing-wheelhouse", $ExistingWheelhouse,
  "--output", $OutputRoot
)
if ($AcquireMissingWheels) { $Arguments += "--acquire-missing-wheels" }
if ($Materialize) { $Arguments += "--materialize" }
if ($Force) { $Arguments += "--force" }

& $Python @Arguments
if ($LASTEXITCODE -ne 0) {
  throw "Clean embedded runtime builder failed with exit code $LASTEXITCODE."
}
