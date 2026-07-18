param(
  [string]$SourceRoot = (Resolve-Path "$PSScriptRoot\..").Path,
  [string]$InstallRoot = "D:\ANN",
  [string]$RuntimeSource = "",
  [string]$DesktopSource = "",
  [string]$ModelSource = "",
  [ValidateSet("Copy", "HardLink")]
  [string]$ModelInstallMode = "Copy",
  [switch]$RequireModels,
  [switch]$SkipShortcut,
  [string]$ShortcutLocation = ""
)

$ErrorActionPreference = "Stop"
$ExcludedNames = @(
  ".git", "models", "training", "outputs", "memory", "knowledge",
  "unsloth_compiled_cache", "__pycache__", ".pytest_cache", ".ruff_cache",
  "node_modules", ".venv-qlora", "tmp"
)
$CodeExcludedNames = @(
  ".git", "__pycache__", ".pytest_cache", ".ruff_cache",
  "node_modules", ".venv-qlora", "tmp"
)

function Write-InstallLog {
  param([string]$Message)
  Add-Content -Path (Join-Path $InstallRoot "install_log.txt") -Value "$(Get-Date -Format o) $Message"
}

function Write-JsonUtf8NoBom {
  param([object]$Payload, [string]$PathValue, [int]$Depth = 10)
  $json = $Payload | ConvertTo-Json -Depth $Depth
  $encoding = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($PathValue, $json, $encoding)
}

