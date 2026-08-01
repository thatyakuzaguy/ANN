"""Deterministic local runtimes for ANN engineering skills.

Every subprocess command is assembled by a named action in this module. User
payloads can select an action and bounded values, but can never provide a raw
command or opt into ``shell=True``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any
from urllib.parse import urlparse
import zipfile

from agentic_network.failure_context.runtime import (
    compile_failure_context,
    render_failure_context_markdown,
)
from agentic_network.installer.runtime import build_install_plan
from agentic_network.installer.validation import validate_install_plan
from agentic_network.project_patch_apply_agent.runtime import apply_project_patch
from agentic_network.project_test_runner_agent.runtime import detect_project_test_commands
from agentic_network.repository_intelligence_agent.runtime import build_repository_intelligence
from agentic_network.safety.filesystem_policy import load_filesystem_policy
from agentic_network.skills.sandbox import validate_workspace_path


PROTECTED_PARTS = {
    ".git",
    "adapters",
    "datasets",
    "knowledge",
    "memory",
    "models",
    "training",
    "unsloth_compiled_cache",
}
MAX_TIMEOUT = 600
MAX_CAPTURE = 80_000
MAX_SCAN_FILES = 5_000
COMMAND_META = re.compile(r"[;&|<>`]|\$\(")


@dataclass(frozen=True)
class RecipeResult:
    name: str
    status: str
    command: list[str]
    exit_code: int | None
    stdout_path: str
    stderr_path: str
    duration_seconds: float
    error: str = ""


def execute_engineering_action(
    skill_name: str,
    action: str,
    payload: dict[str, Any],
    workspace: Path,
) -> dict[str, Any]:
    """Dispatch one registered engineering action."""

    handlers: dict[str, Callable[[str, dict[str, Any], Path], dict[str, Any]]] = {
        "repository_intelligence": _repository_intelligence,
        "sandbox_verification": _sandbox_verification,
        "failure_diagnostics": _failure_diagnostics,
        "patch_workspace": _patch_workspace,
        "browser_e2e": _browser_e2e,
        "database_migration": _database_migration,
        "security_audit": _security_audit,
        "container_operations": _container_operations,
        "api_contract": _api_contract,
        "release_packaging": _release_packaging,
    }
    handler = handlers.get(skill_name)
    result = (
        handler(action, payload, workspace)
        if handler is not None
        else _advanced_engineering_action(skill_name, action, payload, workspace)
    )
    result.setdefault("status", "SUCCESS")
    result.setdefault("summary", f"{skill_name}.{action} completed")
    result.setdefault("artifacts", [])
    result.setdefault("warnings", [])
    result.setdefault("errors", [])
    result.setdefault("terminal_used", False)
    result.setdefault("internet_used", False)
    result.setdefault("dependency_install_used", False)
    result["workspace"] = str(workspace)
    result["skill"] = skill_name
    result["action"] = action
    result["generated_at"] = _now()
    _write_json(workspace / "skill_result.json", result, workspace)
    _write_summary(workspace / "result_summary.md", result, workspace)
    return result


def _advanced_engineering_action(
    skill_name: str,
    action: str,
    payload: dict[str, Any],
    workspace: Path,
) -> dict[str, Any]:
    no_project_skills = {"internet_search", "package_registry"}
    root = workspace if skill_name in no_project_skills else _project_root(payload)
    if skill_name == "backup_restore" and action in {"backup", "restore"}:
        return _backup_restore_command(action, payload, workspace, root)
    if skill_name == "performance_testing" and action == "run":
        return _performance_command(payload, workspace, root)
    if skill_name == "architecture_refactor_execution" and action == "prepare":
        return _patch_workspace("inspect", payload, workspace)
    specialist_execution = (skill_name, action) in {
        ("api_abuse_simulation", "run"),
        ("behavioral_acceptance_oracle", "run"),
        ("dynamic_authorization_verification", "run"),
        ("flaky_test_investigator", "run"),
        ("installer_vm_lab", "run"),
        ("local_resource_guardian", "cleanup"),
        ("long_horizon_checkpoint_integrity", "run"),
        ("model_runtime_certification", "benchmark"),
        ("online_migration_rehearsal", "run"),
        ("performance_regression_bisect", "run"),
    }
    if specialist_execution or (
        skill_name
        in {
            "accessibility_execution",
            "chaos_verification",
            "consumer_contract_testing",
            "concurrency_correctness",
            "cross_platform_matrix",
            "data_quality_execution",
            "database_query_performance",
            "dependency_provisioning",
            "disaster_recovery_drill",
            "documentation_drift",
            "failure_replay",
            "formal_model_checking",
            "fuzz_property_testing",
            "infrastructure_plan_execution",
            "memory_profiling",
            "mutation_testing",
            "policy_as_code",
            "queue_broker_verification",
            "release_rollback",
            "reproducible_build_verification",
            "schema_drift_data_evolution",
            "slo_telemetry_verification",
            "stateful_workflow_verification",
            "upgrade_compatibility",
            "visual_regression",
        }
        and action == "run"
    ):
        return _specialist_test_command(skill_name, payload, workspace, root)
    if skill_name == "release_provenance" and action in {"verify", "sign"}:
        return _release_provenance_command(action, payload, workspace, root)
    if skill_name == "deployment_verification" and action == "smoke":
        return _deployment_smoke(payload, workspace)
    if skill_name == "git_collaboration":
        return _git_collaboration_command(action, payload, workspace, root)
    if skill_name == "git_history_intelligence":
        return _git_history_intelligence_command(payload, workspace, root)
    from agentic_network.skills.advanced_runtime import (
        execute_advanced_action,
    )

    return execute_advanced_action(skill_name, action, payload, workspace, root)


def _repository_intelligence(
    action: str, payload: dict[str, Any], workspace: Path
) -> dict[str, Any]:
    root = _project_root(payload)
    output = workspace / "repository_intelligence"
    result = build_repository_intelligence(
        root,
        output,
        allowed_roots=[root],
        max_files=_bounded_int(payload.get("max_files"), 1, MAX_SCAN_FILES, MAX_SCAN_FILES),
    )
    data = asdict(result)
    artifacts = list(result.output_files.values())
    if action == "impact":
        targets = _relative_paths(payload.get("target_paths"), root, required=True)
        graph = _read_json(output / "dependency_graph.json")
        tests = _read_json(output / "tests_map.json")
        impact = _impact_payload(targets, graph, tests)
        impact_path = workspace / "impact_analysis.json"
        _write_json(impact_path, impact, workspace)
        artifacts.append(str(impact_path))
        data["impact"] = impact
    return {
        "status": "SUCCESS" if result.validation_passed else "FAILED",
        "summary": (
            f"Scanned {result.files_scanned} files, {result.functions} functions, "
            f"{result.classes} classes, and {result.routes} routes."
        ),
        "data": data,
        "artifacts": artifacts,
        "warnings": result.warnings,
        "errors": result.validation_errors,
    }


def _sandbox_verification(action: str, payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    root = _project_root(payload)
    commands, warnings = _container_verification_commands(root)
    selected = [_display_command(item) for item in commands]
    if action == "detect":
        return {
            "summary": f"Detected {len(commands)} allowlisted verification recipe(s).",
            "data": {"recipes": selected},
            "warnings": warnings,
        }
    compose = _compose_file(root)
    services = _compose_services(compose) if compose else set()
    if compose is None:
        return {
            "status": "BLOCKED",
            "summary": "Docker Compose sandbox is required for project code execution.",
            "data": {"recipes": selected},
            "warnings": warnings,
            "errors": ["docker_compose_sandbox_required"],
        }
    execution_blockers = _compose_execution_blockers(compose)
    if execution_blockers:
        return {
            "status": "BLOCKED",
            "summary": "Compose topology violates verification sandbox policy.",
            "data": {"recipes": selected},
            "warnings": warnings,
            "errors": execution_blockers,
        }
    timeout = _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 120)
    project_name = _compose_project_name(payload.get("project_name"), root)
    prefix = _compose_prefix(root, compose, project_name, workspace)
    sandboxed: list[list[str]] = []
    for command in commands:
        service = "api" if command[0] == "python" else "web"
        if service not in services:
            warnings.append(f"compose_service_missing:{service}")
            continue
        inner = command if command[0] != "npm" else _container_npm_command(command)
        sandboxed.append([*prefix, "run", "--rm", "--no-deps", "--pull", "never", service, *inner])
    results = [
        _run_recipe(f"verification_{index}", command, root, workspace, timeout)
        for index, command in enumerate(sandboxed, start=1)
    ]
    status = _aggregate_recipe_status(results)
    return {
        "status": status,
        "summary": f"Executed {len(results)} allowlisted verification recipe(s): {status}.",
        "data": {
            "recipes": selected,
            "sandbox": "docker_compose",
            "compose_project": project_name,
            "results": [asdict(item) for item in results],
        },
        "artifacts": _recipe_artifacts(results),
        "warnings": warnings,
        "errors": [item.error for item in results if item.error],
        "terminal_used": bool(results),
    }


def _failure_diagnostics(_action: str, payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    root = _project_root(payload)
    context = compile_failure_context(
        project_root=root,
        reviewer_report=_bounded_text(payload.get("reviewer_report")),
        test_report=_bounded_text(payload.get("test_report")),
        stdout=_bounded_text(payload.get("stdout")),
        stderr=_bounded_text(payload.get("stderr")),
        commands=_safe_command_evidence(payload.get("commands")),
        affected_files=_string_list(payload.get("affected_files"), 100),
        patch_text=_bounded_text(payload.get("patch_text")),
        user_request=_bounded_text(payload.get("user_request"), 20_000),
        product_requirements=_bounded_text(payload.get("product_requirements"), 30_000),
        architecture_plan=_bounded_text(payload.get("architecture_plan"), 30_000),
        test_plan=_bounded_text(payload.get("test_plan"), 30_000),
        code_plan=_bounded_text(payload.get("code_plan"), 30_000),
        source="failure_diagnostics_skill",
    )
    json_path = workspace / "failure_context.json"
    md_path = workspace / "failure_context.md"
    _write_json(json_path, context, workspace)
    _write_text(md_path, render_failure_context_markdown(context), workspace)
    isolation = context.get("root_cause_isolation", {})
    return {
        "status": "SUCCESS" if context["status"] != "EMPTY" else "PARTIAL",
        "summary": f"Failure context status {context['status']}; root cause class {isolation.get('failure_type', 'unknown')}.",
        "data": context,
        "artifacts": [str(json_path), str(md_path)],
    }


def _patch_workspace(action: str, payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    root = _project_root(payload)
    patch_path = _project_file(root, payload.get("patch_file"), required=True)
    token = str(payload.get("approval_token") or "") if action == "apply" else None
    result = apply_project_patch(
        root,
        patch_path,
        approval_token=token,
        confirm_apply=action == "apply",
        backup=True,
        dry_run=action != "apply",
    )
    data = result.to_dict()
    data["approval_center_required"] = True
    data["diff_preview"] = _bounded_text(
        patch_path.read_text(  # lgtm[py/path-injection]
            encoding="utf-8", errors="replace"
        ),
        40_000,
    )
    result_path = workspace / "patch_validation.json"
    _write_json(result_path, data, workspace)
    return {
        "status": "SUCCESS" if result.status in {"DRY_RUN", "APPLIED"} else result.status,
        "summary": f"Patch gate returned {result.status}; no bypass of Approval Center was used.",
        "data": data,
        "artifacts": [str(result_path), *result.backups_created],
        "warnings": result.validation_warnings,
        "errors": result.validation_errors,
    }


def _browser_e2e(action: str, payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    root = _project_root(payload)
    _package_root, command = _playwright_recipe(root)
    compose = _compose_file(root)
    services = _compose_services(compose) if compose else set()
    service = "e2e" if "e2e" in services else "web"
    default_url = (
        "http://web:3000" if service == "e2e" and "web" in services else "http://127.0.0.1:3000"
    )
    base_url = str(payload.get("base_url") or default_url)
    _validate_local_url(base_url, allowed_hosts=services)
    evidence = _browser_validation_evidence(root)
    if action == "detect":
        return {
            "status": "SUCCESS" if command else "PARTIAL",
            "summary": "Playwright recipe detected."
            if command
            else "No safe Playwright recipe detected.",
            "data": {
                "recipe": _display_command(command) if command else [],
                "base_url": base_url,
                "evidence": evidence,
            },
        }
    if not command:
        return {
            "status": "SKIPPED",
            "summary": "No safe Playwright recipe detected.",
            "warnings": ["playwright_recipe_missing"],
        }
    if compose is None or service not in services:
        return {
            "status": "BLOCKED",
            "summary": "A Compose web/e2e service is required for browser execution.",
            "errors": ["browser_compose_service_required"],
        }
    execution_blockers = _compose_execution_blockers(compose)
    if execution_blockers:
        return {
            "status": "BLOCKED",
            "summary": "Compose topology violates browser sandbox policy.",
            "errors": execution_blockers,
        }
    project_name = _compose_project_name(payload.get("project_name"), root)
    sandboxed = [
        *_compose_prefix(root, compose, project_name, workspace),
        "run",
        "--rm",
        "--no-deps",
        "--pull",
        "never",
        service,
        *_container_npm_command(command),
    ]
    result = _run_recipe(
        "browser_e2e",
        sandboxed,
        root,
        workspace,
        _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 180),
        extra_env={"PLAYWRIGHT_BASE_URL": base_url},
    )
    evidence = _browser_validation_evidence(root)
    evidence_path = workspace / "browser_evidence.json"
    _write_json(evidence_path, {"result": asdict(result), "evidence": evidence}, workspace)
    return {
        "status": result.status,
        "summary": f"Local browser/E2E recipe finished with {result.status}.",
        "data": {"result": asdict(result), "evidence": evidence},
        "artifacts": [str(evidence_path), *_recipe_artifacts([result])],
        "errors": [result.error] if result.error else [],
        "terminal_used": True,
    }


def _database_migration(action: str, payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    root = _project_root(payload)
    config = _find_alembic_config(root)
    analysis = _migration_analysis(root, config)
    analysis_path = workspace / "migration_analysis.json"
    _write_json(analysis_path, analysis, workspace)
    if action == "inspect":
        return {
            "status": "SUCCESS" if config else "PARTIAL",
            "summary": f"Found {len(analysis['revisions'])} migration revision(s).",
            "data": analysis,
            "artifacts": [str(analysis_path)],
            "warnings": [] if config else ["alembic_config_missing"],
        }
    if config is None:
        return {
            "status": "BLOCKED",
            "summary": "Alembic config is missing.",
            "artifacts": [str(analysis_path)],
            "errors": ["alembic_config_missing"],
        }
    target = str(payload.get("target") or ("head" if action == "upgrade" else "-1"))
    if not re.fullmatch(r"(?:head|base|-?[1-9][0-9]{0,2}|[A-Za-z0-9_]{1,64})", target):
        raise ValueError("invalid_migration_target")
    compose = _compose_file(root)
    services = _compose_services(compose) if compose else set()
    if compose is None or "api" not in services:
        return {
            "status": "BLOCKED",
            "summary": "A Compose api service is required for migration execution.",
            "artifacts": [str(analysis_path)],
            "errors": ["migration_compose_api_service_required"],
        }
    execution_blockers = _compose_execution_blockers(compose)
    if execution_blockers:
        return {
            "status": "BLOCKED",
            "summary": "Compose topology violates migration sandbox policy.",
            "artifacts": [str(analysis_path)],
            "errors": execution_blockers,
        }
    project_name = _compose_project_name(payload.get("project_name"), root)
    command = [
        *_compose_prefix(root, compose, project_name, workspace),
        "run",
        "--rm",
        "--no-deps",
        "--pull",
        "never",
        "api",
        "python",
        "-m",
        "alembic",
        "-c",
        str(config.relative_to(root)),
        action,
        target,
    ]
    result = _run_recipe(
        f"alembic_{action}",
        command,
        root,
        workspace,
        _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 180),
    )
    return {
        "status": result.status,
        "summary": f"Alembic {action} finished with {result.status}.",
        "data": {"analysis": analysis, "result": asdict(result)},
        "artifacts": [str(analysis_path), *_recipe_artifacts([result])],
        "errors": [result.error] if result.error else [],
        "terminal_used": True,
    }


def _security_audit(_action: str, payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    root = _project_root(payload)
    findings = _scan_security(
        root, _bounded_int(payload.get("max_files"), 1, MAX_SCAN_FILES, 2_000)
    )
    counts: dict[str, int] = defaultdict(int)
    for finding in findings:
        counts[str(finding["severity"])] += 1
    status = "FAILED" if counts["critical"] or counts["high"] else "SUCCESS"
    report = {
        "status": status,
        "counts": dict(counts),
        "findings": findings,
        "scanned_root": str(root),
    }
    json_path = workspace / "security_audit.json"
    md_path = workspace / "security_audit.md"
    _write_json(json_path, report, workspace)
    _write_text(md_path, _security_markdown(report), workspace)
    return {
        "status": status,
        "summary": f"Security audit found {len(findings)} finding(s), including {counts['high']} high and {counts['critical']} critical.",
        "data": report,
        "artifacts": [str(json_path), str(md_path)],
    }


def _container_operations(action: str, payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    root = _project_root(payload)
    compose = _compose_file(root)
    if compose is None:
        return {
            "status": "BLOCKED",
            "summary": "Compose file not found.",
            "errors": ["compose_file_missing"],
        }
    project_name = _compose_project_name(payload.get("project_name"), root)
    isolation_findings = _compose_isolation_findings(compose)
    hard_blockers = sorted(
        finding
        for finding in isolation_findings
        if finding
        in {
            "docker_socket_mount",
            "fixed_container_name",
            "host_ipc",
            "host_network",
            "host_pid",
            "privileged_container",
            "public_host_ports",
        }
    )
    if action == "up" and hard_blockers:
        return {
            "status": "BLOCKED",
            "summary": "Compose topology violates ANN container isolation policy.",
            "data": {"isolation_findings": isolation_findings},
            "errors": hard_blockers,
        }
    if (
        action == "up"
        and "loopback_host_ports" in isolation_findings
        and payload.get("allow_host_ports") is not True
    ):
        return {
            "status": "BLOCKED",
            "summary": "Loopback host ports require explicit acknowledgement in the approved payload.",
            "data": {"isolation_findings": isolation_findings},
            "errors": ["loopback_host_ports_require_acknowledgement"],
        }
    prefix = _compose_prefix(root, compose, project_name, workspace)
    tail = _bounded_int(payload.get("tail"), 1, 2_000, 200)
    recipes = {
        "config": [*prefix, "config", "--quiet"],
        "status": [*prefix, "ps", "--all", "--format", "json"],
        "logs": [*prefix, "logs", "--no-color", "--tail", str(tail)],
        "up": [*prefix, "up", "-d", "--no-build", "--pull", "never", "--remove-orphans"],
        "down": [*prefix, "down", "--remove-orphans"],
        "cleanup": [*prefix, "down", "--remove-orphans", "--volumes"],
    }
    result = _run_recipe(
        f"compose_{action}",
        recipes[action],
        root,
        workspace,
        _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 180),
    )
    return {
        "status": result.status,
        "summary": f"Compose {action} for isolated project {project_name} finished with {result.status}.",
        "data": {
            "project_name": project_name,
            "compose_file": str(compose),
            "network_policy": "internal_no_external_egress",
            "isolation_findings": isolation_findings,
            "result": asdict(result),
        },
        "artifacts": _recipe_artifacts([result]),
        "errors": [result.error] if result.error else [],
        "terminal_used": True,
    }


def _api_contract(_action: str, payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    root = _project_root(payload)
    openapi_paths = _openapi_paths(root)
    backend_paths = _backend_route_paths(root)
    frontend_paths = _frontend_api_paths(root)
    webhooks = sorted(path for path in openapi_paths | backend_paths if "webhook" in path.lower())
    contract_tests = _contract_test_files(root)
    webhook_security = _webhook_security_evidence(root, webhooks)
    missing_backend = sorted(openapi_paths - backend_paths)
    frontend_without_contract = sorted(frontend_paths - (openapi_paths | backend_paths))
    report = {
        "openapi_paths": sorted(openapi_paths),
        "backend_paths": sorted(backend_paths),
        "frontend_paths": sorted(frontend_paths),
        "webhooks": webhooks,
        "webhook_security": webhook_security,
        "contract_tests": contract_tests,
        "contract_tests_present": bool(contract_tests),
        "missing_backend_paths": missing_backend,
        "frontend_paths_without_contract": frontend_without_contract,
        "compatible": not missing_backend and not frontend_without_contract,
    }
    path = workspace / "api_contract_report.json"
    _write_json(path, report, workspace)
    return {
        "status": "SUCCESS" if report["compatible"] else "FAILED",
        "summary": (
            f"Compared {len(openapi_paths)} OpenAPI, {len(backend_paths)} backend, and "
            f"{len(frontend_paths)} frontend paths."
        ),
        "data": report,
        "artifacts": [str(path)],
    }


def _release_packaging(action: str, payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    root = _project_root(payload)
    if action == "smoke_installer":
        verifier = root / "installer" / "verify_install.ps1"
        if not verifier.is_file():
            return {
                "status": "BLOCKED",
                "summary": "Installer verifier missing.",
                "errors": ["installer_verifier_missing"],
            }
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(verifier.relative_to(root)),
        ]
        result = _run_recipe(
            "installer_smoke",
            command,
            root,
            workspace,
            _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 180),
        )
        return {
            "status": result.status,
            "summary": f"Installer smoke finished with {result.status}.",
            "data": {"result": asdict(result)},
            "artifacts": _recipe_artifacts([result]),
            "errors": [result.error] if result.error else [],
            "terminal_used": True,
        }
    if action == "verify":
        manifest = _read_json(workspace / "release_manifest.json")
        if not manifest:
            manifest_path = _project_file(root, payload.get("manifest_path"), required=True)
            manifest = _read_json(manifest_path)
        verification = _verify_release_manifest(manifest)
        path = workspace / "release_verification.json"
        _write_json(path, verification, workspace)
        return {
            "status": "SUCCESS" if verification["valid"] else "FAILED",
            "summary": f"Release verification valid={verification['valid']}.",
            "data": verification,
            "artifacts": [str(path)],
            "errors": verification["errors"],
        }
    files = _release_input_files(root, _bounded_int(payload.get("max_files"), 1, 20_000, 5_000))
    sbom = _build_sbom(root)
    sbom_path = workspace / "sbom.cdx.json"
    _write_json(sbom_path, sbom, workspace)
    archive = workspace / "ann-release.zip"
    hashes: list[dict[str, object]] = []
    installer = root / "installer" / "ANN_Setup.exe"
    install_plan = build_install_plan(root, workspace / "install-target")
    plan_validation = validate_install_plan(install_plan)
    rollback = {
        "strategy": "retain previous package and restore user projects/models/outputs",
        "installer_uninstall": str(root / "installer" / "ANN_Uninstall.exe"),
        "preserve": ["projects", "models", "outputs", "data", "logs"],
    }
    rollback_path = workspace / "rollback_manifest.json"
    _write_json(rollback_path, rollback, workspace)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            relative = path.relative_to(root).as_posix()
            digest = _sha256(path)
            hashes.append({"path": relative, "sha256": digest, "size": path.stat().st_size})
            bundle.write(path, relative)
        bundle.write(sbom_path, "release-evidence/sbom.cdx.json")
        bundle.write(rollback_path, "release-evidence/rollback_manifest.json")
    manifest = {
        "status": "READY" if plan_validation.valid and installer.is_file() else "PARTIAL",
        "archive": str(archive),
        "archive_sha256": _sha256(archive),
        "files": hashes,
        "sbom": str(sbom_path),
        "sbom_sha256": _sha256(sbom_path),
        "rollback_manifest": str(rollback_path),
        "rollback_manifest_sha256": _sha256(rollback_path),
        "installer": str(installer),
        "installer_archive_path": "installer/ANN_Setup.exe",
        "installer_exists": installer.is_file(),
        "installer_sha256": _sha256(installer) if installer.is_file() else "",
        "install_plan_valid": plan_validation.valid,
        "install_plan_errors": plan_validation.errors,
        "rollback": rollback,
    }
    manifest_path = workspace / "release_manifest.json"
    _write_json(manifest_path, manifest, workspace)
    return {
        "status": "SUCCESS" if manifest["status"] == "READY" else "PARTIAL",
        "summary": f"Packaged {len(files)} files with SBOM, hashes, installer evidence, and rollback metadata.",
        "data": manifest,
        "artifacts": [str(archive), str(sbom_path), str(rollback_path), str(manifest_path)],
        "warnings": plan_validation.warnings,
        "errors": plan_validation.errors,
    }


def _backup_restore_command(
    action: str,
    payload: dict[str, Any],
    workspace: Path,
    root: Path,
) -> dict[str, Any]:
    compose = _compose_file(root)
    if compose is None:
        return {
            "status": "BLOCKED",
            "summary": "Compose file not found.",
            "errors": ["compose_file_missing"],
        }
    execution_blockers = _compose_execution_blockers(compose)
    if execution_blockers:
        return {
            "status": "BLOCKED",
            "summary": "Compose topology violates backup sandbox policy.",
            "errors": execution_blockers,
        }
    services = _compose_services(compose)
    service = _safe_recipe_segment(payload.get("service"), "db", "database_service")
    if service not in services:
        return {
            "status": "BLOCKED",
            "summary": f"Compose service {service} was not found.",
            "errors": ["database_service_missing"],
        }
    database = _safe_recipe_segment(payload.get("database"), "postgres", "database_name")
    username = _safe_recipe_segment(payload.get("username"), "postgres", "database_username")
    project_name = _compose_project_name(payload.get("project_name"), root)
    prefix = _compose_prefix(root, compose, project_name, workspace)
    timeout = _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 180)
    if action == "backup":
        command = [
            *prefix,
            "exec",
            "-T",
            service,
            "pg_dump",
            "-U",
            username,
            "--format=plain",
            "--no-owner",
            "--no-privileges",
            database,
        ]
        backup_path = validate_workspace_path(workspace / "postgres_backup.sql", workspace)
        result = _run_recipe(
            "postgres_backup",
            command,
            root,
            workspace,
            timeout,
            stdout_artifact=backup_path,
        )
        return {
            "status": result.status,
            "summary": (f"PostgreSQL logical backup finished with {result.status}."),
            "data": {
                "database": database,
                "service": service,
                "backup_path": (
                    str(backup_path)
                    if backup_path.is_file()  # lgtm[py/path-injection]
                    else ""
                ),
                "result": asdict(result),
            },
            "artifacts": [
                *_recipe_artifacts([result]),
                *(
                    [str(backup_path)]
                    if backup_path.is_file()  # lgtm[py/path-injection]
                    else []
                ),
            ],
            "errors": [result.error] if result.error else [],
            "terminal_used": True,
        }
    backup_file = _project_file(root, payload.get("backup_file"), required=True)
    if backup_file.suffix.lower() != ".sql":
        raise ValueError("restore_file_must_be_sql")
    sql = backup_file.read_text(  # lgtm[py/path-injection]
        encoding="utf-8", errors="strict"
    )
    if len(sql) > 100_000_000:
        raise ValueError("restore_file_too_large")
    command = [
        *prefix,
        "exec",
        "-T",
        service,
        "psql",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        username,
        "-d",
        database,
    ]
    result = _run_recipe(
        "postgres_restore",
        command,
        root,
        workspace,
        timeout,
        input_text=sql,
    )
    return {
        "status": result.status,
        "summary": (f"PostgreSQL restore finished with {result.status}."),
        "data": {
            "database": database,
            "service": service,
            "backup_file": str(backup_file),
            "backup_sha256": _sha256(backup_file),
            "result": asdict(result),
        },
        "artifacts": _recipe_artifacts([result]),
        "errors": [result.error] if result.error else [],
        "terminal_used": True,
    }


def _performance_command(
    payload: dict[str, Any],
    workspace: Path,
    root: Path,
) -> dict[str, Any]:
    compose = _compose_file(root)
    if compose is None:
        return {
            "status": "BLOCKED",
            "summary": "Compose file not found.",
            "errors": ["compose_file_missing"],
        }
    execution_blockers = _compose_execution_blockers(compose)
    if execution_blockers:
        return {
            "status": "BLOCKED",
            "summary": "Compose topology violates performance sandbox policy.",
            "errors": execution_blockers,
        }
    service = _safe_recipe_segment(payload.get("service"), "api", "performance_service")
    if service not in _compose_services(compose):
        return {
            "status": "BLOCKED",
            "summary": f"Compose service {service} was not found.",
            "errors": ["performance_service_missing"],
        }
    recipe = str(payload.get("recipe") or "").strip()
    commands = {
        "python_pytest_performance": [
            "python",
            "-m",
            "pytest",
            "-q",
            "-m",
            "performance",
        ],
        "npm_benchmark": ["npm", "run", "benchmark"],
        "npm_performance": ["npm", "run", "test:performance"],
    }
    inner = commands.get(recipe)
    if inner is None:
        return {
            "status": "BLOCKED",
            "summary": "Performance recipe is not allowlisted.",
            "errors": ["performance_recipe_not_allowlisted"],
            "data": {"allowed_recipes": sorted(commands)},
        }
    if inner[0] == "npm":
        inner = _container_npm_command(inner)
    prefix = _compose_prefix(
        root,
        compose,
        _compose_project_name(payload.get("project_name"), root),
        workspace,
    )
    command = [
        *prefix,
        "run",
        "--rm",
        "--no-deps",
        service,
        *inner,
    ]
    result = _run_recipe(
        "performance",
        command,
        root,
        workspace,
        _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 300),
    )
    return {
        "status": result.status,
        "summary": (f"Performance recipe {recipe} finished with {result.status}."),
        "data": {"recipe": recipe, "result": asdict(result)},
        "artifacts": _recipe_artifacts([result]),
        "errors": [result.error] if result.error else [],
        "terminal_used": True,
    }


def _specialist_test_command(
    skill_name: str,
    payload: dict[str, Any],
    workspace: Path,
    root: Path,
) -> dict[str, Any]:
    """Run one closed specialist recipe in the project's Compose sandbox."""

    compose = _compose_file(root)
    if compose is None:
        return {
            "status": "BLOCKED",
            "summary": "Docker Compose sandbox is required.",
            "errors": ["compose_file_missing"],
        }
    requested = str(payload.get("recipe") or "").strip().lower()
    defaults = {
        "accessibility_execution": "web_accessibility",
        "chaos_verification": "python_chaos",
        "consumer_contract_testing": "python_contract",
        "concurrency_correctness": "python_concurrency",
        "cross_platform_matrix": "python_compatibility",
        "data_quality_execution": "python_data_quality",
        "database_query_performance": "python_db_performance",
        "dependency_provisioning": "python_dependency_lock",
        "disaster_recovery_drill": "python_disaster_recovery",
        "documentation_drift": "python_docs",
        "failure_replay": "python_tests",
        "formal_model_checking": "python_formal_model",
        "fuzz_property_testing": "python_fuzz",
        "infrastructure_plan_execution": "terraform_plan",
        "memory_profiling": "python_memory",
        "mutation_testing": "python_mutation",
        "policy_as_code": "python_policy",
        "queue_broker_verification": "python_queue",
        "release_rollback": "python_release_rollback",
        "reproducible_build_verification": "python_reproducible_build",
        "schema_drift_data_evolution": "python_schema_drift",
        "slo_telemetry_verification": "python_telemetry",
        "stateful_workflow_verification": "python_stateful_workflow",
        "upgrade_compatibility": "python_upgrade_compatibility",
        "visual_regression": "web_visual",
        "api_abuse_simulation": "python_api_abuse",
        "behavioral_acceptance_oracle": "python_behavioral_oracle",
        "dynamic_authorization_verification": "python_authorization",
        "flaky_test_investigator": "python_flaky",
        "installer_vm_lab": "python_installer_vm",
        "local_resource_guardian": "compose_cleanup",
        "long_horizon_checkpoint_integrity": "python_checkpoint",
        "model_runtime_certification": "python_model_runtime",
        "online_migration_rehearsal": "python_online_migration",
        "performance_regression_bisect": "python_performance_bisect",
    }
    aliases = {
        "accessibility": "web_accessibility",
        "fuzz": "python_fuzz",
        "memory": "python_memory",
        "mutation": "python_mutation",
        "visual": "web_visual",
    }
    recipe = aliases.get(requested, requested) or defaults[skill_name]
    allowed_by_skill = {
        "accessibility_execution": {"web_accessibility"},
        "chaos_verification": {"python_chaos", "web_chaos"},
        "consumer_contract_testing": {"python_contract", "web_contract"},
        "concurrency_correctness": {"python_concurrency", "web_concurrency"},
        "cross_platform_matrix": {"python_compatibility", "web_compatibility"},
        "data_quality_execution": {"python_data_quality"},
        "database_query_performance": {"python_db_performance"},
        "dependency_provisioning": {"python_dependency_lock"},
        "disaster_recovery_drill": {"python_disaster_recovery"},
        "documentation_drift": {"python_docs", "web_docs"},
        "failure_replay": {
            "compose_config",
            "python_fuzz",
            "python_memory",
            "python_tests",
            "web_accessibility",
            "web_tests",
        },
        "fuzz_property_testing": {"python_fuzz", "web_fuzz"},
        "formal_model_checking": {"python_formal_model", "web_formal_model"},
        "infrastructure_plan_execution": {"terraform_plan"},
        "memory_profiling": {"python_memory", "web_memory"},
        "mutation_testing": {"python_mutation", "web_mutation"},
        "policy_as_code": {"python_policy", "web_policy"},
        "queue_broker_verification": {"python_queue", "web_queue"},
        "release_rollback": {"python_release_rollback"},
        "reproducible_build_verification": {
            "python_reproducible_build",
            "web_reproducible_build",
        },
        "schema_drift_data_evolution": {"python_schema_drift"},
        "slo_telemetry_verification": {"python_telemetry", "web_telemetry"},
        "stateful_workflow_verification": {
            "python_stateful_workflow",
            "web_stateful_workflow",
        },
        "upgrade_compatibility": {
            "python_upgrade_compatibility",
            "web_upgrade_compatibility",
        },
        "visual_regression": {"web_visual"},
        "api_abuse_simulation": {"python_api_abuse"},
        "behavioral_acceptance_oracle": {"python_behavioral_oracle"},
        "dynamic_authorization_verification": {"python_authorization"},
        "flaky_test_investigator": {"python_flaky"},
        "installer_vm_lab": {"python_installer_vm"},
        "local_resource_guardian": {"compose_cleanup"},
        "long_horizon_checkpoint_integrity": {"python_checkpoint"},
        "model_runtime_certification": {"python_model_runtime"},
        "online_migration_rehearsal": {"python_online_migration"},
        "performance_regression_bisect": {"python_performance_bisect"},
    }
    if recipe not in allowed_by_skill[skill_name]:
        return {
            "status": "BLOCKED",
            "summary": "Specialist recipe is not allowlisted.",
            "errors": ["specialist_recipe_not_allowlisted"],
            "data": {"allowed_recipes": sorted(allowed_by_skill[skill_name])},
        }

    isolation_findings = _compose_isolation_findings(compose)
    execution_blockers = _compose_execution_blockers(compose)
    if execution_blockers:
        return {
            "status": "BLOCKED",
            "summary": "Compose topology violates specialist sandbox policy.",
            "errors": execution_blockers,
            "data": {"isolation_findings": isolation_findings},
        }

    prefix = _compose_prefix(
        root,
        compose,
        _compose_project_name(payload.get("project_name"), root),
        workspace,
    )
    if recipe == "compose_config":
        command = [*prefix, "config", "--quiet"]
    elif recipe == "compose_cleanup":
        command = [*prefix, "down", "--remove-orphans"]
    else:
        service, inner, script = _specialist_recipe(recipe)
        if service not in _compose_services(compose):
            return {
                "status": "BLOCKED",
                "summary": f"Compose service {service} was not found.",
                "errors": ["specialist_service_missing"],
                "data": {"recipe": recipe, "service": service},
            }
        if script and not _safe_specialist_package_script(root, script):
            return {
                "status": "BLOCKED",
                "summary": f"Safe package script {script} was not found.",
                "errors": ["specialist_package_script_missing_or_unsafe"],
                "data": {"recipe": recipe, "service": service},
            }
        readiness_error = _specialist_recipe_readiness(root, recipe)
        if readiness_error:
            return {
                "status": "BLOCKED",
                "summary": "Specialist recipe prerequisites are not satisfied.",
                "errors": [readiness_error],
                "data": {"recipe": recipe, "service": service},
            }
        command = [
            *prefix,
            "run",
            "--rm",
            "--no-deps",
            "--pull",
            "never",
            service,
            *inner,
        ]
    result = _run_recipe(
        f"specialist_{recipe}",
        command,
        root,
        workspace,
        _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 300),
    )
    return {
        "status": result.status,
        "summary": (f"Approved specialist recipe {recipe} finished with {result.status}."),
        "data": {
            "recipe": recipe,
            "sandbox": "docker_compose",
            "result": asdict(result),
        },
        "artifacts": _recipe_artifacts([result]),
        "errors": [result.error] if result.error else [],
        "terminal_used": True,
    }


