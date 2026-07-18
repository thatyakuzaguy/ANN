from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from agentic_network.runtime_engine import local_model_activation
from agentic_network.runtime_engine.local_model_activation import (
    build_embedded_runtime_installer_readiness,
    write_embedded_runtime_installer_readiness_artifacts,
)


def test_embedded_import_probe_configures_dlls_before_llama_cpp(
    monkeypatch,
    tmp_path: Path,
) -> None:
    python_exe = tmp_path / "python.exe"
    python_exe.touch()
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "packages": {
                        "llama_cpp": {
                            "importable": True,
                            "version": "0.3.32",
                            "error": "",
                        }
                    }
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(local_model_activation.subprocess, "run", fake_run)

    result = local_model_activation._run_embedded_runtime_import_probe(
        python_exe,
        ("llama_cpp",),
        15,
    )

    assert result["status"] == "PASSED"
    script = captured["command"][2]
    assert "configure_windows_runtime_dll_paths()" in script
    assert script.index("configure_windows_runtime_dll_paths()") < script.index(
        "module = importlib.import_module(name)"
    )


def test_embedded_runtime_installer_readiness_detects_missing_embedded_python() -> None:
    readiness = build_embedded_runtime_installer_readiness()

    assert readiness["status"] in {"READY", "EMBEDDED_RUNTIME_MISSING"}
    assert readiness["expected_paths"]["embedded_python"] == "D:\\ANN\\runtime\\python\\python.exe"
    assert readiness["no_dependency_download_in_installer"] is True
    assert readiness["no_model_movement"] is True
    assert "projects" in readiness["preserve"]
    assert any(check["id"] == "embedded_python" for check in readiness["checks"])


def test_embedded_runtime_installer_readiness_artifacts(tmp_path: Path) -> None:
    artifacts = write_embedded_runtime_installer_readiness_artifacts(tmp_path)
    names = {Path(path).name for path in artifacts}

    assert names == {
        "142_embedded_runtime_installer_readiness.json",
        "143_embedded_runtime_installer_readiness.md",
    }
    payload = json.loads((tmp_path / "142_embedded_runtime_installer_readiness.json").read_text(encoding="utf-8"))
    assert payload["version"] == "14.3"
