"""Deterministic analyses for ANN's frontier engineering skills.

Project repositories remain read-only in this module. Executable checks are
dispatched by :mod:`agentic_network.skills.engineering_runtime`, where they
must pass the existing permission, approval, path, and Compose isolation gates.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable

from agentic_network.skills.supreme_runtime import (
    TEXT_SUFFIXES,
    _corpus,
    _files,
    _read,
    _signal_report,
    _write_json,
)
from agentic_network.skills.external_runner_evidence import validate_external_runner_evidence
from agentic_network.skills.sandbox import validate_workspace_path


FRONTIER_SKILLS = frozenset(
    {
        "autonomous_delivery_benchmark",
        "capacity_economics",
        "cross_store_consistency",
        "cryptographic_protocol_verification",
        "language_server_intelligence",
        "llm_application_security",
        "mobile_device_lab",
        "native_ui_automation",
        "privacy_rights_verification",
        "product_telemetry_validation",
        "runtime_failure_lab",
        "sdk_contract_conformance",
    }
)
MAX_ITEMS = 500
BENCHMARK_CATALOG = Path(__file__).resolve().parents[2] / "config" / "autonomous_delivery_benchmarks.json"


def parse_language_server_diagnostics(text: str, tool: str) -> list[dict[str, Any]]:
    """Normalize bounded Pyright or TypeScript diagnostics without retaining source text."""

    bounded = str(text or "")[:1_000_000]
    diagnostics: list[dict[str, Any]] = []
    if tool.lower() in {"pyright", "python_lsp"}:
        try:
            payload = json.loads(bounded)
        except json.JSONDecodeError:
            payload = {}
        items = payload.get("generalDiagnostics", []) if isinstance(payload, dict) else []
        for item in items[:MAX_ITEMS] if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            start = item.get("range", {}).get("start", {}) if isinstance(item.get("range"), dict) else {}
            message = str(item.get("message") or "")
            diagnostics.append(
                {
                    "path": str(item.get("file") or "")[:500],
                    "severity": str(item.get("severity") or "unknown").lower()[:30],
                    "code": str(item.get("rule") or "")[:100],
                    "line": _integer(start.get("line"), 0, 10_000_000) + 1,
                    "column": _integer(start.get("character"), 0, 10_000_000) + 1,
                    "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
                }
            )
        if diagnostics:
            return diagnostics
    pattern = re.compile(
        r"^(?P<path>.+?)\((?P<line>\d+),(?P<column>\d+)\):\s*"
        r"(?P<severity>error|warning)\s+(?P<code>TS\d+):\s*(?P<message>.+)$",
        re.IGNORECASE,
    )
    for line in bounded.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        diagnostics.append(
            {
                "path": match.group("path")[:500],
                "severity": match.group("severity").lower(),
                "code": match.group("code").upper(),
                "line": int(match.group("line")),
                "column": int(match.group("column")),
                "message_sha256": hashlib.sha256(
                    match.group("message").encode("utf-8")
                ).hexdigest(),
            }
        )
        if len(diagnostics) >= MAX_ITEMS:
            break
    return diagnostics


def enrich_specialist_execution(
    skill_name: str,
    workspace: Path,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Attach bounded interpreted evidence to an approved Compose recipe result."""

    data = result.setdefault("data", {})
    recipe = str(data.get("recipe") or "") if isinstance(data, dict) else ""
    recipe_result = data.get("result", {}) if isinstance(data, dict) else {}
    stdout = _workspace_text(workspace, recipe_result.get("stdout_path"))
    stderr = _workspace_text(workspace, recipe_result.get("stderr_path"))
    interpretation: dict[str, Any] = {
        "recipe": recipe,
        "runtime_status": str(result.get("status") or "UNKNOWN"),
        "evidence_source": "approved_docker_compose_recipe",
        "project_modified_by_interpreter": False,
        "raw_log_injected": False,
    }
    if skill_name == "language_server_intelligence":
        diagnostics = parse_language_server_diagnostics(
            stdout or stderr,
            "pyright" if recipe == "python_lsp" else "typescript",
        )
        counts = Counter(item["severity"] for item in diagnostics)
        interpretation.update(
            {
                "diagnostics": diagnostics,
                "diagnostic_counts": dict(sorted(counts.items())),
            }
        )
        artifact = _write_json(
            workspace / "language_server_diagnostics.json", interpretation, workspace
        )
        result.setdefault("artifacts", []).append(str(artifact))
    elif skill_name == "autonomous_delivery_benchmark":
        interpretation["benchmark_catalog"] = _benchmark_catalog()
        interpretation["full_delivery_claim_allowed"] = False
        interpretation["reason"] = "stage-specific evidence is required in addition to recipe exit status"
    else:
        interpretation["output_fingerprint"] = hashlib.sha256(
            (stdout + "\n" + stderr).encode("utf-8")
        ).hexdigest()
    data["interpretation"] = interpretation
    return result