def _specialist_recipe(
    recipe: str,
) -> tuple[str, list[str], str | None]:
    recipes: dict[str, tuple[str, list[str], str | None]] = {
        "python_fuzz": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "fuzz"],
            None,
        ),
        "python_chaos": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "chaos"],
            None,
        ),
        "python_api_abuse": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "api_abuse"],
            None,
        ),
        "python_authorization": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "authorization"],
            None,
        ),
        "python_behavioral_oracle": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "behavioral_oracle"],
            None,
        ),
        "python_checkpoint": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "checkpoint_integrity"],
            None,
        ),
        "python_compatibility": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "compatibility"],
            None,
        ),
        "python_contract": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "contract"],
            None,
        ),
        "python_concurrency": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "concurrency"],
            None,
        ),
        "python_data_quality": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "data_quality"],
            None,
        ),
        "python_db_performance": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "db_performance"],
            None,
        ),
        "python_dependency_lock": (
            "api",
            [
                "python",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-index",
                "--require-hashes",
                "--target",
                "/tmp/ann-dependencies",
                "-r",
                "requirements.lock",
            ],
            None,
        ),
        "python_docs": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "docs"],
            None,
        ),
        "python_disaster_recovery": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "disaster_recovery"],
            None,
        ),
        "python_formal_model": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "formal_model"],
            None,
        ),
        "python_flaky": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "flaky_investigation"],
            None,
        ),
        "python_installer_vm": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "installer_vm_lab"],
            None,
        ),
        "python_memory": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "memory"],
            None,
        ),
        "python_mutation": (
            "api",
            ["python", "-m", "mutmut", "run"],
            None,
        ),
        "python_model_runtime": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "model_runtime"],
            None,
        ),
        "python_online_migration": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "online_migration"],
            None,
        ),
        "python_policy": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "policy"],
            None,
        ),
        "python_performance_bisect": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "performance_history"],
            None,
        ),
        "python_queue": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "queue"],
            None,
        ),
        "python_release_rollback": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "release_rollback"],
            None,
        ),
        "python_reproducible_build": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "reproducible_build"],
            None,
        ),
        "python_schema_drift": (
            "api",
            ["python", "-m", "alembic", "check"],
            None,
        ),
        "python_tests": (
            "api",
            ["python", "-m", "pytest", "-q"],
            None,
        ),
        "python_stateful_workflow": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "stateful_workflow"],
            None,
        ),
        "python_telemetry": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "telemetry"],
            None,
        ),
        "python_upgrade_compatibility": (
            "api",
            ["python", "-m", "pytest", "-q", "-m", "upgrade_compatibility"],
            None,
        ),
        "web_accessibility": (
            "web",
            ["npm", "run", "test:a11y"],
            "test:a11y",
        ),
        "terraform_plan": (
            "infra",
            [
                "terraform",
                "plan",
                "-input=false",
                "-lock=false",
                "-refresh=false",
                "-out=/tmp/ann.tfplan",
            ],
            None,
        ),
        "web_chaos": (
            "web",
            ["npm", "run", "test:chaos"],
            "test:chaos",
        ),
        "web_compatibility": (
            "web",
            ["npm", "run", "test:compatibility"],
            "test:compatibility",
        ),
        "web_contract": (
            "web",
            ["npm", "run", "test:contract"],
            "test:contract",
        ),
        "web_concurrency": (
            "web",
            ["npm", "run", "test:concurrency"],
            "test:concurrency",
        ),
        "web_docs": (
            "web",
            ["npm", "run", "test:docs"],
            "test:docs",
        ),
        "web_fuzz": (
            "web",
            ["npm", "run", "test:fuzz"],
            "test:fuzz",
        ),
        "web_formal_model": (
            "web",
            ["npm", "run", "test:formal"],
            "test:formal",
        ),
        "web_memory": (
            "web",
            ["npm", "run", "test:memory"],
            "test:memory",
        ),
        "web_mutation": (
            "web",
            ["npm", "run", "test:mutation"],
            "test:mutation",
        ),
        "web_policy": (
            "web",
            ["npm", "run", "test:policy"],
            "test:policy",
        ),
        "web_queue": (
            "web",
            ["npm", "run", "test:queue"],
            "test:queue",
        ),
        "web_tests": ("web", ["npm", "test", "--", "--run"], "test"),
        "web_reproducible_build": (
            "web",
            ["npm", "run", "test:reproducible"],
            "test:reproducible",
        ),
        "web_stateful_workflow": (
            "web",
            ["npm", "run", "test:stateful"],
            "test:stateful",
        ),
        "web_telemetry": (
            "web",
            ["npm", "run", "test:telemetry"],
            "test:telemetry",
        ),
        "web_upgrade_compatibility": (
            "web",
            ["npm", "run", "test:upgrade"],
            "test:upgrade",
        ),
        "web_visual": (
            "web",
            ["npm", "run", "test:visual"],
            "test:visual",
        ),
    }
    return recipes[recipe]


