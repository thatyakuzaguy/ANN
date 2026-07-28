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