def _workspace_text(workspace: Path, value: Any) -> str:
    if not value:
        return ""
    try:
        candidate = validate_workspace_path(str(value), workspace)
    except (OSError, ValueError):
        return ""
    try:
        return candidate.read_text(  # lgtm[py/path-injection]
            encoding="utf-8", errors="replace"
        )[:1_000_000]
    except OSError:
        return ""


def _benchmark_catalog() -> dict[str, Any]:
    try:
        payload = json.loads(BENCHMARK_CATALOG.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"version": 0, "cases": [], "status": "MISSING"}
    if not isinstance(payload, dict):
        return {"version": 0, "cases": [], "status": "INVALID"}
    cases = payload.get("cases", [])
    return {
        "version": payload.get("version", 0),
        "case_ids": [str(item.get("id")) for item in cases if isinstance(item, dict)][:100],
        "status": "LOADED",
    }


def execute_frontier_action(
    skill_name: str,
    action: str,
    payload: dict[str, Any],
    workspace: Path,
    project_root: Path,
) -> dict[str, Any]:
    """Execute one bounded frontier analysis without modifying the project."""

    handlers: dict[str, Callable[[str, dict[str, Any], Path], dict[str, Any]]] = {
        "language_server_intelligence": _language_server_intelligence,
        "autonomous_delivery_benchmark": _autonomous_delivery_benchmark,
        "runtime_failure_lab": _runtime_failure_lab,
        "native_ui_automation": _native_ui_automation,
        "llm_application_security": _llm_application_security,
        "privacy_rights_verification": _privacy_rights_verification,
        "cryptographic_protocol_verification": _cryptographic_protocol_verification,
        "sdk_contract_conformance": _sdk_contract_conformance,
        "mobile_device_lab": _mobile_device_lab,
        "capacity_economics": _capacity_economics,
        "cross_store_consistency": _cross_store_consistency,
        "product_telemetry_validation": _product_telemetry_validation,
    }
    if skill_name not in FRONTIER_SKILLS:
        raise ValueError("unsupported_frontier_skill")
    data = handlers[skill_name](action, payload, project_root)
    data.setdefault("action", action)
    data.setdefault("project_modified", False)
    data.setdefault("terminal_executed", False)
    data.setdefault("network_used", False)
    data.setdefault("bounded", True)
    ready = bool(data.pop("ready", False))
    summary = str(data.pop("summary", f"{skill_name}.{action} evidence generated."))
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


