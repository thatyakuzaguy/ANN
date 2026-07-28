from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path

import pytest

from agentic_network.skills import PermissionDecision, SkillAuditLogger, SkillPermissionStore, SkillRegistry
from agentic_network.skills.runtime import execute_skill
from agentic_network.skills_builtin.documentation.runtime import (
    DocumentationLookupResult,
    _validated_public_https_url,
    write_lookup_artifacts,
)


def _enabled_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.enable_skill("documentation")
    return registry


def _store(tmp_path: Path) -> SkillPermissionStore:
    return SkillPermissionStore(tmp_path / "config" / "ann_skill_permissions.json")


def _audit(tmp_path: Path) -> SkillAuditLogger:
    return SkillAuditLogger(tmp_path / "outputs" / "skills")


def _payload(url: str = "https://fastapi.tiangolo.com/tutorial/dependencies/") -> dict[str, object]:
    return {
        "query": "FastAPI dependency injection",
        "allowed_domains": ["fastapi.tiangolo.com"],
        "urls": [url],
        "max_results": 5,
    }


def _fake_fetch(_url: str, _allowed_domains: list[str] | None = None) -> str:
    return """
    <html>
      <head><title>Dependencies - FastAPI</title></head>
      <body>
        FastAPI dependency injection lets you declare reusable dependencies
        and inject them into path operation functions.
      </body>
    </html>
    """


def test_lookup_blocked_without_network_permission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ASK_ALWAYS)

    result = execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    assert result.status == "BLOCKED"
    assert "explicit approval" in result.errors[0]


def test_lookup_allowed_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ONCE)

    result = execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    assert result.status == "SUCCESS"
    assert result.output["query"] == "FastAPI dependency injection"
    assert result.output["sources"][0]["domain"] == "fastapi.tiangolo.com"


def test_allow_once_consumed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ONCE)

    execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    assert store.get_permission("documentation", "network") == PermissionDecision.ASK_ALWAYS


def test_deny_always_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.DENY_ALWAYS)

    result = execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    assert result.status == "FAILED"
    assert "Permission denied" in result.errors[0]


def test_allowed_domains_blocks_unapproved_domain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_fetch(_url: str, _allowed_domains: list[str] | None = None) -> str:
        raise AssertionError("Blocked domains must not be fetched.")

    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", fail_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ALWAYS)

    result = execute_skill(
        "documentation",
        "lookup",
        _payload("https://example.com/docs"),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    assert result.status == "FAILED"
    assert "blocked_domain:example.com" in result.errors


def test_url_validation_blocks_private_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))],
    )

    with pytest.raises(ValueError, match="non-public"):
        _validated_public_https_url("https://docs.example.com/reference", ("docs.example.com",))


def test_url_validation_accepts_allowlisted_public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))],
    )

    assert (
        _validated_public_https_url("https://docs.example.com/reference", ("docs.example.com",))
        == "https://docs.example.com/reference"
    )


def test_artifact_writer_rejects_unpaired_audit_path(tmp_path: Path) -> None:
    workspace = tmp_path / "outputs" / "skills" / "documentation" / "workspace"
    workspace.mkdir(parents=True)
    result = DocumentationLookupResult("FAILED", "query", [], "summary", [], [])

    with pytest.raises(ValueError, match="parent of its workspace"):
        write_lookup_artifacts(result, {}, workspace, tmp_path / "unrelated")


def test_result_generates_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ALWAYS)

    execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    assert (tmp_path / "outputs" / "skills" / "documentation" / "audit.log").is_file()
    assert (tmp_path / "outputs" / "skills" / "documentation" / "lookup_result.json").is_file()


def test_result_generates_sources_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ALWAYS)

    execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    sources = json.loads((tmp_path / "outputs" / "skills" / "documentation" / "sources.json").read_text())
    assert sources[0]["url"] == "https://fastapi.tiangolo.com/tutorial/dependencies/"


def test_result_generates_result_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ALWAYS)

    execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    summary = (tmp_path / "outputs" / "skills" / "documentation" / "result_summary.md").read_text(encoding="utf-8")
    assert "FastAPI dependency injection" in summary
    assert "fastapi.tiangolo.com" in summary


def test_no_terminal_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_subprocess(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Documentation lookup must not execute terminal.")

    monkeypatch.setattr(subprocess, "run", fail_subprocess)
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ALWAYS)

    result = execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    assert result.output["terminal_used"] is False


def test_no_dependency_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ALWAYS)

    execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    assert not (tmp_path / "node_modules").exists()
    assert not (tmp_path / ".venv").exists()


def test_no_git_usage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ALWAYS)

    result = execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    assert result.output["sandbox_status"] == "ALLOWED"
    assert result.permission_used == ["network"]


def test_sandbox_workspace_respected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ALWAYS)

    result = execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    )

    workspace = Path(str(result.output["workspace"]))
    assert workspace.is_dir()
    assert workspace.parent == tmp_path / "outputs" / "skills" / "documentation"


def test_lookup_does_not_use_socket_when_fetch_is_mocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Only the documentation fetch adapter may use network.")

    monkeypatch.setattr(socket, "create_connection", fail_socket)
    monkeypatch.setattr("agentic_network.skills_builtin.documentation.runtime.fetch_url", _fake_fetch)
    store = _store(tmp_path)
    store.set_permission("documentation", "network", PermissionDecision.ALLOW_ALWAYS)

    assert execute_skill(
        "documentation",
        "lookup",
        _payload(),
        registry=_enabled_registry(),
        store=store,
        audit_logger=_audit(tmp_path),
    ).status == "SUCCESS"
