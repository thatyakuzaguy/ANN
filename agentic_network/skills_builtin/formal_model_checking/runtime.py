"""Formal Model Checking built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Formal Model Checking action."""

    return execute_engineering_action("formal_model_checking", action, payload, Path(workspace).resolve())
