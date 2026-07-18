"""Model loader enforcing ANN's single active backend and sequential VRAM policy."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

from agentic_network.runtime_engine.backend_registry import get_backend
from agentic_network.runtime_engine.backends.base import ModelBackend
from agentic_network.runtime_engine.model_policy import load_model_policy, validate_model_load_request


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "ann_runtime_engine.json"
_LOADED_MODELS: list[str] = []
_ACTIVE_BACKEND: ModelBackend | None = None
_METRICS: dict[str, Any] = {
    "load_count": 0,
    "unload_count": 0,
    "active_models": 0,
    "parallel_llm_loads": 0,
    "peak_active_models": 0,
    "peak_vram_mb": 0,
    "backend_name": "mock",
    "backend_status": "UNKNOWN",
    "last_load_status": "UNKNOWN",
    "last_generate_status": "UNKNOWN",
    "last_unload_status": "UNKNOWN",
    "events": [],
}


def load_model(
    model_name: str,
    backend_name: str | None = None,
    *,
    backend: ModelBackend | None = None,
) -> dict[str, Any]:
    """Load one logical model, unloading any previous model first."""

    global _ACTIVE_BACKEND
    started = perf_counter()
    clean_name = model_name.strip()
    if not clean_name:
        return {"status": "BLOCKED", "model_name": "", "load_time_ms": 0, "errors": ["model_name_required"]}
    config = _load_config()
    if int(config.get("max_loaded_models", 1)) != 1 or bool(config.get("allow_parallel_llms", False)):
        return {
            "status": "BLOCKED",
            "model_name": clean_name,
            "load_time_ms": 0,
            "errors": ["runtime_policy_must_remain_sequential"],
        }
    if _LOADED_MODELS == [clean_name] and _ACTIVE_BACKEND is not None:
        active_backend = _ACTIVE_BACKEND
        _METRICS["backend_name"] = active_backend.name
        _METRICS["last_load_status"] = "LOADED"
        _update_active_metrics()
        return {
            "status": "LOADED",
            "model_name": clean_name,
            "backend": active_backend.name,
            "backend_status": str(_METRICS["backend_status"]),
            "load_time_ms": _elapsed_ms(started),
            "errors": [],
            "warnings": ["model_already_loaded_on_active_backend"],
            "backend_result": {
                "status": "LOADED",
                "model_name": clean_name,
                "backend": active_backend.name,
                "loaded": True,
                "errors": [],
                "warnings": ["model_already_loaded_on_active_backend"],
            },
        }
    if _LOADED_MODELS and _LOADED_MODELS[0] != clean_name:
        previous_unload = unload_model(_LOADED_MODELS[0])
        if previous_unload.get("status") != "UNLOADED":
            return {
                "status": "BLOCKED",
                "model_name": clean_name,
                "load_time_ms": _elapsed_ms(started),
                "errors": ["previous_model_unload_failed", *previous_unload.get("errors", [])],
                "warnings": previous_unload.get("warnings", []),
            }
    model_policy = load_model_policy()
    selected_backend = backend or get_backend(
        backend_name,
        config=config,
        policy=model_policy.to_dict(),
    )
    policy_decision = validate_model_load_request(
        clean_name,
        selected_backend.name,
        str(config.get("default_mode", "FAST")),
        policy=model_policy,
    )
    if not policy_decision.allowed:
        _METRICS["backend_name"] = selected_backend.name
        _METRICS["backend_status"] = "BLOCKED_BY_POLICY"
        _METRICS["last_load_status"] = "BLOCKED"
        _update_active_metrics()
        return {
            "status": "BLOCKED",
            "model_name": clean_name,
            "backend": selected_backend.name,
            "backend_status": "BLOCKED_BY_POLICY",
            "load_time_ms": _elapsed_ms(started),
            "errors": policy_decision.errors,
            "warnings": policy_decision.warnings,
            "backend_result": {
                "status": "BLOCKED",
                "model_name": clean_name,
                "backend": selected_backend.name,
                "loaded": False,
                "errors": policy_decision.errors,
                "warnings": policy_decision.warnings,
            },
            "policy_decision": policy_decision.to_dict(),
        }
    try:
        health = selected_backend.health_check()
        load = selected_backend.load_model(clean_name)
    except Exception as exc:
        error = _backend_exception_error("backend_load_failed", exc)
        _METRICS["backend_name"] = selected_backend.name
        _METRICS["backend_status"] = "FAILED"
        _METRICS["last_load_status"] = "FAILED"
        _update_active_metrics()
        return {
            "status": "FAILED",
            "model_name": clean_name,
            "backend": selected_backend.name,
            "backend_status": "FAILED",
            "load_time_ms": _elapsed_ms(started),
            "errors": [error],
            "warnings": [],
            "backend_result": {
                "status": "FAILED",
                "model_name": clean_name,
                "backend": selected_backend.name,
                "loaded": False,
                "errors": [error],
                "warnings": [],
            },
            "policy_decision": policy_decision.to_dict(),
        }
    _METRICS["backend_name"] = selected_backend.name
    _METRICS["backend_status"] = health.status
    _METRICS["last_load_status"] = load.status
    if not load.loaded:
        _update_active_metrics()
        return {
            "status": load.status,
            "model_name": clean_name,
            "backend": selected_backend.name,
            "backend_status": health.status,
            "load_time_ms": _elapsed_ms(started),
            "errors": load.errors,
            "warnings": [*health.warnings, *load.warnings],
            "backend_result": load.to_dict(),
            "policy_decision": policy_decision.to_dict(),
        }
    if not _LOADED_MODELS:
        _LOADED_MODELS.append(clean_name)
        _ACTIVE_BACKEND = selected_backend
        _METRICS["load_count"] = int(_METRICS["load_count"]) + 1
        _record_event("load", clean_name, selected_backend.name)
    _update_active_metrics()
    return {
        "status": "LOADED",
        "model_name": clean_name,
        "backend": selected_backend.name,
        "backend_status": health.status,
        "load_time_ms": _elapsed_ms(started),
        "errors": [],
        "warnings": [*health.warnings, *load.warnings],
        "backend_result": load.to_dict(),
        "policy_decision": policy_decision.to_dict(),
    }


def unload_model(
    model_name: str,
    backend_name: str | None = None,
    *,
    backend: ModelBackend | None = None,
) -> dict[str, Any]:
    """Unload one logical model if it is active."""

    global _ACTIVE_BACKEND
    started = perf_counter()
    clean_name = model_name.strip()
    config = _load_config()
    model_policy = load_model_policy()
    selected_backend = _ACTIVE_BACKEND if clean_name in _LOADED_MODELS else None
    selected_backend = selected_backend or backend or get_backend(
        backend_name,
        config=config,
        policy=model_policy.to_dict(),
    )
    try:
        unload = selected_backend.unload_model(clean_name)
    except Exception as exc:
        error = _backend_exception_error("backend_unload_failed", exc)
        unload_payload = {
            "status": "FAILED",
            "model_name": clean_name,
            "backend": selected_backend.name,
            "unloaded": False,
            "errors": [error],
            "warnings": [],
        }
    else:
        unload_payload = unload.to_dict()
    _METRICS["backend_name"] = selected_backend.name
    _METRICS["last_unload_status"] = str(unload_payload["status"])
    if clean_name in _LOADED_MODELS:
        _LOADED_MODELS.remove(clean_name)
        _METRICS["unload_count"] = int(_METRICS["unload_count"]) + 1
        _record_event("unload", clean_name, selected_backend.name)
        _ACTIVE_BACKEND = None
    _update_active_metrics()
    return {
        "status": unload_payload["status"],
        "model_name": clean_name,
        "backend": selected_backend.name,
        "unload_time_ms": _elapsed_ms(started),
        "errors": unload_payload["errors"],
        "warnings": unload_payload["warnings"],
        "backend_result": unload_payload,
    }


def get_loaded_models() -> list[str]:
    """Return currently loaded logical models."""

    return list(_LOADED_MODELS)


def get_runtime_metrics() -> dict[str, Any]:
    """Return runtime metrics without mutating protected areas."""

    _update_active_metrics()
    return {**_METRICS, "events": list(_METRICS["events"])}


def record_generate_status(backend_name: str, status: str) -> None:
    """Record backend generation status without changing loaded model state."""

    _METRICS["backend_name"] = backend_name
    _METRICS["last_generate_status"] = status
    _update_active_metrics()


def reset_runtime_state() -> None:
    """Reset logical loader state for tests and deterministic smoke runs."""

    global _ACTIVE_BACKEND
    if _ACTIVE_BACKEND is not None and _LOADED_MODELS:
        try:
            _ACTIVE_BACKEND.unload_model(_LOADED_MODELS[0])
        except Exception:
            pass
    _ACTIVE_BACKEND = None
    _LOADED_MODELS.clear()
    _METRICS.update(
        {
            "load_count": 0,
            "unload_count": 0,
            "active_models": 0,
            "parallel_llm_loads": 0,
            "peak_active_models": 0,
            "peak_vram_mb": 0,
            "backend_name": "mock",
            "backend_status": "UNKNOWN",
            "last_load_status": "UNKNOWN",
            "last_generate_status": "UNKNOWN",
            "last_unload_status": "UNKNOWN",
            "events": [],
        }
    )


def _load_config() -> dict[str, Any]:
    try:
        payload = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"max_loaded_models": 1, "allow_parallel_llms": False}
    return payload if isinstance(payload, dict) else {"max_loaded_models": 1, "allow_parallel_llms": False}


def _update_active_metrics() -> None:
    active = len(_LOADED_MODELS)
    _METRICS["active_models"] = active
    _METRICS["peak_active_models"] = max(int(_METRICS["peak_active_models"]), active)
    _METRICS["parallel_llm_loads"] = max(0, active - 1)
    _METRICS["peak_vram_mb"] = max(int(_METRICS["peak_vram_mb"]), _estimate_vram_mb(_LOADED_MODELS[0]) if active else 0)


def _record_event(action: str, model_name: str, backend_name: str) -> None:
    _METRICS["events"].append(
        {
            "action": action,
            "model_name": model_name,
            "backend": backend_name,
            "active_models": len(_LOADED_MODELS),
        }
    )


def _estimate_vram_mb(model_name: str) -> int:
    lowered = model_name.lower()
    if "14b" in lowered:
        return 14000
    if "qwen3" in lowered:
        return 7000
    return 4096


def _elapsed_ms(started: float) -> int:
    return max(0, int((perf_counter() - started) * 1000))


def _backend_exception_error(prefix: str, exc: Exception) -> str:
    detail = str(exc).strip()
    return f"{prefix}:{type(exc).__name__}" + (f":{detail}" if detail else "")
