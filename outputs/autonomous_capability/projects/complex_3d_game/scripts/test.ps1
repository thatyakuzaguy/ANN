$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
docker compose run --rm api pytest -q
docker compose run --rm web npm run build
