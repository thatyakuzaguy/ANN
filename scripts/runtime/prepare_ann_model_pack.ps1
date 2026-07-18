param(
  [string]$OutputRoot = "D:\AgenticEngineeringNetwork\outputs\release_final\model_pack",
  [string]$Qwen25Path = "D:\AgenticEngineeringNetwork\models\qwen2.5-coder-7b-q4_k_m.gguf",
  [string]$Qwen34BPath = "D:\Models\qwen3-4b-instruct-2507-q4_k_m.gguf",
  [string]$Qwen38BPath = "D:\Models\qwen3_gguf\Qwen3-8B-Q4_K_M.gguf",
  [string]$DeepSeek14BPath = "D:\Models\deepseek\DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
  [ValidateSet("Copy", "HardLink")]
  [string]$Mode = "HardLink"
)

$ErrorActionPreference = "Stop"

function Resolve-SafeLocalPath {
  param([string]$PathValue, [string]$Label, [switch]$RequireFile)
  $full = [System.IO.Path]::GetFullPath($PathValue)
  $drive = [System.IO.Path]::GetPathRoot($full).TrimEnd('\')
  if ($drive -ieq "C:") { throw "$Label on C:\ is blocked." }
  if ($drive -notin @("D:", "E:")) { throw "$Label must be on D: or E:." }
  if ($full -split '[\\/]' -contains '..') { throw "$Label contains path traversal." }
  if ($RequireFile -and -not (Test-Path -LiteralPath $full -PathType Leaf)) {
    throw "$Label missing: $full"
  }
  return $full.TrimEnd('\')
}

$OutputRoot = Resolve-SafeLocalPath $OutputRoot "Output root"
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$declared = @(
  @{ name = "qwen2.5-coder-7b-q4_k_m.gguf"; source = $Qwen25Path; model_id = "qwen2_5_coder_7b_v5" },
  @{ name = "qwen3-4b-instruct-2507-q4_k_m.gguf"; source = $Qwen34BPath; model_id = "qwen3_4b_conversation_orchestrator" },
  @{ name = "Qwen3-8B-Q4_K_M.gguf"; source = $Qwen38BPath; model_id = "qwen3_8b_product_v9_repaired_v2_bullets" },
  @{ name = "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf"; source = $DeepSeek14BPath; model_id = "deepseek_r1_distill_qwen_14b" }
)

$files = @()
$totalSize = [int64]0
foreach ($entry in $declared) {
  $source = Resolve-SafeLocalPath $entry.source "Model $($entry.model_id)" -RequireFile
  $target = Join-Path $OutputRoot $entry.name
  if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Force }
  if ($Mode -eq "HardLink") {
    New-Item -ItemType HardLink -Path $target -Target $source | Out-Null
  } else {
    Copy-Item -LiteralPath $source -Destination $target -Force
  }
  $file = Get-Item -LiteralPath $target
  $totalSize += [int64]$file.Length
  $files += [ordered]@{
    model_id = $entry.model_id
    relative_path = $entry.name
    size_bytes = [int64]$file.Length
    sha256 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}

$manifest = [ordered]@{
  schema_version = "1.0"
  created_at = (Get-Date -Format o)
  mode = $Mode
  redistribution_authorized = $false
  redistribution_note = "Verify every upstream model license and provenance before publishing this local pack."
  active_models = 0
  parallel_llm_loads = 0
  files = $files
  total_size_bytes = $totalSize
}
$manifestPath = Join-Path $OutputRoot "MODEL_PACK_MANIFEST.json"
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 6), $encoding)
Write-Host "ANN local model pack prepared: $manifestPath"
