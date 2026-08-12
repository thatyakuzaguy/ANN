"""Run ANN autonomous capability scenarios through the existing project builder.

This is a thin wrapper around ``run_end_to_end_project``. It is not a new
pipeline and does not bypass approval gates. Scenario execution requires
``--execute`` plus the same project-builder confirmations and approval token.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
for package_root in (
    ".",
    "packages/agents",
    "packages/orchestration",
    "packages/sandbox",
    "packages/git",
    "packages/logs",
    "packages/shared",
    "packages/database",
    "packages/security",
    "apps/api",
):
    candidate = str(REPO_ROOT / package_root)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from agentic_network.project_builder_orchestrator.runtime import run_end_to_end_project  # noqa: E402
from agentic_network.project_builder_orchestrator.capability_evidence import (  # noqa: E402
    evaluate_project_capability,
)
from agentic_network.project_builder_orchestrator.lifecycle_evidence import (  # noqa: E402
    write_lifecycle_capability_summary,
)
from agentic_network.runtime_engine.local_model_activation import (  # noqa: E402
    build_autonomous_capability_evidence_plan,
)

DEFAULT_EVIDENCE_ROOT = REPO_ROOT / "outputs" / "autonomous_capability"
DEFAULT_TARGET_ROOT = REPO_ROOT / "outputs" / "autonomous_capability_projects"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ANN autonomous capability scenarios.")
    parser.add_argument("--scenario", action="append", help="Scenario id to run. Omit to run all scenarios.")
    parser.add_argument("--evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--target-root", default=str(DEFAULT_TARGET_ROOT))
    parser.add_argument("--approval-token", default=None)
    parser.add_argument("--max-features", type=int, default=5)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument(
        "--api-base",
        default=None,
        help="Use the existing real sequential run API instead of the legacy project-builder adapter.",
    )
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--max-run-seconds", type=int, default=2400)
    parser.add_argument("--execute", action="store_true", help="Actually run scenarios and write evidence.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    plan = build_autonomous_capability_evidence_plan(args.evidence_root)
    selected = _selected_scenarios(plan["scenarios"], args.scenario)
    if not args.execute:
        print(_plan_summary(plan, selected))
        return 0
    evidence_root = Path(args.evidence_root).resolve()
    target_root = Path(args.target_root).resolve()
    results = []
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    for scenario in selected:
        scenario_dir = evidence_root / scenario["id"]
        scenario_dir.mkdir(parents=True, exist_ok=True)
        if args.api_base:
            summary = _run_api_scenario(
                scenario,
                api_base=args.api_base.rstrip("/"),
                workspace=target_root / scenario["id"] / run_id,
                scenario_dir=scenario_dir,
                allowed_workspace_root=target_root,
                poll_seconds=max(0.25, args.poll_seconds),
                max_run_seconds=max(1, args.max_run_seconds),
            )
        else:
            result = run_end_to_end_project(
                idea=scenario["prompt"],
                target_root=target_root / scenario["id"] / run_id,
                project_name=scenario["id"],
                approval_token=args.approval_token,
                max_features=args.max_features,
                max_retries=args.max_retries,
                confirm_create=True,
                confirm_apply=True,
                confirm_tests=True,
                generate_tests_if_missing=True,
            )
            summary = _summary_from_result(scenario, result)
        (scenario_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (scenario_dir / "summary.md").write_text(_summary_markdown(summary), encoding="utf-8")
        results.append(summary)
    complete = all(item["status"] == "COMPLETED_VERIFIED" and item["security_review"] == "PASSED" for item in results)
    print(
        "\n".join(
            [
                "ANN Autonomous Capability Scenario Execution",
                f"Scenarios Run: {len(results)}",
                f"Completed Verified: {sum(1 for item in results if item['status'] == 'COMPLETED_VERIFIED')}",
                f"Status: {'SCENARIOS_VERIFIED' if complete else 'SCENARIOS_REQUIRE_REVIEW'}",
                f"Evidence Root: {evidence_root}",
            ]
        )
    )
    return 0 if complete else 2


def _selected_scenarios(scenarios: list[dict[str, Any]], requested: list[str] | None) -> list[dict[str, Any]]:
    if not requested:
        return scenarios
    by_id = {item["id"]: item for item in scenarios}
    missing = sorted(set(requested) - set(by_id))
    if missing:
        raise SystemExit(f"Unknown scenario id(s): {', '.join(missing)}")
    return [by_id[item] for item in requested]


def _plan_summary(plan: dict[str, Any], selected: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "ANN Autonomous Capability Scenario Plan",
            f"Evidence Status: {plan['status']}",
            f"Selected Scenarios: {len(selected)}",
            "Execute: false",
            "Pass --execute with valid project-builder approval tokens to run.",
        ]
    )


def _summary_from_result(scenario: dict[str, Any], result: Any) -> dict[str, Any]:
    payload = result.to_dict()
    verification = payload.get("verification_evidence") or {}
    commands_executed = verification.get("commands_executed")
    if not isinstance(commands_executed, list):
        commands_executed = []
    summary = {
        "scenario_id": scenario["id"],
        "prompt": scenario["prompt"],
        "status": payload.get("status"),
        "completion_quality": payload.get("completion_quality"),
        "project_root": payload.get("project_root"),
        "verification_evidence": verification,
        "commands_executed": commands_executed,
        "security_review": "REVIEW_REQUIRED",
        "security_review_basis": "independent security evidence required",
        "protected_paths_modified": False,
        "validation_errors": payload.get("validation_errors", []),
        "artifacts": payload.get("artifacts", []),
        "model_routing_status": payload.get("model_routing_status"),
        "next_action": payload.get("next_action"),
        "no_fake_success": True,
    }
    capability = evaluate_project_capability(scenario["id"], summary)
    summary["capability_assessment"] = capability
    if capability.get("security_status") == "PASSED":
        summary["security_review"] = "PASSED"
        summary["security_review_basis"] = "independent security_review.json"
    if not capability["passed"] and summary["status"] == "COMPLETED_VERIFIED":
        summary["status"] = "CAPABILITY_EVIDENCE_BLOCKED"
        summary["completion_quality"] = "REVIEW_REQUIRED"
        summary["next_action"] = "complete_independent_capability_evidence"
    return summary


def _run_api_scenario(
    scenario: dict[str, Any],
    *,
    api_base: str,
    workspace: Path,
    scenario_dir: Path,
    allowed_workspace_root: Path,
    poll_seconds: float,
    max_run_seconds: int,
) -> dict[str, Any]:
    workspace.mkdir(parents=True, exist_ok=True)
    created = _post_json(
        f"{api_base}/runs",
        {
            "idea": scenario["prompt"],
            "workspace_directory": str(workspace),
            "approval_mode": "full",
        },
    )
    api_run_id = str(created["run_id"])
    record, telemetry = _wait_for_api_run(
        api_base,
        api_run_id,
        poll_seconds=poll_seconds,
        max_run_seconds=max_run_seconds,
    )
    execution = record.get("execution_results")
    execution = execution if isinstance(execution, dict) else {}
    display_root = execution.get("display_root")
    project_root = Path(str(display_root)).resolve() if display_root else workspace
    lifecycle_path = project_root / ".aen" / "real-lifecycle-result.json"
    visual = {"status": "NOT_REQUIRED", "screenshots": [], "log": None}
    errors: list[str] = []
    if str(record.get("status", "")).lower() != "completed":
        errors.append(f"api_run_status:{record.get('status')}")
    if str(execution.get("status", "")).lower() != "passed":
        errors.append(f"lifecycle_status:{execution.get('status')}")
    if not lifecycle_path.is_file():
        errors.append(f"immutable_lifecycle_result_missing:{lifecycle_path}")
    if int(telemetry.get("peak_active_models", 0)) > 1:
        errors.append(f"active_models_policy_violation:{telemetry['peak_active_models']}")
    if int(telemetry.get("peak_parallel_llm_loads", 0)) != 0:
        errors.append(f"parallel_llm_loads_policy_violation:{telemetry['peak_parallel_llm_loads']}")
    if int(telemetry.get("active_models_after", 0)) != 0:
        errors.append(f"model_rollback_failed:{telemetry['active_models_after']}")

    if not errors and str(execution.get("profile")) != "algorithm_service":
        visual = _capture_visual_evidence(project_root, str(execution.get("sandbox_id") or api_run_id[:8]))
        if visual["status"] != "PASSED":
            errors.append("host_visual_evidence_failed")

    if lifecycle_path.is_file():
        summary = write_lifecycle_capability_summary(
            str(scenario["id"]),
            project_root,
            scenario_dir,
            allowed_workspace_root=allowed_workspace_root,
            lifecycle_result_path=lifecycle_path,
        )
    else:
        summary = {
            "scenario_id": scenario["id"],
            "status": "CAPABILITY_EVIDENCE_BLOCKED",
            "completion_quality": "REVIEW_REQUIRED",
            "project_root": str(project_root),
            "generated_project_path": str(project_root),
            "artifacts": [],
            "commands_executed": [],
            "verification_evidence": {"evidence_level": "INSUFFICIENT", "logs": [], "screenshots": []},
            "security_review": "REVIEW_REQUIRED",
            "protected_paths_modified": False,
            "write_boundary": str(allowed_workspace_root),
        }
    summary.update(
        {
            "prompt": scenario["prompt"],
            "api_run_id": api_run_id,
            "api_run_status": record.get("status"),
            "runtime_telemetry": telemetry,
            "host_visual_verification": visual,
            "validation_errors": errors,
            "no_fake_success": True,
        }
    )
    if errors:
        summary["status"] = "CAPABILITY_EVIDENCE_BLOCKED"
        summary["completion_quality"] = "REVIEW_REQUIRED"
        summary["next_action"] = "resolve_real_lifecycle_or_visual_evidence_failure"
    else:
        summary["next_action"] = (
            "completed_verified" if summary.get("status") == "COMPLETED_VERIFIED" else "review_capability_assessment"
        )
    return summary


def _wait_for_api_run(
    api_base: str,
    run_id: str,
    *,
    poll_seconds: float,
    max_run_seconds: int,
) -> tuple[dict[str, Any], dict[str, int]]:
    deadline = time.monotonic() + max_run_seconds
    record: dict[str, Any] = {"run_id": run_id, "status": "running"}
    peak_active = 0
    peak_parallel = 0
    while time.monotonic() < deadline:
        record = _get_json(f"{api_base}/runs/{run_id}")
        metrics = _get_json(f"{api_base}/runtime/provider-metrics")
        peak_active = max(
            peak_active,
            int(metrics.get("active_models", 0)),
            int(metrics.get("peak_active_models", 0)),
        )
        peak_parallel = max(
            peak_parallel,
            int(metrics.get("parallel_llm_loads", 0)),
            int(metrics.get("peak_parallel_llm_loads", 0)),
        )
        if str(record.get("status", "")).lower() in {"completed", "failed", "blocked", "interrupted"}:
            break
        time.sleep(poll_seconds)
    else:
        record = {**record, "status": "timed_out", "error": "run_timeout"}
    metrics_after = _get_json(f"{api_base}/runtime/provider-metrics")
    return record, {
        "peak_active_models": max(peak_active, int(metrics_after.get("peak_active_models", 0))),
        "peak_parallel_llm_loads": max(peak_parallel, int(metrics_after.get("peak_parallel_llm_loads", 0))),
        "active_models_after": int(metrics_after.get("active_models", 0)),
        "parallel_llm_loads_after": int(metrics_after.get("parallel_llm_loads", 0)),
        "unload_failures": int(metrics_after.get("unload_failures", 0)),
    }


def _capture_visual_evidence(project_root: Path, sandbox_id: str) -> dict[str, Any]:
    web_root = project_root / "apps" / "web"
    log_path = project_root / ".aen" / "host-visual-e2e.log"
    if not (project_root / "docker-compose.yml").is_file() or not web_root.is_dir():
        return {"status": "FAILED", "screenshots": [], "log": str(log_path), "error": "web_project_missing"}
    started_ns = time.time_ns()
    env = os.environ.copy()
    env["COMPOSE_PROJECT_NAME"] = sandbox_id
    command = ["docker", "compose", "--profile", "test", "run", "--rm", "--no-deps", "e2e"]
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            check=False,
        )
        output = f"$ {' '.join(command)}\n{completed.stdout}\n{completed.stderr}".strip() + "\n"
        log_path.write_text(output, encoding="utf-8")
    except (OSError, subprocess.TimeoutExpired) as exc:
        log_path.write_text(f"Visual E2E execution failed: {exc}\n", encoding="utf-8")
        return {"status": "FAILED", "screenshots": [], "log": str(log_path), "error": str(exc)}
    finally:
        subprocess.run(
            ["docker", "compose", "--profile", "test", "down", "-v"],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    screenshots = sorted(
        str(path.resolve())
        for base in (web_root / "test-results", web_root / "playwright-report")
        if base.is_dir()
        for path in base.rglob("*.png")
        if path.is_file() and path.stat().st_size >= 100 and path.stat().st_mtime_ns >= started_ns
    )
    return {
        "status": "PASSED" if completed.returncode == 0 and screenshots else "FAILED",
        "exit_code": completed.returncode,
        "command": command,
        "screenshots": screenshots,
        "log": str(log_path),
    }


def _get_json(url: str) -> dict[str, Any]:
    return _request_json(Request(url, method="GET"))


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _request_json(
        Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
    )


def _request_json(request: Request) -> dict[str, Any]:
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - local API URL is explicit CLI input
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"ANN API request failed for {request.full_url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"ANN API returned a non-object payload for {request.full_url}")
    return payload


def _summary_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {summary['scenario_id']}",
            "",
            f"- Status: {summary['status']}",
            f"- Completion quality: {summary['completion_quality']}",
            f"- Security review: {summary['security_review']}",
            f"- Commands executed: {len(summary['commands_executed'])}",
            f"- Project root: {summary['project_root']}",
            f"- Next action: {summary['next_action']}",
            "",
        ]
    )


if __name__ == "__main__":
    sys.exit(main())
