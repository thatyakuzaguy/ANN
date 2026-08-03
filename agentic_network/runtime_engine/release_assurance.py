"""Deterministic external assurance gate for ANN public releases.

Technical release checks cannot prove that independent review or prolonged
validation happened. This module validates operator-supplied evidence without
executing commands, loading models, contacting the network, or trusting marker
files that do not satisfy the configured contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = REPO_ROOT / "config" / "release-assurance-policy.json"
EVIDENCE_FILES = {
    "hardware_matrix": "hardware_matrix.json",
    "soak_validation": "soak_validation.json",
    "independent_security_review": "independent_security_review.json",
    "legal_review": "legal_review.json",
    "model_license_review": "model_license_review.json",
    "generated_software_acceptance": "generated_software_acceptance.json",
}
PASS_DECISIONS = {"PASSED", "APPROVED", "APPROVED_WITH_LIMITATIONS"}


def build_release_assurance_report(
    evidence_root: str | Path,
    *,
    policy_path: str | Path = DEFAULT_POLICY_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate externally collected release evidence without side effects."""

    root = Path(evidence_root).resolve()
    policy_file = Path(policy_path).resolve()
    policy, policy_error = _load_json(policy_file)
    checks: list[dict[str, Any]] = []
    records: dict[str, Any] = {}
    if policy_error:
        checks.append(_check("assurance_policy", False, policy_error))
        policy = {}
    else:
        checks.append(
            _check(
                "assurance_policy",
                policy.get("schema_version") == 1,
                "valid" if policy.get("schema_version") == 1 else "unsupported_schema_version",
            )
        )

    validators: dict[str, Callable[[dict[str, Any], dict[str, Any]], tuple[bool, str]]] = {
        "hardware_matrix": _validate_hardware_matrix,
        "soak_validation": _validate_soak,
        "independent_security_review": _validate_security_review,
        "legal_review": _validate_legal_review,
        "model_license_review": _validate_model_licenses,
        "generated_software_acceptance": _validate_human_acceptance,
    }
    current = now or datetime.now(timezone.utc)
    max_age_days = _positive_int(policy.get("max_evidence_age_days"), 180)
    for evidence_type, filename in EVIDENCE_FILES.items():
        path = root / filename
        path_allowed = _is_within(path.resolve(), root)
        payload, error = _load_json(path) if path_allowed else ({}, "evidence_path_outside_root")
        if error:
            checks.append(_check(evidence_type, False, error))
            records[evidence_type] = {"path": str(path), "status": "MISSING_OR_INVALID"}
            continue
        common_passed, common_detail = _validate_common_evidence(
            payload,
            evidence_type=evidence_type,
            evidence_root=root,
            current=current,
            max_age_days=max_age_days,
        )
        category_passed, category_detail = validators[evidence_type](payload, policy)
        passed = common_passed and category_passed
        detail = "valid" if passed else "; ".join(
            item for item in (common_detail, category_detail) if item and item != "valid"
        )
        checks.append(_check(evidence_type, passed, detail or "invalid"))
        records[evidence_type] = {
            "path": str(path),
            "status": "VERIFIED" if passed else "REJECTED",
            "sha256": _sha256_file(path),
            "collected_at": payload.get("collected_at"),
            "detail": detail,
        }

    blockers = [item for item in checks if not item["passed"]]
    evidence_found = sum((root / filename).is_file() for filename in EVIDENCE_FILES.values())
    if not blockers:
        status = "PRODUCTION_ASSURANCE_READY"
    elif evidence_found:
        status = "PRODUCTION_ASSURANCE_PARTIAL"
    else:
        status = "PRODUCTION_ASSURANCE_BLOCKED"
    return {
        "schema_version": 1,
        "status": status,
        "ready": status == "PRODUCTION_ASSURANCE_READY",
        "exit_code": 0 if status == "PRODUCTION_ASSURANCE_READY" else 2,
        "evidence_root": str(root),
        "policy_path": str(policy_file),
        "checks": checks,
        "blockers": blockers,
        "evidence": records,
        "evidence_files_found": evidence_found,
        "evidence_files_required": len(EVIDENCE_FILES),
        "next_step": _next_step(blockers),
        "claims": {
            "legal_compliance_guaranteed": False,
            "security_guaranteed": False,
            "automatic_sellability_guaranteed": False,
            "external_work_fabricated": False,
        },
        "safety": {
            "read_only": True,
            "network_used": False,
            "downloads_performed": False,
            "installs_performed": False,
            "model_load_performed": False,
            "inference_performed": False,
            "shell_used": False,
        },
    }


