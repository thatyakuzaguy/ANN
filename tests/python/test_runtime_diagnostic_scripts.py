from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_ann_runtime_backend_diagnostic_runs_without_pythonpath() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/runtime/check_ann_runtime_backend.py"],
        cwd=ROOT,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": ""},
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["script"] == "check_ann_runtime_backend"
    assert payload["read_only"] is True
    assert payload["model_load"] is False


def test_gpu_verifier_is_checkout_relative_and_never_pulls() -> None:
    source = (ROOT / "scripts" / "setup" / "verify-gpu.ps1").read_text(encoding="utf-8")

    assert "$PSScriptRoot" in source
    assert 'Root = "D:\\AgenticEngineeringNetwork"' not in source
    assert "--pull=never" in source
    assert source.count("$LASTEXITCODE") >= 4
    assert "docker compose exec -T api" in source
