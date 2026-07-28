from __future__ import annotations

from collections import OrderedDict, deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
import json
from pathlib import PurePath
from threading import Lock
from time import monotonic
from typing import Any
from uuid import uuid4

from agentic_engineering_network.agents.definitions import AgentDefinition, AgentName
from agentic_engineering_network.logs.audit import AuditLogger


class SubagentStatus(StrEnum):
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(frozen=True)
class SubagentDefinition:
    id: str
    parent_agent: AgentName
    name: str
    role: str
    goals: tuple[str, ...]
    tools: tuple[str, ...]
    outputs: tuple[str, ...]
    triggers: tuple[str, ...]


@dataclass(frozen=True)
class SubagentWorkOrder:
    work_order_id: str
    task_id: str
    parent_agent: str
    specialization: str
    objective: str
    allowed_files: tuple[str, ...]
    context_references: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    token_budget: int
    timeout_seconds: int
    required_output_schema: tuple[str, ...]
    depth: int
    lineage: tuple[str, ...]
    created_at: str

    @classmethod
    def create(
        cls,
        *,
        task_id: str,
        parent_agent: str,
        specialization: str,
        objective: str,
        allowed_files: Sequence[str] = (),
        context_references: Sequence[str] = (),
        acceptance_criteria: Sequence[str] = (),
        allowed_tools: Sequence[str] = (),
        token_budget: int = 512,
        timeout_seconds: int = 120,
        required_output_schema: Sequence[str] = (
            "summary",
            "evidence",
            "risks",
            "blockers",
            "confidence",
            "recommendation",
        ),
        depth: int = 1,
        lineage: Sequence[str] = (),
    ) -> SubagentWorkOrder:
        return cls(
            work_order_id=str(uuid4()),
            task_id=task_id,
            parent_agent=parent_agent,
            specialization=specialization,
            objective=objective.strip(),
            allowed_files=tuple(allowed_files),
            context_references=tuple(context_references),
            acceptance_criteria=tuple(acceptance_criteria),
            allowed_tools=tuple(allowed_tools),
            token_budget=token_budget,
            timeout_seconds=timeout_seconds,
            required_output_schema=tuple(required_output_schema),
            depth=depth,
            lineage=tuple(lineage),
            created_at=_now(),
        )


@dataclass(frozen=True)
class SubagentExecution:
    content: str
    provider: str
    model: str


@dataclass(frozen=True)
class SubagentResult:
    work_order_id: str
    task_id: str
    parent_agent: str
    subagent_id: str
    subagent_name: str
    status: SubagentStatus
    summary: str
    evidence: tuple[str, ...]
    risks: tuple[str, ...]
    blockers: tuple[str, ...]
    confidence: float
    recommendation: str
    requested_context: tuple[str, ...]
    provider: str
    model: str
    duration_seconds: float
    created_at: str


@dataclass(frozen=True)
class DelegationPolicy:
    enabled: bool = True
    max_depth: int = 1
    max_subagents_per_parent: int = 1
    max_subagents_per_run: int = 20
    max_context_characters: int = 12_000
    max_token_budget: int = 768
    max_timeout_seconds: int = 300


SubagentExecutor = Callable[
    [SubagentDefinition, SubagentWorkOrder, dict[str, str]],
    SubagentExecution,
]


FORBIDDEN_SUBAGENT_TOOLS = {
    "deployment",
    "file_manager",
    "git_write",
    "package_installer",
    "patch_apply",
    "shell",
    "terminal_manager",
}
PROTECTED_PATH_PARTS = {
    ".git",
    "adapters",
    "datasets",
    "knowledge",
    "memory",
    "models",
    "training",
    "unsloth_compiled_cache",
}
SENSITIVE_CONTEXT_MARKERS = ("api_key", "password", "secret", "token", "credential")


