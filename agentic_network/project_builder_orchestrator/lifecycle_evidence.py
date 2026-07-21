"""Compile immutable project-lifecycle results into capability evidence artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


REQUIRED_LIVE_VERIFICATION_STEPS = frozenset(
    {
        "api_dependency_audit_live",
        "api_dependency_integrity_live",
        "api_health_live",
        "api_pytest_live",
        "docker_compose_build",
        "docker_compose_up",
        "web_build_live",
        "web_dependency_audit_live",
        "web_e2e_live",
        "web_health_live",
        "web_unit_live",
    }
)
REQUIRED_ALGORITHM_VERIFICATION_STEPS = frozenset(
    {
        "algorithm_benchmark_live",
        "algorithm_integration_live",
        "api_dependency_audit_live",
        "api_dependency_integrity_live",
        "api_health_live",
        "api_pytest_live",
        "docker_compose_build",
        "docker_compose_up",
    }
)
SECURITY_STEPS = frozenset(
    {
        "api_dependency_audit_live",
        "api_dependency_integrity_live",
        "security_review",
        "web_dependency_audit_live",
    }
)
FUNCTIONAL_STEPS = frozenset(
    {
        "api_health_live",
        "api_pytest_live",
        "web_build_live",
        "web_e2e_live",
        "web_health_live",
        "web_unit_live",
    }
)


def compile_lifecycle_evidence(
    project_root: str | Path,
    lifecycle_result_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Write evidence derived only from an existing real lifecycle result."""

    root = Path(project_root).resolve()
    result_path = Path(lifecycle_result_path or root / ".aen" / "real-lifecycle-result.json").resolve()
    evidence_dir = Path(output_dir or root / ".aen" / "evidence").resolve()
    _require_inside(root, result_path)
    _require_inside(root, evidence_dir)
    result = _read_json(result_path)
    raw_steps = result.get("steps")
    steps = [step for step in raw_steps if isinstance(step, dict)] if isinstance(raw_steps, list) else []
    by_name = {str(step.get("name", "")): step for step in steps if step.get("name")}
    profile = str(result.get("profile") or "full_stack")
    required_steps = (
        REQUIRED_ALGORITHM_VERIFICATION_STEPS if profile == "algorithm_service" else REQUIRED_LIVE_VERIFICATION_STEPS
    )
    security_steps = (
        SECURITY_STEPS.difference({"web_dependency_audit_live"}) if profile == "algorithm_service" else SECURITY_STEPS
    )
    functional_steps = (
        frozenset({"algorithm_benchmark_live", "algorithm_integration_live", "api_health_live", "api_pytest_live"})
        if profile == "algorithm_service"
        else FUNCTIONAL_STEPS
    )

    evidence_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = evidence_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    stdout_artifacts: list[str] = []
    commands: list[list[str]] = []
    exit_codes: list[int] = []
    for index, step in enumerate(steps, start=1):
        detail = str(step.get("detail") or "").strip()
        if detail:
            name = _safe_name(str(step.get("name") or f"step-{index}"))
            log_path = logs_dir / f"{index:02d}-{name}.log"
            log_path.write_text(detail + "\n", encoding="utf-8")
            stdout_artifacts.append(str(log_path))
        command = step.get("command")
        if isinstance(command, list) and command and all(isinstance(part, str) for part in command):
            commands.append(command)
            exit_codes.append(0 if step.get("status") == "passed" else 1)

    missing = sorted(required_steps.difference(by_name))
    failed_required = sorted(name for name in required_steps if by_name.get(name, {}).get("status") != "passed")
    verification_passed = (
        result.get("status") == "passed"
        and not missing
        and not failed_required
        and bool(commands)
        and bool(stdout_artifacts)
        and all(code == 0 for code in exit_codes)
    )
    verification = {
        "status": "PASSED" if verification_passed else "FAILED",
        "source": str(result_path),
        "source_status": result.get("status", "missing"),
        "commands_executed": commands,
        "exit_codes": exit_codes,
        "stdout_artifacts": stdout_artifacts,
        "profile": profile,
        "required_steps": sorted(required_steps),
        "missing_steps": missing,
        "failed_required_steps": failed_required,
        "compiled_at": datetime.now(timezone.utc).isoformat(),
    }

    static_security = _security_payload(by_name.get("security_review", {}))
    security_failed = sorted(name for name in security_steps if by_name.get(name, {}).get("status") != "passed")
    findings = static_security.get("findings", [])
    severe = [
        finding
        for finding in findings
        if isinstance(finding, dict) and str(finding.get("severity", "")).upper() in {"HIGH", "CRITICAL"}
    ]
    security_passed = not security_failed and not severe and static_security.get("passed") is True
    security = {
        "status": "PASSED" if security_passed else "FAILED",
        "scanners": ["ann-static-security-review", "pip-check", "pip-audit", "npm-audit"],
        "checks": [
            {"name": name, "passed": by_name.get(name, {}).get("status") == "passed"}
            for name in sorted(security_steps)
        ],
        "findings": findings if isinstance(findings, list) else [],
        "notes": static_security.get("notes", []),
        "failed_steps": security_failed,
        "source": str(result_path),
    }

    screenshots = sorted(
        str(path.resolve())
        for base in (root / "apps" / "web" / "test-results", root / "apps" / "web" / "playwright-report")
        if base.is_dir()
        for path in base.rglob("*.png")
        if path.is_file() and path.stat().st_size >= 100
    )
    functional_checks = [
        {
            "name": name,
            "passed": by_name.get(name, {}).get("status") == "passed",
            "log": _log_for_step(stdout_artifacts, name),
        }
        for name in sorted(functional_steps)
    ]
    functional_passed = all(check["passed"] for check in functional_checks) and (
        profile == "algorithm_service" or bool(screenshots)
    )
    functional = {
        "status": "PASSED" if functional_passed else "FAILED",
        "checks": functional_checks,
        "screenshots": screenshots,
        "source": str(result_path),
    }

    paths = {
        "verification": evidence_dir / "47_project_verification.json",
        "verification_markdown": evidence_dir / "47_project_verification.md",
        "security": evidence_dir / "security_review.json",
        "functional": evidence_dir / "functional_smoke.json",
    }
    _write_json(paths["verification"], verification)
    _write_json(paths["security"], security)
    _write_json(paths["functional"], functional)
    paths["verification_markdown"].write_text(_verification_markdown(verification, security, functional), encoding="utf-8")
    return {
        "status": "PASSED" if verification_passed and security_passed and functional_passed else "FAILED",
        "artifacts": [str(path) for path in paths.values()],
        "verification": verification,
        "security": security,
        "functional_smoke": functional,
    }


