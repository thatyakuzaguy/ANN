from __future__ import annotations

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
from agentic_network.skills.frontier_runtime import (
    FRONTIER_SKILLS,
    enrich_specialist_execution,
)
from agentic_network.skills.runtime import execute_skill
from agentic_engineering_network.agents.subagents import SUBAGENT_REGISTRY


@pytest.fixture(autouse=True)
def allow_pytest_temp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANN_ALLOW_TEMP_SKILL_TARGETS", "1")
    monkeypatch.setenv("TEMP", str(tmp_path.parent))
    monkeypatch.setenv("TMP", str(tmp_path.parent))


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "frontier-project"
    (root / "app").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "sdk" / "python").mkdir(parents=True)
    (root / "android" / "app" / "src" / "main").mkdir(parents=True)
    (root / "app" / "main.py").write_text(
        "# pyright: strict; PySide6 QMainWindow UIAutomation\n"
        "# JWT issuer audience algorithm, key rotation kid JWKS, TLS HSTS\n"
        "# argon2 secure random secrets.token_urlsafe\n"
        "# prompt injection, untrusted input, tool allowlist, approval_required\n"
        "# retrieval citation source trust, redact secret, output schema\n"
        "# data export DSAR, delete account anonymize, retention purge TTL\n"
        "# consent, tenant purge tenant_id row level security, audit log\n"
        "# postgres redis queue search index outbox reconcile idempotency\n"
        "# analytics.track event_name anonymous_id analytics consent opt out\n"
        "# PII property allowlist funnel activation experiment variant schema validation\n"
        "def health() -> bool:\n    return True\n",
        encoding="utf-8",
    )
    (root / "app" / "client.ts").write_text(
        "export interface Health { ok: boolean }\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_frontier.py").write_text(
        "# delivery_benchmark runtime_failure llm_security privacy_rights\n"
        "# crypto_protocol sdk_contract capacity cross_store product_telemetry\n"
        "def test_frontier():\n    assert True\n",
        encoding="utf-8",
    )
    (root / "sdk" / "python" / "client.py").write_text(
        "class ApiError(Exception):\n    pass\n",
        encoding="utf-8",
    )
    (root / "android" / "app" / "src" / "main" / "AndroidManifest.xml").write_text(
        "<manifest package='dev.ann.frontier' />\n", encoding="utf-8"
    )
    (root / "openapi.yaml").write_text(
        "openapi: 3.1.0\ninfo:\n  title: Frontier\n  version: 1.0.0\n",
        encoding="utf-8",
    )
    (root / "pyrightconfig.json").write_text(
        json.dumps({"typeCheckingMode": "strict"}), encoding="utf-8"
    )
    (root / "pyproject.toml").write_text(
        "[tool.pyright]\ntypeCheckingMode = 'strict'\n", encoding="utf-8"
    )
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: ann-frontier-api:test\n",
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


def test_frontier_skills_are_registered_packaged_and_delegated() -> None:
    registry = SkillRegistry()
    delegated = {tool for item in SUBAGENT_REGISTRY for tool in item.tools}

    assert len(FRONTIER_SKILLS) == 12
    assert FRONTIER_SKILLS.issubset(ENGINEERING_SKILL_ACTIONS)
    assert FRONTIER_SKILLS.issubset(delegated)
    assert len(ENGINEERING_SKILL_ACTIONS) == 126
    assert sum(len(actions) for actions in ENGINEERING_SKILL_ACTIONS.values()) == 245
    for name in FRONTIER_SKILLS:
        assert registry.get_skill(name) is not None
        assert (Path("agentic_network/skills_builtin") / name / "SKILL.md").is_file()


