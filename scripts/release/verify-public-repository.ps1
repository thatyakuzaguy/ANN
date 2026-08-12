[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [switch]$AllowContentDrift,
    [switch]$UpdateManifest
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
$RepositoryRoot = [IO.Path]::GetFullPath($RepositoryRoot)
$manifestPath = Join-Path $RepositoryRoot "PUBLIC_RELEASE_MANIFEST.json"
$configPath = Join-Path $RepositoryRoot "config\public-release.json"
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$allowedDirectories = @(
    $config.source_directories | ForEach-Object {
        ([string]$_).Replace('\', '/').Trim('/')
    }
)
$allowedFiles = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
foreach ($item in $config.source_files) {
    [void]$allowedFiles.Add(([string]$item).Replace('\', '/').TrimStart('/'))
}

function Test-AnnPublicPathAllowed {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    $normalized = $RelativePath.Replace('\', '/').TrimStart('/')
    if ($allowedFiles.Contains($normalized)) {
        return $true
    }
    foreach ($directory in $allowedDirectories) {
        if ($normalized.StartsWith($directory + '/', [StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

$privateKeyMarkers = @("RSA ", "EC ", "OPENSSH ", "") | ForEach-Object {
    "-----BEGIN $($_)PRIVATE KEY-----"
}
$blockedIdentityPatterns = @()
if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    $blockedIdentityPatterns += [regex]::Escape($env:USERPROFILE)
}
if (-not [string]::IsNullOrWhiteSpace($env:USERNAME)) {
    $blockedIdentityPatterns += [regex]::Escape("/home/$($env:USERNAME)")
}
$gitEmail = (git -C $RepositoryRoot config user.email 2>$null)
if (-not [string]::IsNullOrWhiteSpace($gitEmail)) {
    $blockedIdentityPatterns += [regex]::Escape($gitEmail.Trim())
}
$publicTextExtensions = @(
    ".bat", ".cfg", ".cff", ".cs", ".css", ".dockerfile", ".example",
    ".html", ".ini", ".js", ".json", ".jsonl", ".md", ".mjs", ".ps1",
    ".py", ".sql", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml"
)

function Assert-AnnPublicTextSafe {
    param([Parameter(Mandatory = $true)][string]$PathValue)
    $file = Get-Item -LiteralPath $PathValue
    if ($publicTextExtensions -notcontains $file.Extension.ToLowerInvariant() -and
        $file.Name -notin @("Dockerfile", ".env.example", ".gitignore", ".dockerignore")) {
        return
    }
    $content = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content) {
        $content = ""
    }
    foreach ($pattern in $blockedIdentityPatterns) {
        if ($content -match $pattern) {
            throw "Machine-specific identity found in public source: $($file.FullName)"
        }
    }
    foreach ($marker in $privateKeyMarkers) {
        if ($content.Contains($marker)) {
            throw "Private key material found in public source: $($file.FullName)"
        }
    }
}

if ($UpdateManifest) {
    $gitRoot = [string](git -C $RepositoryRoot rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitRoot)) {
        throw "Updating the public manifest requires a Git worktree."
    }
    $resolvedGitRoot = [IO.Path]::GetFullPath($gitRoot.Trim())
    if (-not $resolvedGitRoot.Equals($RepositoryRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "RepositoryRoot must be the root of the public Git worktree."
    }

    $relativeFiles = @(
        git -C $RepositoryRoot ls-files --cached --others --exclude-standard |
            Where-Object { $_ -ne "PUBLIC_RELEASE_MANIFEST.json" } |
            Sort-Object
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to enumerate public source files from Git."
    }

    $entries = [Collections.Generic.List[object]]::new()
    $totalBytes = [int64]0
    $maximumBytes = [int64]$config.maximum_file_size_mb * 1MB
    foreach ($relativePath in $relativeFiles) {
        if (-not (Test-AnnPublicPathAllowed $relativePath)) {
            throw "File is outside the public release allowlist: $relativePath"
        }
        if ([IO.Path]::IsPathRooted($relativePath) -or $relativePath -split '[\\/]' -contains '..') {
            throw "Unsafe public manifest path: $relativePath"
        }
        $fullPath = [IO.Path]::GetFullPath((Join-Path $RepositoryRoot $relativePath))
        $prefix = $RepositoryRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if (-not $fullPath.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Public manifest path escaped repository: $relativePath"
        }
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            throw "Public manifest source file is missing: $relativePath"
        }
        $file = Get-Item -LiteralPath $fullPath
        if ($file.Length -gt $maximumBytes) {
            throw "File exceeds public size limit ($($config.maximum_file_size_mb) MiB): $relativePath"
        }
        Assert-AnnPublicTextSafe $fullPath
        $totalBytes += $file.Length
        $entries.Add([ordered]@{
            path = $relativePath.Replace('\', '/')
            bytes = [int64]$file.Length
            sha256 = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
        })
    }

    $updatedManifest = [ordered]@{
        schema_version = 1
        generated_at_utc = [DateTime]::UtcNow.ToString("o")
        release_stage = [string]$config.release_stage
        release_version = [string]$config.release_version
        source_revision = (git -C $RepositoryRoot rev-parse HEAD).Trim()
        file_count = $entries.Count
        total_bytes = $totalBytes
        maximum_file_size_mb = [int]$config.maximum_file_size_mb
        files = @($entries)
    }
    $manifestJson = ConvertTo-Json -InputObject $updatedManifest -Depth 5
    [IO.File]::WriteAllText(
        $manifestPath,
        $manifestJson.Replace("`r`n", "`n") + "`n",
        [Text.UTF8Encoding]::new($false)
    )
    Write-Host "Public release manifest updated from $($entries.Count) Git inventory files."
}

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Public release manifest not found: $manifestPath"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$declaredPaths = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$failures = [Collections.Generic.List[string]]::new()
$contentDrift = [Collections.Generic.List[string]]::new()
$actualBytes = [int64]0
$inventoryExcludedSegments = @(
    ".git", ".next", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".tmp", ".venv", ".venv-qlora", "__pycache__", "node_modules",
    "dist", "build", "playwright-report", "test-results"
)
$inventoryExcludedExtensions = @(
    ".7z", ".bin", ".dll", ".exe", ".gguf", ".gz", ".log", ".onnx",
    ".p12", ".pfx", ".pt", ".pth", ".pyc", ".pyd", ".safetensors",
    ".tar", ".tmp", ".tsbuildinfo", ".zip"
)
$inventoryExcludedNames = @(".env", ".DS_Store", "Thumbs.db")

function Get-AnnRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$PathValue
    )
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $pathFull = [IO.Path]::GetFullPath($PathValue)
    $prefix = $rootFull + [IO.Path]::DirectorySeparatorChar
    if (-not $pathFull.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Inventory path escaped public repository: $pathFull"
    }
    return $pathFull.Substring($prefix.Length).Replace('\', '/')
}

foreach ($entry in $manifest.files) {
    if (-not (Test-AnnPublicPathAllowed ([string]$entry.path))) {
        $failures.Add("manifest path outside public allowlist: $($entry.path)")
        continue
    }
    $relativePath = ([string]$entry.path).Replace('/', [IO.Path]::DirectorySeparatorChar)
    if ([IO.Path]::IsPathRooted($relativePath) -or $relativePath -split '[\\/]' -contains '..') {
        $failures.Add("unsafe path: $($entry.path)")
        continue
    }
    $candidate = [IO.Path]::GetFullPath((Join-Path $RepositoryRoot $relativePath))
    $prefix = $RepositoryRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        $failures.Add("path escaped repository: $($entry.path)")
        continue
    }
    [void]$declaredPaths.Add(([string]$entry.path).Replace('\', '/'))
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        $failures.Add("missing file: $($entry.path)")
        continue
    }
    Assert-AnnPublicTextSafe $candidate
    $file = Get-Item -LiteralPath $candidate
    $actualBytes += $file.Length
    if ($file.Length -ne [int64]$entry.bytes) {
        $contentDrift.Add("size mismatch: $($entry.path)")
    }
    $hash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne [string]$entry.sha256) {
        $contentDrift.Add("hash mismatch: $($entry.path)")
    }
}

if ($declaredPaths.Count -ne [int]$manifest.file_count) {
    $failures.Add("manifest file_count does not match unique entries")
}
if ($actualBytes -ne [int64]$manifest.total_bytes) {
    $contentDrift.Add("manifest total_bytes does not match checked files")
}

$gitRoot = [string](git -C $RepositoryRoot rev-parse --show-toplevel 2>$null)
$useGitInventory = $LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($gitRoot)
if ($useGitInventory) {
    $resolvedGitRoot = [IO.Path]::GetFullPath($gitRoot.Trim())
    $useGitInventory = $resolvedGitRoot.Equals(
        $RepositoryRoot,
        [StringComparison]::OrdinalIgnoreCase
    )
}

if ($useGitInventory) {
    $tracked = @(git -C $RepositoryRoot ls-files --cached --others --exclude-standard)
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to enumerate public source files from Git."
    }
}
else {
    $tracked = @(
        Get-ChildItem -LiteralPath $RepositoryRoot -Recurse -File -Force |
            ForEach-Object {
                $relativePath = Get-AnnRelativePath $RepositoryRoot $_.FullName
                $segments = $relativePath -split '/'
                $excluded = @(
                    $segments | Where-Object { $inventoryExcludedSegments -contains $_ }
                ).Count -gt 0
                $excluded = $excluded -or (
                    $inventoryExcludedExtensions -contains $_.Extension.ToLowerInvariant()
                )
                $excluded = $excluded -or ($inventoryExcludedNames -contains $_.Name)
                if (-not $excluded) {
                    $relativePath
                }
            }
    )
}
foreach ($path in $tracked) {
    if ($path -eq "PUBLIC_RELEASE_MANIFEST.json") {
        continue
    }
    if (-not (Test-AnnPublicPathAllowed $path)) {
        $failures.Add("tracked file outside public allowlist: $path")
        continue
    }
    if (-not $declaredPaths.Contains($path.Replace('\', '/'))) {
        $failures.Add("tracked file missing from manifest: $path")
    }
}
if ($tracked.Count -ne ($declaredPaths.Count + 1)) {
    $failures.Add("tracked file count is not manifest entries plus the manifest")
}

if (-not $AllowContentDrift) {
    foreach ($message in $contentDrift) {
        $failures.Add($message)
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    throw "Public release verification failed with $($failures.Count) error(s)."
}

if ($contentDrift.Count -gt 0) {
    foreach ($message in $contentDrift) {
        Write-Warning $message
    }
    Write-Host "Public repository structure verified with $($contentDrift.Count) expected content drift item(s)."
}
else {
    Write-Host "Public release manifest verified strictly: $($manifest.file_count) files, $actualBytes bytes."
}
