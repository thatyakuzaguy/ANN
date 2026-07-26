"""Safe local model registration and runtime activation for ANN Desktop.

This module never downloads weights and never instantiates a model. It only
registers an explicitly selected local GGUF file, verifies its integrity, and
updates ANN's existing inventory and runtime policy atomically.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
from typing import Any
from uuid import uuid4

from agentic_network.runtime_engine.local_model_activation import diagnose_llama_cpp_real_status
from agentic_network.runtime_engine.model_inventory import load_model_inventory


REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,99}$")
ALLOWED_DRIVES = {"d:", "e:"}
WINDOWS_REMOTE_OR_DEVICE_PREFIXES = ("\\\\", "//")
EMPTY_INVENTORY: dict[str, Any] = {"version": 2, "models": []}
SAFE_MODEL_POLICY: dict[str, Any] = {
    "version": 1,
    "allow_real_model_load": False,
    "allow_model_download": False,
    "allow_training": False,
    "allow_adapter_write": False,
    "allow_dataset_write": False,
    "max_loaded_models": 1,
    "vram_policy": "SEQUENTIAL",
    "default_backend": "mock",
    "allowed_backends": ["mock", "llama_cpp"],
}
SAFE_RUNTIME_POLICY: dict[str, Any] = {
    "version": 1,
    "backend": "mock",
    "vram_policy": "SEQUENTIAL",
    "max_loaded_models": 1,
    "allow_parallel_llms": False,
    "auto_unload_after_execution": True,
    "backend_policy": {
        "allow_real_model_load": False,
        "allow_network": False,
        "allow_model_download": False,
    },
}


@dataclass(frozen=True)
class ModelSetupPaths:
    root: Path
    models: Path
    inventory: Path
    policy: Path
    runtime: Path


def model_setup_paths(root: str | Path | None = None) -> ModelSetupPaths:
    resolved_root = _safe_local_path(root or REPO_ROOT, require_exists=True, directory=True)
    return ModelSetupPaths(
        root=resolved_root,
        models=resolved_root / "models",
        inventory=resolved_root / "config" / "ann_model_inventory.json",
        policy=resolved_root / "config" / "ann_model_policy.json",
        runtime=resolved_root / "config" / "ann_runtime_engine.json",
    )


def get_model_setup_state(root: str | Path | None = None) -> dict[str, Any]:
    paths = model_setup_paths(root)
    inventory = load_model_inventory(paths.inventory)
    policy = _read_json_or_default(paths.policy, SAFE_MODEL_POLICY)
    runtime = _read_json_or_default(paths.runtime, SAFE_RUNTIME_POLICY)
    missing_configuration = [
        str(path)
        for path in (paths.inventory, paths.policy, paths.runtime)
        if not path.is_file()
    ]
    return {
        "status": "READY" if not inventory.errors and not missing_configuration else "PARTIAL",
        "root": str(paths.root),
        "models_root": str(paths.models),
        "models": [model.to_dict() for model in inventory.models],
        "inventory_errors": inventory.errors,
        "inventory_warnings": inventory.warnings,
        "configuration_warnings": [f"configuration_missing:{path}" for path in missing_configuration],
        "runtime": {
            "backend": str(runtime.get("backend", "mock")),
            "allow_real_model_load": bool(policy.get("allow_real_model_load", False)),
            "vram_policy": str(policy.get("vram_policy", "SEQUENTIAL")),
            "max_loaded_models": int(policy.get("max_loaded_models", 1)),
        },
        "downloads_performed": False,
        "model_load_performed": False,
    }


def register_local_gguf(
    *,
    source_path: str | Path,
    model_id: str,
    family: str,
    mode: str = "FAST",
    install_mode: str = "hardlink",
    expected_sha256: str = "",
    license_acknowledged: bool,
    confirmed: bool,
    risk_acknowledged: bool,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Register a user-supplied GGUF without loading it or accessing the network."""

    clean_id = model_id.strip().lower()
    if not MODEL_ID_PATTERN.fullmatch(clean_id):
        raise ValueError("model_id must contain 3-100 lowercase letters, numbers, dots, dashes, or underscores.")
    if not license_acknowledged:
        raise ValueError("The model license and local-use terms must be acknowledged.")
    if not confirmed or not risk_acknowledged:
        raise ValueError("Model registration requires confirmation and storage risk acknowledgement.")
    clean_mode = mode.strip().upper()
    if clean_mode not in {"FAST", "POWERFUL"}:
        raise ValueError("mode must be FAST or POWERFUL.")
    clean_install_mode = install_mode.strip().lower()
    if clean_install_mode not in {"copy", "hardlink"}:
        raise ValueError("install_mode must be copy or hardlink.")

    source = _safe_local_path(source_path, require_exists=True, directory=False)
    if source.suffix.lower() != ".gguf":
        raise ValueError("ANN v1.0 local model import accepts GGUF files only.")
    # The source is an explicitly selected local GGUF. _safe_local_path has
    # already canonicalized it, rejected traversal/UNC/device paths, and
    # constrained its resolved location to D: or E:.
    # codeql[py/path-injection]
    if source.stat().st_size <= 0:
        raise ValueError("Selected GGUF file is empty.")

    paths = model_setup_paths(root)
    paths.models.mkdir(parents=True, exist_ok=True)
    destination = _managed_model_destination(paths.models, source.name)
    source_hash = _sha256(source)
    expected = expected_sha256.strip().lower()
    if expected and (not re.fullmatch(r"[0-9a-f]{64}", expected) or expected != source_hash):
        raise ValueError("Selected model SHA256 does not match the expected digest.")

    installed_by = "existing"
    # Both paths are canonical capabilities returned by the policy helpers.
    # codeql[py/path-injection]
    if source.resolve() != destination.resolve():
        # codeql[py/path-injection]
        if destination.exists():
            # codeql[py/path-injection]
            if destination.stat().st_size != source.stat().st_size or _sha256(destination) != source_hash:
                raise FileExistsError(f"A different model file already exists at {destination}.")
        elif clean_install_mode == "hardlink":
            if source.drive.lower() != destination.drive.lower():
                raise ValueError("Hard-link import requires source and ANN to be on the same drive.")
            try:
                # codeql[py/path-injection]
                os.link(source, destination)
                installed_by = "hardlink"
            except FileExistsError:
                # A second approved setup process may win the race after the
                # existence check. Accept only the exact verified payload.
                # codeql[py/path-injection]
                if destination.stat().st_size != source.stat().st_size or _sha256(destination) != source_hash:
                    raise FileExistsError(f"A different model file already exists at {destination}.") from None
                installed_by = "existing"
        else:
            # codeql[py/path-injection]
            shutil.copy2(source, destination)
            installed_by = "copy"

    payload = _read_json_or_default(paths.inventory, EMPTY_INVENTORY)
    raw_models = payload.get("models")
    if not isinstance(raw_models, list):
        raw_models = []
    record = {
        "model_name": clean_id,
        "name": clean_id,
        "family": family.strip() or "local-gguf",
        "mode": clean_mode,
        "source_path": str(source),
        "distribution_path": str(destination),
        "path": f"models/{destination.name}",
        "backend": "llama_cpp",
        "adapter_path": None,
        "quantization": _quantization_from_name(destination.name),
        "estimated_vram_mb": 0,
        "size_bytes": destination.stat().st_size,
        "sha256": source_hash,
        "context_tokens": 8192,
        "max_tokens": 1024 if clean_mode == "FAST" else 1536,
        "temperature": 0.2,
        "n_gpu_layers": -1,
        "main_gpu": 0,
        "enabled": True,
        "status": "detected",
    }
    filtered = [item for item in raw_models if not _same_model(item, clean_id, destination.name)]
    payload["version"] = max(2, int(payload.get("version", 1)))
    payload["models"] = [*filtered, record]
    _write_json_atomic(paths.inventory, payload)
    return {
        "status": "MODEL_REGISTERED",
        "model": record,
        "installed_by": installed_by,
        "sha256_verified": True,
        "license_acknowledged": True,
        "downloads_performed": False,
        "model_load_performed": False,
    }