@pytest.mark.parametrize(
    ("skill", "action", "extra"),
    [
        ("language_server_intelligence", "inspect", {}),
        ("autonomous_delivery_benchmark", "inspect", {}),
        ("runtime_failure_lab", "inspect", {}),
        ("native_ui_automation", "inspect", {}),
        ("llm_application_security", "inspect", {}),
        ("privacy_rights_verification", "inspect", {}),
        ("cryptographic_protocol_verification", "inspect", {}),
        ("sdk_contract_conformance", "analyze", {}),
        ("mobile_device_lab", "inspect", {}),
        (
            "capacity_economics",
            "analyze",
            {"baseline": {"requests_per_second": 20, "latency_ms": 100, "memory_mb": 256}},
        ),
        ("cross_store_consistency", "inspect", {}),
        ("product_telemetry_validation", "analyze", {}),
    ],
)
def test_every_frontier_skill_emits_bounded_read_only_evidence(
    tmp_path: Path,
    skill: str,
    action: str,
    extra: dict[str, object],
) -> None:
    root = _project(tmp_path)
    before = (root / "app" / "main.py").read_text(encoding="utf-8")
    result = _runtime(tmp_path, skill, action, {"project_root": str(root), **extra})

    assert result.status in {"SUCCESS", "PARTIAL"}
    assert result.output["terminal_used"] is False
    assert result.output["internet_used"] is False
    assert result.output["dependency_install_used"] is False
    assert result.output["data"]["project_modified"] is False
    assert result.output["data"]["bounded"] is True
    assert all(Path(path).is_file() for path in result.output["artifacts"])
    assert (root / "app" / "main.py").read_text(encoding="utf-8") == before


@pytest.mark.parametrize(
    ("skill", "action", "recipe", "expected"),
    [
        ("language_server_intelligence", "run", "python_lsp", "pyright"),
        (
            "autonomous_delivery_benchmark",
            "run",
            "python_delivery_benchmark",
            "delivery_benchmark",
        ),
        ("runtime_failure_lab", "run", "python_runtime_failure", "runtime_failure"),
        ("llm_application_security", "run", "python_llm_security", "llm_security"),
        ("privacy_rights_verification", "run", "python_privacy_rights", "privacy_rights"),
        (
            "cryptographic_protocol_verification",
            "run",
            "python_crypto_protocol",
            "crypto_protocol",
        ),
        ("sdk_contract_conformance", "run", "python_sdk_contract", "sdk_contract"),
        ("capacity_economics", "benchmark", "python_capacity", "capacity"),
        ("cross_store_consistency", "run", "python_cross_store", "cross_store"),
        (
            "product_telemetry_validation",
            "run",
            "python_product_telemetry",
            "product_telemetry",
        ),
    ],
)
def test_executable_frontier_skills_use_closed_approved_compose_recipes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    skill: str,
    action: str,
    recipe: str,
    expected: str,
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
        action,
        {
            "project_root": str(root),
            "recipe": recipe,
            "command": "git reset --hard && powershell -Command Remove-Item C:\\",
        },
        approved=True,
    )

    assert result.status == "SUCCESS"
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert kwargs["shell"] is False
    assert expected in command
    assert "reset" not in command
    assert "Remove-Item" not in command
    assert "--pull" in command
    assert "never" in command


