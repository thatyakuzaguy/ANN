from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from threading import Lock

from agentic_engineering_network.shared.config import Settings, ensure_model_read_path
from agentic_network.models.gpu_policy import llama_cpp_supports_gpu_offload
from agentic_network.models.llama_cpp_security import load_secure_llama_cpp
from agentic_network.models.deepseek_gguf import clean_deepseek_output
from agentic_network.runtime_engine.windows_dlls import configure_windows_runtime_dll_paths


_PROVIDER_RUNTIME_LOCK = Lock()
_PROVIDER_LOAD_GATE = Lock()
_PROVIDER_RUNTIME_STATE: dict[str, object] = {
    "active_models": 0,
    "peak_active_models": 0,
    "parallel_llm_loads": 0,
    "peak_parallel_llm_loads": 0,
    "total_loads": 0,
    "total_unloads": 0,
    "unload_failures": 0,
    "loaded_models": [],
}


def get_provider_runtime_metrics() -> dict[str, object]:
    """Return process-local telemetry for canonical llama.cpp providers."""

    with _PROVIDER_RUNTIME_LOCK:
        return {
            **_PROVIDER_RUNTIME_STATE,
            "loaded_models": list(_PROVIDER_RUNTIME_STATE["loaded_models"]),
        }


def reset_provider_runtime_metrics() -> None:
    """Reset telemetry only when no provider model is currently loaded."""

    with _PROVIDER_RUNTIME_LOCK:
        if int(_PROVIDER_RUNTIME_STATE["active_models"]) != 0:
            raise RuntimeError("Cannot reset provider telemetry while a model is loaded.")
        _PROVIDER_RUNTIME_STATE.update(
            {
                "active_models": 0,
                "peak_active_models": 0,
                "parallel_llm_loads": 0,
                "peak_parallel_llm_loads": 0,
                "total_loads": 0,
                "total_unloads": 0,
                "unload_failures": 0,
                "loaded_models": [],
            }
        )


def _record_provider_load(model_path: Path) -> None:
    with _PROVIDER_RUNTIME_LOCK:
        loaded = list(_PROVIDER_RUNTIME_STATE["loaded_models"])
        loaded.append(model_path.name)
        active = len(loaded)
        parallel = max(0, active - 1)
        _PROVIDER_RUNTIME_STATE.update(
            {
                "active_models": active,
                "peak_active_models": max(
                    int(_PROVIDER_RUNTIME_STATE["peak_active_models"]), active
                ),
                "parallel_llm_loads": parallel,
                "peak_parallel_llm_loads": max(
                    int(_PROVIDER_RUNTIME_STATE["peak_parallel_llm_loads"]), parallel
                ),
                "total_loads": int(_PROVIDER_RUNTIME_STATE["total_loads"]) + 1,
                "loaded_models": loaded,
            }
        )


def _record_provider_unload(model_path: Path, *, failed: bool) -> None:
    with _PROVIDER_RUNTIME_LOCK:
        loaded = list(_PROVIDER_RUNTIME_STATE["loaded_models"])
        model = model_path.name
        if model in loaded:
            loaded.remove(model)
        _PROVIDER_RUNTIME_STATE.update(
            {
                "active_models": len(loaded),
                "parallel_llm_loads": max(0, len(loaded) - 1),
                "total_unloads": int(_PROVIDER_RUNTIME_STATE["total_unloads"]) + 1,
                "unload_failures": int(_PROVIDER_RUNTIME_STATE["unload_failures"])
                + int(failed),
                "loaded_models": loaded,
            }
        )


@dataclass(frozen=True)
class Prompt:
    system: str
    user: str


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    content: str


class AIProvider:
    name = "base"

    def generate(self, prompt: Prompt) -> ProviderResponse:
        raise NotImplementedError


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: Prompt) -> ProviderResponse:
        payload = {
            "model": self.model,
            "stream": False,
            "prompt": f"{prompt.system}\n\nUser request:\n{prompt.user}",
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        return ProviderResponse(provider=self.name, model=self.model, content=body.get("response", ""))


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, model: str) -> None:
        self.model = model
        self.api_key = os.environ.get("OPENAI_API_KEY", "")

    def generate(self, prompt: Prompt) -> ProviderResponse:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc
        text = ""
        for item in body.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    text += content.get("text", "")
        return ProviderResponse(provider=self.name, model=self.model, content=text)


