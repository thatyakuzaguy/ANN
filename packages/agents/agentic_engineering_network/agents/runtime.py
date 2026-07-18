from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from agentic_engineering_network.agents.definitions import AgentDefinition
from agentic_engineering_network.logs.audit import AuditLogger
from agentic_engineering_network.shared.providers import AIProvider, Prompt


@dataclass(frozen=True)
class AgentRunResult:
    run_id: str
    agent: str
    role: str
    decision: str
    outputs: tuple[str, ...]
    created_at: str
    metadata: dict[str, Any]


class AgentRuntime:
    def __init__(
        self,
        provider: AIProvider,
        audit: AuditLogger,
        provider_factory: Callable[[AgentDefinition], AIProvider] | None = None,
    ) -> None:
        self.provider = provider
        self.audit = audit
        self.provider_factory = provider_factory

    def run(self, agent: AgentDefinition, idea: str, context: dict[str, Any]) -> AgentRunResult:
        system = (
            f"You are {agent.name}. Role: {agent.role}. "
            f"Goals: {', '.join(agent.goals)}. Produce: {', '.join(agent.outputs)}. "
            f"Validate with: {', '.join(agent.validation_logic)}. "
            f"Quality rubric: {', '.join(agent.quality_rubric)}. "
            f"Escalate on: {', '.join(agent.escalation_rules)}."
        )
        self.audit.record(
            event_type="agent.started",
            actor=agent.name,
            message=f"{agent.name} started.",
            metadata={"agent": agent.name, "run_id": context.get("run_id"), "outputs": agent.outputs},
        )
        provider = self.provider_factory(agent) if self.provider_factory else self.provider
        try:
            provider_response = provider.generate(Prompt(system=system, user=idea))
        finally:
            if provider is not self.provider:
                close = getattr(provider, "close", None)
                if callable(close):
                    close()
        result = AgentRunResult(
            run_id=str(uuid4()),
            agent=agent.name,
            role=agent.role,
            decision=provider_response.content,
            outputs=agent.outputs,
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata={
                "provider": provider_response.provider,
                "model": provider_response.model,
                "context_keys": sorted(context.keys()),
                "parent_run_id": context.get("run_id"),
            },
        )
        self.audit.record(
            event_type="agent.decision",
            actor=agent.name,
            message=result.decision,
            metadata=asdict(result),
        )
        return result

    def close(self) -> None:
        close = getattr(self.provider, "close", None)
        if callable(close):
            close()
