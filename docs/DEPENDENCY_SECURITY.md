# Dependency Security

## Active Temporary Exception

`llama-cpp-python` depends on `diskcache 5.6.3`. The Python advisory database
reports `PYSEC-2026-2447` / `CVE-2025-69872`: DiskCache uses pickle for cache
serialization, so an attacker who can replace files in a cache directory may
cause code execution when a trusted process reads them. No fixed DiskCache
release is available as of 2026-07-17.

ANN isolates `llama-cpp-python` in the optional `local-models` dependency group.
The base API, public CI, and CPU API image do not install it. The GPU image and
operators who enable local inference still receive it because it is required by
the selected backend.

Risk controls:

- use local inference only on a single-user, trusted workstation;
- keep model and cache directories on access-controlled local storage;
- never restore model caches from untrusted archives or shared writable paths;
- do not expose the llama.cpp cache directory to generated project containers;
- preserve ANN's protected-path and sequential-runtime policies;
- audit the optional requirements for every release and remove this exception
  immediately when a fixed upstream version is available.

The GitHub security workflow ignores only `PYSEC-2026-2447` for the optional
requirements file; any additional advisory still fails the job. Review date:
2026-08-17.

## JavaScript Override

Next.js 16.2.10 declares `postcss 8.4.31`, which is affected by
`GHSA-qx2v-qp2m-jg93`. npm's automatic remediation proposes an unsafe downgrade
to Next 9.3.3 because no patched stable Next release is currently available.

ANN pins and overrides PostCSS to `8.5.20`, removes the vulnerable nested copy
from the lockfile, and verifies both the lockfile and installed dependency tree
with `scripts/security/verify-postcss-resolution.mjs`. `npm audit` reports zero
findings and CI blocks at moderate severity. The verifier intentionally fails
when Next changes its internal pin so the override can be reassessed and
removed as soon as a stable upstream release carries the fix.