def _subagent(
    parent: AgentName,
    slug: str,
    name: str,
    role: str,
    goals: tuple[str, ...],
    tools: tuple[str, ...],
    outputs: tuple[str, ...],
    triggers: tuple[str, ...],
) -> SubagentDefinition:
    return SubagentDefinition(
        id=f"{parent.value.lower().replace(' ', '-')}/{slug}",
        parent_agent=parent,
        name=name,
        role=role,
        goals=goals,
        tools=tools,
        outputs=outputs,
        triggers=triggers,
    )


SUBAGENT_REGISTRY: tuple[SubagentDefinition, ...] = (
    _subagent(
        AgentName.PRODUCT_MANAGER,
        "discovery",
        "Customer Discovery Analyst",
        "Validates buyer, problem, and measurable value.",
        ("Identify the user and pain", "Define measurable outcomes"),
        ("requirements_reader", "evidence_reader"),
        ("discovery_evidence",),
        ("customer", "user", "problem", "market"),
    ),
    _subagent(
        AgentName.PRODUCT_MANAGER,
        "commercial",
        "Commercial Strategy Analyst",
        "Tests pricing, packaging, and economic assumptions.",
        ("Define pricing hypotheses", "Expose unsupported commercial claims"),
        ("requirements_reader", "risk_matrix"),
        ("commercial_assessment",),
        ("pricing", "billing", "subscription", "saas"),
    ),
    _subagent(
        AgentName.PRODUCT_MANAGER,
        "onboarding",
        "Activation Journey Analyst",
        "Designs onboarding and activation success criteria.",
        ("Map first value", "Measure activation"),
        ("requirements_reader", "journey_mapper"),
        ("activation_plan",),
        ("onboarding", "activation", "retention"),
    ),
    _subagent(
        AgentName.REQUIREMENTS,
        "functional",
        "Functional Contract Analyst",
        "Turns intent into atomic testable behavior.",
        ("Remove ambiguity", "Trace behavior to acceptance criteria"),
        ("contract_reader", "requirements_parser"),
        ("functional_contract",),
        ("api", "feature", "workflow", "function"),
    ),
    _subagent(
        AgentName.REQUIREMENTS,
        "non-functional",
        "Quality Attribute Analyst",
        "Defines performance, security, reliability, and operability constraints.",
        ("Quantify quality attributes", "Identify missing constraints"),
        ("contract_reader", "risk_matrix"),
        ("quality_attributes",),
        ("performance", "security", "scale", "reliability"),
    ),
    _subagent(
        AgentName.REQUIREMENTS,
        "edge-cases",
        "Acceptance Edge-Case Analyst",
        "Finds boundary cases and contradictory expectations.",
        ("Generate edge cases", "Detect contract conflicts"),
        ("contract_reader", "test_plan_reader"),
        ("edge_case_matrix",),
        ("edge", "validation", "error", "acceptance"),
    ),
    _subagent(
        AgentName.PLANNER,
        "dependency-graph",
        "Dependency Graph Analyst",
        "Builds an ordered, cycle-free delivery graph.",
        ("Find blockers", "Sequence work by dependency"),
        ("architecture_reader", "task_graph"),
        ("dependency_graph",),
        ("dependency", "plan", "sequence", "milestone"),
    ),
    _subagent(
        AgentName.PLANNER,
        "risk-plan",
        "Delivery Risk Analyst",
        "Front-loads uncertain and high-impact work.",
        ("Rank delivery risks", "Define checkpoints"),
        ("risk_matrix", "evidence_reader"),
        ("risk_order",),
        ("risk", "unknown", "integration"),
    ),
    _subagent(
        AgentName.PLANNER,
        "approval-plan",
        "Approval Boundary Analyst",
        "Maps host-affecting actions to existing approval gates.",
        ("Identify approval boundaries", "Prevent implicit execution"),
        ("approval_policy_reader", "task_graph"),
        ("approval_plan",),
        ("approval", "install", "deploy", "write"),
    ),
    _subagent(
        AgentName.SOLUTION_ARCHITECT,
        "domain",
        "Domain Boundary Architect",
        "Defines bounded contexts, ownership, and invariants.",
        ("Minimize coupling", "Make ownership explicit"),
        ("requirements_reader", "architecture_modeler"),
        ("domain_map",),
        ("domain", "business", "service", "module"),
    ),
    _subagent(
        AgentName.SOLUTION_ARCHITECT,
        "contracts",
        "API Contract Architect",
        "Designs typed boundaries and compatibility rules.",
        ("Define API contracts", "Specify failure semantics"),
        ("contract_reader", "api_contract_designer"),
        ("api_contract_review",),
        ("api", "webhook", "integration", "schema"),
    ),
    _subagent(
        AgentName.SOLUTION_ARCHITECT,
        "topology",
        "Runtime Topology Architect",
        "Reviews deployment, data flow, and failure isolation.",
        ("Map runtime components", "Define resilience boundaries"),
        ("architecture_modeler", "deployment_reader"),
        ("runtime_topology",),
        ("docker", "deployment", "queue", "runtime"),
    ),
    _subagent(
        AgentName.FRONTEND_ENGINEER,
        "ux",
        "Product UX Engineer",
        "Maps requirements to efficient accessible user flows.",
        ("Define interaction states", "Protect accessibility"),
        ("requirements_reader", "component_inspector"),
        ("ux_contract",),
        ("ui", "screen", "form", "dashboard"),
    ),
    _subagent(
        AgentName.FRONTEND_ENGINEER,
        "state",
        "Frontend State Engineer",
        "Reviews API, cache, error, and loading state boundaries.",
        ("Align state with contracts", "Handle loading and failure states"),
        ("api_contract_reader", "component_inspector"),
        ("state_plan",),
        ("react", "query", "state", "api"),
    ),
    _subagent(
        AgentName.FRONTEND_ENGINEER,
        "visual-qa",
        "Accessibility and Visual QA Engineer",
        "Checks responsive behavior and accessibility evidence.",
        ("Find accessibility gaps", "Define visual verification"),
        ("component_inspector", "test_report_reader"),
        ("visual_qa_plan",),
        ("accessibility", "responsive", "playwright", "visual"),
    ),
    _subagent(
        AgentName.BACKEND_ENGINEER,
        "services",
        "Application Service Engineer",
        "Designs typed service boundaries and business invariants.",
        ("Separate transport from business logic", "Preserve invariants"),
        ("api_contract_reader", "repository_context"),
        ("service_design",),
        ("fastapi", "service", "endpoint", "business"),
    ),
    _subagent(
        AgentName.BACKEND_ENGINEER,
        "auth",
        "Identity and Authorization Engineer",
        "Reviews authentication, sessions, RBAC, and tenant boundaries.",
        ("Prevent privilege escalation", "Define authorization checks"),
        ("security_policy_reader", "api_contract_reader"),
        ("auth_design",),
        ("auth", "jwt", "rbac", "tenant"),
    ),
    _subagent(
        AgentName.BACKEND_ENGINEER,
        "integrations",
        "Integration Reliability Engineer",
        "Designs idempotent external boundaries and failure handling.",
        ("Define retries and idempotency", "Map cross-domain failure causes"),
        ("contract_reader", "failure_context_reader"),
        ("integration_plan",),
        ("stripe", "webhook", "email", "external"),
    ),
    _subagent(
        AgentName.DATABASE_ENGINEER,
        "schema",
        "Relational Schema Engineer",
        "Reviews entities, constraints, and ownership.",
        ("Protect integrity", "Avoid accidental denormalization"),
        ("domain_model_reader", "schema_inspector"),
        ("schema_review",),
        ("database", "schema", "entity", "postgres"),
    ),
    _subagent(
        AgentName.DATABASE_ENGINEER,
        "migrations",
        "Migration Safety Engineer",
        "Plans reversible and deployable schema evolution.",
        ("Define upgrade and rollback", "Protect existing data"),
        ("schema_inspector", "migration_reader"),
        ("migration_plan",),
        ("migration", "alembic", "upgrade", "rollback"),
    ),
    _subagent(
        AgentName.DATABASE_ENGINEER,
        "queries",
        "Query and Tenancy Engineer",
        "Checks indexes, query scope, and tenant isolation.",
        ("Prevent cross-tenant access", "Identify index needs"),
        ("query_inspector", "security_policy_reader"),
        ("query_review",),
        ("query", "index", "tenant", "performance"),
    ),
    _subagent(
        AgentName.DEVOPS,
        "containers",
        "Container Runtime Engineer",
        "Reviews reproducible local runtime and isolation.",
        ("Make builds deterministic", "Keep execution sandboxed"),
        ("deployment_reader", "runtime_policy_reader"),
        ("container_plan",),
        ("docker", "container", "compose", "sandbox"),
    ),
    _subagent(
        AgentName.DEVOPS,
        "cicd",
        "CI/CD Engineer",
        "Designs gated build, test, scan, and release automation.",
        ("Order CI gates", "Keep secrets external"),
        ("workflow_reader", "security_policy_reader"),
        ("cicd_plan",),
        ("github", "ci", "workflow", "release"),
    ),
    _subagent(
        AgentName.DEVOPS,
        "operations",
        "Reliability Operations Engineer",
        "Defines health, backup, restore, and observability controls.",
        ("Define operational checks", "Prepare recovery evidence"),
        ("deployment_reader", "evidence_reader"),
        ("operations_plan",),
        ("health", "backup", "logs", "observability"),
    ),
    _subagent(
        AgentName.QA,
        "unit",
        "Unit Test Designer",
        "Targets pure behavior and boundary conditions.",
        ("Trace tests to contracts", "Avoid implementation-coupled assertions"),
        ("contract_reader", "test_plan_reader"),
        ("unit_test_matrix",),
        ("unit", "function", "validation", "edge"),
    ),
    _subagent(
        AgentName.QA,
        "integration",
        "Integration Test Engineer",
        "Tests cross-component contracts and real failure boundaries.",
        ("Localize cross-domain failures", "Verify integrations end to end"),
        ("failure_context_reader", "api_contract_reader"),
        ("integration_test_matrix",),
        ("integration", "docker", "database", "webhook"),
    ),
    _subagent(
        AgentName.QA,
        "test-validity",
        "Test Validity Reviewer",
        "Challenges assertions that conflict with the product contract.",
        ("Detect false negatives", "Escalate ambiguous contracts"),
        ("contract_reader", "test_report_reader"),
        ("test_validity_decision",),
        ("failed", "assert", "contract", "regression"),
    ),
    _subagent(
        AgentName.SECURITY,
        "threat-model",
        "Threat Modeling Analyst",
        "Maps assets, trust boundaries, and abuse cases.",
        ("Identify threats", "Prioritize mitigations"),
        ("architecture_reader", "security_policy_reader"),
        ("threat_model_evidence",),
        ("security", "threat", "trust", "abuse"),
    ),
    _subagent(
        AgentName.SECURITY,
        "access",
        "Access Control Reviewer",
        "Checks auth, RBAC, tenancy, and data exposure.",
        ("Find authorization gaps", "Verify least privilege"),
        ("api_contract_reader", "security_policy_reader"),
        ("access_review",),
        ("auth", "rbac", "permission", "tenant"),
    ),
    _subagent(
        AgentName.SECURITY,
        "supply-chain",
        "Dependency and Secret Reviewer",
        "Reviews dependencies, configuration, and secret boundaries.",
        ("Find unsafe dependencies", "Prevent secret disclosure"),
        ("dependency_manifest_reader", "secret_scan_reader"),
        ("supply_chain_review",),
        ("dependency", "secret", "package", "cve"),
    ),
    _subagent(
        AgentName.DOCUMENTATION,
        "user",
        "User Documentation Writer",
        "Produces task-oriented setup and usage guidance.",
        ("Document user workflows", "State limitations honestly"),
        ("artifact_reader", "requirements_reader"),
        ("user_docs_plan",),
        ("readme", "setup", "user", "guide"),
    ),
    _subagent(
        AgentName.DOCUMENTATION,
        "developer",
        "Developer Documentation Writer",
        "Documents contracts, tests, and extension points.",
        ("Explain code boundaries", "Keep examples traceable"),
        ("repository_context", "api_contract_reader"),
        ("developer_docs_plan",),
        ("api", "developer", "architecture", "extend"),
    ),
    _subagent(
        AgentName.DOCUMENTATION,
        "operations",
        "Operations Runbook Writer",
        "Documents deployment, recovery, and troubleshooting.",
        ("Make operations repeatable", "Document rollback"),
        ("deployment_reader", "test_report_reader"),
        ("runbook_plan",),
        ("deploy", "troubleshoot", "backup", "rollback"),
    ),
    _subagent(
        AgentName.CODE_REVIEW,
        "correctness",
        "Correctness Reviewer",
        "Finds concrete behavioral defects and missing guards.",
        ("Prioritize runtime evidence", "Reject speculative findings"),
        ("diff_reader", "contract_reader"),
        ("correctness_findings",),
        ("bug", "error", "failed", "correctness"),
    ),
    _subagent(
        AgentName.CODE_REVIEW,
        "maintainability",
        "Architecture Entropy Reviewer",
        "Detects duplication, coupling, and patch accumulation.",
        ("Measure structural drift", "Recommend refactor only with evidence"),
        ("diff_reader", "repository_context"),
        ("entropy_findings",),
        ("refactor", "duplicate", "complex", "maintain"),
    ),
    _subagent(
        AgentName.CODE_REVIEW,
        "contract",
        "Contract Alignment Reviewer",
        "Checks implementation, tests, and requirements for contradictions.",
        ("Resolve contract mismatches", "Suppress stylistic bikeshedding"),
        ("contract_reader", "test_report_reader"),
        ("contract_findings",),
        ("contract", "test", "api", "review"),
    ),
    _subagent(
        AgentName.RELEASE,
        "package",
        "Release Packaging Reviewer",
        "Checks artifact completeness and reproducibility.",
        ("Verify package inputs", "Detect missing artifacts"),
        ("artifact_reader", "release_policy_reader"),
        ("package_evidence",),
        ("package", "artifact", "installer", "release"),
    ),
    _subagent(
        AgentName.RELEASE,
        "migration",
        "Release Migration Planner",
        "Prepares upgrade, compatibility, and rollback steps.",
        ("Protect upgrades", "Define rollback triggers"),
        ("migration_reader", "release_policy_reader"),
        ("release_migration_plan",),
        ("migration", "upgrade", "rollback", "version"),
    ),
    _subagent(
        AgentName.RELEASE,
        "readiness",
        "Release Evidence Auditor",
        "Verifies every release claim against concrete evidence.",
        ("Block unsupported claims", "Summarize residual risk"),
        ("evidence_reader", "gate_reader"),
        ("release_evidence",),
        ("ready", "gate", "evidence", "public"),
    ),
    _subagent(
        AgentName.PRODUCT_REVIEW,
        "value",
        "Product Value Reviewer",
        "Challenges vague buyer and value assumptions.",
        ("Require buyer specificity", "Require measurable value"),
        ("product_brief_reader", "evidence_reader"),
        ("value_review",),
        ("buyer", "value", "market", "problem"),
    ),
    _subagent(
        AgentName.PRODUCT_REVIEW,
        "scope",
        "Product Scope Reviewer",
        "Finds oversized, incoherent, or untestable scope.",
        ("Protect MVP focus", "Identify missing decisions"),
        ("requirements_reader", "risk_matrix"),
        ("scope_review",),
        ("mvp", "scope", "feature", "roadmap"),
    ),
    _subagent(
        AgentName.PRODUCT_REVIEW,
        "launch",
        "Launch Readiness Reviewer",
        "Reviews pricing, onboarding, support, and launch assumptions.",
        ("Validate activation path", "Expose launch dependencies"),
        ("product_brief_reader", "release_policy_reader"),
        ("launch_review",),
        ("launch", "pricing", "onboarding", "support"),
    ),
    _subagent(
        AgentName.META_REVIEW,
        "consistency",
        "Cross-Agent Consistency Auditor",
        "Finds contradictions between agent outputs.",
        ("Reconcile evidence", "Expose unresolved conflicts"),
        ("agent_output_reader", "contract_reader"),
        ("consistency_report",),
        ("conflict", "agent", "consensus", "contradiction"),
    ),
    _subagent(
        AgentName.META_REVIEW,
        "gates",
        "Gate Evidence Auditor",
        "Verifies pass/fail decisions against artifacts and runtime facts.",
        ("Reject unsupported passes", "Prioritize executable evidence"),
        ("gate_reader", "evidence_reader"),
        ("gate_audit",),
        ("gate", "passed", "failed", "evidence"),
    ),
    _subagent(
        AgentName.META_REVIEW,
        "escalation",
        "Escalation Decision Auditor",
        "Checks retry limits, ambiguity, and human handoff quality.",
        ("Stop unproductive loops", "Prepare actionable escalation"),
        ("retry_history_reader", "approval_policy_reader"),
        ("escalation_review",),
        ("retry", "blocked", "human", "permanent"),
    ),
)


