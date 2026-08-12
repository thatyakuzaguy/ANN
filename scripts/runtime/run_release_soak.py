"""Run ANN's prolonged, real-project release soak against the local API.

The runner never marks a campaign as passing from elapsed time alone. Every
counted attempt must traverse the real run API, approval mode, generated
project lifecycle, Docker build, live health checks, tests, packaging, and
model unload telemetry. State is written atomically so a host restart can
resume the campaign without discarding earlier attempts.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CASES = (
    {
        "id": "saas-task-platform",
        "archetype": "saas",
        "prompt": (
            "Build a production-oriented SaaS task platform with FastAPI, PostgreSQL, "
            "JWT authentication, tenant isolation, React UI, tests, documentation, and Docker."
        ),
    },
    {
        "id": "web-incident-console",
        "archetype": "web_application",
        "prompt": (
            "Build a full-stack incident response web application with typed FastAPI APIs, "
            "a React operations console, audit history, tests, accessibility checks, and Docker."
        ),
    },
    {
        "id": "route-optimization-service",
        "archetype": "algorithm_service",
        "prompt": (
            "Build a route optimization algorithm service with a FastAPI endpoint, explicit "
            "complexity constraints, benchmarks, edge-case tests, integration tests, and Docker."
        ),
    },
)

FULL_STACK_LIVE_STEPS = {
    "docker_compose_build",
    "docker_compose_up",
    "api_health_live",
    "web_health_live",
    "api_pytest_live",
    "web_unit_live",
    "web_build_live",
    "web_e2e_live",
    "docker_compose_down",
}
ALGORITHM_LIVE_STEPS = {
    "docker_compose_build",
    "docker_compose_up",
    "api_health_live",
    "api_pytest_live",
    "algorithm_integration_live",
    "algorithm_benchmark_live",
    "docker_compose_down",
}
TERMINAL_STATUSES = {"completed", "failed", "blocked", "interrupted"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the real ANN release soak.")
    parser.add_argument("--api-base", default="http://127.0.0.1:18000/api")
    parser.add_argument("--workspace-root", default=r"E:\ANN-Soak\workspaces")
    parser.add_argument("--evidence-root", default=r"E:\ANN-Soak\evidence")
    parser.add_argument("--duration-hours", type=float, default=8.0)
    parser.add_argument("--min-runs", type=int, default=20)
    parser.add_argument("--poll-seconds", type=float, default=3.0)
    parser.add_argument("--max-run-seconds", type=int, default=2400)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument(
        "--case-id",
        choices=tuple(str(case["id"]) for case in CASES),
        help="Run one named archetype during preflight. Official campaigns always rotate all cases.",
    )
    parser.add_argument("--continue-on-failure", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.case_id and not args.preflight:
        raise SystemExit("--case-id is only allowed with --preflight.")
    if not args.preflight and (args.duration_hours < 8 or args.min_runs < 20):
        raise SystemExit("Official soak requires at least 8 hours and 20 runs.")
    workspace_root = Path(args.workspace_root).resolve()
    evidence_root = Path(args.evidence_root).resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    session_dir = evidence_root / ("preflight" if args.preflight else "official")
    session_dir.mkdir(parents=True, exist_ok=True)
    state_path = session_dir / "campaign_state.json"
    state = _load_or_create_state(
        state_path,
        duration_hours=args.duration_hours,
        min_runs=1 if args.preflight else args.min_runs,
        preflight=args.preflight,
    )
    _require_api_ready(args.api_base)
    baseline = _get_json(f"{args.api_base}/runtime/provider-metrics")
    state.setdefault("provider_baseline", baseline)
    target_runs = 1 if args.preflight else args.min_runs
    interval_seconds = 0.0 if args.preflight else args.duration_hours * 3600 / target_runs
    session_started = time.monotonic()
    base_active_seconds = _infer_active_elapsed_seconds(state, interval_seconds)
    state["active_elapsed_seconds"] = base_active_seconds
    state["last_resumed_at"] = _utc_now()
    _atomic_json(state_path, state)

    while len(state["runs"]) < target_runs:
        if (session_dir / "STOP").exists():
            state["status"] = "STOPPED_BY_OPERATOR"
            _atomic_json(state_path, state)
            break
        attempt = len(state["runs"]) + 1
        case = _case_for_attempt(attempt, case_id=args.case_id)
        scheduled_active_seconds = interval_seconds * (attempt - 1)
        scheduled = session_started + max(0.0, scheduled_active_seconds - base_active_seconds)
        _wait_until(
            scheduled,
            session_dir,
            state,
            state_path,
            base_active_seconds=base_active_seconds,
            session_started=session_started,
        )
        if (session_dir / "STOP").exists():
            state["status"] = "STOPPED_BY_OPERATOR"
            _update_active_elapsed(state, base_active_seconds, session_started)
            _atomic_json(state_path, state)
            break
        run = _execute_attempt(
            api_base=args.api_base,
            workspace_root=workspace_root,
            case=case,
            attempt=attempt,
            poll_seconds=max(1.0, args.poll_seconds),
            max_run_seconds=args.max_run_seconds,
        )
        state["runs"].append(run)
        state["gpu_peak_vram_mb"] = max(
            int(state.get("gpu_peak_vram_mb", 0)), int(run.get("gpu_peak_vram_mb", 0))
        )
        state["provider_metrics"] = run["provider_metrics_after"]
        _update_active_elapsed(state, base_active_seconds, session_started)
        _atomic_json(session_dir / f"attempt_{attempt:03d}.json", run)
        _atomic_json(state_path, state)
        print(
            f"attempt={attempt} case={case['id']} status={run['status']} "
            f"duration={run['duration_seconds']:.1f}s",
            flush=True,
        )
        if run["status"] != "PASSED" and not args.continue_on_failure:
            state["status"] = "FAILED_EARLY"
            _atomic_json(state_path, state)
            break

    if not args.preflight and len(state["runs"]) >= target_runs:
        campaign_end = session_started + max(
            0.0, args.duration_hours * 3600 - base_active_seconds
        )
        _wait_until(
            campaign_end,
            session_dir,
            state,
            state_path,
            base_active_seconds=base_active_seconds,
            session_started=session_started,
        )

    final_metrics = _get_json(f"{args.api_base}/runtime/provider-metrics")
    state["provider_metrics"] = final_metrics
    _update_active_elapsed(state, base_active_seconds, session_started)
    state["finished_at"] = _utc_now()
    report = build_campaign_report(state, preflight=args.preflight)
    finalize_campaign_state(state, report)
    if args.preflight:
        _atomic_json(session_dir / "preflight_result.json", report)
        (session_dir / "preflight_result.md").write_text(
            _report_markdown(report, title="ANN Release Soak Preflight"), encoding="utf-8"
        )
    else:
        report_path = session_dir / "soak_validation_report.md"
        report_path.write_text(_report_markdown(report), encoding="utf-8")
        evidence = build_assurance_evidence(report, report_path)
        _atomic_json(session_dir / "soak_validation.json", evidence)
    _atomic_json(state_path, state)
    print(json.dumps(report, indent=2), flush=True)
    return 0 if report["status"] == "PASSED" else 2


def _case_for_attempt(attempt: int, *, case_id: str | None = None) -> dict[str, str]:
    if case_id is not None:
        return next(case for case in CASES if case["id"] == case_id)
    return CASES[(attempt - 1) % len(CASES)]


def _execute_attempt(
    *,
    api_base: str,
    workspace_root: Path,
    case: dict[str, str],
    attempt: int,
    poll_seconds: float,
    max_run_seconds: int,
) -> dict[str, Any]:
    started = time.monotonic()
    workspace = workspace_root / f"attempt-{attempt:03d}-{case['id']}"
    workspace.mkdir(parents=True, exist_ok=True)
    metrics_before = _get_json(f"{api_base}/runtime/provider-metrics")
    created = _post_json(
        f"{api_base}/runs",
        {
            "idea": case["prompt"],
            "workspace_directory": str(workspace),
            "approval_mode": "full",
        },
    )
    run_id = str(created["run_id"])
    peak_vram = 0
    peak_active = 0
    peak_parallel = 0
    deadline = started + max_run_seconds
    record = created
    while time.monotonic() < deadline:
        record = _get_json(f"{api_base}/runs/{run_id}")
        metrics = _get_json(f"{api_base}/runtime/provider-metrics")
        peak_active = max(peak_active, int(metrics.get("active_models", 0)))
        peak_parallel = max(peak_parallel, int(metrics.get("parallel_llm_loads", 0)))
        peak_vram = max(peak_vram, _gpu_memory_used_mb())
        if str(record.get("status", "")).lower() in TERMINAL_STATUSES:
            break
        time.sleep(poll_seconds)
    else:
        record = {**record, "status": "timed_out", "error": "run_timeout"}

    metrics_after = _get_json(f"{api_base}/runtime/provider-metrics")
    loads = max(
        0,
        int(metrics_after.get("total_loads", 0))
        - int(metrics_before.get("total_loads", 0)),
    )
    unloads = max(
        0,
        int(metrics_after.get("total_unloads", 0))
        - int(metrics_before.get("total_unloads", 0)),
    )
    unload_failures = max(
        0,
        int(metrics_after.get("unload_failures", 0))
        - int(metrics_before.get("unload_failures", 0)),
    )
    # A completed load event proves an active-model peak even when a fast load
    # and unload occurs between polling intervals.
    observed_peak_active = max(peak_active, 1 if loads else 0)
    passed, failures, step_statuses = evaluate_run_record(record, str(case["archetype"]))
    if loads == 0:
        failures.append("provider_model_load_missing")
    if unloads < loads:
        failures.append(f"provider_unload_count:{unloads}/{loads}")
    if observed_peak_active != 1:
        failures.append(f"provider_peak_active_models:{observed_peak_active}")
    if peak_parallel != 0:
        failures.append(f"provider_parallel_llm_loads:{peak_parallel}")
    if int(metrics_after.get("active_models", 0)) != 0:
        failures.append("models_still_loaded_after_run")
    if unload_failures != 0:
        failures.append("provider_unload_failure")
    passed = passed and not failures
    return {
        "attempt": attempt,
        "case_id": case["id"],
        "archetype": case["archetype"],
        "run_id": run_id,
        "status": "PASSED" if passed else "FAILED",
        "ann_status": record.get("status"),
        "duration_seconds": round(time.monotonic() - started, 3),
        "workspace": str(workspace),
        "display_project_root": _execution(record).get("display_root"),
        "release_package": _execution(record).get("release_package"),
        "step_statuses": step_statuses,
        "failures": failures,
        "gpu_peak_vram_mb": peak_vram,
        "provider_peak_active_models": observed_peak_active,
        "provider_peak_parallel_llm_loads": peak_parallel,
        "provider_loads": loads,
        "provider_unloads": unloads,
        "provider_unload_failures": unload_failures,
        "provider_metrics_before": metrics_before,
        "provider_metrics_after": metrics_after,
        "completed_at": _utc_now(),
    }


def evaluate_run_record(
    record: dict[str, Any], archetype: str
) -> tuple[bool, list[str], dict[str, str]]:
    execution = _execution(record)
    steps = execution.get("steps") if isinstance(execution.get("steps"), list) else []
    statuses = {
        str(item.get("name", "")): str(item.get("status", "")).lower()
        for item in steps
        if isinstance(item, dict)
    }
    required = ALGORITHM_LIVE_STEPS if archetype == "algorithm_service" else FULL_STACK_LIVE_STEPS
    failures: list[str] = []
    if str(record.get("status", "")).lower() != "completed":
        failures.append(f"run_status:{record.get('status')}")
    if str(execution.get("status", "")).lower() != "passed":
        failures.append(f"lifecycle_status:{execution.get('status')}")
    for name in sorted(required):
        if statuses.get(name) != "passed":
            failures.append(f"required_step_not_passed:{name}:{statuses.get(name, 'missing')}")
    failed_steps = sorted(name for name, status in statuses.items() if status == "failed")
    failures.extend(f"failed_step:{name}" for name in failed_steps)
    return not failures, failures, statuses


def build_campaign_report(state: dict[str, Any], *, preflight: bool) -> dict[str, Any]:
    runs = [item for item in state.get("runs", []) if isinstance(item, dict)]
    passed = sum(item.get("status") == "PASSED" for item in runs)
    failed = len(runs) - passed
    active_elapsed = state.get("active_elapsed_seconds")
    if isinstance(active_elapsed, (int, float)):
        duration_hours = max(0.0, float(active_elapsed) / 3600)
    else:
        started = _parse_iso(str(state["started_at"]))
        finished = _parse_iso(str(state.get("finished_at") or _utc_now()))
        duration_hours = max(0.0, (finished - started).total_seconds() / 3600)
    metrics = state.get("provider_metrics") if isinstance(state.get("provider_metrics"), dict) else {}
    per_attempt_metrics = bool(runs) and all("provider_loads" in item for item in runs)
    if per_attempt_metrics:
        active_models_peak = max(int(item.get("provider_peak_active_models", 0)) for item in runs)
        parallel_llm_loads_peak = max(
            int(item.get("provider_peak_parallel_llm_loads", 0)) for item in runs
        )
        model_loads = sum(int(item.get("provider_loads", 0)) for item in runs)
        model_unloads = sum(int(item.get("provider_unloads", 0)) for item in runs)
        model_unload_failures = sum(
            int(item.get("provider_unload_failures", 0)) for item in runs
        )
    else:
        active_models_peak = int(metrics.get("peak_active_models", 0))
        parallel_llm_loads_peak = int(metrics.get("peak_parallel_llm_loads", 0))
        model_loads = int(metrics.get("total_loads", 0))
        model_unloads = int(metrics.get("total_unloads", 0))
        model_unload_failures = int(metrics.get("unload_failures", 0))
    archetypes = sorted({str(item.get("archetype")) for item in runs})
    min_runs = int(state.get("min_runs", 1))
    duration_target = 0.0 if preflight else float(state.get("duration_hours", 8.0))
    failures: list[str] = []
    if len(runs) < min_runs:
        failures.append("minimum_runs_not_reached")
    if duration_hours < duration_target:
        failures.append("minimum_duration_not_reached")
    if not preflight and len(archetypes) < 3:
        failures.append("minimum_archetypes_not_reached")
    if failed:
        failures.append(f"failed_runs:{failed}")
    if per_attempt_metrics:
        invalid_model_attempts = [
            int(item.get("attempt", index))
            for index, item in enumerate(runs, start=1)
            if int(item.get("provider_loads", 0)) < 1
            or int(item.get("provider_unloads", 0))
            < int(item.get("provider_loads", 0))
        ]
        if invalid_model_attempts:
            failures.append(
                "attempt_model_lifecycle_invalid:"
                + ",".join(str(item) for item in invalid_model_attempts)
            )
    if active_models_peak != 1:
        failures.append("active_models_peak_not_one")
    if parallel_llm_loads_peak != 0:
        failures.append("parallel_model_load_detected")
    if int(metrics.get("active_models", 0)) != 0:
        failures.append("models_loaded_after_campaign")
    if model_unload_failures != 0:
        failures.append("model_unload_failures")
    return {
        "status": "PASSED" if not failures else "FAILED",
        "preflight": preflight,
        "started_at": state["started_at"],
        "finished_at": state.get("finished_at"),
        "duration_hours": round(duration_hours, 6),
        "attempted_runs": len(runs),
        "successful_runs": passed,
        "failed_runs": failed,
        "failure_rate": round(failed / len(runs), 6) if runs else 1.0,
        "project_archetypes": archetypes,
        "active_models_peak": active_models_peak,
        "parallel_llm_loads_peak": parallel_llm_loads_peak,
        "models_loaded_after": int(metrics.get("active_models", 0)),
        "model_loads": model_loads,
        "model_unloads": model_unloads,
        "rollback_status": (
            "PASSED"
            if int(metrics.get("active_models", 0)) == 0
            and model_unload_failures == 0
            else "FAILED"
        ),
        "gpu_peak_vram_mb": int(state.get("gpu_peak_vram_mb", 0)),
        "runs": runs,
        "failures": failures,
    }


def build_assurance_evidence(report: dict[str, Any], report_path: Path) -> dict[str, Any]:
    digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
    return {
        "schema_version": 1,
        "evidence_type": "soak_validation",
        "collected_at": report["finished_at"],
        "report_path": report_path.name,
        "report_sha256": digest,
        "decision": report["status"],
        "duration_hours": report["duration_hours"],
        "attempted_runs": report["attempted_runs"],
        "successful_runs": report["successful_runs"],
        "failed_runs": report["failed_runs"],
        "project_archetypes": report["project_archetypes"],
        "active_models_peak": report["active_models_peak"],
        "parallel_llm_loads_peak": report["parallel_llm_loads_peak"],
        "models_loaded_after": report["models_loaded_after"],
        "rollback_status": report["rollback_status"],
    }


def finalize_campaign_state(state: dict[str, Any], report: dict[str, Any]) -> None:
    """Persist a terminal state without erasing an explicit operator stop."""

    if state.get("status") != "STOPPED_BY_OPERATOR":
        state["status"] = str(report["status"])


def _report_markdown(report: dict[str, Any], title: str = "ANN Release Soak Validation") -> str:
    lines = [
        f"# {title}",
        "",
        f"Status: `{report['status']}`",
        f"Duration: `{report['duration_hours']}` hours",
        f"Runs: `{report['successful_runs']}/{report['attempted_runs']}` passed",
        f"Archetypes: `{', '.join(report['project_archetypes'])}`",
        f"Peak active models: `{report['active_models_peak']}`",
        f"Peak parallel loads: `{report['parallel_llm_loads_peak']}`",
        f"Peak VRAM: `{report['gpu_peak_vram_mb']} MB`",
        f"Rollback: `{report['rollback_status']}`",
        "",
        "## Attempts",
        "",
    ]
    lines.extend(
        f"- `{item['attempt']:03d}` `{item['case_id']}`: `{item['status']}` "
        f"({item['duration_seconds']}s, run `{item['run_id']}`)"
        for item in report["runs"]
    )
    if report["failures"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{item}`" for item in report["failures"])
    lines.extend(
        [
            "",
            "This report records real local API, model, Docker, build, test, and rollback evidence.",
            "It does not replace independent security, legal, or human product review.",
            "",
        ]
    )
    return "\n".join(lines)


def _execution(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("execution_results")
    return value if isinstance(value, dict) else {}


def _require_api_ready(api_base: str) -> None:
    health = _get_json(f"{api_base}/health")
    if health.get("status") != "ok":
        raise RuntimeError(f"ANN API is not healthy: {health}")


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
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed local API URL
                value = json.loads(response.read().decode("utf-8"))
            if not isinstance(value, dict):
                raise RuntimeError("ANN API returned a non-object response.")
            return value
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"ANN API request failed: {last_error}") from last_error


def _gpu_memory_used_mb() -> int:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0
    if completed.returncode != 0:
        return 0
    try:
        return max(int(float(item.strip())) for item in completed.stdout.splitlines() if item.strip())
    except ValueError:
        return 0


def _load_or_create_state(
    path: Path, *, duration_hours: float, min_runs: int, preflight: bool
) -> dict[str, Any]:
    if path.is_file():
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise RuntimeError("Campaign state must be a JSON object.")
        return value
    state = {
        "schema_version": 2,
        "status": "RUNNING",
        "preflight": preflight,
        "started_at": _utc_now(),
        "finished_at": None,
        "duration_hours": duration_hours,
        "min_runs": min_runs,
        "runs": [],
        "gpu_peak_vram_mb": 0,
        "active_elapsed_seconds": 0.0,
    }
    _atomic_json(path, state)
    return state


def _wait_until(
    target_monotonic: float,
    session_dir: Path,
    state: dict[str, Any],
    state_path: Path,
    *,
    base_active_seconds: float = 0.0,
    session_started: float | None = None,
) -> None:
    started = time.monotonic() if session_started is None else session_started
    while time.monotonic() < target_monotonic:
        if (session_dir / "STOP").exists():
            return
        state["heartbeat_at"] = _utc_now()
        _update_active_elapsed(state, base_active_seconds, started)
        _atomic_json(state_path, state)
        time.sleep(min(30.0, max(0.1, target_monotonic - time.monotonic())))


def _infer_active_elapsed_seconds(state: dict[str, Any], interval_seconds: float) -> float:
    recorded = state.get("active_elapsed_seconds")
    if isinstance(recorded, (int, float)):
        return max(0.0, float(recorded))
    runs = [item for item in state.get("runs", []) if isinstance(item, dict)]
    run_seconds = sum(float(item.get("duration_seconds", 0.0)) for item in runs)
    scheduled_seconds = interval_seconds * max(0, len(runs) - 1)
    wall_seconds = max(
        0.0,
        (datetime.now(timezone.utc) - _parse_iso(str(state["started_at"]))).total_seconds(),
    )
    return min(wall_seconds, max(run_seconds, scheduled_seconds))


def _update_active_elapsed(
    state: dict[str, Any],
    base_active_seconds: float,
    session_started: float,
) -> None:
    state["active_elapsed_seconds"] = round(
        base_active_seconds + max(0.0, time.monotonic() - session_started),
        3,
    )


def _parse_utc(value: str) -> float:
    parsed = _parse_iso(value)
    elapsed = (datetime.now(timezone.utc) - parsed).total_seconds()
    return time.monotonic() - elapsed


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