def _safe_specialist_package_script(root: Path, name: str) -> bool:
    allowed_prefixes = {
        "test": ("jest", "node --test", "vitest"),
        "test:a11y": ("axe", "jest", "playwright test", "vitest"),
        "test:chaos": ("jest", "node --test", "playwright test", "vitest"),
        "test:compatibility": ("jest", "node --test", "playwright test", "vitest"),
        "test:concurrency": ("jest", "node --test", "playwright test", "vitest"),
        "test:contract": ("jest", "node --test", "pact", "playwright test", "vitest"),
        "test:docs": ("jest", "node --test", "playwright test", "vitest"),
        "test:formal": ("alloy", "jest", "node --test", "playwright test", "tlc", "vitest"),
        "test:fuzz": ("fast-check", "jest", "node --test", "vitest"),
        "test:memory": ("clinic", "jest", "node --test", "vitest"),
        "test:mutation": ("stryker",),
        "test:policy": ("conftest", "jest", "node --test", "opa test", "vitest"),
        "test:queue": ("jest", "node --test", "playwright test", "vitest"),
        "test:reproducible": ("jest", "node --test", "vitest"),
        "test:stateful": ("jest", "node --test", "playwright test", "vitest"),
        "test:telemetry": ("jest", "node --test", "playwright test", "vitest"),
        "test:upgrade": ("jest", "node --test", "playwright test", "vitest"),
        "test:visual": ("playwright test",),
    }
    for package_root in (root, root / "apps" / "web"):
        manifest = _read_json(package_root / "package.json")
        scripts = manifest.get("scripts", {}) if isinstance(manifest, dict) else {}
        script = scripts.get(name) if isinstance(scripts, dict) else None
        if not isinstance(script, str):
            continue
        normalized = " ".join(script.lower().split())
        if not COMMAND_META.search(normalized) and normalized.startswith(allowed_prefixes[name]):
            return True
    return False