SUBAGENTS_BY_ID = {item.id: item for item in SUBAGENT_REGISTRY}
SUBAGENTS_BY_PARENT: dict[AgentName, tuple[SubagentDefinition, ...]] = {
    parent: tuple(item for item in SUBAGENT_REGISTRY if item.parent_agent is parent)
    for parent in AgentName
}


def get_subagent_registry(
    parent_agent: AgentName | str | None = None,
) -> tuple[SubagentDefinition, ...]:
    if parent_agent is None:
        return SUBAGENT_REGISTRY
    try:
        parent = parent_agent if isinstance(parent_agent, AgentName) else AgentName(parent_agent)
    except ValueError:
        return ()
    return SUBAGENTS_BY_PARENT.get(parent, ())


def build_default_work_orders(
    agent: AgentDefinition,
    idea: str,
    context: Mapping[str, Any],
    *,
    limit: int,
    token_budget: int,
    timeout_seconds: int,
) -> tuple[SubagentWorkOrder, ...]:
    if limit <= 0:
        return ()
    candidates = get_subagent_registry(agent.name)
    normalized_idea = idea.lower()
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: (
            -sum(1 for trigger in item[1].triggers if trigger in normalized_idea),
            item[0],
        ),
    )
    run_id = str(context.get("run_id") or "standalone")
    references = tuple(
        key
        for key in ("run_id", "workspace_directory", "task_count", "quality_context")
        if key in context
    )
    return tuple(
        SubagentWorkOrder.create(
            task_id=f"{run_id}:{definition.id}",
            parent_agent=agent.name.value,
            specialization=definition.id,
            objective=(
                f"Support {agent.name.value} for this request: {idea.strip()}. "
                f"Focus only on {definition.role}"
            ),
            context_references=references,
            acceptance_criteria=definition.goals,
            allowed_tools=definition.tools,
            token_budget=token_budget,
            timeout_seconds=timeout_seconds,
        )
        for _, definition in ranked[:limit]
    )


