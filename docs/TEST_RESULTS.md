# Test Results

Date: 2026-08-12

## Final 1.0.1 Release-Candidate Validation

The release-candidate source tree was validated on Windows with Python 3.11,
Node.js 24, Docker Desktop 29.5.2, and the pinned npm lockfile. The exact final
results were:

```text
D:\AgenticEngineeringNetwork\outputs\ci-python311\Scripts\python.exe -m pytest tests/python -q --basetemp D:\ANN-CI-Tmp\pytest-final-confirmed
1958 passed, 55 skipped, 1 warning in 614.85s (0:10:14)

python -m ruff check agentic_network apps packages tests/python scripts
All checks passed!

npm ci
added 274 packages; found 0 vulnerabilities

npm --workspace apps/web run lint
TypeScript passed

npm --workspace apps/web run test
6 test files passed, 29 tests passed

npm --workspace apps/web run build
Next.js 16.3.0 production build passed

npm --workspace apps/web run e2e
2 passed

npm --workspace apps/desktop run package
Wrote new app to apps/desktop/dist/ANN-win32-x64
```

The one Python warning is Starlette's upstream deprecation notice for using
`httpx` through `starlette.testclient`; it does not fail a test. A first clean
Python 3.11 run caught a stale assertion that still required ANN's removed
PostCSS override. The test was corrected to require Next.js 16.3.0's direct
patched PostCSS 8.5.23 dependency, and the complete suite above was rerun.
The final post-audit suite also includes regressions for cross-provider model
load serialization, private-path redaction, per-attempt soak lifecycle metrics,
portable evidence confinement, cached-assessment recomputation, and public
release allowlist enforcement.

Dependency and repository security gates passed:

```text
npm audit --audit-level=moderate
found 0 vulnerabilities

npm audit --omit=dev --audit-level=moderate
found 0 vulnerabilities

pip-audit -r apps/api/requirements.txt
No known vulnerabilities found

pip-audit -r apps/api/requirements-models.txt
No known vulnerabilities found

pip-audit --disable-pip --no-deps -r apps/api/requirements-llama-cpp.txt
No known vulnerabilities found

Gitleaks Git-history scan
67 commits scanned, 8.10 MB, no leaks found
```

Both `ann-api:latest` and `ann-web:latest` built successfully from the release
source. Docker Desktop's BuildKit content store contained a missing historical
blob, so the final local build used Docker's classic builder; the source and
images themselves completed successfully. `docker compose config --quiet`
also passed. The post-audit images are API
`sha256:19346b865b09d330458be2dc70a42f39153151fe1a27b64aa259141cae89d87a`
and web
`sha256:e81f32c3e368444ffadc8479875f0f6b8417e5a6b1973d2663322b0ddb3dc3a0`.

The autonomous-capability verifier passed all seven scenarios and regenerated
the portable 589-file evidence manifest. The official soak remains
hash-verified at 8.000001 active hours, 20 of 20 runs, zero counted failures,
all three required archetypes, `active_models <= 1`, and
`parallel_llm_loads = 0`. The release-candidate handoff verified 23 files with
no protected content, and the Git/source gate returned
`GIT_SOURCE_RELEASE_READY`.

The final offline bundle was rebuilt from the installed runtime and the latest
Desktop package, then independently re-read and verified:

```text
E:\ANN-Release-Bundles\ANN-1.0.1-final-post-audit-20260812
17,330 payload files
4,380,271,817 archive bytes
3 split parts
SHA-256 7db8b030a0100d5085cab61efdf7eef6717f03b4cd35209d7fad442eeeabb109
OFFLINE_RELEASE_BUNDLE_VERIFIED
```

The post-audit parts were then assembled and installed into a new isolated
`E:` root. The embedded verifier reported Python 3.11.9, PySide6 6.11.1,
Desktop importable, and status `VALID`. Launching the installed `ANN.exe`
returned HTTP 200 from both the local API and standalone web UI. Closing the
Desktop left zero listeners on ports 8000 and 3001. The default uninstaller
correctly preserved user data; a second invocation with the explicit project,
model, and output removal switches removed the test root with zero residual
entries.

