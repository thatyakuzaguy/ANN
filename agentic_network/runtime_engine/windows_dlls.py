"""Windows native-library discovery for ANN's embedded model runtime."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


_DLL_DIRECTORY_HANDLES: dict[str, Any] = {}


def configure_windows_runtime_dll_paths(
    python_prefix: str | Path | None = None,
    *,
    force: bool = False,
) -> list[str]:
    """Expose bundled CUDA and llama.cpp DLL directories to the current process.

    Python 3.8+ no longer resolves extension-module dependencies from ``PATH``
    alone in every import path. ANN therefore registers each verified bundled
    directory with ``os.add_dll_directory`` and retains the returned handles for
    the lifetime of the process. The operation is local, idempotent, and never
    installs or downloads anything.
    """

    if os.name != "nt" and not force:
        return []

    prefix = Path(python_prefix or sys.prefix)
    site_packages = prefix / "Lib" / "site-packages"
    candidates = _runtime_dll_candidates(site_packages)
    existing = [path.resolve() for path in candidates if path.is_dir()]
    if not existing:
        return []

    add_dll_directory = getattr(os, "add_dll_directory", None)
    for path in existing:
        key = str(path).casefold()
        if callable(add_dll_directory) and key not in _DLL_DIRECTORY_HANDLES:
            _DLL_DIRECTORY_HANDLES[key] = add_dll_directory(str(path))

    current_path = [part for part in os.environ.get("PATH", "").split(os.pathsep) if part]
    known = {part.casefold() for part in current_path}
    additions = [str(path) for path in existing if str(path).casefold() not in known]
    if additions:
        os.environ["PATH"] = os.pathsep.join([*additions, *current_path])
    return [str(path) for path in existing]


def _runtime_dll_candidates(site_packages: Path) -> list[Path]:
    nvidia_root = site_packages / "nvidia"
    candidates: list[Path] = []
    if nvidia_root.is_dir():
        candidates.extend(sorted(path for path in nvidia_root.glob("*/bin") if path.is_dir()))
    candidates.append(site_packages / "llama_cpp" / "lib")
    return candidates