class SubagentScheduler:
    def __init__(self, audit: AuditLogger, policy: DelegationPolicy | None = None) -> None:
        self.audit = audit
        self.policy = policy or DelegationPolicy()
        self._lock = Lock()
        self._run_counts: OrderedDict[str, int] = OrderedDict()
        self._parent_counts: OrderedDict[tuple[str, str], int] = OrderedDict()
        self._results: deque[SubagentResult] = deque(maxlen=500)

    def execute(
        self,
        work_order: SubagentWorkOrder,
        context: Mapping[str, Any],
        executor: SubagentExecutor,
    ) -> SubagentResult:
        started = monotonic()
        run_id = str(context.get("run_id") or "standalone")
        definition, errors = self._validate(work_order, run_id)
        self.audit.record(
            "subagent.delegation_requested",
            work_order.parent_agent,
            f"Delegation requested for {work_order.specialization}.",
            {"run_id": run_id, "work_order": asdict(work_order), "validation_errors": errors},
        )
        if definition is None or errors:
            result = self._blocked_result(work_order, errors, monotonic() - started)
            self._store(result)
            self.audit.record(
                "subagent.blocked",
                work_order.parent_agent,
                result.summary,
                {"run_id": run_id, "result": asdict(result)},
            )
            return result

        with self._lock:
            current = self._run_counts.get(run_id, 0)
            parent_key = (run_id, work_order.parent_agent)
            parent_count = self._parent_counts.get(parent_key, 0)
            if current >= self.policy.max_subagents_per_run:
                errors = ("run_subagent_budget_exhausted",)
            elif parent_count >= self.policy.max_subagents_per_parent:
                errors = ("parent_subagent_budget_exhausted",)
            else:
                self._run_counts[run_id] = current + 1
                self._run_counts.move_to_end(run_id)
                self._parent_counts[parent_key] = parent_count + 1
                self._parent_counts.move_to_end(parent_key)
                while len(self._run_counts) > 100:
                    expired_run_id, _ = self._run_counts.popitem(last=False)
                    expired_keys = [key for key in self._parent_counts if key[0] == expired_run_id]
                    for key in expired_keys:
                        self._parent_counts.pop(key, None)
        if errors:
            result = self._blocked_result(work_order, errors, monotonic() - started)
            self._store(result)
            return result

        self.audit.record(
            "subagent.started",
            definition.name,
            f"{definition.name} started delegated analysis.",
            {
                "run_id": run_id,
                "work_order_id": work_order.work_order_id,
                "parent_agent": work_order.parent_agent,
                "subagent_id": definition.id,
            },
        )
        try:
            execution = executor(definition, work_order, self._compile_context(work_order, context))
            content = execution.content.strip()
            if not content:
                raise RuntimeError("subagent_returned_empty_output")
            result = SubagentResult(
                work_order_id=work_order.work_order_id,
                task_id=work_order.task_id,
                parent_agent=work_order.parent_agent,
                subagent_id=definition.id,
                subagent_name=definition.name,
                status=SubagentStatus.COMPLETED,
                summary=content,
                evidence=("model_output",),
                risks=(),
                blockers=(),
                confidence=0.75,
                recommendation=content,
                requested_context=(),
                provider=execution.provider,
                model=execution.model,
                duration_seconds=round(monotonic() - started, 3),
                created_at=_now(),
            )
        except Exception as exc:
            result = SubagentResult(
                work_order_id=work_order.work_order_id,
                task_id=work_order.task_id,
                parent_agent=work_order.parent_agent,
                subagent_id=definition.id,
                subagent_name=definition.name,
                status=SubagentStatus.FAILED,
                summary="Delegated analysis failed; the parent agent remains authoritative.",
                evidence=(),
                risks=("delegated_analysis_unavailable",),
                blockers=(str(exc),),
                confidence=0.0,
                recommendation="Continue with parent-agent evidence or escalate if this specialty is required.",
                requested_context=(),
                provider="unavailable",
                model="unavailable",
                duration_seconds=round(monotonic() - started, 3),
                created_at=_now(),
            )
        self._store(result)
        self.audit.record(
            f"subagent.{result.status.value}",
            definition.name,
            result.summary,
            {"run_id": run_id, "result": asdict(result)},
        )
        return result

    def state(self, run_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        with self._lock:
            results = list(self._results)
        if run_id:
            prefix = f"{run_id}:"
            results = [result for result in results if result.task_id.startswith(prefix)]
        selected = results[-max(1, min(limit, 500)) :]
        return {
            "policy": asdict(self.policy),
            "catalog_size": len(SUBAGENT_REGISTRY),
            "active_models_limit": 1,
            "parallel_llm_loads": 0,
            "execution_policy": "SEQUENTIAL",
            "results": [asdict(result) for result in selected],
        }

    def _validate(
        self,
        work_order: SubagentWorkOrder,
        run_id: str,
    ) -> tuple[SubagentDefinition | None, tuple[str, ...]]:
        errors: list[str] = []
        definition = SUBAGENTS_BY_ID.get(work_order.specialization)
        if not self.policy.enabled:
            errors.append("subagent_delegation_disabled")
        if definition is None:
            errors.append("unknown_subagent_specialization")
        elif definition.parent_agent.value != work_order.parent_agent:
            errors.append("subagent_parent_mismatch")
        if not work_order.objective:
            errors.append("empty_subagent_objective")
        if work_order.depth < 1 or work_order.depth > self.policy.max_depth:
            errors.append("subagent_depth_blocked")
        if work_order.specialization in work_order.lineage:
            errors.append("subagent_cycle_detected")
        if len(work_order.lineage) >= self.policy.max_depth:
            errors.append("subagent_lineage_depth_blocked")
        if work_order.token_budget < 1 or work_order.token_budget > self.policy.max_token_budget:
            errors.append("subagent_token_budget_blocked")
        if (
            work_order.timeout_seconds < 1
            or work_order.timeout_seconds > self.policy.max_timeout_seconds
        ):
            errors.append("subagent_timeout_blocked")
        if len(work_order.context_references) > 16:
            errors.append("too_many_context_references")
        if definition is not None:
            if not set(work_order.allowed_tools).issubset(definition.tools):
                errors.append("subagent_tool_not_declared")
        if set(work_order.allowed_tools) & FORBIDDEN_SUBAGENT_TOOLS:
            errors.append("subagent_host_affecting_tool_blocked")
        if any(not _is_safe_relative_path(path) for path in work_order.allowed_files):
            errors.append("subagent_allowed_file_path_blocked")
        if not run_id:
            errors.append("missing_parent_run_id")
        return definition, tuple(dict.fromkeys(errors))

    def _compile_context(
        self,
        work_order: SubagentWorkOrder,
        context: Mapping[str, Any],
    ) -> dict[str, str]:
        compiled: dict[str, str] = {}
        remaining = self.policy.max_context_characters
        for key in work_order.context_references:
            if key not in context or remaining <= 0:
                continue
            if any(marker in key.lower() for marker in SENSITIVE_CONTEXT_MARKERS):
                compiled[key] = "[REDACTED]"
                continue
            value = context[key]
            if isinstance(value, str):
                serialized = value
            else:
                try:
                    serialized = json.dumps(value, sort_keys=True, default=str)
                except (TypeError, ValueError):
                    serialized = str(value)
            clipped = serialized[:remaining]
            compiled[key] = clipped
            remaining -= len(clipped)
        return compiled

    def _blocked_result(
        self,
        work_order: SubagentWorkOrder,
        errors: Sequence[str],
        duration: float,
    ) -> SubagentResult:
        return SubagentResult(
            work_order_id=work_order.work_order_id,
            task_id=work_order.task_id,
            parent_agent=work_order.parent_agent,
            subagent_id=work_order.specialization,
            subagent_name=work_order.specialization,
            status=SubagentStatus.BLOCKED,
            summary="Delegation was blocked by policy.",
            evidence=(),
            risks=(),
            blockers=tuple(errors),
            confidence=0.0,
            recommendation="Correct the work order or keep the decision with the parent agent.",
            requested_context=(),
            provider="none",
            model="none",
            duration_seconds=round(duration, 3),
            created_at=_now(),
        )

    def _store(self, result: SubagentResult) -> None:
        with self._lock:
            self._results.append(result)


def _is_safe_relative_path(raw_path: str) -> bool:
    normalized = raw_path.replace("\\", "/")
    if not normalized or normalized.startswith("/") or ":" in normalized:
        return False
    parts = PurePath(normalized).parts
    return (
        bool(parts)
        and not any(part in {".", ".."} for part in parts)
        and not any(part.lower() in PROTECTED_PATH_PARTS for part in parts)
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
