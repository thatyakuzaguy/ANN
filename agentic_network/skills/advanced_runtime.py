"""Deterministic runtimes for ANN's advanced engineering skills.

This module contains analysis and narrowly scoped network checks. Host
commands and mutations remain in engineering_runtime so they reuse ANN's
command allowlist, Compose isolation, and Approval Center.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import html
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from agentic_network.architecture_entropy import evaluate_architecture_entropy
from agentic_network.contract_arbitration import evaluate_contract_arbitration
from agentic_network.repository_intelligence_agent.runtime import build_repository_intelligence
from agentic_network.skills.sandbox import validate_workspace_path
from agentic_network.test_validity_gate import evaluate_test_validity_gate


EXCLUDED_PARTS = {
    ".git",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "adapters",
    "build",
    "coverage",
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
MAX_FILES = 5_000
MAX_TEXT = 1_000_000
SECRET_NAME = re.compile(
    r"(?i)(api[_-]?key|password|secret|token|credential|private[_-]?key)"
)


def execute_advanced_action(
    skill_name: str,
    action: str,
    payload: dict[str, Any],
    workspace: Path,
    project_root: Path,
) -> dict[str, Any]:
    """Execute one advanced analytical or network skill action."""

    handlers = {
        "internet_search": _internet_search,
        "package_registry": _package_registry,
        "requirements_contract": _requirements_contract,
        "dependency_doctor": _dependency_doctor,
        "runtime_observability": _runtime_observability,
        "test_quality": _test_quality,
        "architecture_fitness": _architecture_fitness,
        "backup_restore": _backup_restore_readiness,
        "performance_testing": _performance_readiness,
        "supply_chain_compliance": _supply_chain,
        "release_provenance": _release_provenance,
        "deployment_verification": _deployment_readiness,
        "external_integration_verification": _external_integrations,
        "ux_quality": _ux_quality,
        "mobile_validation": _mobile_validation,
        "game_validation": _game_validation,
        "data_pipeline": _data_pipeline,
        "ml_evaluation": _ml_evaluation,
        "infrastructure_validation": _infrastructure_validation,
        "desktop_validation": _desktop_validation,
        "localization": _localization,
    }
    handler = handlers.get(skill_name)
    if handler is None:
        raise ValueError("unsupported_advanced_skill")
    result = handler(action, payload, workspace, project_root)
    result.setdefault("status", "SUCCESS")
    result.setdefault("summary", f"{skill_name}.{action} completed")
    result.setdefault("data", {})
    result.setdefault("artifacts", [])
    result.setdefault("warnings", [])
    result.setdefault("errors", [])
    result.setdefault("terminal_used", False)
    result.setdefault("internet_used", False)
    result.setdefault("dependency_install_used", False)
    return result


def _requirements_contract(
    action: str, payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    user_request = _bounded_text(
        payload.get("user_request") or payload.get("request"), 30_000
    )
    product = _bounded_text(payload.get("product_requirements"), 60_000)
    architecture = _bounded_text(payload.get("architecture_plan"), 60_000)
    test_plan = _bounded_text(payload.get("test_plan"), 60_000)
    if action == "arbitrate":
        report = evaluate_contract_arbitration(
            user_request=user_request,
            product_requirements=product,
            architecture_plan=architecture,
            test_plan=test_plan,
            assertion_evidence=_string_list(payload.get("assertion_evidence"), 20),
        )
        return _artifact_result(
            workspace,
            "contract_arbitration.json",
            report,
            "SUCCESS" if report["status"] == "CONTRACT_RESOLVED" else "BLOCKED",
            f"Contract arbitration returned {report['status']} with owner {report['owner']}.",
        )
    if not user_request.strip():
        return _blocked("user_request_required")
    statements = _contract_statements(user_request)
    constraints = _dedupe(
        [
            *_string_list(payload.get("constraints"), 50),
            *[item for item in statements if _is_constraint(item)],
        ]
    )
    requirements = [item for item in statements if item not in constraints]
    ambiguity = [
        item
        for item in statements
        if re.search(
            r"(?i)\b(?:etc|maybe|somehow|anything|as needed|nice to have)\b",
            item,
        )
    ]
    contract_id = hashlib.sha256(user_request.encode("utf-8")).hexdigest()[:16]
    report = {
        "version": "1.0",
        "contract_id": contract_id,
        "source": "USER_REQUEST",
        "user_request": user_request,
        "requirements": [
            {
                "id": f"REQ-{index:03d}",
                "statement": statement,
                "priority": "MUST",
            }
            for index, statement in enumerate(requirements, 1)
        ],
        "constraints": constraints,
        "user_stories": [
            (
                "As a user, I need "
                f"{statement.rstrip('.').lower()} so that the requested outcome is available."
            )
            for statement in requirements[:30]
        ],
        "acceptance_criteria": [
            {
                "requirement_id": f"REQ-{index:03d}",
                "given": "the feature is available",
                "when": statement,
                "then": "the observable result matches this contract",
            }
            for index, statement in enumerate(requirements[:50], 1)
        ],
        "ambiguities": ambiguity,
        "clarifying_questions": [
            f"Please define the measurable meaning of: {item}" for item in ambiguity
        ],
        "human_review_required": bool(ambiguity or not requirements),
        "policy": {
            "ask_only_when_required": True,
            "user_request_is_highest_authority": True,
            "generated_tests_cannot_override_contract": True,
        },
        "project_root": str(root),
    }
    status = "BLOCKED" if report["human_review_required"] else "SUCCESS"
    return _artifact_result(
        workspace,
        "requirements_contract.json",
        report,
        status,
        (
            f"Produced {len(requirements)} requirements and "
            f"{len(ambiguity)} required clarifications."
        ),
    )


def _dependency_doctor(
    action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    manifests = _dependency_manifests(root)
    ecosystems: dict[str, dict[str, Any]] = {}
    if "pyproject.toml" in manifests or "requirements.txt" in manifests:
        locks: list[str] = [
            name
            for name in (
                "uv.lock",
                "poetry.lock",
                "Pipfile.lock",
                "requirements.lock",
                "requirements.txt",
            )
            if name in manifests
        ]
        ecosystems["python"] = {
            "manifests": [
                name
                for name in manifests
                if name in {"pyproject.toml", "requirements.txt", "Pipfile"}
            ],
            "locks": locks,
        }
    if "package.json" in manifests:
        locks = [
            name
            for name in (
                "pnpm-lock.yaml",
                "package-lock.json",
                "yarn.lock",
                "bun.lockb",
            )
            if name in manifests
        ]
        ecosystems["node"] = {"manifests": ["package.json"], "locks": locks}
    if "Cargo.toml" in manifests:
        ecosystems["rust"] = {
            "manifests": ["Cargo.toml"],
            "locks": [name for name in ("Cargo.lock",) if name in manifests],
        }
    if "go.mod" in manifests:
        ecosystems["go"] = {
            "manifests": ["go.mod"],
            "locks": [name for name in ("go.sum",) if name in manifests],
        }
    missing_locks = sorted(
        name for name, data in ecosystems.items() if not data["locks"]
    )
    report: dict[str, Any] = {
        "action": action,
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "manifests": manifests,
        "ecosystems": ecosystems,
        "missing_lockfiles": missing_locks,
        "docker_images": _docker_images(root),
        "version_risks": _unbounded_dependency_specs(root),
        "install_performed": False,
        "network_used": False,
        "reproducible": not missing_locks,
    }
    status = "SUCCESS" if not missing_locks else "PARTIAL"
    return _artifact_result(
        workspace,
        "dependency_doctor.json",
        report,
        status,
        f"Detected {len(ecosystems)} ecosystems; {len(missing_locks)} lack lockfiles.",
    )


def _runtime_observability(
    action: str, payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    log_files = _matching_files(root, {".log"}, 80)
    recent_events: list[dict[str, Any]] = []
    for path in sorted(
        log_files, key=lambda item: item.stat().st_mtime, reverse=True
    )[:20]:
        text = _read_text(path, 80_000)
        error_lines = [
            line[-1_000:]
            for line in text.splitlines()
            if re.search(
                r"(?i)\b(error|failed|exception|critical|timeout)\b", line
            )
        ][-20:]
        recent_events.append(
            {
                "path": _relative(root, path),
                "errors": error_lines,
                "size": path.stat().st_size,
            }
        )
    runtime: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "process_id": os.getpid(),
        "load_average": _load_average(),
        "declared_ports": _declared_ports(root),
        "log_files": [_relative(root, path) for path in log_files],
        "recent_error_events": recent_events,
        "telemetry_files": [
            _relative(root, path)
            for path in _find_named(
                root,
                {
                    "metrics.json",
                    "telemetry.json",
                    "trace.json",
                    "runtime_status.json",
                },
            )
        ],
    }
    if action == "correlate":
        failure = _bounded_text(payload.get("failure"), 30_000)
        terms = set(
            re.findall(r"[A-Za-z_][A-Za-z0-9_.-]{3,}", failure.lower())
        )
        runtime["correlations"] = [
            event
            for event in recent_events
            if any(
                term in json.dumps(event).lower() for term in list(terms)[:100]
            )
        ]
    return _artifact_result(
        workspace,
        "runtime_observability.json",
        runtime,
        "SUCCESS",
        (
            f"Collected {len(log_files)} log sources and "
            f"{len(runtime['declared_ports'])} declared ports."
        ),
    )


def _test_quality(
    action: str, payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    if action == "validate_failure":
        report = evaluate_test_validity_gate(
            test_report=_bounded_text(payload.get("test_report"), 80_000),
            stdout=_bounded_text(payload.get("stdout"), 80_000),
            stderr=_bounded_text(payload.get("stderr"), 80_000),
            user_request=_bounded_text(payload.get("user_request"), 30_000),
            product_requirements=_bounded_text(
                payload.get("product_requirements"), 50_000
            ),
            architecture_plan=_bounded_text(
                payload.get("architecture_plan"), 50_000
            ),
            test_plan=_bounded_text(payload.get("test_plan"), 50_000),
            code_plan=_bounded_text(payload.get("code_plan"), 50_000),
            affected_files=_string_list(payload.get("affected_files"), 100),
        )
        status = (
            "SUCCESS" if report["status"] == "VALID_TEST_FAILURE" else "BLOCKED"
        )
        return _artifact_result(
            workspace,
            "test_validity.json",
            report,
            status,
            (
                "Test Validity Gate classified evidence as "
                f"{report['classification']}."
            ),
        )
    tests = [
        path
        for path in _source_files(
            root, {".py", ".ts", ".tsx", ".js", ".jsx"}
        )
        if _is_test(path)
    ]
    counts: Counter[str] = Counter()
    weak_files: list[str] = []
    for path in tests:
        text = _read_text(path)
        counts["assertions"] += len(
            re.findall(r"\bassert\b|\bexpect\s*\(", text)
        )
        counts["skips"] += len(
            re.findall(
                r"(?i)pytest\.mark\.skip|\.skip\s*\(|@skip|xit\s*\(", text
            )
        )
        counts["mocks"] += len(
            re.findall(r"(?i)\bmock\b|monkeypatch|vi\.mock|jest\.mock", text)
        )
        counts["tests"] += len(
            re.findall(
                r"(?m)^\s*(?:async\s+)?def\s+test_|\b(?:it|test)\s*\(",
                text,
            )
        )
        has_test = re.search(
            r"(?m)^\s*(?:async\s+)?def\s+test_|\b(?:it|test)\s*\(", text
        )
        if has_test and not re.search(r"\bassert\b|\bexpect\s*\(", text):
            weak_files.append(_relative(root, path))
    mutation = _find_named(
        root,
        {
            "mutmut_config.py",
            "cosmic-ray.toml",
            "stryker.conf.json",
            "stryker.config.json",
        },
    )
    report = {
        "test_files": len(tests),
        "test_cases": counts["tests"],
        "assertions": counts["assertions"],
        "skips": counts["skips"],
        "mocks": counts["mocks"],
        "weak_test_files": weak_files[:100],
        "mutation_configuration": [
            _relative(root, path) for path in mutation
        ],
        "mutation_ready": bool(mutation),
        "quality_score": max(
            0,
            min(
                100,
                50
                + min(counts["assertions"], 40)
                - len(weak_files) * 5
                - counts["skips"] * 2,
            ),
        ),
    }
    status = "SUCCESS" if tests and not weak_files else "PARTIAL"
    return _artifact_result(
        workspace,
        "test_quality.json",
        report,
        status,
        f"Analyzed {len(tests)} test files and {counts['tests']} test cases.",
    )


def _architecture_fitness(
    _action: str, payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    intelligence = build_repository_intelligence(
        root,
        workspace / "repository",
        allowed_roots=[root],
        max_files=MAX_FILES,
    )
    graph = _read_json(
        Path(intelligence.output_files.get("dependencies", ""))
    )
    cycles = _dependency_cycles(graph)
    duplicates = _duplicate_sources(root)
    entropy: dict[str, Any] = {}
    run_dir = _safe_existing_directory(payload.get("run_dir"), root)
    if run_dir is not None:
        entropy = evaluate_architecture_entropy(run_dir, project_root=root)
    report = {
        "repository": {
            "files": intelligence.files_scanned,
            "functions": intelligence.functions,
            "classes": intelligence.classes,
            "routes": intelligence.routes,
        },
        "dependency_cycles": cycles,
        "duplicate_source_groups": duplicates,
        "entropy": entropy,
        "fitness_passed": (
            not cycles
            and not duplicates
            and entropy.get("status")
            not in {
                "REFACTOR_RECOMMENDED",
                "ARCHITECTURE_REVIEW_REQUIRED",
            }
        ),
    }
    status = "SUCCESS" if report["fitness_passed"] else "PARTIAL"
    return _artifact_result(
        workspace,
        "architecture_fitness.json",
        report,
        status,
        (
            f"Found {len(cycles)} dependency cycles and "
            f"{len(duplicates)} duplicate groups."
        ),
    )


def _backup_restore_readiness(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    compose = _first_existing(
        root,
        (
            "compose.yaml",
            "compose.yml",
            "docker-compose.yaml",
            "docker-compose.yml",
        ),
    )
    text = _read_text(compose) if compose else ""
    report = {
        "compose_file": _relative(root, compose) if compose else "",
        "postgres_service_detected": bool(
            re.search(r"(?i)postgres|timescale", text)
        ),
        "persistent_volume_detected": bool(
            re.search(
                r"(?m)^\s*volumes\s*:|/var/lib/postgresql/data", text
            )
        ),
        "backup_scripts": [
            _relative(root, path)
            for path in _matching_name(
                root,
                re.compile(r"(?i)(backup|restore).*(?:\.ps1|\.sh|\.py)$"),
                100,
            )
        ],
        "retention_policy": bool(
            _find_text(
                root,
                re.compile(
                    r"(?i)data retention|backup retention|retention_days"
                ),
                200,
            )
        ),
        "restore_test_evidence": bool(
            _find_text(
                root,
                re.compile(
                    r"(?i)test.*restore|restore.*test|disaster recovery"
                ),
                200,
            )
        ),
        "encrypted_backup_evidence": bool(
            _find_text(
                root,
                re.compile(r"(?i)encrypt.*backup|backup.*encrypt"),
                200,
            )
        ),
    }
    report["ready"] = all(
        (
            report["postgres_service_detected"],
            report["persistent_volume_detected"],
            report["backup_scripts"],
            report["restore_test_evidence"],
        )
    )
    return _artifact_result(
        workspace,
        "backup_restore_readiness.json",
        report,
        "SUCCESS" if report["ready"] else "PARTIAL",
        f"Backup/restore readiness={report['ready']}.",
    )


def _performance_readiness(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    tools = {
        "k6": bool(
            _matching_name(
                root, re.compile(r"(?i)(?:k6|load).*\.js$"), 20
            )
        ),
        "locust": bool(_find_named(root, {"locustfile.py"})),
        "artillery": bool(
            _matching_name(
                root,
                re.compile(r"(?i)artillery.*\.(?:ya?ml|json)$"),
                20,
            )
        ),
        "pytest_benchmark": bool(
            _find_text(
                root,
                re.compile(
                    r"pytest[-_]benchmark|@pytest\.mark\.benchmark"
                ),
                200,
            )
        ),
    }
    budgets = _find_text(
        root,
        re.compile(
            r"(?i)(p95|p99|latency|throughput|requests per second|performance budget)"
        ),
        300,
    )
    report = {
        "tools": tools,
        "performance_budget_evidence": budgets[:100],
        "benchmark_scripts": _package_scripts(
            root, {"benchmark", "test:performance", "perf", "load"}
        ),
        "ready": any(tools.values()) and bool(budgets),
    }
    return _artifact_result(
        workspace,
        "performance_readiness.json",
        report,
        "SUCCESS" if report["ready"] else "PARTIAL",
        (
            f"Performance tooling detected={sum(tools.values())}; "
            f"budgets={len(budgets)}."
        ),
    )


def _supply_chain(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    manifests = _dependency_manifests(root)
    licenses = [
        _relative(root, path)
        for path in _matching_name(
            root,
            re.compile(r"(?i)^(license|notice|copying)(?:\..*)?$"),
            50,
        )
    ]
    workflows = (
        _matching_files(root / ".github" / "workflows", {".yml", ".yaml"}, 100)
        if (root / ".github" / "workflows").is_dir()
        else []
    )
    unpinned_actions: list[str] = []
    for path in workflows:
        for match in re.findall(
            r"(?m)^\s*uses:\s*([^\s#]+)", _read_text(path)
        ):
            if "@" in match and not re.search(r"@[0-9a-f]{40}$", match):
                unpinned_actions.append(
                    f"{_relative(root, path)}:{match}"
                )
    report: dict[str, Any] = {
        "manifests": manifests,
        "license_files": licenses,
        "sbom_files": [
            _relative(root, path)
            for path in _matching_name(
                root,
                re.compile(r"(?i)(sbom|bom).*(?:\.json|\.xml)$"),
                100,
            )
        ],
        "lockfiles": [
            name
            for name in manifests
            if "lock" in name or name in {"go.sum", "requirements.txt"}
        ],
        "unbounded_dependencies": _unbounded_dependency_specs(root),
        "unpinned_github_actions": unpinned_actions,
        "provenance_files": [
            _relative(root, path)
            for path in _matching_name(
                root,
                re.compile(
                    r"(?i)(provenance|attestation|checksums?|sha256).*(?:\.json|\.txt|\.md)$"
                ),
                100,
            )
        ],
    }
    report["compliant"] = (
        bool(licenses)
        and bool(report["lockfiles"])
        and not unpinned_actions
    )
    return _artifact_result(
        workspace,
        "supply_chain_compliance.json",
        report,
        "SUCCESS" if report["compliant"] else "PARTIAL",
        (
            "Supply-chain policy found "
            f"{len(unpinned_actions)} unpinned actions and "
            f"{len(report['unbounded_dependencies'])} version risks."
        ),
    )


def _release_provenance(
    _action: str, payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    artifacts = (
        _matching_files(
            root / "installer", {".exe", ".msi", ".zip"}, 100
        )
        if (root / "installer").is_dir()
        else []
    )
    evidence = _matching_name(
        root,
        re.compile(
            r"(?i)(signing|provenance|attestation|hash|checksum).*\.(?:json|md|txt)$"
        ),
        200,
    )
    hashes = {
        _relative(root, path): _sha256(path)
        for path in artifacts
        if path.stat().st_size <= 1_000_000_000
    }
    expected_value = payload.get("expected_hashes")
    expected: dict[str, object] = (
        {
            str(name): value
            for name, value in expected_value.items()
        }
        if isinstance(expected_value, dict)
        else {}
    )
    mismatches = [
        str(name)
        for name, value in expected.items()
        if name not in hashes or hashes[name] != str(value).lower()
    ]
    report: dict[str, Any] = {
        "release_artifacts": list(hashes),
        "sha256": hashes,
        "evidence_files": [_relative(root, path) for path in evidence],
        "signature_files": [
            _relative(root, path)
            for path in _matching_files(
                root, {".sig", ".asc", ".p7s"}, 100
            )
        ],
        "expected_hash_mismatches": mismatches,
        "clean_machine_evidence": any(
            "clean" in path.name.lower()
            and "machine" in path.name.lower()
            for path in evidence
        ),
        "signed_evidence_declared": any(
            "sign" in path.name.lower() for path in evidence
        ),
    }
    report["verified"] = (
        bool(hashes)
        and not mismatches
        and report["signed_evidence_declared"]
    )
    return _artifact_result(
        workspace,
        "release_provenance.json",
        report,
        "SUCCESS" if report["verified"] else "PARTIAL",
        (
            f"Verified hashes for {len(hashes)} release artifacts; "
            f"provenance complete={report['verified']}."
        ),
    )


def _deployment_readiness(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    compose = _first_existing(
        root,
        (
            "compose.yaml",
            "compose.yml",
            "docker-compose.yaml",
            "docker-compose.yml",
        ),
    )
    compose_text = _read_text(compose) if compose else ""
    report: dict[str, Any] = {
        "compose_file": _relative(root, compose) if compose else "",
        "healthchecks": len(
            re.findall(r"(?m)^\s*healthcheck\s*:", compose_text)
        ),
        "restart_policies": len(
            re.findall(r"(?m)^\s*restart\s*:", compose_text)
        ),
        "rollback_evidence": _find_text(
            root, re.compile(r"(?i)rollback"), 200
        )[:100],
        "tls_evidence": _find_text(
            root, re.compile(r"(?i)https|tls|certificate"), 200
        )[:100],
        "deployment_files": [
            _relative(root, path)
            for path in _matching_name(
                root,
                re.compile(
                    r"(?i)(deploy|helm|terraform|kustom).*(?:\.ya?ml|\.tf|\.ps1|\.sh)$"
                ),
                300,
            )
        ],
        "secrets_externalized": not bool(
            _find_text(
                root,
                re.compile(
                    r"(?i)(password|api_key|secret)\s*[:=]\s*['\"]?[A-Za-z0-9+/]{12,}"
                ),
                100,
            )
        ),
    }
    report["ready"] = (
        bool(compose)
        and report["healthchecks"] > 0
        and bool(report["rollback_evidence"])
    )
    return _artifact_result(
        workspace,
        "deployment_readiness.json",
        report,
        "SUCCESS" if report["ready"] else "PARTIAL",
        (
            f"Deployment readiness={report['ready']} with "
            f"{report['healthchecks']} health checks."
        ),
    )


def _external_integrations(
    action: str, payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    if action == "probe":
        return _probe_integrations(payload, workspace)
    evidence = _find_text(
        root,
        re.compile(
            r"(?i)stripe|sendgrid|resend|s3|oauth|webhook|twilio|sentry|analytics"
        ),
        500,
    )
    env_names = sorted(
        {
            match
            for path in _source_files(
                root,
                {
                    ".py",
                    ".ts",
                    ".tsx",
                    ".js",
                    ".jsx",
                    ".env",
                    ".example",
                },
            )
            for match in re.findall(
                r"\b[A-Z][A-Z0-9_]{3,}\b", _read_text(path)
            )
            if SECRET_NAME.search(match)
        }
    )
    report = {
        "integration_evidence": evidence[:200],
        "credential_variable_names": env_names[:200],
        "hardcoded_secret_values_recorded": False,
        "webhook_signature_evidence": _find_text(
            root,
            re.compile(
                r"(?i)webhook.*signature|signature.*webhook"
            ),
            100,
        ),
        "idempotency_evidence": _find_text(
            root, re.compile(r"(?i)idempoten"), 100
        ),
        "retry_evidence": _find_text(
            root,
            re.compile(r"(?i)retry|backoff|circuit breaker"),
            100,
        ),
    }
    return _artifact_result(
        workspace,
        "external_integrations.json",
        report,
        "SUCCESS" if evidence else "PARTIAL",
        (
            f"Detected {len(evidence)} integration references and "
            f"{len(env_names)} credential variable names."
        ),
    )


def _internet_search(
    _action: str,
    payload: dict[str, Any],
    workspace: Path,
    _root: Path,
) -> dict[str, Any]:
    query = " ".join(
        _bounded_text(payload.get("query"), 500).split()
    )
    if not query:
        return _blocked("search_query_required")
    allowed_domains, domains_valid = _allowed_domains(
        payload.get("allowed_domains"), 30, required=False
    )
    if not domains_valid:
        return _blocked("allowed_domains_invalid")
    max_results = max(
        1, min(10, _int(payload.get("max_results"), 5))
    )
    endpoint = (
        "https://html.duckduckgo.com/html/?"
        + urlencode({"q": query})
    )
    opener = build_opener(_NoRedirect())
    try:
        response = opener.open(
            Request(
                endpoint,
                headers={"User-Agent": "ANN-Web-Search/1.0"},
            ),
            timeout=max(
                1,
                min(
                    15,
                    _int(payload.get("timeout_seconds"), 8),
                ),
            ),
        )
        page = response.read(600_000).decode(
            "utf-8", errors="replace"
        )
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {
            "status": "FAILED",
            "summary": "Public web search request failed.",
            "errors": [type(exc).__name__],
            "internet_used": True,
        }
    links = re.findall(
        r"""(?is)<a[^>]+class=["'][^"']*result__a[^"']*["'][^>]+href=["']([^"']+)["'][^>]*>(.*?)</a>""",
        page,
    )
    snippets = re.findall(
        r"""(?is)<(?:a|div)[^>]+class=["'][^"']*result__snippet[^"']*["'][^>]*>(.*?)</(?:a|div)>""",
        page,
    )
    results: list[dict[str, str]] = []
    for index, (raw_url, raw_title) in enumerate(links):
        destination = _duckduckgo_destination(
            html.unescape(raw_url)
        )
        parsed = urlparse(destination)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in {"http", "https"} or not host:
            continue
        if allowed_domains and not any(
            host == domain or host.endswith(f".{domain}")
            for domain in allowed_domains
        ):
            continue
        title = _strip_html(raw_title)
        snippet = (
            _strip_html(snippets[index])
            if index < len(snippets)
            else ""
        )
        results.append(
            {
                "title": title[:500],
                "url": destination[:2_000],
                "domain": host,
                "snippet": snippet[:1_000],
            }
        )
        if len(results) >= max_results:
            break
    report = {
        "query": query,
        "provider": "duckduckgo_html",
        "allowed_domains": sorted(allowed_domains),
        "results": results,
        "result_pages_opened": False,
        "credentials_sent": False,
    }
    return _artifact_result(
        workspace,
        "internet_search.json",
        report,
        "SUCCESS" if results else "PARTIAL",
        f"Public web search returned {len(results)} bounded results.",
        internet_used=True,
    )


