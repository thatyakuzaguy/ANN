# Production Hardening Plan

## Authentication

- Rotate refresh tokens on every use.
- Store only refresh token hashes.
- Add account lockout and suspicious-login audit events.
- Enforce strong password policy or external identity provider.

## Authorization

- Enforce tenant-scoped queries at repository boundaries.
- Permission dependencies are scaffolded through `app/rbac.py`.
- Add service-account scopes for integrations.

## Platform Security

- Add rate limiting at API gateway or middleware.
- Set strict CORS by environment.
- Security headers and CSP are scaffolded in `app/security_headers.py`.
- Move secrets to a vault provider.
- Add dependency scanning and image scanning in CI.

## Reliability

- Use Alembic for all schema changes.
- Add backups and restore drills.
- Add structured app logs, metrics, and trace IDs.
- Add queue workers for workflows and integrations.
