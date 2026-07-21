from __future__ import annotations

import json
from pathlib import Path

from agentic_network.runtime_engine.loader import get_loaded_models, get_runtime_metrics
from agentic_network.runtime_engine.local_model_activation import (
    build_controlled_first_inference_gate,
    write_controlled_first_inference_gate_artifacts,
    write_runtime_readiness_macro_artifacts,
)


def test_controlled_first_inference_gate_blocked_no_load_no_inference() -> None:
    before = get_loaded_models()
    gate = build_controlled_first_inference_gate()
    blockers = {item["id"] for item in gate["checks"] if item["status"] == "BLOCKED"}
    checks = {item["id"]: item for item in gate["checks"]}

    assert gate["status"] == "NOT_READY"
    assert blockers.intersection({"qwen25_backend", "launch_guard"})
    for check_id in {"wheelhouse", "runtime_integrity"}:
        assert (check_id in blockers) is (checks[check_id]["status"] == "BLOCKED")
    assert gate["model_load_attempted"] is False
    assert gate["real_inference_attempted"] is False
    assert gate["qwen3_blocked"] is True
    assert gate["deepseek_blocked"] is True
    assert gate["powerful_blocked"] is True
    assert get_loaded_models() == before == []
    assert get_runtime_metrics().get("parallel_llm_loads", 0) == 0


def test_controlled_first_inference_gate_artifacts(tmp_path: Path) -> None:
    artifacts = write_controlled_first_inference_gate_artifacts(tmp_path)
    names = {Path(path).name for path in artifacts}

    assert names == {"208_controlled_first_inference_gate.json", "209_controlled_first_inference_gate.md"}
    payload = json.loads((tmp_path / "208_controlled_first_inference_gate.json").read_text(encoding="utf-8"))
    assert payload["version"] == "16.8"


def test_runtime_readiness_macro_artifacts(tmp_path: Path) -> None:
    artifacts = write_runtime_readiness_macro_artifacts(tmp_path)
    names = {Path(path).name for path in artifacts}

    assert {
        "204_post_materialization_validator.json",
        "205_post_materialization_validator.md",
        "206_runtime_readiness_evidence.json",
        "207_runtime_readiness_evidence.md",
        "208_controlled_first_inference_gate.json",
        "209_controlled_first_inference_gate.md",
    } == names
