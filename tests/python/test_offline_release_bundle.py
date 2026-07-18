from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.release.build_offline_release_bundle import (
    PAYLOAD_MANIFEST_NAME,
    ReleaseItem,
    build_release_archive,
    sha256_file,
    split_archive,
)
from scripts.release.verify_offline_release_bundle import verify_bundle


ROOT = Path("D:/AgenticEngineeringNetwork")


def test_split_release_archive_round_trip_is_hash_verified(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    first = source / "first.txt"
    second = source / "second.bin"
    first.write_text("ANN release\n", encoding="utf-8")
    second.write_bytes(bytes(range(64)) * 8)
    output = tmp_path / "release"
    output.mkdir()
    archive = output / "ANN-test.zip"
    result = build_release_archive(
        [
            ReleaseItem(first, "payload/app/first.txt"),
            ReleaseItem(second, "payload/runtime/second.bin"),
        ],
        archive,
        version="test",
    )
    parts = split_archive(archive, output, 100)
    bootstrap = output / "assemble_release.ps1"
    bootstrap.write_text("Write-Host 'test'\n", encoding="utf-8")
    manifest = {
        "status": "OFFLINE_RELEASE_BUNDLE_READY",
        "archive_name": archive.name,
        "archive_size_bytes": result["archive_size_bytes"],
        "archive_sha256": result["archive_sha256"],
        "parts": parts,
        "bootstrap_files": [
            {
                "file_name": bootstrap.name,
                "size_bytes": bootstrap.stat().st_size,
                "sha256": sha256_file(bootstrap),
            }
        ],
        "models_included": False,
        "no_download": True,
        "no_inference": True,
    }
    (output / "ANN_RELEASE_PARTS.json").write_text(json.dumps(manifest), encoding="utf-8")
    archive.unlink()

    verification = verify_bundle(output)

    assert len(parts) > 1
    assert verification["status"] == "OFFLINE_RELEASE_BUNDLE_VERIFIED"
    assert verification["archive_sha256"] == result["archive_sha256"]


def test_release_archive_contains_manifest_and_preserves_code_blocks(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    source.write_text("```python\nprint('ANN')\n```\n", encoding="utf-8")
    archive = tmp_path / "release.zip"

    build_release_archive([ReleaseItem(source, "payload/app/README.md")], archive, version="test")

    with zipfile.ZipFile(archive) as payload:
        manifest = json.loads(payload.read(PAYLOAD_MANIFEST_NAME))
        assert payload.read("payload/app/README.md") == source.read_bytes()
    assert manifest["file_count"] == 1
    assert manifest["model_files_included"] is False


def test_release_builder_rejects_model_artifacts(tmp_path: Path) -> None:
    model = tmp_path / "model.gguf"
    model.write_bytes(b"model")

    try:
        build_release_archive([ReleaseItem(model, "payload/app/model.gguf")], tmp_path / "bad.zip", version="test")
    except ValueError as exc:
        assert "Model artifact" in str(exc)
    else:
        raise AssertionError("Model artifact unexpectedly entered public release")


def test_release_scripts_are_offline_and_installer_verifies_payload() -> None:
    sources = "\n".join(
        [
            (ROOT / "scripts/release/build_offline_release_bundle.py").read_text(encoding="utf-8"),
            (ROOT / "scripts/release/verify_offline_release_bundle.py").read_text(encoding="utf-8"),
            (ROOT / "installer/assemble_release.ps1").read_text(encoding="utf-8"),
        ]
    ).lower()
    installer = (ROOT / "installer/install_ann.ps1").read_text(encoding="utf-8")

    for forbidden in ("invoke-webrequest", "start-bitstransfer", "pip install", "npm install", "shell=true"):
        assert forbidden not in sources
    assert "Test-ReleasePayloadManifest" in installer
    assert "Release payload SHA256 mismatch" in installer
    assert "Get-FileHash" in (ROOT / "installer/assemble_release.ps1").read_text(encoding="utf-8")
    assert '"README_OFFLINE_RELEASE.md"' in installer
    assert '"validate_clean_machine.ps1"' in installer