class LlamaCppProvider(AIProvider):
    name = "llama_cpp"

    def __init__(
        self,
        model_path: Path,
        context_size: int,
        max_tokens: int,
        temperature: float,
        gpu_layers: int,
        main_gpu: int,
    ) -> None:
        self.model_path = ensure_model_read_path(model_path)
        if self.model_path.suffix.lower() != ".gguf":
            raise ValueError(f"Local llama.cpp model must be a GGUF file: {self.model_path}")
        self.model = self.model_path.name
        self.context_size = context_size
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.gpu_layers = gpu_layers
        self.main_gpu = main_gpu
        self._llm: object | None = None
        self._load_gate_held = False

    def _load(self) -> object:
        if not self.model_path.exists():
            raise RuntimeError(f"Local GGUF model not found: {self.model_path}")
        if self.gpu_layers == 0:
            raise RuntimeError(
                "LOCAL_MODEL_GPU_LAYERS=0 forces CPU inference. ANN local GGUF providers "
                "require GPU offload; use -1 or a positive layer count."
            )
        if self._llm is None:
            try:
                load_timeout = max(
                    1.0,
                    float(os.environ.get("AEN_MODEL_LOAD_GATE_TIMEOUT_SECONDS", "600")),
                )
            except ValueError:
                load_timeout = 600.0
            if not _PROVIDER_LOAD_GATE.acquire(timeout=load_timeout):
                raise RuntimeError(
                    "Timed out waiting for the sequential local-model load gate."
                )
            self._load_gate_held = True
            try:
                configure_windows_runtime_dll_paths()
                try:
                    llama_cpp = load_secure_llama_cpp()
                except ImportError as exc:
                    raise RuntimeError(
                        "llama-cpp-python is not installed. Run setup.ps1 or rebuild the API image."
                    ) from exc
                if llama_cpp_supports_gpu_offload(llama_cpp) is not True:
                    raise RuntimeError("llama-cpp-python was built without GPU offload support.")
                self._llm = llama_cpp.Llama(
                    model_path=str(self.model_path),
                    n_ctx=self.context_size,
                    n_threads=max(1, (os.cpu_count() or 4) - 1),
                    n_gpu_layers=self.gpu_layers,
                    main_gpu=self.main_gpu,
                    verbose=False,
                )
                _record_provider_load(self.model_path)
            except Exception:
                self._load_gate_held = False
                _PROVIDER_LOAD_GATE.release()
                raise
        return self._llm

    def _final_answer_prompt(self, prompt: Prompt, *, retry: bool) -> Prompt:
        directive = (
            "Return only the final answer. Do not emit analysis, hidden reasoning, or "
            "<think> blocks."
        )
        if retry:
            directive += " A previous response contained no usable final answer."
        user = prompt.user
        if "qwen3" in self.model.lower() and "/no_think" not in user.lower():
            user = f"{user.rstrip()}\n\n/no_think"
        return Prompt(system=f"{prompt.system.rstrip()}\n\n{directive}", user=user)

    def _generate_once(
        self,
        llm: object,
        prompt: Prompt,
        *,
        temperature: float,
    ) -> str:
        create_chat_completion = getattr(llm, "create_chat_completion", None)
        if callable(create_chat_completion):
            result = create_chat_completion(
                messages=[
                    {"role": "system", "content": prompt.system},
                    {"role": "user", "content": prompt.user},
                ],
                max_tokens=self.max_tokens,
                temperature=temperature,
            )
            first = result["choices"][0]
            message = first.get("message", {}) if isinstance(first, dict) else {}
            raw_content = str(message.get("content") or "")
        else:
            text_prompt = (
                "<|im_start|>system\n"
                f"{prompt.system}\n"
                "<|im_end|>\n"
                "<|im_start|>user\n"
                f"{prompt.user}\n"
                "<|im_end|>\n"
                "<|im_start|>assistant\n"
            )
            result = llm(  # type: ignore[operator]
                text_prompt,
                max_tokens=self.max_tokens,
                temperature=temperature,
                stop=["<|im_end|>", "<|im_start|>"],
            )
            raw_content = str(result["choices"][0]["text"])
        return clean_deepseek_output(raw_content).strip()

    def generate(self, prompt: Prompt) -> ProviderResponse:
        llm = self._load()
        content = self._generate_once(
            llm,
            self._final_answer_prompt(prompt, retry=False),
            temperature=self.temperature,
        )
        if not content:
            content = self._generate_once(
                llm,
                self._final_answer_prompt(prompt, retry=True),
                temperature=0.0,
            )
        if not content:
            raise RuntimeError(
                "Local model returned no final answer after one deterministic final-only retry."
            )
        return ProviderResponse(provider=self.name, model=self.model, content=content)

    def close(self) -> None:
        llm = self._llm
        self._llm = None
        if llm is None:
            return
        close = getattr(llm, "close", None)
        failed = False
        try:
            if callable(close):
                close()
        except Exception:
            failed = True
            raise
        finally:
            _record_provider_unload(self.model_path, failed=failed)
            if self._load_gate_held:
                self._load_gate_held = False
                _PROVIDER_LOAD_GATE.release()


