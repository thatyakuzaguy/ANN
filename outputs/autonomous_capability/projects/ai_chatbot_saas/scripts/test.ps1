$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
docker compose run --rm api pytest
docker compose run --rm web npm run e2e
