from __future__ import annotations

from pathlib import Path
from threading import Lock
from time import sleep
from typing import Any
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from agentic_engineering_network.agents.definitions import AgentName, get_agent_registry
from agentic_engineering_network.agents.runtime import AgentRuntime
from agentic_engineering_network.agents.subagents import (
    DelegationPolicy,
    SubagentExecution,
    SubagentScheduler,
    SubagentStatus,
    SubagentWorkOrder,
    get_subagent_registry,
)
from agentic_engineering_network.logs.audit import AuditLogger
from agentic_engineering_network.shared.providers import AIProvider, Prompt, ProviderResponse
from app.main import app
from app.services.agent_office import LiveAgentOfficeProvider


class RecordingProvider(AIProvider):
    name = "recording"

    def __init__(self, *, fail_first: bool = False) -> None:
        self.prompts: list[Prompt] = []
        self.fail_first = fail_first

    def generate(self, prompt: Prompt) -> ProviderResponse:
        self.prompts.append(prompt)
        if self.fail_first and len(self.prompts) == 1:
            raise RuntimeError("specialist unavailable")
        return ProviderResponse(self.name, "test-model", f"response-{len(self.prompts)}")


class ConcurrencyProbeProvider(AIProvider):
    name = "concurrency-probe"

    def __init__(self) -> None:
        self._lock = Lock()
        self.active = 0
        self.peak_active = 0

    def generate(self, prompt: Prompt) -> ProviderResponse:
        with self._lock:
            self.active += 1
            self.peak_active = max(self.peak_active, self.active)
        sleep(0.01)
        with self._lock:
            self.active -= 1
        return ProviderResponse(self.name, "probe", prompt.user[:20] or "ok")


def _backend_agent():
    return next(agent for agent in get_agent_registry() if agent.name is AgentName.BACKEND_ENGINEER)


def _work_order(**overrides: Any) -> SubagentWorkOrder:
    definition = get_subagent_registry(AgentName.BACKEND_ENGINEER)[0]
    values: dict[str, Any] = {
        "task_id": "run-1:backend",
        "parent_agent": AgentName.BACKEND_ENGINEER.value,
        "specialization": definition.id,
        "objective": "Review the service boundary.",
        "context_references": ("run_id",),
        "acceptance_criteria": definition.goals,
        "allowed_tools": definition.tools,
        "token_budget": 256,
        "timeout_seconds": 60,
    }
    values.update(overrides)
    return SubagentWorkOrder.create(**values)


def _executor(*_args: Any) -> SubagentExecution:
    return SubagentExecution("Evidence is consistent.", "test", "test-model")


def test_catalog_has_three_specialists_for_every_parent_agent() -> None:
    registry = get_subagent_registry()

    assert len(registry) == len(AgentName) * 3
    assert len({item.id for item in registry}) == len(registry)
    for parent in AgentName:
        specialists = get_subagent_registry(parent)
        assert len(specialists) == 3
        assert all(item.parent_agent is parent for item in specialists)
        assert not any(
            set(item.tools) & {"shell", "terminal_manager", "patch_apply"} for item in specialists
        )


def test_scheduler_executes_valid_work_order_and_audits_it(tmp_path: Path) -> None:
    audit = AuditLogger(tmp_path / "audit.jsonl")
    scheduler = SubagentScheduler(audit)

    result = scheduler.execute(_work_order(), {"run_id": "run-1"}, _executor)

    assert result.status is SubagentStatus.COMPLETED
    assert result.parent_agent == AgentName.BACKEND_ENGINEER.value
    assert result.summary == "Evidence is consistent."
    event_types = [event["event_type"] for event in audit.tail(10)]
    assert event_types == [
        "subagent.delegation_requested",
        "subagent.started",
        "subagent.completed",
    ]


