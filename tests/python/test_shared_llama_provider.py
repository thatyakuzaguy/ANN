from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from types import SimpleNamespace

import pytest

from agentic_engineering_network.shared import providers
from agentic_engineering_network.shared.config import Settings, ensure_model_read_path
from agentic_engineering_network.shared.providers import (
    LlamaCppProvider,
    Prompt,
    get_provider_runtime_metrics,
    reset_provider_runtime_metrics,
)


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


class _FakeChatLlama:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def create_chat_completion(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        content = self.responses.pop(0)
        return {"choices": [{"message": {"content": content}}]}


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
    reset_provider_runtime_metrics()
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"gguf")
    fake_llm = _FakeLlama()
    dll_configured: list[bool] = []

    monkeypatch.setattr(providers, "ensure_model_read_path", lambda path: path)
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
    loaded = get_provider_runtime_metrics()
    assert loaded["active_models"] == 1
    assert loaded["peak_active_models"] == 1
    assert loaded["parallel_llm_loads"] == 0
    assert loaded["total_loads"] == 1
    assert loaded["loaded_models"] == ["model.gguf"]
    assert fake_llm.kwargs["n_gpu_layers"] == -1
    assert fake_llm.kwargs["main_gpu"] == 0
    assert dll_configured == [True]
    provider.close()
    assert fake_llm.closed is True
    assert provider._llm is None  # noqa: SLF001
    unloaded = get_provider_runtime_metrics()
    assert unloaded["active_models"] == 0
    assert unloaded["loaded_models"] == []
    assert unloaded["total_unloads"] == 1
    assert unloaded["unload_failures"] == 0


def test_llama_cpp_provider_rejects_cpu_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"gguf")
    monkeypatch.setattr(providers, "ensure_model_read_path", lambda path: path)

    with pytest.raises(RuntimeError, match="forces CPU inference"):
        _provider(model_path, gpu_layers=0).generate(Prompt(system="system", user="user"))


def test_llama_cpp_provider_rejects_cpu_only_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"gguf")
    monkeypatch.setattr(providers, "ensure_model_read_path", lambda path: path)
    monkeypatch.setattr(providers, "configure_windows_runtime_dll_paths", lambda: None)
    monkeypatch.setattr(providers, "llama_cpp_supports_gpu_offload", lambda module: False)
    monkeypatch.setitem(__import__("sys").modules, "llama_cpp", SimpleNamespace())

    with pytest.raises(RuntimeError, match="without GPU offload"):
        _provider(model_path).generate(Prompt(system="system", user="user"))


def test_qwen3_provider_disables_thinking_and_retries_empty_final_answer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "Qwen3-8B-Q4_K_M.gguf"
    model_path.write_bytes(b"gguf")
    fake_llm = _FakeChatLlama(["<think>unfinished reasoning</think>", "FINAL ANSWER"])
    monkeypatch.setattr(providers, "ensure_model_read_path", lambda path: path)
    provider = _provider(model_path)
    provider._llm = fake_llm  # noqa: SLF001

    response = provider.generate(Prompt(system="system", user="solve this"))

    assert response.content == "FINAL ANSWER"
    assert len(fake_llm.calls) == 2
    first_messages = fake_llm.calls[0]["messages"]
    assert isinstance(first_messages, list)
    assert str(first_messages[1]["content"]).endswith("/no_think")
    assert fake_llm.calls[0]["temperature"] == 0.1
    assert fake_llm.calls[1]["temperature"] == 0.0
    assert "previous response" in str(fake_llm.calls[1]["messages"][0]["content"]).lower()


def test_llama_cpp_provider_stops_after_one_empty_final_answer_retry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"gguf")
    fake_llm = _FakeChatLlama(["<think>one</think>", "<think>two</think>"])
    monkeypatch.setattr(providers, "ensure_model_read_path", lambda path: path)
    provider = _provider(model_path)
    provider._llm = fake_llm  # noqa: SLF001

    with pytest.raises(RuntimeError, match="one deterministic final-only retry"):
        provider.generate(Prompt(system="system", user="solve this"))

    assert len(fake_llm.calls) == 2


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


def test_external_model_requires_explicit_read_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_root = Path("E:/ANN-test/external-models")
    model_path = model_root / "model.gguf"

    monkeypatch.delenv("AEN_MODEL_READ_ROOTS", raising=False)
    with pytest.raises(ValueError, match="explicit read-only model root"):
        ensure_model_read_path(model_path)

    monkeypatch.setenv("AEN_MODEL_READ_ROOTS", str(model_root))
    assert ensure_model_read_path(model_path) == model_path.resolve()


def test_model_read_root_does_not_allow_path_escape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_root = Path("E:/ANN-test/models")
    outside = Path("E:/ANN-test/outside.gguf")
    monkeypatch.setenv("AEN_MODEL_READ_ROOTS", str(model_root))

    with pytest.raises(ValueError, match="explicit read-only model root"):
        ensure_model_read_path(model_root / ".." / outside.name)


def test_system_drive_model_root_remains_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    blocked_root = Path("C:/ANN/models")
    monkeypatch.setenv("AEN_MODEL_READ_ROOTS", str(blocked_root))

    with pytest.raises(ValueError, match="system drive is blocked"):
        ensure_model_read_path(blocked_root / "model.gguf")


def test_provider_metrics_endpoint_reports_canonical_state() -> None:
    from app.api.routes import provider_runtime_metrics

    reset_provider_runtime_metrics()

    public = provider_runtime_metrics()

    assert public["active_models"] == 0
    assert "loaded_models" not in public


def test_llama_cpp_provider_serializes_model_lifetimes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    reset_provider_runtime_metrics()
    first_path = tmp_path / "first.gguf"
    second_path = tmp_path / "second.gguf"
    first_path.write_bytes(b"gguf")
    second_path.write_bytes(b"gguf")
    first_loaded = Event()
    allow_first_close = Event()
    second_loaded = Event()
    created: list[_FakeLlama] = []

    def create(**kwargs: object) -> _FakeLlama:
        instance = _FakeLlama()
        instance.kwargs = kwargs
        created.append(instance)
        if len(created) == 1:
            first_loaded.set()
        else:
            second_loaded.set()
        return instance

    monkeypatch.setattr(providers, "ensure_model_read_path", lambda path: path)
    monkeypatch.setattr(providers, "configure_windows_runtime_dll_paths", lambda: None)
    monkeypatch.setattr(providers, "llama_cpp_supports_gpu_offload", lambda module: True)
    monkeypatch.setattr(providers, "load_secure_llama_cpp", lambda: SimpleNamespace(Llama=create))
    first = _provider(first_path)
    second = _provider(second_path)

    def use_first() -> None:
        first.generate(Prompt(system="system", user="first"))
        allow_first_close.wait(timeout=5)
        first.close()

    def use_second() -> None:
        second.generate(Prompt(system="system", user="second"))
        second.close()

    first_thread = Thread(target=use_first)
    second_thread = Thread(target=use_second)
    first_thread.start()
    assert first_loaded.wait(timeout=2)
    second_thread.start()
    assert second_loaded.wait(timeout=0.2) is False
    assert get_provider_runtime_metrics()["active_models"] == 1
    allow_first_close.set()
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)

    assert second_loaded.is_set()
    metrics = get_provider_runtime_metrics()
    assert metrics["peak_active_models"] == 1
    assert metrics["peak_parallel_llm_loads"] == 0
    assert metrics["active_models"] == 0
