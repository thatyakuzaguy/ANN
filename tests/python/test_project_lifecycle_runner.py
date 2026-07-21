from pathlib import Path

from agentic_engineering_network.logs.audit import AuditLogger
from agentic_engineering_network.orchestration.artifact_router import build_project_artifacts
from agentic_engineering_network.shared.config import Settings

from app.services import project_lifecycle
from app.services.project_lifecycle import LifecycleStep, ProjectLifecycleRunner


def test_live_sandbox_uses_compose_project_env_instead_of_dash_p(monkeypatch) -> None:
    scratch = Path(r"D:\AgenticEngineeringNetwork\tests\.tmp\project-lifecycle-compose")
    settings = Settings(
        ai_provider="deterministic",
        audit_log_path=scratch / "audit.jsonl",
        generated_projects_path=scratch / "generated-projects",
    )
    runner = ProjectLifecycleRunner(settings, AuditLogger(settings.audit_log_path))
    commands: list[list[str]] = []
    envs: list[dict[str, str]] = []
    monkeypatch.setenv("SYSTEMROOT", r"C:\Windows")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "must-not-reach-generated-project")

    monkeypatch.setattr(runner, "_compose_command", lambda project_root=None, env=None: ["docker", "compose"])

    def fake_run_command(name, command, cwd, env, timeout):  # noqa: ANN001
        commands.append(command)
        envs.append(env)
        status = "failed" if name == "docker_compose_build" else "passed"
        return LifecycleStep(name, status, "stop after compose build", command)

    monkeypatch.setattr(runner, "_run_command", fake_run_command)

    steps = runner._run_live_sandbox(scratch, "0039c970-09ce-4c6f-a2c8-d950fcc8e88d")  # noqa: SLF001

    assert commands
    assert all("-p" not in command for command in commands)
    assert all("--quiet" not in command for command in commands)
    assert all("--rmi" not in command for command in commands)
    assert steps[0].name == "docker_compose_config"
    assert steps[0].status == "passed"
    assert steps[0].command == ["docker", "compose", "config"]
    assert commands[0] == ["docker", "compose", "--profile", "test", "build"]
    assert envs[0]["COMPOSE_PROJECT_NAME"] == "aen-0039c970"
    assert envs[0]["SYSTEMROOT"] == r"C:\Windows"
    assert "AWS_SECRET_ACCESS_KEY" not in envs[0]
    assert any(
        step.name == "docker_compose_remove_sandbox_images" and step.status == "skipped"
        for step in steps
    )


def test_live_sandbox_can_use_standalone_docker_compose(monkeypatch) -> None:
    scratch = Path(r"D:\AgenticEngineeringNetwork\tests\.tmp\project-lifecycle-compose-standalone")
    settings = Settings(
        ai_provider="deterministic",
        audit_log_path=scratch / "audit.jsonl",
        generated_projects_path=scratch / "generated-projects",
    )
    runner = ProjectLifecycleRunner(settings, AuditLogger(settings.audit_log_path))
    commands: list[list[str]] = []

    monkeypatch.setattr(runner, "_compose_command", lambda project_root=None, env=None: ["docker-compose"])

    def fake_run_command(name, command, cwd, env, timeout):  # noqa: ANN001
        commands.append(command)
        status = "failed" if name == "docker_compose_build" else "passed"
        return LifecycleStep(name, status, "stop after compose build", command)

    monkeypatch.setattr(runner, "_run_command", fake_run_command)

    runner._run_live_sandbox(scratch, "a8781282-fe67-4dc5-b001-b0b1c0f10b21")  # noqa: SLF001

    assert commands
    assert commands[0] == ["docker-compose", "--profile", "test", "build"]
    assert all("-p" not in command for command in commands)
    assert all("--quiet" not in command for command in commands)
    assert all("--rmi" not in command for command in commands)