def test_scheduler_blocks_parent_mismatch_cycle_and_host_tools(tmp_path: Path) -> None:
    scheduler = SubagentScheduler(AuditLogger(tmp_path / "audit.jsonl"))
    definition = get_subagent_registry(AgentName.BACKEND_ENGINEER)[0]

    mismatch = scheduler.execute(
        _work_order(parent_agent=AgentName.QA.value),
        {"run_id": "run-mismatch"},
        _executor,
    )
    cycle = scheduler.execute(
        _work_order(lineage=(definition.id,)),
        {"run_id": "run-cycle"},
        _executor,
    )
    unsafe_tool = scheduler.execute(
        _work_order(allowed_tools=(*definition.tools, "shell")),
        {"run_id": "run-tool"},
        _executor,
    )

    assert mismatch.status is SubagentStatus.BLOCKED
    assert "subagent_parent_mismatch" in mismatch.blockers
    assert "subagent_cycle_detected" in cycle.blockers
    assert "subagent_host_affecting_tool_blocked" in unsafe_tool.blockers


def test_scheduler_blocks_absolute_traversal_and_protected_paths(tmp_path: Path) -> None:
    scheduler = SubagentScheduler(AuditLogger(tmp_path / "audit.jsonl"))

    for index, path in enumerate(
        (r"C:\temp\file.py", "../file.py", "models/model.gguf", "src/file.py:stream")
    ):
        result = scheduler.execute(
            _work_order(allowed_files=(path,)),
            {"run_id": f"run-path-{index}"},
            _executor,
        )
        assert result.status is SubagentStatus.BLOCKED
        assert "subagent_allowed_file_path_blocked" in result.blockers


def test_scheduler_redacts_sensitive_context_and_bounds_payload(tmp_path: Path) -> None:
    scheduler = SubagentScheduler(
        AuditLogger(tmp_path / "audit.jsonl"),
        DelegationPolicy(max_context_characters=12, max_subagents_per_parent=1),
    )
    captured: dict[str, str] = {}

    def capture(
        _definition: object,
        _work_order: object,
        context: dict[str, str],
    ) -> SubagentExecution:
        captured.update(context)
        return _executor()

    order = _work_order(context_references=("api_token", "details"))
    result = scheduler.execute(
        order,
        {"run_id": "run-context", "api_token": "do-not-leak", "details": "x" * 100},
        capture,
    )

    assert result.status is SubagentStatus.COMPLETED
    assert captured["api_token"] == "[REDACTED]"
    assert captured["details"] == "x" * 12
    assert "do-not-leak" not in str(captured)


def test_scheduler_enforces_parent_and_run_budgets(tmp_path: Path) -> None:
    scheduler = SubagentScheduler(
        AuditLogger(tmp_path / "audit.jsonl"),
        DelegationPolicy(max_subagents_per_parent=1, max_subagents_per_run=2),
    )

    first = scheduler.execute(_work_order(), {"run_id": "run-budget"}, _executor)
    second = scheduler.execute(_work_order(), {"run_id": "run-budget"}, _executor)

    assert first.status is SubagentStatus.COMPLETED
    assert second.status is SubagentStatus.BLOCKED
    assert second.blockers == ("parent_subagent_budget_exhausted",)


def test_agent_runtime_runs_specialist_before_parent_with_one_provider(tmp_path: Path) -> None:
    provider = RecordingProvider()
    runtime = AgentRuntime(provider, AuditLogger(tmp_path / "audit.jsonl"))

    result = runtime.run(
        _backend_agent(),
        "Build a FastAPI service with JWT authentication.",
        {"run_id": "run-runtime", "workspace_directory": r"D:\project"},
    )

    assert len(provider.prompts) == 2
    assert "read-only subagent" in provider.prompts[0].system
    assert "Do not execute commands" in provider.prompts[0].system
    assert "Delegated specialist evidence" in provider.prompts[1].user
    assert result.decision == "response-2"
    assert len(result.subagent_results) == 1
    assert result.subagent_results[0].status is SubagentStatus.COMPLETED
    assert result.metadata["execution_policy"] == "SEQUENTIAL"
    assert result.metadata["active_models_limit"] == 1
    assert result.metadata["parallel_llm_loads"] == 0


