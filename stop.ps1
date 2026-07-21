$ErrorActionPreference = "Stop"
$Root = [System.IO.Path]::GetFullPath($PSScriptRoot)
Set-Location $Root
$composeFile = Join-Path $Root "docker-compose.yml"

if ((Test-Path -LiteralPath $composeFile -PathType Leaf) -and (Get-Command docker -ErrorAction SilentlyContinue)) {
    docker compose -f $composeFile down
    Write-Host "Docker services stopped."
} else {
    Write-Warning "No Docker source stack is active here. Close ANN Desktop to stop its local API and web child processes."
}
