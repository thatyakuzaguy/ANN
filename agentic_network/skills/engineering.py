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
        EngineeringSkillAction("search", "Search the public web through ANN's fixed privacy-bounded search endpoint.", (SkillPermission.NETWORK.value,), True),
    ),
    "package_registry": (
        EngineeringSkillAction("lookup", "Read package metadata from the fixed PyPI or npm registry without installing.", (SkillPermission.NETWORK.value,), True),
    ),
    "requirements_contract": (
        EngineeringSkillAction("refine", "Create a versioned, testable product contract from user intent.", (READ,)),
        EngineeringSkillAction("arbitrate", "Resolve contract ownership with the existing deterministic arbitration gate.", (READ,)),
    ),
    "dependency_doctor": (
        EngineeringSkillAction("analyze", "Inspect runtimes, manifests, lockfiles, and dependency compatibility.", (READ,)),
        EngineeringSkillAction("verify_lock", "Verify lockfile coverage without installing dependencies.", (READ,)),
    ),
    "runtime_observability": (
        EngineeringSkillAction("snapshot", "Collect bounded local runtime, log, port, and resource evidence.", (READ,)),
        EngineeringSkillAction("correlate", "Correlate runtime evidence with recent project failures.", (READ,)),
    ),
    "test_quality": (
        EngineeringSkillAction("analyze", "Measure test quality, weak assertions, skips, and mutation readiness.", (READ,)),
        EngineeringSkillAction("validate_failure", "Challenge a failed test through the existing Test Validity Gate.", (READ,)),
    ),
    "architecture_fitness": (
        EngineeringSkillAction("analyze", "Measure boundaries, cycles, complexity, duplication, and entropy.", (READ,)),
    ),
    "backup_restore": (
        EngineeringSkillAction("inspect", "Inspect backup, restore, retention, and recovery readiness.", (READ,)),
        EngineeringSkillAction("backup", "Create an approved PostgreSQL logical backup through Compose.", (READ, WRITE, TERMINAL), True),
        EngineeringSkillAction("restore", "Restore an approved PostgreSQL logical backup through Compose.", (READ, WRITE, TERMINAL), True, True),
    ),
    "performance_testing": (
        EngineeringSkillAction("analyze", "Inspect performance budgets, benchmarks, and load-test readiness.", (READ,)),
        EngineeringSkillAction("run", "Run an allowlisted performance recipe in the project sandbox.", (READ, WRITE, TERMINAL), True),
    ),
    "supply_chain_compliance": (
        EngineeringSkillAction("scan", "Audit licenses, lockfiles, provenance, SBOM, and dependency policy.", (READ,)),
    ),
    "release_provenance": (
        EngineeringSkillAction("inspect", "Inspect hashes, signatures, attestations, and clean-machine evidence.", (READ,)),
        EngineeringSkillAction("verify", "Verify release provenance and Authenticode evidence.", (READ, TERMINAL), True),
        EngineeringSkillAction("sign", "Run the repository's approved Authenticode signing script.", (READ, WRITE, SkillPermission.NETWORK.value, TERMINAL), True, True),
    ),
    "deployment_verification": (
        EngineeringSkillAction("inspect", "Inspect deployment manifests, health checks, TLS, and rollback readiness.", (READ,)),
        EngineeringSkillAction("smoke", "Start and smoke-test an approved isolated local deployment.", (READ, WRITE, TERMINAL), True),
    ),
    "external_integration_verification": (
        EngineeringSkillAction("inspect", "Inspect provider, webhook, credential, retry, and idempotency boundaries.", (READ,)),
        EngineeringSkillAction("probe", "Probe explicitly allowlisted HTTPS integration health endpoints.", (READ, SkillPermission.NETWORK.value), True),
    ),
    "ux_quality": (
        EngineeringSkillAction("analyze", "Inspect responsive, accessibility, keyboard, and visual-regression evidence.", (READ,)),
    ),
    "git_collaboration": (
        EngineeringSkillAction("status", "Read branch, worktree, and remote collaboration state.", (READ, SkillPermission.GIT_READ.value, TERMINAL), True),
        EngineeringSkillAction("branch", "Create an approved namespaced Git branch.", (READ, WRITE, SkillPermission.GIT_WRITE.value, TERMINAL), True, True),
        EngineeringSkillAction("commit", "Create an approved commit from an explicit bounded file list.", (READ, WRITE, SkillPermission.GIT_WRITE.value, TERMINAL), True, True),
        EngineeringSkillAction("publish_pr", "Push an approved branch and open a draft pull request.", (READ, SkillPermission.NETWORK.value, SkillPermission.GIT_READ.value, SkillPermission.GIT_WRITE.value, TERMINAL), True, True),
    ),
    "mobile_validation": (
        EngineeringSkillAction("analyze", "Inspect Android, iOS, React Native, and Flutter project readiness.", (READ,)),
    ),
    "game_validation": (
        EngineeringSkillAction("analyze", "Inspect game loop, assets, controls, physics, and gameplay-test readiness.", (READ,)),
    ),
    "data_pipeline": (
        EngineeringSkillAction("analyze", "Inspect ETL lineage, schemas, quality checks, idempotency, and backfills.", (READ,)),
    ),
    "ml_evaluation": (
        EngineeringSkillAction("analyze", "Inspect datasets, metrics, model cards, reproducibility, and evaluation evidence.", (READ,)),
    ),
    "infrastructure_validation": (
        EngineeringSkillAction("analyze", "Inspect Terraform, Kubernetes, CI, secrets, and infrastructure safety.", (READ,)),
    ),
    "desktop_validation": (
        EngineeringSkillAction("analyze", "Inspect native desktop packaging, lifecycle, accessibility, and update readiness.", (READ,)),
    ),
    "localization": (
        EngineeringSkillAction("analyze", "Inspect locale coverage, hardcoded text, pluralization, and RTL readiness.", (READ,)),
    ),
    "agent_evaluation": (
        EngineeringSkillAction("evaluate", "Score agent task outcomes against explicit golden expectations and runtime evidence.", (READ,)),
        EngineeringSkillAction("compare", "Compare bounded agent or model evaluation result sets without loading a model.", (READ,)),
    ),
    "adversarial_red_team": (
        EngineeringSkillAction("analyze", "Inspect prompt, tool, approval, filesystem, and secret boundaries for adversarial exposure.", (READ,)),
        EngineeringSkillAction("simulate", "Generate a non-executing adversarial scenario matrix and expected defenses.", (READ,)),
    ),
    "fuzz_property_testing": (
        EngineeringSkillAction("inspect", "Inspect fuzz targets, property tests, schemas, seeds, and crash-corpus readiness.", (READ,)),
        EngineeringSkillAction("plan", "Create bounded fuzz and property-testing targets from repository evidence.", (READ,)),
        EngineeringSkillAction("run", "Run only an approved fuzz test recipe inside Docker Compose.", (READ, WRITE, TERMINAL), True, True),
    ),
    "dependency_remediation": (
        EngineeringSkillAction("analyze", "Rank vulnerable, incompatible, and stale dependencies using local manifest evidence.", (READ,)),
        EngineeringSkillAction("plan", "Prepare a bounded dependency update, verification, and rollback plan without installing packages.", (READ,)),
    ),
    "refactor_migration": (
        EngineeringSkillAction("analyze", "Identify refactor seams, deprecated APIs, blast radius, and migration ordering.", (READ,)),
        EngineeringSkillAction("plan", "Create an incremental codemod and compatibility migration plan without applying changes.", (READ,)),
    ),
    "incident_response": (
        EngineeringSkillAction("triage", "Correlate bounded logs, events, releases, and health evidence into an incident assessment.", (READ,)),
        EngineeringSkillAction("postmortem", "Generate a blameless postmortem draft with evidence, impact, and prevention actions.", (READ,)),
    ),
    "observability_instrumentation": (
        EngineeringSkillAction("inspect", "Inspect metrics, traces, logs, correlation IDs, dashboards, and alert coverage.", (READ,)),
        EngineeringSkillAction("plan", "Prepare an OpenTelemetry-compatible instrumentation plan without modifying the project.", (READ,)),
    ),
    "context_quality_evaluation": (
        EngineeringSkillAction("evaluate", "Measure retrieval precision, recall, stale context, and token-budget quality.", (READ,)),
    ),
    "failure_replay": (
        EngineeringSkillAction("prepare", "Create a deterministic replay recipe from bounded failure evidence.", (READ,)),
        EngineeringSkillAction("verify", "Validate replay completeness, redaction, environment, and seed evidence.", (READ,)),
        EngineeringSkillAction("run", "Run an approved fixed replay recipe inside Docker Compose.", (READ, WRITE, TERMINAL), True, True),
    ),
    "privacy_data_governance": (
        EngineeringSkillAction("scan", "Inspect PII, consent, retention, deletion, export, and tenant-isolation evidence.", (READ,)),
        EngineeringSkillAction("retention_plan", "Create a data-classification and retention plan requiring human legal review.", (READ,)),
    ),
    "event_contract": (
        EngineeringSkillAction("analyze", "Validate AsyncAPI, message schemas, producers, consumers, retries, and compatibility.", (READ,)),
    ),
    "distributed_resilience": (
        EngineeringSkillAction("analyze", "Inspect timeouts, retries, idempotency, circuit breakers, concurrency, and degradation.", (READ,)),
        EngineeringSkillAction("fault_plan", "Create a non-executing fault-injection and recovery verification plan.", (READ,)),
    ),
    "synthetic_test_data": (
        EngineeringSkillAction("plan", "Design privacy-safe deterministic fixture coverage from a bounded schema.", (READ,)),
        EngineeringSkillAction("generate", "Generate deterministic synthetic JSON fixtures only inside the skill workspace.", (READ,)),
    ),
    "feature_flag_management": (
        EngineeringSkillAction("analyze", "Inventory feature flags, defaults, ownership, rollout, and stale-flag evidence.", (READ,)),
        EngineeringSkillAction("cleanup_plan", "Prepare a safe flag retirement and rollback plan without changing code.", (READ,)),
    ),
    "memory_profiling": (
        EngineeringSkillAction("inspect", "Inspect CPU, RAM, GPU, handle, connection, and leak-test evidence.", (READ,)),
        EngineeringSkillAction("run", "Run only an approved memory profiling test recipe inside Docker Compose.", (READ, WRITE, TERMINAL), True, True),
    ),
    "cloud_deployment": (
        EngineeringSkillAction("inspect", "Inspect provider manifests, identity, secret, region, cost, and rollback boundaries.", (READ,)),
        EngineeringSkillAction("plan", "Create a provider-neutral deployment plan without contacting or modifying cloud accounts.", (READ,)),
    ),
    "llm_prompt_regression": (
        EngineeringSkillAction("evaluate", "Evaluate bounded prompt cases against explicit expected output evidence without model loading.", (READ,)),
        EngineeringSkillAction("compare", "Compare prompt-suite result sets for quality, format, latency, and token regressions.", (READ,)),
    ),
    "accessibility_execution": (
        EngineeringSkillAction("inspect", "Inspect automated and manual accessibility execution readiness.", (READ,)),
        EngineeringSkillAction("run", "Run only an approved accessibility package script inside Docker Compose.", (READ, WRITE, TERMINAL), True, True),
    ),
    "repository_intelligence": (
        EngineeringSkillAction("scan", "Index AST symbols, routes, tests, and dependencies.", (READ,)),
        EngineeringSkillAction("impact", "Rank files and tests affected by target paths.", (READ,)),
    ),
    "sandbox_verification": (
        EngineeringSkillAction("detect", "Detect allowlisted build, lint, test, and E2E recipes.", (READ,)),
        EngineeringSkillAction(
            "run",
            "Execute only detected allowlisted verification recipes.",
            (READ, WRITE, TERMINAL),
            True,
        ),
    ),
    "failure_diagnostics": (
        EngineeringSkillAction("diagnose", "Compile AST-localized, cross-domain failure evidence.", (READ,)),
    ),
    "patch_workspace": (
        EngineeringSkillAction("inspect", "Validate a unified diff without applying it.", (READ,)),
        EngineeringSkillAction("apply", "Apply a validated patch through existing patch gates.", (READ, WRITE), True, True),
    ),
    "browser_e2e": (
        EngineeringSkillAction("detect", "Detect a local Playwright recipe and evidence paths.", (READ,)),
        EngineeringSkillAction(
            "run",
            "Run an allowlisted local Playwright package script.",
            (READ, WRITE, TERMINAL),
            True,
        ),
    ),
    "database_migration": (
        EngineeringSkillAction("inspect", "Inspect Alembic revisions, indexes, and tenant-scope signals.", (READ,)),
        EngineeringSkillAction("upgrade", "Run an approved Alembic upgrade in the project workspace.", (READ, WRITE, TERMINAL), True, True),
        EngineeringSkillAction("downgrade", "Run an approved Alembic downgrade in the project workspace.", (READ, WRITE, TERMINAL), True, True),
    ),
    "security_audit": (
        EngineeringSkillAction("scan", "Run deterministic source, secret, dependency, Docker, auth, RBAC, and API checks.", (READ,)),
    ),
    "container_operations": (
        EngineeringSkillAction(
            "config", "Validate Docker Compose configuration.", (READ, TERMINAL), True
        ),
        EngineeringSkillAction(
            "status", "Read Compose service status.", (READ, TERMINAL), True
        ),
        EngineeringSkillAction(
            "logs", "Read bounded Compose logs.", (READ, TERMINAL), True
        ),
        EngineeringSkillAction("up", "Start an approved isolated Compose project.", (READ, WRITE, TERMINAL), True, True),
        EngineeringSkillAction("down", "Stop an approved isolated Compose project.", (READ, WRITE, TERMINAL), True, True),
        EngineeringSkillAction("cleanup", "Remove approved project containers and orphans.", (READ, WRITE, TERMINAL), True, True),
    ),
    "api_contract": (
        EngineeringSkillAction("analyze", "Compare OpenAPI, backend routes, frontend calls, and webhook contracts.", (READ,)),
    ),
    "release_packaging": (
        EngineeringSkillAction("prepare", "Create a local SBOM, hashes, release archive, and rollback manifest.", (READ, WRITE)),
        EngineeringSkillAction("verify", "Verify a prepared package and installer evidence.", (READ,)),
        EngineeringSkillAction("smoke_installer", "Run the approved installer verification recipe.", (READ, WRITE, TERMINAL), True, True),
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
