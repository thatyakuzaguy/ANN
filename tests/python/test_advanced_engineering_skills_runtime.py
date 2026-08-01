from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from agentic_network.skills import (
    PermissionDecision,
    SkillAuditLogger,
    SkillPermissionStore,
    SkillRegistry,
)
from agentic_network.skills import engineering_runtime
from agentic_network.skills.engineering import (
    ENGINEERING_SKILL_ACTIONS,
    engineering_skill_catalog,
)
from agentic_network.skills.runtime import execute_skill
from app.main import app
from agentic_engineering_network.agents.subagents import SUBAGENT_REGISTRY


ADVANCED_SKILLS = {
    "internet_search",
    "package_registry",
    "requirements_contract",
    "dependency_doctor",
    "runtime_observability",
    "test_quality",
    "architecture_fitness",
    "backup_restore",
    "performance_testing",
    "supply_chain_compliance",
    "release_provenance",
    "deployment_verification",
    "external_integration_verification",
    "ux_quality",
    "git_collaboration",
    "mobile_validation",
    "game_validation",
    "data_pipeline",
    "ml_evaluation",
    "infrastructure_validation",
    "desktop_validation",
    "localization",
    "agent_evaluation",
    "adversarial_red_team",
    "fuzz_property_testing",
    "dependency_remediation",
    "refactor_migration",
    "incident_response",
    "observability_instrumentation",
    "context_quality_evaluation",
    "failure_replay",
    "privacy_data_governance",
    "event_contract",
    "distributed_resilience",
    "synthetic_test_data",
    "feature_flag_management",
    "memory_profiling",
    "cloud_deployment",
    "llm_prompt_regression",
    "accessibility_execution",
    "dependency_provisioning",
    "semantic_code_transformation",
    "test_generation",
    "mutation_testing",
    "visual_regression",
    "service_virtualization",
    "consumer_contract_testing",
    "architecture_refactor_execution",
    "infrastructure_plan_execution",
    "schema_drift_data_evolution",
    "chaos_verification",
    "release_rollback",
    "semantic_repository_search",
    "queue_broker_verification",
    "data_quality_execution",
    "secrets_lifecycle",
    "cross_platform_matrix",
    "documentation_drift",
    "requirements_traceability",
    "git_history_intelligence",
    "database_query_performance",
    "stateful_workflow_verification",
    "concurrency_correctness",
    "reproducible_build_verification",
    "configuration_parity",
    "slo_telemetry_verification",
    "user_journey_synthesis",
    "upgrade_compatibility",
    "disaster_recovery_drill",
    "release_channel_management",
    "clean_machine_certification",
    "signed_vulnerability_intelligence",
    "policy_as_code",
    "formal_model_checking",
    "coverage_guided_test_synthesis",
    "architectural_debt_ledger",
}


def test_project_root_honors_global_filesystem_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allowed_root = Path.cwd().resolve()
    disallowed_root = allowed_root.parent
    monkeypatch.setattr(engineering_runtime, "_allowed_test_temp", lambda _path: False)
    monkeypatch.setenv("ANN_PROJECT_ROOT", str(allowed_root))
    monkeypatch.setenv("ANN_ALLOWED_ROOTS", str(allowed_root))
    monkeypatch.setenv("ANN_BLOCKED_ROOTS", "")
    monkeypatch.setenv("ANN_PROTECTED_PATHS", "")

    assert engineering_runtime._project_root({"project_root": str(allowed_root)}) == allowed_root
    with pytest.raises(ValueError, match="project_root_policy_blocked"):
        engineering_runtime._project_root({"project_root": str(disallowed_root)})


