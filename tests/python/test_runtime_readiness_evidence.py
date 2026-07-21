from __future__ import annotations

import json
from pathlib import Path

from agentic_network.runtime_engine.local_model_activation import (
    build_runtime_readiness_evidence,
    write_runtime_readiness_evidence_artifacts,
)


def test_runtime_readiness_evidence_blocked() -> None:
    evidence = build_runtime_readiness_evidence()
    blockers = {item["id"] for item in evidence["blockers"]}
    checks = {item["id"]: item for item in evidence["checks"]}

    assert evidence["status"] in {"NOT_READY", "PARTIAL"}
    for check_id in {"runtime_ready", "wheelhouse_verified", "embedded_python_detected"}:
        assert (check_id in blockers) is (checks[check_id]["status"] == "BLOCKED")
    assert "launch_guard_ready" in blockers
    assert evidence["safe_rollback_ready"] is True
    assert evidence["warnings"]
    assert evidence["next_manual_step"]


def test_runtime_readiness_evidence_artifacts(tmp_path: Path) -> None:
    artifacts = write_runtime_readiness_evidence_artifacts(tmp_path)
    names = {Path(path).name for path in artifacts}

    assert names == {"206_runtime_readiness_evidence.json", "207_runtime_readiness_evidence.md"}
    payload = json.loads((tmp_path / "206_runtime_readiness_evidence.json").read_text(encoding="utf-8"))
    assert payload["version"] == "16.7"
