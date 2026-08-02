[CmdletBinding()]
param([string]$Root = "")

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
} else {
    $Root = [IO.Path]::GetFullPath($Root)
}
if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    throw "ANN root does not exist: $Root"
}
Set-Location $Root

Write-Host "Host NVIDIA status:"
nvidia-smi
if ($LASTEXITCODE -ne 0) { throw "Host nvidia-smi failed." }

Write-Host "Docker NVIDIA status:"
docker run --rm --pull=never --gpus all nvidia/cuda:12.6.3-base-ubuntu24.04 nvidia-smi
if ($LASTEXITCODE -ne 0) { throw "Docker NVIDIA validation failed." }

Write-Host "API CUDA Python package check:"
$services = @(docker compose ps --status running --services)
if ($LASTEXITCODE -ne 0) { throw "Unable to inspect Docker Compose services." }
if ("api" -notin $services) { throw "The ANN api service must be running before GPU verification." }
$Code = @"
from app.core.settings import settings
from agentic_engineering_network.shared.providers import build_provider
provider = build_provider(settings)
print(type(provider).__name__)
print("gpu_layers", settings.local_model_gpu_layers)
print("main_gpu", settings.local_model_main_gpu)
"@
docker compose exec -T api python3 -c $Code
if ($LASTEXITCODE -ne 0) { throw "ANN API GPU provider validation failed." }
