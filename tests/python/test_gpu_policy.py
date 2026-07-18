from __future__ import annotations

from types import SimpleNamespace

from agentic_network.models.gpu_policy import llama_cpp_supports_gpu_offload


def test_gpu_offload_probe_uses_native_function() -> None:
    module = SimpleNamespace(
        llama_supports_gpu_offload=lambda: True,
        LLAMA_SUPPORTS_GPU_OFFLOAD=False,
    )

    assert llama_cpp_supports_gpu_offload(module) is True


def test_gpu_offload_probe_supports_legacy_constant() -> None:
    module = SimpleNamespace(LLAMA_SUPPORTS_GPU_OFFLOAD=True)

    assert llama_cpp_supports_gpu_offload(module) is True


def test_gpu_offload_probe_is_unknown_when_native_probe_fails() -> None:
    def fail() -> bool:
        raise RuntimeError("native probe failed")

    assert llama_cpp_supports_gpu_offload(SimpleNamespace(llama_supports_gpu_offload=fail)) is None
