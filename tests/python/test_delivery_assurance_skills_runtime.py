from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
from agentic_network.skills.advanced_runtime import _walk
from agentic_network.skills.engineering_runtime import (
    RecipeResult,
    _backup_restore_command,
)
from agentic_network.skills.runtime import execute_skill
from agentic_engineering_network.agents.subagents import SUBAGENT_REGISTRY


DELIVERY_ASSURANCE_SKILLS = {
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


@pytest.fixture(autouse=True)
def allow_pytest_temp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANN_ALLOW_TEMP_SKILL_TARGETS", "1")
    monkeypatch.setenv("TEMP", str(tmp_path.parent))
    monkeypatch.setenv("TMP", str(tmp_path.parent))


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "delivery-project"
    (root / "app").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "docs").mkdir()
    (root / "app" / "workflow.py").write_text(
        "# REQ-001 architecture debt TODO\n"
        "import asyncio\n"
        "async def complete_task():\n"
        "    lock = asyncio.Lock()\n"
        "    async with lock:\n"
        "        return 'completed'\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_workflow.py").write_text(
        "# REQ-001 stateful_workflow concurrency telemetry\n"
        "def test_complete_task():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    (root / "docs" / "SPEC.md").write_text(
        "# REQ-001\nArchitecture requires a tested task completion workflow.\n",
        encoding="utf-8",
    )
    (root / ".env.example").write_text("DATABASE_URL=\nJWT_SECRET=\n", encoding="utf-8")
    (root / ".env.test.example").write_text("DATABASE_URL=\nJWT_SECRET=\n", encoding="utf-8")
    (root / "requirements.lock").write_text(
        "fastapi==1.0 --hash=sha256:" + "a" * 64 + "\n",
        encoding="utf-8",
    )
    (root / "docker-compose.yml").write_text(
        "services:\n"
        "  api:\n"
        "    image: ann-delivery-api:test\n"
        "  web:\n"
        "    image: ann-delivery-web:test\n",
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "test:concurrency": "vitest --run concurrency",
                    "test:formal": "vitest --run formal",
                    "test:policy": "vitest --run policy",
                    "test:reproducible": "vitest --run reproducible",
                    "test:stateful": "vitest --run stateful",
                    "test:telemetry": "vitest --run telemetry",
                    "test:upgrade": "vitest --run upgrade",
                }
            }
        ),
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


def test_all_delivery_assurance_skills_are_registered_and_delegated() -> None:
    registry = SkillRegistry()
    delegated = {tool for item in SUBAGENT_REGISTRY for tool in item.tools}

    assert DELIVERY_ASSURANCE_SKILLS.issubset(ENGINEERING_SKILL_ACTIONS)
    assert DELIVERY_ASSURANCE_SKILLS.issubset(delegated)
    for name in DELIVERY_ASSURANCE_SKILLS:
        skill = registry.get_skill(name)
        assert skill is not None
        assert skill.enabled is True
        assert (Path("agentic_network/skills_builtin") / name / "SKILL.md").is_file()


