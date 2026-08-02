from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def test_release_and_operator_powershell_scripts_parse() -> None:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        pytest.skip("PowerShell parser is unavailable")

    scripts = sorted(
        [*ROOT.glob("*.ps1"), *ROOT.joinpath("installer").rglob("*.ps1"), *ROOT.joinpath("scripts").rglob("*.ps1")]
    )
    assert scripts

    command = (
        "$failures = @(); "
        "$paths = $env:ANN_POWERSHELL_PARSE_PATHS -split [IO.Path]::PathSeparator; "
        "foreach ($path in $paths) { "
        "$tokens = $null; $errors = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        "$path, [ref]$tokens, [ref]$errors) | Out-Null; "
        "foreach ($errorRecord in $errors) { "
        "$failures += \"${path}:$($errorRecord.Extent.StartLineNumber) "
        "$($errorRecord.Message)\" } }; "
        "if ($failures.Count -gt 0) { "
        "$failures | Write-Error; exit 1 }"
    )
    completed = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=ROOT,
        capture_output=True,
        env={**os.environ, "ANN_POWERSHELL_PARSE_PATHS": os.pathsep.join(map(str, scripts))},
        text=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
