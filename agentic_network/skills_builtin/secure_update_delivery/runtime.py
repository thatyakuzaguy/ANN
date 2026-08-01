"""Secure Update Delivery built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Secure Update Delivery action."""

    return execute_engineering_action("secure_update_delivery", action, payload, Path(workspace).resolve())
