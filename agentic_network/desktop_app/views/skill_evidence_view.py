"""Read-only Skill Evidence view for ANN Desktop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentic_network.skill_evidence_agent.runtime import DEFAULT_EVIDENCE_ROOT, REPO_ROOT

try:  # pragma: no cover - covered by manual desktop smoke.
    from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

    PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    QLabel = None
    QPlainTextEdit = None
    QVBoxLayout = None
    QWidget = object
    PYSIDE6_AVAILABLE = False


SKILL_EVIDENCE_MESSAGE = (
    "Skill Evidence is read-only advisory context. This view does not execute skills, "
    "use internet, run terminal commands, apply patches, or copy external code."
)


def skill_evidence_snapshot(evidence_root: str | Path | None = None) -> str:
    """Render latest skill evidence bundles."""

    root = Path(evidence_root or DEFAULT_EVIDENCE_ROOT).resolve()
    lines = ["Skill Evidence", "", SKILL_EVIDENCE_MESSAGE, ""]
    bundles = sorted(root.glob("*/70_skill_evidence_bundle.json")) if root.is_dir() else []
    direct = root / "70_skill_evidence_bundle.json"
    if direct.is_file():
        bundles.insert(0, direct)
    if not bundles:
        lines.append("No skill evidence bundles found.")
    run_roots = [root]
    if evidence_root is None:
        run_roots.append((REPO_ROOT / "outputs" / "runs").resolve())
    for bundle_path in bundles[-5:]:
        payload = _read_json(bundle_path)
        lines.extend(
            [
                str(bundle_path.parent),
                f"- Status: {payload.get('status', 'UNKNOWN')}",
                f"- Sources used: {payload.get('sources_used', [])}",
                f"- Summary: {payload.get('summary', '')}",
                "- Recommendations:",
                *[f"  - {item}" for item in payload.get("recommendations", []) if isinstance(item, str)],
                "- Risks:",
                *[f"  - {item}" for item in payload.get("risks", []) if isinstance(item, str)],
                "- Items:",
            ]
        )
        for item in payload.get("evidence_items", []) if isinstance(payload.get("evidence_items"), list) else []:
            if isinstance(item, dict):
                lines.append(
                    f"  - {item.get('evidence_type', 'unknown')}: {item.get('title', '')} "
                    f"safe_to_use={item.get('safe_to_use', False)} source={item.get('source_path', '')}"
                )
        lines.append("")
    plans: list[Path] = []
    for run_root in run_roots:
        if run_root.is_dir():
            plans.extend(run_root.rglob("38_skill_evidence_plan_attempt_*.json"))
    if plans:
        lines.extend(["Correction Loop Evidence", ""])
    for plan_path in sorted(set(plans))[-10:]:
        payload = _read_json(plan_path)
        decision_path = plan_path.with_name(
            plan_path.name.replace("38_skill_evidence_plan_", "39_skill_evidence_decision_")
        )
        decision = _read_json(decision_path) if decision_path.is_file() else {}
        selected = payload.get("selected_skills", [])
        lines.extend(
            [
                str(plan_path.parent),
                f"- Plan status: {payload.get('status', 'UNKNOWN')}",
                f"- Decision: {decision.get('status', 'EVIDENCE_REQUIRED')}",
                f"- Next action: {decision.get('next_action', payload.get('next_action', ''))}",
                "- Selected skills:",
                *[
                    f"  - {item.get('skill', '')}.{item.get('action', '')}: {item.get('reason', '')}"
                    for item in selected
                    if isinstance(item, dict)
                ],
                "",
            ]
        )
    return "\n".join(lines)


if PYSIDE6_AVAILABLE:

    class SkillEvidenceView(QWidget):  # type: ignore[misc]
        """Read-only Skill Evidence view."""

        def __init__(self) -> None:
            super().__init__()
            layout = QVBoxLayout(self)
            title = QLabel("Skill Evidence")
            title.setAccessibleName("Skill Evidence view title")
            self.body = QPlainTextEdit(skill_evidence_snapshot())
            self.body.setReadOnly(True)
            self.body.setAccessibleName("Skill Evidence read only status")
            layout.addWidget(title)
            layout.addWidget(self.body, 1)

        def set_bundle(self, _bundle: Any, _snapshot: dict[str, Any]) -> None:
            self.body.setPlainText(skill_evidence_snapshot())

else:

    class SkillEvidenceView:  # type: ignore[no-redef]
        pass


def _read_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