@pytest.fixture(autouse=True)
def allow_pytest_temp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANN_ALLOW_TEMP_SKILL_TARGETS", "1")
    monkeypatch.setenv("ANN_ALLOW_TEMP_PROJECT_PATCH_TARGETS", "1")
    monkeypatch.setenv("TEMP", str(tmp_path.parent))
    monkeypatch.setenv("TMP", str(tmp_path.parent))


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "advanced-project"
    (root / "app").mkdir(parents=True)
    (root / "app" / "main.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'ok': True}\n",
        encoding="utf-8",
    )
    (root / "tests").mkdir()
    (root / "tests" / "test_main.py").write_text(
        "from app.main import health\ndef test_health():\n    assert health()['ok'] is True\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        "[project]\nname='advanced-project'\nversion='1.0.0'\ndependencies=['fastapi==0.116.0']\n",
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text("fastapi==0.116.0\n", encoding="utf-8")
    (root / "requirements.lock").write_text(
        "fastapi==0.116.0 --hash=sha256:" + "a" * 64 + "\n",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "benchmark": "vitest bench --run",
                    "test": "vitest --run",
                    "test:a11y": "playwright test --grep a11y",
                    "test:chaos": "vitest --run chaos",
                    "test:compatibility": "vitest --run compatibility",
                    "test:contract": "vitest --run contract",
                    "test:docs": "vitest --run docs",
                    "test:fuzz": "vitest --run fuzz",
                    "test:memory": "vitest --run memory",
                    "test:mutation": "vitest --run mutation",
                    "test:performance": "vitest bench --run",
                    "test:queue": "vitest --run queue",
                    "test:visual": "playwright test --grep visual",
                },
                "dependencies": {"react": "18.3.1"},
            }
        ),
        encoding="utf-8",
    )
    (root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (root / "docker-compose.yml").write_text(
        "services:\n"
        "  api:\n"
        "    image: ann-api:test\n"
        "    healthcheck:\n"
        "      test: ['CMD', 'python', '-V']\n"
        "  web:\n"
        "    image: ann-web:test\n"
        "  db:\n"
        "    image: postgres:16\n"
        "    volumes:\n"
        "      - db-data:/var/lib/postgresql/data\n"
        "  infra:\n"
        "    image: hashicorp/terraform:1.9\n"
        "volumes:\n"
        "  db-data:\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "# Project\n"
        "Rollback uses the previous release. Performance budget: p95 < 200ms.\n"
        "Backup retention is 30 days and restore tests run weekly.\n"
        "Webhook signatures and idempotency keys are required with retry backoff.\n",
        encoding="utf-8",
    )
    (root / "scripts").mkdir()
    (root / "scripts" / "backup.ps1").write_text("Write-Output backup\n", encoding="utf-8")
    (root / "apps" / "web" / "src").mkdir(parents=True)
    (root / "apps" / "web" / "src" / "App.tsx").write_text(
        "export function App(){return <main aria-label='App' "
        "className='md:grid focus-visible:ring'>Dashboard</main>}\n",
        encoding="utf-8",
    )
    (root / "apps" / "web" / "visual.a11y.spec.ts").write_text(
        "test('visual accessibility', async () => { expect(true).toBe(true) })\n",
        encoding="utf-8",
    )
    (root / "playwright.config.ts").write_text("export default {}\n", encoding="utf-8")
    (root / "locales" / "en").mkdir(parents=True)
    (root / "locales" / "en" / "common.json").write_text(
        '{"dashboard":"Dashboard"}\n', encoding="utf-8"
    )
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (root / "installer").mkdir()
    (root / "installer" / "ANN_Setup.exe").write_bytes(b"test installer")
    (root / "installer" / "signing_evidence.json").write_text(
        '{"signed": true}\n', encoding="utf-8"
    )
    (root / "game.ts").write_text(
        "import * as THREE from 'three';\nrequestAnimationFrame(loop);\n",
        encoding="utf-8",
    )
    (root / "pipeline.py").write_text(
        "def backfill():\n    # lineage upsert checkpoint data quality\n    return True\n",
        encoding="utf-8",
    )
    (root / "model_card.md").write_text(
        "Model card: accuracy, precision, recall, fairness, drift, seed.\n",
        encoding="utf-8",
    )
    (root / "main.tf").write_text(
        'terraform { backend "local" {} }\n',
        encoding="utf-8",
    )
    (root / "alembic.ini").write_text(
        "[alembic]\nscript_location = migrations\n",
        encoding="utf-8",
    )
    (root / "models").mkdir()
    (root / "models" / "must-not-read.txt").write_text("API_KEY=protected-value", encoding="utf-8")
    return root


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
        approval_validator=((lambda *_args: (True, "test_approval")) if approved else None),
    )


def test_all_advanced_skills_are_registered_enabled_and_typed() -> None:
    registry = SkillRegistry()
    catalog = {str(item["name"]): item for item in engineering_skill_catalog()}

    assert ADVANCED_SKILLS.issubset(catalog)
    assert all(registry.get_skill(name) is not None for name in ADVANCED_SKILLS)
    assert all(
        registry.get_skill(name).enabled  # type: ignore[union-attr]
        for name in ADVANCED_SKILLS
    )
    assert all(catalog[name]["actions"] for name in ADVANCED_SKILLS)
    assert len(catalog) == 104
    assert sum(len(item["actions"]) for item in catalog.values()) == 201


