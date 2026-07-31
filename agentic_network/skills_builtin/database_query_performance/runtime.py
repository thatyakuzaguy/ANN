"""Database Query Performance built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Database Query Performance action."""

    return execute_engineering_action("database_query_performance", action, payload, Path(workspace).resolve())