def write_lifecycle_capability_summary(
    scenario_id: str,
    project_root: str | Path,
    summary_dir: str | Path,
    *,
    allowed_workspace_root: str | Path,
    lifecycle_result_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compile a lifecycle and publish a gate-compatible scenario summary."""

    from agentic_network.project_builder_orchestrator.capability_evidence import evaluate_project_capability

    root = Path(project_root).resolve()
    workspace = Path(allowed_workspace_root).resolve()
    _require_inside(workspace, root)
    compiled = compile_lifecycle_evidence(root, lifecycle_result_path)
    evidence = compiled["verification"]
    artifacts = [*compiled["artifacts"]]
    for candidate in (
        root / ".aen" / "real-lifecycle-result.json",
        root / "docs" / "SPEC.md",
        root / "docs" / "ARCHITECTURE.md",
    ):
        if candidate.is_file():
            artifacts.append(str(candidate.resolve()))
    summary: dict[str, Any] = {
        "scenario_id": scenario_id,
        "status": "BLOCKED",
        "completion_quality": "UNVERIFIED",
        "project_root": str(root),
        "generated_project_path": str(root),
        "artifacts": list(dict.fromkeys(artifacts)),
        "commands_executed": evidence["commands_executed"],
        "verification_evidence": {
            "evidence_level": "STRONG" if compiled["status"] == "PASSED" else "INSUFFICIENT",
            "source": evidence["source"],
            "logs": evidence["stdout_artifacts"],
            "screenshots": compiled["functional_smoke"]["screenshots"],
        },
        "security_review": compiled["security"]["status"],
        "protected_paths_modified": False,
        "write_boundary": str(workspace),
        "compiled_evidence_status": compiled["status"],
    }
    capability = evaluate_project_capability(scenario_id, summary)
    summary["capability_assessment"] = capability
    if compiled["status"] == "PASSED" and capability["passed"]:
        summary["status"] = "COMPLETED_VERIFIED"
        summary["completion_quality"] = "VERIFIED"
    target = Path(summary_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    summary_path = target / "summary.json"
    _write_json(summary_path, summary)
    return {**summary, "summary_path": str(summary_path)}


def _security_payload(step: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(str(step.get("detail") or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-") or "step"


def _log_for_step(logs: list[str], step_name: str) -> str:
    suffix = f"-{_safe_name(step_name)}.log"
    return next((path for path in logs if path.endswith(suffix)), "")


def _require_inside(root: Path, path: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Evidence path must stay inside project root {root}: {path}") from exc


def _verification_markdown(
    verification: dict[str, Any], security: dict[str, Any], functional: dict[str, Any]
) -> str:
    return "\n".join(
        [
            "# Real Project Verification Evidence",
            "",
            f"- Lifecycle verification: **{verification['status']}**",
            f"- Security: **{security['status']}**",
            f"- Functional smoke: **{functional['status']}**",
            f"- Commands captured: **{len(verification['commands_executed'])}**",
            f"- Logs captured: **{len(verification['stdout_artifacts'])}**",
            f"- Screenshots captured: **{len(functional['screenshots'])}**",
            "",
            "This report is compiled from the immutable lifecycle result and its captured command output.",
        ]
    ) + "\n"