def _specialist_recipe_readiness(root: Path, recipe: str) -> str:
    if recipe == "python_dependency_lock":
        try:
            lock = _project_file(root, "requirements.lock", required=True)
        except ValueError:
            return "hashed_requirements_lock_missing"
        requirements = [
            line.strip()
            for line in lock.read_text(  # lgtm[py/path-injection]
                encoding="utf-8", errors="replace"
            ).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not requirements or any(
            "==" not in line or re.search(r"--hash=sha256:[0-9a-fA-F]{64}(?:\s|$)", line) is None
            for line in requirements
        ):
            return "requirements_lock_hashes_required"
    terraform_files = _top_level_files(root, ".tf")
    if recipe == "terraform_plan" and not terraform_files:
        return "terraform_configuration_missing"
    if recipe == "terraform_plan":
        terraform = "\n".join(
            path.read_text(  # lgtm[py/path-injection]
                encoding="utf-8", errors="replace"
            )[:512_000]
            for path in terraform_files
        )
        if re.search(
            r'(?is)(?:provisioner\s+"(?:local|remote)-exec"|data\s+"external")',
            terraform,
        ):
            return "terraform_executable_hooks_blocked"
    if recipe == "python_schema_drift" and _find_alembic_config(root) is None:
        return "alembic_config_missing"
    return ""


def _top_level_files(root: Path, suffix: str) -> list[Path]:
    files: list[Path] = []
    for candidate in sorted(root.iterdir()):  # lgtm[py/path-injection]
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if (
            candidate.suffix.lower() == suffix and candidate.is_file()  # lgtm[py/path-injection]
        ):
            files.append(candidate)
            if len(files) >= 100:
                break
    return files


def _release_provenance_command(
    action: str,
    payload: dict[str, Any],
    workspace: Path,
    root: Path,
) -> dict[str, Any]:
    timeout = _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 180)
    if action == "verify":
        artifact = _project_file(root, payload.get("artifact"), required=True)
        if artifact.suffix.lower() not in {".exe", ".msi"}:
            raise ValueError("signature_artifact_type_not_allowed")
        result = _run_recipe(
            "authenticode_verify",
            ["signtool", "verify", "/pa", "/all", "/v", str(artifact)],
            root,
            workspace,
            timeout,
        )
        return {
            "status": result.status,
            "summary": (f"Authenticode verification finished with {result.status}."),
            "data": {
                "artifact": str(artifact),
                "sha256": _sha256(artifact),
                "result": asdict(result),
            },
            "artifacts": _recipe_artifacts([result]),
            "errors": [result.error] if result.error else [],
            "terminal_used": True,
        }
    script = root / "installer" / "sign_release.ps1"
    if not script.is_file():  # lgtm[py/path-injection]
        return {
            "status": "BLOCKED",
            "summary": "Approved signing script is missing.",
            "errors": ["signing_script_missing"],
        }
    thumbprint = re.sub(r"\s+", "", str(payload.get("certificate_thumbprint") or ""))
    if not re.fullmatch(r"[0-9A-Fa-f]{40}", thumbprint):
        raise ValueError("certificate_thumbprint_invalid")
    timestamp_url = str(payload.get("timestamp_url") or "https://timestamp.digicert.com")
    parsed = urlparse(timestamp_url)
    timestamp_host = (parsed.hostname or "").lower().rstrip(".")
    allowed_timestamp_domains = {
        "timestamp.digicert.com",
        *(
            _safe_network_domain(item)
            for item in _string_list(payload.get("allowed_timestamp_domains"), 10)
        ),
    }
    if (
        parsed.scheme != "https"
        or not timestamp_host
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or not any(
            timestamp_host == domain or timestamp_host.endswith(f".{domain}")
            for domain in allowed_timestamp_domains
        )
    ):
        raise ValueError("timestamp_url_invalid")
    evidence = validate_workspace_path(workspace / "release_signing_evidence.json", workspace)
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script.relative_to(root)),
        "-CertificateThumbprint",
        thumbprint,
        "-TimestampUrl",
        timestamp_url,
        "-OutputPath",
        str(evidence),
        "-Execute",
    ]
    result = _run_recipe(
        "authenticode_sign",
        command,
        root,
        workspace,
        timeout,
    )
    return {
        "status": result.status,
        "summary": (f"Authenticode signing recipe finished with {result.status}."),
        "data": {
            "timestamp_host": timestamp_host,
            "evidence": str(evidence),
            "result": asdict(result),
        },
        "artifacts": [
            *_recipe_artifacts([result]),
            *(
                [str(evidence)]
                if evidence.is_file()  # lgtm[py/path-injection]
                else []
            ),
        ],
        "errors": [result.error] if result.error else [],
        "terminal_used": True,
    }


