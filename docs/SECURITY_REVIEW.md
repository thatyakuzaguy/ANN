# Security Review

Date: 2026-08-12

## Scope And Decision

This is the repository's internal automated security assessment for ANN 1.0.1.
It records implemented controls and reproducible checks. It is not an independent
security review, penetration test, legal opinion, or security guarantee.

Internal automated decision: `PASSED_WITH_EXTERNAL_REVIEW_PENDING`.

## Implemented Controls

- Approval Center gates generated writes, patch application, dependency changes,
  command recipes, deployment actions, and other sensitive effects.
- Commands are selected from bounded recipes; ANN does not expose arbitrary
  `shell=True` execution.
- Workspace and protected-path guards keep generated effects inside approved
  roots and preserve audit decisions.
- The sequential runtime enforces `active_models <= 1`,
  `parallel_llm_loads = 0`, explicit unload checks, and rollback evidence.
- Model weights, private adapters, datasets, credentials, databases, memory,
  conversations, generated runs, and build caches are excluded from Git.
- Generated-project verification covers auth, RBAC, APIs, migrations, Docker,
  dependency integrity, browser E2E, and cross-domain failure diagnostics.
- Installer validation is fail-closed for the trusted-publisher channel and
  verifies hashes, signing evidence, clean-machine evidence, startup, and
  uninstallation.
- The public manifest hashes every distributable source/evidence file and rejects
  unlisted, oversized, missing, or modified content.

## Dependency Status

- Next.js: 16.3.0
- Vitest: 4.1.10
- PostCSS: 8.5.23, with no vulnerable nested copy
- `npm audit --audit-level=moderate`: zero findings
- `npm audit --omit=dev --audit-level=moderate`: zero findings
- API requirements: no known vulnerabilities reported by `pip-audit`
- Optional model requirements: no known vulnerabilities reported by `pip-audit`
- Isolated llama.cpp binding: no known vulnerabilities in the audited binding;
  vulnerable optional DiskCache is excluded and persistent caching is disabled

The PostCSS resolution contract is enforced by
`scripts/security/verify-postcss-resolution.mjs`. The llama.cpp dependency
contract is enforced by `scripts/security/verify_llama_cpp_dependency_policy.py`.

## Release Security Gates

```powershell
python -m ruff check agentic_network apps packages tests/python scripts
python -m pytest tests/python -q
node scripts/security/verify-postcss-resolution.mjs
npm audit --audit-level=moderate
npm audit --omit=dev --audit-level=moderate
npm --workspace apps/web run lint
npm --workspace apps/web run test
npm --workspace apps/web run build
npm --workspace apps/web run e2e
docker compose config --quiet
docker compose build api web
```

GitHub additionally runs gitleaks, CodeQL for Python and JavaScript/TypeScript,
and rejects open high or critical CodeQL alerts for the tested ref.

## Independent Review Boundary

Production assurance remains blocked until a named independent reviewer assesses
the exact release commit and records a decision with zero unresolved critical or
high findings. The prepared packet is
`outputs/release_assurance/external/independent_security_review_report.md`.
No automated result is substituted for that human decision.
