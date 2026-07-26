# ANN 1.0 Release Contract

ANN 1.0 is the first stable local-first Community release. It is accepted only
when the source revision passes Python, Ruff, frontend, production build,
dependency audit, Docker, and release-manifest verification.

## Supported Product Boundary

- Windows 11 x64 desktop and source execution.
- Local API and Desktop UI without a cloud account.
- User-supplied GGUF models through `llama_cpp` with sequential loading.
- Supervised or full approval-gated software engineering runs.
- Durable run, approval, conversation, audit, and generated-project artifacts.
- SaaS/API and canvas-game foundations with bounded autonomous correction.

## First Run

1. Install or launch ANN from the verified Community package.
2. Open **Models** and select **Add Model**.
3. Choose a licensed `.gguf` file on D: or E:.
4. Review the model identifier, execution mode, and license acknowledgement.
5. Register the model. ANN computes SHA-256 and updates the inventory without
   loading the model or accessing the network.
6. Select **Enable Real Runtime**. ANN enables `llama_cpp` only after its
   native binding reports GPU offload readiness.

At all times `max_loaded_models=1`, `parallel_llm_loads=0`, and
`vram_policy=SEQUENTIAL` remain mandatory.

## Recovery

If the backend closes after generation created a durable proposal, the run is
shown as **interrupted** with **Resume checkpoint**. Resume is an explicit user
action. ANN re-enters lifecycle verification only after checking persisted
approval decisions. A run interrupted before the durable proposal boundary is
blocked and must be restarted.

## Distribution Channels

The **Community** channel is source-available and may include an unsigned
portable Windows installer. Published SHA-256 manifests provide integrity but
do not establish publisher identity. Windows may display SmartScreen.

The **trusted-publisher** channel remains unavailable until setup and uninstall
binaries are timestamped with a real trusted Authenticode certificate and the
same artifacts pass validation on an independent clean Windows 11 machine.

## Non-Claims

ANN does not guarantee market success, legal compliance, production security,
or a correct commercial product from one prompt. Repeated failures,
contract ambiguity, invalid tests, unavailable infrastructure, and exhausted
retry budgets stop with evidence for qualified human review.
