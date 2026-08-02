"""Deterministic read-only analyses for precision engineering skills."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from agentic_network.skills.external_runner_evidence import validate_external_runner_evidence
from agentic_network.skills.supreme_runtime import _signal_report, _write_json


PRECISION_SKILLS = frozenset(
    {
        "agent_tool_contract_verification",
        "assistive_technology_lab",
        "binary_hardening_verification",
        "data_residency_mapping",
        "identity_protocol_conformance",
        "messaging_deliverability",
        "offline_sync_conflict_verification",
        "search_relevance_evaluation",
        "temporal_monetary_correctness",
        "web_protocol_conformance",
    }
)


def execute_precision_action(
    skill_name: str,
    action: str,
    payload: dict[str, Any],
    workspace: Path,
    project_root: Path,
) -> dict[str, Any]:
    """Produce bounded project evidence without executing or modifying the project."""

    handlers: dict[str, Callable[[str, dict[str, Any], Path], dict[str, Any]]] = {
        "identity_protocol_conformance": _identity_protocol,
        "temporal_monetary_correctness": _temporal_monetary,
        "offline_sync_conflict_verification": _offline_sync,
        "binary_hardening_verification": _binary_hardening,
        "web_protocol_conformance": _web_protocol,
        "search_relevance_evaluation": _search_relevance,
        "agent_tool_contract_verification": _agent_tool_contract,
        "messaging_deliverability": _messaging_deliverability,
        "data_residency_mapping": _data_residency,
        "assistive_technology_lab": _assistive_technology,
    }
    if skill_name not in PRECISION_SKILLS:
        raise ValueError("unsupported_precision_skill")
    data = handlers[skill_name](action, payload, project_root)
    ready = bool(data.pop("ready", False))
    summary = str(data.pop("summary", f"{skill_name}.{action} evidence generated."))
    data.update(
        {
            "action": action,
            "project_modified": False,
            "terminal_executed": False,
            "network_used": False,
            "raw_command_accepted": False,
            "bounded": True,
        }
    )
    artifact = _write_json(workspace / f"{skill_name}_{action}.json", data, workspace)
    return {
        "status": "SUCCESS" if ready else "PARTIAL",
        "summary": summary,
        "data": data,
        "artifacts": [str(artifact)],
        "terminal_used": False,
        "internet_used": False,
        "dependency_install_used": False,
    }


def _coverage(
    root: Path,
    profile: dict[str, tuple[str, ...]],
    *,
    action: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    signals = _signal_report(root, profile)
    covered = sum(bool(paths) for paths in signals.values())
    total = len(signals)
    result: dict[str, Any] = {
        "controls": signals,
        "covered_controls": covered,
        "required_controls": total,
        "execution_available": action == "run",
        "ready": total > 0 and covered == total,
        "summary": f"Implementation evidence covered {covered}/{total} control domains.",
    }
    result.update(extra or {})
    return result


def _identity_protocol(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    return _coverage(
        root,
        {
            "oauth_oidc": ("oauth", "openid", "oidc", "authorization_code"),
            "request_binding": ("pkce", "code_verifier", "state", "nonce"),
            "token_validation": ("issuer", "audience", "jwks", "token rotation"),
            "enterprise_identity": ("saml", "scim", "identity provider"),
            "session_lifecycle": ("session cookie", "same_site", "logout", "revoke"),
        },
        action=action,
    )


def _temporal_monetary(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    return _coverage(
        root,
        {
            "timezone": ("timezone", "zoneinfo", "utc", "offset-aware"),
            "dst_boundaries": ("daylight saving", "dst", "fold", "ambiguous time"),
            "money_representation": ("decimal", "minor unit", "currency_code", "money"),
            "rounding": ("rounding", "round_half", "quantize"),
            "tax_and_fx": ("tax rate", "vat", "exchange rate", "fx rate"),
        },
        action=action,
    )


def _offline_sync(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    return _coverage(
        root,
        {
            "offline_queue": ("offline queue", "pending mutation", "sync queue"),
            "versioning": ("version vector", "vector clock", "etag", "row_version"),
            "conflicts": ("conflict resolution", "last write wins", "merge conflict"),
            "deletions": ("tombstone", "soft delete", "deleted_at"),
            "idempotency": ("idempotency", "dedup", "operation_id"),
        },
        action=action,
    )


def _binary_hardening(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    attestation = validate_external_runner_evidence(payload.get("evidence"), "windows_binary")
    result = _coverage(
        root,
        {
            "integrity": ("sha256", "checksum", "manifest hash"),
            "signing": ("authenticode", "signtool", "code signing"),
            "supply_chain": ("sbom", "cyclonedx", "provenance"),
            "rollback": ("rollback", "uninstall", "backup"),
            "mitigations": ("aslr", "dep", "control flow guard", "cfg"),
        },
        action=action,
        extra={
            "external_evidence": attestation,
            "host_binary_executed": False,
            "external_runner_required": True,
        },
    )
    if action == "verify":
        result["ready"] = bool(result["ready"] and attestation["valid"])
    return result


def _web_protocol(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    return _coverage(
        root,
        {
            "cache_semantics": ("cache-control", "etag", "if-none-match", "vary"),
            "cors": ("access-control-allow-origin", "cors", "preflight"),
            "compression": ("gzip", "brotli", "content-encoding"),
            "streaming": ("server-sent events", "eventsource", "websocket", "streamingresponse"),
            "resilience": ("retry-after", "backoff", "idempotency-key", "timeout"),
        },
        action=action,
    )


def _search_relevance(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    supplied_metrics = {
        name: metrics.get(name)
        for name in ("mrr", "ndcg", "precision_at_k", "recall_at_k")
        if isinstance(metrics.get(name), (int, float))
    }
    return _coverage(
        root,
        {
            "ranking": ("rank", "bm25", "relevance", "score"),
            "analysis": ("tokenizer", "stemming", "synonym", "analyzer"),
            "filtering": ("facet", "filter", "tenant_id", "permission"),
            "golden_queries": ("golden quer", "relevance case", "expected_results"),
            "metrics": ("ndcg", "precision@", "recall@", "mean reciprocal rank"),
        },
        action=action,
        extra={"supplied_metrics": supplied_metrics, "metrics_are_advisory": True},
    )


def _agent_tool_contract(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    return _coverage(
        root,
        {
            "input_schema": ("input_schema", "json schema", "tool schema"),
            "approval": ("approval_required", "approval center", "human approval"),
            "timeouts": ("timeout_seconds", "deadline", "cancel"),
            "idempotency": ("idempotency", "request_id", "dedup"),
            "result_validation": ("output schema", "validate result", "tool error"),
        },
        action=action,
    )


def _messaging_deliverability(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    return _coverage(
        root,
        {
            "domain_authentication": ("spf", "dkim", "dmarc"),
            "bounce_handling": ("bounce", "complaint", "suppression list"),
            "delivery_retries": ("delivery retry", "exponential backoff", "dead letter"),
            "consent": ("unsubscribe", "opt out", "notification preference"),
            "webhooks": ("delivery webhook", "message delivered", "provider event"),
        },
        action=action,
    )


def _data_residency(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    attestation = validate_external_runner_evidence(payload.get("evidence"), "data_residency")
    result = _coverage(
        root,
        {
            "regions": ("data region", "residency", "region allowlist"),
            "storage": ("storage location", "database region", "bucket region"),
            "backups": ("backup region", "replication", "disaster recovery region"),
            "transfers": ("cross-border", "data transfer", "subprocessor"),
            "retention": ("retention", "delete", "purge"),
        },
        action=action,
        extra={
            "external_evidence": attestation,
            "legal_review_required": True,
            "compliance_guaranteed": False,
        },
    )
    if action == "verify":
        result["ready"] = bool(result["ready"] and attestation["valid"])
    return result


def _assistive_technology(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    attestation = validate_external_runner_evidence(
        payload.get("evidence"), "assistive_technology"
    )
    result = _coverage(
        root,
        {
            "semantics": ("accessible name", "aria-label", "semantic role"),
            "keyboard": ("keyboard navigation", "tabindex", "shortcut"),
            "focus": ("focus visible", "focus trap", "setfocus"),
            "contrast": ("high contrast", "forced-colors", "contrast ratio"),
            "screen_reader": ("nvda", "narrator", "voiceover", "talkback"),
        },
        action=action,
        extra={
            "external_evidence": attestation,
            "host_ui_automation_executed": False,
            "manual_accessibility_review_required": True,
        },
    )
    if action == "verify":
        result["ready"] = bool(result["ready"] and attestation["valid"])
    return result
