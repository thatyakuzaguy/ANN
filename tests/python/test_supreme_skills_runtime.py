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
from agentic_network.skills.runtime import execute_skill
from agentic_network.skills.supreme_runtime import SUPREME_SKILLS
from agentic_engineering_network.agents.subagents import SUBAGENT_REGISTRY


@pytest.fixture(autouse=True)
def allow_pytest_temp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANN_ALLOW_TEMP_SKILL_TARGETS", "1")
    monkeypatch.setenv("TEMP", str(tmp_path.parent))
    monkeypatch.setenv("TMP", str(tmp_path.parent))


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "supreme-project"
    (root / "app").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "docs").mkdir()
    (root / "assets").mkdir()
    (root / "app" / "api.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/tasks')\n"
        "def list_tasks(current_user, tenant_id: str):\n"
        "    # permission and RBAC tenant invariant: tenant_id must match\n"
        "    return []\n",
        encoding="utf-8",
    )
    (root / "app" / "client.ts").write_text(
        "import { Task } from './types';\nexport function listTasks(): Task[] { return []; }\n",
        encoding="utf-8",
    )
    (root / "app" / "types.ts").write_text(
        "export interface Task { id: string; tenant_id: string }\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_behavior.py").write_text(
        "# behavioral_oracle authorization checkpoint_integrity flaky_investigation\n"
        "# online_migration installer_vm_lab model_runtime api_abuse performance_history\n"
        "def test_tasks():\n    assert True\n",
        encoding="utf-8",
    )
    (root / "docs" / "SPEC.md").write_text(
        "The API must list tasks only for the active tenant.\n"
        "Use checkpoint and idempotency before resume. Rollback must be supported.\n",
        encoding="utf-8",
    )
    (root / "docker-compose.yml").write_text(
        "services:\n  api:\n    image: ann-supreme-api:test\n",
        encoding="utf-8",
    )
    (root / "assets" / "logo.svg").write_text("<svg></svg>\n", encoding="utf-8")
    (root / "ATTRIBUTIONS.md").write_text("logo.svg: original project asset\n", encoding="utf-8")
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


def test_supreme_skills_are_registered_packaged_and_delegated() -> None:
    registry = SkillRegistry()
    delegated = {tool for item in SUBAGENT_REGISTRY for tool in item.tools}

    assert len(SUPREME_SKILLS) == 18
    assert SUPREME_SKILLS.issubset(ENGINEERING_SKILL_ACTIONS)
    assert SUPREME_SKILLS.issubset(delegated)
    assert len(ENGINEERING_SKILL_ACTIONS) == 104
    assert sum(len(actions) for actions in ENGINEERING_SKILL_ACTIONS.values()) == 201
    for name in SUPREME_SKILLS:
        assert registry.get_skill(name) is not None
        assert (Path("agentic_network/skills_builtin") / name / "SKILL.md").is_file()


@pytest.mark.parametrize(
    ("skill", "action", "extra"),
    [
        ("project_archetype_synthesis", "synthesize", {"request": "Build a FastAPI service"}),
        ("behavioral_acceptance_oracle", "analyze", {"requirements": [{"id": "REQ-1", "statement": "tasks behavior"}]}),
        ("dynamic_authorization_verification", "inspect", {}),
        ("long_horizon_checkpoint_integrity", "inspect", {}),
        ("agent_trajectory_forensics", "analyze", {"trajectories": [{"id": "t1", "events": [{"status": "passed", "evidence": "artifact"}]}]}),
        ("delegation_optimizer", "plan", {"assignments": [{"owner": "qa", "objective": "verify", "acceptance_criteria": ["green"]}]}),
        ("cross_language_semantic_graph", "scan", {}),
        ("flaky_test_investigator", "analyze", {"runs": [{"test": "test_tasks", "status": "PASSED", "duration_seconds": 1.0}]}),
        ("online_migration_rehearsal", "inspect", {}),
        ("local_resource_guardian", "snapshot", {"quota_bytes": 10_000_000}),
        ("secure_update_delivery", "inspect", {}),
        ("installer_vm_lab", "inspect", {}),
        ("model_runtime_certification", "inspect", {}),
        ("api_abuse_simulation", "inspect", {}),
        ("performance_regression_bisect", "analyze", {"revisions": [{"revision": "a", "latency_ms": 10}, {"revision": "b", "latency_ms": 10.5}]}),
        ("asset_provenance", "scan", {"provenance": {"assets/logo.svg": {"license": "original"}}}),
        ("domain_invariant_mining", "generate", {}),
        ("ai_governance_evidence", "assess", {}),
    ],
)
def test_every_supreme_skill_emits_bounded_read_only_evidence(
    tmp_path: Path,
    skill: str,
    action: str,
    extra: dict[str, object],
) -> None:
    root = _project(tmp_path)
    before = (root / "app" / "api.py").read_text(encoding="utf-8")
    result = _runtime(tmp_path, skill, action, {"project_root": str(root), **extra})

    assert result.status in {"SUCCESS", "PARTIAL"}
    assert result.output["terminal_used"] is False
    assert result.output["internet_used"] is False
    assert result.output["dependency_install_used"] is False
    assert result.output["data"]["project_modified"] is False
    assert result.output["data"]["bounded"] is True
    assert all(Path(path).is_file() for path in result.output["artifacts"])
    assert (root / "app" / "api.py").read_text(encoding="utf-8") == before


