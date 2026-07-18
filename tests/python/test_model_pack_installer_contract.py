from __future__ import annotations

from pathlib import Path


ROOT = Path("D:/AgenticEngineeringNetwork")


def test_model_pack_builder_declares_every_runtime_model() -> None:
    source = (ROOT / "scripts" / "runtime" / "prepare_ann_model_pack.ps1").read_text(encoding="utf-8")

    for filename in (
        "qwen2.5-coder-7b-q4_k_m.gguf",
        "qwen3-4b-instruct-2507-q4_k_m.gguf",
        "Qwen3-8B-Q4_K_M.gguf",
        "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
    ):
        assert filename in source
    assert "MODEL_PACK_MANIFEST.json" in source
    assert "Get-FileHash" in source


def test_installer_requires_verified_manifest_for_complete_model_install() -> None:
    source = (ROOT / "installer" / "install_ann.ps1").read_text(encoding="utf-8")

    assert "[switch]$RequireModels" in source
    assert "MODEL_PACK_MANIFEST.json" in source
    assert "Model SHA256 mismatch" in source
    assert "Model size mismatch" in source
    assert "Write-JsonUtf8NoBom" in source


def test_installer_does_not_exclude_python_model_memory_or_knowledge_modules() -> None:
    source = (ROOT / "installer" / "install_ann.ps1").read_text(encoding="utf-8")

    assert "$CodeExcludedNames" in source
    assert "(Join-Path $appSource $name) (Join-Path $InstallRoot $name) $CodeExcludedNames" in source


def test_model_pack_and_installer_have_no_network_or_dependency_install() -> None:
    combined = "\n".join(
        [
            (ROOT / "scripts" / "runtime" / "prepare_ann_model_pack.ps1").read_text(encoding="utf-8"),
            (ROOT / "installer" / "install_ann.ps1").read_text(encoding="utf-8"),
        ]
    ).lower()

    for forbidden in ("invoke-webrequest", "start-bitstransfer", "pip install", "npm install", "shell=true"):
        assert forbidden not in combined
