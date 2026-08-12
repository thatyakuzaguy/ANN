# ANN Local Model Backends

ANN runs model inference locally and routes every model through one sequential
runtime. Model weights are never stored in this public repository and are not
downloaded by setup or the installer.

## Supported Roles

| Inventory ID | Intended role | Backend |
|---|---|---|
| `qwen3_4b_conversation_orchestrator` | ANN conversation and request handoff | GPU-capable `llama_cpp` GGUF runtime |
| `qwen3_8b_product_v9_repaired_v2_bullets` | product and requirements work | GPU-capable `llama_cpp` GGUF runtime; private adapter not distributed or enabled by the public inventory |
| `qwen2_5_coder_7b_v5` | implementation and repair | GPU-capable `llama_cpp` GGUF runtime |
| `deepseek_r1_distill_qwen_14b` | POWERFUL review and reasoning | GPU-capable `llama_cpp` GGUF runtime |

The inventory contains paths and policy, not redistribution rights. Operators
must supply legally authorized model files and acknowledge their applicable
licenses.

## Real Activation Evidence

The repository preserves load, inference, benchmark, and safe-rollback records
under `outputs/model_activation/release_verified`. The records show that each
model path used by ANN reached real inference and returned to:

```text
active_models = 0
parallel_llm_loads = 0
```

The release soak and autonomous project campaigns independently preserve peak
runtime telemetry. This evidence establishes runtime activation, not model
quality for every task or a right to redistribute model weights.

## Sequential GPU Policy

ANN enforces:

- `active_models <= 1`;
- `max_loaded_models = 1`;
- `parallel_llm_loads = 0`;
- `vram_policy = SEQUENTIAL`;
- explicit unload verification between routed stages;
- fail-closed activation when the configured GPU backend is unavailable.

POWERFUL and Qwen3 stages are never parallel. The API exposes current and peak
provider metrics so Desktop and release validators can detect a policy breach.

## Register A Model

The Desktop **Models** view can register a user-supplied GGUF from D: or E:.
ANN calculates SHA-256, records license acknowledgement, validates the storage
policy, and does not load the file during registration. Real runtime enablement
requires a GPU-capable `llama_cpp` binding and the existing activation gates.

For Hugging Face models or adapters, configure the existing inventory and
runtime policy. ANN does not modify model weights, adapters, datasets, or
training data during inference.

## Hardware Boundary

The primary validation workstation used an RTX 3060 Ti with 8 GB VRAM, Ryzen 5
2600, and 32 GB DDR4. Quantization, context length, backend build, and model
size determine whether a configuration fits. DeepSeek 14B POWERFUL execution
may require aggressive offload and is slower than smaller routed stages.

## Diagnostics

```powershell
python scripts\runtime\check_llama_cpp_cuda.py
python scripts\runtime\check_ann_runtime_backend.py
python scripts\runtime\verify_autonomous_capability.py
```

All diagnostics are bounded and use the existing runtime. They do not install
packages, download models, train, quantize, or mutate local model assets.