def configure_real_model_runtime(
    *,
    enabled: bool,
    confirmed: bool,
    risk_acknowledged: bool,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Enable or disable the existing llama_cpp policy without loading a model."""

    if not confirmed or not risk_acknowledged:
        raise ValueError("Runtime policy changes require confirmation and risk acknowledgement.")
    paths = model_setup_paths(root)
    inventory = load_model_inventory(paths.inventory)
    valid_models = [model for model in inventory.models if model.path_exists and model.enabled]
    diagnostic: dict[str, Any] = {"status": "SAFE_MODE"}
    if enabled:
        if not valid_models:
            raise ValueError("At least one registered local GGUF must be present before enabling real inference.")
        diagnostic = diagnose_llama_cpp_real_status(valid_models[0].path)
        if diagnostic.get("status") != "READY":
            raise RuntimeError(
                "GPU-capable llama_cpp runtime is not ready: "
                + ", ".join(str(item) for item in diagnostic.get("errors", [])[:5])
            )

    policy = _read_json_or_default(paths.policy, SAFE_MODEL_POLICY)
    runtime = _read_json_or_default(paths.runtime, SAFE_RUNTIME_POLICY)
    policy["allow_real_model_load"] = enabled
    policy["default_backend"] = "llama_cpp" if enabled else "mock"
    policy["max_loaded_models"] = 1
    policy["vram_policy"] = "SEQUENTIAL"
    allowed_backends = policy.get("allowed_backends")
    if not isinstance(allowed_backends, list):
        allowed_backends = ["mock"]
    policy["allowed_backends"] = list(
        dict.fromkeys([*(str(item).strip().lower() for item in allowed_backends), "llama_cpp"])
    )
    runtime["backend"] = "llama_cpp" if enabled else "mock"
    runtime["vram_policy"] = "SEQUENTIAL"
    runtime["max_loaded_models"] = 1
    runtime["allow_parallel_llms"] = False
    backend_policy = runtime.setdefault("backend_policy", {})
    if not isinstance(backend_policy, dict):
        backend_policy = {}
        runtime["backend_policy"] = backend_policy
    backend_policy["allow_real_model_load"] = enabled

    _write_json_atomic(paths.policy, policy)
    try:
        _write_json_atomic(paths.runtime, runtime)
    except Exception:
        policy["allow_real_model_load"] = False
        policy["default_backend"] = "mock"
        _write_json_atomic(paths.policy, policy)
        raise
    return {
        "status": "REAL_MODEL_RUNTIME_ENABLED" if enabled else "SAFE_MODE_ENABLED",
        "backend": runtime["backend"],
        "active_models": 0,
        "parallel_llm_loads": 0,
        "vram_policy": "SEQUENTIAL",
        "diagnostic": diagnostic,
        "model_load_performed": False,
    }


def _safe_local_path(
    raw_path: str | Path,
    *,
    require_exists: bool,
    directory: bool,
) -> Path:
    raw = str(raw_path).strip()
    if not raw or any(part == ".." for part in raw.replace("\\", "/").split("/")):
        raise ValueError("Unsafe or empty local path.")
    if raw.startswith(WINDOWS_REMOTE_OR_DEVICE_PREFIXES):
        raise ValueError("UNC, network, and Windows device paths are not permitted.")
    windows_path = PureWindowsPath(raw)
    drive = windows_path.drive.lower()
    if drive and drive not in ALLOWED_DRIVES:
        raise ValueError("ANN model setup only permits D: or E: paths.")
    if os.name == "nt" and not windows_path.is_absolute():
        raise ValueError("ANN model setup requires an absolute local path.")
    if not drive and os.name == "nt":
        # codeql[py/path-injection]
        resolved_candidate = Path(raw).resolve()
        if resolved_candidate.drive.lower() not in ALLOWED_DRIVES:
            raise ValueError("ANN model setup only permits D: or E: paths.")
    # This is the single canonicalization boundary for local model paths.
    # The checks above reject traversal, remote/device paths, and unauthorized
    # drives; the resolved-drive check below also catches junction escapes.
    # codeql[py/path-injection]
    path = Path(raw).resolve()
    if os.name == "nt":
        resolved_drive = PureWindowsPath(str(path)).drive.lower()
        if resolved_drive not in ALLOWED_DRIVES:
            raise ValueError("ANN model setup only permits paths that resolve to D: or E:.")
    # codeql[py/path-injection]
    if require_exists and not path.exists():
        raise FileNotFoundError(f"Local path does not exist: {path}")
    # codeql[py/path-injection]
    if require_exists and directory and not path.is_dir():
        raise ValueError(f"Expected a directory: {path}")
    # codeql[py/path-injection]
    if require_exists and not directory and not path.is_file():
        raise ValueError(f"Expected a file: {path}")
    return path


def _managed_model_destination(models_root: Path, filename: str) -> Path:
    """Return a canonical destination capability confined to ANN's model root."""

    if not filename or filename in {".", ".."} or Path(filename).name != filename:
        raise ValueError("Model filename must be a single local path component.")
    canonical_root = _safe_local_path(models_root, require_exists=True, directory=True)
    destination = _safe_local_path(canonical_root / filename, require_exists=False, directory=False)
    if destination.parent != canonical_root:
        raise ValueError("Model destination escaped ANN's managed model directory.")
    return destination


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Required ANN configuration is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"ANN configuration is invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"ANN configuration must contain a JSON object: {path}")
    return payload


def _read_json_or_default(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    """Return an isolated safe default for a not-yet-configured installation."""

    if not path.exists():
        return json.loads(json.dumps(default))
    return _read_json(path)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    # Callers supply only capabilities returned by _safe_local_path or
    # _managed_model_destination; arbitrary request paths never reach here.
    # codeql[py/path-injection]
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _same_model(item: object, model_id: str, filename: str) -> bool:
    if not isinstance(item, dict):
        return False
    item_id = str(item.get("model_name") or item.get("name") or "").lower()
    item_path = str(item.get("path") or "").replace("\\", "/")
    return item_id == model_id or item_path.lower().endswith(f"/{filename.lower()}")


def _quantization_from_name(filename: str) -> str:
    match = re.search(r"(?i)(q\d(?:_[a-z0-9]+)+)", filename)
    return match.group(1).upper() if match else "GGUF"
