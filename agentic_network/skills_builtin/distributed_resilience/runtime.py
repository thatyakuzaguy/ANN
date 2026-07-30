"""Distributed Resilience built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Distributed Resilience action."""

    return execute_engineering_action("distributed_resilience", action, payload, Path(workspace).resolve())
