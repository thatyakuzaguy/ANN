"""Reproducible Build Verification built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Reproducible Build Verification action."""

    return execute_engineering_action("reproducible_build_verification", action, payload, Path(workspace).resolve())