def test_parent_agent_continues_when_specialist_fails(tmp_path: Path) -> None:
    provider = RecordingProvider(fail_first=True)
    runtime = AgentRuntime(provider, AuditLogger(tmp_path / "audit.jsonl"))

    result = runtime.run(
        _backend_agent(),
        "Build a FastAPI service.",
        {"run_id": "run-fallback"},
    )

    assert len(provider.prompts) == 2
    assert result.decision == "response-2"
    assert result.subagent_results[0].status is SubagentStatus.FAILED
    assert "specialist unavailable" in result.subagent_results[0].blockers


def test_public_delegate_api_uses_parent_route_and_read_only_prompt(tmp_path: Path) -> None:
    provider = RecordingProvider()
    runtime = AgentRuntime(provider, AuditLogger(tmp_path / "audit.jsonl"))

    result = runtime.delegate(
        _backend_agent(),
        _work_order(task_id="run-delegate:backend"),
        {"run_id": "run-delegate"},
    )

    assert result.status is SubagentStatus.COMPLETED
    assert len(provider.prompts) == 1
    assert "read-only subagent" in provider.prompts[0].system
    assert "apply patches" in provider.prompts[0].system


def test_concurrent_parent_runs_never_overlap_model_calls(tmp_path: Path) -> None:
    provider = ConcurrencyProbeProvider()
    runtime = AgentRuntime(provider, AuditLogger(tmp_path / "audit.jsonl"))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda run_id: runtime.run(
                    _backend_agent(),
                    "Build a FastAPI service.",
                    {"run_id": run_id},
                ),
                ("run-concurrent-1", "run-concurrent-2"),
            )
        )

    assert len(results) == 2
    assert provider.peak_active == 1


def test_standalone_runs_receive_independent_budget_ids(tmp_path: Path) -> None:
    provider = RecordingProvider()
    runtime = AgentRuntime(provider, AuditLogger(tmp_path / "audit.jsonl"))

    first = runtime.run(_backend_agent(), "Build one service.", {})
    second = runtime.run(_backend_agent(), "Build another service.", {})

    assert first.metadata["parent_run_id"] != second.metadata["parent_run_id"]
    assert first.subagent_results[0].status is SubagentStatus.COMPLETED
    assert second.subagent_results[0].status is SubagentStatus.COMPLETED


def test_subagent_api_is_read_only_and_reports_sequential_policy() -> None:
    client = TestClient(app)

    catalog = client.get("/api/subagents/catalog")
    backend = client.get(
        "/api/subagents/catalog",
        params={"parent_agent": AgentName.BACKEND_ENGINEER.value},
    )
    state = client.get("/api/subagents/state", params={"limit": 10})
    method_not_allowed = client.post("/api/subagents/state")

    assert catalog.status_code == 200
    assert catalog.json()["count"] == len(AgentName) * 3
    assert backend.json()["count"] == 3
    assert state.status_code == 200
    assert state.json()["execution_policy"] == "SEQUENTIAL"
    assert state.json()["active_models_limit"] == 1
    assert state.json()["parallel_llm_loads"] == 0
    assert method_not_allowed.status_code == 405


def test_agent_office_attributes_subagent_activity_to_parent(tmp_path: Path) -> None:
    audit = AuditLogger(tmp_path / "audit.jsonl")
    definition = get_subagent_registry(AgentName.BACKEND_ENGINEER)[0]
    audit.record(
        "subagent.started",
        definition.name,
        "Inspecting backend service boundaries.",
        {
            "run_id": "run-office",
            "parent_agent": AgentName.BACKEND_ENGINEER.value,
            "subagent_id": definition.id,
        },
    )

    state = LiveAgentOfficeProvider(audit).state()
    backend = next(agent for agent in state["agents"] if agent["id"] == "backend-engineer")

    assert state["provider"] == "live"
    assert backend["currentTask"] == "Inspecting backend service boundaries."
    assert backend["status"] == "thinking"
