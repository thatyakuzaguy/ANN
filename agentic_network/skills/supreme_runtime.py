"""Deterministic specialist analyses for ANN's supreme engineering skill wave.

The module is deliberately read-only with respect to project repositories.
Executable verification remains in ``engineering_runtime`` so it must pass the
existing permission, approval, path, and Docker Compose gates.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Callable

from agentic_network.skills.sandbox import validate_workspace_path


SUPREME_SKILLS = frozenset(
    {
        "agent_trajectory_forensics",
        "ai_governance_evidence",
        "api_abuse_simulation",
        "asset_provenance",
        "behavioral_acceptance_oracle",
        "cross_language_semantic_graph",
        "delegation_optimizer",
        "domain_invariant_mining",
        "dynamic_authorization_verification",
        "flaky_test_investigator",
        "installer_vm_lab",
        "local_resource_guardian",
        "long_horizon_checkpoint_integrity",
        "model_runtime_certification",
        "online_migration_rehearsal",
        "performance_regression_bisect",
        "project_archetype_synthesis",
        "secure_update_delivery",
    }
)
EXCLUDED = {
    ".git",
    ".next",
    ".venv",
    "adapters",
    "datasets",
    "dist",
    "knowledge",
    "memory",
    "models",
    "node_modules",
    "outputs",
    "training",
    "unsloth_compiled_cache",
    "venv",
}
TEXT_SUFFIXES = {
    ".cs",
    ".go",
    ".java",
    ".js",
    ".json",
    ".md",
    ".py",
    ".rs",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
ASSET_SUFFIXES = {
    ".avif",
    ".eot",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".mp4",
    ".ogg",
    ".otf",
    ".png",
    ".svg",
    ".ttf",
    ".wav",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
}
MAX_FILES = 5_000
MAX_FILE_BYTES = 500_000
MAX_ITEMS = 500


def execute_supreme_action(
    skill_name: str,
    action: str,
    payload: dict[str, Any],
    workspace: Path,
    project_root: Path,
) -> dict[str, Any]:
    """Execute one bounded, deterministic supreme-skill analysis."""

    handlers: dict[str, Callable[[str, dict[str, Any], Path], dict[str, Any]]] = {
        "project_archetype_synthesis": _project_archetype,
        "behavioral_acceptance_oracle": _behavioral_oracle,
        "dynamic_authorization_verification": _authorization,
        "long_horizon_checkpoint_integrity": _checkpoint_integrity,
        "agent_trajectory_forensics": _trajectory_forensics,
        "delegation_optimizer": _delegation,
        "cross_language_semantic_graph": _semantic_graph,
        "flaky_test_investigator": _flaky_tests,
        "online_migration_rehearsal": _migration_rehearsal,
        "local_resource_guardian": _resource_guardian,
        "secure_update_delivery": _secure_updates,
        "installer_vm_lab": _installer_lab,
        "model_runtime_certification": _model_runtime,
        "api_abuse_simulation": _api_abuse,
        "performance_regression_bisect": _performance_bisect,
        "asset_provenance": _asset_provenance,
        "domain_invariant_mining": _domain_invariants,
        "ai_governance_evidence": _ai_governance,
    }
    if skill_name not in SUPREME_SKILLS:
        raise ValueError("unsupported_supreme_skill")
    data = handlers[skill_name](action, payload, project_root)
    data.setdefault("action", action)
    data.setdefault("project_modified", False)
    data.setdefault("terminal_executed", False)
    data.setdefault("network_used", False)
    data.setdefault("bounded", True)
    ready = bool(data.pop("ready", False))
    filename = f"{skill_name}_{action}.json"
    path = _write_json(workspace / filename, data, workspace)
    return {
        "status": "SUCCESS" if ready else "PARTIAL",
        "summary": str(data.pop("summary", f"{skill_name}.{action} evidence generated.")),
        "data": data,
        "artifacts": [str(path)],
        "terminal_used": False,
        "internet_used": False,
        "dependency_install_used": False,
    }


def _project_archetype(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    corpus = _corpus(root, extra=_text(payload.get("request"), 20_000))
    archetypes = {
        "api_service": ("fastapi", "openapi", "router", "endpoint"),
        "saas_web": ("tenant", "billing", "subscription", "react", "next.js"),
        "game": ("three.js", "unity", "godot", "game loop", "score"),
        "desktop": ("pyside", "qtwidgets", "tauri", "electron", "desktop"),
        "cli": ("argparse", "typer", "click.command", "command line"),
        "data_ml": ("pandas", "dataset", "pipeline", "model evaluation"),
        "infrastructure": ("terraform", "kubernetes", "helm", "docker compose"),
        "library": ("public api", "package", "sdk", "library"),
    }
    scores = {
        name: sum(corpus.count(marker) for marker in markers)
        for name, markers in archetypes.items()
    }
    ranked = sorted(scores, key=lambda name: (-scores[name], name))
    primary = ranked[0] if ranked and scores[ranked[0]] else "unknown"
    blueprint = {
        "primary_archetype": primary,
        "secondary_archetypes": [name for name in ranked[1:4] if scores[name]],
        "layers": _archetype_layers(primary),
        "required_gates": [
            "requirements_contract",
            "architecture_fitness",
            "sandbox_verification",
            "security_audit",
            "release_packaging",
        ],
    }
    return {
        "scores": scores,
        "classification": blueprint,
        "blueprint_generated": action == "synthesize",
        "ready": primary != "unknown",
        "summary": f"Classified repository as {primary} from deterministic evidence.",
    }


def _behavioral_oracle(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    requirements = _objects(payload.get("requirements"))
    if not requirements:
        requirements = [
            {"id": path.stem, "statement": line.strip("# -")}
            for path in _files(root, {".md"})[:30]
            for line in _read(path).splitlines()
            if "shall" in line.lower() or "must" in line.lower()
        ][:MAX_ITEMS]
    tests = [path.relative_to(root).as_posix() for path in _files(root, TEXT_SUFFIXES) if _is_test(path)]
    checks = []
    for index, item in enumerate(requirements[:MAX_ITEMS], 1):
        statement = _text(item.get("statement") or item.get("requirement"), 2_000)
        identifier = _text(item.get("id"), 100) or f"REQ-{index:03d}"
        terms = _terms(statement)
        matched = [path for path in tests if any(term in path.lower() for term in terms)]
        checks.append(
            {
                "id": identifier,
                "behavior": statement,
                "observable_outcome": _text(item.get("expected"), 1_000) or statement,
                "test_evidence": matched[:20],
                "covered": bool(matched),
            }
        )
    return {
        "checks": checks,
        "uncovered": [item["id"] for item in checks if not item["covered"]],
        "execution_available": action == "run",
        "ready": bool(checks) and all(item["covered"] for item in checks),
        "summary": f"Mapped {len(checks)} behavioral contracts to {len(tests)} test files.",
    }


def _authorization(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    routes: list[dict[str, Any]] = []
    route_pattern = re.compile(r"(?i)(?:@\w+\.(get|post|put|patch|delete)|route\s*\()[^\n]{0,200}")
    controls = re.compile(r"(?i)rbac|permission|authorize|current_user|tenant_id|organization_id|scope")
    for path in _files(root, {".py", ".ts", ".tsx", ".js", ".java", ".cs"}):
        text = _read(path)
        for match in route_pattern.finditer(text):
            nearby = text[max(0, match.start() - 500) : match.end() + 800]
            routes.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "route_excerpt": match.group(0)[:240],
                    "auth_control": bool(controls.search(nearby)),
                    "tenant_scope": "tenant" in nearby.lower() or "organization" in nearby.lower(),
                }
            )
            if len(routes) >= MAX_ITEMS:
                break
    gaps = [item for item in routes if not item["auth_control"]]
    return {
        "routes": routes,
        "authorization_gaps": gaps,
        "execution_available": action == "run",
        "ready": bool(routes) and not gaps,
        "summary": f"Inspected {len(routes)} route declarations; {len(gaps)} lack nearby access controls.",
    }


def _checkpoint_integrity(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    groups = {
        "checkpoint": ("checkpoint", "resume", "snapshot"),
        "idempotency": ("idempotency", "dedup", "request_id"),
        "approval": ("approval", "token", "human review"),
        "replay_guard": ("attempt", "max_attempts", "failed_permanently"),
        "atomic_write": ("atomic", "replace(", "transaction"),
    }
    signals = _signal_report(root, groups)
    missing = [name for name, values in signals.items() if not values]
    return {
        "signals": signals,
        "missing_controls": missing,
        "execution_available": action == "run",
        "ready": not missing,
        "summary": f"Checkpoint integrity covered {len(groups) - len(missing)}/{len(groups)} controls.",
    }


def _trajectory_forensics(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del root
    trajectories = _objects(payload.get("trajectories"))
    if action == "compare":
        trajectories = [
            item
            for item in (payload.get("baseline"), payload.get("candidate"))
            if isinstance(item, dict)
        ]
    summaries = []
    for index, trajectory in enumerate(trajectories[:200], 1):
        events = _objects(trajectory.get("events"))
        statuses = Counter(_text(event.get("status"), 80) for event in events)
        summaries.append(
            {
                "id": _text(trajectory.get("id"), 100) or f"trajectory-{index}",
                "event_count": len(events),
                "tool_calls": sum(bool(event.get("tool")) for event in events),
                "evidence_links": sum(bool(event.get("evidence")) for event in events),
                "retries": sum("retry" in _text(event.get("type"), 80).lower() for event in events),
                "status_counts": dict(statuses),
                "terminal_status": _text(trajectory.get("status"), 80),
            }
        )
    return {
        "trajectories": summaries,
        "raw_prompts_preserved": False,
        "secret_values_preserved": False,
        "ready": bool(summaries),
        "summary": f"Compiled {len(summaries)} redacted trajectory summaries.",
    }


def _delegation(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del root
    assignments = _objects(payload.get("assignments"))
    owners: Counter[str] = Counter()
    objectives: Counter[str] = Counter()
    gaps: list[dict[str, str]] = []
    for item in assignments[:MAX_ITEMS]:
        owner = _text(item.get("owner"), 100)
        objective = " ".join(_text(item.get("objective"), 500).lower().split())
        owners[owner or "UNASSIGNED"] += 1
        objectives[objective or "UNSPECIFIED"] += 1
        if not owner or not item.get("acceptance_criteria"):
            gaps.append({"owner": owner, "objective": objective[:200]})
    duplicates = [name for name, count in objectives.items() if name not in {"UNSPECIFIED"} and count > 1]
    return {
        "assignment_count": len(assignments),
        "owner_load": dict(owners),
        "duplicate_objectives": duplicates,
        "ownership_gaps": gaps,
        "plan_generated": action == "plan",
        "recommendation": "merge_duplicates_then_balance_owner_load" if duplicates else "preserve_scope",
        "ready": bool(assignments) and not duplicates and not gaps,
        "summary": f"Evaluated {len(assignments)} assignments with {len(duplicates)} duplicates.",
    }


def _semantic_graph(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    files = _files(root, {".cs", ".go", ".java", ".js", ".py", ".rs", ".ts", ".tsx"})
    symbol_re = re.compile(
        r"(?m)^\s*(?:export\s+)?(?:async\s+)?(?:def|class|function|interface|type|struct|enum|func|public\s+class)\s+([A-Za-z_][\w]*)"
    )
    import_re = re.compile(r"(?m)^\s*(?:from|import|use|require\(|using|package)\s+([^\n;]+)")
    nodes: list[dict[str, Any]] = []
    for path in files:
        text = _read(path)
        nodes.append(
            {
                "path": path.relative_to(root).as_posix(),
                "language": path.suffix.lower().lstrip("."),
                "symbols": symbol_re.findall(text)[:100],
                "imports": [item.strip(" '\"()")[:300] for item in import_re.findall(text)[:100]],
            }
        )
    targets = {_text(item, 300).replace("\\", "/").lower() for item in _list(payload.get("targets"))}
    impacted = [
        node
        for node in nodes
        if any(target and (target in node["path"].lower() or any(target in value.lower() for value in node["imports"])) for target in targets)
    ]
    return {
        "nodes": nodes[:MAX_ITEMS],
        "language_counts": dict(Counter(node["language"] for node in nodes)),
        "impacted": impacted[:MAX_ITEMS] if action == "impact" else [],
        "ready": bool(nodes),
        "summary": f"Indexed {len(nodes)} source files across {len({node['language'] for node in nodes})} languages.",
    }


def _flaky_tests(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del root
    runs = _objects(payload.get("runs"))
    outcomes: defaultdict[str, list[str]] = defaultdict(list)
    durations: defaultdict[str, list[float]] = defaultdict(list)
    for run in runs[:2_000]:
        name = _text(run.get("test"), 300) or "unknown"
        outcomes[name].append(_text(run.get("status"), 50).upper())
        durations[name].append(_number(run.get("duration_seconds")))
    suspects = []
    for name, values in outcomes.items():
        unique = set(values)
        timings = durations[name]
        variance = round(max(timings) - min(timings), 4) if timings else 0.0
        if len(unique) > 1 or variance > _number(payload.get("duration_variance_threshold", 2.0)):
            suspects.append({"test": name, "outcomes": dict(Counter(values)), "duration_range": variance})
    return {
        "suspects": suspects,
        "run_count": len(runs),
        "execution_available": action == "run",
        "ready": bool(runs) and not suspects,
        "summary": f"Analyzed {len(runs)} outcomes and identified {len(suspects)} flaky-test candidates.",
    }


def _migration_rehearsal(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    groups = {
        "expand_contract": ("expand", "contract phase", "compatible"),
        "backfill": ("backfill", "batch", "checkpoint"),
        "locking": ("lock_timeout", "concurrently", "online"),
        "rollback": ("downgrade", "rollback"),
        "tenant_integrity": ("tenant_id", "organization_id", "row level security"),
    }
    signals = _signal_report(root, groups, suffixes={".py", ".sql", ".md", ".yaml", ".yml"})
    missing = [name for name, values in signals.items() if not values]
    return {
        "signals": signals,
        "missing_evidence": missing,
        "execution_available": action == "run",
        "ready": not missing,
        "summary": f"Online migration rehearsal covered {len(groups) - len(missing)}/{len(groups)} controls.",
    }


def _resource_guardian(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    files = _files(root, None)
    total = sum(_safe_size(path) for path in files)
    disk = shutil.disk_usage(root)
    quota = max(1, int(_number(payload.get("quota_bytes", 20 * 1024**3))))
    return {
        "project_file_count": len(files),
        "project_bytes": total,
        "quota_bytes": quota,
        "quota_usage_percent": round(total * 100 / quota, 2),
        "disk_total_bytes": disk.total,
        "disk_free_bytes": disk.free,
        "cleanup_scope": "isolated_compose_project_only" if action == "cleanup" else "none",
        "host_files_deleted": False,
        "ready": total <= quota and disk.free >= min(5 * 1024**3, disk.total // 20),
        "summary": f"Project uses {total} bytes across {len(files)} bounded files.",
    }


def _secure_updates(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del root
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    required = {"root", "timestamp", "snapshot", "targets"}
    present = {name for name in required if isinstance(metadata.get(name), dict)}
    checks = {
        "roles_present": present == required,
        "signatures_present": all(bool(metadata.get(name, {}).get("signatures")) for name in present),
        "hashes_present": bool(metadata.get("targets", {}).get("hashes")),
        "version_monotonic": bool(metadata.get("version_monotonic")),
        "not_expired": bool(metadata.get("not_expired")),
        "rollback_protected": bool(metadata.get("rollback_protected")),
    }
    return {
        "checks": checks,
        "download_performed": False,
        "install_performed": False,
        "verification_only": action == "verify",
        "ready": all(checks.values()),
        "summary": f"Secure update metadata passed {sum(checks.values())}/{len(checks)} checks.",
    }


def _installer_lab(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del root
    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {}
    required = (
        "clean_vm",
        "installer_hash_verified",
        "install_passed",
        "first_launch_passed",
        "upgrade_passed",
        "uninstall_passed",
        "rollback_passed",
        "residue_checked",
    )
    checks = {name: evidence.get(name) is True for name in required}
    return {
        "checks": checks,
        "execution_available": action == "run",
        "host_installer_executed": False,
        "ready": all(checks.values()),
        "summary": f"Installer VM evidence passed {sum(checks.values())}/{len(checks)} gates.",
    }


def _model_runtime(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del root
    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {}
    required = (
        "manifest_verified",
        "backend_available",
        "device_verified",
        "load_passed",
        "inference_passed",
        "unload_passed",
        "active_models_zero_after",
        "parallel_loads_zero",
        "rollback_passed",
    )
    checks = {name: evidence.get(name) is True for name in required}
    return {
        "checks": checks,
        "benchmark_requested": action == "benchmark",
        "model_modified": False,
        "training_used": False,
        "ready": all(checks.values()),
        "summary": f"Model runtime certification passed {sum(checks.values())}/{len(checks)} gates.",
    }


def _api_abuse(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    route_count = sum(
        len(re.findall(r"(?i)@\w+\.(?:get|post|put|patch|delete)|\broute\s*\(", _read(path)))
        for path in _files(root, {".py", ".ts", ".tsx", ".js"})
    )
    scenarios = [
        {"id": "AUTHZ-OBJECT", "control": "object-level authorization", "destructive": False},
        {"id": "AUTHZ-FUNCTION", "control": "function-level authorization", "destructive": False},
        {"id": "RATE-LIMIT", "control": "bounded request rate", "destructive": False},
        {"id": "REPLAY", "control": "nonce or idempotency guard", "destructive": False},
        {"id": "INPUT", "control": "schema and size validation", "destructive": False},
        {"id": "RESOURCE", "control": "pagination and resource caps", "destructive": False},
    ]
    return {
        "route_count": route_count,
        "scenarios": scenarios,
        "execution_available": action == "run",
        "production_target_allowed": False,
        "ready": route_count > 0,
        "summary": f"Prepared {len(scenarios)} non-destructive abuse scenarios for {route_count} routes.",
    }


def _performance_bisect(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del root
    revisions = _objects(payload.get("revisions"))
    metric = _text(payload.get("metric"), 100) or "latency_ms"
    threshold = _number(payload.get("regression_percent", 10.0))
    baseline = _number(revisions[0].get(metric)) if revisions else 0.0
    first: dict[str, Any] | None = None
    for item in revisions[1:MAX_ITEMS]:
        current = _number(item.get(metric))
        change = ((current - baseline) * 100 / baseline) if baseline else 0.0
        if change > threshold:
            first = {"revision": _text(item.get("revision"), 200), "value": current, "change_percent": round(change, 3)}
            break
    return {
        "metric": metric,
        "revision_count": len(revisions),
        "first_regression": first,
        "execution_available": action == "run",
        "git_history_modified": False,
        "ready": bool(revisions) and first is None,
        "summary": "No evidenced regression found." if first is None else f"First evidenced regression: {first['revision']}.",
    }


def _asset_provenance(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    attribution_names = {"attributions.md", "license", "license.md", "notices.md", "third_party.md"}
    attribution_files = [path.relative_to(root).as_posix() for path in _files(root, None) if path.name.lower() in attribution_names]
    supplied = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
    assets = []
    for path in _files(root, ASSET_SUFFIXES):
        relative = path.relative_to(root).as_posix()
        assets.append(
            {
                "path": relative,
                "sha256": _hash(path),
                "bytes": _safe_size(path),
                "provenance_supplied": relative in supplied,
            }
        )
    missing = [item["path"] for item in assets if not item["provenance_supplied"]]
    return {
        "assets": assets[:MAX_ITEMS],
        "attribution_files": attribution_files,
        "missing_provenance": missing,
        "legal_review_required": True,
        "legal_clearance_claimed": False,
        "verification_only": action == "verify",
        "ready": bool(assets) and not missing and bool(attribution_files),
        "summary": f"Inventoried {len(assets)} assets; {len(missing)} lack supplied provenance.",
    }


def _domain_invariants(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    supplied = [_text(item, 1_000) for item in _list(payload.get("requirements"))]
    pattern = re.compile(r"(?i)^.{0,180}\b(?:must|shall|cannot|never|unique|invariant|constraint)\b.{0,220}$")
    candidates = supplied[:MAX_ITEMS]
    evidence: list[dict[str, str]] = []
    for path in _files(root, TEXT_SUFFIXES):
        for line in _read(path).splitlines():
            if pattern.match(line.strip()):
                statement = line.strip()[:400]
                candidates.append(statement)
                evidence.append({"path": path.relative_to(root).as_posix(), "statement": statement})
                if len(candidates) >= MAX_ITEMS:
                    break
    unique = list(dict.fromkeys(item for item in candidates if item))
    catalog = [
        {"id": f"INV-{index:03d}", "statement": value, "status": "CANDIDATE", "human_validation_required": True}
        for index, value in enumerate(unique, 1)
    ]
    return {
        "catalog": catalog,
        "evidence": evidence[:MAX_ITEMS],
        "generated": action == "generate",
        "ready": bool(catalog),
        "summary": f"Mined {len(catalog)} candidate domain invariants for review.",
    }


def _ai_governance(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del root
    source = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else payload
    groups = {
        "inventory": ("model_inventory", "system_owner", "intended_use"),
        "risk": ("risk_assessment", "misuse_cases", "impact"),
        "evaluation": ("evaluation", "limitations", "monitoring"),
        "oversight": ("human_oversight", "approval", "escalation"),
        "privacy_security": ("privacy", "security", "data_governance"),
        "incidents": ("incident_response", "rollback", "audit_log"),
    }
    checks = {
        name: {key: bool(source.get(key)) for key in keys}
        for name, keys in groups.items()
    }
    complete = all(all(values.values()) for values in checks.values())
    return {
        "checks": checks,
        "comparison_requested": action == "compare",
        "legal_review_required": True,
        "compliance_guaranteed": False,
        "ready": complete,
        "summary": f"AI governance evidence covered {sum(all(v.values()) for v in checks.values())}/{len(checks)} domains.",
    }


def _files(root: Path, suffixes: set[str] | None) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if len(files) >= MAX_FILES:
            break
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if path.is_symlink() or any(part.lower() in EXCLUDED for part in relative.parts):
            continue
        if path.is_file() and (suffixes is None or path.suffix.lower() in suffixes):
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def _corpus(root: Path, *, extra: str = "") -> str:
    chunks = [extra.lower()]
    for path in _files(root, TEXT_SUFFIXES):
        if sum(len(item) for item in chunks) >= 2_000_000:
            break
        chunks.append(_read(path).lower())
    return "\n".join(chunks)


def _signal_report(
    root: Path,
    groups: dict[str, tuple[str, ...]],
    *,
    suffixes: set[str] | None = None,
) -> dict[str, list[str]]:
    results = {name: [] for name in groups}
    for path in _files(root, suffixes or TEXT_SUFFIXES):
        lowered = _read(path).lower()
        relative = path.relative_to(root).as_posix()
        for name, markers in groups.items():
            if len(results[name]) < 30 and any(marker in lowered for marker in markers):
                results[name].append(relative)
    return results


def _read(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _write_json(path: Path, data: dict[str, Any], workspace: Path) -> Path:
    target = validate_workspace_path(path, workspace)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    return target


def _objects(value: object) -> list[dict[str, Any]]:
    return [item for item in value[:2_000] if isinstance(item, dict)] if isinstance(value, list) else []


def _list(value: object) -> list[object]:
    return value[:MAX_ITEMS] if isinstance(value, list) else []


def _text(value: object, limit: int = 2_000) -> str:
    return str(value)[:limit] if value is not None else ""


def _number(value: object, default: float = 0.0) -> float:
    try:
        number = float(value) if isinstance(value, (str, int, float)) else default
    except ValueError:
        return default
    return number if number == number and abs(number) != float("inf") else default


def _terms(value: str) -> list[str]:
    return [item for item in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{3,}", value.lower()) if item not in {"shall", "should", "must", "with", "from", "that"}][:20]


def _is_test(path: Path) -> bool:
    lowered = path.as_posix().lower()
    return "test" in path.name.lower() or "/tests/" in f"/{lowered}" or ".spec." in lowered


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _archetype_layers(archetype: str) -> list[str]:
    return {
        "api_service": ["transport", "application", "domain", "persistence", "verification"],
        "saas_web": ["web", "api", "domain", "tenancy", "billing", "data", "operations"],
        "game": ["input", "simulation", "rendering", "audio", "assets", "gameplay_tests"],
        "desktop": ["native_shell", "views", "application", "runtime", "local_storage", "packaging"],
        "cli": ["commands", "application", "domain", "adapters", "tests"],
        "data_ml": ["ingestion", "validation", "transformation", "evaluation", "lineage"],
        "infrastructure": ["modules", "environments", "policy", "verification", "rollback"],
        "library": ["public_api", "implementation", "compatibility", "tests", "packaging"],
    }.get(archetype, ["requirements", "architecture", "implementation", "verification"])
