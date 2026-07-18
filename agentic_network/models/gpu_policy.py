"""GPU execution policy helpers for local LLM backends."""

from __future__ import annotations

from typing import Any


def llama_cpp_supports_gpu_offload(llama_cpp_module: Any) -> bool | None:
    """Return native llama.cpp GPU-offload capability across binding versions."""

    probe = getattr(llama_cpp_module, "llama_supports_gpu_offload", None)
    if callable(probe):
        try:
            return bool(probe())
        except Exception:
            return None
    legacy = getattr(llama_cpp_module, "LLAMA_SUPPORTS_GPU_OFFLOAD", None)
    return legacy if isinstance(legacy, bool) else None


def require_cuda_available(torch_module: Any, backend_name: str) -> None:
    """Fail fast when a Transformers/Unsloth backend would fall back to CPU."""

    cuda = getattr(torch_module, "cuda", None)
    if cuda is None or not bool(cuda.is_available()):
        raise RuntimeError(
            f"{backend_name} requires CUDA/GPU execution. CPU inference is disabled for "
            "ANN local LLMs to avoid runaway host CPU/RAM usage."
        )


def require_gguf_gpu_offload(n_gpu_layers: int, backend_name: str) -> None:
    """Fail fast when a llama.cpp GGUF backend is explicitly configured for CPU."""

    if n_gpu_layers == 0:
        raise RuntimeError(
            f"{backend_name} is configured with n_gpu_layers=0, which forces CPU inference. "
            "Use -1 for full GPU offload or a positive layer count."
        )
