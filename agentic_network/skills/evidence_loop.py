"""Deterministic skill selection and evidence interpretation for repair loops.

This module never executes a skill, command, patch, or approval. It produces a
reviewable plan and interprets already-gated skill results.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from agentic_network.skills.engineering import get_engineering_action


SELECTION_RULES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("language_server_intelligence", "inspect", "typed diagnostic evidence", ("pyright", "typescript", "tsc", "type error", "mypy")),
    ("identity_protocol_conformance", "inspect", "identity protocol boundary", ("oauth", "oidc", "saml", "scim", "jwt", "login", "auth")),
    ("temporal_monetary_correctness", "inspect", "temporal or monetary invariant", ("timezone", "dst", "currency", "decimal", "rounding", "money", "tax")),
    ("offline_sync_conflict_verification", "inspect", "offline synchronization conflict", ("offline", "sync conflict", "tombstone", "vector clock")),
    ("web_protocol_conformance", "inspect", "web protocol boundary", ("cors", "cache-control", "etag", "websocket", "sse", "http")),
    ("search_relevance_evaluation", "analyze", "search ranking or relevance", ("search", "ranking", "relevance", "bm25", "ndcg")),
    ("agent_tool_contract_verification", "inspect", "agent tool contract", ("tool call", "tool schema", "function calling", "approval_required")),
    ("messaging_deliverability", "inspect", "messaging delivery boundary", ("email", "smtp", "dkim", "dmarc", "bounce", "notification")),
    ("data_residency_mapping", "analyze", "regional data boundary", ("residency", "region", "cross-border", "subprocessor")),
    ("assistive_technology_lab", "inspect", "assistive technology boundary", ("screen reader", "nvda", "narrator", "voiceover", "talkback", "accessibility")),
    ("binary_hardening_verification", "inspect", "binary or installer boundary", ("installer", "binary", "authenticode", "signtool", "executable")),
    ("database_migration", "inspect", "database migration boundary", ("alembic", "migration", "database", "sql", "column", "table")),
    ("container_operations", "config", "container topology boundary", ("docker", "compose", "container", "port", "redis")),
    ("api_contract", "analyze", "API contract boundary", ("openapi", "api contract", "webhook", "endpoint")),
)
DEFAULT_SELECTIONS = (
    ("failure_diagnostics", "diagnose", "cross-domain root cause isolation"),
    ("test_quality", "analyze", "failed-test validity and expectation review"),
    ("repository_intelligence", "scan", "repository impact and dependency context"),
)


def select_skills_for_context(context: dict[str, Any], max_skills: int = 5) -> list[dict[str, Any]]:
    """Select a stable, bounded skill set from failure facts."""

    text = _context_text(context)
    selected: list[dict[str, Any]] = []
    for skill, action, reason, terms in SELECTION_RULES:
        matches = sorted({term for term in terms if term in text})
        if matches:
            selected.append(_selection(skill, action, reason, matches))
    for skill, action, reason in DEFAULT_SELECTIONS:
        selected.append(_selection(skill, action, reason, []))
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in selected:
        if item["skill"] in seen:
            continue
        seen.add(item["skill"])
        deduped.append(item)
        if len(deduped) >= max(1, min(max_skills, 10)):
            break
    return deduped


def build_skill_evidence_plan(
    context: dict[str, Any],
    *,
    max_skills: int = 5,
) -> dict[str, Any]:
    """Create a no-side-effect plan that preserves all existing gates."""

    selections = select_skills_for_context(context, max_skills=max_skills)
    approvals = [item["skill"] for item in selections if item["approval_required"]]
    return {
        "status": "APPROVAL_REQUIRED" if approvals else "ANALYSIS_READY",
        "selected_skills": selections,
        "approval_required_for": approvals,
        "execution_policy": "existing_skill_executor_only",
        "raw_command_allowed": False,
        "automatic_execution": False,
        "automatic_patch_apply": False,
        "result_drop_directory": "skill_evidence_results",
        "next_action": "request_skill_approval" if approvals else "collect_skill_evidence",
        "context_fingerprint": _fingerprint(text=_context_text(context)),
    }


def load_skill_results(run_dir: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Load bounded, already-produced skill results from one fixed run directory."""

    expected = {
        str(item.get("skill"))
        for item in plan.get("selected_skills", [])
        if isinstance(item, dict)
    }
    result_dir = run_dir.resolve() / "skill_evidence_results"
    if not result_dir.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for path in sorted(result_dir.glob("*.json"))[:20]:
        resolved = path.resolve()
        try:
            resolved.relative_to(result_dir)
        except ValueError:
            continue
        if path.is_symlink() or not resolved.is_file() or resolved.stat().st_size > 1_000_000:
            continue
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        skill = str(payload.get("skill") or "")
        if skill not in expected:
            continue
        results.append(
            {
                "skill": skill,
                "status": str(payload.get("status") or "UNKNOWN").upper(),
                "summary": str(payload.get("summary") or "")[:1000],
                "source_file": path.name,
                "approval_evidence_present": bool(payload.get("approval_evidence_present")),
            }
        )
    return results