def test_live_sandbox_uses_local_fallback_when_docker_build_is_registry_blocked(monkeypatch) -> None:
    scratch = Path(r"D:\AgenticEngineeringNetwork\tests\.tmp\project-lifecycle-local-fallback")
    (scratch / "apps" / "web").mkdir(parents=True, exist_ok=True)
    (scratch / "apps" / "web" / "package.json").write_text("{}", encoding="utf-8")
    settings = Settings(
        ai_provider="deterministic",
        audit_log_path=scratch / "audit.jsonl",
        generated_projects_path=scratch / "generated-projects",
    )
    runner = ProjectLifecycleRunner(settings, AuditLogger(settings.audit_log_path))

    monkeypatch.setattr(runner, "_compose_command", lambda project_root=None, env=None: ["docker-compose"])

    def fake_run_command(name, command, cwd, env, timeout):  # noqa: ANN001, ARG001
        if name == "docker_compose_build":
            return LifecycleStep(
                name,
                "failed",
                "failed to resolve reference docker.io/library/python:3.12-slim: net/http: TLS handshake timeout",
                command,
            )
        return LifecycleStep(name, "passed", "ok", command)

    monkeypatch.setattr(runner, "_run_command", fake_run_command)

    steps = runner._run_live_sandbox(scratch, "422d0a6e-10ff-4938-a18c-cc2187352d04")  # noqa: SLF001
    statuses = {step.name: step.status for step in steps}

    assert statuses["docker_compose_config"] == "passed"
    assert statuses["docker_compose_build"] == "skipped"
    assert statuses["api_pytest_local_fallback"] == "passed"
    assert statuses["web_build_local_fallback"] == "skipped"


def test_live_sandbox_runs_web_unit_audit_and_browser_gates(monkeypatch) -> None:
    scratch = Path(r"D:\AgenticEngineeringNetwork\tests\.tmp\project-lifecycle-complete-web-gates")
    settings = Settings(
        ai_provider="deterministic",
        audit_log_path=scratch / "audit.jsonl",
        generated_projects_path=scratch / "generated-projects",
    )
    runner = ProjectLifecycleRunner(settings, AuditLogger(settings.audit_log_path))
    commands: dict[str, list[str]] = {}

    monkeypatch.setattr(runner, "_compose_command", lambda project_root=None, env=None: ["docker", "compose"])
    monkeypatch.setattr(
        runner,
        "_wait_for_http",
        lambda name, url, timeout: LifecycleStep(name, "passed", f"{url} ready"),
    )

    def fake_run_command(name, command, cwd, env, timeout):  # noqa: ANN001, ARG001
        commands[name] = command
        assert env["JWT_SECRET"] == "ann-local-sandbox-verification-secret-32-bytes-minimum"
        assert env["NEXT_TELEMETRY_DISABLED"] == "1"
        return LifecycleStep(name, "passed", "ok", command)

    monkeypatch.setattr(runner, "_run_command", fake_run_command)

    steps = runner._run_live_sandbox(scratch, "beef0005-0000-4000-8000-000000000005")  # noqa: SLF001

    assert commands["web_unit_live"][-2:] == ["npm", "test"]
    assert commands["api_dependency_integrity_live"][-2:] == ["pip", "check"]
    assert commands["api_dependency_audit_live"][-4:] == [
        "pip-audit",
        "--local",
        "--progress-spinner",
        "off",
    ]
    assert commands["web_dependency_audit_live"][-3:] == ["npm", "audit", "--audit-level=moderate"]
    assert commands["web_e2e_live"] == [
        "docker",
        "compose",
        "--profile",
        "test",
        "run",
        "--rm",
        "e2e",
    ]
    assert ProjectLifecycleRunner._lifecycle_status(steps) == "passed"  # noqa: SLF001


def test_compose_command_prefers_project_validated_compose_plugin(monkeypatch) -> None:
    scratch = Path(r"D:\AgenticEngineeringNetwork\tests\.tmp\project-lifecycle-compose-detect")
    scratch.mkdir(parents=True, exist_ok=True)
    settings = Settings(
        ai_provider="deterministic",
        audit_log_path=scratch / "audit.jsonl",
        generated_projects_path=scratch / "generated-projects",
    )
    runner = ProjectLifecycleRunner(settings, AuditLogger(settings.audit_log_path))
    probes: list[tuple[list[str], Path | None]] = []

    monkeypatch.setattr(runner, "_docker_available", lambda: True)

    def fake_subprocess_run(  # noqa: ANN001, ARG001
        command,
        cwd=None,
        env=None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    ):
        probes.append((command, cwd))

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr(project_lifecycle.subprocess, "run", fake_subprocess_run)

    command = runner._compose_command(scratch, {"COMPOSE_PROJECT_NAME": "aen-test"})  # noqa: SLF001

    assert command == ["docker", "compose"]
    assert probes == [(["docker", "compose", "config"], scratch)]