def test_unapproved_or_unknown_frontier_recipe_never_executes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    called = False

    def fail_run(*_args: Any, **_kwargs: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr("agentic_network.skills.engineering_runtime.subprocess.run", fail_run)
    unapproved = _runtime(
        tmp_path,
        "runtime_failure_lab",
        "run",
        {"project_root": str(root), "recipe": "python_runtime_failure"},
    )
    unknown = _runtime(
        tmp_path,
        "runtime_failure_lab",
        "run",
        {"project_root": str(root), "recipe": "powershell -Command Stop-Computer"},
        approved=True,
    )

    assert unapproved.status == "BLOCKED"
    assert unknown.status == "BLOCKED"
    assert called is False


def test_specialist_interpreter_rejects_logs_outside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "skill-workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.log"
    outside.write_text("secret diagnostic", encoding="utf-8")
    result = {
        "status": "SUCCESS",
        "data": {
            "recipe": "python_lsp",
            "result": {
                "stdout_path": str(outside),
                "stderr_path": str(outside),
            },
        },
    }

    enriched = enrich_specialist_execution(
        "language_server_intelligence", workspace, result
    )

    interpretation = enriched["data"]["interpretation"]
    assert interpretation["diagnostics"] == []
    assert "secret diagnostic" not in json.dumps(enriched)


def test_specialist_interpreter_rejects_workspace_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "skill-workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.log"
    outside.write_text("secret diagnostic", encoding="utf-8")
    link = workspace / "stdout.log"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("File symlinks are unavailable on this Windows account.")
    result = {
        "status": "SUCCESS",
        "data": {
            "recipe": "python_lsp",
            "result": {"stdout_path": str(link), "stderr_path": ""},
        },
    }

    enriched = enrich_specialist_execution(
        "language_server_intelligence", workspace, result
    )

    assert enriched["data"]["interpretation"]["diagnostics"] == []


def test_delivery_benchmark_requires_real_stage_and_model_evidence(tmp_path: Path) -> None:
    root = _project(tmp_path)
    incomplete = _runtime(
        tmp_path,
        "autonomous_delivery_benchmark",
        "inspect",
        {"project_root": str(root)},
    )
    complete = _runtime(
        tmp_path,
        "autonomous_delivery_benchmark",
        "inspect",
        {
            "project_root": str(root),
            "stages": {
                name: "PASSED"
                for name in (
                    "requirements",
                    "architecture",
                    "implementation",
                    "build",
                    "tests",
                    "review",
                    "package",
                    "rollback",
                )
            },
            "model_provenance": {
                "model": "local-test-model",
                "model_hash": "a" * 64,
                "backend": "llama_cpp",
                "runtime_version": "test",
            },
        },
    )

    assert incomplete.status == "PARTIAL"
    assert complete.status == "SUCCESS"


def test_native_and_mobile_verification_never_launch_host_programs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)

    def fail_run(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("host execution is forbidden")

    monkeypatch.setattr(subprocess, "run", fail_run)
    native = _runtime(
        tmp_path,
        "native_ui_automation",
        "verify",
        {"project_root": str(root), "evidence": {"first_launch": True}},
    )
    mobile = _runtime(
        tmp_path,
        "mobile_device_lab",
        "verify",
        {"project_root": str(root), "evidence": {"launch": True}},
    )

    assert native.output["data"]["host_application_executed"] is False
    assert mobile.output["data"]["host_emulator_started"] is False
    assert native.status == "PARTIAL"
    assert mobile.status == "PARTIAL"


def test_native_and_mobile_evidence_requires_runner_hash_and_timestamp(tmp_path: Path) -> None:
    root = _project(tmp_path)
    native_checks = {
        name: True
        for name in (
            "clean_machine",
            "first_launch",
            "navigation",
            "keyboard",
            "accessibility_tree",
            "shutdown",
        )
    }
    mobile_checks = {
        name: True
        for name in (
            "device_identity",
            "install",
            "launch",
            "interaction",
            "network_capture",
            "accessibility",
            "uninstall",
        )
    }
    native = _runtime(
        tmp_path,
        "native_ui_automation",
        "verify",
        {
            "project_root": str(root),
            "evidence": {
                **native_checks,
                "runner": "uiautomation",
                "status": "PASSED",
                "report_sha256": "a" * 64,
                "generated_at": "2026-08-01T00:00:00Z",
                "artifact_hashes": [
                    {"path": "native/report.json", "sha256": "c" * 64}
                ],
            },
        },
    )
    mobile = _runtime(
        tmp_path,
        "mobile_device_lab",
        "verify",
        {
            "project_root": str(root),
            "evidence": {
                **mobile_checks,
                "runner": "android_emulator",
                "status": "PASSED",
                "report_sha256": "b" * 64,
                "generated_at": "2026-08-01T00:00:00Z",
                "artifact_hashes": [
                    {"path": "mobile/report.json", "sha256": "d" * 64}
                ],
            },
        },
    )

    assert native.status == "SUCCESS"
    assert mobile.status == "SUCCESS"


def test_crypto_findings_and_capacity_projection_are_concrete(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "app" / "unsafe.py").write_text(
        "import hashlib\ndigest = hashlib.md5(b'data')\n", encoding="utf-8"
    )
    crypto = _runtime(
        tmp_path,
        "cryptographic_protocol_verification",
        "inspect",
        {"project_root": str(root)},
    )
    capacity = _runtime(
        tmp_path,
        "capacity_economics",
        "analyze",
        {
            "project_root": str(root),
            "baseline": {"requests_per_second": 20, "latency_ms": 100, "memory_mb": 256},
            "target_multiplier": 3,
        },
    )

    assert crypto.status == "PARTIAL"
    assert crypto.output["data"]["insecure_usage_findings"] == [
        {"path": "app/unsafe.py", "finding": "insecure_hash"}
    ]
    assert capacity.status == "SUCCESS"
    assert capacity.output["data"]["projection"]["target_requests_per_second"] == 60
    assert capacity.output["data"]["projection"]["binding_cost_estimate"] is False
