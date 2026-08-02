"""Generate ANN advanced built-in skill packages from the typed catalog."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentic_network.skills.engineering import (  # noqa: E402
    ENGINEERING_SKILL_ACTIONS,
    EngineeringSkillAction,
)
from agentic_network.skills.models import SkillPermission  # noqa: E402


BUILTINS = ROOT / "agentic_network" / "skills_builtin"
ADVANCED_SKILLS = {
    "requirements_contract": "Versioned requirements, acceptance criteria, and deterministic contract arbitration.",
    "dependency_doctor": "Runtime, manifest, lockfile, and dependency compatibility diagnostics without installs.",
    "runtime_observability": "Bounded local runtime, log, port, resource, and failure-correlation evidence.",
    "test_quality": "Test strength, mutation readiness, and deterministic failed-test validity review.",
    "architecture_fitness": "Architecture boundaries, dependency cycles, duplication, complexity, and entropy.",
    "backup_restore": "PostgreSQL backup, restore, retention, and recovery verification through approved Compose recipes.",
    "performance_testing": "Performance budgets, benchmark readiness, and approved sandboxed performance recipes.",
    "supply_chain_compliance": "License, lockfile, SBOM, provenance, and dependency policy evidence.",
    "release_provenance": "Release hashes, Authenticode, attestations, and clean-machine evidence.",
    "deployment_verification": "Deployment manifests, health checks, rollback, TLS, and isolated smoke verification.",
    "external_integration_verification": "Provider, webhook, credential-boundary, idempotency, and approved HTTPS health checks.",
    "ux_quality": "Responsive, accessibility, keyboard, and visual-regression evidence.",
    "git_collaboration": "Approval-gated branch, commit, push, and draft pull-request collaboration.",
    "mobile_validation": "Android, iOS, React Native, and Flutter project evidence.",
    "game_validation": "Game engine, loop, assets, controls, physics, and gameplay-test evidence.",
    "data_pipeline": "ETL lineage, schema, quality, idempotency, and backfill evidence.",
    "ml_evaluation": "Model-card, metric, reproducibility, drift, and bias evidence without training.",
    "infrastructure_validation": "Terraform, Kubernetes, Helm, CI, policy, and infrastructure safety evidence.",
    "desktop_validation": "Native desktop lifecycle, packaging, accessibility, installer, and update evidence.",
    "localization": "Locale coverage, hardcoded text, pluralization, and RTL evidence.",
    "agent_evaluation": "Golden-task scoring, outcome comparison, latency, retry, and agent-quality evidence.",
    "adversarial_red_team": "Non-destructive prompt, tool, approval, filesystem, and secret-boundary adversarial review.",
    "fuzz_property_testing": "Fuzz targets, property tests, schemas, seeds, crash evidence, and approved Compose execution.",
    "dependency_remediation": "Bounded dependency risk ranking, update planning, verification, and rollback evidence without installs.",
    "refactor_migration": "Architecture-aware refactor seams, blast radius, codemod planning, and compatibility migration evidence.",
    "incident_response": "Bounded incident triage, timeline correlation, impact assessment, and blameless postmortem evidence.",
    "observability_instrumentation": "Metrics, traces, logs, correlation IDs, dashboards, alerts, and instrumentation planning.",
    "context_quality_evaluation": "Retrieval precision, recall, stale context, grounding, and token-budget quality evidence.",
    "failure_replay": "Deterministic failure recipes, redacted environment evidence, seeds, verification, and approved replay.",
    "privacy_data_governance": "PII, consent, retention, deletion, export, and tenant-isolation evidence requiring legal review.",
    "event_contract": "AsyncAPI, message schema, producer, consumer, retry, and compatibility evidence.",
    "distributed_resilience": "Timeout, retry, idempotency, circuit breaker, concurrency, degradation, and fault-plan evidence.",
    "synthetic_test_data": "Privacy-safe deterministic fixture planning and workspace-only JSON generation.",
    "feature_flag_management": "Feature-flag inventory, ownership, rollout, stale-flag, cleanup, and rollback evidence.",
    "memory_profiling": "CPU, RAM, GPU, handle, connection, leak-test, and approved profiling evidence.",
    "cloud_deployment": "Provider-neutral identity, secret, region, cost, rollback, and deployment-planning evidence.",
    "llm_prompt_regression": "Golden prompt cases, output quality, format, latency, token, and regression comparison evidence.",
    "accessibility_execution": "Automated and manual accessibility readiness plus approved Compose-based execution.",
    "dependency_provisioning": "Hash-locked offline dependency inputs and approved ephemeral Compose provisioning.",
    "semantic_code_transformation": "Token-aware symbol impact analysis and workspace-only Python rename diffs.",
    "test_generation": "Repository-grounded test-gap analysis and deterministic workspace-only test skeletons.",
    "mutation_testing": "Mutation configuration, survivor evidence, and approved Compose mutation execution.",
    "visual_regression": "Screenshot baselines, viewport evidence, and approved Playwright visual execution.",
    "service_virtualization": "Deterministic workspace-only mock contracts for external service boundaries and failures.",
    "consumer_contract_testing": "Consumer/provider contract compatibility evidence and approved Compose execution.",
    "architecture_refactor_execution": "Entropy-driven refactor evidence and dry-run validation through existing patch gates.",
    "infrastructure_plan_execution": "Offline Terraform, Helm, and Kubernetes validation through approved Compose recipes.",
    "schema_drift_data_evolution": "ORM, migration, tenant, backfill, index, and approved schema-drift verification.",
    "chaos_verification": "Bounded non-destructive fault scenarios and approved Compose recovery verification.",
    "release_rollback": "Upgrade, rollback, compatibility, data-preservation, and approved rollback verification.",
    "semantic_repository_search": "Bounded intent-term repository path and symbol search without model loading.",
    "queue_broker_verification": "Queue ordering, idempotency, retry, dead-letter, and approved broker-test evidence.",
    "data_quality_execution": "Executable data constraints, reconciliation, lineage, anomaly, and backfill verification.",
    "secrets_lifecycle": "Value-free secret ownership, rotation, revocation, redaction, and rollback planning.",
    "cross_platform_matrix": "Operating-system, runtime, architecture, and approved compatibility-matrix evidence.",
    "documentation_drift": "Documentation-to-code command, route, setting, example, and approved doctest verification.",
    "requirements_traceability": "Requirement-to-architecture, source, test, artifact, and release traceability evidence.",
    "git_history_intelligence": "Bounded Git churn, co-change, ownership, and regression-hotspot evidence.",
    "database_query_performance": "Query-plan, index, N+1, lock, budget, and approved database-performance verification.",
    "stateful_workflow_verification": "State, transition, invariant, idempotency, and interruption-recovery verification.",
    "concurrency_correctness": "Race, deadlock, lock, atomicity, cancellation, and approved concurrency verification.",
    "reproducible_build_verification": "Deterministic build-input, artifact-hash, and approved repeat-build verification.",
    "configuration_parity": "Environment, setting, port, runtime, and secret-reference parity evidence.",
    "slo_telemetry_verification": "SLO, error-budget, metric, trace, log, redaction, and alert-contract verification.",
    "user_journey_synthesis": "Repository-grounded user journeys and workspace-only E2E journey specifications.",
    "upgrade_compatibility": "Runtime, framework, database, deprecation, migration, and approved upgrade verification.",
    "disaster_recovery_drill": "RPO, RTO, backup, restore, isolation, and approved recovery-drill verification.",
    "release_channel_management": "Alpha, beta, stable, promotion, downgrade, and compatibility evidence.",
    "clean_machine_certification": "Installer, first-run, uninstall, residue, and clean-machine evidence validation.",
    "signed_vulnerability_intelligence": "Local vulnerability-feed freshness, provenance, signature, and coverage gating.",
    "policy_as_code": "OPA, Rego, Conftest, infrastructure policy, and approved offline policy verification.",
    "formal_model_checking": "TLA+, PlusCal, Alloy, invariant, state-space, and approved bounded model checking.",
    "coverage_guided_test_synthesis": "Coverage-gap, surviving-mutant, branch-risk, and workspace-only test synthesis plans.",
    "architectural_debt_ledger": "Versioned architecture debt, trend, ownership, exception, and repayment evidence.",
    "project_archetype_synthesis": "Deterministic product classification and workspace-only architecture blueprint synthesis.",
    "behavioral_acceptance_oracle": "Requirement-to-observable-behavior traceability and approved acceptance verification.",
    "dynamic_authorization_verification": "Endpoint, role, tenant, and authorization-boundary evidence plus approved tests.",
    "long_horizon_checkpoint_integrity": "Checkpoint, idempotency, replay, approval, and recovery integrity evidence.",
    "agent_trajectory_forensics": "Redacted agent decision, evidence, tool, retry, and terminal-outcome forensics.",
    "delegation_optimizer": "Duplicate-work, ownership, context-budget, load, and skill-coverage optimization.",
    "cross_language_semantic_graph": "Bounded symbols, imports, language boundaries, and cross-language impact evidence.",
    "flaky_test_investigator": "Repeated outcome, timing variance, shared-state, and flaky-test investigation.",
    "online_migration_rehearsal": "Expand-contract, backfill, locking, compatibility, tenancy, and rollback rehearsal.",
    "local_resource_guardian": "Bounded project capacity, quota, retention, and isolated Compose cleanup controls.",
    "secure_update_delivery": "Offline update metadata, signature, hash, expiry, freeze, and rollback verification.",
    "installer_vm_lab": "Clean-VM installation, first-run, upgrade, uninstall, rollback, and residue evidence.",
    "model_runtime_certification": "Model manifest, backend, device, load-run-unload, memory, and rollback certification.",
    "api_abuse_simulation": "Non-destructive authorization, rate, replay, validation, and resource-abuse verification.",
    "performance_regression_bisect": "Evidence-driven benchmark history localization without Git history mutation.",
    "asset_provenance": "Hashed asset inventory, source, license, attribution, and legal-review evidence.",
    "domain_invariant_mining": "Repository-grounded candidate business invariants and reviewable invariant catalogs.",
    "ai_governance_evidence": "AI inventory, risk, evaluation, oversight, privacy, security, and incident evidence.",
    "language_server_intelligence": "Language-server configuration, typed source coverage, diagnostics, and approved type-analysis execution.",
    "autonomous_delivery_benchmark": "End-to-end requirements, architecture, implementation, verification, release, rollback, and model-provenance benchmarks.",
    "runtime_failure_lab": "Controlled interruption, resource, Docker, model-integrity, packaging, and recovery verification.",
    "native_ui_automation": "Windows native UI automation readiness and clean-machine evidence verification without host project execution.",
    "llm_application_security": "Prompt, retrieval, tool, tenant, secret, and output-boundary security verification for LLM applications.",
    "privacy_rights_verification": "Export, erasure, retention, consent, tenancy, audit, and approved privacy-rights execution evidence.",
    "cryptographic_protocol_verification": "TLS, JWT, key rotation, password hashing, randomness, and unsafe cryptographic-use verification.",
    "sdk_contract_conformance": "OpenAPI, generated SDK, versioning, error mapping, and approved client-contract verification.",
    "mobile_device_lab": "Android, iOS, Flutter, and React Native device-lab readiness and external evidence verification.",
    "capacity_economics": "Throughput, latency, memory, concurrency, and non-binding capacity planning from approved benchmarks.",
    "cross_store_consistency": "Database, cache, queue, search, outbox, reconciliation, and idempotency verification.",
    "product_telemetry_validation": "Event taxonomy, identity, consent, PII, funnel, experiment, and telemetry-quality verification.",
    "identity_protocol_conformance": "OAuth, OIDC, SAML, SCIM, session, and identity lifecycle protocol verification.",
    "temporal_monetary_correctness": "Timezone, DST, currency, decimal, rounding, tax, and exchange correctness verification.",
    "offline_sync_conflict_verification": "Offline queue, version, tombstone, idempotency, and conflict-resolution verification.",
    "binary_hardening_verification": "Binary integrity, signing, SBOM, mitigation, update, and rollback evidence verification.",
    "web_protocol_conformance": "HTTP caching, CORS, compression, streaming, retry, and web protocol verification.",
    "search_relevance_evaluation": "Ranking, filtering, tokenization, golden-query, and relevance-metric evaluation.",
    "agent_tool_contract_verification": "Agent tool schema, approval, timeout, idempotency, error, and result-contract verification.",
    "messaging_deliverability": "Messaging authentication, bounce, retry, consent, webhook, and deliverability verification.",
    "data_residency_mapping": "Regional storage, processing, backup, transfer, retention, and subprocessor evidence mapping.",
    "assistive_technology_lab": "Keyboard, semantics, focus, contrast, screen-reader, and assistive-technology evidence verification.",
}


def main() -> None:
    for name, description in ADVANCED_SKILLS.items():
        actions = ENGINEERING_SKILL_ACTIONS[name]
        permissions = {item.value: "DENY" for item in SkillPermission}
        for action in actions:
            for permission in action.permissions:
                permissions[permission] = "ASK_ALWAYS"
        directory = BUILTINS / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "manifest.yaml").write_text(
            _manifest(name, description, permissions),
            encoding="utf-8",
            newline="\n",
        )
        (directory / "SKILL.md").write_text(
            _documentation(name, description, actions),
            encoding="utf-8",
            newline="\n",
        )
        (directory / "runtime.py").write_text(
            _runtime(name),
            encoding="utf-8",
            newline="\n",
        )


def _manifest(
    name: str,
    description: str,
    permissions: dict[str, str],
) -> str:
    lines = [
        f"name: {name}",
        "version: 1.0",
        f"description: {description}",
        "enabled: true",
        "requires_user_approval: true",
        "audit_enabled: true",
        "permissions:",
        *[f"  {permission}: {decision}" for permission, decision in permissions.items()],
        "",
    ]
    return "\n".join(lines)


def _documentation(
    name: str,
    description: str,
    actions: tuple[EngineeringSkillAction, ...],
) -> str:
    title = name.replace("_", " ").title()
    lines = [
        f"# {title}",
        "",
        description,
        "",
        "## Actions",
        "",
    ]
    for action in actions:
        lines.append(f"- {action.name}: {action.description}")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Permissions are evaluated by the persistent ANN skill permission store.",
            "- Mutating, terminal, Git-write, or network actions require Approval Center.",
            "- Commands are fixed shell=False recipes; raw shell input is rejected.",
            "- Project paths are normalized and protected ANN paths remain blocked.",
            "- Every execution writes an audit record and bounded evidence artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def _runtime(name: str) -> str:
    title = name.replace("_", " ").title()
    return f'''"""{title} built-in runtime entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_network.skills.engineering_runtime import execute_engineering_action


def run(action: str, payload: dict[str, Any], workspace: str | Path) -> dict[str, Any]:
    """Execute a registered {title} action."""

    return execute_engineering_action("{name}", action, payload, Path(workspace).resolve())
'''


if __name__ == "__main__":
    main()