def test_provider_unavailable_is_skipped_not_extra_lifecycle_failure(monkeypatch) -> None:
    scratch = Path(r"D:\AgenticEngineeringNetwork\tests\.tmp\project-lifecycle-provider")
    project_root = scratch / "generated"
    (project_root / ".aen").mkdir(parents=True, exist_ok=True)
    settings = Settings(
        ai_provider="ollama",
        audit_log_path=scratch / "audit.jsonl",
        generated_projects_path=scratch / "generated-projects",
    )
    runner = ProjectLifecycleRunner(settings, AuditLogger(settings.audit_log_path))

    def fail_provider(settings):  # noqa: ANN001
        raise RuntimeError("Ollama request failed: connection refused")

    monkeypatch.setattr(project_lifecycle, "build_provider", fail_provider)

    step = runner._apply_provider_patch(  # noqa: SLF001
        project_root,
        "run-123",
        "Build a task API",
        [LifecycleStep("docker_compose_config", "failed", "compose failed")],
        1,
    )

    assert step.name == "qwen_patch"
    assert step.status == "skipped"
    assert "Provider patch request unavailable" in step.detail


def test_provider_patch_is_proposed_but_never_applied_without_patch_approval(tmp_path, monkeypatch) -> None:
    project_root = tmp_path / "generated"
    (project_root / ".aen").mkdir(parents=True)
    source = project_root / "app.py"
    source.write_text("answer = 1\n", encoding="utf-8")
    settings = Settings(
        ai_provider="local-test",
        audit_log_path=tmp_path / "audit.jsonl",
        generated_projects_path=tmp_path / "generated-projects",
    )
    runner = ProjectLifecycleRunner(settings, AuditLogger(settings.audit_log_path))

    class Provider:
        def generate(self, prompt):  # noqa: ANN001, ARG002
            return type(
                "Response",
                (),
                {
                    "content": "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-answer = 1\n+answer = 2\n",
                    "provider": "local-test",
                    "model": "repair-model",
                },
            )()

        def close(self) -> None:
            return None

    apply_modes: list[bool] = []

    def fake_git_apply(project_root, diff, check_only):  # noqa: ANN001, ARG001
        apply_modes.append(check_only)
        return LifecycleStep("git_apply_check", "passed", "Diff is valid.", ["git", "apply", "--check", "-"])

    monkeypatch.setattr(project_lifecycle, "build_provider", lambda settings: Provider())
    monkeypatch.setattr(runner, "_run_git_apply", fake_git_apply)

    step = runner._apply_provider_patch(  # noqa: SLF001
        project_root,
        "run-approval-gate",
        "Fix the generated app",
        [LifecycleStep("api_pytest_live", "failed", "assert 1 == 2")],
        1,
    )

    assert step.status == "blocked"
    assert apply_modes == [True]
    assert source.read_text(encoding="utf-8") == "answer = 1\n"
    assert (project_root / ".aen" / "repair-attempt-1.diff").is_file()
    assert "Explicit Patch Approval" in step.detail


def test_lifecycle_status_blocks_on_docker_registry_timeout() -> None:
    steps = [
        LifecycleStep(
            "docker_compose_build",
            "failed",
            (
                'failed to resolve reference "docker.io/library/python:3.12-slim": '
                "failed to do request: Head https://registry-1.docker.io/v2/library/python/manifests/3.12-slim: "
                "net/http: TLS handshake timeout"
            ),
            ["docker-compose", "build"],
        ),
        LifecycleStep("security_review", "passed", "{}"),
        LifecycleStep("failure_summary", "blocked", "{}"),
        LifecycleStep("release_package", "passed", "Created package."),
    ]

    assert ProjectLifecycleRunner._lifecycle_status(steps) == "blocked"  # noqa: SLF001


def test_lifecycle_status_blocks_on_docker_layer_download_timeout() -> None:
    steps = [
        LifecycleStep(
            "docker_compose_build",
            "failed",
            "48347b15c85f: Downloading [==================================================>]  12.11MB/12.11MB",
            ["docker-compose", "build"],
        ),
        LifecycleStep("security_review", "passed", "{}"),
        LifecycleStep("failure_summary", "blocked", "{}"),
        LifecycleStep("release_package", "passed", "Created package."),
    ]

    assert ProjectLifecycleRunner._lifecycle_status(steps) == "blocked"  # noqa: SLF001