@pytest.mark.parametrize(
    ("skill", "action"),
    [
        ("database_query_performance", "inspect"),
        ("stateful_workflow_verification", "analyze"),
        ("concurrency_correctness", "inspect"),
        ("reproducible_build_verification", "inspect"),
        ("slo_telemetry_verification", "inspect"),
        ("upgrade_compatibility", "inspect"),
        ("disaster_recovery_drill", "inspect"),
        ("policy_as_code", "inspect"),
        ("formal_model_checking", "inspect"),
    ],
)
def test_analytical_skills_emit_bounded_read_only_evidence(
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
    assert result.output["data"]["safety"]["project_modified"] is False


def test_requirements_are_traced_to_source_and_tests(tmp_path: Path) -> None:
    root = _project(tmp_path)
    result = _runtime(
        tmp_path,
        "requirements_traceability",
        "verify",
        {
            "project_root": str(root),
            "requirements": [{"id": "REQ-001", "statement": "Complete tasks"}],
        },
    )

    trace = result.output["data"]["requirements"][0]
    assert result.status == "SUCCESS"
    assert trace["references"]["implementation"] == ["app/workflow.py"]
    assert trace["references"]["tests"] == ["tests/test_workflow.py"]
    assert trace["missing_required_evidence"] == []


def test_configuration_parity_never_reads_values(tmp_path: Path) -> None:
    root = _project(tmp_path)
    result = _runtime(
        tmp_path,
        "configuration_parity",
        "analyze",
        {"project_root": str(root)},
    )

    assert result.status == "SUCCESS"
    assert result.output["data"]["parity"] is True
    assert result.output["data"]["secret_values_read"] is False
    assert "JWT_SECRET" in result.output["data"]["expected_keys"]


def test_user_journeys_and_coverage_plans_are_workspace_only(tmp_path: Path) -> None:
    root = _project(tmp_path)
    before = (root / "app" / "workflow.py").read_text(encoding="utf-8")
    journey = _runtime(
        tmp_path,
        "user_journey_synthesis",
        "generate",
        {
            "project_root": str(root),
            "stories": [
                {
                    "id": "J-1",
                    "persona": "member",
                    "goal": "Complete a task",
                    "steps": ["Open task", "Mark complete"],
                    "expected_outcomes": ["Task is completed"],
                }
            ],
        },
    )
    coverage = _runtime(
        tmp_path,
        "coverage_guided_test_synthesis",
        "generate",
        {
            "project_root": str(root),
            "coverage": [
                {
                    "path": "app/workflow.py",
                    "uncovered_lines": [4, 5],
                    "uncovered_branches": 1,
                    "critical": True,
                }
            ],
            "surviving_mutants": [{"path": "app/workflow.py"}],
        },
    )

    assert journey.status == "SUCCESS"
    assert journey.output["data"]["generated_test_code"] is False
    assert coverage.status == "SUCCESS"
    assert coverage.output["data"]["gaps"][0]["priority_score"] == 29
    assert coverage.output["data"]["project_modified"] is False
    assert (root / "app" / "workflow.py").read_text(encoding="utf-8") == before


def test_certification_gates_never_fake_success(tmp_path: Path) -> None:
    root = _project(tmp_path)
    incomplete = _runtime(
        tmp_path,
        "clean_machine_certification",
        "verify",
        {"project_root": str(root), "evidence": {"isolated_machine": True}},
    )
    complete = _runtime(
        tmp_path,
        "clean_machine_certification",
        "verify",
        {
            "project_root": str(root),
            "evidence": {
                "isolated_machine": True,
                "clean_before": True,
                "installer_sha256": "a" * 64,
                "steps": [
                    {"name": name, "status": "PASSED"}
                    for name in ("install", "first_run", "uninstall", "residue_scan")
                ],
            },
        },
    )

    assert incomplete.status == "BLOCKED"
    assert incomplete.output["data"]["host_installer_executed"] is False
    assert complete.status == "SUCCESS"
    assert complete.output["data"]["certified"] is True


def test_signed_vulnerability_feed_requires_fresh_signature_evidence(
    tmp_path: Path,
) -> None:
    root = _project(tmp_path)
    now = datetime.now(timezone.utc)
    verification = {
        "signature_verified": True,
        "feed_sha256": "b" * 64,
        "signer_fingerprint": "c" * 64,
        "algorithm": "ed25519",
        "generated_at": (now - timedelta(hours=1)).isoformat(),
        "expires_at": (now + timedelta(days=1)).isoformat(),
        "entry_count": 500,
    }
    passed = _runtime(
        tmp_path,
        "signed_vulnerability_intelligence",
        "verify",
        {"project_root": str(root), "verification": verification},
    )
    verification["signature_verified"] = False
    blocked = _runtime(
        tmp_path,
        "signed_vulnerability_intelligence",
        "verify",
        {"project_root": str(root), "verification": verification},
    )

    assert passed.status == "SUCCESS"
    assert passed.output["data"]["feed_loaded"] is False
    assert passed.output["internet_used"] is False
    assert blocked.status == "BLOCKED"


def test_release_channels_and_debt_trends_are_deterministic(tmp_path: Path) -> None:
    root = _project(tmp_path)
    channels = _runtime(
        tmp_path,
        "release_channel_management",
        "verify",
        {
            "project_root": str(root),
            "channels": [
                {
                    "name": name,
                    "version": f"1.0.0-{name}",
                    "artifact_sha256": "d" * 64,
                    "rollback_supported": True,
                    "compatibility_verified": True,
                }
                for name in ("alpha", "beta", "rc", "stable")
            ],
        },
    )
    debt = _runtime(
        tmp_path,
        "architectural_debt_ledger",
        "compare",
        {
            "project_root": str(root),
            "baseline": {"complexity": 10, "cycles": 1},
            "current": {"complexity": 8, "cycles": 2},
        },
    )

    assert channels.status == "SUCCESS"
    assert channels.output["data"]["release_published"] is False
    assert debt.status == "PARTIAL"
    assert debt.output["data"]["trend"] == "REGRESSING"
    assert debt.output["data"]["regressed_metrics"] == ["cycles"]


@pytest.mark.parametrize(
    ("skill", "recipe", "marker"),
    [
        ("database_query_performance", "python_db_performance", "db_performance"),
        ("stateful_workflow_verification", "python_stateful_workflow", "stateful_workflow"),
        ("concurrency_correctness", "python_concurrency", "concurrency"),
        ("reproducible_build_verification", "python_reproducible_build", "reproducible_build"),
        ("slo_telemetry_verification", "python_telemetry", "telemetry"),
        ("upgrade_compatibility", "python_upgrade_compatibility", "upgrade_compatibility"),
        ("disaster_recovery_drill", "python_disaster_recovery", "disaster_recovery"),
        ("policy_as_code", "python_policy", "policy"),
        ("formal_model_checking", "python_formal_model", "formal_model"),
    ],
)
def test_executable_skills_use_closed_compose_recipes(
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
            "command": "git reset --hard",
        },
        approved=True,
    )

    assert result.status == "SUCCESS"
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert kwargs["shell"] is False
    assert marker in command
    assert "reset" not in command
    assert command.count("--pull") == 1
    assert "never" in command


