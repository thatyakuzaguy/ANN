from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest
from fastapi.testclient import TestClient

from agentic_network.skills import PermissionDecision, SkillAuditLogger, SkillPermissionStore, SkillRegistry
from agentic_network.skills.engineering import ENGINEERING_SKILL_ACTIONS, engineering_skill_catalog
from agentic_network.skills.runtime import execute_skill
from agentic_network.skills.manager import SkillsManager
from agentic_engineering_network.logs.audit import AuditLogger
from agentic_engineering_network.security.approvals import ApprovalCenter
import app.api.routes as api_routes
from app.main import app


ENGINEERING_SKILLS = {
    "repository_intelligence",
    "sandbox_verification",
    "failure_diagnostics",
    "patch_workspace",
    "browser_e2e",
    "database_migration",
    "security_audit",
    "container_operations",
    "api_contract",
    "release_packaging",
}


def _runtime(
    tmp_path: Path,
    skill: str,
    action: str,
    payload: dict[str, object],
    *,
    approved: bool = False,
):
    registry = SkillRegistry()
    store = SkillPermissionStore(tmp_path / "permissions.json")
    spec = next(item for item in ENGINEERING_SKILL_ACTIONS[skill] if item.name == action)
    for permission in spec.permissions:
        store.set_permission(skill, permission, PermissionDecision.ALLOW_ALWAYS)
    return execute_skill(
        skill,
        action,
        payload,
        registry=registry,
        store=store,
        audit_logger=SkillAuditLogger(tmp_path / "skill-outputs"),
        approval_validator=(lambda *_args: (True, "test_approval")) if approved else None,
    )


@pytest.fixture(autouse=True)
def allow_pytest_temp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANN_ALLOW_TEMP_SKILL_TARGETS", "1")
    monkeypatch.setenv("ANN_ALLOW_TEMP_PROJECT_PATCH_TARGETS", "1")
    monkeypatch.setenv("TEMP", str(tmp_path.parent))
    monkeypatch.setenv("TMP", str(tmp_path.parent))


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "app").mkdir(parents=True)
    (root / "app" / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef health():\n    return {'ok': True}\n",
        encoding="utf-8",
    )
    (root / "tests" / "python").mkdir(parents=True)
    (root / "tests" / "python" / "test_main.py").write_text(
        "from app.main import health\n\ndef test_health():\n    assert health()['ok'] is True\n",
        encoding="utf-8",
    )
    return root


def test_all_engineering_skills_are_registered_and_enabled() -> None:
    registry = SkillRegistry()
    catalog = {item["name"]: item for item in engineering_skill_catalog()}

    assert ENGINEERING_SKILLS.issubset(catalog)
    assert all(registry.get_skill(name) is not None for name in ENGINEERING_SKILLS)
    assert all(registry.get_skill(name).enabled for name in ENGINEERING_SKILLS)  # type: ignore[union-attr]
    assert all(catalog[name]["actions"] for name in ENGINEERING_SKILLS)


def test_repository_intelligence_generates_ast_and_impact_artifacts(tmp_path: Path) -> None:
    root = _project(tmp_path)

    result = _runtime(
        tmp_path,
        "repository_intelligence",
        "impact",
        {"project_root": str(root), "target_paths": ["app/main.py"]},
    )

    assert result.status == "SUCCESS"
    assert result.output["data"]["files_scanned"] >= 2
    assert result.output["data"]["impact"]["targets"] == ["app/main.py"]
    assert Path(result.output["data"]["output_files"]["functions"]).is_file()
    assert any(path.endswith("impact_analysis.json") for path in result.output["artifacts"])


def test_skill_is_blocked_without_explicit_permission(tmp_path: Path) -> None:
    root = _project(tmp_path)

    result = execute_skill(
        "repository_intelligence",
        "scan",
        {"project_root": str(root)},
        registry=SkillRegistry(),
        store=SkillPermissionStore(tmp_path / "permissions.json"),
        audit_logger=SkillAuditLogger(tmp_path / "skill-outputs"),
    )

    assert result.status == "BLOCKED"
    assert "explicit approval" in result.errors[0]


