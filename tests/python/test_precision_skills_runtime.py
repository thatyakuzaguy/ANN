from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from agentic_network.skills import (
    PermissionDecision,
    SkillAuditLogger,
    SkillPermissionStore,
    SkillRegistry,
)
from agentic_network.skills.engineering import ENGINEERING_SKILL_ACTIONS
from agentic_network.skills.frontier_runtime import parse_language_server_diagnostics
from agentic_network.skills.precision_runtime import PRECISION_SKILLS
from agentic_network.skills.runtime import execute_skill
from agentic_engineering_network.agents.subagents import SUBAGENT_REGISTRY


@pytest.fixture(autouse=True)
def allow_pytest_temp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANN_ALLOW_TEMP_SKILL_TARGETS", "1")
    monkeypatch.setenv("TEMP", str(tmp_path.parent))
    monkeypatch.setenv("TMP", str(tmp_path.parent))


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "precision-project"
    (root / "app").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "app" / "service.py").write_text(
        "# OAuth OIDC PKCE state nonce issuer audience JWKS SAML SCIM\n"
        "# timezone zoneinfo DST decimal currency_code rounding VAT exchange rate\n"
        "# offline queue vector clock conflict resolution tombstone idempotency\n"
        "# Cache-Control ETag CORS gzip WebSocket retry-after\n"
        "# BM25 tokenizer facet golden query NDCG\n"
        "# input_schema approval_required timeout_seconds request_id output schema\n"
        "# SPF DKIM DMARC bounce exponential backoff unsubscribe delivery webhook\n"
        "# data region storage location backup region cross-border subprocessor retention\n"
        "def ready() -> bool:\n    return True\n",
        encoding="utf-8",
    )
    (root / "app" / "ui.tsx").write_text(
        "// aria-label keyboard navigation focus visible high contrast NVDA Narrator VoiceOver\n",
        encoding="utf-8",
    )
    (root / "release.ps1").write_text(
        "# sha256 Authenticode signtool SBOM rollback ASLR DEP control flow guard\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_precision.py").write_text(
        "def test_precision():\n    assert True\n", encoding="utf-8"
    )
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: ann-precision-api:test\n",
        encoding="utf-8",
    )
    return root


def _runtime(
    tmp_path: Path,
    skill: str,
    action: str,
    payload: dict[str, object],
    *,
    approved: bool = False,
):
    store = SkillPermissionStore(tmp_path / "permissions.json")
    spec = next(item for item in ENGINEERING_SKILL_ACTIONS[skill] if item.name == action)
    for permission in spec.permissions:
        store.set_permission(skill, permission, PermissionDecision.ALLOW_ALWAYS)
    return execute_skill(
        skill,
        action,
        payload,
        registry=SkillRegistry(),
        store=store,
        audit_logger=SkillAuditLogger(tmp_path / "skill-outputs"),
        approval_validator=((lambda *_args: (True, "test_approval")) if approved else None),
    )


def _attestation(runner: str) -> dict[str, object]:
    return {
        "runner": runner,
        "status": "PASSED",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_sha256": "a" * 64,
        "artifact_hashes": [{"path": "reports/result.json", "sha256": "b" * 64}],
        "signature_verified": True,
    }


def test_precision_skills_are_registered_packaged_and_delegated() -> None:
    delegated = {tool for item in SUBAGENT_REGISTRY for tool in item.tools}

    assert len(PRECISION_SKILLS) == 10
    assert PRECISION_SKILLS.issubset(ENGINEERING_SKILL_ACTIONS)
    assert PRECISION_SKILLS.issubset(delegated)
    assert len(ENGINEERING_SKILL_ACTIONS) == 126
    assert sum(len(actions) for actions in ENGINEERING_SKILL_ACTIONS.values()) == 245
    for name in PRECISION_SKILLS:
        assert SkillRegistry().get_skill(name) is not None
        assert (Path("agentic_network/skills_builtin") / name / "SKILL.md").is_file()


@pytest.mark.parametrize(
    ("skill", "action"),
    [
        ("identity_protocol_conformance", "inspect"),
        ("temporal_monetary_correctness", "inspect"),
        ("offline_sync_conflict_verification", "inspect"),
        ("binary_hardening_verification", "inspect"),
        ("web_protocol_conformance", "inspect"),
        ("search_relevance_evaluation", "analyze"),
        ("agent_tool_contract_verification", "inspect"),
        ("messaging_deliverability", "inspect"),
        ("data_residency_mapping", "analyze"),
        ("assistive_technology_lab", "inspect"),
    ],
)
def test_precision_analysis_is_bounded_and_read_only(
    tmp_path: Path, skill: str, action: str
) -> None:
    root = _project(tmp_path)
    before = (root / "app" / "service.py").read_bytes()

    result = _runtime(tmp_path, skill, action, {"project_root": str(root)})

    assert result.status in {"SUCCESS", "PARTIAL"}
    assert result.output["terminal_used"] is False
    assert result.output["internet_used"] is False
    assert result.output["dependency_install_used"] is False
    assert result.output["data"]["project_modified"] is False
    assert result.output["data"]["raw_command_accepted"] is False
    assert (root / "app" / "service.py").read_bytes() == before


