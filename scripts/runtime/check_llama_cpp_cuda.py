"""Read-only llama.cpp Python binding check for ANN.

This script never instantiates Llama and never loads a GGUF file. It only
checks importability, metadata, and the declared Qwen2.5 model path.
"""

from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
from pathlib import PureWindowsPath
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentic_network.models.gpu_policy import llama_cpp_supports_gpu_offload  # noqa: E402
from agentic_network.models.llama_cpp_security import load_secure_llama_cpp  # noqa: E402
from agentic_network.runtime_engine.windows_dlls import (  # noqa: E402
    configure_windows_runtime_dll_paths,
)
from scripts.runtime.run_conversation_llama_cpp import (  # noqa: E402
    _prepare_cuda_library_path,
    _preload_cuda_libraries,
)


QWEN25_GGUF = Path("D:/AgenticEngineeringNetwork/models/qwen2.5-coder-7b-q4_k_m.gguf")


def _resolve_declared_path(path: Path) -> Path:
    if os.name == "nt":
        return path
    windows_path = PureWindowsPath(str(path))
    if windows_path.drive and windows_path.drive[0].isalpha():
        relative = "/".join(windows_path.parts[1:])
        return Path(f"/mnt/{windows_path.drive[0].lower()}/{relative}")
    return path


def main() -> None:
    qwen25_path = _resolve_declared_path(QWEN25_GGUF)
    payload = {
        "script": "check_llama_cpp_cuda",
        "read_only": True,
        "installs": False,
        "downloads": False,
        "model_load": False,
        "qwen25_gguf_path": str(QWEN25_GGUF),
        "qwen25_gguf_resolved_path": str(qwen25_path),
        "qwen25_gguf_exists": qwen25_path.is_file(),
    }
    configured_dll_paths = configure_windows_runtime_dll_paths()
    payload["configured_dll_paths"] = configured_dll_paths
    try:
        _prepare_cuda_library_path()
        _preload_cuda_libraries()
        llama_cpp = load_secure_llama_cpp()

        try:
            version = importlib.metadata.version("llama-cpp-python")
        except importlib.metadata.PackageNotFoundError:
            version = None
        payload.update(
            {
                "status": "available",
                "llama_cpp_importable": True,
                "llama_cpp_version": version,
                "llama_class_available": hasattr(llama_cpp, "Llama"),
                "gpu_offload_metadata": llama_cpp_supports_gpu_offload(llama_cpp),
                "persistent_disk_cache_enabled": False,
            }
        )
    except Exception as exc:  # pragma: no cover - depends on optional runtime.
        payload.update(
            {
                "status": "unavailable",
                "llama_cpp_importable": False,
                "llama_class_available": False,
                "error": f"{type(exc).__name__}:{exc}",
            }
        )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