def test_high_assurance_evidence_never_fakes_success(tmp_path: Path) -> None:
    root = _project(tmp_path)
    incomplete = _runtime(
        tmp_path,
        "secure_update_delivery",
        "verify",
        {"project_root": str(root), "metadata": {"root": {}}},
    )
    complete_metadata = {
        name: {"signatures": ["verified"]} for name in ("root", "timestamp", "snapshot", "targets")
    }
    complete_metadata["targets"]["hashes"] = {"ann.exe": "a" * 64}
    complete_metadata.update(
        {"version_monotonic": True, "not_expired": True, "rollback_protected": True}
    )
    complete = _runtime(
        tmp_path,
        "secure_update_delivery",
        "verify",
        {"project_root": str(root), "metadata": complete_metadata},
    )

    assert incomplete.status == "PARTIAL"
    assert complete.status == "SUCCESS"
    assert complete.output["data"]["download_performed"] is False
    assert complete.output["data"]["install_performed"] is False


def test_cross_language_graph_and_performance_bisect_are_concrete(tmp_path: Path) -> None:
    root = _project(tmp_path)
    graph = _runtime(
        tmp_path,
        "cross_language_semantic_graph",
        "impact",
        {"project_root": str(root), "targets": ["types"]},
    )
    bisect = _runtime(
        tmp_path,
        "performance_regression_bisect",
        "analyze",
        {
            "project_root": str(root),
            "metric": "latency_ms",
            "regression_percent": 10,
            "revisions": [
                {"revision": "good", "latency_ms": 10},
                {"revision": "bad", "latency_ms": 13},
            ],
        },
    )

    assert graph.output["data"]["language_counts"]["py"] >= 1
    assert graph.output["data"]["language_counts"]["ts"] >= 1
    assert graph.output["data"]["impacted"]
    assert bisect.status == "PARTIAL"
    assert bisect.output["data"]["first_regression"]["revision"] == "bad"
    assert bisect.output["data"]["git_history_modified"] is False


@pytest.mark.parametrize(
    ("skill", "action", "recipe", "marker"),
    [
        ("behavioral_acceptance_oracle", "run", "python_behavioral_oracle", "behavioral_oracle"),
        ("dynamic_authorization_verification", "run", "python_authorization", "authorization"),
        ("long_horizon_checkpoint_integrity", "run", "python_checkpoint", "checkpoint_integrity"),
        ("flaky_test_investigator", "run", "python_flaky", "flaky_investigation"),
        ("online_migration_rehearsal", "run", "python_online_migration", "online_migration"),
        ("installer_vm_lab", "run", "python_installer_vm", "installer_vm_lab"),
        ("model_runtime_certification", "benchmark", "python_model_runtime", "model_runtime"),
        ("api_abuse_simulation", "run", "python_api_abuse", "api_abuse"),
        ("performance_regression_bisect", "run", "python_performance_bisect", "performance_history"),
    ],
)
def test_executable_supreme_skills_use_closed_approved_compose_recipes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    skill: str,
    action: str,
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
        action,
        {"project_root": str(root), "recipe": recipe, "command": "git reset --hard"},
        approved=True,
    )

    assert result.status == "SUCCESS"
    command, kwargs = calls[0]
    assert kwargs["shell"] is False
    assert marker in command
    assert "reset" not in command
    assert command.count("--pull") == 1
    assert "never" in command


def test_resource_cleanup_is_isolated_and_approval_gated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert kwargs["shell"] is False
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "removed", "")

    monkeypatch.setattr("agentic_network.skills.engineering_runtime.subprocess.run", fake_run)
    blocked = _runtime(
        tmp_path,
        "local_resource_guardian",
        "cleanup",
        {"project_root": str(root)},
    )
    approved = _runtime(
        tmp_path,
        "local_resource_guardian",
        "cleanup",
        {"project_root": str(root), "host_path": "C:\\"},
        approved=True,
    )

    assert blocked.status == "BLOCKED"
    assert approved.status == "SUCCESS"
    assert len(calls) == 1
    assert calls[0][-2:] == ["down", "--remove-orphans"]
    assert "C:\\" not in calls[0]


def test_unknown_recipe_and_unapproved_execution_never_run(
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
        "api_abuse_simulation",
        "run",
        {"project_root": str(root), "recipe": "python_api_abuse"},
    )
    unknown = _runtime(
        tmp_path,
        "api_abuse_simulation",
        "run",
        {"project_root": str(root), "recipe": "python -c unsafe"},
        approved=True,
    )

    assert unapproved.status == "BLOCKED"
    assert unknown.status == "BLOCKED"
    assert called is False


def test_artifacts_do_not_contain_supplied_secret_values(tmp_path: Path) -> None:
    root = _project(tmp_path)
    secret = "super-secret-value-that-must-not-be-recorded"
    result = _runtime(
        tmp_path,
        "agent_trajectory_forensics",
        "analyze",
        {
            "project_root": str(root),
            "trajectories": [
                {
                    "id": "trace",
                    "prompt": secret,
                    "events": [{"status": "passed", "secret": secret}],
                }
            ],
        },
    )

    assert secret not in json.dumps(result.output)
