"""Browser/E2E built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Browser/E2E action."""

    return execute_engineering_action("browser_e2e", action, payload, Path(workspace).resolve())
