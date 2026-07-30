"""Synthetic Test Data built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Synthetic Test Data action."""

    return execute_engineering_action("synthetic_test_data", action, payload, Path(workspace).resolve())