def _package_registry(
    _action: str,
    payload: dict[str, Any],
    workspace: Path,
    _root: Path,
) -> dict[str, Any]:
    ecosystem = str(
        payload.get("ecosystem") or ""
    ).strip().lower()
    name = str(payload.get("name") or "").strip()
    if ecosystem == "pypi":
        if ".." in name or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", name
        ):
            return _blocked("pypi_package_name_invalid")
        url = (
            "https://pypi.org/pypi/"
            f"{quote(name, safe='')}/json"
        )
    elif ecosystem == "npm":
        if ".." in name or not re.fullmatch(
            r"(?:@[a-z0-9][a-z0-9._-]{0,126}/)?[a-z0-9][a-z0-9._-]{0,127}",
            name,
        ):
            return _blocked("npm_package_name_invalid")
        url = (
            "https://registry.npmjs.org/"
            f"{quote(name, safe='')}"
        )
    else:
        return _blocked("package_ecosystem_not_supported")
    opener = build_opener(_NoRedirect())
    try:
        response = opener.open(
            Request(
                url,
                headers={"User-Agent": "ANN-Package-Metadata/1.0"},
            ),
            timeout=max(
                1,
                min(
                    15,
                    _int(payload.get("timeout_seconds"), 8),
                ),
            ),
        )
        raw = response.read(2_000_000)
        metadata = json.loads(raw.decode("utf-8"))
    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        return {
            "status": "FAILED",
            "summary": "Package registry request failed.",
            "errors": [type(exc).__name__],
            "internet_used": True,
        }
    if not isinstance(metadata, dict):
        return _blocked("package_registry_payload_invalid")
    report = (
        _pypi_metadata(name, metadata)
        if ecosystem == "pypi"
        else _npm_metadata(name, metadata)
    )
    report.update(
        {
            "ecosystem": ecosystem,
            "archive_downloaded": False,
            "dependency_installed": False,
            "registry_host": urlparse(url).hostname,
        }
    )
    return _artifact_result(
        workspace,
        "package_registry.json",
        report,
        "SUCCESS",
        (
            f"Read {ecosystem} metadata for {name}; "
            "no package was downloaded or installed."
        ),
        internet_used=True,
    )