def test_semantic_transformation_prepares_token_aware_diff_only(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    source_path = root / "app" / "main.py"
    original = source_path.read_text(encoding="utf-8")
    source_path.write_text(
        original + "\nhealth_label = 'health'\n# health remains a comment\n",
        encoding="utf-8",
    )
    before = source_path.read_text(encoding="utf-8")

    result = _runtime(
        tmp_path,
        "semantic_code_transformation",
        "prepare",
        {
            "project_root": str(root),
            "from_symbol": "health",
            "to_symbol": "health_check",
            "target_paths": ["app/main.py"],
        },
    )

    data = result.output["data"]
    diff = Path(data["diff_path"]).read_text(encoding="utf-8")
    assert result.status == "SUCCESS"
    assert data["replacement_count"] == 1
    assert data["project_modified"] is False
    assert source_path.read_text(encoding="utf-8") == before
    assert "+def health_check():" in diff
    assert "health_label = 'health'" in diff
    assert "-# health remains a comment" not in diff
    assert "+# health remains a comment" not in diff


def test_test_generation_writes_only_a_deterministic_workspace_skeleton(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    before = (root / "app" / "main.py").read_text(encoding="utf-8")
    result = _runtime(
        tmp_path,
        "test_generation",
        "generate",
        {
            "project_root": str(root),
            "module": "app.main",
            "callable": "health",
            "cases": [
                {
                    "id": "healthy",
                    "arguments": {},
                    "expected": {"ok": True},
                }
            ],
        },
    )

    data = result.output["data"]
    skeleton = next(
        Path(path)
        for path in result.output["artifacts"]
        if path.endswith("test_generated_contract.py")
    )
    assert result.status == "SUCCESS"
    assert data["skeleton_generated"] is True
    assert "from app.main import health as subject" in skeleton.read_text(encoding="utf-8")
    assert (root / "app" / "main.py").read_text(encoding="utf-8") == before


def test_architecture_refactor_prepare_reuses_dry_run_patch_gate(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    target = root / "app" / "main.py"
    before = target.read_text(encoding="utf-8")
    patch = root / "refactor.diff"
    patch.write_text(
        "diff --git a/app/main.py b/app/main.py\n"
        "--- a/app/main.py\n"
        "+++ b/app/main.py\n"
        "@@ -3,2 +3,2 @@\n"
        " @app.get('/health')\n"
        "-def health():\n"
        "+def health_check():\n",
        encoding="utf-8",
    )

    result = _runtime(
        tmp_path,
        "architecture_refactor_execution",
        "prepare",
        {"project_root": str(root), "patch_file": "refactor.diff"},
    )

    assert result.status == "SUCCESS"
    assert result.output["data"]["status"] == "DRY_RUN"
    assert result.output["data"]["approval_center_required"] is True
    assert target.read_text(encoding="utf-8") == before


def test_service_virtualization_discards_credentials_and_raw_responses(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    result = _runtime(
        tmp_path,
        "service_virtualization",
        "generate",
        {
            "project_root": str(root),
            "services": [
                {
                    "name": "stripe",
                    "status": 429,
                    "latency_ms": 250,
                    "failure_mode": "rate_limit",
                    "api_key": "must-not-survive",
                    "response": {"secret": "must-not-survive"},
                }
            ],
        },
    )

    encoded = json.dumps(result.output)
    assert result.status == "SUCCESS"
    assert result.output["data"]["credentials_stored"] is False
    assert result.output["data"]["network_used"] is False
    assert "must-not-survive" not in encoded


def test_semantic_search_is_bounded_and_does_not_load_a_model(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    result = _runtime(
        tmp_path,
        "semantic_repository_search",
        "query",
        {
            "project_root": str(root),
            "query": "FastAPI health endpoint",
            "max_results": 3,
        },
    )

    data = result.output["data"]
    assert result.status == "SUCCESS"
    assert 1 <= data["result_count"] <= 3
    assert data["model_loaded"] is False
    assert data["raw_source_stored"] is False
    assert all(
        set(item) == {"path", "score", "matched_terms", "is_test"} for item in data["results"]
    )


def test_requirements_contract_refines_and_arbitrates(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    refined = _runtime(
        tmp_path,
        "requirements_contract",
        "refine",
        {
            "project_root": str(root),
            "user_request": (
                "Build a task API with JWT authentication. Users can create and complete tasks."
            ),
        },
    )

    assert refined.status == "SUCCESS"
    assert len(refined.output["data"]["requirements"]) == 2
    assert Path(refined.output["artifacts"][0]).is_file()

    arbitration = _runtime(
        tmp_path,
        "requirements_contract",
        "arbitrate",
        {
            "project_root": str(root),
            "user_request": "Return an integer task count.",
            "test_plan": "Expect an integer task count.",
        },
    )
    assert arbitration.status == "SUCCESS"
    assert arbitration.output["data"]["owner"] == "USER_REQUEST"


@pytest.mark.parametrize(
    ("skill", "action"),
    [
        ("dependency_doctor", "analyze"),
        ("runtime_observability", "snapshot"),
        ("test_quality", "analyze"),
        ("architecture_fitness", "analyze"),
        ("backup_restore", "inspect"),
        ("performance_testing", "analyze"),
        ("supply_chain_compliance", "scan"),
        ("release_provenance", "inspect"),
        ("deployment_verification", "inspect"),
        ("external_integration_verification", "inspect"),
        ("ux_quality", "analyze"),
        ("mobile_validation", "analyze"),
        ("game_validation", "analyze"),
        ("data_pipeline", "analyze"),
        ("ml_evaluation", "analyze"),
        ("infrastructure_validation", "analyze"),
        ("desktop_validation", "analyze"),
        ("localization", "analyze"),
        ("agent_evaluation", "evaluate"),
        ("adversarial_red_team", "analyze"),
        ("fuzz_property_testing", "inspect"),
        ("dependency_remediation", "analyze"),
        ("refactor_migration", "analyze"),
        ("incident_response", "triage"),
        ("observability_instrumentation", "inspect"),
        ("context_quality_evaluation", "evaluate"),
        ("failure_replay", "prepare"),
        ("privacy_data_governance", "scan"),
        ("event_contract", "analyze"),
        ("distributed_resilience", "analyze"),
        ("synthetic_test_data", "plan"),
        ("feature_flag_management", "analyze"),
        ("memory_profiling", "inspect"),
        ("cloud_deployment", "inspect"),
        ("llm_prompt_regression", "evaluate"),
        ("accessibility_execution", "inspect"),
        ("dependency_provisioning", "inspect"),
        ("semantic_code_transformation", "analyze"),
        ("test_generation", "analyze"),
        ("mutation_testing", "inspect"),
        ("visual_regression", "inspect"),
        ("service_virtualization", "inspect"),
        ("consumer_contract_testing", "analyze"),
        ("architecture_refactor_execution", "analyze"),
        ("infrastructure_plan_execution", "inspect"),
        ("schema_drift_data_evolution", "inspect"),
        ("chaos_verification", "inspect"),
        ("release_rollback", "inspect"),
        ("queue_broker_verification", "inspect"),
        ("data_quality_execution", "inspect"),
        ("secrets_lifecycle", "inspect"),
        ("cross_platform_matrix", "inspect"),
        ("documentation_drift", "analyze"),
    ],
)
def test_advanced_analytical_skills_generate_bounded_evidence(
    tmp_path: Path, skill: str, action: str
) -> None:
    root = _project(tmp_path)

    result = _runtime(
        tmp_path,
        skill,
        action,
        {"project_root": str(root)},
    )

    assert result.status in {"SUCCESS", "PARTIAL"}
    assert result.output["terminal_used"] is False
    assert result.output["internet_used"] is False
    assert result.output["dependency_install_used"] is False
    assert result.output["artifacts"]
    assert all(Path(path).is_file() for path in result.output["artifacts"])
    assert "protected-value" not in json.dumps(result.output)


def test_test_quality_challenges_bad_test_contract(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    result = _runtime(
        tmp_path,
        "test_quality",
        "validate_failure",
        {
            "project_root": str(root),
            "user_request": "The amount must be a float.",
            "test_report": ("tests/test_amount.py AssertionError: expected integer got float"),
            "affected_files": ["tests/test_amount.py"],
        },
    )

    assert result.status == "BLOCKED"
    assert result.output["data"]["classification"] == "TEST_EXPECTATION_SUSPECT"


@pytest.mark.parametrize(
    ("skill", "action"),
    [
        ("backup_restore", "backup"),
        ("backup_restore", "restore"),
        ("performance_testing", "run"),
        ("release_provenance", "verify"),
        ("release_provenance", "sign"),
        ("deployment_verification", "smoke"),
        ("external_integration_verification", "probe"),
        ("internet_search", "search"),
        ("package_registry", "lookup"),
        ("git_collaboration", "status"),
        ("git_collaboration", "branch"),
        ("git_collaboration", "commit"),
        ("git_collaboration", "publish_pr"),
        ("fuzz_property_testing", "run"),
        ("failure_replay", "run"),
        ("memory_profiling", "run"),
        ("accessibility_execution", "run"),
        ("dependency_provisioning", "run"),
        ("mutation_testing", "run"),
        ("visual_regression", "run"),
        ("consumer_contract_testing", "run"),
        ("infrastructure_plan_execution", "run"),
        ("schema_drift_data_evolution", "run"),
        ("chaos_verification", "run"),
        ("release_rollback", "run"),
        ("queue_broker_verification", "run"),
        ("data_quality_execution", "run"),
        ("cross_platform_matrix", "run"),
        ("documentation_drift", "run"),
    ],
)
def test_dangerous_actions_are_blocked_without_approval(
    tmp_path: Path, skill: str, action: str
) -> None:
    root = _project(tmp_path)

    result = _runtime(
        tmp_path,
        skill,
        action,
        {"project_root": str(root)},
    )

    assert result.status == "BLOCKED"
    assert "approval" in " ".join(result.errors).lower()


def test_backup_and_performance_use_only_closed_compose_recipes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        stdout = (
            "CREATE TABLE tasks(id integer);\n" if "pg_dump" in command else "benchmark passed\n"
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fake_run,
    )
    backup = _runtime(
        tmp_path,
        "backup_restore",
        "backup",
        {
            "project_root": str(root),
            "service": "db",
            "database": "postgres",
        },
        approved=True,
    )
    performance = _runtime(
        tmp_path,
        "performance_testing",
        "run",
        {
            "project_root": str(root),
            "service": "api",
            "recipe": "python_pytest_performance",
        },
        approved=True,
    )

    assert backup.status == "SUCCESS"
    assert (
        Path(backup.output["data"]["backup_path"])
        .read_text(encoding="utf-8")
        .startswith("CREATE TABLE")
    )
    assert performance.status == "SUCCESS"
    assert all(kwargs["shell"] is False for _, kwargs in calls)
    assert any("pg_dump" in command for command, _ in calls)
    assert any("performance" in command for command, _ in calls)


def test_restore_passes_sql_as_stdin_not_command_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    backup = root / "backup.sql"
    backup.write_text("CREATE TABLE restored(id integer);\n", encoding="utf-8")
    observed: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["input"] = kwargs.get("input")
        observed["shell"] = kwargs.get("shell")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fake_run,
    )
    result = _runtime(
        tmp_path,
        "backup_restore",
        "restore",
        {
            "project_root": str(root),
            "service": "db",
            "backup_file": "backup.sql",
        },
        approved=True,
    )

    assert result.status == "SUCCESS"
    assert observed["input"].startswith("CREATE TABLE")
    assert "CREATE TABLE" not in observed["command"]
    assert observed["shell"] is False


def test_external_probe_enforces_https_domain_allowlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)

    class Response:
        status = 204
        headers = {"Content-Type": "application/json"}

    class Opener:
        def open(self, request: Any, timeout: int) -> Response:
            assert request.full_url == "https://api.example.com/health"
            assert timeout <= 15
            return Response()

    monkeypatch.setattr(
        "agentic_network.skills.advanced_runtime.build_opener",
        lambda *_args: Opener(),
    )
    result = _runtime(
        tmp_path,
        "external_integration_verification",
        "probe",
        {
            "project_root": str(root),
            "urls": [
                "https://api.example.com/health",
                "http://evil.example.net",
            ],
            "allowed_domains": ["example.com"],
        },
        approved=True,
    )

    assert result.status == "FAILED"
    assert result.output["internet_used"] is True
    assert result.output["data"]["credentials_sent"] is False
    assert result.output["data"]["results"][0]["status"] == "SUCCESS"
    assert result.output["data"]["results"][1]["status"] == "BLOCKED"


def test_internet_search_and_package_registry_are_real_bounded_lookups(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Response:
        def __init__(self, body: bytes) -> None:
            self.body = body

        def read(self, limit: int) -> bytes:
            return self.body[:limit]

    class Opener:
        def open(self, request: Any, timeout: int) -> Response:
            assert timeout <= 15
            if urlparse(request.full_url).hostname == "html.duckduckgo.com":
                return Response(
                    b'<a class="result__a" href="https://docs.example.com/api">'
                    b'Example API</a><div class="result__snippet">Official docs</div>'
                )
            assert "pypi.org/pypi/fastapi/json" in request.full_url
            return Response(
                json.dumps(
                    {
                        "info": {
                            "name": "fastapi",
                            "version": "1.0.0",
                            "summary": "API framework",
                            "license": "MIT",
                        },
                        "releases": {"1.0.0": []},
                    }
                ).encode()
            )

    monkeypatch.setattr(
        "agentic_network.skills.advanced_runtime.build_opener",
        lambda *_args: Opener(),
    )
    search = _runtime(
        tmp_path,
        "internet_search",
        "search",
        {
            "query": "example API",
            "allowed_domains": ["example.com"],
            "max_results": 3,
        },
        approved=True,
    )
    package = _runtime(
        tmp_path,
        "package_registry",
        "lookup",
        {"ecosystem": "pypi", "name": "fastapi"},
        approved=True,
    )

    assert search.status == "SUCCESS"
    assert search.output["data"]["results"][0]["domain"] == "docs.example.com"
    assert search.output["data"]["result_pages_opened"] is False
    assert package.status == "SUCCESS"
    assert package.output["data"]["latest_version"] == "1.0.0"
    assert package.output["data"]["archive_downloaded"] is False
    assert package.output["dependency_install_used"] is False


def test_git_collaboration_rejects_raw_commands_and_uses_shell_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fake_run,
    )
    result = _runtime(
        tmp_path,
        "git_collaboration",
        "branch",
        {
            "project_root": str(root),
            "branch": "agent/safe-feature",
            "command": "git reset --hard",
        },
        approved=True,
    )

    assert result.status == "SUCCESS"
    assert calls[0][0][-3:] == [
        "switch",
        "-c",
        "agent/safe-feature",
    ]
    assert calls[0][1]["shell"] is False
    assert "reset" not in calls[0][0]


def test_git_commit_accepts_only_explicit_project_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fake_run,
    )
    result = _runtime(
        tmp_path,
        "git_collaboration",
        "commit",
        {
            "project_root": str(root),
            "files": ["README.md"],
            "message": "Document the release",
        },
        approved=True,
    )

    assert result.status == "SUCCESS"
    assert len(calls) == 2
    assert calls[0][0][-3:] == ["add", "--", "README.md"]
    assert calls[1][0][-3:] == [
        "commit",
        "-m",
        "Document the release",
    ]
    assert all(kwargs["shell"] is False for _, kwargs in calls)


@pytest.mark.parametrize(
    "payload",
    [
        {"files": ["../outside.txt"], "message": "Unsafe path"},
        {"files": ["README.md"], "message": "safe; git reset --hard"},
    ],
)
def test_git_commit_rejects_traversal_and_command_metacharacters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
) -> None:
    root = _project(tmp_path)
    called = False

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal called
        called = True
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fake_run,
    )
    result = _runtime(
        tmp_path,
        "git_collaboration",
        "commit",
        {"project_root": str(root), **payload},
        approved=True,
    )

    assert result.status == "FAILED"
    assert called is False


def test_external_probe_blocks_suffix_confusion_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    called = False

    class Opener:
        def open(self, request: Any, timeout: int) -> object:
            nonlocal called
            called = True
            raise AssertionError((request, timeout))

    monkeypatch.setattr(
        "agentic_network.skills.advanced_runtime.build_opener",
        lambda *_args: Opener(),
    )
    result = _runtime(
        tmp_path,
        "external_integration_verification",
        "probe",
        {
            "project_root": str(root),
            "urls": ["https://example.com.evil.test/health"],
            "allowed_domains": ["example.com"],
        },
        approved=True,
    )

    assert result.status == "FAILED"
    assert result.output["data"]["results"][0]["status"] == "BLOCKED"
    assert called is False


@pytest.mark.parametrize(
    "url",
    [
        "https://user:password@api.example.com/health",
        "https://api.example.com/health?token=secret",
        "https://api.example.com/health#private",
    ],
)
def test_external_probe_rejects_url_credentials_and_query_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    root = _project(tmp_path)
    called = False

    class Opener:
        def open(self, request: Any, timeout: int) -> object:
            nonlocal called
            called = True
            raise AssertionError((request, timeout))

    monkeypatch.setattr(
        "agentic_network.skills.advanced_runtime.build_opener",
        lambda *_args: Opener(),
    )
    result = _runtime(
        tmp_path,
        "external_integration_verification",
        "probe",
        {
            "project_root": str(root),
            "urls": [url],
            "allowed_domains": ["example.com"],
        },
        approved=True,
    )

    assert result.status == "FAILED"
    assert result.output["data"]["results"][0]["status"] == "BLOCKED"
    assert called is False


def test_search_invalid_domain_filter_fails_closed_before_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called = False

    def fail_open(*_args: Any, **_kwargs: Any) -> object:
        nonlocal called
        called = True
        raise AssertionError("network must not be reached")

    monkeypatch.setattr(
        "agentic_network.skills.advanced_runtime.build_opener",
        fail_open,
    )
    result = _runtime(
        tmp_path,
        "internet_search",
        "search",
        {
            "query": "FastAPI security",
            "allowed_domains": ["localhost"],
        },
        approved=True,
    )

    assert result.status == "BLOCKED"
    assert called is False


@pytest.mark.parametrize(
    ("ecosystem", "name"),
    [
        ("pypi", "../../private"),
        ("pypi", "unsafe..name"),
        ("npm", "@scope/../../private"),
        ("npm", "@../private"),
    ],
)
def test_package_registry_rejects_unsafe_names_before_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ecosystem: str,
    name: str,
) -> None:
    called = False

    def fail_open(*_args: Any, **_kwargs: Any) -> object:
        nonlocal called
        called = True
        raise AssertionError("network must not be reached")

    monkeypatch.setattr(
        "agentic_network.skills.advanced_runtime.build_opener",
        fail_open,
    )
    result = _runtime(
        tmp_path,
        "package_registry",
        "lookup",
        {"ecosystem": ecosystem, "name": name},
        approved=True,
    )

    assert result.status == "BLOCKED"
    assert called is False


def test_release_signing_rejects_unapproved_timestamp_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    (root / "installer" / "sign_release.ps1").write_text("param()\n", encoding="utf-8")
    called = False

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal called
        called = True
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fake_run,
    )
    result = _runtime(
        tmp_path,
        "release_provenance",
        "sign",
        {
            "project_root": str(root),
            "certificate_thumbprint": "A" * 40,
            "timestamp_url": "https://localhost/sign",
        },
        approved=True,
    )

    assert result.status == "FAILED"
    assert called is False