Production assurance intentionally returns exit code `2` and
`PRODUCTION_ASSURANCE_PARTIAL`: a second independent machine/GPU, independent
security review, qualified legal and model-license decisions, human acceptance
of three generated projects, and trusted Authenticode signing are external
gates that ANN does not fabricate. They do not block the source/unsigned
Community channel.

Strict mypy is configured but is not a release or GitHub Actions gate. An
exploratory run still reports substantial gradual-typing debt, including
optional GPU/UI dependencies without stubs; this release does not claim a
clean strict-mypy result.

Date: 2026-07-28

## Controlled Subagent Validation

```text
python -m ruff check agentic_network packages tests/python scripts
All checks passed!

python -m pytest tests/python -q
1612 passed, 54 skipped in 825.89s (0:13:45)

npm --workspace apps/web run lint
TypeScript passed

npm --workspace apps/web run test
5 test files passed, 22 tests passed

npm --workspace apps/web run build
Next.js 16.2.12 production build passed

npm --workspace apps/web run e2e
1 passed

npm audit --audit-level=moderate
found 0 vulnerabilities
```

The new regression coverage verifies catalog completeness, parent ownership,
cycle and depth blocking, protected paths, host-affecting tool rejection,
credential redaction, bounded context, per-parent and per-run budgets,
specialist failure fallback, read-only APIs, Agent Office attribution, and the
one-active-model invariant under concurrent runs.

Date: 2026-07-27

## Stable 1.0.1 Source Validation

```text
python -m pytest tests/python -q
1599 passed, 54 skipped in 848.36s (0:14:08)

python -m ruff check agentic_network apps packages tests/python scripts
All checks passed!
```

The 54 skips are the explicit public-release allowlist for private model,
runtime, signing, and historical evidence that is deliberately absent from
Git. Portable orchestration, safety, API, installer, Desktop, and project
builder tests execute normally.

```text
npm audit --audit-level=moderate
found 0 vulnerabilities

npm --workspace apps/web run lint
TypeScript passed

npm --workspace apps/web run test -- --run
5 test files passed, 22 tests passed

npm --workspace apps/web run build
Next.js 16.2.12 production build passed

npm --workspace apps/web run e2e
1 passed

npm --workspace apps/desktop run package
Wrote new app to apps/desktop/dist/ANN-win32-x64
```

The unsigned Community installer was reconstructed from its split release
parts, installed into an isolated D: root, and checked with the embedded
Python 3.11.9 runtime. Installed Desktop startup returned HTTP 200 from both
the local API and standalone web UI, the model inventory returned `READY`,
closing Desktop removed its child listeners, and the native uninstaller
returned exit code 0 with zero residual files.

```text
Final ANN 1.0.1 offline Community bundle
16,897 files
4,400,360,892 bytes
SHA-256 49a6d33c847497245c9177ea8e4bcec1c5892d500d7adb85d6adbd3b0b22ece4
3 parts, each below GitHub's 2 GiB release-asset limit
```

The final `main` revision also passed Test, Lint, Security Scan, Docker Build,
CodeQL, and GitHub's dependency graph update. CodeQL alert 58 was closed by
the public-diagnostic hardening in 1.0.1. The repository reports zero open
CodeQL, Dependabot, or secret-scanning alerts.

Real local GPU lifecycle smokes passed for Qwen3 4B, Qwen2.5-Coder 7B, Qwen3
8B, and DeepSeek-R1-Distill-Qwen 14B. Every smoke ended with
`active_models=0`, `parallel_llm_loads=0`, and safe mode restored. DeepSeek
used bounded partial GPU offload (`n_gpu_layers=28`) because its quantized
weights exceed the workstation's 8 GB VRAM. These are load/run/unload and
rollback checks, not claims that a short diagnostic prompt measures product
quality.

## Stable 0.1.5 Validation

```text
GitHub Actions / Test
1574 passed, 54 skipped, 1 warning in 139.92s

npm audit --audit-level=moderate
found 0 vulnerabilities

npm --workspace apps/web run test
5 test files passed, 22 tests passed

npm --workspace apps/web run build
Next.js 16.2.10 production build passed
```

