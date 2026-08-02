"""Typed action catalog for ANN's built-in engineering skills."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from agentic_network.skills.models import SkillPermission


@dataclass(frozen=True)
class EngineeringSkillAction:
    """One closed, permission-scoped engineering skill action."""

    name: str
    description: str
    permissions: tuple[str, ...]
    approval_required: bool = False
    mutates_project: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


READ = SkillPermission.FILESYSTEM_READ.value
WRITE = SkillPermission.FILESYSTEM_WRITE.value
TERMINAL = SkillPermission.TERMINAL_EXECUTE.value


ENGINEERING_SKILL_ACTIONS: dict[str, tuple[EngineeringSkillAction, ...]] = {
    "internet_search": (
        EngineeringSkillAction(
            "search",
            "Search the public web through ANN's fixed privacy-bounded search endpoint.",
            (SkillPermission.NETWORK.value,),
            True,
        ),
    ),
    "package_registry": (
        EngineeringSkillAction(
            "lookup",
            "Read package metadata from the fixed PyPI or npm registry without installing.",
            (SkillPermission.NETWORK.value,),
            True,
        ),
    ),
    "requirements_contract": (
        EngineeringSkillAction(
            "refine", "Create a versioned, testable product contract from user intent.", (READ,)
        ),
        EngineeringSkillAction(
            "arbitrate",
            "Resolve contract ownership with the existing deterministic arbitration gate.",
            (READ,),
        ),
    ),
    "dependency_doctor": (
        EngineeringSkillAction(
            "analyze",
            "Inspect runtimes, manifests, lockfiles, and dependency compatibility.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify_lock", "Verify lockfile coverage without installing dependencies.", (READ,)
        ),
    ),
    "runtime_observability": (
        EngineeringSkillAction(
            "snapshot", "Collect bounded local runtime, log, port, and resource evidence.", (READ,)
        ),
        EngineeringSkillAction(
            "correlate", "Correlate runtime evidence with recent project failures.", (READ,)
        ),
    ),
    "test_quality": (
        EngineeringSkillAction(
            "analyze",
            "Measure test quality, weak assertions, skips, and mutation readiness.",
            (READ,),
        ),
        EngineeringSkillAction(
            "validate_failure",
            "Challenge a failed test through the existing Test Validity Gate.",
            (READ,),
        ),
    ),
    "architecture_fitness": (
        EngineeringSkillAction(
            "analyze", "Measure boundaries, cycles, complexity, duplication, and entropy.", (READ,)
        ),
    ),
    "backup_restore": (
        EngineeringSkillAction(
            "inspect", "Inspect backup, restore, retention, and recovery readiness.", (READ,)
        ),
        EngineeringSkillAction(
            "backup",
            "Create an approved PostgreSQL logical backup through Compose.",
            (READ, WRITE, TERMINAL),
            True,
        ),
        EngineeringSkillAction(
            "restore",
            "Restore an approved PostgreSQL logical backup through Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "performance_testing": (
        EngineeringSkillAction(
            "analyze", "Inspect performance budgets, benchmarks, and load-test readiness.", (READ,)
        ),
        EngineeringSkillAction(
            "run",
            "Run an allowlisted performance recipe in the project sandbox.",
            (READ, WRITE, TERMINAL),
            True,
        ),
    ),
    "supply_chain_compliance": (
        EngineeringSkillAction(
            "scan", "Audit licenses, lockfiles, provenance, SBOM, and dependency policy.", (READ,)
        ),
    ),
    "release_provenance": (
        EngineeringSkillAction(
            "inspect",
            "Inspect hashes, signatures, attestations, and clean-machine evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify", "Verify release provenance and Authenticode evidence.", (READ, TERMINAL), True
        ),
        EngineeringSkillAction(
            "sign",
            "Run the repository's approved Authenticode signing script.",
            (READ, WRITE, SkillPermission.NETWORK.value, TERMINAL),
            True,
            True,
        ),
    ),
    "deployment_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect deployment manifests, health checks, TLS, and rollback readiness.",
            (READ,),
        ),
        EngineeringSkillAction(
            "smoke",
            "Start and smoke-test an approved isolated local deployment.",
            (READ, WRITE, TERMINAL),
            True,
        ),
    ),
    "external_integration_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect provider, webhook, credential, retry, and idempotency boundaries.",
            (READ,),
        ),
        EngineeringSkillAction(
            "probe",
            "Probe explicitly allowlisted HTTPS integration health endpoints.",
            (READ, SkillPermission.NETWORK.value),
            True,
        ),
    ),
    "ux_quality": (
        EngineeringSkillAction(
            "analyze",
            "Inspect responsive, accessibility, keyboard, and visual-regression evidence.",
            (READ,),
        ),
    ),
    "git_collaboration": (
        EngineeringSkillAction(
            "status",
            "Read branch, worktree, and remote collaboration state.",
            (READ, SkillPermission.GIT_READ.value, TERMINAL),
            True,
        ),
        EngineeringSkillAction(
            "branch",
            "Create an approved namespaced Git branch.",
            (READ, WRITE, SkillPermission.GIT_WRITE.value, TERMINAL),
            True,
            True,
        ),
        EngineeringSkillAction(
            "commit",
            "Create an approved commit from an explicit bounded file list.",
            (READ, WRITE, SkillPermission.GIT_WRITE.value, TERMINAL),
            True,
            True,
        ),
        EngineeringSkillAction(
            "publish_pr",
            "Push an approved branch and open a draft pull request.",
            (
                READ,
                SkillPermission.NETWORK.value,
                SkillPermission.GIT_READ.value,
                SkillPermission.GIT_WRITE.value,
                TERMINAL,
            ),
            True,
            True,
        ),
    ),
    "mobile_validation": (
        EngineeringSkillAction(
            "analyze", "Inspect Android, iOS, React Native, and Flutter project readiness.", (READ,)
        ),
    ),
    "game_validation": (
        EngineeringSkillAction(
            "analyze",
            "Inspect game loop, assets, controls, physics, and gameplay-test readiness.",
            (READ,),
        ),
    ),
    "data_pipeline": (
        EngineeringSkillAction(
            "analyze",
            "Inspect ETL lineage, schemas, quality checks, idempotency, and backfills.",
            (READ,),
        ),
    ),
    "ml_evaluation": (
        EngineeringSkillAction(
            "analyze",
            "Inspect datasets, metrics, model cards, reproducibility, and evaluation evidence.",
            (READ,),
        ),
    ),
    "infrastructure_validation": (
        EngineeringSkillAction(
            "analyze",
            "Inspect Terraform, Kubernetes, CI, secrets, and infrastructure safety.",
            (READ,),
        ),
    ),
    "desktop_validation": (
        EngineeringSkillAction(
            "analyze",
            "Inspect native desktop packaging, lifecycle, accessibility, and update readiness.",
            (READ,),
        ),
    ),
    "localization": (
        EngineeringSkillAction(
            "analyze",
            "Inspect locale coverage, hardcoded text, pluralization, and RTL readiness.",
            (READ,),
        ),
    ),
    "agent_evaluation": (
        EngineeringSkillAction(
            "evaluate",
            "Score agent task outcomes against explicit golden expectations and runtime evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "compare",
            "Compare bounded agent or model evaluation result sets without loading a model.",
            (READ,),
        ),
    ),
    "adversarial_red_team": (
        EngineeringSkillAction(
            "analyze",
            "Inspect prompt, tool, approval, filesystem, and secret boundaries for adversarial exposure.",
            (READ,),
        ),
        EngineeringSkillAction(
            "simulate",
            "Generate a non-executing adversarial scenario matrix and expected defenses.",
            (READ,),
        ),
    ),
    "fuzz_property_testing": (
        EngineeringSkillAction(
            "inspect",
            "Inspect fuzz targets, property tests, schemas, seeds, and crash-corpus readiness.",
            (READ,),
        ),
        EngineeringSkillAction(
            "plan",
            "Create bounded fuzz and property-testing targets from repository evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved fuzz test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "dependency_remediation": (
        EngineeringSkillAction(
            "analyze",
            "Rank vulnerable, incompatible, and stale dependencies using local manifest evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "plan",
            "Prepare a bounded dependency update, verification, and rollback plan without installing packages.",
            (READ,),
        ),
    ),
    "refactor_migration": (
        EngineeringSkillAction(
            "analyze",
            "Identify refactor seams, deprecated APIs, blast radius, and migration ordering.",
            (READ,),
        ),
        EngineeringSkillAction(
            "plan",
            "Create an incremental codemod and compatibility migration plan without applying changes.",
            (READ,),
        ),
    ),
    "incident_response": (
        EngineeringSkillAction(
            "triage",
            "Correlate bounded logs, events, releases, and health evidence into an incident assessment.",
            (READ,),
        ),
        EngineeringSkillAction(
            "postmortem",
            "Generate a blameless postmortem draft with evidence, impact, and prevention actions.",
            (READ,),
        ),
    ),
    "observability_instrumentation": (
        EngineeringSkillAction(
            "inspect",
            "Inspect metrics, traces, logs, correlation IDs, dashboards, and alert coverage.",
            (READ,),
        ),
        EngineeringSkillAction(
            "plan",
            "Prepare an OpenTelemetry-compatible instrumentation plan without modifying the project.",
            (READ,),
        ),
    ),
    "context_quality_evaluation": (
        EngineeringSkillAction(
            "evaluate",
            "Measure retrieval precision, recall, stale context, and token-budget quality.",
            (READ,),
        ),
    ),
    "failure_replay": (
        EngineeringSkillAction(
            "prepare",
            "Create a deterministic replay recipe from bounded failure evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Validate replay completeness, redaction, environment, and seed evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run an approved fixed replay recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "privacy_data_governance": (
        EngineeringSkillAction(
            "scan",
            "Inspect PII, consent, retention, deletion, export, and tenant-isolation evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "retention_plan",
            "Create a data-classification and retention plan requiring human legal review.",
            (READ,),
        ),
    ),
    "event_contract": (
        EngineeringSkillAction(
            "analyze",
            "Validate AsyncAPI, message schemas, producers, consumers, retries, and compatibility.",
            (READ,),
        ),
    ),
    "distributed_resilience": (
        EngineeringSkillAction(
            "analyze",
            "Inspect timeouts, retries, idempotency, circuit breakers, concurrency, and degradation.",
            (READ,),
        ),
        EngineeringSkillAction(
            "fault_plan",
            "Create a non-executing fault-injection and recovery verification plan.",
            (READ,),
        ),
    ),
    "synthetic_test_data": (
        EngineeringSkillAction(
            "plan",
            "Design privacy-safe deterministic fixture coverage from a bounded schema.",
            (READ,),
        ),
        EngineeringSkillAction(
            "generate",
            "Generate deterministic synthetic JSON fixtures only inside the skill workspace.",
            (READ,),
        ),
    ),
    "feature_flag_management": (
        EngineeringSkillAction(
            "analyze",
            "Inventory feature flags, defaults, ownership, rollout, and stale-flag evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "cleanup_plan",
            "Prepare a safe flag retirement and rollback plan without changing code.",
            (READ,),
        ),
    ),
    "memory_profiling": (
        EngineeringSkillAction(
            "inspect", "Inspect CPU, RAM, GPU, handle, connection, and leak-test evidence.", (READ,)
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved memory profiling test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "cloud_deployment": (
        EngineeringSkillAction(
            "inspect",
            "Inspect provider manifests, identity, secret, region, cost, and rollback boundaries.",
            (READ,),
        ),
        EngineeringSkillAction(
            "plan",
            "Create a provider-neutral deployment plan without contacting or modifying cloud accounts.",
            (READ,),
        ),
    ),
    "llm_prompt_regression": (
        EngineeringSkillAction(
            "evaluate",
            "Evaluate bounded prompt cases against explicit expected output evidence without model loading.",
            (READ,),
        ),
        EngineeringSkillAction(
            "compare",
            "Compare prompt-suite result sets for quality, format, latency, and token regressions.",
            (READ,),
        ),
    ),
    "accessibility_execution": (
        EngineeringSkillAction(
            "inspect", "Inspect automated and manual accessibility execution readiness.", (READ,)
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved accessibility package script inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "dependency_provisioning": (
        EngineeringSkillAction(
            "inspect",
            "Inspect lockfiles, hashes, offline caches, and deterministic dependency inputs.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Provision only hash-locked dependencies into an ephemeral Compose container target.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "semantic_code_transformation": (
        EngineeringSkillAction(
            "analyze",
            "Locate typed symbol rename targets and estimate their repository impact.",
            (READ,),
        ),
        EngineeringSkillAction(
            "prepare",
            "Prepare a token-aware Python symbol rename diff in the skill workspace without applying it.",
            (READ,),
        ),
    ),
    "test_generation": (
        EngineeringSkillAction(
            "analyze",
            "Identify test gaps from source, routes, contracts, and existing test evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "generate",
            "Generate a deterministic test plan and safe test skeleton in the skill workspace.",
            (READ,),
        ),
    ),
    "mutation_testing": (
        EngineeringSkillAction(
            "inspect",
            "Inspect mutation configuration, test strength, and surviving-mutant evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved mutation recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "visual_regression": (
        EngineeringSkillAction(
            "inspect",
            "Inspect screenshot baselines, viewport coverage, masks, and visual evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved Playwright visual-regression recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "service_virtualization": (
        EngineeringSkillAction(
            "inspect",
            "Inspect external service boundaries, fixtures, webhooks, latency, and failure modes.",
            (READ,),
        ),
        EngineeringSkillAction(
            "generate",
            "Generate deterministic mock-service contracts only inside the skill workspace.",
            (READ,),
        ),
    ),
    "consumer_contract_testing": (
        EngineeringSkillAction(
            "analyze",
            "Inspect consumer/provider contracts, versions, fixtures, and compatibility evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved consumer-contract recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "architecture_refactor_execution": (
        EngineeringSkillAction(
            "analyze",
            "Rank architecture refactor candidates using entropy, cycles, coupling, and impact evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "prepare",
            "Validate an explicit refactor diff through the existing dry-run Patch Workspace gate.",
            (READ,),
        ),
    ),
    "infrastructure_plan_execution": (
        EngineeringSkillAction(
            "inspect",
            "Inspect Terraform, Helm, and Kubernetes plan prerequisites without contacting cloud APIs.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved offline infrastructure validate/plan recipe inside Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "schema_drift_data_evolution": (
        EngineeringSkillAction(
            "inspect",
            "Compare ORM, migrations, indexes, tenant scope, backfills, and destructive operations.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved Alembic schema-drift check inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "chaos_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect bounded fault cases, recovery assertions, timeouts, and rollback evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved non-destructive chaos test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "release_rollback": (
        EngineeringSkillAction(
            "inspect",
            "Inspect upgrade, rollback, data preservation, and version compatibility evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved release rollback verification recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "semantic_repository_search": (
        EngineeringSkillAction(
            "query",
            "Search bounded repository paths and symbols using intent terms without loading a model.",
            (READ,),
        ),
    ),
    "queue_broker_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect queue schemas, ordering, idempotency, retries, and dead-letter handling.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved queue/broker integration recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "data_quality_execution": (
        EngineeringSkillAction(
            "inspect",
            "Inspect executable data constraints, reconciliation, lineage, anomaly, and backfill evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved data-quality recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "secrets_lifecycle": (
        EngineeringSkillAction(
            "inspect",
            "Inspect secret references, ownership, rotation, revocation, redaction, and storage boundaries.",
            (READ,),
        ),
        EngineeringSkillAction(
            "plan",
            "Prepare a value-free secret rotation and rollback plan requiring human approval.",
            (READ,),
        ),
    ),
    "cross_platform_matrix": (
        EngineeringSkillAction(
            "inspect",
            "Inspect declared operating systems, runtimes, architectures, and compatibility evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved compatibility-matrix recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "documentation_drift": (
        EngineeringSkillAction(
            "analyze",
            "Compare documentation commands, routes, settings, and examples with repository evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved documentation-test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "requirements_traceability": (
        EngineeringSkillAction(
            "analyze",
            "Trace requirements through architecture, source, tests, and release evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Identify orphaned requirements and unsubstantiated implementation evidence.",
            (READ,),
        ),
    ),
    "git_history_intelligence": (
        EngineeringSkillAction(
            "analyze",
            "Compute bounded churn, co-change, ownership, and regression-hotspot evidence from Git history.",
            (READ, SkillPermission.GIT_READ.value, TERMINAL),
            True,
        ),
    ),
    "database_query_performance": (
        EngineeringSkillAction(
            "inspect",
            "Inspect query plans, indexes, N+1 signals, locks, and database performance budgets.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved database-performance test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "stateful_workflow_verification": (
        EngineeringSkillAction(
            "analyze",
            "Inspect states, transitions, invariants, idempotency, and interruption recovery.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved state-machine verification tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "concurrency_correctness": (
        EngineeringSkillAction(
            "inspect",
            "Inspect locks, async cancellation, races, deadlocks, and atomicity boundaries.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved deterministic concurrency tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "reproducible_build_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect deterministic build inputs, timestamps, locks, and artifact hashes.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved reproducible-build comparison recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "configuration_parity": (
        EngineeringSkillAction(
            "analyze",
            "Compare declared settings, environment keys, ports, and runtime versions across environments.",
            (READ,),
        ),
    ),
    "slo_telemetry_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect SLOs, error budgets, metrics, traces, logs, redaction, and alert evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved telemetry-contract tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "user_journey_synthesis": (
        EngineeringSkillAction(
            "analyze",
            "Map user stories, routes, roles, and acceptance criteria into bounded journeys.",
            (READ,),
        ),
        EngineeringSkillAction(
            "generate",
            "Generate reviewable E2E journey specifications only inside the skill workspace.",
            (READ,),
        ),
    ),
    "upgrade_compatibility": (
        EngineeringSkillAction(
            "inspect",
            "Inspect runtime, framework, database, deprecation, and migration compatibility.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved upgrade-compatibility test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "disaster_recovery_drill": (
        EngineeringSkillAction(
            "inspect",
            "Inspect RPO, RTO, backup integrity, restore isolation, and recovery assertions.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved destructive-isolated disaster-recovery test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "release_channel_management": (
        EngineeringSkillAction(
            "inspect",
            "Inspect alpha, beta, stable, promotion, downgrade, and compatibility policies.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Verify bounded release-channel evidence without publishing a release.",
            (READ,),
        ),
    ),
    "clean_machine_certification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect clean-machine installer, first-run, uninstall, and residue requirements.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Validate supplied clean-machine evidence without executing the installer on the host.",
            (READ,),
        ),
    ),
    "signed_vulnerability_intelligence": (
        EngineeringSkillAction(
            "inspect",
            "Inspect local vulnerability-feed freshness, provenance, signature, and coverage evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Gate a local vulnerability feed on bounded cryptographic verification evidence.",
            (READ,),
        ),
    ),
    "policy_as_code": (
        EngineeringSkillAction(
            "inspect",
            "Inspect OPA, Rego, Conftest, infrastructure policies, and policy-test coverage.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved offline policy test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "formal_model_checking": (
        EngineeringSkillAction(
            "inspect", "Inspect TLA+, PlusCal, Alloy, and explicit invariant evidence.", (READ,)
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved bounded model-checking recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "coverage_guided_test_synthesis": (
        EngineeringSkillAction(
            "analyze",
            "Rank uncovered branches and surviving mutants using supplied coverage evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "generate", "Generate a bounded test-gap plan only inside the skill workspace.", (READ,)
        ),
    ),
    "architectural_debt_ledger": (
        EngineeringSkillAction(
            "snapshot",
            "Create a bounded architecture-debt snapshot from repository evidence and supplied metrics.",
            (READ,),
        ),
        EngineeringSkillAction(
            "compare",
            "Compare debt snapshots and identify improving or regressing architecture metrics.",
            (READ,),
        ),
    ),
    "project_archetype_synthesis": (
        EngineeringSkillAction(
            "analyze",
            "Classify the repository and requested product using deterministic cross-domain evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "synthesize",
            "Generate a bounded architecture blueprint only inside the skill workspace.",
            (READ,),
        ),
    ),
    "behavioral_acceptance_oracle": (
        EngineeringSkillAction(
            "analyze",
            "Map requirements and acceptance criteria to observable behavior and test evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved behavioral-oracle test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "dynamic_authorization_verification": (
        EngineeringSkillAction(
            "inspect",
            "Build an endpoint, role, tenant, and authorization-control verification matrix.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved authorization-boundary tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "long_horizon_checkpoint_integrity": (
        EngineeringSkillAction(
            "inspect",
            "Inspect checkpoints, idempotency keys, replay guards, approvals, and recovery evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved checkpoint-resume recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "agent_trajectory_forensics": (
        EngineeringSkillAction(
            "analyze",
            "Analyze bounded agent decisions, evidence, tool calls, retries, and terminal outcomes.",
            (READ,),
        ),
        EngineeringSkillAction(
            "compare",
            "Compare two redacted trajectory summaries without exposing prompts or secrets.",
            (READ,),
        ),
    ),
    "delegation_optimizer": (
        EngineeringSkillAction(
            "analyze",
            "Detect duplicate delegation, missing ownership, context waste, and skill coverage gaps.",
            (READ,),
        ),
        EngineeringSkillAction(
            "plan",
            "Create a bounded evidence-based delegation plan without executing subagents.",
            (READ,),
        ),
    ),
    "cross_language_semantic_graph": (
        EngineeringSkillAction(
            "scan",
            "Index bounded symbols and imports across Python, TypeScript, JavaScript, Go, Rust, Java, and C#.",
            (READ,),
        ),
        EngineeringSkillAction(
            "impact",
            "Rank cross-language files and boundaries affected by supplied target paths or symbols.",
            (READ,),
        ),
    ),
    "flaky_test_investigator": (
        EngineeringSkillAction(
            "analyze",
            "Classify repeated test outcomes, timing variance, shared-state signals, and failure signatures.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved repeated-test investigation recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "online_migration_rehearsal": (
        EngineeringSkillAction(
            "inspect",
            "Inspect expand-contract ordering, locks, backfills, compatibility, and rollback evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved isolated online-migration rehearsal inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "local_resource_guardian": (
        EngineeringSkillAction(
            "snapshot",
            "Measure bounded project and local disk capacity without enumerating unrelated host data.",
            (READ,),
        ),
        EngineeringSkillAction(
            "plan",
            "Create quota, retention, and cleanup recommendations without deleting host data.",
            (READ,),
        ),
        EngineeringSkillAction(
            "cleanup",
            "Run only the approved isolated Compose cleanup recipe; never delete arbitrary host paths.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "secure_update_delivery": (
        EngineeringSkillAction(
            "inspect",
            "Inspect offline update metadata, version monotonicity, expiry, hashes, signatures, and rollback policy.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Verify supplied update evidence without downloading, installing, or publishing anything.",
            (READ,),
        ),
    ),
    "installer_vm_lab": (
        EngineeringSkillAction(
            "inspect",
            "Inspect clean-VM install, launch, upgrade, uninstall, rollback, and residue evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved installer-lab evidence recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "model_runtime_certification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect model manifest, backend, device, memory, load-run-unload, and rollback evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "benchmark",
            "Run only an approved model-runtime certification recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "api_abuse_simulation": (
        EngineeringSkillAction(
            "inspect",
            "Derive bounded authorization, rate-limit, injection, replay, and resource-abuse scenarios.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved non-destructive API abuse test recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "performance_regression_bisect": (
        EngineeringSkillAction(
            "analyze",
            "Rank supplied benchmark revisions and identify the first evidenced performance regression.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved performance-history recipe without mutating Git history.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "asset_provenance": (
        EngineeringSkillAction(
            "scan",
            "Inventory bounded visual, audio, font, and binary assets with hashes and attribution evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Gate supplied asset provenance without claiming legal clearance.",
            (READ,),
        ),
    ),
    "domain_invariant_mining": (
        EngineeringSkillAction(
            "analyze",
            "Mine candidate business invariants from models, schemas, guards, tests, and requirements.",
            (READ,),
        ),
        EngineeringSkillAction(
            "generate",
            "Generate a reviewable invariant catalog only inside the skill workspace.",
            (READ,),
        ),
    ),
    "ai_governance_evidence": (
        EngineeringSkillAction(
            "assess",
            "Assess bounded AI inventory, intended use, evaluation, oversight, privacy, and incident evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "compare",
            "Compare governance snapshots without claiming legal or regulatory compliance.",
            (READ,),
        ),
    ),
    "language_server_intelligence": (
        EngineeringSkillAction(
            "inspect",
            "Inspect language-server configuration, typed source coverage, and supplied diagnostics.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved Python or web type-analysis recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "autonomous_delivery_benchmark": (
        EngineeringSkillAction(
            "inspect",
            "Assess end-to-end delivery stages, model provenance, and benchmark evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only an approved delivery-benchmark recipe inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "runtime_failure_lab": (
        EngineeringSkillAction(
            "inspect",
            "Inspect bounded recovery evidence for interruption, resource, Docker, model, and packaging failures.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved non-destructive runtime-failure tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "native_ui_automation": (
        EngineeringSkillAction(
            "inspect",
            "Inspect Windows UI automation configuration and native application test readiness.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Verify supplied clean-machine native UI evidence without launching project binaries on the host.",
            (READ,),
        ),
    ),
    "llm_application_security": (
        EngineeringSkillAction(
            "inspect",
            "Inspect prompt, retrieval, tool, secret, tenant, and output-validation boundaries.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved non-destructive LLM application security tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "privacy_rights_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect export, erasure, retention, consent, tenancy, and audit implementation evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved privacy-rights verification tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "cryptographic_protocol_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect TLS, JWT, rotation, hashing, randomness, and unsafe cryptographic usage evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved cryptographic protocol tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "sdk_contract_conformance": (
        EngineeringSkillAction(
            "analyze",
            "Compare OpenAPI evidence, generated SDK surfaces, versioning, errors, and contract tests.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved SDK contract-conformance tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "mobile_device_lab": (
        EngineeringSkillAction(
            "inspect",
            "Inspect Android, iOS, Flutter, and React Native device-test readiness.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Verify supplied device-lab evidence without starting host emulators or executing project binaries.",
            (READ,),
        ),
    ),
    "capacity_economics": (
        EngineeringSkillAction(
            "analyze",
            "Analyze supplied throughput, latency, memory, concurrency, and non-binding capacity evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "benchmark",
            "Run only an approved capacity benchmark inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "cross_store_consistency": (
        EngineeringSkillAction(
            "inspect",
            "Inspect database, cache, queue, search, outbox, reconciliation, and idempotency boundaries.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved cross-store consistency tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "product_telemetry_validation": (
        EngineeringSkillAction(
            "analyze",
            "Inspect event taxonomy, identity, consent, PII, funnels, experiments, and telemetry quality.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved product telemetry contract tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "identity_protocol_conformance": (
        EngineeringSkillAction(
            "inspect",
            "Inspect OAuth, OIDC, SAML, SCIM, session, and identity lifecycle conformance evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved identity-protocol contract tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "temporal_monetary_correctness": (
        EngineeringSkillAction(
            "inspect",
            "Inspect timezone, DST, currency, decimal, rounding, and tax correctness evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved temporal and monetary correctness tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "offline_sync_conflict_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect offline queues, versions, tombstones, idempotency, and conflict-resolution evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved offline synchronization and conflict tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "binary_hardening_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect signing, hashes, SBOM, mitigations, update, and binary release evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Verify attested external binary-lab evidence without launching host binaries.",
            (READ,),
        ),
    ),
    "web_protocol_conformance": (
        EngineeringSkillAction(
            "inspect",
            "Inspect HTTP caching, CORS, streaming, compression, retry, and protocol-boundary evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved web-protocol conformance tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "search_relevance_evaluation": (
        EngineeringSkillAction(
            "analyze",
            "Analyze ranking, filtering, tokenization, golden-query, and relevance-metric evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved search relevance evaluations inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "agent_tool_contract_verification": (
        EngineeringSkillAction(
            "inspect",
            "Inspect tool schemas, approvals, timeouts, idempotency, error handling, and result validation.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved agent-tool contract tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "messaging_deliverability": (
        EngineeringSkillAction(
            "inspect",
            "Inspect email and notification authentication, bounce, retry, consent, and delivery evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "run",
            "Run only approved messaging deliverability contract tests inside Docker Compose.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "data_residency_mapping": (
        EngineeringSkillAction(
            "analyze",
            "Map regional storage, processing, backup, transfer, retention, and subprocessor evidence.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Verify attested residency evidence while preserving mandatory human legal review.",
            (READ,),
        ),
    ),
    "assistive_technology_lab": (
        EngineeringSkillAction(
            "inspect",
            "Inspect keyboard, semantics, focus, contrast, and assistive-technology test readiness.",
            (READ,),
        ),
        EngineeringSkillAction(
            "verify",
            "Verify attested assistive-technology runner evidence without host UI automation.",
            (READ,),
        ),
    ),
    "repository_intelligence": (
        EngineeringSkillAction(
            "scan", "Index AST symbols, routes, tests, and dependencies.", (READ,)
        ),
        EngineeringSkillAction("impact", "Rank files and tests affected by target paths.", (READ,)),
    ),
    "sandbox_verification": (
        EngineeringSkillAction(
            "detect", "Detect allowlisted build, lint, test, and E2E recipes.", (READ,)
        ),
        EngineeringSkillAction(
            "run",
            "Execute only detected allowlisted verification recipes.",
            (READ, WRITE, TERMINAL),
            True,
        ),
    ),
    "failure_diagnostics": (
        EngineeringSkillAction(
            "diagnose", "Compile AST-localized, cross-domain failure evidence.", (READ,)
        ),
    ),
    "patch_workspace": (
        EngineeringSkillAction("inspect", "Validate a unified diff without applying it.", (READ,)),
        EngineeringSkillAction(
            "apply",
            "Apply a validated patch through existing patch gates.",
            (READ, WRITE),
            True,
            True,
        ),
    ),
    "browser_e2e": (
        EngineeringSkillAction(
            "detect", "Detect a local Playwright recipe and evidence paths.", (READ,)
        ),
        EngineeringSkillAction(
            "run",
            "Run an allowlisted local Playwright package script.",
            (READ, WRITE, TERMINAL),
            True,
        ),
    ),
    "database_migration": (
        EngineeringSkillAction(
            "inspect", "Inspect Alembic revisions, indexes, and tenant-scope signals.", (READ,)
        ),
        EngineeringSkillAction(
            "upgrade",
            "Run an approved Alembic upgrade in the project workspace.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
        EngineeringSkillAction(
            "downgrade",
            "Run an approved Alembic downgrade in the project workspace.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "security_audit": (
        EngineeringSkillAction(
            "scan",
            "Run deterministic source, secret, dependency, Docker, auth, RBAC, and API checks.",
            (READ,),
        ),
    ),
    "container_operations": (
        EngineeringSkillAction(
            "config", "Validate Docker Compose configuration.", (READ, TERMINAL), True
        ),
        EngineeringSkillAction("status", "Read Compose service status.", (READ, TERMINAL), True),
        EngineeringSkillAction("logs", "Read bounded Compose logs.", (READ, TERMINAL), True),
        EngineeringSkillAction(
            "up", "Start an approved isolated Compose project.", (READ, WRITE, TERMINAL), True, True
        ),
        EngineeringSkillAction(
            "down",
            "Stop an approved isolated Compose project.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
        EngineeringSkillAction(
            "cleanup",
            "Remove approved project containers and orphans.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
    "api_contract": (
        EngineeringSkillAction(
            "analyze",
            "Compare OpenAPI, backend routes, frontend calls, and webhook contracts.",
            (READ,),
        ),
    ),
    "release_packaging": (
        EngineeringSkillAction(
            "prepare",
            "Create a local SBOM, hashes, release archive, and rollback manifest.",
            (READ, WRITE),
        ),
        EngineeringSkillAction(
            "verify", "Verify a prepared package and installer evidence.", (READ,)
        ),
        EngineeringSkillAction(
            "smoke_installer",
            "Run the approved installer verification recipe.",
            (READ, WRITE, TERMINAL),
            True,
            True,
        ),
    ),
}


def get_engineering_action(skill_name: str, action: str) -> EngineeringSkillAction | None:
    """Return an action specification without executing it."""

    return next(
        (item for item in ENGINEERING_SKILL_ACTIONS.get(skill_name, ()) if item.name == action),
        None,
    )


def engineering_skill_catalog() -> list[dict[str, object]]:
    """Return the stable user/API catalog."""

    return [
        {"name": name, "actions": [action.to_dict() for action in actions]}
        for name, actions in sorted(ENGINEERING_SKILL_ACTIONS.items())
    ]