def interpret_skill_results(
    plan: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Interpret completed skill results without treating absence as success."""

    expected = {
        str(item.get("skill"))
        for item in plan.get("selected_skills", [])
        if isinstance(item, dict)
    }
    supplied = {
        str(item.get("skill")): item for item in results if isinstance(item, dict) and item.get("skill")
    }
    approval_required = {
        str(item.get("skill"))
        for item in plan.get("selected_skills", [])
        if isinstance(item, dict) and item.get("approval_required")
    }
    missing = sorted(expected - supplied.keys())
    statuses = {
        name: str(item.get("status") or "UNKNOWN").upper() for name, item in supplied.items()
    }
    for name in approval_required:
        if name in supplied and not supplied[name].get("approval_evidence_present"):
            statuses[name] = "BLOCKED"
    blocked = sorted(name for name, status in statuses.items() if status in {"BLOCKED", "DENIED"})
    failed = sorted(name for name, status in statuses.items() if status in {"FAILED", "ERROR", "PARTIAL"})
    if not results or missing:
        status = "EVIDENCE_REQUIRED"
        next_action = "collect_approved_skill_evidence"
    elif blocked:
        status = "APPROVAL_REQUIRED"
        next_action = "resolve_skill_approvals"
    elif failed:
        status = "REMEDIATION_REQUIRED"
        next_action = "compile_targeted_fix_context"
    elif statuses and all(value == "SUCCESS" for value in statuses.values()):
        status = "VERIFIED"
        next_action = "continue_existing_correction_gate"
    else:
        status = "HUMAN_REVIEW_REQUIRED"
        next_action = "review_ambiguous_skill_evidence"
    return {
        "status": status,
        "next_action": next_action,
        "expected_skills": sorted(expected),
        "result_statuses": statuses,
        "missing_skills": missing,
        "blocked_skills": blocked,
        "failed_or_partial_skills": failed,
        "patch_apply_allowed": False,
        "human_approval_bypassed": False,
    }


def write_skill_evidence_loop_artifacts(
    run_dir: Path,
    attempt: int,
    plan: dict[str, Any],
    decision: dict[str, Any],
) -> list[str]:
    """Persist a plan and decision beside one autonomous-loop attempt."""

    resolved = run_dir.resolve()
    if not resolved.is_dir() or attempt <= 0:
        raise ValueError("invalid_skill_evidence_run")
    plan_json = resolved / f"38_skill_evidence_plan_attempt_{attempt:03d}.json"
    plan_md = resolved / f"38_skill_evidence_plan_attempt_{attempt:03d}.md"
    decision_json = resolved / f"39_skill_evidence_decision_attempt_{attempt:03d}.json"
    decision_md = resolved / f"39_skill_evidence_decision_attempt_{attempt:03d}.md"
    plan_json.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    decision_json.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    plan_md.write_text(_plan_markdown(plan), encoding="utf-8")
    decision_md.write_text(_decision_markdown(decision), encoding="utf-8")
    return [str(plan_json), str(plan_md), str(decision_json), str(decision_md)]


def _selection(skill: str, action: str, reason: str, matches: list[str]) -> dict[str, Any]:
    spec = get_engineering_action(skill, action)
    if spec is None:
        raise ValueError(f"unregistered_skill_action:{skill}.{action}")
    return {
        "skill": skill,
        "action": action,
        "reason": reason,
        "matched_terms": matches,
        "permissions": list(spec.permissions),
        "approval_required": spec.approval_required,
        "mutates_project": spec.mutates_project,
    }


def _context_text(context: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("stdout", "stderr", "test_report", "failure_reason", "user_request"):
        values.append(str(context.get(key) or ""))
    for key in ("commands", "affected_files"):
        value = context.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value[:200])
    return re.sub(r"\s+", " ", " ".join(values)).lower()[:200_000]


def _fingerprint(*, text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Skill Evidence Plan",
        "",
        f"Status: {plan.get('status', 'UNKNOWN')}",
        f"Next action: {plan.get('next_action', '')}",
        "",
        "## Selected Skills",
    ]
    for item in plan.get("selected_skills", []):
        lines.append(f"- {item['skill']}.{item['action']}: {item['reason']}")
    lines.extend(
        [
            "",
            "No skill, command, patch, or approval was executed while creating this plan.",
            "",
        ]
    )
    return "\n".join(lines)


def _decision_markdown(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Skill Evidence Decision",
            "",
            f"Status: {decision.get('status', 'UNKNOWN')}",
            f"Next action: {decision.get('next_action', '')}",
            f"Missing skills: {decision.get('missing_skills', [])}",
            f"Failed or partial skills: {decision.get('failed_or_partial_skills', [])}",
            "",
            "Patch application remains subject to the existing Approval Center and patch gates.",
            "",
        ]
    )
