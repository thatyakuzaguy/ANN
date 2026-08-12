# Dependency Security

## llama.cpp Disk Cache Removal

`llama-cpp-python 0.3.32` declares `diskcache`, whose latest release is affected
by `PYSEC-2026-2447` / `CVE-2025-69872`. No fixed DiskCache release is available.
ANN therefore removes the vulnerable component instead of accepting the risk.

The safe runtime contract:

- installs the required NumPy, typing and Jinja dependencies explicitly;
- installs the pinned llama.cpp binding with `--no-deps`;
- rejects any DiskCache wheel or installed distribution during release builds;
- routes every ANN llama.cpp import through `load_secure_llama_cpp()`;
- replaces the binding's disk-cache reference with a fail-closed stub;
- raises `PersistentLlamaCacheDisabledError` if persistent caching is requested;
- permits the default no-cache mode and in-memory `LlamaRAMCache` only;
- audits the complete explicit runtime closure without an advisory ignore.

`scripts/security/verify_llama_cpp_dependency_policy.py` fails CI if DiskCache,
an unsafe direct import, a non-isolated binding installation, or an advisory
suppression is reintroduced. Existing embedded runtimes are migrated with the
transactional `scripts/security/harden_llama_cpp_runtime.py` tool. The migration
loads no model and performs no inference.

## JavaScript Dependency Gate

PostCSS versions before `8.5.10` are affected by `GHSA-qx2v-qp2m-jg93`.
Next.js 16.3.0 now declares the patched PostCSS 8.5.23 directly, so ANN removed
the temporary root and Next-specific overrides used by earlier release
candidates. The web workspace keeps an explicit PostCSS 8.5.23 development
dependency for its own build configuration.

`scripts/security/verify-postcss-resolution.mjs` verifies that Next declares a
patched version, the lockfile resolves PostCSS 8.5.23, and no vulnerable nested
copy exists. `npm audit` reports zero findings and CI blocks at moderate
severity. The verifier fails if any of those properties regress.