function Resolve-SafeRoot {
  param([string]$PathValue)
  $full = [System.IO.Path]::GetFullPath($PathValue)
  if ($full -match '^[Cc]:\\') { throw "C:\ install roots are blocked by default." }
  if ($full -notmatch '^[DdEe]:\\') { throw "ANN install root must be on D: or E:." }
  if ($full.Length -lt 6) { throw "Refusing a shallow install root." }
  return $full.TrimEnd('\')
}

function Copy-Tree {
  param([string]$Source, [string]$Destination, [string[]]$ExcludeDirectories = @())
  if (-not (Test-Path -LiteralPath $Source -PathType Container)) { throw "Required directory missing: $Source" }
  $sourceFull = [System.IO.Path]::GetFullPath($Source).TrimEnd('\')
  $destinationFull = [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')
  if ($sourceFull.Equals($destinationFull, [System.StringComparison]::OrdinalIgnoreCase)) { return }
  New-Item -ItemType Directory -Force -Path $destinationFull | Out-Null
  $arguments = @($sourceFull, $destinationFull, "/E", "/R:2", "/W:1", "/NFL", "/NDL", "/NJH", "/NJS", "/NP")
  if ($ExcludeDirectories.Count -gt 0) { $arguments += "/XD"; $arguments += $ExcludeDirectories }
  & robocopy @arguments | Out-Null
  if ($LASTEXITCODE -gt 7) { throw "robocopy failed for $sourceFull with exit code $LASTEXITCODE" }
  $global:LASTEXITCODE = 0
}

function Resolve-SafePayloadRoot {
  param([string]$PathValue, [string]$Label)
  $full = [System.IO.Path]::GetFullPath($PathValue).TrimEnd('\')
  $drive = [System.IO.Path]::GetPathRoot($full).TrimEnd('\')
  if ($drive -ieq "C:") { throw "$Label on C:\ is blocked by default." }
  if ($drive -notin @("D:", "E:")) { throw "$Label must be on D: or E:." }
  if (-not (Test-Path -LiteralPath $full -PathType Container)) { throw "$Label not found: $full" }
  return $full
}

function Install-ModelPayload {
  param([string]$Source, [string]$Destination, [string]$Mode)
  $installed = @()
  if (-not $Source) { return $installed }
  $safeSource = Resolve-SafePayloadRoot $Source "Model source"
  $verifiedEntries = @{}
  $manifestPath = Join-Path $safeSource "MODEL_PACK_MANIFEST.json"
  if ($RequireModels -and -not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Complete ANN model payload requires MODEL_PACK_MANIFEST.json."
  }
  if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
    $payloadManifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    foreach ($entry in $payloadManifest.files) {
      $relative = [string]$entry.relative_path
      if (-not $relative -or $relative.Replace('\', '/').Split('/') -contains "..") {
        throw "Unsafe model manifest path: $relative"
      }
      $declaredFile = Join-Path $safeSource $relative
      if (-not (Test-Path -LiteralPath $declaredFile -PathType Leaf)) {
        throw "Model manifest file missing: $relative"
      }
      $actualFile = Get-Item -LiteralPath $declaredFile
      if ([int64]$entry.size_bytes -ne [int64]$actualFile.Length) {
        throw "Model size mismatch: $relative"
      }
      $actualHash = (Get-FileHash -LiteralPath $declaredFile -Algorithm SHA256).Hash.ToLowerInvariant()
      if ($actualHash -ne ([string]$entry.sha256).ToLowerInvariant()) {
        throw "Model SHA256 mismatch: $relative"
      }
      $verifiedEntries[$relative.Replace('\', '/').ToLowerInvariant()] = $actualHash
    }
  }
  $files = Get-ChildItem -LiteralPath $safeSource -File -Recurse | Where-Object {
    ($_.Extension -in @(".gguf", ".safetensors", ".json", ".model") -or $_.Name -eq "tokenizer.model") -and
      $_.Name -ne "MODEL_PACK_MANIFEST.json"
  }
  foreach ($file in $files) {
    $sourceUri = New-Object System.Uri(($safeSource.TrimEnd('\') + '\'))
    $fileUri = New-Object System.Uri($file.FullName)
    $relative = [System.Uri]::UnescapeDataString($sourceUri.MakeRelativeUri($fileUri).ToString()).Replace('/', '\')
    if ($relative.Split([System.IO.Path]::DirectorySeparatorChar) -contains "..") {
      throw "Unsafe model payload path: $relative"
    }
    $target = Join-Path $Destination $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    if ($Mode -eq "HardLink") {
      if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Force }
      New-Item -ItemType HardLink -Path $target -Target $file.FullName | Out-Null
    } else {
      Copy-Item -LiteralPath $file.FullName -Destination $target -Force
    }
    $relativeKey = $relative.Replace('\', '/').ToLowerInvariant()
    $targetHash = if ($Mode -eq "HardLink" -and $verifiedEntries.ContainsKey($relativeKey)) {
      $verifiedEntries[$relativeKey]
    } else {
      (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $installed += [ordered]@{
      relative_path = $relative.Replace('\', '/')
      size_bytes = [int64]$file.Length
      sha256 = $targetHash
    }
  }
  return $installed
}

function Update-InstalledModelConfiguration {
  param([string]$Root, [bool]$EnableRealModels)
  $modelRoot = Join-Path $Root "models"
  $mapping = @{
    "qwen2_5_coder_7b_v5" = "qwen2.5-coder-7b-q4_k_m.gguf"
    "qwen3_8b_product_v9_repaired_v2_bullets" = "Qwen3-8B-Q4_K_M.gguf"
    "qwen3_4b_conversation_orchestrator" = "qwen3-4b-instruct-2507-q4_k_m.gguf"
    "qwen3_8b_conversation_orchestrator" = "Qwen3-8B-Q4_K_M.gguf"
    "deepseek_r1_distill_qwen_14b" = "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf"
  }
  $inventoryPath = Join-Path $Root "config\ann_model_inventory.json"
  if (Test-Path -LiteralPath $inventoryPath -PathType Leaf) {
    $inventory = Get-Content -LiteralPath $inventoryPath -Raw | ConvertFrom-Json
    foreach ($model in $inventory.models) {
      $name = [string]$model.model_name
      if (-not $mapping.ContainsKey($name)) { continue }
      $candidate = Join-Path $modelRoot $mapping[$name]
      if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
      $model.path = $candidate.Replace('\', '/')
      $model.source_path = $model.path
      $model.distribution_path = $model.path
      $model.backend = "llama_cpp"
      $model.adapter_path = $null
      $model.status = "detected"
      $model.enabled = $true
    }
    Write-JsonUtf8NoBom $inventory $inventoryPath
  }

  $conversationPath = Join-Path $Root "config\ann_terminal_conversation_runtime.json"
  if (Test-Path -LiteralPath $conversationPath -PathType Leaf) {
    $conversation = Get-Content -LiteralPath $conversationPath -Raw | ConvertFrom-Json
    $conversation.runtime_type = "embedded_windows"
    $conversation.python_executable_windows = (Join-Path $Root "runtime\python\python.exe").Replace('\', '/')
    $conversationModel = Join-Path $modelRoot "qwen3-4b-instruct-2507-q4_k_m.gguf"
    if (Test-Path -LiteralPath $conversationModel -PathType Leaf) {
      $conversation.model_path_windows = $conversationModel.Replace('\', '/')
    }
    Write-JsonUtf8NoBom $conversation $conversationPath
  }

  if ($EnableRealModels) {
    $policyPath = Join-Path $Root "config\ann_model_policy.json"
    if (Test-Path -LiteralPath $policyPath -PathType Leaf) {
      $policy = Get-Content -LiteralPath $policyPath -Raw | ConvertFrom-Json
      $policy.allow_real_model_load = $true
      $policy.default_backend = "llama_cpp"
      Write-JsonUtf8NoBom $policy $policyPath
    }
    $runtimePath = Join-Path $Root "config\ann_runtime_engine.json"
    if (Test-Path -LiteralPath $runtimePath -PathType Leaf) {
      $runtime = Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json
      $runtime.backend = "llama_cpp"
      $runtime.backend_policy.allow_real_model_load = $true
      Write-JsonUtf8NoBom $runtime $runtimePath
    }
  }
}

$SourceRoot = [System.IO.Path]::GetFullPath($SourceRoot).TrimEnd('\')
$InstallRoot = Resolve-SafeRoot $InstallRoot
if ($InstallRoot.Equals($SourceRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Install root must not equal source root."
}

New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
Write-InstallLog "Starting ANN install from $SourceRoot to $InstallRoot"

foreach ($dir in @("agentic_network", "apps", "packages", "scripts", "config", "installer", "desktop", "runtime", "data", "projects", "outputs", "logs", "models", "adapters")) {
  New-Item -ItemType Directory -Force -Path (Join-Path $InstallRoot $dir) | Out-Null
}

$appSource = if (Test-Path -LiteralPath (Join-Path $SourceRoot "payload\app")) {
  Join-Path $SourceRoot "payload\app"
} else {
  $SourceRoot
}

foreach ($name in @("agentic_network", "packages", "config")) {
  Copy-Tree (Join-Path $appSource $name) (Join-Path $InstallRoot $name) $CodeExcludedNames
}
Copy-Tree (Join-Path $appSource "apps\api") (Join-Path $InstallRoot "apps\api") $CodeExcludedNames
Copy-Tree (Join-Path $appSource "scripts\runtime") (Join-Path $InstallRoot "scripts\runtime") $CodeExcludedNames
Copy-Tree (Join-Path $appSource "apps\web\.next\standalone") (Join-Path $InstallRoot "apps\web\.next\standalone") @()

foreach ($name in @("pyproject.toml", "README.md", "start.ps1", "stop.ps1")) {
  $source = Join-Path $appSource $name
  if (Test-Path -LiteralPath $source -PathType Leaf) {
    Copy-Item -LiteralPath $source -Destination (Join-Path $InstallRoot $name) -Force
  }
}

if (-not $DesktopSource) {
  $payloadDesktop = Join-Path $SourceRoot "payload\desktop"
  if (Test-Path -LiteralPath $payloadDesktop -PathType Container) {
    $DesktopSource = $payloadDesktop
  } else {
    $DesktopSource = Get-ChildItem -LiteralPath (Join-Path $appSource "apps\desktop\dist") -Directory -ErrorAction SilentlyContinue |
      Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "Agentic Engineering Network.exe") } |
      Select-Object -First 1 -ExpandProperty FullName
  }
}
if (-not $DesktopSource) { throw "Packaged ANN Desktop payload was not found." }
Copy-Tree $DesktopSource (Join-Path $InstallRoot "desktop") @()

if (-not $RuntimeSource) {
  foreach ($candidate in @(
    (Join-Path $SourceRoot "payload\runtime"),
    (Join-Path $SourceRoot "runtime"),
    (Join-Path $InstallRoot "runtime")
  )) {
    if (Test-Path -LiteralPath (Join-Path $candidate "python\python.exe") -PathType Leaf) {
      $RuntimeSource = $candidate
      break
    }
  }
}
if (-not $RuntimeSource) { throw "Embedded ANN runtime payload was not found." }
$RuntimeSource = [System.IO.Path]::GetFullPath($RuntimeSource).TrimEnd('\')
Copy-Tree (Join-Path $RuntimeSource "python") (Join-Path $InstallRoot "runtime\python") @()
if (Test-Path -LiteralPath (Join-Path $RuntimeSource "wheels") -PathType Container) {
  Copy-Tree (Join-Path $RuntimeSource "wheels") (Join-Path $InstallRoot "runtime\wheels") @()
}

if (-not $ModelSource) {
  foreach ($candidate in @(
    (Join-Path $SourceRoot "payload\models"),
    (Join-Path $SourceRoot "model-pack")
  )) {
    if (Test-Path -LiteralPath $candidate -PathType Container) {
      $ModelSource = $candidate
      break
    }
  }
}
$installedModels = @(Install-ModelPayload $ModelSource (Join-Path $InstallRoot "models") $ModelInstallMode)
if ($RequireModels) {
  foreach ($requiredModel in @(
    "qwen2.5-coder-7b-q4_k_m.gguf",
    "qwen3-4b-instruct-2507-q4_k_m.gguf",
    "Qwen3-8B-Q4_K_M.gguf",
    "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf"
  )) {
    if (-not (Test-Path -LiteralPath (Join-Path $InstallRoot "models\$requiredModel") -PathType Leaf)) {
      throw "Complete ANN model payload is missing: $requiredModel"
    }
  }
}
Update-InstalledModelConfiguration $InstallRoot ([bool]$RequireModels)

foreach ($name in @("ann_launcher.ps1", "create_shortcut.ps1", "uninstall_ann.ps1", "verify_install.ps1")) {
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $InstallRoot "installer\$name") -Force
}

$python = Join-Path $InstallRoot "runtime\python\python.exe"
$desktopExe = Join-Path $InstallRoot "desktop\Agentic Engineering Network.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "Embedded Python missing after install: $python" }
if (-not (Test-Path -LiteralPath $desktopExe -PathType Leaf)) { throw "ANN Desktop executable missing after install: $desktopExe" }
$env:PYTHONPATH = $InstallRoot
& $python -c "import fastapi, uvicorn, PySide6, agentic_network; from agentic_network.models.gpu_policy import llama_cpp_supports_gpu_offload; from agentic_network.runtime_engine.backends.llama_cpp_backend import LlamaCppBackend; print('ANN embedded runtime imports: OK')"
if ($LASTEXITCODE -ne 0) { throw "Embedded runtime import validation failed." }
if ($RequireModels) {
  & $python -c "from agentic_network.runtime_engine.windows_dlls import configure_windows_runtime_dll_paths; from agentic_network.models.gpu_policy import llama_cpp_supports_gpu_offload; configure_windows_runtime_dll_paths(); import llama_cpp; raise SystemExit(0 if llama_cpp_supports_gpu_offload(llama_cpp) is True else 1)"
  if ($LASTEXITCODE -ne 0) { throw "Embedded llama.cpp runtime does not expose GPU offload support." }
}

if (-not $SkipShortcut) {
  $shortcutArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "create_shortcut.ps1"), "-InstallRoot", $InstallRoot)
  if ($ShortcutLocation) { $shortcutArgs += @("-ShortcutLocation", $ShortcutLocation) }
  & powershell.exe @shortcutArgs
  if ($LASTEXITCODE -ne 0) { throw "Shortcut creation failed." }
}

$manifest = [ordered]@{
  schema_version = "1.0"
  installed_at = (Get-Date -Format o)
  source_root = $SourceRoot
  install_root = $InstallRoot
  embedded_python = $python
  desktop_executable = $desktopExe
  embedded_runtime_validated = $true
  model_source = $ModelSource
  model_install_mode = $ModelInstallMode
  installed_models = $installedModels
  shortcut_skipped = [bool]$SkipShortcut
  shortcut_location = $ShortcutLocation
  preserved_by_default = @("projects", "models", "outputs", "data", "logs")
  excluded_source_areas = $ExcludedNames
}
Write-JsonUtf8NoBom $manifest (Join-Path $InstallRoot "install_manifest.json")
Write-InstallLog "Install complete. Embedded runtime and native desktop validated."
Write-Host "ANN installed to $InstallRoot"