def _deployment_smoke(payload: dict[str, Any], workspace: Path) -> dict[str, Any]:
    start = _container_operations("up", payload, workspace)
    results: list[dict[str, Any]] = [start]
    if start.get("status") == "SUCCESS":
        results.append(_container_operations("status", payload, workspace))
    if payload.get("cleanup") is not False:
        results.append(_container_operations("down", payload, workspace))
    status = (
        "SUCCESS"
        if results and all(item.get("status") == "SUCCESS" for item in results)
        else "FAILED"
    )
    return {
        "status": status,
        "summary": (f"Local deployment smoke completed with {status}."),
        "data": {
            "steps": results,
            "cleanup_attempted": payload.get("cleanup") is not False,
        },
        "artifacts": [artifact for item in results for artifact in item.get("artifacts", [])],
        "errors": [error for item in results for error in item.get("errors", [])],
        "terminal_used": True,
    }


def _git_collaboration_command(
    action: str,
    payload: dict[str, Any],
    workspace: Path,
    root: Path,
) -> dict[str, Any]:
    timeout = _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 120)
    if action == "status":
        result = _run_recipe(
            "git_status",
            ["git", "status", "--porcelain=v2", "--branch"],
            root,
            workspace,
            timeout,
        )
        return _git_result(action, [result])
    if action == "branch":
        branch = _safe_git_branch(payload.get("branch"))
        result = _run_recipe(
            "git_branch",
            ["git", "switch", "-c", branch],
            root,
            workspace,
            timeout,
        )
        return _git_result(action, [result])
    if action == "commit":
        files = _relative_paths(payload.get("files"), root, required=True)[:100]
        message = _safe_commit_message(payload.get("message"))
        add = _run_recipe(
            "git_add",
            ["git", "add", "--", *files],
            root,
            workspace,
            timeout,
        )
        results = [add]
        if add.status == "SUCCESS":
            results.append(
                _run_recipe(
                    "git_commit",
                    ["git", "commit", "-m", message],
                    root,
                    workspace,
                    timeout,
                )
            )
        return _git_result(action, results)
    branch = _safe_git_branch(payload.get("branch"))
    if not branch.startswith("agent/"):
        raise ValueError("publish_branch_must_be_namespaced")
    push = _run_recipe(
        "git_push",
        ["git", "push", "-u", "origin", branch],
        root,
        workspace,
        timeout,
    )
    results = [push]
    if push.status == "SUCCESS":
        title = _safe_commit_message(payload.get("title") or f"Publish {branch}")
        results.append(
            _run_recipe(
                "github_pr",
                [
                    "gh",
                    "pr",
                    "create",
                    "--draft",
                    "--fill",
                    "--head",
                    branch,
                    "--title",
                    title,
                ],
                root,
                workspace,
                timeout,
            )
        )
    return _git_result(action, results)


