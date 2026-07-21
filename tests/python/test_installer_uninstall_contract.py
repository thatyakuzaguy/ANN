from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_full_uninstall_covers_generated_projects_and_validation_markers() -> None:
    script = (REPO_ROOT / "installer" / "uninstall_ann.ps1").read_text(encoding="utf-8")

    assert 'if ($RemoveProjects) { $remove += @("projects", "generated-projects") }' in script
    assert '"local_smoke_validation.json", "clean_machine_external_validation.json"' in script


def test_install_manifest_declares_generated_projects_preserved_by_default() -> None:
    script = (REPO_ROOT / "installer" / "install_ann.ps1").read_text(encoding="utf-8")

    assert (
        'preserved_by_default = @("projects", "generated-projects", "models", "outputs", "data", "logs")'
        in script
    )
