from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_public_exporter_preserves_declared_release_version() -> None:
    config = json.loads((ROOT / "config" / "public-release.json").read_text(encoding="utf-8"))
    script = (ROOT / "scripts" / "release" / "build-public-repository.ps1").read_text(
        encoding="utf-8-sig"
    )

    assert config["release_version"] == "1.0.1"
    assert "release_version = [string]$config.release_version" in script
    assert '$manifest.release_version -Compress)' in script


def test_public_exporter_supports_re_exporting_a_public_checkout() -> None:
    script = (ROOT / "scripts" / "release" / "build-public-repository.ps1").read_text(
        encoding="utf-8-sig"
    )

    assert '$publicReadme = Join-Path $SourceRoot "docs\\public\\README.md"' in script
    assert '$publicReadme = Join-Path $SourceRoot "README.md"' in script
    assert "Copy-Item -LiteralPath $publicReadme" in script