def test_lifecycle_status_blocks_when_docker_daemon_is_unavailable() -> None:
    steps = [
        LifecycleStep(
            "docker_compose_down",
            "failed",
            (
                "failed to connect to the docker API at npipe:////./pipe/docker_engine; "
                "check if the path is correct and if the daemon is running: "
                "El sistema no puede encontrar el archivo especificado."
            ),
            ["docker-compose", "down", "--volumes"],
        ),
        LifecycleStep("security_review", "passed", "{}"),
        LifecycleStep("release_package", "passed", "Created package."),
    ]

    assert ProjectLifecycleRunner._lifecycle_status(steps) == "blocked"  # noqa: SLF001


def test_lifecycle_status_blocks_when_docker_buildx_plugin_is_missing() -> None:
    steps = [
        LifecycleStep(
            "docker_compose_build",
            "failed",
            "Docker Compose requires buildx plugin to be installed.",
            ["docker-compose", "build"],
        ),
        LifecycleStep("security_review", "passed", "{}"),
    ]

    assert ProjectLifecycleRunner._lifecycle_status(steps) == "blocked"  # noqa: SLF001


def test_lifecycle_status_is_partial_when_live_sandbox_is_unavailable() -> None:
    steps = [
        LifecycleStep("required_files", "passed", "ok"),
        LifecycleStep("live_sandbox", "skipped", "Docker Compose is unavailable."),
        LifecycleStep("security_review", "passed", "{}"),
        LifecycleStep("release_package", "passed", "created"),
    ]

    assert ProjectLifecycleRunner._lifecycle_status(steps) == "partial"  # noqa: SLF001


def test_lifecycle_status_is_partial_when_web_build_falls_back_to_skip() -> None:
    steps = [
        LifecycleStep("docker_compose_build", "skipped", "infrastructure failure"),
        LifecycleStep("api_pytest_local_fallback", "passed", "4 passed"),
        LifecycleStep("web_build_local_fallback", "skipped", "dependencies unavailable"),
        LifecycleStep("docker_compose_down", "passed", "clean"),
        LifecycleStep("security_review", "passed", "{}"),
    ]

    assert ProjectLifecycleRunner._lifecycle_status(steps) == "partial"  # noqa: SLF001


def test_algorithm_project_uses_service_specific_static_validation(tmp_path, monkeypatch) -> None:
    artifacts = build_project_artifacts(
        "Build a service implementing a complex algorithm with benchmarks and edge cases",
        "algo-test",
    )
    for relative, content in artifacts.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    project_root = tmp_path / next(iter(artifacts)).split("/")[0]
    runner = ProjectLifecycleRunner(Settings(), AuditLogger(tmp_path / "audit.jsonl"))
    monkeypatch.setattr(runner, "_run_algorithm_live_sandbox", lambda project_root, run_id: [])

    steps = runner._validate(project_root, "algorithm-run")  # noqa: SLF001

    assert runner._project_profile(project_root) == "algorithm_service"  # noqa: SLF001
    assert [step.name for step in steps] == ["required_files", "python_syntax", "compose_static", "algorithm_static"]
    assert all(step.status == "passed" for step in steps)


def test_algorithm_live_sandbox_runs_tests_integration_benchmark_and_audits(tmp_path, monkeypatch) -> None:
    runner = ProjectLifecycleRunner(Settings(), AuditLogger(tmp_path / "audit.jsonl"))
    commands: dict[str, list[str]] = {}
    monkeypatch.setattr(runner, "_compose_command", lambda project_root, env: ["docker", "compose"])
    monkeypatch.setattr(
        runner,
        "_wait_for_http",
        lambda name, url, timeout: LifecycleStep(name, "passed", f"{url} ready"),
    )

    def fake_run(name, command, cwd, env, timeout):  # noqa: ANN001, ARG001
        commands[name] = command
        return LifecycleStep(name, "passed", "captured", command)

    monkeypatch.setattr(runner, "_run_command", fake_run)

    steps = runner._run_algorithm_live_sandbox(tmp_path, "algorithm-live")  # noqa: SLF001

    assert all(step.status == "passed" for step in steps)
    assert commands["docker_compose_up"][-1] == "api"
    assert "web" not in commands["docker_compose_up"]
    assert "tests/test_integration.py" in commands["algorithm_integration_live"]
    assert commands["api_pytest_live"][5:8] == ["python", "-m", "pytest"]
    assert commands["algorithm_benchmark_live"][-2:] == ["python", "benchmark.py"]
    assert "pip-audit" in commands["api_dependency_audit_live"]
