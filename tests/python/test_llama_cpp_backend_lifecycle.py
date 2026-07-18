from __future__ import annotations

import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import agentic_network.runtime_engine.backends.llama_cpp_backend as llama_backend_module
import agentic_network.runtime_engine.executor as executor
import agentic_network.runtime_engine.loader as loader
from agentic_network.runtime_engine.backends.llama_cpp_backend import LlamaCppBackend
from agentic_network.runtime_engine.model_policy import ModelPolicy


MODEL_NAME = "local_gpu_model"


@dataclass(frozen=True)
class _Record:
    name: str
    model_name: str
    backend: str
    path: str
    enabled: bool = True
    n_gpu_layers: int = -1
    context_tokens: int = 2048
    max_tokens: int = 64
    temperature: float = 0.1
    main_gpu: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _Inventory:
    def __init__(self, record: _Record) -> None:
        self.record = record

    def to_dict(self) -> dict[str, Any]:
        return {"version": 1, "models": [self.record.to_dict()], "errors": [], "warnings": []}


class _FakeLlama:
    instances: list[_FakeLlama] = []
    fail_generation = False

    def __init__(self, **kwargs: Any) -> None:
        self.load_options = kwargs
        self.generation_calls: list[tuple[str, dict[str, Any]]] = []
        self.close_calls = 0
        self.__class__.instances.append(self)

    def __call__(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        self.generation_calls.append((prompt, kwargs))
        if self.__class__.fail_generation:
            raise RuntimeError("fake generation failed")
        return {
            "choices": [{"text": "local completion"}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 2},
        }

    def close(self) -> None:
        self.close_calls += 1


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    loader.reset_runtime_state()
    _FakeLlama.instances.clear()
    _FakeLlama.fail_generation = False
    yield
    loader.reset_runtime_state()


def test_executor_reuses_one_backend_instance_without_socket_or_subprocess(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    record = _record(tmp_path)
    binding = _fake_binding(gpu=True)
    backend_instances: list[LlamaCppBackend] = []
    dll_calls: list[str] = []

    _patch_executor_runtime(monkeypatch, record, binding)
    monkeypatch.setattr(
        llama_backend_module,
        "configure_windows_runtime_dll_paths",
        lambda: dll_calls.append("configured") or [],
    )

    def create_backend(_name: str, *, policy: dict[str, Any]) -> LlamaCppBackend:
        backend = LlamaCppBackend(policy)
        backend_instances.append(backend)
        return backend

    def fail_registry_lookup(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("loader must reuse the executor backend instance")

    def fail_external_io(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("llama_cpp backend must remain in-process and offline")

    monkeypatch.setattr(executor, "get_backend", create_backend)
    monkeypatch.setattr(loader, "get_backend", fail_registry_lookup)
    monkeypatch.setattr(socket, "socket", fail_external_io)
    monkeypatch.setattr(socket, "create_connection", fail_external_io)
    monkeypatch.setattr(subprocess, "run", fail_external_io)

    result = executor.execute_agent_runtime("code", "Implement locally", run_dir=tmp_path / "run")

    assert result.status == "SUCCESS"
    assert result.backend_name == "llama_cpp"
    assert result.load_status == "LOADED"
    assert result.generate_status == "SUCCESS"
    assert result.unload_status == "UNLOADED"
    assert result.active_models == 0
    assert result.parallel_llm_loads == 0
    assert len(backend_instances) == 1
    assert len(_FakeLlama.instances) == 1
    assert _FakeLlama.instances[0].load_options["n_gpu_layers"] == -1
    assert _FakeLlama.instances[0].generation_calls
    assert _FakeLlama.instances[0].close_calls == 1
    assert dll_calls == ["configured"]
    assert loader.get_runtime_metrics()["peak_active_models"] == 1


def test_backend_rejects_binding_without_native_gpu_offload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    record = _record(tmp_path)
    monkeypatch.setattr(llama_backend_module, "_resolve_model_record", lambda _name: record)
    monkeypatch.setitem(sys.modules, "llama_cpp", _fake_binding(gpu=False))

    backend = LlamaCppBackend({"allow_real_model_load": True})
    result = backend.load_model(MODEL_NAME)

    assert result.status == "UNAVAILABLE"
    assert result.loaded is False
    assert "llama_cpp_native_gpu_offload_required" in result.errors
    assert _FakeLlama.instances == []


def test_executor_unloads_when_llama_generation_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    record = _record(tmp_path)
    _FakeLlama.fail_generation = True
    _patch_executor_runtime(monkeypatch, record, _fake_binding(gpu=True))
    backend = LlamaCppBackend(_real_policy().to_dict())
    monkeypatch.setattr(executor, "get_backend", lambda *_args, **_kwargs: backend)

    result = executor.execute_agent_runtime("code", "Fail safely", run_dir=tmp_path / "run")

    assert result.status == "FAILED"
    assert result.generate_status == "FAILED"
    assert result.unload_status == "UNLOADED"
    assert result.active_models == 0
    assert loader.get_loaded_models() == []
    assert len(_FakeLlama.instances) == 1
    assert _FakeLlama.instances[0].close_calls == 1
    assert backend._model is None


def test_backend_accepts_explicit_partial_gpu_offload_for_oversized_model(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    record = _record(tmp_path, n_gpu_layers=24)
    monkeypatch.setattr(llama_backend_module, "_resolve_model_record", lambda _name: record)
    monkeypatch.setitem(sys.modules, "llama_cpp", _fake_binding(gpu=True))

    backend = LlamaCppBackend({"allow_real_model_load": True})
    result = backend.load_model(MODEL_NAME)

    assert result.status == "LOADED"
    assert result.loaded is True
    assert _FakeLlama.instances[0].load_options["n_gpu_layers"] == 24
    assert backend.unload_model(MODEL_NAME).unloaded is True


def test_backend_does_not_return_unclosed_reasoning(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    record = _record(tmp_path)
    monkeypatch.setattr(llama_backend_module, "_resolve_model_record", lambda _name: record)
    monkeypatch.setitem(sys.modules, "llama_cpp", _fake_binding(gpu=True))
    monkeypatch.setattr(
        _FakeLlama,
        "__call__",
        lambda self, prompt, **kwargs: {"choices": [{"text": "<think>hidden"}]},
    )
    backend = LlamaCppBackend({"allow_real_model_load": True})
    assert backend.load_model(MODEL_NAME).loaded is True

    result = backend.generate(MODEL_NAME, "prompt")

    assert result.text == ""
    assert result.status == "FAILED"
    assert "llama_cpp_empty_output_after_reasoning_cleanup" in result.errors
    backend.unload_model(MODEL_NAME)


def _record(tmp_path: Path, *, n_gpu_layers: int = -1) -> _Record:
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"fake gguf")
    return _Record(
        name=MODEL_NAME,
        model_name=MODEL_NAME,
        backend="llama_cpp",
        path=str(model_path),
        n_gpu_layers=n_gpu_layers,
    )


def _fake_binding(*, gpu: bool) -> SimpleNamespace:
    return SimpleNamespace(
        Llama=_FakeLlama,
        llama_supports_gpu_offload=lambda: gpu,
    )


def _real_policy() -> ModelPolicy:
    return ModelPolicy(
        version=1,
        allow_real_model_load=True,
        allow_model_download=False,
        allow_training=False,
        allow_adapter_write=False,
        allow_dataset_write=False,
        max_loaded_models=1,
        vram_policy="SEQUENTIAL",
        default_backend="mock",
        allowed_backends=["mock", "llama_cpp"],
        errors=[],
        warnings=[],
    )


def _patch_executor_runtime(
    monkeypatch: pytest.MonkeyPatch,
    record: _Record,
    binding: SimpleNamespace,
) -> None:
    policy = _real_policy()
    route = SimpleNamespace(
        status="READY",
        agent_name="code",
        selected_model=MODEL_NAME,
        mode="FAST",
        warnings=[],
        errors=[],
    )
    monkeypatch.setitem(sys.modules, "llama_cpp", binding)
    monkeypatch.setattr(llama_backend_module, "_resolve_model_record", lambda _name: record)
    monkeypatch.setattr(executor, "resolve_model_route", lambda *_args, **_kwargs: route)
    monkeypatch.setattr(executor, "load_model_inventory", lambda: _Inventory(record))
    monkeypatch.setattr(executor, "resolve_model_record", lambda _name: record)
    monkeypatch.setattr(executor, "load_model_policy", lambda: policy)
    monkeypatch.setattr(loader, "load_model_policy", lambda: policy)