@pytest.mark.parametrize(
    ("skill", "recipe", "marker"),
    [
        ("identity_protocol_conformance", "python_identity_protocol", "identity_protocol"),
        ("temporal_monetary_correctness", "python_temporal_monetary", "temporal_monetary"),
        ("offline_sync_conflict_verification", "python_offline_sync", "offline_sync"),
        ("web_protocol_conformance", "python_web_protocol", "web_protocol"),
        ("search_relevance_evaluation", "python_search_relevance", "search_relevance"),
        ("agent_tool_contract_verification", "python_agent_tool_contract", "agent_tool_contract"),
        ("messaging_deliverability", "python_messaging_deliverability", "messaging_deliverability"),
    ],
)
def test_precision_execution_uses_only_approved_compose_recipes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    skill: str,
    recipe: str,
    marker: str,
) -> None:
    root = _project(tmp_path)
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "passed", "")

    monkeypatch.setattr("agentic_network.skills.engineering_runtime.subprocess.run", fake_run)
    result = _runtime(
        tmp_path,
        skill,
        "run",
        {
            "project_root": str(root),
            "recipe": recipe,
            "command": "powershell -Command Remove-Item C:\\ -Recurse",
        },
        approved=True,
    )

    assert result.status == "SUCCESS"
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert kwargs["shell"] is False
    assert marker in command
    assert "Remove-Item" not in command
    assert "--pull" in command and "never" in command


def test_external_evidence_is_attested_and_never_executes_host_programs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)

    def fail_run(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("host execution is forbidden")

    monkeypatch.setattr(subprocess, "run", fail_run)
    binary = _runtime(
        tmp_path,
        "binary_hardening_verification",
        "verify",
        {"project_root": str(root), "evidence": _attestation("windows-sandbox")},
    )
    assistive = _runtime(
        tmp_path,
        "assistive_technology_lab",
        "verify",
        {"project_root": str(root), "evidence": _attestation("nvda-windows")},
    )

    assert binary.output["data"]["external_evidence"]["valid"] is True
    assert binary.output["data"]["host_binary_executed"] is False
    assert assistive.output["data"]["external_evidence"]["valid"] is True
    assert assistive.output["data"]["host_ui_automation_executed"] is False


def test_invalid_external_evidence_cannot_pass(tmp_path: Path) -> None:
    root = _project(tmp_path)
    result = _runtime(
        tmp_path,
        "binary_hardening_verification",
        "verify",
        {"project_root": str(root), "evidence": {"status": "PASSED"}},
    )

    assert result.status == "PARTIAL"
    assert result.output["data"]["external_evidence"]["status"] == "REJECTED"


def test_lsp_parsers_normalize_pyright_and_typescript_without_raw_messages() -> None:
    pyright = parse_language_server_diagnostics(
        json.dumps(
            {
                "generalDiagnostics": [
                    {
                        "file": "/workspace/app.py",
                        "severity": "error",
                        "rule": "reportAssignmentType",
                        "message": "Type secret should not be retained",
                        "range": {"start": {"line": 4, "character": 2}},
                    }
                ]
            }
        ),
        "pyright",
    )
    typescript = parse_language_server_diagnostics(
        "src/app.ts(7,11): error TS2322: Type string is not assignable to number",
        "typescript",
    )

    assert pyright[0]["line"] == 5
    assert pyright[0]["code"] == "reportAssignmentType"
    assert "message" not in pyright[0]
    assert typescript[0]["code"] == "TS2322"
    assert typescript[0]["column"] == 11


def test_benchmark_and_runner_configuration_is_local_and_versioned() -> None:
    benchmark = json.loads(
        Path("config/autonomous_delivery_benchmarks.json").read_text(encoding="utf-8")
    )
    runners = json.loads(Path("config/external_skill_runners.json").read_text(encoding="utf-8"))

    assert benchmark["version"] == 1
    assert len(benchmark["cases"]) >= 6
    assert runners["execution_policy"] == "external_explicit_only"
    assert all(not item.get("ann_launches_host_binary", False) for item in runners["runners"])