def test_unapproved_and_unknown_recipes_never_execute(
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
        "concurrency_correctness",
        "run",
        {"project_root": str(root), "recipe": "python_concurrency"},
    )
    unknown = _runtime(
        tmp_path,
        "concurrency_correctness",
        "run",
        {"project_root": str(root), "recipe": "python -c unsafe"},
        approved=True,
    )

    assert unapproved.status == "BLOCKED"
    assert unknown.status == "BLOCKED"
    assert called is False


def test_git_history_is_bounded_and_pseudonymized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        output = (
            "ANN_COMMIT\tabcdef1234567890\tJane Developer\t2026-07-31T10:00:00Z\tFix race\n"
            "app/workflow.py\n"
            "tests/test_workflow.py\n"
        )
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr("agentic_network.skills.engineering_runtime.subprocess.run", fake_run)
    result = _runtime(
        tmp_path,
        "git_history_intelligence",
        "analyze",
        {
            "project_root": str(root),
            "max_commits": 25,
            "command": "git show --all",
        },
        approved=True,
    )

    encoded = json.dumps(result.output)
    assert result.status == "SUCCESS"
    assert result.output["data"]["commit_count"] == 1
    assert result.output["data"]["authors_pseudonymized"] is True
    assert "Jane Developer" not in encoded
    assert "Fix race" not in encoded
    assert calls[0][-3:] == ["-n", "25", "--"]
    assert "show" not in calls[0]


def test_repository_walk_does_not_follow_file_symlinks(tmp_path: Path) -> None:
    root = _project(tmp_path)
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("must not be scanned", encoding="utf-8")
    link = root / "linked-secret.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("File symlinks are unavailable on this Windows account.")

    scanned = _walk(root)

    assert link not in scanned
    assert outside not in scanned


def test_database_backup_ignores_result_supplied_source_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "backup-project"
    root.mkdir()
    (root / "docker-compose.yml").write_text(
        "services:\n  db:\n    image: postgres:16\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "skill-workspace"
    workspace.mkdir()
    outside = tmp_path / "attacker-controlled.sql"
    outside.write_text("unsafe backup", encoding="utf-8")
    captured_artifact: list[Path] = []

    def fake_recipe(*_args: Any, **_kwargs: Any) -> RecipeResult:
        artifact = _kwargs["stdout_artifact"]
        assert isinstance(artifact, Path)
        captured_artifact.append(artifact)
        artifact.write_text("safe backup", encoding="utf-8")
        return RecipeResult(
            name="postgres_backup",
            status="SUCCESS",
            command=["docker", "compose", "exec", "db", "pg_dump"],
            exit_code=0,
            stdout_path=str(outside),
            stderr_path=str(workspace / "postgres_backup_stderr.log"),
            duration_seconds=0.1,
            error="",
        )

    monkeypatch.setattr(
        "agentic_network.skills.engineering_runtime._run_recipe", fake_recipe
    )

    result = _backup_restore_command(
        "backup", {"service": "db"}, workspace, root.resolve()
    )

    assert result["status"] == "SUCCESS"
    assert captured_artifact == [workspace / "postgres_backup.sql"]
    assert (workspace / "postgres_backup.sql").read_text(encoding="utf-8") == "safe backup"
