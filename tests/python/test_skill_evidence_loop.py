from __future__ import annotations

import json
from pathlib import Path

from agentic_network.skills.evidence_loop import (
    build_skill_evidence_plan,
    interpret_skill_results,
    load_skill_results,
    select_skills_for_context,
    write_skill_evidence_loop_artifacts,
)
from agentic_network.desktop_app.views.skill_evidence_view import skill_evidence_snapshot


def test_cross_domain_context_selects_relevant_skills_deterministically() -> None:
    context = {
        "stderr": "Docker Redis port mismatch caused OAuth webhook database timeout",
        "affected_files": ["docker-compose.yml", "app/auth.py", "migrations/003.sql"],
    }

    first = select_skills_for_context(context)
    second = select_skills_for_context(context)
    names = [item["skill"] for item in first]

    assert first == second
    assert "identity_protocol_conformance" in names
    assert "container_operations" in names
    assert all(item["mutates_project"] is False for item in first)


def test_plan_preserves_existing_approval_and_execution_gates() -> None:
    plan = build_skill_evidence_plan({"stderr": "docker compose port failure"})

    assert plan["status"] == "APPROVAL_REQUIRED"
    assert "container_operations" in plan["approval_required_for"]
    assert plan["raw_command_allowed"] is False
    assert plan["automatic_execution"] is False
    assert plan["automatic_patch_apply"] is False


def test_missing_partial_and_successful_evidence_have_distinct_decisions() -> None:
    plan = build_skill_evidence_plan({"stderr": "pyright type error"}, max_skills=2)
    skills = [item["skill"] for item in plan["selected_skills"]]
    missing = interpret_skill_results(plan, [])
    partial = interpret_skill_results(
        plan,
        [{"skill": skill, "status": "PARTIAL"} for skill in skills],
    )
    success = interpret_skill_results(
        plan,
        [{"skill": skill, "status": "SUCCESS"} for skill in skills],
    )

    assert missing["status"] == "EVIDENCE_REQUIRED"
    assert partial["status"] == "REMEDIATION_REQUIRED"
    assert success["status"] == "VERIFIED"
    assert success["patch_apply_allowed"] is False
    assert success["human_approval_bypassed"] is False


def test_evidence_loop_artifacts_are_bounded_and_do_not_execute(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    plan = build_skill_evidence_plan({"stderr": "TS2322 in src/app.ts"})
    decision = interpret_skill_results(plan, [])

    artifacts = write_skill_evidence_loop_artifacts(run_dir, 2, plan, decision)

    assert len(artifacts) == 4
    assert all(Path(item).is_file() for item in artifacts)
    payload = json.loads(Path(artifacts[0]).read_text(encoding="utf-8"))
    assert payload["automatic_execution"] is False
    assert payload["automatic_patch_apply"] is False
    assert not list(run_dir.glob("*.diff"))


def test_desktop_skill_evidence_snapshot_shows_correction_plan(tmp_path: Path) -> None:
    plan = build_skill_evidence_plan({"stderr": "OAuth token validation failed"})
    decision = interpret_skill_results(plan, [])
    write_skill_evidence_loop_artifacts(tmp_path, 1, plan, decision)

    snapshot = skill_evidence_snapshot(tmp_path)

    assert "Correction Loop Evidence" in snapshot
    assert "identity_protocol_conformance.inspect" in snapshot
    assert "EVIDENCE_REQUIRED" in snapshot


def test_only_matching_bounded_results_are_loaded_from_fixed_drop_directory(
    tmp_path: Path,
) -> None:
    plan = build_skill_evidence_plan({"stderr": "OAuth token validation failed"}, max_skills=2)
    selected = plan["selected_skills"][0]["skill"]
    drop = tmp_path / "skill_evidence_results"
    drop.mkdir()
    (drop / "accepted.json").write_text(
        json.dumps({"skill": selected, "status": "SUCCESS", "summary": "verified"}),
        encoding="utf-8",
    )
    (drop / "unrelated.json").write_text(
        json.dumps({"skill": "container_operations", "status": "SUCCESS"}),
        encoding="utf-8",
    )
    (drop / "invalid.json").write_text("not json", encoding="utf-8")

    results = load_skill_results(tmp_path, plan)

    assert results == [
        {
            "skill": selected,
            "status": "SUCCESS",
            "summary": "verified",
            "source_file": "accepted.json",
            "approval_evidence_present": False,
        }
    ]


def test_approval_required_result_cannot_self_attest_success() -> None:
    plan = build_skill_evidence_plan({"stderr": "docker compose port failure"})
    results = [
        {
            "skill": item["skill"],
            "status": "SUCCESS",
            "approval_evidence_present": False,
        }
        for item in plan["selected_skills"]
    ]

    decision = interpret_skill_results(plan, results)

    assert decision["status"] == "APPROVAL_REQUIRED"
    assert "container_operations" in decision["blocked_skills"]
