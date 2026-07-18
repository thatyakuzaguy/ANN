from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path("D:/AgenticEngineeringNetwork")
HOST_SCRIPT = REPO_ROOT / "scripts" / "release" / "invoke-windows-sandbox-validation.ps1"
SANDBOX_SCRIPT = REPO_ROOT / "scripts" / "release" / "run-windows-sandbox-validation.ps1"


def test_windows_sandbox_host_harness_is_safe_and_approval_explicit() -> None:
    source = HOST_SCRIPT.read_text(encoding="utf-8")

    assert "[switch]$Launch" in source
    assert "if (-not $Launch)" in source
    assert "WINDOWS_SANDBOX_VALIDATION_BLOCKED" in source
    assert "Get-AuthenticodeSignature" in source
    assert 'setup_signature_not_valid' in source
    assert 'uninstall_signature_not_valid' in source
    assert 'signing_evidence_missing' in source
    assert 'release_transfer_manifest_missing' in source
    assert 'windows_sandbox_not_enabled' in source
    assert "Start-Process -FilePath $configPath" in source


def test_windows_sandbox_configuration_disables_network_and_host_input_writes() -> None:
    source = HOST_SCRIPT.read_text(encoding="utf-8")

    assert "<Networking>Disable</Networking>" in source
    assert "<VGpu>Disable</VGpu>" in source
    assert "<ClipboardRedirection>Disable</ClipboardRedirection>" in source
    assert source.count("<ReadOnly>true</ReadOnly>") == 6
    assert source.count("<ReadOnly>false</ReadOnly>") == 1
    assert "C:\\ANNWork\\sources\\harness\\run-windows-sandbox-validation.ps1" in source


def test_windows_sandbox_bootstrap_reuses_strict_clean_machine_gate() -> None:
    source = SANDBOX_SCRIPT.read_text(encoding="utf-8")

    assert "subst.exe D:" in source
    assert '$substCreated = $false' in source
    assert "if ($substCreated)" in source
    assert 'D:\\sources\\installer\\ANN_Setup.exe' in source
    assert '-SourceRoot "D:\\sources\\source"' in source
    assert '-RuntimeSource "D:\\sources\\runtime"' in source
    assert '-DesktopSource "D:\\sources\\desktop"' in source
    assert '-InstallRoot "D:\\ANN"' in source
    assert "ANN_Setup.exe did not produce a fresh installation manifest" in source
    assert "-EnvironmentType clean_machine" in source
    assert "-RequireSignedInstaller" in source
    assert "release_signing_evidence.json" in source
    assert "RELEASE_TRANSFER_MANIFEST.json" in source
    assert "clean_machine_external_validation.json" in source
    assert 'status = "PASSED"' in source
    assert 'environment = "windows_sandbox"' in source


def test_windows_sandbox_validates_a_fresh_install_not_a_preinstalled_tree() -> None:
    host = HOST_SCRIPT.read_text(encoding="utf-8")
    sandbox = SANDBOX_SCRIPT.read_text(encoding="utf-8")

    assert "[string]$SourceRoot" in host
    assert "[string]$RuntimeSource" in host
    assert "[string]$DesktopSource" in host
    assert "installed_root_missing" not in host
    assert "C:\\ANNMapped\\ANN" not in sandbox
    assert "setup_executed = $true" in sandbox


@pytest.mark.parametrize("script", [HOST_SCRIPT, SANDBOX_SCRIPT])
def test_windows_sandbox_scripts_parse(script: Path) -> None:
    powershell = shutil.which("powershell.exe") or shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell parser is unavailable")
    command = (
        "$tokens=$null;$errors=$null;"
        "[System.Management.Automation.Language.Parser]::ParseFile("
        f"'{script}',[ref]$tokens,[ref]$errors)|Out-Null;"
        "if($errors.Count){$errors|ForEach-Object{$_.Message};exit 1}"
    )

    result = subprocess.run(
        [powershell, "-NoProfile", "-Command", command],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_windows_sandbox_harness_never_downloads_or_runs_models() -> None:
    combined = "\n".join(
        [HOST_SCRIPT.read_text(encoding="utf-8"), SANDBOX_SCRIPT.read_text(encoding="utf-8")]
    ).lower()

    assert "invoke-webrequest" not in combined
    assert "start-bitstransfer" not in combined
    assert "pip install" not in combined
    assert "npm install" not in combined
    assert "model load" not in combined
    assert "inference" in combined
    assert "no_model_load = $true" in combined
    assert "no_inference = $true" in combined