def _git_history_intelligence_command(
    payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    max_commits = _bounded_int(payload.get("max_commits"), 1, 500, 100)
    result = _run_recipe(
        "git_history_intelligence",
        [
            "git",
            "log",
            "--no-renames",
            "--date=iso-strict",
            "--format=ANN_COMMIT%x09%H%x09%an%x09%aI%x09%s",
            "--name-only",
            "-n",
            str(max_commits),
            "--",
        ],
        root,
        workspace,
        _bounded_int(payload.get("timeout_seconds"), 1, MAX_TIMEOUT, 120),
    )
    if result.status != "SUCCESS":
        return {
            "status": result.status,
            "summary": "Bounded Git history collection failed.",
            "data": {"max_commits": max_commits, "result": asdict(result)},
            "artifacts": _recipe_artifacts([result]),
            "errors": [result.error] if result.error else [],
            "terminal_used": True,
        }

    stdout = _read_recipe_output(result.stdout_path, workspace)
    commits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in stdout.splitlines():
        if line.startswith("ANN_COMMIT\t"):
            parts = line.split("\t", 4)
            if len(parts) != 5:
                current = None
                continue
            message = parts[4].lower()
            current = {
                "sha": parts[1][:12],
                "author_id": hashlib.sha256(parts[2].encode("utf-8")).hexdigest()[:12],
                "timestamp": parts[3][:40],
                "classification": (
                    "regression_fix"
                    if re.search(r"\b(?:fix|bug|regression|revert|hotfix)\b", message)
                    else "change"
                ),
                "files": [],
            }
            commits.append(current)
            continue
        normalized = line.strip().replace("\\", "/").strip("/")
        if not normalized or current is None:
            continue
        parts = normalized.split("/")
        if (
            ".." not in parts
            and not any(part.lower() in PROTECTED_PARTS for part in parts)
            and len(current["files"]) < 500
        ):
            current["files"].append(normalized)

    churn: Counter[str] = Counter()
    owners: dict[str, Counter[str]] = defaultdict(Counter)
    cochange: Counter[tuple[str, str]] = Counter()
    for commit in commits:
        files = sorted(set(commit["files"]))[:100]
        for path in files:
            churn[path] += 1
            owners[path][commit["author_id"]] += 1
        for index, left in enumerate(files):
            for right in files[index + 1 :]:
                cochange[(left, right)] += 1

    hotspots = [
        {
            "path": path,
            "changes": count,
            "primary_owner_id": owners[path].most_common(1)[0][0] if owners[path] else "",
            "owner_count": len(owners[path]),
        }
        for path, count in churn.most_common(100)
    ]
    report = {
        "commit_count": len(commits),
        "regression_fix_count": sum(
            1 for item in commits if item["classification"] == "regression_fix"
        ),
        "hotspots": hotspots,
        "cochange_pairs": [
            {"left": pair[0], "right": pair[1], "count": count}
            for pair, count in cochange.most_common(100)
        ],
        "authors_pseudonymized": True,
        "commit_messages_stored": False,
        "project_modified": False,
    }
    report_path = workspace / "git_history_intelligence.json"
    _write_json(report_path, report, workspace)
    return {
        "status": "SUCCESS" if commits else "PARTIAL",
        "summary": f"Analyzed {len(commits)} commits and {len(churn)} changed files.",
        "data": report,
        "artifacts": [str(report_path), *_recipe_artifacts([result])],
        "terminal_used": True,
    }


def _read_recipe_output(value: str, workspace: Path) -> str:
    path = Path(value)
    validate_workspace_path(path, workspace)
    try:
        return path.read_text(  # lgtm[py/path-injection]
            encoding="utf-8", errors="replace"
        )[:MAX_CAPTURE]
    except OSError:
        return ""


def _git_result(action: str, results: list[RecipeResult]) -> dict[str, Any]:
    status = _aggregate_recipe_status(results)
    return {
        "status": status,
        "summary": (f"Git collaboration action {action} finished with {status}."),
        "data": {
            "action": action,
            "results": [asdict(item) for item in results],
        },
        "artifacts": _recipe_artifacts(results),
        "errors": [item.error for item in results if item.error],
        "terminal_used": True,
    }


def _safe_recipe_segment(value: object, default: str, label: str) -> str:
    text = str(value or default).strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,63}", text):
        raise ValueError(f"{label}_invalid")
    return text


def _safe_git_branch(value: object) -> str:
    raw = str(value or "").strip().replace("\\", "/")
    if not re.fullmatch(r"agent/[a-z0-9][a-z0-9._/-]{0,80}", raw):
        raise ValueError("git_branch_invalid")
    if ".." in raw or raw.endswith("/") or "//" in raw:
        raise ValueError("git_branch_invalid")
    return raw


def _safe_network_domain(value: object) -> str:
    domain = str(value or "").strip().lower().rstrip(".")
    if len(domain) > 253 or "." not in domain:
        raise ValueError("network_domain_invalid")
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise ValueError("network_domain_invalid")
    if not all(
        re.fullmatch(
            r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
            label,
        )
        is not None
        for label in domain.split(".")
    ):
        raise ValueError("network_domain_invalid")
    return domain


def _safe_commit_message(value: object) -> str:
    text = " ".join(str(value or "").split())[:120]
    if not text or COMMAND_META.search(text) or any(ord(char) < 32 for char in text):
        raise ValueError("git_message_invalid")
    return text


def _project_root(payload: dict[str, Any]) -> Path:
    raw = str(payload.get("project_root") or "").strip()
    if not raw:
        raise ValueError("project_root_required")
    normalized = raw.replace("\\", "/")
    if ".." in normalized.split("/"):
        raise ValueError("project_root_path_traversal")
    # The selected path is normalized first, then constrained by ANN's global
    # read policy before any filesystem operation can observe it.
    root = Path(raw).resolve()  # lgtm[py/path-injection]
    if re.match(r"(?i)^(?:c:/|/mnt/c(?:/|$))", normalized) and not _allowed_test_temp(root):
        raise ValueError("project_root_c_drive_blocked")
    if not _allowed_test_temp(root):
        policy_errors = load_filesystem_policy().validate_read_path(root)
        if policy_errors:
            raise ValueError("project_root_policy_blocked:" + ";".join(policy_errors))
    if not root.is_dir():  # lgtm[py/path-injection]
        raise ValueError("project_root_missing")
    if any(part.lower() in PROTECTED_PARTS for part in root.parts):
        raise ValueError("project_root_protected")
    return root


def _allowed_test_temp(path: Path) -> bool:
    if os.environ.get("ANN_ALLOW_TEMP_SKILL_TARGETS") != "1":
        return False
    temp = os.environ.get("TEMP") or os.environ.get("TMP")
    if not temp:
        return False
    try:
        path.relative_to(Path(temp).resolve())
        return True
    except ValueError:
        return False


def _project_file(root: Path, value: object, *, required: bool) -> Path:
    raw = str(value or "").strip()
    if not raw:
        if required:
            raise ValueError("project_file_required")
        return root
    if ".." in raw.replace("\\", "/").split("/"):
        raise ValueError("project_file_path_traversal")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()  # lgtm[py/path-injection]
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("project_file_outside_root") from exc
    if any(part.lower() in PROTECTED_PARTS for part in relative.parts):
        raise ValueError("project_file_protected")
    if required and not resolved.is_file():  # lgtm[py/path-injection]
        raise ValueError("project_file_missing")
    return resolved


def _run_recipe(
    name: str,
    command: list[str],
    cwd: Path,
    workspace: Path,
    timeout: int,
    *,
    extra_env: dict[str, str] | None = None,
    input_text: str | None = None,
    stdout_artifact: Path | None = None,
) -> RecipeResult:
    if not command or any(COMMAND_META.search(str(part)) for part in command):
        raise ValueError("unsafe_recipe_command")
    started = time.perf_counter()
    stdout_path = workspace / f"{name}_stdout.log"
    stderr_path = workspace / f"{name}_stderr.log"
    environment = _safe_env(cwd)
    if extra_env:
        environment.update(extra_env)
    try:
        completed = subprocess.run(  # noqa: S603 - command is built only by closed recipes.
            _resolve_executable(  # lgtm[py/command-line-injection]
                command
            ),
            cwd=str(cwd),
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            env=environment,
            check=False,
        )
        stdout = _bounded_text(completed.stdout, MAX_CAPTURE)
        stderr = _bounded_text(completed.stderr, MAX_CAPTURE)
        status = "SUCCESS" if completed.returncode == 0 else "FAILED"
        error = "" if completed.returncode == 0 else f"recipe_exit_code:{completed.returncode}"
        exit_code: int | None = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = _bounded_text(exc.stdout, MAX_CAPTURE)
        stderr = _bounded_text(exc.stderr, MAX_CAPTURE)
        status = "TIMEOUT"
        error = "recipe_timeout"
        exit_code = None
    except OSError as exc:
        stdout = ""
        stderr = _bounded_text(str(exc), MAX_CAPTURE)
        status = "FAILED"
        error = f"recipe_execution_failed:{type(exc).__name__}"
        exit_code = None
    _write_text(stdout_path, stdout, workspace)
    _write_text(stderr_path, stderr, workspace)
    if stdout_artifact is not None and status == "SUCCESS":
        _write_text(stdout_artifact, stdout, workspace)
    return RecipeResult(
        name,
        status,
        _redact_command(command),
        exit_code,
        str(stdout_path),
        str(stderr_path),
        round(time.perf_counter() - started, 3),
        error,
    )


