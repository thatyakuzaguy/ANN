from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

from agentic_network.runtime_engine.release_assurance import (
    EVIDENCE_FILES,
    build_release_assurance_report,
    write_release_assurance_artifacts,
    write_release_assurance_templates,
)
from scripts.runtime import verify_release_assurance


NOW = datetime(2026, 8, 3, tzinfo=timezone.utc)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _policy(path: Path) -> Path:
    _write_json(
        path,
        {
            "schema_version": 1,
            "max_evidence_age_days": 180,
            "hardware_matrix": {"minimum_machines": 2, "minimum_distinct_gpu_profiles": 2},
            "soak_validation": {
                "minimum_duration_hours": 8,
                "minimum_attempted_runs": 20,
                "minimum_project_archetypes": 3,
                "maximum_failure_rate": 0.02,
            },
            "required_model_ids": ["code", "product", "review"],
            "generated_software_acceptance": {"minimum_projects": 3, "minimum_archetypes": 3},
        },
    )
    return path


def _common(root: Path, evidence_type: str) -> dict[str, object]:
    report = root / f"{evidence_type}.md"
    report.write_text(f"verified {evidence_type}\n", encoding="utf-8")
    digest = hashlib.sha256(report.read_bytes()).hexdigest()
    return {
        "schema_version": 1,
        "evidence_type": evidence_type,
        "collected_at": "2026-08-01T12:00:00Z",
        "report_path": report.name,
        "report_sha256": digest,
    }


def _ready_bundle(root: Path) -> Path:
    root.mkdir(parents=True)
    hardware = {
        **_common(root, "hardware_matrix"),
        "machines": [
            {
                "machine_id": "windows-rtx3060ti",
                "os": "Windows 11 23H2",
                "clean_install": True,
                "gpu_vendor": "NVIDIA",
                "gpu_model": "RTX 3060 Ti",
                "installer_status": "PASSED",
                "uninstaller_status": "PASSED",
                "inference_status": "PASSED",
                "project_smoke_status": "PASSED",
            },
            {
                "machine_id": "windows-rtx4070",
                "os": "Windows 11 24H2",
                "clean_install": True,
                "gpu_vendor": "NVIDIA",
                "gpu_model": "RTX 4070",
                "installer_status": "PASSED",
                "uninstaller_status": "PASSED",
                "inference_status": "PASSED",
                "project_smoke_status": "PASSED",
            },
        ],
    }
    soak = {
        **_common(root, "soak_validation"),
        "duration_hours": 12,
        "attempted_runs": 20,
        "successful_runs": 20,
        "failed_runs": 0,
        "project_archetypes": ["api", "web", "desktop"],
        "active_models_peak": 1,
        "parallel_llm_loads_peak": 0,
        "models_loaded_after": 0,
        "rollback_status": "PASSED",
    }
    security = {
        **_common(root, "independent_security_review"),
        "independent": True,
        "reviewer": "External Security Reviewer",
        "organization": "Independent Lab",
        "decision": "PASSED",
        "open_critical_findings": 0,
        "open_high_findings": 0,
    }
    legal = {
        **_common(root, "legal_review"),
        "human_review": True,
        "reviewer": "Qualified Counsel",
        "decision": "APPROVED_WITH_LIMITATIONS",
        "scope": ["distribution", "privacy", "model_licensing", "terms"],
        "compliance_guaranteed": False,
    }
    licenses = {
        **_common(root, "model_license_review"),
        "models": [
            {
                "model_id": model_id,
                "license_name": "reviewed upstream license",
                "license_source": f"https://example.invalid/{model_id}",
                "reviewed_by": "Qualified Counsel",
                "decision": "USER_SUPPLIED_ONLY",
                "weights_in_public_repository": False,
                "distribution_mode": "user_supplied",
            }
            for model_id in ("code", "product", "review")
        ],
    }
    acceptance = {
        **_common(root, "generated_software_acceptance"),
        "projects": [
            {
                "project_id": archetype,
                "archetype": archetype,
                "decision": "ACCEPTED",
                "human_review": True,
                "reviewer": "Senior Engineer",
                "build_status": "PASSED",
                "test_status": "PASSED",
                "security_status": "PASSED",
            }
            for archetype in ("api", "web", "desktop")
        ],
    }
    for evidence_type, payload in {
        "hardware_matrix": hardware,
        "soak_validation": soak,
        "independent_security_review": security,
        "legal_review": legal,
        "model_license_review": licenses,
        "generated_software_acceptance": acceptance,
    }.items():
        _write_json(root / EVIDENCE_FILES[evidence_type], payload)
    return root


def test_release_assurance_blocks_without_external_evidence(tmp_path: Path) -> None:
    policy = _policy(tmp_path / "policy.json")

    report = build_release_assurance_report(tmp_path / "missing", policy_path=policy, now=NOW)

    assert report["status"] == "PRODUCTION_ASSURANCE_BLOCKED"
    assert report["exit_code"] == 2
    assert report["evidence_files_found"] == 0
    assert {item["id"] for item in report["blockers"]} == set(EVIDENCE_FILES)
    assert report["safety"]["read_only"] is True
    assert report["safety"]["network_used"] is False
    assert report["claims"]["external_work_fabricated"] is False