def _ux_quality(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    sources = _source_files(
        root, {".tsx", ".jsx", ".html", ".css", ".vue", ".svelte"}
    )
    joined = "\n".join(
        _read_text(path, 200_000) for path in sources[:500]
    )
    report: dict[str, Any] = {
        "ui_files": len(sources),
        "semantic_landmarks": len(
            re.findall(
                r"<(?:main|nav|header|footer|section)\b", joined, re.I
            )
        ),
        "aria_labels": len(
            re.findall(
                r"aria-(?:label|labelledby|describedby)", joined, re.I
            )
        ),
        "unlabelled_image_candidates": len(
            re.findall(r"<img\b(?![^>]*\balt=)", joined, re.I)
        ),
        "responsive_evidence": len(
            re.findall(r"@media|\b(?:sm|md|lg|xl):", joined)
        ),
        "focus_evidence": len(
            re.findall(r"focus(?:-visible)?[:\-]", joined)
        ),
        "visual_tests": [
            _relative(root, path)
            for path in _matching_name(
                root,
                re.compile(
                    r"(?i)(visual|screenshot|accessibility|a11y).*\.(?:spec|test)\.(?:ts|js|tsx|jsx)$"
                ),
                100,
            )
        ],
        "playwright_config": bool(
            _matching_name(
                root,
                re.compile(r"playwright\.config\.(?:ts|js)$"),
                20,
            )
        ),
    }
    report["ready"] = (
        report["ui_files"] > 0
        and report["responsive_evidence"] > 0
        and report["aria_labels"] > 0
        and bool(report["visual_tests"])
    )
    return _artifact_result(
        workspace,
        "ux_quality.json",
        report,
        "SUCCESS" if report["ready"] else "PARTIAL",
        (
            f"UX quality analyzed {len(sources)} UI files; "
            f"complete evidence={report['ready']}."
        ),
    )


def _mobile_validation(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    report = _domain_report(
        root,
        {
            "android": (
                "android/build.gradle",
                "android/app/build.gradle",
                "gradlew",
            ),
            "ios": ("ios/Podfile", ".xcodeproj", ".xcworkspace"),
            "flutter": ("pubspec.yaml",),
            "react_native": ("app.json", "metro.config.js"),
            "mobile_tests": (
                "androidTest",
                "XCTest",
                "integration_test",
            ),
        },
    )
    return _domain_result(
        workspace, "mobile_validation.json", report, "mobile"
    )


def _game_validation(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    report = _domain_report(
        root,
        {
            "three_js": ("three", "@react-three/fiber"),
            "unity": ("ProjectSettings/ProjectVersion.txt", "Assets"),
            "godot": ("project.godot",),
            "game_loop": (
                "requestAnimationFrame",
                "_process(",
                "FixedUpdate(",
            ),
            "gameplay_tests": ("gameplay", "playtest", "physics test"),
            "assets": ("assets", "sprites", "textures", "models"),
        },
    )
    return _domain_result(
        workspace, "game_validation.json", report, "game"
    )


def _data_pipeline(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    report = _domain_report(
        root,
        {
            "orchestrator": ("airflow", "dagster", "prefect"),
            "lineage": ("lineage", "source_table", "target_table"),
            "quality": (
                "great_expectations",
                "pandera",
                "data quality",
            ),
            "idempotency": ("idempoten", "upsert", "merge into"),
            "backfill": ("backfill", "checkpoint", "watermark"),
            "schema": ("schema_registry", "avro", "parquet"),
        },
    )
    return _domain_result(
        workspace, "data_pipeline.json", report, "data pipeline"
    )


def _ml_evaluation(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    report = _domain_report(
        root,
        {
            "model_card": ("model card", "model_card"),
            "metrics": (
                "accuracy",
                "precision",
                "recall",
                "f1",
                "bleu",
                "rouge",
            ),
            "evaluation": ("evaluate", "eval_dataset", "benchmark"),
            "reproducibility": (
                "seed",
                "deterministic",
                "random_state",
            ),
            "drift": ("drift", "distribution shift"),
            "bias": ("bias", "fairness", "subgroup"),
        },
    )
    report["safety"] = {
        "training_executed": False,
        "models_modified": False,
        "datasets_modified": False,
    }
    return _domain_result(
        workspace, "ml_evaluation.json", report, "ML evaluation"
    )


def _infrastructure_validation(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    report = _domain_report(
        root,
        {
            "terraform": (".tf", "terraform"),
            "kubernetes": (
                "apiVersion:",
                "kind: Deployment",
                "kind: StatefulSet",
            ),
            "helm": ("Chart.yaml", "values.yaml"),
            "ci": (
                ".github/workflows",
                "gitlab-ci",
                "azure-pipelines",
            ),
            "policy": ("opa", "conftest", "checkov", "tfsec"),
            "state_backend": ('backend "', "remote_state"),
        },
    )
    report["dangerous_signals"] = _find_text(
        root,
        re.compile(
            r"(?i)privileged:\s*true|0\.0\.0\.0/0|hostNetwork:\s*true"
        ),
        100,
    )
    return _domain_result(
        workspace,
        "infrastructure_validation.json",
        report,
        "infrastructure",
    )


def _desktop_validation(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    report = _domain_report(
        root,
        {
            "electron": ("electron", "electron-builder"),
            "pyside": ("PySide6", "QMainWindow"),
            "tauri": ("tauri.conf.json", "src-tauri"),
            "installer": (
                "ANN_Setup.exe",
                "installer",
                "uninstaller",
            ),
            "single_instance": (
                "requestSingleInstanceLock",
                "QLockFile",
            ),
            "update": ("autoUpdater", "update manifest"),
            "accessibility": ("AccessibleName", "aria-label"),
        },
    )
    return _domain_result(
        workspace, "desktop_validation.json", report, "desktop"
    )


def _localization(
    _action: str, _payload: dict[str, Any], workspace: Path, root: Path
) -> dict[str, Any]:
    locale_files = [
        path
        for path in _source_files(
            root, {".json", ".po", ".pot", ".mo", ".ftl", ".arb"}
        )
        if re.search(
            r"(?i)(?:^|[\\/])(locales?|i18n|translations?)(?:[\\/]|$)",
            str(path),
        )
    ]
    sources = _source_files(
        root, {".tsx", ".jsx", ".ts", ".js", ".py", ".html"}
    )
    hardcoded: list[dict[str, object]] = []
    for path in sources[:1_000]:
        for line_number, line in enumerate(
            _read_text(path).splitlines(), 1
        ):
            if len(hardcoded) >= 200:
                break
            if re.search(
                r""">[A-Z][A-Za-z ]{4,}<|(?:label|title|placeholder)=["'][A-Z][^"']{3,}""",
                line,
            ):
                hardcoded.append(
                    {"path": _relative(root, path), "line": line_number}
                )
    report = {
        "locale_files": [
            _relative(root, path) for path in locale_files
        ],
        "locale_count": len(
            {path.parent.name for path in locale_files}
        ),
        "hardcoded_text_candidates": hardcoded,
        "pluralization_evidence": _find_text(
            root,
            re.compile(
                r"(?i)plural|pluralRules|_one\b|_other\b"
            ),
            100,
        ),
        "rtl_evidence": _find_text(
            root,
            re.compile(r"""(?i)\brtl\b|dir=["']rtl"""),
            100,
        ),
        "ready": bool(locale_files) and not hardcoded,
    }
    return _artifact_result(
        workspace,
        "localization.json",
        report,
        "SUCCESS" if report["ready"] else "PARTIAL",
        (
            f"Found {len(locale_files)} locale files and "
            f"{len(hardcoded)} hardcoded-text candidates."
        ),
    )


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _probe_integrations(
    payload: dict[str, Any], workspace: Path
) -> dict[str, Any]:
    urls = _string_list(payload.get("urls"), 10)
    allowed_domains, domains_valid = _allowed_domains(
        payload.get("allowed_domains"), 20, required=True
    )
    if not urls or not domains_valid:
        return _blocked("urls_and_allowed_domains_required")
    timeout = max(
        1, min(15, _int(payload.get("timeout_seconds"), 5))
    )
    opener = build_opener(_NoRedirect())
    results: list[dict[str, Any]] = []
    for raw in urls:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").lower().rstrip(".")
        allowed = _host_is_allowed(host, allowed_domains)
        if (
            parsed.scheme != "https"
            or not host
            or not allowed
            or parsed.username is not None
            or parsed.password is not None
            or bool(parsed.query)
            or bool(parsed.fragment)
        ):
            results.append(
                {
                    "url": raw,
                    "status": "BLOCKED",
                    "error": "domain_or_scheme_not_allowed",
                }
            )
            continue
        try:
            response = opener.open(
                Request(
                    raw,
                    method="HEAD",
                    headers={
                        "User-Agent": "ANN-Integration-Health/1.0"
                    },
                ),
                timeout=timeout,
            )
            results.append(
                {
                    "url": raw,
                    "status": "SUCCESS",
                    "http_status": int(response.status),
                    "content_type": response.headers.get(
                        "Content-Type", ""
                    ),
                }
            )
        except HTTPError as exc:
            results.append(
                {
                    "url": raw,
                    "status": "FAILED",
                    "http_status": int(exc.code),
                    "error": "http_error",
                }
            )
        except (URLError, TimeoutError, OSError) as exc:
            results.append(
                {
                    "url": raw,
                    "status": "FAILED",
                    "error": type(exc).__name__,
                }
            )
    report = {
        "allowed_domains": sorted(allowed_domains),
        "results": results,
        "credentials_sent": False,
        "redirects_followed": False,
    }
    status = (
        "SUCCESS"
        if results
        and all(item["status"] == "SUCCESS" for item in results)
        else "FAILED"
    )
    return _artifact_result(
        workspace,
        "integration_probe.json",
        report,
        status,
        f"Probed {len(results)} approved HTTPS endpoints.",
        internet_used=True,
    )


def _duckduckgo_destination(value: str) -> str:
    parsed = urlparse(value)
    query = parse_qs(parsed.query)
    destination = query.get("uddg", [""])[0]
    return destination or value


def _strip_html(value: str) -> str:
    without_tags = re.sub(r"(?s)<[^>]+>", " ", value)
    return " ".join(html.unescape(without_tags).split())


def _pypi_metadata(
    name: str, metadata: dict[str, Any]
) -> dict[str, Any]:
    info_value = metadata.get("info")
    info: dict[str, Any] = (
        info_value if isinstance(info_value, dict) else {}
    )
    releases_value = metadata.get("releases")
    releases: dict[str, Any] = (
        releases_value
        if isinstance(releases_value, dict)
        else {}
    )
    return {
        "name": str(info.get("name") or name),
        "latest_version": str(info.get("version") or ""),
        "summary": _bounded_text(info.get("summary"), 1_000),
        "license": _bounded_text(info.get("license"), 500),
        "requires_python": _bounded_text(
            info.get("requires_python"), 200
        ),
        "project_url": _bounded_text(
            info.get("project_url")
            or info.get("home_page"),
            2_000,
        ),
        "versions": sorted(
            (str(version) for version in releases),
            reverse=True,
        )[:50],
    }


def _npm_metadata(
    name: str, metadata: dict[str, Any]
) -> dict[str, Any]:
    dist_tags_value = metadata.get("dist-tags")
    dist_tags: dict[str, Any] = (
        dist_tags_value
        if isinstance(dist_tags_value, dict)
        else {}
    )
    versions_value = metadata.get("versions")
    versions: dict[str, Any] = (
        versions_value
        if isinstance(versions_value, dict)
        else {}
    )
    repository = metadata.get("repository")
    if isinstance(repository, dict):
        repository = repository.get("url")
    return {
        "name": str(metadata.get("name") or name),
        "latest_version": str(dist_tags.get("latest") or ""),
        "summary": _bounded_text(
            metadata.get("description"), 1_000
        ),
        "license": _bounded_text(metadata.get("license"), 500),
        "repository": _bounded_text(repository, 2_000),
        "versions": list(reversed(list(versions)[-50:])),
    }


def _artifact_result(
    workspace: Path,
    filename: str,
    data: dict[str, Any],
    status: str,
    summary: str,
    *,
    internet_used: bool = False,
) -> dict[str, Any]:
    path = _write_json(workspace / filename, data, workspace)
    return {
        "status": status,
        "summary": summary,
        "data": data,
        "artifacts": [str(path)],
        "internet_used": internet_used,
    }


def _domain_result(
    workspace: Path,
    filename: str,
    report: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    covered = sum(
        1 for value in report["signals"].values() if value
    )
    report["coverage_count"] = covered
    report["ready"] = covered >= max(
        2, len(report["signals"]) // 2
    )
    return _artifact_result(
        workspace,
        filename,
        report,
        "SUCCESS" if report["ready"] else "PARTIAL",
        (
            f"{label.title()} validation covered "
            f"{covered}/{len(report['signals'])} evidence groups."
        ),
    )


def _domain_report(
    root: Path, groups: dict[str, tuple[str, ...]]
) -> dict[str, Any]:
    searchable = [
        path
        for path in _source_files(
            root,
            {
                ".py",
                ".ts",
                ".tsx",
                ".js",
                ".jsx",
                ".json",
                ".toml",
                ".yaml",
                ".yml",
                ".md",
                ".tf",
                ".gradle",
                ".cs",
                ".gd",
            },
        )
        if path.stat().st_size <= 500_000
    ]
    names = "\n".join(
        _relative(root, path) for path in searchable
    ).lower()
    text = "\n".join(
        _read_text(path, 100_000) for path in searchable[:1_000]
    ).lower()
    signals = {
        name: sorted(
            {
                term
                for term in terms
                if term.lower() in names or term.lower() in text
            }
        )
        for name, terms in groups.items()
    }
    return {
        "project_root": str(root),
        "signals": signals,
        "files_scanned": len(searchable),
    }


def _dependency_manifests(root: Path) -> list[str]:
    names = {
        "pyproject.toml",
        "requirements.txt",
        "Pipfile",
        "Pipfile.lock",
        "poetry.lock",
        "uv.lock",
        "requirements.lock",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lockb",
        "Cargo.toml",
        "Cargo.lock",
        "go.mod",
        "go.sum",
        "pom.xml",
        "build.gradle",
        "pubspec.yaml",
        "pubspec.lock",
    }
    return sorted(
        _relative(root, path)
        for path in _walk(root)
        if path.name in names
    )


def _unbounded_dependency_specs(root: Path) -> list[str]:
    risks: list[str] = []
    for path in _walk(root):
        if path.name == "requirements.txt":
            for line in _read_text(path).splitlines():
                clean = line.strip()
                if (
                    clean
                    and not clean.startswith("#")
                    and not re.search(
                        r"(?:==|===|@\s*https?://)", clean
                    )
                ):
                    risks.append(
                        f"{_relative(root, path)}:{clean[:120]}"
                    )
        elif path.name == "package.json":
            payload = _read_json(path)
            for group in (
                "dependencies",
                "devDependencies",
                "optionalDependencies",
            ):
                entries = payload.get(group)
                if not isinstance(entries, dict):
                    continue
                for name, version in entries.items():
                    if str(version).strip() in {
                        "*",
                        "latest",
                        "next",
                    }:
                        risks.append(
                            f"{_relative(root, path)}:{name}@{version}"
                        )
    return risks[:500]


def _docker_images(root: Path) -> list[str]:
    images: set[str] = set()
    for path in _walk(root):
        if path.name.lower().startswith("dockerfile"):
            images.update(
                match.strip()
                for match in re.findall(
                    r"(?im)^\s*FROM\s+([^\s]+)", _read_text(path)
                )
            )
        elif path.name in {
            "compose.yaml",
            "compose.yml",
            "docker-compose.yaml",
            "docker-compose.yml",
        }:
            images.update(
                match.strip()
                for match in re.findall(
                    r"(?im)^\s*image:\s*([^\s#]+)",
                    _read_text(path),
                )
            )
    return sorted(images)


def _dependency_cycles(graph: object) -> list[list[str]]:
    if not isinstance(graph, dict):
        return []
    raw = graph.get("edges", graph)
    adjacency: dict[str, set[str]] = defaultdict(set)
    if isinstance(raw, list):
        for edge in raw:
            if (
                isinstance(edge, dict)
                and edge.get("source")
                and edge.get("target")
            ):
                adjacency[str(edge["source"])].add(
                    str(edge["target"])
                )
    elif isinstance(raw, dict):
        for source, targets in raw.items():
            if isinstance(targets, list):
                adjacency[str(source)].update(
                    str(item) for item in targets
                )
    cycles: set[tuple[str, ...]] = set()

    def visit(
        node: str, path: list[str], active: set[str]
    ) -> None:
        if len(path) > 20 or len(cycles) >= 100:
            return
        for target in adjacency.get(node, set()):
            if target in active:
                start = path.index(target) if target in path else 0
                cycles.add(tuple(path[start:] + [target]))
            else:
                visit(
                    target,
                    [*path, target],
                    {*active, target},
                )

    for node in list(adjacency)[:2_000]:
        visit(node, [node], {node})
    return [list(item) for item in sorted(cycles)[:100]]


def _duplicate_sources(root: Path) -> list[list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for path in _source_files(
        root,
        {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".cs"},
    ):
        text = re.sub(r"\s+", " ", _read_text(path)).strip()
        if len(text) >= 400:
            digest = hashlib.sha256(
                text.encode("utf-8")
            ).hexdigest()
            groups[digest].append(_relative(root, path))
    return [
        paths for paths in groups.values() if len(paths) > 1
    ][:100]


def _contract_statements(text: str) -> list[str]:
    lines = []
    for chunk in re.split(
        r"[\r\n]+|(?<=[.!?])\s+", text
    ):
        clean = re.sub(
            r"^\s*(?:[-*]|\d+[.)])\s*", "", chunk
        ).strip()
        if clean:
            lines.append(clean[:2_000])
    return _dedupe(lines)[:100]


def _is_constraint(value: str) -> bool:
    return bool(
        re.search(
            r"(?i)\b(?:must|never|only|without|prohibited|required|local|windows|linux|docker|security|privacy)\b",
            value,
        )
    )


def _package_scripts(
    root: Path, names: set[str]
) -> dict[str, str]:
    payload = _read_json(root / "package.json")
    scripts_value = payload.get("scripts")
    scripts: dict[str, Any] = (
        scripts_value
        if isinstance(scripts_value, dict)
        else {}
    )
    return {
        str(name): str(command)
        for name, command in scripts.items()
        if str(name).lower() in names
    }


def _declared_ports(root: Path) -> list[str]:
    values: set[str] = set()
    for path in _walk(root):
        if path.name in {
            "compose.yaml",
            "compose.yml",
            "docker-compose.yaml",
            "docker-compose.yml",
            ".env",
            ".env.example",
        }:
            text = _read_text(path)
            values.update(
                re.findall(
                    r"(?<!\d)(?:127\.0\.0\.1:)?\d{2,5}:\d{2,5}(?!\d)",
                    text,
                )
            )
            values.update(
                re.findall(
                    r"(?im)^\s*[A-Z0-9_]*PORT\s*=\s*(\d{2,5})\s*$",
                    text,
                )
            )
    return sorted(values)


def _load_average() -> list[float]:
    getloadavg = getattr(os, "getloadavg", None)
    if not callable(getloadavg):
        return []
    try:
        return [round(value, 3) for value in getloadavg()]
    except OSError:
        return []


def _matching_files(
    root: Path, suffixes: set[str], limit: int
) -> list[Path]:
    if not root.is_dir():
        return []
    return [
        path
        for path in _walk(root)
        if path.suffix.lower() in suffixes
    ][:limit]


def _matching_name(
    root: Path, pattern: re.Pattern[str], limit: int
) -> list[Path]:
    return [
        path for path in _walk(root) if pattern.search(path.name)
    ][:limit]


def _find_named(root: Path, names: set[str]) -> list[Path]:
    lowered = {name.lower() for name in names}
    return [
        path for path in _walk(root) if path.name.lower() in lowered
    ]


def _find_text(
    root: Path, pattern: re.Pattern[str], limit: int
) -> list[str]:
    evidence: list[str] = []
    suffixes = {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".json",
        ".toml",
        ".yaml",
        ".yml",
        ".md",
        ".txt",
        ".tf",
        ".css",
        ".html",
    }
    for path in _source_files(root, suffixes):
        for line_number, line in enumerate(
            _read_text(path).splitlines(), 1
        ):
            if pattern.search(line):
                evidence.append(
                    f"{_relative(root, path)}:{line_number}"
                )
                if len(evidence) >= limit:
                    return evidence
    return evidence


def _source_files(
    root: Path, suffixes: set[str]
) -> list[Path]:
    return [
        path
        for path in _walk(root)
        if path.suffix.lower() in suffixes
        and path.stat().st_size <= MAX_TEXT
    ]


def _walk(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory, names, filenames in os.walk(root):
        names[:] = [
            name
            for name in names
            if name.lower() not in EXCLUDED_PARTS
        ]
        current = Path(directory)
        for filename in filenames:
            path = current / filename
            if not any(
                part.lower() in EXCLUDED_PARTS
                for part in path.relative_to(root).parts
            ):
                files.append(path)
                if len(files) >= MAX_FILES:
                    return files
    return files


def _is_test(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return (
        "/test" in normalized
        or "/__tests__/" in normalized
        or re.search(
            r"(?:^|/)(?:test_|.*\.(?:test|spec)\.)",
            normalized,
        )
        is not None
    )


def _safe_existing_directory(
    value: object, root: Path
) -> Path | None:
    raw = str(value or "").strip()
    if not raw or ".." in raw.replace("\\", "/").split("/"):
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved if resolved.is_dir() else None


def _first_existing(
    root: Path, names: tuple[str, ...]
) -> Path | None:
    return next(
        (root / name for name in names if (root / name).is_file()),
        None,
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(_read_text(path))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _read_text(
    path: Path | None, limit: int = MAX_TEXT
) -> str:
    if path is None or not path.is_file():
        return ""
    try:
        return path.read_text(
            encoding="utf-8", errors="replace"
        )[:limit]
    except OSError:
        return ""


def _write_json(
    path: Path, value: object, workspace: Path
) -> Path:
    safe = cast(Path, validate_workspace_path(path, workspace))
    safe.parent.mkdir(
        parents=True, exist_ok=True
    )  # lgtm[py/path-injection]
    safe.write_text(  # lgtm[py/path-injection]
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )
    return safe


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024), b""
        ):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(root: Path, path: Path) -> str:
    try:
        return (
            path.resolve()
            .relative_to(root.resolve())
            .as_posix()
        )
    except ValueError:
        return path.name


def _bounded_text(
    value: object, limit: int = MAX_TEXT
) -> str:
    return str(value or "")[:limit]


def _string_list(value: object, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        str(item).strip()[:2_000]
        for item in value[:limit]
        if str(item).strip()
    ]


def _allowed_domains(
    value: object, limit: int, *, required: bool
) -> tuple[set[str], bool]:
    raw = _string_list(value, limit)
    if not raw:
        return set(), not required
    domains = {
        item.lower().rstrip(".")
        for item in raw
        if _is_public_domain(item.lower().rstrip("."))
    }
    return domains, len(domains) == len(raw)


def _is_public_domain(value: str) -> bool:
    if len(value) > 253 or "." not in value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        return False
    return all(
        re.fullmatch(
            r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
            label,
        )
        is not None
        for label in value.split(".")
    )


def _host_is_allowed(host: str, domains: set[str]) -> bool:
    return any(
        host == domain or host.endswith(f".{domain}")
        for domain in domains
    )


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _int(value: object, default: int) -> int:
    try:
        if isinstance(value, (str, bytes, bytearray, int, float)):
            return int(value)
        return default
    except (TypeError, ValueError):
        return default


def _blocked(error: str) -> dict[str, Any]:
    return {
        "status": "BLOCKED",
        "summary": error.replace("_", " "),
        "errors": [error],
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
