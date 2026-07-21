from __future__ import annotations

import json
from pathlib import Path

from agentic_network.runtime_engine.local_model_activation import (
    build_guided_runtime_activation_state,
    write_guided_runtime_activation_state_artifacts,
)


def test_guided_runtime_activation_state_blocked_when_runtime_missing() -> None:
    state = build_guided_runtime_activation_state()
    completed = [item["id"] for item in state["steps"] if item["status"] == "COMPLETED"]
    blocked = [item["id"] for item in state["steps"] if item["status"] == "BLOCKED"]

    expected_status = "GUIDED_PARTIAL" if completed else "GUIDED_BLOCKED"
    assert state["status"] == expected_status
    assert state["current_step"] == blocked[0]
    assert state["completed_steps"] == completed
    assert state["blocked_steps"] == blocked
    assert state["ready_for_smoke_button"] is False
    assert state["safe_mode"] is True
    assert state["qwen3_blocked"] is True
    assert state["deepseek_blocked"] is True
    assert state["powerful_blocked"] is True


def test_guided_runtime_activation_artifacts(tmp_path: Path) -> None:
    artifacts = write_guided_runtime_activation_state_artifacts(tmp_path)
    names = {Path(path).name for path in artifacts}

    assert names == {"218_guided_runtime_activation_state.json", "219_guided_runtime_activation_state.md"}
    payload = json.loads((tmp_path / "218_guided_runtime_activation_state.json").read_text(encoding="utf-8"))
    assert payload["version"] == "17.2"
