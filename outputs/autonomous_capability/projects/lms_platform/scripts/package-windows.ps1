$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm is required to package the Windows desktop app."
}

Push-Location "apps\desktop"
npm install
npm run package
Pop-Location

$Release = Join-Path $Root "release"
New-Item -ItemType Directory -Force -Path $Release | Out-Null
$DesktopDist = Join-Path $Root "apps\desktop\dist"
Compress-Archive -Path (Join-Path $DesktopDist "*") -DestinationPath (Join-Path $Release "windows-desktop.zip") -Force
Write-Host "Windows desktop package: $Release\windows-desktop.zip"
