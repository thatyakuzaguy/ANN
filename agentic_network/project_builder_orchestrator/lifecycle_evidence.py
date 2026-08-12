"""Compile immutable project-lifecycle results into capability evidence artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
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
CAPABILITY_MANIFEST_FILES = frozenset(
    {
        "EVIDENCE_MANIFEST.json",
        "EVIDENCE_MANIFEST.sha256",
        "EVIDENCE_MANIFEST.md",
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
        command_status = str(step.get("status") or "").lower()
        if (
            command_status in {"passed", "failed"}
            and isinstance(command, list)
            and command
            and all(isinstance(part, str) for part in command)
        ):
            commands.append(command)
            exit_codes.append(0 if command_status == "passed" else 1)

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


def make_capability_evidence_portable(summary_path: str | Path) -> dict[str, Any]:
    """Rewrite derived evidence paths relative to its summary without touching lifecycle truth."""

    from agentic_network.project_builder_orchestrator.capability_evidence import evaluate_project_capability

    target = Path(summary_path).resolve()
    summary = _read_json(target)
    if not summary:
        raise ValueError(f"Capability summary is missing or invalid: {target}")
    base = target.parent
    packet_project_path = Path(str(summary.get("project_root") or ""))
    packet_project_root = (
        packet_project_path.resolve()
        if packet_project_path.is_absolute()
        else (base / packet_project_path).resolve()
    )
    verification_summary = summary.get("verification_evidence")
    summary_source_root = _source_project_root(
        verification_summary.get("source")
        if isinstance(verification_summary, dict)
        else None
    )
    original_artifacts = []
    for value in summary.get("artifacts", []):
        artifact = Path(str(value))
        original_artifacts.append(
            artifact.resolve() if artifact.is_absolute() else (base / artifact).resolve()
        )
    for artifact in original_artifacts:
        if not artifact.is_file() or artifact.name not in {
            "47_project_verification.json",
            "security_review.json",
            "functional_smoke.json",
        }:
            continue
        payload = _read_json(artifact)
        source_root = _source_project_root(payload.get("source")) or summary_source_root
        if artifact.name == "47_project_verification.json":
            payload["source"] = _portable_relocated_path(
                payload.get("source"), base, source_root, packet_project_root
            )
            payload["stdout_artifacts"] = _portable_relocated_paths(
                payload.get("stdout_artifacts"), base, source_root, packet_project_root
            )
        elif artifact.name == "security_review.json":
            payload["source"] = _portable_relocated_path(
                payload.get("source"), base, source_root, packet_project_root
            )
        else:
            payload["source"] = _portable_relocated_path(
                payload.get("source"), base, source_root, packet_project_root
            )
            payload["screenshots"] = _portable_relocated_paths(
                payload.get("screenshots"), base, source_root, packet_project_root
            )
            checks = payload.get("checks")
            if isinstance(checks, list):
                for check in checks:
                    if isinstance(check, dict) and check.get("log"):
                        check["log"] = _portable_relocated_path(
                            check["log"], base, source_root, packet_project_root
                        )
        _write_json(artifact, payload)

    for key in ("project_root", "generated_project_path", "write_boundary", "summary_path"):
        if summary.get(key):
            summary[key] = _portable_path(summary[key], base)
    summary["artifacts"] = _portable_paths(summary.get("artifacts"), base)
    verification = summary.get("verification_evidence")
    if isinstance(verification, dict):
        verification["source"] = _portable_relocated_path(
            verification.get("source"),
            base,
            summary_source_root,
            packet_project_root,
        )
        verification["logs"] = _portable_relocated_paths(
            verification.get("logs"),
            base,
            summary_source_root,
            packet_project_root,
        )
        verification["screenshots"] = _portable_relocated_paths(
            verification.get("screenshots"),
            base,
            summary_source_root,
            packet_project_root,
        )
    summary["portable_paths"] = True
    assessment = evaluate_project_capability(
        str(summary.get("scenario_id") or ""),
        summary,
        summary_path=target,
    )
    if assessment.get("project_root"):
        assessment["project_root"] = _portable_path(assessment["project_root"], base)
    assessment["visual_evidence"] = _portable_paths(
        assessment.get("visual_evidence"),
        base,
    )
    summary["capability_assessment"] = assessment
    _write_json(target, summary)
    markdown_path = target.with_suffix(".md")
    if markdown_path.is_file():
        markdown_path.write_text(_portable_summary_markdown(summary), encoding="utf-8")
    return summary


def build_capability_evidence_manifest(evidence_root: str | Path) -> dict[str, Any]:
    """Build a deterministic integrity manifest for a portable capability packet."""

    from agentic_network.project_builder_orchestrator.capability_evidence import evaluate_project_capability

    root = Path(evidence_root).resolve()
    if not root.is_dir():
        raise ValueError(f"Capability evidence root does not exist: {root}")
    files = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().lower()):
        if not path.is_file() or path.name in CAPABILITY_MANIFEST_FILES:
            continue
        relative_path = path.relative_to(root).as_posix()
        files.append(
            {
                "relative_path": relative_path,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )

    scenarios = []
    for summary_path in sorted(root.glob("*/summary.json"), key=lambda item: item.as_posix().lower()):
        summary = _read_json(summary_path)
        assessment = evaluate_project_capability(
            str(summary.get("scenario_id") or summary_path.parent.name),
            summary,
            summary_path=summary_path,
        )
        scenarios.append(
            {
                "scenario_id": str(summary.get("scenario_id") or summary_path.parent.name),
                "status": str(summary.get("status") or "MISSING"),
                "completion_quality": str(summary.get("completion_quality") or "MISSING"),
                "portable_paths": summary.get("portable_paths") is True,
                "capability_passed": isinstance(assessment, dict) and assessment.get("passed") is True,
                "summary_path": summary_path.relative_to(root).as_posix(),
                "summary_sha256": _sha256(summary_path),
            }
        )
    packet_ready = bool(scenarios) and all(
        scenario["status"] == "COMPLETED_VERIFIED"
        and scenario["completion_quality"] == "VERIFIED"
        and scenario["portable_paths"]
        and scenario["capability_passed"]
        for scenario in scenarios
    )
    canonical_payload = {"files": files, "scenarios": scenarios}
    aggregate_sha256 = hashlib.sha256(
        json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "ann.autonomous-capability-evidence.v1",
        "status": "PORTABLE_EVIDENCE_READY" if packet_ready else "PORTABLE_EVIDENCE_BLOCKED",
        "portable": packet_ready,
        "scenario_count": len(scenarios),
        "file_count": len(files),
        "total_size_bytes": sum(entry["size_bytes"] for entry in files),
        "aggregate_sha256": aggregate_sha256,
        "canonical_scope": "files(relative_path,size_bytes,sha256),scenarios",
        "scenarios": scenarios,
        "files": files,
    }


def write_capability_evidence_manifest(evidence_root: str | Path) -> dict[str, Any]:
    """Write the portable evidence manifest and independently verifiable sidecars."""

    root = Path(evidence_root).resolve()
    manifest = build_capability_evidence_manifest(root)
    manifest_path = root / "EVIDENCE_MANIFEST.json"
    _write_json(manifest_path, manifest)
    manifest_sha256 = _sha256(manifest_path)
    (root / "EVIDENCE_MANIFEST.sha256").write_text(
        f"{manifest_sha256}  EVIDENCE_MANIFEST.json\n",
        encoding="utf-8",
    )
    (root / "EVIDENCE_MANIFEST.md").write_text(
        "\n".join(
            [
                "# ANN Autonomous Capability Evidence",
                "",
                f"- Status: **{manifest['status']}**",
                f"- Scenarios: **{manifest['scenario_count']}**",
                f"- Files: **{manifest['file_count']}**",
                f"- Bytes: **{manifest['total_size_bytes']}**",
                f"- Aggregate SHA-256: `{manifest['aggregate_sha256']}`",
                f"- Manifest SHA-256: `{manifest_sha256}`",
                "",
                "Verification-relevant paths in project summaries are relative to this evidence packet. Original lifecycle records and command transcripts are preserved unchanged as provenance.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {**manifest, "manifest_sha256": manifest_sha256}


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _portable_path(value: Any, base: Path) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    path = Path(raw)
    if not path.is_absolute():
        return path.as_posix()
    return Path(os.path.relpath(path.resolve(), base)).as_posix()


def _portable_paths(values: Any, base: Path) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_portable_path(value, base) for value in values if str(value or "").strip()]


def _source_project_root(value: Any) -> Path | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    source = Path(raw)
    if not source.is_absolute():
        return None
    for parent in source.parents:
        if parent.name == ".aen":
            return parent.parent.resolve()
    return None


def _portable_relocated_path(
    value: Any,
    base: Path,
    source_root: Path | None,
    packet_root: Path,
) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    path = Path(raw)
    if path.is_absolute() and source_root is not None:
        try:
            path = packet_root / path.resolve().relative_to(source_root)
        except ValueError:
            pass
    return _portable_path(path, base)


def _portable_relocated_paths(
    values: Any,
    base: Path,
    source_root: Path | None,
    packet_root: Path,
) -> list[str]:
    if not isinstance(values, list):
        return []
    return [
        _portable_relocated_path(value, base, source_root, packet_root)
        for value in values
        if str(value or "").strip()
    ]


def _portable_summary_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {summary.get('scenario_id', 'scenario')}",
            "",
            f"- Status: {summary.get('status', 'UNKNOWN')}",
            f"- Completion quality: {summary.get('completion_quality', 'UNKNOWN')}",
            f"- Security review: {summary.get('security_review', 'UNKNOWN')}",
            f"- Commands executed: {len(summary.get('commands_executed', []))}",
            f"- Project root: {summary.get('project_root', '')}",
            f"- Next action: {summary.get('next_action', '')}",
            "",
        ]
    )


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