def test_failure_diagnostics_ranks_cross_domain_evidence(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: ann-test-api:local\n  db:\n    image: postgres:16\n",
        encoding="utf-8",
    )
    migration = root / "app" / "alembic" / "versions" / "001_users.py"
    migration.parent.mkdir(parents=True)
    migration.write_text("def upgrade():\n    pass\n\ndef downgrade():\n    pass\n", encoding="utf-8")

    result = _runtime(
        tmp_path,
        "failure_diagnostics",
        "diagnose",
        {
            "project_root": str(root),
            "stderr": "psycopg.errors.UndefinedTable: relation users does not exist during integration test",
            "affected_files": ["app/main.py"],
        },
    )

    assert result.status == "SUCCESS"
    isolation = result.output["data"]["root_cause_isolation"]
    assert isolation["failure_type"] in {"integration_boundary_failure", "possible_cross_domain_failure"}
    assert any("001_users.py" in item["path"] for item in isolation["ranked_suspects"])


def test_sandbox_verification_detects_only_closed_recipes(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: ann-test-api:local\n  web:\n    image: ann-test-web:local\n",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        json.dumps({"scripts": {"build": "vite build", "danger": "powershell payload.ps1"}}),
        encoding="utf-8",
    )

    result = _runtime(
        tmp_path,
        "sandbox_verification",
        "detect",
        {"project_root": str(root), "command": ["powershell", "payload.ps1"]},
    )

    assert result.status == "SUCCESS"
    rendered = json.dumps(result.output["data"])
    assert "pytest" in rendered
    assert "payload.ps1" not in rendered


def test_sandbox_verification_uses_docker_shell_false_and_never_installs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: ann-test-api:local\n",
        encoding="utf-8",
    )
    calls: list[tuple[list[str], dict[str, object]]] = []

    class Completed:
        returncode = 0
        stdout = "1 passed"
        stderr = ""

    def fake_run(command: list[str], **kwargs: object) -> Completed:
        calls.append((command, kwargs))
        return Completed()

    monkeypatch.setattr("agentic_network.skills.engineering_runtime.subprocess.run", fake_run)

    result = _runtime(
        tmp_path,
        "sandbox_verification",
        "run",
        {"project_root": str(root)},
        approved=True,
    )

    assert result.status == "SUCCESS"
    assert calls
    assert all(Path(call[0][0]).name.lower().startswith("docker") for call in calls)
    assert all(call[1]["shell"] is False for call in calls)
    assert all("--pull" in call[0] and "never" in call[0] for call in calls)
    assert all("install" not in " ".join(call[0]).lower() for call in calls)
    override_paths = [
        Path(call[0][index + 1])
        for call in calls
        for index, value in enumerate(call[0][:-1])
        if value == "-f" and str(call[0][index + 1]).endswith("compose.ann-internal.yaml")
    ]
    assert override_paths
    assert all("internal: true" in path.read_text(encoding="utf-8") for path in override_paths)


def test_patch_workspace_inspects_without_modifying_source(tmp_path: Path) -> None:
    root = _project(tmp_path)
    target = root / "app" / "value.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    patch = root / "change.diff"
    patch.write_text(
        "diff --git a/app/value.py b/app/value.py\n"
        "--- a/app/value.py\n"
        "+++ b/app/value.py\n"
        "@@ -1 +1 @@\n"
        "-VALUE = 1\n"
        "+VALUE = 2\n",
        encoding="utf-8",
    )

    result = _runtime(
        tmp_path,
        "patch_workspace",
        "inspect",
        {"project_root": str(root), "patch_file": "change.diff"},
    )

    assert result.status == "SUCCESS"
    assert result.output["data"]["status"] == "DRY_RUN"
    assert target.read_text(encoding="utf-8") == "VALUE = 1\n"
    assert result.output["data"]["approval_center_required"] is True


def test_patch_apply_cannot_bypass_approval_center(tmp_path: Path) -> None:
    root = _project(tmp_path)
    target = root / "app" / "value.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    patch = root / "change.diff"
    patch.write_text(
        "diff --git a/app/value.py b/app/value.py\n--- a/app/value.py\n+++ b/app/value.py\n"
        "@@ -1 +1 @@\n-VALUE = 1\n+VALUE = 2\n",
        encoding="utf-8",
    )

    result = _runtime(
        tmp_path,
        "patch_workspace",
        "apply",
        {"project_root": str(root), "patch_file": "change.diff", "approval_token": "fake"},
    )

    assert result.status == "BLOCKED"
    assert "approval_center_validation_required" in result.errors
    assert target.read_text(encoding="utf-8") == "VALUE = 1\n"