def _language_server_intelligence(
    action: str, payload: dict[str, Any], root: Path
) -> dict[str, Any]:
    suffix_languages = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".cs": "csharp",
    }
    counts = Counter(
        suffix_languages[path.suffix.lower()]
        for path in _files(root, set(suffix_languages))
        if path.suffix.lower() in suffix_languages
    )
    config_names = {
        "jsconfig.json",
        "mypy.ini",
        "pyproject.toml",
        "pyrightconfig.json",
        "rust-project.json",
        "tsconfig.json",
    }
    configs = [
        path.relative_to(root).as_posix()
        for path in _files(root, None)
        if path.name.lower() in config_names or path.name.lower().startswith("tsconfig.")
    ][:MAX_ITEMS]
    corpus = _corpus(root)
    tools = {
        tool: tool in corpus
        for tool in (
            "gopls",
            "jdtls",
            "mypy",
            "pyright",
            "rust-analyzer",
            "typescript",
        )
    }
    diagnostics = []
    for item in _objects(payload.get("diagnostics")):
        diagnostics.append(
            {
                "path": _label(item.get("path"), 300),
                "code": _label(item.get("code"), 100),
                "severity": _label(item.get("severity"), 30).lower(),
                "line": _integer(item.get("line"), 0, 10_000_000),
            }
        )
    return {
        "language_counts": dict(sorted(counts.items())),
        "configuration_files": configs,
        "language_server_markers": tools,
        "diagnostics": diagnostics[:MAX_ITEMS],
        "execution_available": action == "run",
        "raw_command_accepted": False,
        "ready": bool(counts) and (bool(configs) or any(tools.values())),
        "summary": f"Indexed language-server readiness for {sum(counts.values())} source files.",
    }


def _autonomous_delivery_benchmark(
    action: str, payload: dict[str, Any], root: Path
) -> dict[str, Any]:
    required = (
        "requirements",
        "architecture",
        "implementation",
        "build",
        "tests",
        "review",
        "package",
        "rollback",
    )
    supplied = payload.get("stages") if isinstance(payload.get("stages"), dict) else {}
    stages = {
        name: {
            "status": _status(supplied.get(name)),
            "passed": _status(supplied.get(name)) in {"complete", "passed", "success"},
        }
        for name in required
    }
    provenance = payload.get("model_provenance")
    provenance_fields = {
        name: bool(provenance.get(name)) if isinstance(provenance, dict) else False
        for name in ("model", "model_hash", "backend", "runtime_version")
    }
    artifacts = [path.relative_to(root).as_posix() for path in _files(root, {".json", ".md"})]
    passed = sum(bool(item["passed"]) for item in stages.values())
    return {
        "stages": stages,
        "passed_stages": passed,
        "required_stages": len(stages),
        "model_provenance": provenance_fields,
        "evidence_artifacts": artifacts[:MAX_ITEMS],
        "benchmark_catalog": _benchmark_catalog(),
        "execution_available": action == "run",
        "success_requires_runtime_evidence": True,
        "ready": passed == len(stages) and all(provenance_fields.values()),
        "summary": f"Delivery benchmark has passing evidence for {passed}/{len(stages)} stages.",
    }


