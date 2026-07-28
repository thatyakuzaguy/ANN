"""Public Skill Runtime API for ANN skills."""

from __future__ import annotations

from typing import Any

from agentic_network.skills.audit import SkillAuditLogger
from agentic_network.skills.executor import ApprovalValidator, SkillExecutionResult, SkillExecutor
from agentic_network.skills.permission_store import SkillPermissionStore
from agentic_network.skills.registry import SkillRegistry


def execute_skill(
    skill_name: str,
    action: str,
    payload: dict[str, Any] | None = None,
    *,
    registry: SkillRegistry | None = None,
    store: SkillPermissionStore | None = None,
    audit_logger: SkillAuditLogger | None = None,
    approval_validator: ApprovalValidator | None = None,
) -> SkillExecutionResult:
    """Execute a local skill action through the ANN sandbox."""

    return SkillExecutor(
        registry=registry,
        store=store,
        audit_logger=audit_logger,
        approval_validator=approval_validator,
    ).execute_skill(
        skill_name,
        action,
        payload,
    )
