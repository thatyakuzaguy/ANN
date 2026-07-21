from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_network.project_builder_orchestrator.lifecycle_evidence import (
    REQUIRED_ALGORITHM_VERIFICATION_STEPS,
    REQUIRED_LIVE_VERIFICATION_STEPS,
    compile_lifecycle_evidence,
    write_lifecycle_capability_summary,
)


def _write_result(root: Path, *, failed_step: str = "") -> Path:
    commands = {
        "api_dependency_audit_live": ["docker", "compose", "run", "api", "pip-audit"],
        "api_dependency_integrity_live": ["docker", "compose", "run", "api", "pip", "check"],
        "api_pytest_live": ["docker", "compose", "run", "api", "pytest", "-q"],
        "docker_compose_build": ["docker", "compose", "build"],
        "docker_compose_up": ["docker", "compose", "up", "-d"],
        "web_build_live": ["docker", "compose", "exec", "web", "npm", "run", "build"],
        "web_dependency_audit_live": ["docker", "compose", "exec", "web", "npm", "audit"],
        "web_e2e_live": ["docker", "compose", "run", "e2e", "playwright", "test"],
        "web_unit_live": ["docker", "compose", "exec", "web", "npm", "test"],
    }
    steps = [
        {
            "name": name,
            "status": "failed" if name == failed_step else "passed",
            "detail": f"captured output for {name}",
            "command": commands.get(name),
        }
        for name in sorted(REQUIRED_LIVE_VERIFICATION_STEPS)
    ]
    steps.append(
        {
            "name": "security_review",
            "status": "passed",
            "detail": json.dumps({"passed": True, "findings": [], "notes": ["reviewed"]}),
            "command": None,
        }
    )
    result_path = root / ".aen" / "real-lifecycle-result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps({"status": "failed" if failed_step else "passed", "steps": steps}), encoding="utf-8"
    )
    screenshot = root / "apps" / "web" / "test-results" / "smoke" / "test-finished-1.png"
    screenshot.parent.mkdir(parents=True)
    screenshot.write_bytes(b"valid-e2e-screenshot" * 20)
    return result_path


def test_compiles_real_lifecycle_result_into_capability_evidence(tmp_path: Path) -> None:
    result_path = _write_result(tmp_path)

    result = compile_lifecycle_evidence(tmp_path, result_path)

    assert result["status"] == "PASSED"
    assert result["verification"]["status"] == "PASSED"
    assert result["security"]["status"] == "PASSED"
    assert result["functional_smoke"]["status"] == "PASSED"
    assert result["functional_smoke"]["screenshots"]
    assert all(Path(path).is_file() for path in result["artifacts"])
    assert all(Path(path).is_file() for path in result["verification"]["stdout_artifacts"])


def test_failed_lifecycle_step_can_never_compile_as_passed(tmp_path: Path) -> None:
    result_path = _write_result(tmp_path, failed_step="api_pytest_live")

    result = compile_lifecycle_evidence(tmp_path, result_path)

    assert result["status"] == "FAILED"
    assert result["verification"]["status"] == "FAILED"
    assert result["functional_smoke"]["status"] == "FAILED"
    assert 1 in result["verification"]["exit_codes"]


def test_missing_visual_artifact_fails_functional_evidence(tmp_path: Path) -> None:
    result_path = _write_result(tmp_path)
    for screenshot in tmp_path.rglob("*.png"):
        screenshot.unlink()

    result = compile_lifecycle_evidence(tmp_path, result_path)

    assert result["status"] == "FAILED"
    assert result["verification"]["status"] == "PASSED"
    assert result["functional_smoke"]["status"] == "FAILED"


def test_evidence_compiler_rejects_output_path_traversal(tmp_path: Path) -> None:
    result_path = _write_result(tmp_path)

    with pytest.raises(ValueError, match="must stay inside project root"):
        compile_lifecycle_evidence(tmp_path, result_path, tmp_path.parent / "escaped-evidence")


def test_summary_writer_never_marks_failed_lifecycle_verified(tmp_path: Path) -> None:
    project = tmp_path / "workspace" / "project"
    result_path = _write_result(project, failed_step="web_e2e_live")

    summary = write_lifecycle_capability_summary(
        "ecommerce_marketplace",
        project,
        tmp_path / "summaries" / "ecommerce_marketplace",
        allowed_workspace_root=tmp_path / "workspace",
        lifecycle_result_path=result_path,
    )

    assert summary["status"] == "BLOCKED"
    assert summary["completion_quality"] == "UNVERIFIED"
    assert summary["capability_assessment"]["passed"] is False


def test_summary_writer_rejects_project_outside_allowed_workspace(tmp_path: Path) -> None:
    project = tmp_path / "outside"
    result_path = _write_result(project)

    with pytest.raises(ValueError, match="must stay inside project root"):
        write_lifecycle_capability_summary(
            "ecommerce_marketplace",
            project,
            tmp_path / "summaries" / "ecommerce_marketplace",
            allowed_workspace_root=tmp_path / "allowed",
            lifecycle_result_path=result_path,
        )


def test_algorithm_evidence_requires_benchmark_but_not_visual_artifacts(tmp_path: Path) -> None:
    commands = {
        "algorithm_benchmark_live": ["docker", "compose", "run", "api", "python", "benchmark.py"],
        "algorithm_integration_live": ["docker", "compose", "run", "api", "pytest", "tests/test_integration.py"],
        "api_dependency_audit_live": ["docker", "compose", "run", "api", "pip-audit"],
        "api_dependency_integrity_live": ["docker", "compose", "run", "api", "pip", "check"],
        "api_pytest_live": ["docker", "compose", "run", "api", "pytest", "-q"],
        "docker_compose_build": ["docker", "compose", "build"],
        "docker_compose_up": ["docker", "compose", "up", "api"],
    }
    steps = [
        {"name": name, "status": "passed", "detail": f"output {name}", "command": commands.get(name)}
        for name in sorted(REQUIRED_ALGORITHM_VERIFICATION_STEPS)
    ]
    steps.append(
        {
            "name": "security_review",
            "status": "passed",
            "detail": json.dumps({"passed": True, "findings": [], "notes": []}),
            "command": None,
        }
    )
    result_path = tmp_path / ".aen" / "real-lifecycle-result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(json.dumps({"status": "passed", "profile": "algorithm_service", "steps": steps}))

    result = compile_lifecycle_evidence(tmp_path, result_path)

    assert result["status"] == "PASSED"
    assert result["functional_smoke"]["status"] == "PASSED"
    assert result["functional_smoke"]["screenshots"] == []