def _safe_env(root: Path) -> dict[str, str]:
    allowed = {
        key: value
        for key, value in os.environ.items()
        if key.upper()
        in {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE"}
    }
    allowed.update(
        {
            "ANN_PROJECT_ROOT": str(root),
            "NEXT_TELEMETRY_DISABLED": "1",
            "CI": "1",
            "PYTHONNOUSERSITE": "1",
        }
    )
    return allowed


def _resolve_executable(command: list[str]) -> list[str]:
    first = command[0]
    if first in {"python", sys.executable}:
        return [sys.executable, *command[1:]]
    if first == "npm":
        return [shutil.which("npm.cmd" if os.name == "nt" else "npm") or "npm", *command[1:]]
    if first == "docker":
        return [
            shutil.which("docker.exe" if os.name == "nt" else "docker") or "docker",
            *command[1:],
        ]
    if first == "powershell":
        return [shutil.which("powershell.exe") or "powershell", *command[1:]]
    if first == "git":
        return [shutil.which("git.exe" if os.name == "nt" else "git") or "git", *command[1:]]
    if first == "gh":
        return [shutil.which("gh.exe" if os.name == "nt" else "gh") or "gh", *command[1:]]
    if first == "signtool":
        return [
            shutil.which("signtool.exe" if os.name == "nt" else "signtool") or "signtool",
            *command[1:],
        ]
    raise ValueError("recipe_executable_not_allowlisted")


def _display_command(command: list[str]) -> list[str]:
    return ["python" if item == sys.executable else item for item in command]


def _redact_command(command: list[str]) -> list[str]:
    return [
        "<redacted>" if re.search(r"(?i)(token|secret|password|api[_-]?key)=", item) else item
        for item in command
    ]


def _impact_payload(targets: list[str], graph: object, tests: object) -> dict[str, object]:
    dependencies = graph.get("file_dependencies", []) if isinstance(graph, dict) else []
    reverse: dict[str, set[str]] = defaultdict(set)
    for item in dependencies if isinstance(dependencies, list) else []:
        if not isinstance(item, dict):
            continue
        source = str(item.get("file", ""))
        for dependency in item.get("depends_on", []):
            reverse[str(dependency)].add(source)
    tests_map = tests if isinstance(tests, dict) else {}
    affected: set[str] = set(targets)
    queue = list(targets)
    while queue and len(affected) < 500:
        current = queue.pop(0)
        for dependent in reverse.get(current, set()):
            if dependent not in affected:
                affected.add(dependent)
                queue.append(dependent)
    impacted_tests = sorted({str(test) for path in affected for test in tests_map.get(path, [])})
    return {
        "targets": targets,
        "affected_files": sorted(affected),
        "impacted_tests": impacted_tests,
    }


def _relative_paths(value: object, root: Path, *, required: bool) -> list[str]:
    values = _string_list(value, 100)
    if required and not values:
        raise ValueError("target_paths_required")
    result = []
    for item in values:
        path = _project_file(root, item, required=False)
        result.append(path.relative_to(root).as_posix())
    return sorted(set(result))


def _safe_command_evidence(value: object) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value[:50]:
        if isinstance(item, list):
            result.append([_bounded_text(part, 500) for part in item[:40]])
        elif isinstance(item, str):
            result.append([_bounded_text(item, 2_000)])
    return result


def _playwright_recipe(root: Path) -> tuple[Path | None, list[str]]:
    for package_root, prefix in ((root, []), (root / "apps" / "web", ["--prefix", "apps/web"])):
        manifest = _read_json(package_root / "package.json")
        scripts = manifest.get("scripts", {}) if isinstance(manifest, dict) else {}
        script = scripts.get("e2e") if isinstance(scripts, dict) else None
        if (
            isinstance(script, str)
            and "playwright test" in script.lower()
            and not COMMAND_META.search(script)
        ):
            return package_root, ["npm", *prefix, "run", "e2e"]
    return None, []


def _container_verification_commands(root: Path) -> tuple[list[list[str]], list[str]]:
    commands, warnings = detect_project_test_commands(root)
    existing = {tuple(command) for command in commands}
    for package_root, prefix in ((root, []), (root / "apps" / "web", ["--prefix", "apps/web"])):
        manifest = _read_json(package_root / "package.json")
        scripts = manifest.get("scripts", {}) if isinstance(manifest, dict) else {}
        if not isinstance(scripts, dict):
            continue
        for name in ("test", "build", "e2e"):
            script = scripts.get(name)
            if not isinstance(script, str) or not _safe_package_script(name, script):
                continue
            command = ["npm", *prefix, *([name] if name == "test" else ["run", name])]
            if tuple(command) not in existing:
                commands.append(command)
                existing.add(tuple(command))
    return commands, warnings


def _safe_package_script(name: str, script: str) -> bool:
    normalized = " ".join(script.lower().split())
    if COMMAND_META.search(normalized):
        return False
    allowed = {
        "test": ("vitest", "jest", "node --test"),
        "build": ("next build", "vite build", "tsc", "react-scripts build"),
        "e2e": ("playwright test",),
    }
    return normalized.startswith(allowed[name])


def _container_npm_command(command: list[str]) -> list[str]:
    if command[:3] == ["npm", "--prefix", "apps/web"]:
        return ["npm", *command[3:]]
    return command


def _validate_local_url(value: str, *, allowed_hosts: set[str] | None = None) -> None:
    parsed = urlparse(value)
    local_hosts = {"localhost", "127.0.0.1", "::1", *(allowed_hosts or set())}
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.hostname not in local_hosts
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError("browser_e2e_requires_local_url")


def _browser_evidence_paths(root: Path) -> list[str]:
    candidates = []
    for base in (root, root / "apps" / "web"):
        for name in ("playwright-report", "test-results"):
            path = base / name
            if path.exists():
                candidates.append(str(path))
    return candidates


def _browser_validation_evidence(root: Path) -> dict[str, object]:
    artifact_paths = _browser_evidence_paths(root)
    test_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")[:200_000]
        for pattern in ("*.spec.ts", "*.spec.tsx", "*.test.ts", "*.test.tsx")
        for path in root.rglob(pattern)
        if "node_modules" not in path.parts
    ).lower()
    files = []
    for raw_path in artifact_paths:
        path = Path(raw_path)
        if path.is_file():
            files.append(str(path))
        elif path.is_dir():
            files.extend(str(item) for item in path.rglob("*") if item.is_file())
    return {
        "artifact_paths": artifact_paths,
        "screenshots": sorted(
            path for path in files if Path(path).suffix.lower() in {".png", ".jpg", ".jpeg"}
        ),
        "traces": sorted(
            path for path in files if Path(path).name.lower().endswith(("trace.zip", ".zip"))
        ),
        "videos": sorted(path for path in files if Path(path).suffix.lower() in {".webm", ".mp4"}),
        "console_assertions_declared": bool(re.search(r"console|pageerror", test_text)),
        "network_assertions_declared": bool(
            re.search(r"page\.(?:on|waitforresponse|waitforrequest)|route\(", test_text)
        ),
        "accessibility_assertions_declared": bool(
            re.search(r"axe|accessib|aria-|tobeaccessible", test_text)
        ),
        "visual_assertions_declared": bool(re.search(r"toscreenshot|screenshot\(", test_text)),
    }


def _find_alembic_config(root: Path) -> Path | None:
    for candidate in (root / "alembic.ini", root / "apps" / "api" / "alembic.ini"):
        if candidate.is_file():
            return candidate
    return None


def _migration_analysis(root: Path, config: Path | None) -> dict[str, Any]:
    revisions: list[dict[str, Any]] = []
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(
            part.lower() in PROTECTED_PARTS | {"node_modules", ".venv", "venv"}
            for part in relative.parts
        ):
            continue
        normalized = relative.as_posix().lower()
        if "migration" not in normalized and "alembic" not in normalized:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        revisions.append(
            {
                "path": relative.as_posix(),
                "upgrade": "def upgrade" in text,
                "downgrade": "def downgrade" in text,
                "indexes": len(re.findall(r"create_index|Index\(", text)),
                "constraints": len(
                    re.findall(
                        r"create_(?:foreign_key|unique_constraint|check_constraint)|"
                        r"ForeignKey\(|UniqueConstraint\(|CheckConstraint\(",
                        text,
                    )
                ),
                "destructive_operations": len(
                    re.findall(r"drop_(?:table|column)|alter_column\(", text)
                ),
                "tenant_scope": bool(re.search(r"tenant_id|organization_id", text, re.IGNORECASE)),
            }
        )
    return {
        "alembic_config": str(config) if config else "",
        "revisions": revisions,
        "reversible": bool(revisions) and all(item["downgrade"] for item in revisions),
        "tenant_scope_detected": any(item["tenant_scope"] for item in revisions),
        "constraint_count": sum(int(item["constraints"]) for item in revisions),
        "destructive_operation_count": sum(
            int(item["destructive_operations"]) for item in revisions
        ),
    }


def _scan_security(root: Path, max_files: int) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    patterns = (
        (
            "critical",
            "hardcoded_secret",
            re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]"),
        ),
        ("high", "shell_true", re.compile(r"shell\s*=\s*True")),
        ("high", "dynamic_eval", re.compile(r"\b(?:eval|exec)\s*\(")),
        ("high", "docker_privileged", re.compile(r"privileged\s*:\s*true", re.IGNORECASE)),
        ("medium", "docker_latest", re.compile(r"image\s*:\s*[^\s:#]+:latest", re.IGNORECASE)),
        (
            "medium",
            "jwt_decode_without_algorithms",
            re.compile(r"jwt\.decode\([^\n]+\)(?![^\n]*algorithms)"),
        ),
        ("medium", "wildcard_cors", re.compile(r"allow_origins\s*=\s*\[['\"]\*['\"]\]")),
    )
    scanned = 0
    for path in sorted(root.rglob("*")):
        if scanned >= max_files:
            break
        if not path.is_file() or path.stat().st_size > 512_000:
            continue
        relative = path.relative_to(root)
        if any(
            part.lower() in PROTECTED_PARTS | {"node_modules", ".venv", "venv", "dist", "build"}
            for part in relative.parts
        ):
            continue
        if path.suffix.lower() not in {
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".yaml",
            ".yml",
            ".json",
            ".toml",
            ".env",
        }:
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for severity, rule, pattern in patterns:
            match = pattern.search(text)
            if match:
                findings.append(
                    {
                        "severity": severity,
                        "rule": rule,
                        "path": relative.as_posix(),
                        "line": text.count("\n", 0, match.start()) + 1,
                    }
                )
        if path.name in {"requirements.txt", "pyproject.toml", "package.json"}:
            for line_number, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if (
                    stripped
                    and not stripped.startswith(("#", "[", "{", "}"))
                    and "latest" in stripped.lower()
                ):
                    findings.append(
                        {
                            "severity": "medium",
                            "rule": "unbounded_dependency",
                            "path": relative.as_posix(),
                            "line": line_number,
                        }
                    )
    return findings[:1_000]


def _security_markdown(report: dict[str, Any]) -> str:
    lines = ["# Security Audit", "", f"Status: {report['status']}", "", "## Findings"]
    for item in report["findings"]:
        lines.append(
            f"- {item['severity'].upper()} {item['rule']} at {item['path']}:{item['line']}"
        )
    if not report["findings"]:
        lines.append("- No deterministic findings.")
    return "\n".join(lines) + "\n"


def _compose_file(root: Path) -> Path | None:
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        candidate = root / name
        if candidate.is_file():  # lgtm[py/path-injection]
            return candidate
    return None


def _compose_services(compose: Path | None) -> set[str]:
    if compose is None:
        return set()
    text = compose.read_text(  # lgtm[py/path-injection]
        encoding="utf-8", errors="replace"
    )
    services: set[str] = set()
    in_services = False
    base_indent = 0
    service_indent: int | None = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if re.fullmatch(r"services\s*:\s*", line.strip()):
            in_services = True
            base_indent = indent
            continue
        if in_services and indent <= base_indent:
            break
        if in_services and service_indent is None:
            service_indent = indent
        if in_services and indent == service_indent:
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)\s*:\s*", line.strip())
            if match:
                services.add(match.group(1))
    return services


def _compose_project_name(value: object, root: Path) -> str:
    raw = str(value or f"ann-{root.name}").lower()
    cleaned = re.sub(r"[^a-z0-9_-]", "-", raw).strip("-_")[:48]
    if not cleaned:
        raise ValueError("invalid_compose_project_name")
    return cleaned


