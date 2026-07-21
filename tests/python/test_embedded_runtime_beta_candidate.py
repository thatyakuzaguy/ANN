from __future__ import annotations

import json
from pathlib import Path

from agentic_network.runtime_engine.local_model_activation import (
    build_embedded_runtime_beta_candidate,
    write_beta_candidate_macro_artifacts,
    write_embedded_runtime_beta_candidate_artifacts,
)


def test_embedded_runtime_beta_candidate_ready_after_verified_runtime() -> None:
    candidate = build_embedded_runtime_beta_candidate()
    checks = {item["id"]: item for item in candidate["checks"]}

    assert candidate["status"] in {"BETA_CANDIDATE_READY", "BETA_CANDIDATE_BLOCKED"}
    assert candidate["beta_candidate"] is (candidate["status"] == "BETA_CANDIDATE_READY")
    assert candidate["embedded_python_present"] is checks["embedded_python_present"]["passed"]
    assert candidate["runtime_verified"] is checks["runtime_verified"]["passed"]
    assert candidate["installer_compatible"] is checks["installer_compatible"]["passed"]
    assert bool(candidate["blockers"]) is (candidate["status"] == "BETA_CANDIDATE_BLOCKED")
    assert candidate["no_install"] is True
    assert candidate["no_model_load"] is True


def test_embedded_runtime_beta_candidate_artifacts(tmp_path: Path) -> None:
    artifacts = write_embedded_runtime_beta_candidate_artifacts(tmp_path)
    names = {Path(path).name for path in artifacts}

    assert names == {"192_embedded_runtime_beta_candidate.json", "193_embedded_runtime_beta_candidate.md"}
    payload = json.loads((tmp_path / "192_embedded_runtime_beta_candidate.json").read_text(encoding="utf-8"))
    assert payload["version"] == "16.2"


def test_beta_candidate_macro_artifacts(tmp_path: Path) -> None:
    artifacts = write_beta_candidate_macro_artifacts(tmp_path)
    names = {Path(path).name for path in artifacts}

    assert {
        "188_external_runtime_materialization.json",
        "189_external_runtime_materialization.md",
        "190_wheelhouse_population_protocol.json",
        "191_wheelhouse_population_protocol.md",
        "192_embedded_runtime_beta_candidate.json",
        "193_embedded_runtime_beta_candidate.md",
        "194_first_real_inference_readiness.json",
        "195_first_real_inference_readiness.md",
    } == names