def test_api_catalog_exposes_all_advanced_skills() -> None:
    payload = TestClient(app).get("/api/skills").json()
    names = {item["name"] for item in payload["skills"]}

    assert ADVANCED_SKILLS.issubset(names)
    assert payload["safety"]["raw_shell"] is False
    assert payload["safety"]["mutations_require_approval_center"] is True


def test_agent_evaluation_uses_bounded_evidence_without_model_load(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    result = _runtime(
        tmp_path,
        "agent_evaluation",
        "evaluate",
        {
            "project_root": str(root),
            "cases": [
                {
                    "id": "golden-1",
                    "expected_status": "PASSED",
                    "actual_status": "PASSED",
                    "latency_seconds": 1.25,
                    "tokens": 80,
                    "retries": 0,
                },
                {
                    "id": "golden-2",
                    "expected_status": "PASSED",
                    "actual_status": "FAILED",
                    "latency_seconds": 2,
                    "tokens": 120,
                    "retries": 1,
                },
            ],
        },
    )

    assert result.status == "PARTIAL"
    assert result.output["data"]["success_rate"] == 0.5
    assert result.output["data"]["model_loaded"] is False
    assert result.output["terminal_used"] is False


def test_context_quality_rejects_unsafe_paths_and_scores_retrieval(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    result = _runtime(
        tmp_path,
        "context_quality_evaluation",
        "evaluate",
        {
            "project_root": str(root),
            "expected_paths": ["app/main.py", "tests/test_main.py"],
            "retrieved_paths": [
                "app/main.py",
                "tests/test_main.py",
                "../secrets.txt",
                "models/private.bin",
            ],
            "tokens_used": 900,
            "token_budget": 1_000,
        },
    )

    data = result.output["data"]
    assert result.status == "SUCCESS"
    assert data["precision"] == 1.0
    assert data["recall"] == 1.0
    assert "../secrets.txt" not in data["retrieved_paths"]
    assert "models/private.bin" not in data["retrieved_paths"]


def test_prompt_regression_hashes_outputs_without_storing_or_loading(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    secret_output = "expected answer with private runtime detail"
    result = _runtime(
        tmp_path,
        "llm_prompt_regression",
        "evaluate",
        {
            "project_root": str(root),
            "cases": [
                {
                    "id": "prompt-1",
                    "actual": secret_output,
                    "expected_contains": ["expected answer"],
                }
            ],
        },
    )

    serialized = json.dumps(result.output)
    assert result.status == "SUCCESS"
    assert secret_output not in serialized
    assert result.output["data"]["raw_outputs_stored"] is False
    assert result.output["data"]["model_loaded"] is False


def test_failure_replay_redacts_environment_and_rejects_raw_recipe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    prepared = _runtime(
        tmp_path,
        "failure_replay",
        "prepare",
        {
            "project_root": str(root),
            "recipe": "python_tests",
            "affected_files": ["app/main.py"],
            "stdout": "one failure",
            "environment": {
                "PYTHONHASHSEED": "7",
                "API_TOKEN": "must-not-survive",
            },
        },
    )
    assert prepared.status == "SUCCESS"
    assert prepared.output["data"]["environment"] == {"PYTHONHASHSEED": "7"}
    assert "one failure" not in json.dumps(prepared.output)
    assert "must-not-survive" not in json.dumps(prepared.output)

    called = False

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal called
        called = True
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fake_run,
    )
    blocked = _runtime(
        tmp_path,
        "failure_replay",
        "run",
        {
            "project_root": str(root),
            "recipe": "python -c dangerous",
            "command": "git reset --hard",
        },
        approved=True,
    )
    assert blocked.status == "BLOCKED"
    assert called is False


def test_synthetic_data_is_deterministic_and_workspace_only(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    payload = {
        "project_root": str(root),
        "schema": {
            "id": "uuid",
            "email": "email",
            "age": "integer",
            "active": "boolean",
        },
        "count": 3,
    }
    first = _runtime(tmp_path, "synthetic_test_data", "generate", payload)
    second = _runtime(tmp_path, "synthetic_test_data", "generate", payload)

    first_data = first.output["data"]
    second_data = second.output["data"]
    assert first_data["records"] == second_data["records"]
    assert first_data["contains_real_personal_data"] is False
    assert first_data["project_modified"] is False
    assert all(item["email"].endswith("@example.invalid") for item in first_data["records"])


def test_incident_and_dependency_skills_never_execute_or_store_raw_logs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    called = False

    def fake_run(*_args: Any, **_kwargs: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fake_run,
    )
    incident = _runtime(
        tmp_path,
        "incident_response",
        "postmortem",
        {
            "project_root": str(root),
            "events": ["SECRET incident error after deploy"],
        },
    )
    dependency = _runtime(
        tmp_path,
        "dependency_remediation",
        "plan",
        {
            "project_root": str(root),
            "updates": [{"package": "fastapi", "current": "1.0", "target": "1.1"}],
        },
    )

    assert called is False
    assert "SECRET incident" not in json.dumps(incident.output)
    assert incident.output["data"]["raw_events_stored"] is False
    assert dependency.output["data"]["packages_installed"] is False
    assert dependency.output["data"]["project_modified"] is False


@pytest.mark.parametrize(
    ("skill", "recipe", "expected"),
    [
        ("fuzz_property_testing", "python_fuzz", "fuzz"),
        ("failure_replay", "compose_config", "config"),
        ("memory_profiling", "python_memory", "memory"),
        ("accessibility_execution", "web_accessibility", "test:a11y"),
        ("dependency_provisioning", "python_dependency_lock", "--require-hashes"),
        ("mutation_testing", "python_mutation", "mutmut"),
        ("visual_regression", "web_visual", "test:visual"),
        ("consumer_contract_testing", "python_contract", "contract"),
        ("infrastructure_plan_execution", "terraform_plan", "plan"),
        ("schema_drift_data_evolution", "python_schema_drift", "alembic"),
        ("chaos_verification", "python_chaos", "chaos"),
        ("release_rollback", "python_release_rollback", "release_rollback"),
        ("queue_broker_verification", "python_queue", "queue"),
        ("data_quality_execution", "python_data_quality", "data_quality"),
        ("cross_platform_matrix", "python_compatibility", "compatibility"),
        ("documentation_drift", "python_docs", "docs"),
    ],
)
def test_specialist_execution_uses_closed_compose_recipes_and_shell_false(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    skill: str,
    recipe: str,
    expected: str,
) -> None:
    root = _project(tmp_path)
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "passed", "")

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fake_run,
    )
    result = _runtime(
        tmp_path,
        skill,
        "run",
        {
            "project_root": str(root),
            "recipe": recipe,
            "command": "git reset --hard",
        },
        approved=True,
    )

    assert result.status == "SUCCESS"
    assert len(calls) == 1
    assert calls[0][1]["shell"] is False
    assert expected in calls[0][0]
    assert "reset" not in calls[0][0]
    if recipe != "compose_config":
        assert "--pull" in calls[0][0]
        assert "never" in calls[0][0]


def test_all_specialist_skills_are_delegated_to_controlled_subagents() -> None:
    tools = {tool for item in SUBAGENT_REGISTRY for tool in item.tools}
    specialist = ADVANCED_SKILLS - {
        "architecture_fitness",
        "backup_restore",
        "data_pipeline",
        "dependency_doctor",
        "deployment_verification",
        "desktop_validation",
        "external_integration_verification",
        "game_validation",
        "git_collaboration",
        "infrastructure_validation",
        "internet_search",
        "localization",
        "ml_evaluation",
        "mobile_validation",
        "package_registry",
        "performance_testing",
        "release_provenance",
        "requirements_contract",
        "runtime_observability",
        "supply_chain_compliance",
        "test_quality",
        "ux_quality",
    }

    assert specialist.issubset(tools)


def test_dependency_provisioning_requires_a_hashed_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    (root / "requirements.lock").write_text("fastapi==0.116.0\n", encoding="utf-8")
    called = False

    def fail_run(*_args: Any, **_kwargs: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fail_run,
    )
    result = _runtime(
        tmp_path,
        "dependency_provisioning",
        "run",
        {"project_root": str(root)},
        approved=True,
    )

    assert result.status == "BLOCKED"
    assert called is False
    assert "hashes" in " ".join(result.errors)


def test_specialist_execution_blocks_docker_socket_mounts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    compose = root / "docker-compose.yml"
    compose.write_text(
        compose.read_text(encoding="utf-8").replace(
            "  api:\n    image: ann-api:test\n",
            "  api:\n"
            "    image: ann-api:test\n"
            "    volumes:\n"
            "      - /var/run/docker.sock:/var/run/docker.sock\n",
        ),
        encoding="utf-8",
    )
    called = False

    def fail_run(*_args: Any, **_kwargs: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fail_run,
    )
    result = _runtime(
        tmp_path,
        "chaos_verification",
        "run",
        {"project_root": str(root)},
        approved=True,
    )

    assert result.status == "BLOCKED"
    assert called is False
    assert "docker_socket_mount" in result.errors


def test_infrastructure_plan_blocks_executable_terraform_hooks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _project(tmp_path)
    (root / "main.tf").write_text(
        'data "external" "unsafe" {\n  program = ["cmd", "/c", "whoami"]\n}\n',
        encoding="utf-8",
    )
    called = False

    def fail_run(*_args: Any, **_kwargs: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime.subprocess.run",
        fail_run,
    )
    result = _runtime(
        tmp_path,
        "infrastructure_plan_execution",
        "run",
        {"project_root": str(root)},
        approved=True,
    )

    assert result.status == "BLOCKED"
    assert called is False
    assert "terraform_executable_hooks_blocked" in result.errors