def _runtime_failure_lab(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    required = (
        "process_interruption",
        "disk_exhaustion",
        "docker_loss",
        "corrupt_model",
        "packaging_interruption",
    )
    supplied = payload.get("scenarios") if isinstance(payload.get("scenarios"), dict) else {}
    scenarios = {
        name: {
            "status": _status(supplied.get(name)),
            "recovered": _status(supplied.get(name)) in {"passed", "recovered", "success"},
            "host_disruption_allowed": False,
        }
        for name in required
    }
    signals = _signal_report(
        root,
        {
            "checkpoint": ("checkpoint", "resume", "recovery"),
            "atomicity": ("atomic", "transaction", "rollback"),
            "resource_guard": ("disk", "quota", "resource limit"),
            "model_integrity": ("sha256", "model hash", "corrupt model"),
        },
    )
    recovered = sum(bool(item["recovered"]) for item in scenarios.values())
    return {
        "scenarios": scenarios,
        "repository_signals": signals,
        "recovered_scenarios": recovered,
        "execution_available": action == "run",
        "physical_power_off_performed": False,
        "host_disk_fill_performed": False,
        "ready": recovered == len(scenarios),
        "summary": f"Runtime recovery evidence passed {recovered}/{len(scenarios)} controlled scenarios.",
    }


def _native_ui_automation(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    corpus = _corpus(root)
    frameworks = {
        "appium_windows": "appium" in corpus and "windows" in corpus,
        "electron": "electron" in corpus,
        "pyside": "pyside6" in corpus,
        "pywinauto": "pywinauto" in corpus,
        "qt": "qtwidgets" in corpus or "qmainwindow" in corpus,
        "tauri": "tauri" in corpus,
        "uiautomation": "uiautomation" in corpus or "automationid" in corpus,
        "winappdriver": "winappdriver" in corpus,
        "winui_wpf": "winui" in corpus or "windowsdesktop" in corpus or "wpf" in corpus,
    }
    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {}
    checks = {
        name: evidence.get(name) is True
        for name in (
            "clean_machine",
            "first_launch",
            "navigation",
            "keyboard",
            "accessibility_tree",
            "shutdown",
        )
    }
    attestation = validate_external_runner_evidence(evidence, "native_ui")
    return {
        "frameworks": frameworks,
        "evidence_checks": checks,
        "evidence_provenance": attestation,
        "verification_requested": action == "verify",
        "host_application_executed": False,
        "external_runner_required": True,
        "ready": any(frameworks.values()) and all(checks.values()) and attestation["valid"],
        "summary": f"Native UI evidence passed {sum(checks.values())}/{len(checks)} gates.",
    }


def _llm_application_security(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    signals = _signal_report(
        root,
        {
            "instruction_boundary": ("prompt injection", "untrusted input", "system prompt"),
            "tool_policy": ("tool allowlist", "allowed_tools", "approval_required"),
            "retrieval_boundary": ("citation", "retrieval", "rag", "source trust"),
            "secret_redaction": ("redact", "secret", "credential", "sensitive"),
            "output_validation": ("output schema", "structured output", "validate output"),
        },
    )
    scenarios = [
        "instruction_override",
        "tool_argument_injection",
        "retrieval_poisoning",
        "cross_tenant_context_leakage",
        "secret_extraction",
        "unsafe_output_consumption",
    ]
    covered = sum(bool(paths) for paths in signals.values())
    return {
        "controls": signals,
        "non_destructive_scenarios": scenarios,
        "execution_available": action == "run",
        "production_attack_allowed": False,
        "ready": covered == len(signals),
        "summary": f"LLM security controls covered {covered}/{len(signals)} domains.",
    }


def _privacy_rights_verification(
    action: str, payload: dict[str, Any], root: Path
) -> dict[str, Any]:
    del payload
    signals = _signal_report(
        root,
        {
            "access_export": ("data export", "download my data", "portability", "dsar"),
            "erasure": ("right to delete", "erase", "anonymize", "delete account"),
            "retention": ("retention", "expires_at", "purge", "ttl"),
            "consent": ("consent", "lawful basis", "cookie preference"),
            "tenant_purge": ("tenant purge", "tenant_id", "row level security"),
            "audit": ("audit log", "audit_event", "deletion receipt"),
        },
    )
    covered = sum(bool(paths) for paths in signals.values())
    return {
        "rights_matrix": signals,
        "execution_available": action == "run",
        "legal_review_required": True,
        "compliance_guaranteed": False,
        "ready": covered == len(signals),
        "summary": f"Privacy-rights implementation evidence covered {covered}/{len(signals)} controls.",
    }


def _cryptographic_protocol_verification(
    action: str, payload: dict[str, Any], root: Path
) -> dict[str, Any]:
    del payload
    signals = _signal_report(
        root,
        {
            "transport": ("tls", "https", "hsts"),
            "token_validation": ("jwt", "issuer", "audience", "algorithm"),
            "key_rotation": ("key rotation", "kid", "jwks", "key version"),
            "password_hashing": ("argon2", "bcrypt", "scrypt"),
            "randomness": ("secrets.token", "randombytes", "secure random"),
        },
    )
    insecure_patterns = {
        "jwt_signature_disabled": re.compile(r"(?i)verify_signature\s*[:=]\s*false"),
        "insecure_hash": re.compile(r"(?i)\b(?:md5|sha1)\s*\("),
        "weak_random": re.compile(r"(?i)\brandom\.(?:random|randint)\s*\("),
        "tls_verification_disabled": re.compile(r"(?i)(?:verify\s*=\s*false|rejectunauthorized\s*:\s*false)"),
    }
    findings: list[dict[str, str]] = []
    for path in _files(root, TEXT_SUFFIXES):
        text = _read(path)
        for finding, pattern in insecure_patterns.items():
            if pattern.search(text):
                findings.append({"path": path.relative_to(root).as_posix(), "finding": finding})
    covered = sum(bool(paths) for paths in signals.values())
    return {
        "control_evidence": signals,
        "insecure_usage_findings": findings[:MAX_ITEMS],
        "execution_available": action == "run",
        "private_key_material_recorded": False,
        "ready": covered == len(signals) and not findings,
        "summary": f"Cryptographic controls covered {covered}/{len(signals)} domains with {len(findings)} unsafe-use findings.",
    }


def _sdk_contract_conformance(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    contract_files = [
        path.relative_to(root).as_posix()
        for path in _files(root, {".json", ".yaml", ".yml"})
        if "openapi" in path.name.lower() or "swagger" in path.name.lower()
    ]
    sdk_paths = [
        path.relative_to(root).as_posix()
        for path in _files(root, TEXT_SUFFIXES)
        if any(part.lower() in {"client", "clients", "sdk", "sdks"} for part in path.parts)
    ][:MAX_ITEMS]
    corpus = _corpus(root)
    controls = {
        "contract_present": bool(contract_files) or "openapi" in corpus,
        "generated_client_present": bool(sdk_paths),
        "versioning_present": "api version" in corpus or "versioned" in corpus,
        "contract_tests_present": "contract test" in corpus or "schemathesis" in corpus,
        "error_mapping_present": "error mapping" in corpus or "apierror" in corpus.lower(),
    }
    return {
        "contract_files": contract_files[:MAX_ITEMS],
        "sdk_paths": sdk_paths,
        "controls": controls,
        "execution_available": action == "run",
        "project_code_generated": False,
        "ready": all(controls.values()),
        "summary": f"SDK conformance evidence passed {sum(controls.values())}/{len(controls)} controls.",
    }


def _mobile_device_lab(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    project_files = _files(root, None)
    names = {path.name.lower() for path in project_files}
    relative_paths = {path.relative_to(root).as_posix().lower() for path in project_files}
    corpus = _corpus(root)
    platforms = {
        "android": "androidmanifest.xml" in names or "gradlew" in names,
        "flutter": "pubspec.yaml" in names and "flutter" in corpus,
        "ios": "info.plist" in names or any(".xcodeproj/" in path for path in relative_paths),
        "react_native": "react-native" in corpus or "metro.config.js" in names,
    }
    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {}
    checks = {
        name: evidence.get(name) is True
        for name in (
            "device_identity",
            "install",
            "launch",
            "interaction",
            "network_capture",
            "accessibility",
            "uninstall",
        )
    }
    attestation = validate_external_runner_evidence(evidence, "mobile")
    return {
        "platforms": platforms,
        "evidence_checks": checks,
        "evidence_provenance": attestation,
        "verification_requested": action == "verify",
        "host_emulator_started": False,
        "external_device_runner_required": True,
        "ready": any(platforms.values()) and all(checks.values()) and attestation["valid"],
        "summary": f"Mobile device evidence passed {sum(checks.values())}/{len(checks)} gates.",
    }


def _capacity_economics(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del root
    baseline = payload.get("baseline") if isinstance(payload.get("baseline"), dict) else {}
    requests_per_second = _number(baseline.get("requests_per_second"))
    latency_ms = _number(baseline.get("latency_ms"))
    memory_mb = _number(baseline.get("memory_mb"))
    concurrent_capacity = (
        round(requests_per_second * latency_ms / 1000, 3)
        if requests_per_second > 0 and latency_ms > 0
        else 0.0
    )
    target_multiplier = max(1.0, min(_number(payload.get("target_multiplier"), 2.0), 100.0))
    projection = {
        "target_requests_per_second": round(requests_per_second * target_multiplier, 3),
        "estimated_concurrent_work": round(concurrent_capacity * target_multiplier, 3),
        "linear_memory_mb": round(memory_mb * target_multiplier, 3),
        "binding_cost_estimate": False,
    }
    complete = requests_per_second > 0 and latency_ms > 0 and memory_mb > 0
    return {
        "baseline": {
            "requests_per_second": requests_per_second,
            "latency_ms": latency_ms,
            "memory_mb": memory_mb,
        },
        "projection": projection,
        "benchmark_requested": action == "benchmark",
        "human_capacity_review_required": True,
        "ready": complete,
        "summary": "Capacity baseline is complete." if complete else "Capacity baseline is incomplete.",
    }


def _cross_store_consistency(action: str, payload: dict[str, Any], root: Path) -> dict[str, Any]:
    del payload
    signals = _signal_report(
        root,
        {
            "primary_database": ("postgres", "sqlalchemy", "database"),
            "cache": ("redis", "cache", "ttl"),
            "queue": ("queue", "broker", "kafka", "rabbitmq"),
            "search_index": ("elasticsearch", "opensearch", "search index"),
            "outbox": ("outbox", "change data capture", "cdc"),
            "reconciliation": ("reconcile", "consistency check", "repair job"),
            "idempotency": ("idempotency", "dedup", "event_id"),
        },
    )
    active_stores = [name for name in ("primary_database", "cache", "queue", "search_index") if signals[name]]
    required_controls = ["outbox", "reconciliation", "idempotency"] if len(active_stores) > 1 else []
    missing = [name for name in required_controls if not signals[name]]
    return {
        "store_evidence": signals,
        "active_stores": active_stores,
        "required_consistency_controls": required_controls,
        "missing_controls": missing,
        "execution_available": action == "run",
        "ready": bool(active_stores) and not missing,
        "summary": f"Detected {len(active_stores)} data stores and {len(missing)} missing consistency controls.",
    }


def _product_telemetry_validation(
    action: str, payload: dict[str, Any], root: Path
) -> dict[str, Any]:
    del payload
    signals = _signal_report(
        root,
        {
            "event_taxonomy": ("event name", "event_name", "analytics.track", "capture("),
            "identity": ("anonymous_id", "user_id", "identify("),
            "consent": ("analytics consent", "cookie preference", "opt out"),
            "pii_filter": ("pii", "redact", "property allowlist"),
            "funnel": ("funnel", "activation", "conversion"),
            "experiment": ("experiment", "variant", "exposure event"),
            "quality": ("duplicate event", "schema validation", "event version"),
        },
    )
    covered = sum(bool(paths) for paths in signals.values())
    return {
        "telemetry_controls": signals,
        "execution_available": action == "run",
        "analytics_provider_contacted": False,
        "production_events_emitted": False,
        "ready": covered == len(signals),
        "summary": f"Product telemetry evidence covered {covered}/{len(signals)} controls.",
    }


def _objects(value: object) -> list[dict[str, Any]]:
    return [item for item in value[:MAX_ITEMS] if isinstance(item, dict)] if isinstance(value, list) else []


def _label(value: object, limit: int) -> str:
    text = str(value or "")[:limit]
    return re.sub(r"[\r\n\x00-\x1f]+", " ", text).strip()


def _status(value: object) -> str:
    if isinstance(value, dict):
        value = value.get("status")
    return _label(value, 40).lower() or "missing"


def _number(value: object, default: float = 0.0) -> float:
    try:
        number = float(value) if isinstance(value, (str, int, float)) else default
    except ValueError:
        return default
    return number if number == number and abs(number) != float("inf") else default


def _integer(value: object, minimum: int, maximum: int) -> int:
    try:
        number = int(value) if isinstance(value, (str, int)) else minimum
    except ValueError:
        number = minimum
    return max(minimum, min(number, maximum))
