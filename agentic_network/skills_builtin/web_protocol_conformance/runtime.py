"""Web Protocol Conformance built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Web Protocol Conformance action."""

    return execute_engineering_action("web_protocol_conformance", action, payload, Path(workspace).resolve())
