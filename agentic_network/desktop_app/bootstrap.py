"""Source-tree package bootstrap for ANN desktop entrypoints."""

from __future__ import annotations

import sys
from pathlib import Path


def bootstrap_local_package_paths() -> tuple[str, ...]:
    """Expose ANN monorepo packages to source and installed desktop launches."""

    root = Path(__file__).resolve().parents[2]
    candidates = (
        root,
        root / "packages" / "agents",
        root / "packages" / "orchestration",
        root / "packages" / "sandbox",
        root / "packages" / "git",
        root / "packages" / "logs",
        root / "packages" / "shared",
        root / "packages" / "database",
        root / "packages" / "security",
        root / "apps" / "api",
    )
    available = tuple(str(path) for path in candidates if path.is_dir())
    for package_path in reversed(available):
        if package_path not in sys.path:
            sys.path.insert(0, package_path)
    return available
