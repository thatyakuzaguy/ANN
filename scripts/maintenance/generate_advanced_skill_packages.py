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
}


def main() -> None:
    for name, description in ADVANCED_SKILLS.items():
        actions = ENGINEERING_SKILL_ACTIONS[name]
        permissions = {
            item.value: "DENY"
            for item in SkillPermission
        }
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
        *[
            f"  {permission}: {decision}"
            for permission, decision in permissions.items()
        ],
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