def test_browser_e2e_rejects_non_local_url(tmp_path: Path) -> None:
    root = _project(tmp_path)

    result = _runtime(
        tmp_path,
        "browser_e2e",
        "detect",
        {"project_root": str(root), "base_url": "https://example.com"},
    )

    assert result.status == "FAILED"
    assert result.errors == ["browser_e2e_requires_local_url"]


def test_browser_e2e_reports_declared_and_captured_evidence(tmp_path: Path) -> None:
    root = _project(tmp_path)
    web = root / "apps" / "web"
    web.mkdir(parents=True)
    (web / "smoke.spec.ts").write_text(
        "page.on('console', () => undefined);\n"
        "page.waitForResponse('/api/health');\n"
        "await expect(page).toHaveScreenshot();\n"
        "// accessibility axe scan\n",
        encoding="utf-8",
    )
    evidence = web / "test-results" / "smoke"
    evidence.mkdir(parents=True)
    (evidence / "actual.png").write_bytes(b"png")
    (evidence / "trace.zip").write_bytes(b"trace")

    result = _runtime(
        tmp_path,
        "browser_e2e",
        "detect",
        {"project_root": str(root), "base_url": "http://127.0.0.1:3000"},
    )

    data = result.output["data"]["evidence"]
    assert data["console_assertions_declared"] is True
    assert data["network_assertions_declared"] is True
    assert data["accessibility_assertions_declared"] is True
    assert data["visual_assertions_declared"] is True
    assert any(path.endswith("actual.png") for path in data["screenshots"])
    assert any(path.endswith("trace.zip") for path in data["traces"])


def test_browser_e2e_accepts_only_declared_compose_service_hosts(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "docker-compose.yml").write_text(
        "services:\n  web:\n    image: ann-web:local\n  e2e:\n    image: ann-e2e:local\n",
        encoding="utf-8",
    )

    accepted = _runtime(
        tmp_path,
        "browser_e2e",
        "detect",
        {"project_root": str(root), "base_url": "http://web:3000"},
    )
    rejected = _runtime(
        tmp_path,
        "browser_e2e",
        "detect",
        {"project_root": str(root), "base_url": "http://undeclared:3000"},
    )

    assert accepted.status == "PARTIAL"
    assert rejected.status == "FAILED"
    assert rejected.errors == ["browser_e2e_requires_local_url"]


def test_database_migration_inspects_reversibility_indexes_and_tenant_scope(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "alembic.ini").write_text("[alembic]\nscript_location = migrations\n", encoding="utf-8")
    revision = root / "migrations" / "versions" / "001_tenant.py"
    revision.parent.mkdir(parents=True)
    revision.write_text(
        "def upgrade():\n"
        "    op.create_index('ix_tenant', 'items', ['tenant_id'])\n"
        "    op.create_unique_constraint('uq_tenant_name', 'items', ['tenant_id', 'name'])\n\n"
        "def downgrade():\n    op.drop_index('ix_tenant')\n",
        encoding="utf-8",
    )

    result = _runtime(
        tmp_path,
        "database_migration",
        "inspect",
        {"project_root": str(root)},
    )

    assert result.status == "SUCCESS"
    assert result.output["data"]["reversible"] is True
    assert result.output["data"]["tenant_scope_detected"] is True
    assert result.output["data"]["revisions"][0]["indexes"] == 1
    assert result.output["data"]["constraint_count"] == 1
    assert result.output["data"]["destructive_operation_count"] == 0


def test_security_audit_detects_secret_shell_and_docker_risks(tmp_path: Path) -> None:
    root = _project(tmp_path)
    synthetic_secret = "12345678" + "90abcdef"
    (root / "app" / "unsafe.py").write_text(
        f"API_KEY = {synthetic_secret!r}\nsubprocess.run('x', shell=True)\n",
        encoding="utf-8",
    )
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: app:latest\n    privileged: true\n",
        encoding="utf-8",
    )

    result = _runtime(tmp_path, "security_audit", "scan", {"project_root": str(root)})

    rules = {item["rule"] for item in result.output["data"]["findings"]}
    assert result.status == "FAILED"
    assert {"hardcoded_secret", "shell_true", "docker_privileged", "docker_latest"}.issubset(rules)


