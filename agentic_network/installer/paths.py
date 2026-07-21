"""Path helpers for ANN installer foundation."""

from __future__ import annotations

import re
from pathlib import Path


DEFAULT_INSTALL_ROOT = Path("D:/ANN")
BLOCKED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "adapters",
    "datasets",
    "knowledge",
    "memory",
    "models",
    "node_modules",
    "outputs",
    "training",
    "unsloth_compiled_cache",
}


def get_default_install_root() -> Path:
    """Return the default Windows alpha install root."""

    return DEFAULT_INSTALL_ROOT


def normalize_install_path(path: str | Path) -> Path:
    """Normalize Windows and WSL-style install paths."""

    raw = str(path).strip()
    unix_like = raw.replace("\\", "/")
    match = re.match(r"^/?mnt/([A-Za-z])(?:/(.*))?$", unix_like)
    if match:
        drive = match.group(1).upper()
        rest = (match.group(2) or "").replace("/", "\\")
        raw = f"{drive}:\\{rest}" if rest else f"{drive}:\\"
    return Path(raw).expanduser().resolve()


def contains_traversal(path: str | Path) -> bool:
    """Return True when the raw path contains a traversal segment."""

    return any(part == ".." for part in str(path).replace("\\", "/").split("/"))


def is_c_drive(path: str | Path) -> bool:
    """Return True when a path targets C: or /mnt/c."""

    raw = str(path).replace("\\", "/").lower()
    normalized = normalize_install_path(path)
    return raw.startswith("c:/") or raw.startswith("/mnt/c/") or normalized.anchor.lower().startswith("c:")


def is_excluded_path(path: Path, source_root: Path) -> bool:
    """Return True when a source-relative path must not be copied."""

    try:
        # Installer inventory walks already-normalized descendants of source_root.
        # Keep that hot path lexical: resolving every file performs an expensive
        # Windows handle lookup and made a single read-only release gate take tens
        # of seconds on larger repositories.
        relative = path.relative_to(source_root)
    except ValueError:
        try:
            relative = path.resolve().relative_to(source_root.resolve())
        except ValueError:
            return True
    if path.is_symlink():
        try:
            path.resolve(strict=True).relative_to(source_root.resolve(strict=True))
        except (FileNotFoundError, OSError, ValueError):
            return True
    return any(part.lower() in BLOCKED_PARTS for part in relative.parts)


def is_relative_to(path: Path, parent: Path) -> bool:
    """Compatibility helper for Path.is_relative_to."""

    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
