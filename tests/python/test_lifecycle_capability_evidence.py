from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from agentic_network.project_builder_orchestrator.lifecycle_evidence import (
    REQUIRED_ALGORITHM_VERIFICATION_STEPS,
    REQUIRED_LIVE_VERIFICATION_STEPS,
    build_capability_evidence_manifest,
    compile_lifecycle_evidence,
    make_capability_evidence_portable,
    write_capability_evidence_manifest,
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


def test_skipped_optional_recipe_is_not_reported_as_an_executed_failure(tmp_path: Path) -> None:
    result_path = _write_result(tmp_path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["steps"].append(
        {
            "name": "docker_compose_remove_sandbox_images",
            "status": "skipped",
            "detail": "Optional image cleanup was not executed.",
            "command": ["docker", "compose", "down", "--rmi", "local"],
        }
    )
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    result = compile_lifecycle_evidence(tmp_path, result_path)

    assert result["status"] == "PASSED"
    assert ["docker", "compose", "down", "--rmi", "local"] not in result["verification"][
        "commands_executed"
    ]
    assert all(code == 0 for code in result["verification"]["exit_codes"])


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


def test_portable_summary_resolves_project_logs_and_screenshots_relative_to_summary(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    project = workspace / "project"
    result_path = _write_result(project)
    (project / "src").mkdir()
    (project / "tests").mkdir(exist_ok=True)
    keywords = "tenant organization account contact deal pipeline role permission jwt auth"
    for index in range(8):
        (project / "src" / f"module_{index}.ts").write_text(
            "\n".join(f"export const crm{index}_{line} = '{keywords}';" for line in range(40)),
            encoding="utf-8",
        )
    for index in range(3):
        (project / "tests" / f"module_{index}.test.ts").write_text(
            "test('works', () => expect(true).toBe(true));\n",
            encoding="utf-8",
        )
    summary_path = tmp_path / "evidence" / "crm_saas_multitenant" / "summary.json"
    summary_path.parent.mkdir(parents=True)
    write_lifecycle_capability_summary(
        "crm_saas_multitenant",
        project,
        summary_path.parent,
        allowed_workspace_root=workspace,
        lifecycle_result_path=result_path,
    )
    packet_project = tmp_path / "evidence" / "projects" / "crm_saas_multitenant"
    shutil.copytree(project, packet_project)
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["project_root"] = str(packet_project)
    payload["generated_project_path"] = str(packet_project)
    payload["artifacts"] = [
        str(packet_project / Path(path).resolve().relative_to(project.resolve()))
        for path in payload["artifacts"]
    ]
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    summary_path.with_suffix(".md").write_text(
        f"# stale\n\n- Project root: {project}\n",
        encoding="utf-8",
    )

    portable = make_capability_evidence_portable(summary_path)

    assert portable["portable_paths"] is True
    assert not Path(portable["project_root"]).is_absolute()
    assert all(not Path(path).is_absolute() for path in portable["artifacts"])
    assert portable["capability_assessment"]["passed"] is True, portable[
        "capability_assessment"
    ]
    assert not Path(portable["capability_assessment"]["project_root"]).is_absolute()
    assert str(project) not in summary_path.with_suffix(".md").read_text(encoding="utf-8")

    from agentic_network.project_builder_orchestrator.capability_evidence import evaluate_project_capability

    reevaluated = evaluate_project_capability(
        "crm_saas_multitenant",
        json.loads(summary_path.read_text(encoding="utf-8")),
        summary_path=summary_path,
    )
    assert reevaluated["passed"] is True


def test_portable_evidence_manifest_is_deterministic_and_detects_tampering(tmp_path: Path) -> None:
    scenario = tmp_path / "crm_saas_multitenant"
    scenario.mkdir()
    summary = {
        "scenario_id": "crm_saas_multitenant",
        "status": "COMPLETED_VERIFIED",
        "completion_quality": "VERIFIED",
        "portable_paths": True,
        "capability_assessment": {"passed": True},
    }
    (scenario / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    project = tmp_path / "projects" / "crm_saas_multitenant"
    project.mkdir(parents=True)
    source = project / "app.py"
    source.write_text("print('verified')\n", encoding="utf-8")

    first = build_capability_evidence_manifest(tmp_path)
    second = build_capability_evidence_manifest(tmp_path)

    assert first["status"] == "PORTABLE_EVIDENCE_BLOCKED"
    assert first["aggregate_sha256"] == second["aggregate_sha256"]
    assert first["scenario_count"] == 1
    source.write_text("print('tampered')\n", encoding="utf-8")
    tampered = build_capability_evidence_manifest(tmp_path)
    assert tampered["aggregate_sha256"] != first["aggregate_sha256"]


def test_portable_evidence_manifest_sidecar_hashes_actual_manifest(tmp_path: Path) -> None:
    scenario = tmp_path / "complex_algorithm_service"
    scenario.mkdir()
    (scenario / "summary.json").write_text(
        json.dumps(
            {
                "scenario_id": "complex_algorithm_service",
                "status": "COMPLETED_VERIFIED",
                "completion_quality": "VERIFIED",
                "portable_paths": True,
                "capability_assessment": {"passed": True},
            }
        ),
        encoding="utf-8",
    )

    result = write_capability_evidence_manifest(tmp_path)
    manifest_path = tmp_path / "EVIDENCE_MANIFEST.json"
    actual = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    assert result["manifest_sha256"] == actual
    assert (tmp_path / "EVIDENCE_MANIFEST.sha256").read_text(encoding="utf-8") == (
        f"{actual}  EVIDENCE_MANIFEST.json\n"
    )
    assert "PORTABLE_EVIDENCE_BLOCKED" in (tmp_path / "EVIDENCE_MANIFEST.md").read_text(encoding="utf-8")


def test_portable_manifest_recomputes_assessment_and_rejects_external_paths(
    tmp_path: Path,
) -> None:
    external = tmp_path.parent / "external-project"
    external.mkdir(exist_ok=True)
    scenario = tmp_path / "crm_saas_multitenant"
    scenario.mkdir()
    (scenario / "summary.json").write_text(
        json.dumps(
            {
                "scenario_id": "crm_saas_multitenant",
                "status": "COMPLETED_VERIFIED",
                "completion_quality": "VERIFIED",
                "portable_paths": True,
                "project_root": str(external),
                "artifacts": [],
                "capability_assessment": {"passed": True},
            }
        ),
        encoding="utf-8",
    )

    manifest = build_capability_evidence_manifest(tmp_path)

    assert manifest["status"] == "PORTABLE_EVIDENCE_BLOCKED"
    assert manifest["scenarios"][0]["capability_passed"] is False


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
