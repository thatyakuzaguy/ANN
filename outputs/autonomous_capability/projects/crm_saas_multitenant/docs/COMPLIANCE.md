# Compliance Baseline

## Implemented Scaffold

- Tenant-scoped business endpoints require `X-Tenant-ID`.
- RBAC permissions are centralized in `app/rbac.py`.
- Stripe billing endpoints avoid hard-coded secrets and require environment configuration.
- Signed integration webhooks use HMAC verification.
- Security headers include CSP, frame denial, MIME sniffing protection, referrer policy, and permissions policy.
- GitHub Actions runs secret scanning, API tests, web build, and Docker Compose validation.

## Before Internet Deployment

- Move secrets to a managed vault.
- Add persistent audit log storage with retention policy.
- Add rate limiting at gateway or middleware.
- Add refresh token rotation and replay detection.
- Add tenant-aware database indexes and repository-level policy tests.
- Add SAST, dependency scanning, image scanning, and SBOM generation.
- Add backup/restore drills and incident runbooks.