All five public workflows passed on the audited source commit: Test, Lint,
Security Scan, Docker Build, and CodeQL. The skips are the explicit public
allowlist for private release evidence and local model/runtime artifacts.

```text
Validated 0.1.5 offline bundle
16,892 files
4,379,225,421 bytes
SHA-256 3695494cf34c14593b0f51dc742327dbd336b1c2abdf95b98ed62711cbb54e68

Bundled install/runtime validation: VALID
Installed Sharp: 0.35.3
Desktop/API/web smoke: PASSED
Native uninstaller: exit 0, zero residual files

Python wheel SHA-256
ef5e00851fbca6a456aab09896bd8933d323732aad77b0959c3864e677fa108d
```

## Stable 0.1.4 Validation

```text
python -m pytest tests/python -q
1621 passed, 1 skipped in 976.32s
```

```text
python -m ruff check agentic_network apps packages tests scripts
All checks passed!
```

```text
npm --workspace apps/web run test
5 test files passed, 22 tests passed

npm --workspace apps/web run lint
TypeScript passed

npm --workspace apps/web run build
Next.js 16.2.10 production build passed

npm --workspace apps/web run e2e
1 passed
```

```text
npm --workspace apps/desktop run package
Wrote new app to apps/desktop/dist/ANN-win32-x64
```

```text
docker compose build api web
API and web images built from a clean Docker cache

docker compose up -d postgres api web
PostgreSQL healthy; API health/readiness 200; web 200
API container Docker daemon access: 29.5.2
API container Docker Compose: 5.1.4
```

```text
Release/installer/runtime/Docker focused suite
271 passed in 208.22s
```

```text
Validated release-candidate offline bundle
16,840 files
4,396,125,162 bytes
SHA-256 f334176cf3b0dd21c1a8526bd30de0feacb401dc76fcdb814d15574e9249f42b

Bundled install: PASSED
Embedded runtime and CUDA llama.cpp: PASSED
Installed API health: PASSED
Installed native Desktop: PASSED
Bundled uninstall with zero residual files: PASSED
```

Those values identify the release-candidate bundle used for the recorded
installer smoke. For every published bundle, the normative current size and
hashes are in `ANN_RELEASE_PARTS.json`, whose own checksum is published in
`ANN_RELEASE_PARTS.sha256`.

The stable source and unsigned portable distribution passed these local gates.
Trusted-publisher Windows distribution still requires a real Authenticode
certificate and validation on an independent clean Windows machine.

## Historical Development Evidence

```text
python -m pytest tests/python -q
41 passed in 4.81s
```

```text
python -m ruff check apps packages tests
All checks passed!
```

```text
npm --workspace apps/web run lint
TypeScript check passed.
```

```text
npm --workspace apps/web run test
2 tests passed
```

```text
npm --workspace apps/web run build
Next.js production build compiled successfully.
```

```text
docker compose config --quiet
Compose configuration passed.
```

```text
docker compose build api web
Timed out after more than 20 minutes while rebuilding the GPU API image.
The long-running build processes were stopped to avoid leaving Docker consuming host resources indefinitely.
```

```text
docker compose build
Docker images built successfully for api and web.
```

```text
docker compose build api
API image rebuilt successfully with llama-cpp-python and CUDA build tooling.
```

```text
docker compose up -d postgres api web
postgres, api, and web started successfully without Ollama.
```

```text
Invoke-RestMethod http://localhost:8000/api/health
{"status":"ok","service":"agentic-engineering-network-api"}
```

```text
Invoke-WebRequest http://localhost:3000
200
```

```text
npm --workspace apps/web run e2e
1 passed
```

```text
Browser visual verification
10 resizable panels found
10 detach buttons found
Detached panel mode rendered one full-window panel
Browser console errors: []
```

```text
docker compose exec -T api python -c "... LlamaCppProvider ..."
llama_cpp
qwen2.5-coder-7b-q4_k_m.gguf
OK
```

Direct local inference was verified against `D:\AgenticEngineeringNetwork\models\qwen2.5-coder-7b-q4_k_m.gguf` with the Ollama container stopped.

