"""Verify ANN split offline release parts without extracting or executing them."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.release.build_offline_release_bundle import BUFFER_BYTES, sha256_file  # noqa: E402


def verify_bundle(bundle_root: Path) -> dict[str, Any]:
    root = bundle_root.resolve()
    manifest_path = root / "ANN_RELEASE_PARTS.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "OFFLINE_RELEASE_BUNDLE_INVALID", "blockers": [str(exc)], "checks": []}
    checks: list[dict[str, object]] = []
    combined = hashlib.sha256()
    total = 0
    expected_index = 1
    for part in manifest.get("parts", []):
        name = str(part.get("file_name", ""))
        path = root / name
        safe = bool(name) and Path(name).name == name and ".." not in Path(name).parts
        checks.append(_check(f"part_path_safe:{name}", safe, name))
        if not safe:
            continue
        exists = path.is_file()
        actual_size = path.stat().st_size if exists else -1
        actual_hash = sha256_file(path) if exists else ""
        checks.append(_check(f"part_exists:{name}", exists, str(path)))
        checks.append(_check(f"part_size:{name}", actual_size == int(part.get("size_bytes", -2)), str(actual_size)))
        checks.append(_check(f"part_hash:{name}", actual_hash == str(part.get("sha256", "")), actual_hash))
        checks.append(_check(f"part_index:{name}", int(part.get("index", -1)) == expected_index, str(part.get("index"))))
        expected_index += 1
        if exists:
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(BUFFER_BYTES), b""):
                    combined.update(chunk)
                    total += len(chunk)
    for bootstrap in manifest.get("bootstrap_files", []):
        name = str(bootstrap.get("file_name", ""))
        path = root / name
        safe = bool(name) and Path(name).name == name and ".." not in Path(name).parts
        checks.append(_check(f"bootstrap_path_safe:{name}", safe, name))
        exists = safe and path.is_file()
        checks.append(_check(f"bootstrap_exists:{name}", exists, str(path)))
        if exists:
            checks.append(_check(f"bootstrap_size:{name}", path.stat().st_size == int(bootstrap.get("size_bytes", -1)), str(path.stat().st_size)))
            checks.append(_check(f"bootstrap_hash:{name}", sha256_file(path) == str(bootstrap.get("sha256", "")), sha256_file(path)))
    checks.extend(
        [
            _check("manifest_status", manifest.get("status") == "OFFLINE_RELEASE_BUNDLE_READY", str(manifest.get("status"))),
            _check("archive_size", total == int(manifest.get("archive_size_bytes", -1)), str(total)),
            _check("archive_hash", combined.hexdigest() == str(manifest.get("archive_sha256", "")), combined.hexdigest()),
            _check("models_excluded", manifest.get("models_included") is False, str(manifest.get("models_included"))),
            _check("no_download", manifest.get("no_download") is True, str(manifest.get("no_download"))),
            _check("no_inference", manifest.get("no_inference") is True, str(manifest.get("no_inference"))),
        ]
    )
    blockers = [check for check in checks if not check["passed"]]
    return {
        "status": "OFFLINE_RELEASE_BUNDLE_VERIFIED" if not blockers else "OFFLINE_RELEASE_BUNDLE_INVALID",
        "bundle_root": str(root),
        "parts_checked": len(manifest.get("parts", [])),
        "archive_size_bytes": total,
        "archive_sha256": combined.hexdigest(),
        "checks": checks,
        "blockers": blockers,
        "no_install": True,
        "no_model_load": True,
        "no_inference": True,
    }


def _check(identifier: str, passed: bool, detail: str) -> dict[str, object]:
    return {"id": identifier, "passed": bool(passed), "status": "PASS" if passed else "FAIL", "detail": detail}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = verify_bundle(args.bundle_root)
    print(json.dumps(result, indent=2) if args.json else f"Status: {result['status']}\nParts: {result.get('parts_checked', 0)}\nBlockers: {len(result.get('blockers', []))}")
    return 0 if result["status"] == "OFFLINE_RELEASE_BUNDLE_VERIFIED" else 2


if __name__ == "__main__":
    sys.exit(main())