def write_release_assurance_templates(output_dir: str | Path) -> list[str]:
    """Write explicitly pending templates; they can never pass verification."""

    target = Path(output_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    templates = _templates()
    paths: list[str] = []
    for evidence_type, filename in EVIDENCE_FILES.items():
        path = target / filename
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite release evidence: {path}")
        path.write_text(json.dumps(templates[evidence_type], indent=2) + "\n", encoding="utf-8")
        paths.append(str(path))
    return paths


def write_release_assurance_artifacts(report: dict[str, Any], output_dir: str | Path) -> list[str]:
    target = Path(output_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "374_release_assurance_verification.json"
    markdown_path = target / "375_release_assurance_verification.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# ANN Release Assurance Verification",
        "",
        f"Status: `{report['status']}`",
        f"Evidence: `{report['evidence_files_found']}/{report['evidence_files_required']}`",
        f"Next step: {report['next_step']}",
        "",
        "## Checks",
        "",
    ]
    lines.extend(
        f"- `{item['id']}`: `{item['status']}` - {item['detail']}" for item in report["checks"]
    )
    lines.extend(
        [
            "",
            "This verifier does not guarantee legal compliance, security, market success, or generated-software correctness.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return [str(json_path), str(markdown_path)]


def _validate_common_evidence(
    payload: dict[str, Any],
    *,
    evidence_type: str,
    evidence_root: Path,
    current: datetime,
    max_age_days: int,
) -> tuple[bool, str]:
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("unsupported_schema_version")
    if payload.get("evidence_type") != evidence_type:
        errors.append("evidence_type_mismatch")
    collected = _parse_datetime(payload.get("collected_at"))
    if collected is None:
        errors.append("collected_at_invalid")
    elif collected > current:
        errors.append("collected_at_in_future")
    elif (current - collected).days > max_age_days:
        errors.append("evidence_expired")
    report_path = payload.get("report_path")
    report_hash = str(payload.get("report_sha256", "")).lower()
    resolved, path_error = _resolve_evidence_path(evidence_root, report_path)
    if path_error:
        errors.append(path_error)
    elif resolved is None or not resolved.is_file():
        errors.append("report_missing")
    elif not _is_sha256(report_hash) or _sha256_file(resolved) != report_hash:
        errors.append("report_hash_mismatch")
    return not errors, "; ".join(errors) if errors else "valid"


def _validate_hardware_matrix(payload: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, str]:
    rules = _dict(policy.get("hardware_matrix"))
    machines = _dict_list(payload.get("machines"))
    min_machines = _positive_int(rules.get("minimum_machines"), 2)
    min_gpus = _positive_int(rules.get("minimum_distinct_gpu_profiles"), 2)
    identities = {str(item.get("machine_id", "")).strip() for item in machines}
    gpu_profiles = {
        f"{item.get('gpu_vendor', '')}:{item.get('gpu_model', '')}".strip(": ").lower()
        for item in machines
        if item.get("gpu_model")
    }
    valid_machine = all(
        str(item.get("os", "")).lower().startswith("windows 11")
        and item.get("clean_install") is True
        and item.get("installer_status") == "PASSED"
        and item.get("uninstaller_status") == "PASSED"
        and item.get("inference_status") == "PASSED"
        and item.get("project_smoke_status") == "PASSED"
        for item in machines
    )
    errors = []
    if len(machines) < min_machines or len(identities) != len(machines) or "" in identities:
        errors.append(f"minimum_unique_machines:{min_machines}")
    if len(gpu_profiles) < min_gpus:
        errors.append(f"minimum_distinct_gpu_profiles:{min_gpus}")
    if machines and not valid_machine:
        errors.append("machine_gate_failed")
    return not errors, "; ".join(errors) if errors else "valid"


def _validate_soak(payload: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, str]:
    rules = _dict(policy.get("soak_validation"))
    duration = _number(payload.get("duration_hours"))
    attempted = _integer(payload.get("attempted_runs"))
    successful = _integer(payload.get("successful_runs"))
    failed = _integer(payload.get("failed_runs"))
    archetypes = {str(item).strip() for item in _list(payload.get("project_archetypes")) if str(item).strip()}
    errors = []
    if duration < _number(rules.get("minimum_duration_hours"), 8.0):
        errors.append("duration_below_policy")
    if attempted < _positive_int(rules.get("minimum_attempted_runs"), 20):
        errors.append("attempted_runs_below_policy")
    if successful + failed != attempted:
        errors.append("run_totals_inconsistent")
    max_failure_rate = _number(rules.get("maximum_failure_rate"), 0.02)
    if attempted <= 0 or failed / attempted > max_failure_rate:
        errors.append("failure_rate_above_policy")
    if len(archetypes) < _positive_int(rules.get("minimum_project_archetypes"), 3):
        errors.append("project_archetypes_below_policy")
    if payload.get("active_models_peak") != 1 or payload.get("parallel_llm_loads_peak") != 0:
        errors.append("sequential_runtime_invariant_failed")
    if payload.get("models_loaded_after") != 0 or payload.get("rollback_status") != "PASSED":
        errors.append("rollback_invariant_failed")
    return not errors, "; ".join(errors) if errors else "valid"


def _validate_security_review(payload: dict[str, Any], _policy: dict[str, Any]) -> tuple[bool, str]:
    errors = []
    if payload.get("independent") is not True or not str(payload.get("reviewer", "")).strip():
        errors.append("independent_reviewer_missing")
    if payload.get("decision") not in PASS_DECISIONS:
        errors.append("security_decision_not_approved")
    if not _is_non_negative_int(payload.get("open_critical_findings")):
        errors.append("open_critical_findings_invalid")
    elif _integer(payload.get("open_critical_findings")) != 0:
        errors.append("open_critical_findings")
    if not _is_non_negative_int(payload.get("open_high_findings")):
        errors.append("open_high_findings_invalid")
    elif _integer(payload.get("open_high_findings")) != 0:
        errors.append("open_high_findings")
    return not errors, "; ".join(errors) if errors else "valid"


def _validate_legal_review(payload: dict[str, Any], _policy: dict[str, Any]) -> tuple[bool, str]:
    required_scope = {"distribution", "privacy", "model_licensing", "terms"}
    scope = {str(item).strip().lower() for item in _list(payload.get("scope"))}
    errors = []
    if payload.get("human_review") is not True or not str(payload.get("reviewer", "")).strip():
        errors.append("qualified_human_review_missing")
    if payload.get("decision") not in {"APPROVED", "APPROVED_WITH_LIMITATIONS"}:
        errors.append("legal_decision_not_approved")
    if not required_scope.issubset(scope):
        errors.append("legal_scope_incomplete")
    if payload.get("compliance_guaranteed") is not False:
        errors.append("invalid_compliance_guarantee")
    return not errors, "; ".join(errors) if errors else "valid"


def _validate_model_licenses(payload: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, str]:
    records = _dict_list(payload.get("models"))
    required = {str(item) for item in _list(policy.get("required_model_ids"))}
    by_id = {str(item.get("model_id", "")): item for item in records}
    errors = []
    missing = sorted(required - set(by_id))
    if missing:
        errors.append("missing_models:" + ",".join(missing))
    for model_id in sorted(required & set(by_id)):
        item = by_id[model_id]
        valid = (
            bool(str(item.get("license_name", "")).strip())
            and str(item.get("license_source", "")).strip().lower().startswith("https://")
            and bool(str(item.get("reviewed_by", "")).strip())
            and item.get("decision") in {"APPROVED", "USER_SUPPLIED_ONLY"}
            and item.get("weights_in_public_repository") is False
            and item.get("distribution_mode") in {"user_supplied", "separate_licensed_pack"}
        )
        if not valid:
            errors.append(f"model_license_invalid:{model_id}")
    return not errors, "; ".join(errors) if errors else "valid"


def _validate_human_acceptance(payload: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, str]:
    projects = _dict_list(payload.get("projects"))
    rules = _dict(policy.get("generated_software_acceptance"))
    min_projects = _positive_int(rules.get("minimum_projects"), 3)
    min_archetypes = _positive_int(rules.get("minimum_archetypes"), 3)
    archetypes = {str(item.get("archetype", "")).strip() for item in projects if item.get("archetype")}
    errors = []
    if len(projects) < min_projects:
        errors.append("accepted_projects_below_policy")
    if len(archetypes) < min_archetypes:
        errors.append("accepted_archetypes_below_policy")
    if projects and not all(
        item.get("decision") == "ACCEPTED"
        and item.get("human_review") is True
        and bool(str(item.get("reviewer", "")).strip())
        and item.get("build_status") == "PASSED"
        and item.get("test_status") == "PASSED"
        and item.get("security_status") in {"PASSED", "APPROVED_WITH_LIMITATIONS"}
        for item in projects
    ):
        errors.append("project_acceptance_gate_failed")
    return not errors, "; ".join(errors) if errors else "valid"


def _templates() -> dict[str, dict[str, Any]]:
    common = {
        "schema_version": 1,
        "collected_at": "REPLACE_WITH_UTC_ISO_8601",
        "report_path": "REPLACE_WITH_RELATIVE_REPORT_PATH",
        "report_sha256": "REPLACE_WITH_64_CHARACTER_SHA256",
        "decision": "PENDING",
    }
    return {
        "hardware_matrix": {**common, "evidence_type": "hardware_matrix", "machines": []},
        "soak_validation": {
            **common,
            "evidence_type": "soak_validation",
            "duration_hours": 0,
            "attempted_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "project_archetypes": [],
            "active_models_peak": 0,
            "parallel_llm_loads_peak": 0,
            "models_loaded_after": 0,
            "rollback_status": "PENDING",
        },
        "independent_security_review": {
            **common,
            "evidence_type": "independent_security_review",
            "independent": False,
            "reviewer": "",
            "organization": "",
            "open_critical_findings": 0,
            "open_high_findings": 0,
        },
        "legal_review": {
            **common,
            "evidence_type": "legal_review",
            "human_review": False,
            "reviewer": "",
            "scope": [],
            "compliance_guaranteed": False,
        },
        "model_license_review": {**common, "evidence_type": "model_license_review", "models": []},
        "generated_software_acceptance": {
            **common,
            "evidence_type": "generated_software_acceptance",
            "projects": [],
        },
    }


def _check(identifier: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": identifier, "passed": passed, "status": "PASS" if passed else "BLOCKED", "detail": detail}


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        if path.stat().st_size > 10 * 1024 * 1024:
            return {}, "evidence_file_too_large"
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "evidence_file_missing"
    except (OSError, json.JSONDecodeError):
        return {}, "evidence_file_invalid"
    return (value, "") if isinstance(value, dict) else ({}, "evidence_root_must_be_object")


def _resolve_evidence_path(root: Path, value: object) -> tuple[Path | None, str]:
    if not isinstance(value, str) or not value.strip():
        return None, "report_path_missing"
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None, "report_path_outside_evidence_root"
    resolved = (root / candidate).resolve()
    if not _is_within(resolved, root):
        return None, "report_path_outside_evidence_root"
    return resolved, ""


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict_list(value: object) -> list[dict[str, Any]]:
    return [item for item in _list(value) if isinstance(item, dict)]


def _integer(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _positive_int(value: object, default: int) -> int:
    parsed = _integer(value)
    return parsed if parsed > 0 else default


def _number(value: object, default: float = 0.0) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return default
    parsed = float(value)
    return parsed if math.isfinite(parsed) else default


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _next_step(blockers: list[dict[str, Any]]) -> str:
    if not blockers:
        return "Preserve the verified assurance bundle with the release artifacts."
    first = blockers[0]
    return f"Resolve {first['id']}: {first['detail']}."
