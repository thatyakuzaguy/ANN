# Model License Review Preparation

Status: `PENDING_QUALIFIED_REVIEW`

The public repository contains inventory identifiers and paths, not model weights.
The following upstream license candidates were collected from official model
pages. This collection is factual source preparation and is not legal approval.

| ANN inventory ID | Upstream model | Candidate license | Official source | Distribution |
|---|---|---|---|---|
| `qwen2_5_coder_7b_v5` | Qwen2.5-Coder-7B-Instruct | Apache-2.0 | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/blob/main/LICENSE | user supplied |
| `qwen3_4b_conversation_orchestrator` | Qwen3-4B-Instruct-2507 | Apache-2.0 | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE | user supplied |
| `qwen3_8b_product_v9_repaired_v2_bullets` | Qwen3-8B | Apache-2.0 | https://huggingface.co/Qwen/Qwen3-8B/blob/main/LICENSE | user supplied; private adapter excluded |
| `deepseek_r1_distill_qwen_14b` | DeepSeek-R1-Distill-Qwen-14B | MIT | https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B/blob/main/LICENSE | user supplied |

## Required reviewer decision

A qualified reviewer must confirm the exact provenance of each local GGUF,
quantization rights, notices, derivative/adaptor obligations, commercial-use
conditions, and the operator-facing acknowledgement flow. The reviewer must then
populate `reviewed_by` and choose `APPROVED` or `USER_SUPPLIED_ONLY` per model.

No model weights or adapter contents are included in this repository or installer.
