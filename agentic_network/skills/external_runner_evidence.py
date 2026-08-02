"""Validation for evidence produced by isolated external skill runners."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any


RUNNER_FAMILIES: dict[str, frozenset[str]] = {
    "windows_binary": frozenset({"windows-sandbox", "windows-vm", "windows-release-lab"}),
    "native_ui": frozenset(
        {
            "appium_windows",
            "pywinauto",
            "uiautomation",
            "winappdriver",
            "windows-uia",
            "windows-appium",
            "windows-vm-uia",
        }
    ),
    "mobile": frozenset(
        {
            "android-emulator",
            "android-device",
            "ios-simulator",
            "ios-device",
            "android_emulator",
            "android_device",
            "ios_simulator",
            "ios_device",
        }
    ),
    "assistive_technology": frozenset(
        {"nvda-windows", "narrator-windows", "voiceover-macos", "talkback-android"}
    ),
    "data_residency": frozenset({"policy-evidence-export", "infrastructure-inventory"}),
}
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def validate_external_runner_evidence(
    evidence: Any,
    runner_family: str,
) -> dict[str, Any]:
    """Validate bounded attestation metadata without executing the referenced runner."""

    errors: list[str] = []
    payload = evidence if isinstance(evidence, dict) else {}
    allowed = RUNNER_FAMILIES.get(runner_family, frozenset())
    runner = str(payload.get("runner") or "").strip().lower()
    status = str(payload.get("status") or "").strip().upper()
    report_hash = str(payload.get("report_sha256") or "").strip()
    generated_at = str(payload.get("generated_at") or "").strip()
    if not allowed:
        errors.append("unknown_runner_family")
    if runner not in allowed:
        errors.append("runner_not_allowed")
    if status != "PASSED":
        errors.append("runner_status_not_passed")
    if SHA256.fullmatch(report_hash) is None:
        errors.append("report_sha256_invalid")
    try:
        parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
    except ValueError:
        errors.append("generated_at_invalid")
    artifact_hashes = payload.get("artifact_hashes")
    if not isinstance(artifact_hashes, list) or not artifact_hashes:
        errors.append("artifact_hashes_required")
    else:
        for item in artifact_hashes[:100]:
            if not isinstance(item, dict):
                errors.append("artifact_hash_entry_invalid")
                continue
            path = str(item.get("path") or "")
            digest = str(item.get("sha256") or "")
            if not path or ".." in path.replace("\\", "/").split("/"):
                errors.append("artifact_path_invalid")
            if SHA256.fullmatch(digest) is None:
                errors.append("artifact_sha256_invalid")
    return {
        "status": "VERIFIED" if not errors else "REJECTED",
        "valid": not errors,
        "runner_family": runner_family,
        "runner": runner,
        "reported_status": status,
        "report_sha256": report_hash,
        "generated_at": generated_at,
        "signature_verified": bool(payload.get("signature_verified")),
        "errors": sorted(set(errors)),
        "runner_executed_by_ann": False,
    }
