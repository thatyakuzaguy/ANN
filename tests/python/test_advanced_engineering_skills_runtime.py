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
}


def test_project_root_honors_global_filesystem_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    allowed_root = Path.cwd().resolve()
    disallowed_root = allowed_root.parent
    monkeypatch.setattr(
        engineering_runtime, "_allowed_test_temp", lambda _path: False
    )
    monkeypatch.setenv("ANN_PROJECT_ROOT", str(allowed_root))
    monkeypatch.setenv("ANN_ALLOWED_ROOTS", str(allowed_root))
    monkeypatch.setenv("ANN_BLOCKED_ROOTS", "")
    monkeypatch.setenv("ANN_PROTECTED_PATHS", "")

    assert engineering_runtime._project_root(
        {"project_root": str(allowed_root)}
    ) == allowed_root
    with pytest.raises(ValueError, match="project_root_policy_blocked"):
        engineering_runtime._project_root(
            {"project_root": str(disallowed_root)}
        )


@pytest.fixture(autouse=True)
def allow_pytest_temp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ANN_ALLOW_TEMP_SKILL_TARGETS", "1")
    monkeypatch.setenv(
        "ANN_ALLOW_TEMP_PROJECT_PATCH_TARGETS", "1"
    )
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
        "from app.main import health\n"
        "def test_health():\n"
        "    assert health()['ok'] is True\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        "[project]\nname='advanced-project'\n"
        "version='1.0.0'\ndependencies=['fastapi==0.116.0']\n",
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text(
        "fastapi==0.116.0\n", encoding="utf-8"
    )
    (root / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "benchmark": "vitest bench --run",
                    "test:performance": "vitest bench --run",
                },
                "dependencies": {"react": "18.3.1"},
            }
        ),
        encoding="utf-8",
    )
    (root / "pnpm-lock.yaml").write_text(
        "lockfileVersion: '9.0'\n", encoding="utf-8"
    )
    (root / "docker-compose.yml").write_text(
        "services:\n"
        "  api:\n"
        "    image: ann-api:test\n"
        "    healthcheck:\n"
        "      test: ['CMD', 'python', '-V']\n"
        "  db:\n"
        "    image: postgres:16\n"
        "    volumes:\n"
        "      - db-data:/var/lib/postgresql/data\n"
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
    (root / "scripts" / "backup.ps1").write_text(
        "Write-Output backup\n", encoding="utf-8"
    )
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
    (root / "playwright.config.ts").write_text(
        "export default {}\n", encoding="utf-8"
    )
    (root / "locales" / "en").mkdir(parents=True)
    (root / "locales" / "en" / "common.json").write_text(
        '{"dashboard":"Dashboard"}\n', encoding="utf-8"
    )
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (root / "installer").mkdir()
    (root / "installer" / "ANN_Setup.exe").write_bytes(
        b"test installer"
    )
    (root / "installer" / "signing_evidence.json").write_text(
        '{"signed": true}\n', encoding="utf-8"
    )
    (root / "game.ts").write_text(
        "import * as THREE from 'three';\n"
        "requestAnimationFrame(loop);\n",
        encoding="utf-8",
    )
    (root / "pipeline.py").write_text(
        "def backfill():\n"
        "    # lineage upsert checkpoint data quality\n"
        "    return True\n",
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
    (root / "models").mkdir()
    (root / "models" / "must-not-read.txt").write_text(
        "API_KEY=protected-value", encoding="utf-8"
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
    registry = SkillRegistry()
    store = SkillPermissionStore(tmp_path / "permissions.json")
    spec = next(
        item
        for item in ENGINEERING_SKILL_ACTIONS[skill]
        if item.name == action
    )
    for permission in spec.permissions:
        store.set_permission(
            skill, permission, PermissionDecision.ALLOW_ALWAYS
        )
    return execute_skill(
        skill,
        action,
        payload,
        registry=registry,
        store=store,
        audit_logger=SkillAuditLogger(
            tmp_path / "skill-outputs"
        ),
        approval_validator=(
            (lambda *_args: (True, "test_approval"))
            if approved
            else None
        ),
    )


def test_all_advanced_skills_are_registered_enabled_and_typed() -> None:
    registry = SkillRegistry()
    catalog = {
        str(item["name"]): item
        for item in engineering_skill_catalog()
    }

    assert ADVANCED_SKILLS.issubset(catalog)
    assert all(
        registry.get_skill(name) is not None
        for name in ADVANCED_SKILLS
    )
    assert all(
        registry.get_skill(name).enabled  # type: ignore[union-attr]
        for name in ADVANCED_SKILLS
    )
    assert all(catalog[name]["actions"] for name in ADVANCED_SKILLS)


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
                "Build a task API with JWT authentication. "
                "Users can create and complete tasks."
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
    assert all(
        Path(path).is_file() for path in result.output["artifacts"]
    )
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
            "test_report": (
                "tests/test_amount.py AssertionError: "
                "expected integer got float"
            ),
            "affected_files": ["tests/test_amount.py"],
        },
    )

    assert result.status == "BLOCKED"
    assert (
        result.output["data"]["classification"]
        == "TEST_EXPECTATION_SUSPECT"
    )


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

    def fake_run(
        command: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        stdout = (
            "CREATE TABLE tasks(id integer);\n"
            if "pg_dump" in command
            else "benchmark passed\n"
        )
        return subprocess.CompletedProcess(
            command, 0, stdout=stdout, stderr=""
        )

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
    assert Path(
        backup.output["data"]["backup_path"]
    ).read_text(encoding="utf-8").startswith("CREATE TABLE")
    assert performance.status == "SUCCESS"
    assert all(kwargs["shell"] is False for _, kwargs in calls)
    assert any("pg_dump" in command for command, _ in calls)
    assert any(
        "performance" in command for command, _ in calls
    )


def test_restore_passes_sql_as_stdin_not_command_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    backup = root / "backup.sql"
    backup.write_text(
        "CREATE TABLE restored(id integer);\n", encoding="utf-8"
    )
    observed: dict[str, Any] = {}

    def fake_run(
        command: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["input"] = kwargs.get("input")
        observed["shell"] = kwargs.get("shell")
        return subprocess.CompletedProcess(
            command, 0, stdout="", stderr=""
        )

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
                    b"Example API</a><div class=\"result__snippet\">Official docs</div>"
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

    def fake_run(
        command: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command, 0, stdout="", stderr=""
        )

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

    def fake_run(
        command: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command, 0, stdout="", stderr=""
        )

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

    def fake_run(
        command: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
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
    (root / "installer" / "sign_release.ps1").write_text(
        "param()\n", encoding="utf-8"
    )
    called = False

    def fake_run(
        command: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
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
