[CmdletBinding()]
param(
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$installerRoot = Join-Path $repositoryRoot "installer"
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = $installerRoot
}
$outputRoot = [IO.Path]::GetFullPath($OutputDirectory)
if ($outputRoot -match '^[Cc]:\\') {
    throw "C:\ output paths are blocked for ANN release launchers."
}
if ($outputRoot -notmatch '^[DdEe]:\\' -or $outputRoot.Length -lt 6) {
    throw "ANN release launchers must be written to a non-shallow D: or E: directory."
}

$compilerCandidates = @(
    (Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
    (Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe")
)
$compiler = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $compiler) {
    throw "The Windows .NET Framework C# compiler was not found."
}

$sharedSource = Join-Path $installerRoot "AnnPowerShellLauncher.cs"
$targets = @(
    [pscustomobject]@{
        Name = "ANN_Setup.exe"
        Source = Join-Path $installerRoot "AnnSetupLauncher.cs"
    },
    [pscustomobject]@{
        Name = "ANN_Uninstall.exe"
        Source = Join-Path $installerRoot "AnnUninstallLauncher.cs"
    }
)
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

$artifacts = foreach ($target in $targets) {
    $outputPath = Join-Path $outputRoot $target.Name
    & $compiler /nologo /target:exe /optimize+ "/out:$outputPath" $sharedSource $target.Source
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $outputPath -PathType Leaf)) {
        throw "Failed to compile $($target.Name)."
    }
    $signature = Get-AuthenticodeSignature -FilePath $outputPath
    [pscustomobject]@{
        name = $target.Name
        path = $outputPath
        size_bytes = (Get-Item -LiteralPath $outputPath).Length
        sha256 = (Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash.ToLowerInvariant()
        signature_status = [string]$signature.Status
    }
}

$result = [pscustomobject]@{
    schema_version = "1.0"
    compiler = $compiler
    output_directory = $outputRoot
    artifacts = @($artifacts)
    downloads_performed = $false
    signing_performed = $false
}
$result | ConvertTo-Json -Depth 5
