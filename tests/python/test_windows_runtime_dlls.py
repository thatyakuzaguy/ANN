from __future__ import annotations

import os
from pathlib import Path

from agentic_network.runtime_engine import windows_dlls


def test_configures_bundled_nvidia_and_llama_dll_directories(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cuda_bin = tmp_path / "Lib" / "site-packages" / "nvidia" / "cuda_runtime" / "bin"
    llama_lib = tmp_path / "Lib" / "site-packages" / "llama_cpp" / "lib"
    cuda_bin.mkdir(parents=True)
    llama_lib.mkdir(parents=True)
    registered: list[str] = []

    class Handle:
        pass

    monkeypatch.setattr(os, "add_dll_directory", lambda path: registered.append(path) or Handle(), raising=False)
    monkeypatch.setenv("PATH", "existing")
    windows_dlls._DLL_DIRECTORY_HANDLES.clear()

    configured = windows_dlls.configure_windows_runtime_dll_paths(tmp_path, force=True)

    assert configured == [str(cuda_bin.resolve()), str(llama_lib.resolve())]
    assert registered == configured
    assert os.environ["PATH"].split(os.pathsep)[:2] == configured


def test_configuration_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    cuda_bin = tmp_path / "Lib" / "site-packages" / "nvidia" / "cublas" / "bin"
    cuda_bin.mkdir(parents=True)
    registered: list[str] = []
    monkeypatch.setattr(
        os,
        "add_dll_directory",
        lambda path: registered.append(path) or object(),
        raising=False,
    )
    monkeypatch.setenv("PATH", "")
    windows_dlls._DLL_DIRECTORY_HANDLES.clear()

    first = windows_dlls.configure_windows_runtime_dll_paths(tmp_path, force=True)
    second = windows_dlls.configure_windows_runtime_dll_paths(tmp_path, force=True)

    assert first == second == [str(cuda_bin.resolve())]
    assert registered == first


def test_non_windows_runtime_is_unchanged_without_force(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(windows_dlls.os, "name", "posix")
    original_path = os.environ.get("PATH", "")

    assert windows_dlls.configure_windows_runtime_dll_paths(tmp_path) == []
    assert os.environ.get("PATH", "") == original_path
