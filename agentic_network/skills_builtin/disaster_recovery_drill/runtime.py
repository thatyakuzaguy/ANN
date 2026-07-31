"""Disaster Recovery Drill built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Disaster Recovery Drill action."""

    return execute_engineering_action("disaster_recovery_drill", action, payload, Path(workspace).resolve())
