# ANN Release Readiness

ANN 1.0.1 has two deliberately separate distribution channels:

- **Community/source:** reproducible source plus an unsigned local Windows
  installer. Users verify hashes, inspect the source, and explicitly approve
  Windows execution.
- **Trusted Windows publisher:** the same validated payload, signed and
  timestamped with a trusted Authenticode certificate and transferred through
  an independent clean-machine and production-assurance process.

The first channel is technically ready. The second remains fail-closed until
its external evidence is real and complete.

## Verified Technical State

- Installer RC gate: `RC_READY`.
- Embedded Python: present at `D:/ANN/runtime/python/python.exe`.
- Offline wheelhouse: `HASH_VERIFIED`.
- Runtime package audit: `PACKAGE_AUDIT_READY` with no missing package.
- Qwen2.5-Coder, Qwen3 4B, Qwen3 8B, and DeepSeek 14B: preserved real
  load/inference/unload evidence.
- Runtime policy: `active_models <= 1`, `parallel_llm_loads = 0`, and
  `vram_policy = SEQUENTIAL`.
- Autonomous capability: seven of seven real project scenarios passed.
- Release soak: 8.000001 hours, 20 of 20 runs passed across SaaS, web, and
  algorithm-service archetypes.
- Rollback: no model remained loaded after the validated campaigns.

## Public Evidence

- `outputs/autonomous_capability/EVIDENCE_MANIFEST.json` binds 589 files and
  seven portable project packets. Aggregate SHA-256:
  `76c2cd8be184c8c065a2bee96f356dcd5e9a64b5b40ff8ee19399885bdad37a7`.
- `outputs/release_assurance/official-soak/soak_validation.json` records the
  official 20-run campaign. Its report SHA-256 is
  `7ced199e39db320ac08c84be94b6018433a049eb3837bcf398ad865252614ed3`.
- `outputs/model_activation/release_verified` contains the numbered real model
  activation and rollback artifacts plus an integrity manifest.

These records prove the checks they describe. They do not constitute a legal,
security, product-market, or model-license opinion.

## Reproduce The Gates

```powershell
$env:PYTHONPATH="."
python scripts\runtime\verify_autonomous_capability.py --write-manifest
python scripts\runtime\verify_release_assurance.py --json
python scripts\runtime\verify_git_source_release.py --json
python -m pytest tests/python -q
python -m ruff check agentic_network apps packages tests/python scripts
npm --workspace apps/web run test
npm --workspace apps/web run build
npm audit --audit-level=moderate
```

The assurance command currently returns exit code `2` because it correctly
rejects pending external records. The technical checks and soak evidence remain
valid independently of those human gates.

## Remaining Trusted-Publisher Work

- Sign `ANN_Setup.exe` and `ANN_Uninstall.exe` with a real, non-self-signed,
  timestamped Authenticode certificate.
- Validate the exact hashes on a separate clean Windows 11 machine.
- Complete a two-machine/two-GPU hardware matrix.
- Obtain independent security and qualified legal review.
- Record qualified license decisions for all four configured model families.
- Obtain human acceptance for at least three generated projects from three
  archetypes.

ANN never converts placeholders into approvals and never claims a
trusted-publisher release while any of these records is absent.

## Installer States

- `RC_BLOCKED`: required local runtime or installer input is missing.
- `RC_READY_FOR_MANUAL_PACKAGING`: source is ready but payload assembly is
  incomplete.
- `RC_READY`: local runtime, scripts, Desktop entrypoint, wheel hashes, and
  package checks pass.
- `FINAL_RELEASE_READY`: only possible after trusted signing, transferred clean
  machine validation, and all production-assurance records pass.

See [the installer guide](installer/README_INSTALLER.md) and
[release assurance contract](docs/RELEASE_ASSURANCE.md) for the exact external
workflow.