class DeterministicLocalProvider(AIProvider):
    name = "deterministic-local"

    def generate(self, prompt: Prompt) -> ProviderResponse:
        idea = prompt.user.strip().replace("\n", " ")
        content = (
            "Decision: proceed with a secure, approval-gated full-stack architecture.\n"
            f"Rationale: the request '{idea[:160]}' requires product discovery, modular services, "
            "tests, docs, Docker packaging, and auditability before any generated file is committed."
        )
        return ProviderResponse(provider=self.name, model="rules-engine", content=content)


def build_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider in {"llama_cpp", "local_gguf", "qwen_direct"}:
        return LlamaCppProvider(
            settings.local_model_path,
            settings.local_model_context,
            settings.local_model_max_tokens,
            settings.local_model_temperature,
            settings.local_model_gpu_layers,
            settings.local_model_main_gpu,
        )
    if settings.ai_provider == "openai":
        return OpenAIProvider(settings.openai_model)
    if settings.ai_provider == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    return DeterministicLocalProvider()


def build_provider_for_agent(settings: Settings, agent_name: str, execution_mode: str = "FAST") -> AIProvider:
    """Build one policy-approved provider for one sequential ANN agent stage."""

    if settings.ai_provider not in {"llama_cpp", "local_gguf", "qwen_direct"}:
        return build_provider(settings)

    from agentic_network.model_routing.router import resolve_model_route
    from agentic_network.runtime_engine.model_inventory import resolve_model_record
    from agentic_network.runtime_engine.model_policy import load_model_policy, validate_model_load_request

    route = resolve_model_route(agent_name, execution_mode)
    if route.status not in {"VALID", "FALLBACK"}:
        raise RuntimeError(f"Model route blocked for {agent_name}: {route.errors}")
    record = resolve_model_record(route.selected_model)
    if record is None:
        raise RuntimeError(f"Routed model is not declared: {route.selected_model}")
    decision = validate_model_load_request(
        record.name,
        record.backend,
        route.mode,
        policy=load_model_policy(),
    )
    if not decision.allowed:
        raise RuntimeError(f"Routed model load blocked by policy: {','.join(decision.errors)}")
    if record.backend != "llama_cpp":
        raise RuntimeError(f"Routed model backend is not supported by the canonical local provider: {record.backend}")
    if not record.enabled or not record.path_exists:
        raise RuntimeError(f"Routed model is unavailable: {record.name} ({record.path})")
    return LlamaCppProvider(
        Path(record.path),
        record.context_tokens,
        record.max_tokens,
        record.temperature,
        record.n_gpu_layers,
        record.main_gpu,
    )