def test_release_assurance_accepts_complete_hashed_evidence(tmp_path: Path) -> None:
    policy = _policy(tmp_path / "policy.json")
    evidence = _ready_bundle(tmp_path / "evidence")

    report = build_release_assurance_report(evidence, policy_path=policy, now=NOW)

    assert report["status"] == "PRODUCTION_ASSURANCE_READY"
    assert report["ready"] is True
    assert report["exit_code"] == 0
    assert report["blockers"] == []
    assert all(item["status"] == "VERIFIED" for item in report["evidence"].values())


def test_release_assurance_rejects_tampered_report(tmp_path: Path) -> None:
    policy = _policy(tmp_path / "policy.json")
    evidence = _ready_bundle(tmp_path / "evidence")
    (evidence / "soak_validation.md").write_text("tampered", encoding="utf-8")

    report = build_release_assurance_report(evidence, policy_path=policy, now=NOW)

    assert report["status"] == "PRODUCTION_ASSURANCE_PARTIAL"
    blocker = next(item for item in report["blockers"] if item["id"] == "soak_validation")
    assert "report_hash_mismatch" in blocker["detail"]


def test_release_assurance_rejects_path_traversal(tmp_path: Path) -> None:
    policy = _policy(tmp_path / "policy.json")
    evidence = _ready_bundle(tmp_path / "evidence")
    payload = json.loads((evidence / "legal_review.json").read_text(encoding="utf-8"))
    payload["report_path"] = "../outside.md"
    _write_json(evidence / "legal_review.json", payload)

    report = build_release_assurance_report(evidence, policy_path=policy, now=NOW)

    blocker = next(item for item in report["blockers"] if item["id"] == "legal_review")
    assert "report_path_outside_evidence_root" in blocker["detail"]


def test_release_assurance_rejects_expired_evidence(tmp_path: Path) -> None:
    policy = _policy(tmp_path / "policy.json")
    evidence = _ready_bundle(tmp_path / "evidence")
    payload = json.loads((evidence / "hardware_matrix.json").read_text(encoding="utf-8"))
    payload["collected_at"] = "2025-01-01T00:00:00Z"
    _write_json(evidence / "hardware_matrix.json", payload)

    report = build_release_assurance_report(evidence, policy_path=policy, now=NOW)

    blocker = next(item for item in report["blockers"] if item["id"] == "hardware_matrix")
    assert "evidence_expired" in blocker["detail"]


def test_release_assurance_rejects_non_finite_soak_values(tmp_path: Path) -> None:
    policy = _policy(tmp_path / "policy.json")
    evidence = _ready_bundle(tmp_path / "evidence")
    payload = json.loads((evidence / "soak_validation.json").read_text(encoding="utf-8"))
    payload["duration_hours"] = float("nan")
    _write_json(evidence / "soak_validation.json", payload)

    report = build_release_assurance_report(evidence, policy_path=policy, now=NOW)

    blocker = next(item for item in report["blockers"] if item["id"] == "soak_validation")
    assert "duration_below_policy" in blocker["detail"]


def test_release_assurance_requires_explicit_security_finding_counts(tmp_path: Path) -> None:
    policy = _policy(tmp_path / "policy.json")
    evidence = _ready_bundle(tmp_path / "evidence")
    payload = json.loads(
        (evidence / "independent_security_review.json").read_text(encoding="utf-8")
    )
    del payload["open_high_findings"]
    _write_json(evidence / "independent_security_review.json", payload)

    report = build_release_assurance_report(evidence, policy_path=policy, now=NOW)

    blocker = next(
        item for item in report["blockers"] if item["id"] == "independent_security_review"
    )
    assert "open_high_findings_invalid" in blocker["detail"]


def test_release_assurance_templates_are_pending_and_never_overwritten(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"

    paths = write_release_assurance_templates(evidence)

    assert len(paths) == len(EVIDENCE_FILES)
    assert all(json.loads(Path(path).read_text(encoding="utf-8"))["decision"] == "PENDING" for path in paths)
    with pytest.raises(FileExistsError):
        write_release_assurance_templates(evidence)


def test_release_assurance_writes_machine_readable_artifacts(tmp_path: Path) -> None:
    policy = _policy(tmp_path / "policy.json")
    report = build_release_assurance_report(
        _ready_bundle(tmp_path / "evidence"), policy_path=policy, now=NOW
    )

    paths = write_release_assurance_artifacts(report, tmp_path / "artifacts")

    assert [Path(path).name for path in paths] == [
        "374_release_assurance_verification.json",
        "375_release_assurance_verification.md",
    ]


def test_release_assurance_cli_returns_blocked_without_fabricating_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    policy = _policy(tmp_path / "policy.json")

    exit_code = verify_release_assurance.main(
        [
            "--evidence-root",
            str(tmp_path / "missing"),
            "--policy",
            str(policy),
            "--output-dir",
            str(tmp_path / "output"),
        ]
    )

    assert exit_code == 2
    assert "PRODUCTION_ASSURANCE_BLOCKED" in capsys.readouterr().out