```text
Approval mode regression
supervised_wait=waiting_for_approval; pending=5
supervised_final=completed; pending=0
full_final=completed; pending=0; mode=full
```

Supervised approval mode pauses the run until all pending gates are resolved. Full approval mode auto-approves run gates, applies approved file effects, records audit events, and continues without manual clicks.

```text
Generated SaaS CRM regression
Prompt: Build me a SaaS CRM
Output: 35 generated project files
Path: D:\TesT\build-me-a-saas-crm-219e799e
Includes: apps/api, apps/web, apps/desktop, Alembic migrations, database/schema.sql, docker-compose.yml, docs, scripts
Python syntax check: passed
```

```text
Post-approval lifecycle regression
Prompt: Build me a SaaS CRM with advanced lifecycle
Run: 9bf689df-6f91-41bf-8b07-1a85239c0fb3
Output: 35 proposed files
Lifecycle status: passed
Steps: required_files, python_syntax, compose_static, web_static, alembic_migrations, desktop_packaging, security_review, release_package
Sandbox: D:\TesT\build-me-a-saas-crm-with-advanced-lifecycle-9bf689df\.aen\sandbox.json
Release ZIP: D:\TesT\build-me-a-saas-crm-with-advanced-lifecycle-9bf689df\.aen\release\build-me-a-saas-crm-with-advanced-lifecycle-9bf689df.zip
```

```text
docker run --rm --gpus all nvidia/cuda:12.6.3-base-ubuntu24.04 nvidia-smi
NVIDIA GeForce RTX 3060 Ti visible inside Docker
```

```text
docker compose exec -T api nvidia-smi
NVIDIA GeForce RTX 3060 Ti visible inside the API container
```

```text
docker compose exec -T api python3 -c "... LlamaCppProvider ... Reply exactly OK ..."
OK
GPU memory peaked around 5975 MiB during the Qwen load/inference window.
```

The high `VmmemWSL` CPU usage observed during `docker compose build api` was the one-time CUDA compilation of `llama-cpp-python`, not runtime inference.

```text
npm --workspace apps/desktop run package
Wrote new app to: dist\ANN-win32-x64
```

```text
D:\AgenticEngineeringNetwork\apps\desktop\dist\ANN-win32-x64\ANN.exe
Desktop packaged exe started: True
```

```text
D:\AgenticEngineeringNetwork\releases\AgenticEngineeringNetwork-0.1.1.zip
Desktop exe present, no excluded entries found.
```

Portable single-file packaging through electron-builder was not used because Windows blocked symlink creation while extracting the signing helper cache. The delivered Windows package uses an unpacked Electron app folder with a native `.exe`, which does not require opening an external browser.

```text
POST /api/runs with workspace_directory=C:\Temp\outside-aen
HTTP 400
Path must stay inside D:\AgenticEngineeringNetwork
```

Custom workspace selection is covered by Python tests and supports Windows paths under `D:\AgenticEngineeringNetwork`, mapped to Docker's `/workspace` volume internally.

```text
POST /api/runs with workspace_directory=D:\TesT
status=running
workspace_directory=D:\TesT
```

External project workspaces on `D:` are mapped to `/host-d` inside Docker.

```text
Approval effect regression
Approved file_create writes content to disk
```

```text
RunStore async regression
POST-style start returns status=running immediately
polling later reaches status=completed with 13 agent results
```

## Docker Repair Notes

Docker CLI is installed and available:

```text
Docker version 29.5.2
Docker Compose version v5.1.4
```

After enabling virtualization in BIOS and rebooting, Ubuntu was registered with WSL2:

```text
wsl --install -d Ubuntu --no-launch
Distribution installed successfully.
```

Docker Desktop still lacked the internal `docker-desktop` distro, so the existing Docker Desktop VHDX was registered in place:

```powershell
wsl --import-in-place docker-desktop "$env:LOCALAPPDATA\Docker\wsl\main\ext4.vhdx"
```

After restarting Docker Desktop, `docker info` reported a healthy Linux engine.