def test_container_mutations_require_approval_center_before_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: ann-test-api:local\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not execute")),
    )

    result = _runtime(
        tmp_path,
        "container_operations",
        "up",
        {"project_root": str(root)},
    )

    assert result.status == "BLOCKED"
    assert "approval_center_validation_required" in result.errors


def test_compose_service_detection_accepts_four_space_indentation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    (root / "docker-compose.yml").write_text(
        "services:\n    api:\n        image: ann-test-api:local\n",
        encoding="utf-8",
    )

    class Completed:
        returncode = 0
        stdout = "1 passed"
        stderr = ""

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        lambda *_args, **_kwargs: Completed(),
    )
    result = _runtime(
        tmp_path,
        "sandbox_verification",
        "run",
        {"project_root": str(root)},
        approved=True,
    )

    assert result.status == "SUCCESS"
    assert len(result.output["data"]["results"]) == 1


def test_container_up_blocks_non_isolated_compose_topology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: ann-api:local\n    network_mode: host\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not execute")),
    )

    result = _runtime(
        tmp_path,
        "container_operations",
        "up",
        {"project_root": str(root)},
        approved=True,
    )

    assert result.status == "BLOCKED"
    assert result.errors == ["host_network"]


def test_container_up_blocks_public_ports_and_requires_loopback_acknowledgement(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    compose = root / "docker-compose.yml"
    compose.write_text(
        "services:\n  api:\n    image: ann-api:local\n    ports:\n      - '8000:8000'\n",
        encoding="utf-8",
    )

    public = _runtime(
        tmp_path,
        "container_operations",
        "up",
        {"project_root": str(root)},
        approved=True,
    )
    compose.write_text(
        "services:\n  api:\n    image: ann-api:local\n    ports:\n      - '127.0.0.1:8000:8000'\n",
        encoding="utf-8",
    )
    loopback = _runtime(
        tmp_path,
        "container_operations",
        "up",
        {"project_root": str(root)},
        approved=True,
    )

    assert public.status == "BLOCKED"
    assert public.errors == ["public_host_ports"]
    assert loopback.status == "BLOCKED"
    assert loopback.errors == ["loopback_host_ports_require_acknowledgement"]


def test_api_contract_compares_frontend_backend_and_openapi(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "openapi.json").write_text(
        json.dumps(
            {"openapi": "3.1.0", "paths": {"/health": {}, "/users": {}, "/stripe/webhook": {}}}
        ),
        encoding="utf-8",
    )
    (root / "app" / "webhooks.py").write_text(
        "def verify_webhook_signature(payload, signature):\n    return bool(signature)\n",
        encoding="utf-8",
    )
    (root / "tests" / "python" / "test_webhook_contract.py").write_text(
        "def test_webhook_contract():\n    assert True\n",
        encoding="utf-8",
    )
    web = root / "web"
    web.mkdir()
    (web / "api.ts").write_text("fetch('/health'); fetch('/missing');\n", encoding="utf-8")

    result = _runtime(tmp_path, "api_contract", "analyze", {"project_root": str(root)})

    assert result.status == "FAILED"
    assert result.output["data"]["missing_backend_paths"] == ["/stripe/webhook", "/users"]
    assert result.output["data"]["frontend_paths_without_contract"] == ["/missing"]
    assert result.output["data"]["contract_tests_present"] is True
    assert result.output["data"]["webhook_security"]["signature_validation_detected"] is True


def test_release_packaging_generates_sbom_hashes_archive_and_rollback(tmp_path: Path) -> None:
    root = _project(tmp_path)
    installer = root / "installer"
    installer.mkdir()
    (installer / "ANN_Setup.exe").write_bytes(b"setup")
    (installer / "ANN_Uninstall.exe").write_bytes(b"uninstall")
    (root / "requirements.txt").write_text("fastapi==0.115.0\n", encoding="utf-8")
    (root / "package.json").write_text(
        json.dumps({"dependencies": {"react": "18.3.1"}}), encoding="utf-8"
    )

    result = _runtime(tmp_path, "release_packaging", "prepare", {"project_root": str(root)})

    assert result.status in {"SUCCESS", "PARTIAL"}
    assert Path(result.output["data"]["archive"]).is_file()
    assert Path(result.output["data"]["sbom"]).is_file()
    assert result.output["data"]["archive_sha256"]
    assert result.output["data"]["rollback"]["preserve"] == [
        "projects",
        "models",
        "outputs",
        "data",
        "logs",
    ]
    assert Path(result.output["data"]["rollback_manifest"]).is_file()

    (installer / "ANN_Setup.exe").unlink()
    verified = _runtime(tmp_path, "release_packaging", "verify", {"project_root": str(root)})
    assert verified.status == "SUCCESS"
    assert verified.output["data"]["valid"] is True


def test_skill_api_exposes_catalog_and_safety_contract() -> None:
    response = TestClient(app).get("/api/skills")

    assert response.status_code == 200
    payload = response.json()
    names = {item["name"] for item in payload["skills"]}
    assert ENGINEERING_SKILLS.issubset(names)
    assert payload["safety"]["raw_shell"] is False
    assert payload["safety"]["shell_true"] is False
    assert payload["safety"]["mutations_require_approval_center"] is True


def test_manifest_denied_permissions_cannot_be_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = SkillsManager(
        permission_store=SkillPermissionStore(tmp_path / "permissions.json"),
        audit_logger=SkillAuditLogger(tmp_path / "skill-outputs"),
    )
    manager.permission_store.set_permission(
        "browser_e2e",
        "network",
        PermissionDecision.ALLOW_ALWAYS,
    )
    monkeypatch.setattr(api_routes, "skills_manager", manager)

    blocked = TestClient(app).post(
        "/api/skills/browser_e2e/permissions",
        json={"permission": "network", "decision": "ALLOW_ALWAYS"},
    )
    sandbox = api_routes.evaluate_skill_sandbox(
        "browser_e2e",
        ["network"],
        registry=manager.registry,
        store=manager.permission_store,
        outputs_root=manager.audit_logger.audit_root,
    )

    assert blocked.status_code == 403
    assert sandbox.status.value == "DENIED"
    catalog = TestClient(app).get("/api/skills").json()["skills"]
    browser = next(item for item in catalog if item["name"] == "browser_e2e")
    assert browser["permissions"]["network"] == "DENY"
    assert browser["stored_permissions"]["network"] == "DENY"


def test_skill_api_permission_execution_and_single_use_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: ann-test-api:local\n",
        encoding="utf-8",
    )
    manager = SkillsManager(
        permission_store=SkillPermissionStore(tmp_path / "api-permissions.json"),
        audit_logger=SkillAuditLogger(tmp_path / "api-skill-outputs"),
    )
    approvals = ApprovalCenter(
        AuditLogger(tmp_path / "api-audit.jsonl"),
        tmp_path / "api-approvals.json",
    )
    monkeypatch.setattr(api_routes, "skills_manager", manager)
    monkeypatch.setattr(api_routes, "approval_center", approvals)

    class Completed:
        returncode = 0
        stdout = "started"
        stderr = ""

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        lambda *_args, **_kwargs: Completed(),
    )
    client = TestClient(app)
    for permission in ("filesystem_read", "filesystem_write", "terminal_execute"):
        response = client.post(
            "/api/skills/container_operations/permissions",
            json={"permission": permission, "decision": "ALLOW_ALWAYS"},
        )
        assert response.status_code == 200

    request = {
        "action": "up",
        "payload": {"project_root": str(root), "project_name": "api-skill-test"},
    }
    pending = client.post("/api/skills/container_operations/execute", json=request)
    assert pending.status_code == 200
    assert pending.json()["status"] == "PENDING_APPROVAL"
    approval_id = pending.json()["approval_id"]
    approvals.resolve(approval_id, True)

    executed = client.post(
        "/api/skills/container_operations/execute",
        json={**request, "approval_id": approval_id},
    )
    assert executed.status_code == 200
    assert executed.json()["status"] == "SUCCESS"
    assert executed.json()["output"]["terminal_used"] is True

    replay = client.post(
        "/api/skills/container_operations/execute",
        json={**request, "approval_id": approval_id},
    )
    assert replay.status_code == 409
    assert "consumed" in replay.json()["detail"]


def test_path_traversal_and_c_drive_are_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANN_ALLOW_TEMP_SKILL_TARGETS", raising=False)
    result = _runtime(
        tmp_path,
        "repository_intelligence",
        "scan",
        {"project_root": "C:\\unsafe\\project\\..\\escape"},
    )

    assert result.status == "FAILED"
    assert result.errors == ["project_root_path_traversal"]
