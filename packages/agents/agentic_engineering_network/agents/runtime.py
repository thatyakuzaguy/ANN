from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from collections.abc import Callable
import json
from threading import Lock
from typing import Any
from uuid import uuid4

from agentic_engineering_network.agents.definitions import AgentDefinition
from agentic_engineering_network.agents.subagents import (
    DelegationPolicy,
    SubagentDefinition,
    SubagentExecution,
    SubagentResult,
    SubagentScheduler,
    SubagentWorkOrder,
    build_default_work_orders,
)
from agentic_engineering_network.logs.audit import AuditLogger
from agentic_engineering_network.shared.providers import AIProvider, Prompt


@dataclass(frozen=True)
class AgentRunResult:
    run_id: str
    agent: str
    role: str
    decision: str
    outputs: tuple[str, ...]
    subagent_results: tuple[SubagentResult, ...]
    created_at: str
    metadata: dict[str, Any]


class AgentRuntime:
    def __init__(
        self,
        provider: AIProvider,
        audit: AuditLogger,
        provider_factory: Callable[[AgentDefinition], AIProvider] | None = None,
        delegation_policy: DelegationPolicy | None = None,
    ) -> None:
        self.provider = provider
        self.audit = audit
        self.provider_factory = provider_factory
        self.delegation_policy = delegation_policy or DelegationPolicy()
        self.subagents = SubagentScheduler(audit, self.delegation_policy)
        self._model_lock = Lock()

    def run(self, agent: AgentDefinition, idea: str, context: dict[str, Any]) -> AgentRunResult:
        effective_context = dict(context)
        effective_context.setdefault("run_id", f"standalone-{uuid4()}")
        self.audit.record(
            event_type="agent.started",
            actor=agent.name,
            message=f"{agent.name} started.",
            metadata={
                "agent": agent.name,
                "run_id": effective_context["run_id"],
                "outputs": agent.outputs,
            },
        )
        with self._model_lock:
            provider = self.provider_factory(agent) if self.provider_factory else self.provider
            try:
                subagent_results = self._run_subagents(
                    agent,
                    idea,
                    effective_context,
                    provider,
                )
                provider_response = provider.generate(
                    Prompt(
                        system=self._parent_system_prompt(agent),
                        user=self._parent_user_prompt(idea, subagent_results),
                    )
                )
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
            subagent_results=subagent_results,
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata={
                "provider": provider_response.provider,
                "model": provider_response.model,
                "context_keys": sorted(effective_context.keys()),
                "parent_run_id": effective_context["run_id"],
                "subagent_count": len(subagent_results),
                "subagent_statuses": [item.status.value for item in subagent_results],
                "execution_policy": "SEQUENTIAL",
                "active_models_limit": 1,
                "parallel_llm_loads": 0,
            },
        )
        self.audit.record(
            event_type="agent.decision",
            actor=agent.name,
            message=result.decision,
            metadata=asdict(result),
        )
        return result

    def subagent_state(self, run_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        return self.subagents.state(run_id=run_id, limit=limit)

    def delegate(
        self,
        agent: AgentDefinition,
        work_order: SubagentWorkOrder,
        context: dict[str, Any],
    ) -> SubagentResult:
        """Execute one validated, read-only delegation through the parent's model route."""

        effective_context = dict(context)
        effective_context.setdefault("run_id", f"standalone-{uuid4()}")
        with self._model_lock:
            provider = self.provider_factory(agent) if self.provider_factory else self.provider
            try:
                return self.subagents.execute(
                    work_order,
                    effective_context,
                    lambda definition, order, delegated_context: self._execute_subagent(
                        provider,
                        definition,
                        order,
                        delegated_context,
                    ),
                )
            finally:
                if provider is not self.provider:
                    close = getattr(provider, "close", None)
                    if callable(close):
                        close()

    def _run_subagents(
        self,
        agent: AgentDefinition,
        idea: str,
        context: dict[str, Any],
        provider: AIProvider,
    ) -> tuple[SubagentResult, ...]:
        if not self.delegation_policy.enabled:
            return ()
        work_orders = build_default_work_orders(
            agent,
            idea,
            context,
            limit=self.delegation_policy.max_subagents_per_parent,
            token_budget=self.delegation_policy.max_token_budget,
            timeout_seconds=self.delegation_policy.max_timeout_seconds,
        )

        def execute(
            definition: SubagentDefinition,
            work_order: SubagentWorkOrder,
            delegated_context: dict[str, str],
        ) -> SubagentExecution:
            return self._execute_subagent(
                provider,
                definition,
                work_order,
                delegated_context,
            )

        return tuple(self.subagents.execute(order, context, execute) for order in work_orders)

    def _execute_subagent(
        self,
        provider: AIProvider,
        definition: SubagentDefinition,
        work_order: SubagentWorkOrder,
        delegated_context: dict[str, str],
    ) -> SubagentExecution:
        response = provider.generate(
            Prompt(
                system=self._subagent_system_prompt(definition, work_order),
                user=json.dumps(
                    {
                        "objective": work_order.objective,
                        "acceptance_criteria": work_order.acceptance_criteria,
                        "context": delegated_context,
                    },
                    sort_keys=True,
                ),
            )
        )
        return SubagentExecution(response.content, response.provider, response.model)

    @staticmethod
    def _parent_system_prompt(agent: AgentDefinition) -> str:
        return (
            f"You are {agent.name}. Role: {agent.role}. "
            f"Goals: {', '.join(agent.goals)}. Produce: {', '.join(agent.outputs)}. "
            f"Validate with: {', '.join(agent.validation_logic)}. "
            f"Quality rubric: {', '.join(agent.quality_rubric)}. "
            f"Escalate on: {', '.join(agent.escalation_rules)}. "
            "You own the final decision. Delegated evidence is advisory and must be checked against "
            "requirements, executable evidence, and ANN safety gates. Ignore unsupported stylistic advice."
        )

    @staticmethod
    def _parent_user_prompt(idea: str, results: tuple[SubagentResult, ...]) -> str:
        delegated = [
            {
                "subagent": result.subagent_name,
                "status": result.status.value,
                "summary": result.summary,
                "blockers": result.blockers,
                "confidence": result.confidence,
            }
            for result in results
        ]
        return (
            f"User request:\n{idea}\n\n"
            "Delegated specialist evidence (never a substitute for runtime facts):\n"
            f"{json.dumps(delegated, sort_keys=True)}"
        )

    @staticmethod
    def _subagent_system_prompt(
        definition: SubagentDefinition,
        work_order: SubagentWorkOrder,
    ) -> str:
        return (
            f"You are {definition.name}, a read-only subagent of {work_order.parent_agent}. "
            f"Role: {definition.role} Goals: {', '.join(definition.goals)}. "
            f"Use only these analytical capabilities: {', '.join(work_order.allowed_tools)}. "
            "Do not execute commands, write files, apply patches, install packages, deploy, or delegate. "
            f"Stay within {work_order.token_budget} output tokens. Return these fields clearly: "
            f"{', '.join(work_order.required_output_schema)}. Cite only evidence present in the payload "
            "and explicitly mark unknowns."
        )

    def close(self) -> None:
        close = getattr(self.provider, "close", None)
        if callable(close):
            close()
