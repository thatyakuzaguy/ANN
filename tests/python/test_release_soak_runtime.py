from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path

from scripts.runtime.run_release_soak import (
    ALGORITHM_LIVE_STEPS,
    FULL_STACK_LIVE_STEPS,
    build_assurance_evidence,
    build_campaign_report,
    evaluate_run_record,
    finalize_campaign_state,
    _case_for_attempt,
)


def _record(required_steps: set[str], *, status: str = "passed") -> dict[str, object]:
    return {
        "status": "completed",
        "execution_results": {
            "status": status,
            "steps": [
                {"name": name, "status": "passed", "detail": "real runtime evidence"}
                for name in required_steps
            ],
        },
    }


def test_full_stack_run_requires_all_live_steps() -> None:
    passed, failures, statuses = evaluate_run_record(
        _record(FULL_STACK_LIVE_STEPS), "web_application"
    )

    assert passed is True
    assert failures == []
    assert set(statuses) == FULL_STACK_LIVE_STEPS


def test_algorithm_run_rejects_skipped_live_step() -> None:
    record = _record(ALGORITHM_LIVE_STEPS)
    steps = record["execution_results"]["steps"]  # type: ignore[index]
    next(item for item in steps if item["name"] == "algorithm_benchmark_live")["status"] = "skipped"  # type: ignore[index]

    passed, failures, _statuses = evaluate_run_record(record, "algorithm_service")

    assert passed is False
    assert "required_step_not_passed:algorithm_benchmark_live:skipped" in failures


def test_campaign_report_requires_real_runtime_and_rollback() -> None:
    started = datetime.now(timezone.utc) - timedelta(hours=8, minutes=1)
    runs = [
        {"status": "PASSED", "archetype": archetype, "attempt": index}
        for index, archetype in enumerate(
            (["saas", "web_application", "algorithm_service"] * 7)[:20], start=1
        )
    ]
    state = {
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_hours": 8,
        "min_runs": 20,
        "runs": runs,
        "gpu_peak_vram_mb": 7024,
        "provider_metrics": {
            "peak_active_models": 1,
            "peak_parallel_llm_loads": 0,
            "active_models": 0,
            "total_loads": 300,
            "total_unloads": 300,
            "unload_failures": 0,
        },
    }

    report = build_campaign_report(state, preflight=False)

    assert report["status"] == "PASSED"
    assert report["attempted_runs"] == 20
    assert report["rollback_status"] == "PASSED"
    assert report["active_models_peak"] == 1
    assert report["parallel_llm_loads_peak"] == 0


def test_campaign_report_uses_per_attempt_model_events_not_process_peaks() -> None:
    runs = [
        {
            "status": "PASSED",
            "archetype": archetype,
            "provider_peak_active_models": 1,
            "provider_peak_parallel_llm_loads": 0,
            "provider_loads": 1,
            "provider_unloads": 1,
            "provider_unload_failures": 0,
        }
        for archetype in (["saas", "web_application", "algorithm_service"] * 7)[:20]
    ]
    state = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "active_elapsed_seconds": 8 * 3600,
        "duration_hours": 8,
        "min_runs": 20,
        "runs": runs,
        "provider_metrics": {
            "peak_active_models": 9,
            "peak_parallel_llm_loads": 8,
            "active_models": 0,
            "unload_failures": 99,
        },
    }

    report = build_campaign_report(state, preflight=False)

    assert report["status"] == "PASSED"
    assert report["active_models_peak"] == 1
    assert report["parallel_llm_loads_peak"] == 0
    assert report["model_loads"] == 20
    assert report["model_unloads"] == 20


def test_campaign_report_rejects_attempt_without_its_own_model_load() -> None:
    runs = [
        {
            "status": "PASSED",
            "archetype": archetype,
            "attempt": index,
            "provider_peak_active_models": 1,
            "provider_peak_parallel_llm_loads": 0,
            "provider_loads": 1,
            "provider_unloads": 1,
            "provider_unload_failures": 0,
        }
        for index, archetype in enumerate(
            (["saas", "web_application", "algorithm_service"] * 7)[:20],
            start=1,
        )
    ]
    runs[7]["provider_loads"] = 0
    runs[7]["provider_unloads"] = 0
    state = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "active_elapsed_seconds": 8 * 3600,
        "duration_hours": 8,
        "min_runs": 20,
        "runs": runs,
        "provider_metrics": {"active_models": 0},
    }

    report = build_campaign_report(state, preflight=False)

    assert report["status"] == "FAILED"
    assert "attempt_model_lifecycle_invalid:8" in report["failures"]


def test_campaign_report_uses_active_runtime_instead_of_host_downtime() -> None:
    started = datetime.now(timezone.utc) - timedelta(days=2)
    state = {
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "active_elapsed_seconds": 3600,
        "duration_hours": 8,
        "min_runs": 20,
        "runs": [],
        "provider_metrics": {},
    }

    report = build_campaign_report(state, preflight=False)

    assert report["duration_hours"] == 1.0
    assert "minimum_duration_not_reached" in report["failures"]


def test_campaign_state_is_terminal_after_report_generation() -> None:
    state: dict[str, object] = {"status": "RUNNING"}

    finalize_campaign_state(state, {"status": "FAILED"})

    assert state["status"] == "FAILED"


def test_campaign_state_preserves_operator_stop() -> None:
    state: dict[str, object] = {"status": "STOPPED_BY_OPERATOR"}

    finalize_campaign_state(state, {"status": "FAILED"})

    assert state["status"] == "STOPPED_BY_OPERATOR"


def test_assurance_evidence_binds_report_hash(tmp_path: Path) -> None:
    report_path = tmp_path / "soak_validation_report.md"
    report_path.write_text("real soak report\n", encoding="utf-8")
    report = {
        "status": "PASSED",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_hours": 8.1,
        "attempted_runs": 20,
        "successful_runs": 20,
        "failed_runs": 0,
        "project_archetypes": ["algorithm_service", "saas", "web_application"],
        "active_models_peak": 1,
        "parallel_llm_loads_peak": 0,
        "models_loaded_after": 0,
        "rollback_status": "PASSED",
    }

    evidence = build_assurance_evidence(report, report_path)

    assert evidence["report_sha256"] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert evidence["report_path"] == report_path.name
    assert evidence["decision"] == "PASSED"


def test_preflight_case_selector_can_target_each_archetype() -> None:
    assert _case_for_attempt(1, case_id="saas-task-platform")["archetype"] == "saas"
    assert _case_for_attempt(1, case_id="web-incident-console")["archetype"] == "web_application"
    assert _case_for_attempt(1, case_id="route-optimization-service")["archetype"] == "algorithm_service"


def test_official_case_rotation_remains_complete() -> None:
    archetypes = {_case_for_attempt(attempt)["archetype"] for attempt in range(1, 4)}

    assert archetypes == {"saas", "web_application", "algorithm_service"}