def _compose_prefix(root: Path, compose: Path, project_name: str, workspace: Path) -> list[str]:
    override = workspace / "compose.ann-internal.yaml"
    _write_text(
        override,
        "networks:\n  default:\n    internal: true\n",
        workspace,
    )
    return [
        "docker",
        "compose",
        "-p",
        project_name,
        "-f",
        str(compose.relative_to(root)),
        "-f",
        str(override),
    ]


def _compose_isolation_findings(compose: Path) -> list[str]:
    text = compose.read_text(  # lgtm[py/path-injection]
        encoding="utf-8", errors="replace"
    )
    findings = []
    patterns = {
        "fixed_container_name": r"(?im)^\s*container_name\s*:",
        "host_network": r"(?im)^\s*network_mode\s*:\s*['\"]?host['\"]?\s*$",
        "host_pid": r"(?im)^\s*pid\s*:\s*['\"]?host['\"]?\s*$",
        "host_ipc": r"(?im)^\s*ipc\s*:\s*['\"]?host['\"]?\s*$",
        "privileged_container": r"(?im)^\s*privileged\s*:\s*true\s*$",
        "docker_socket_mount": r"(?im)/var/run/docker\.sock",
        "loopback_host_ports": r"(?im)^\s*-\s*['\"]?127\.0\.0\.1:\d{2,5}:\d{2,5}(?:/(?:tcp|udp))?['\"]?\s*$",
        "public_host_ports": r"(?im)^\s*-\s*['\"]?\d{2,5}:\d{2,5}(?:/(?:tcp|udp))?['\"]?\s*$",
    }
    for finding, pattern in patterns.items():
        if re.search(pattern, text):
            findings.append(finding)
    return sorted(findings)


def _compose_execution_blockers(compose: Path) -> list[str]:
    blocked = {
        "docker_socket_mount",
        "fixed_container_name",
        "host_ipc",
        "host_network",
        "host_pid",
        "privileged_container",
    }
    return sorted(finding for finding in _compose_isolation_findings(compose) if finding in blocked)


def _openapi_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    for path in root.rglob("openapi.*"):
        if path.suffix.lower() == ".json":
            payload = _read_json(path)
            values = payload.get("paths", {}) if isinstance(payload, dict) else {}
            if isinstance(values, dict):
                paths.update(str(item) for item in values)
        elif path.suffix.lower() in {".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            paths.update(re.findall(r"(?m)^\s{2}(/[^:]+):\s*$", text))
    return paths


def _backend_route_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    pattern = re.compile(
        r"@(?:router|app)\.(?:get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)"
    )
    for path in root.rglob("*.py"):
        if any(
            part.lower() in PROTECTED_PARTS | {".venv", "venv"}
            for part in path.relative_to(root).parts
        ):
            continue
        paths.update(pattern.findall(path.read_text(encoding="utf-8", errors="replace")))
    return paths


def _frontend_api_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    pattern = re.compile(r"(?:fetch|request)\s*(?:<[^>]+>)?\s*\(\s*[`'\"](/[^`'\"$?]+)")
    for suffix in ("*.ts", "*.tsx", "*.js", "*.jsx"):
        for path in root.rglob(suffix):
            if "node_modules" in path.parts:
                continue
            paths.update(pattern.findall(path.read_text(encoding="utf-8", errors="replace")))
    return paths


def _contract_test_files(root: Path) -> list[str]:
    matches = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(
            part.lower() in PROTECTED_PARTS | {"node_modules", ".venv", "venv"}
            for part in relative.parts
        ):
            continue
        name = path.name.lower()
        normalized = relative.as_posix().lower()
        if any(marker in name for marker in ("contract", "openapi", "webhook")) and any(
            marker in normalized for marker in ("test", "spec")
        ):
            matches.append(relative.as_posix())
    return sorted(matches)[:500]


def _webhook_security_evidence(root: Path, webhook_paths: list[str]) -> dict[str, object]:
    if not webhook_paths:
        return {"required": False, "signature_validation_detected": False, "evidence_files": []}
    evidence = []
    pattern = re.compile(
        r"(?i)(verify[_-]?(?:signature|webhook)|construct_event|webhook[_-]?secret|hmac\.)"
    )
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
            continue
        relative = path.relative_to(root)
        if any(
            part.lower() in PROTECTED_PARTS | {"node_modules", ".venv", "venv"}
            for part in relative.parts
        ):
            continue
        if path.stat().st_size > 512_000:
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
            evidence.append(relative.as_posix())
    return {
        "required": True,
        "signature_validation_detected": bool(evidence),
        "evidence_files": sorted(evidence)[:100],
    }


def _release_input_files(root: Path, max_files: int) -> list[Path]:
    excluded = PROTECTED_PARTS | {
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        "outputs",
        "logs",
        "data",
    }
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if len(files) >= max_files:
            break
        if path.is_file() and not any(
            part.lower() in excluded for part in path.relative_to(root).parts
        ):
            files.append(path)
    return files


def _build_sbom(root: Path) -> dict[str, object]:
    components = []
    requirements = root / "requirements.txt"
    if requirements.is_file():
        for line in requirements.read_text(encoding="utf-8", errors="replace").splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                name = re.split(r"[<>=!~\[]", value, maxsplit=1)[0]
                components.append(
                    {"type": "library", "name": name, "version_spec": value[len(name) :]}
                )
    package = _read_json(root / "package.json")
    for group in ("dependencies", "devDependencies"):
        values = package.get(group, {}) if isinstance(package, dict) else {}
        if isinstance(values, dict):
            components.extend(
                {"type": "library", "name": str(name), "version_spec": str(version), "scope": group}
                for name, version in sorted(values.items())
            )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {"timestamp": _now(), "component": {"type": "application", "name": root.name}},
        "components": components,
    }


def _verify_release_manifest(manifest: dict[str, Any]) -> dict[str, object]:
    errors: list[str] = []
    archive = Path(str(manifest.get("archive") or ""))
    if not archive.is_file():
        errors.append("archive_missing")
    elif manifest.get("archive_sha256") != _sha256(archive):
        errors.append("archive_hash_mismatch")
    if archive.is_file() and "archive_hash_mismatch" not in errors:
        try:
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                if len(names) != len(set(names)):
                    errors.append("archive_duplicate_entries")
                if any(_unsafe_archive_name(name) for name in names):
                    errors.append("archive_path_traversal")
                for item in manifest.get("files", []):
                    if not isinstance(item, dict):
                        errors.append("manifest_file_entry_invalid")
                        continue
                    name = str(item.get("path") or "")
                    expected = str(item.get("sha256") or "")
                    if name not in names:
                        errors.append(f"archive_file_missing:{name}")
                    elif hashlib.sha256(bundle.read(name)).hexdigest() != expected:
                        errors.append(f"archive_file_hash_mismatch:{name}")
                _verify_zip_evidence(
                    bundle,
                    "release-evidence/sbom.cdx.json",
                    str(manifest.get("sbom_sha256") or ""),
                    "sbom",
                    errors,
                )
                _verify_zip_evidence(
                    bundle,
                    "release-evidence/rollback_manifest.json",
                    str(manifest.get("rollback_manifest_sha256") or ""),
                    "rollback_manifest",
                    errors,
                )
                installer_name = str(manifest.get("installer_archive_path") or "")
                installer_hash = str(manifest.get("installer_sha256") or "")
                if not manifest.get("installer_exists") or installer_name not in names:
                    errors.append("installer_missing")
                elif hashlib.sha256(bundle.read(installer_name)).hexdigest() != installer_hash:
                    errors.append("installer_hash_mismatch")
        except (OSError, zipfile.BadZipFile, KeyError) as exc:
            errors.append(f"archive_invalid:{type(exc).__name__}")
    preserve = (
        manifest.get("rollback", {}).get("preserve", [])
        if isinstance(manifest.get("rollback"), dict)
        else []
    )
    if not {"projects", "models", "outputs"}.issubset(set(preserve)):
        errors.append("rollback_policy_incomplete")
    return {"valid": not errors, "errors": errors, "archive": str(archive)}


def _unsafe_archive_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    return (
        not normalized
        or normalized.startswith("/")
        or bool(re.match(r"(?i)^[a-z]:/", normalized))
        or ".." in normalized.split("/")
    )


def _verify_zip_evidence(
    bundle: zipfile.ZipFile,
    name: str,
    expected_hash: str,
    label: str,
    errors: list[str],
) -> None:
    if name not in bundle.namelist():
        errors.append(f"{label}_missing")
    elif not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        errors.append(f"{label}_hash_invalid")
    elif hashlib.sha256(bundle.read(name)).hexdigest() != expected_hash:
        errors.append(f"{label}_hash_mismatch")


def _aggregate_recipe_status(results: list[RecipeResult]) -> str:
    if not results:
        return "SKIPPED"
    if any(item.status == "TIMEOUT" for item in results):
        return "TIMEOUT"
    if any(item.status != "SUCCESS" for item in results):
        return "FAILED"
    return "SUCCESS"


def _recipe_artifacts(results: list[RecipeResult]) -> list[str]:
    return [path for item in results for path in (item.stdout_path, item.stderr_path)]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, value: object, workspace: Path) -> None:
    validate_workspace_path(path, workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _write_text(path: Path, value: str, workspace: Path) -> None:
    validate_workspace_path(path, workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _write_summary(path: Path, result: dict[str, Any], workspace: Path) -> None:
    lines = [
        "# Engineering Skill Result",
        "",
        f"Skill: {result['skill']}",
        f"Action: {result['action']}",
        f"Status: {result['status']}",
        f"Summary: {result['summary']}",
        "",
        "## Safety",
        f"- Terminal used: {result['terminal_used']}",
        f"- Internet used: {result['internet_used']}",
        f"- Dependency install used: {result['dependency_install_used']}",
        "- shell=True: false",
        "",
    ]
    _write_text(path, "\n".join(lines), workspace)


def _bounded_int(value: object, minimum: int, maximum: int, default: int) -> int:
    try:
        parsed = int(value) if isinstance(value, (str, bytes, bytearray, int, float)) else default
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _bounded_text(value: object, limit: int = MAX_CAPTURE) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = str(value)
    return text[:limit]


def _string_list(value: object, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_bounded_text(item, 1_000).strip() for item in value[:limit] if str(item).strip()]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    # Callers supply either a _project_file-validated path or an artifact path
    # created inside the validated skill workspace.
    with path.open("rb") as handle:  # lgtm[py/path-injection]
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
