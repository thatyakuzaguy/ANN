"""Binary Hardening Verification built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered Binary Hardening Verification action."""

    return execute_engineering_action("binary_hardening_verification", action, payload, Path(workspace).resolve())
