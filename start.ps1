param(
    [string[]]$Services = @("postgres", "api", "web")
)
$ErrorActionPreference = "Stop"
$Root = [System.IO.Path]::GetFullPath($PSScriptRoot)
Set-Location $Root
$cacheSetup = Join-Path $Root "scripts\setup\use-d-drive-caches.ps1"
$composeFile = Join-Path $Root "docker-compose.yml"

if (-not (Test-Path -LiteralPath $composeFile -PathType Leaf)) {
    throw "The Docker source stack is not included in this installed ANN payload. Launch desktop\ANN.exe instead."
}
if (Test-Path -LiteralPath $cacheSetup -PathType Leaf) {
    . $cacheSetup
}

if (-not $env:API_DOCKERFILE) {
    $env:API_DOCKERFILE = "docker/api.Dockerfile"
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose -f $composeFile up -d @Services
    Write-Host "API: http://localhost:8000/api/health"
    Write-Host "Web: http://localhost:3000"
} else {
    throw "Docker was not found on PATH. Install Docker Desktop with WSL2 support before starting services. Host execution is intentionally blocked."
}
