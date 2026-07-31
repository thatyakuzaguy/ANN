"""Coverage Guided Test Synthesis built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Coverage Guided Test Synthesis action."""

    return execute_engineering_action("coverage_guided_test_synthesis", action, payload, Path(workspace).resolve())
