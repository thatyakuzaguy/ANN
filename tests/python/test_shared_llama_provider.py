from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from agentic_engineering_network.shared import providers
from agentic_engineering_network.shared.config import Settings
from agentic_engineering_network.shared.providers import LlamaCppProvider, Prompt


class _FakeLlama:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.closed = False

    def __call__(self, prompt: str, **kwargs: object) -> dict[str, object]:
        assert "<|im_start|>system" in prompt
        assert kwargs["max_tokens"] == 32
        return {"choices": [{"text": "READY"}]}

    def close(self) -> None:
        self.closed = True


def _provider(model_path: Path, *, gpu_layers: int = -1) -> LlamaCppProvider:
    return LlamaCppProvider(
        model_path=model_path,
        context_size=512,
        max_tokens=32,
        temperature=0.1,
        gpu_layers=gpu_layers,
        main_gpu=0,
    )


def test_llama_cpp_provider_uses_gpu_and_releases_model(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"gguf")
    fake_llm = _FakeLlama()
    dll_configured: list[bool] = []

    monkeypatch.setattr(providers, "ensure_inside_root", lambda path: path)
    monkeypatch.setattr(providers, "configure_windows_runtime_dll_paths", lambda: dll_configured.append(True))
    monkeypatch.setattr(providers, "llama_cpp_supports_gpu_offload", lambda module: True)
    monkeypatch.setitem(
        __import__("sys").modules,
        "llama_cpp",
        SimpleNamespace(Llama=lambda **kwargs: (setattr(fake_llm, "kwargs", kwargs) or fake_llm)),
    )

    provider = _provider(model_path)
    response = provider.generate(Prompt(system="system", user="user"))

    assert response.content == "READY"
    assert fake_llm.kwargs["n_gpu_layers"] == -1
    assert fake_llm.kwargs["main_gpu"] == 0
    assert dll_configured == [True]
    provider.close()
    assert fake_llm.closed is True
    assert provider._llm is None  # noqa: SLF001


def test_llama_cpp_provider_rejects_cpu_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"gguf")
    monkeypatch.setattr(providers, "ensure_inside_root", lambda path: path)

    with pytest.raises(RuntimeError, match="forces CPU inference"):
        _provider(model_path, gpu_layers=0).generate(Prompt(system="system", user="user"))


def test_llama_cpp_provider_rejects_cpu_only_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"gguf")
    monkeypatch.setattr(providers, "ensure_inside_root", lambda path: path)
    monkeypatch.setattr(providers, "configure_windows_runtime_dll_paths", lambda: None)
    monkeypatch.setattr(providers, "llama_cpp_supports_gpu_offload", lambda module: False)
    monkeypatch.setitem(__import__("sys").modules, "llama_cpp", SimpleNamespace())

    with pytest.raises(RuntimeError, match="without GPU offload"):
        _provider(model_path).generate(Prompt(system="system", user="user"))


def test_agent_provider_uses_declared_route_and_runtime_options(monkeypatch: pytest.MonkeyPatch) -> None:
    from agentic_network.model_routing import router
    from agentic_network.runtime_engine import model_inventory, model_policy

    record = SimpleNamespace(
        name="qwen2_5_coder_7b_v5",
        backend="llama_cpp",
        path="D:/ANN/models/qwen.gguf",
        path_exists=True,
        enabled=True,
        context_tokens=8192,
        max_tokens=1024,
        temperature=0.15,
        n_gpu_layers=-1,
        main_gpu=0,
    )
    route = SimpleNamespace(status="VALID", selected_model=record.name, mode="FAST", errors=[])
    decision = SimpleNamespace(allowed=True, errors=[])
    captured: list[tuple[object, ...]] = []

    monkeypatch.setattr(router, "resolve_model_route", lambda agent, mode: route)
    monkeypatch.setattr(model_inventory, "resolve_model_record", lambda name: record)
    monkeypatch.setattr(model_policy, "load_model_policy", lambda: object())
    monkeypatch.setattr(model_policy, "validate_model_load_request", lambda *args, **kwargs: decision)
    monkeypatch.setattr(providers, "LlamaCppProvider", lambda *args: captured.append(args) or "provider")

    result = providers.build_provider_for_agent(Settings(ai_provider="llama_cpp"), "Backend Engineer Agent")

    assert result == "provider"
    assert captured == [(Path(record.path), 8192, 1024, 0.15, -1, 0)]
