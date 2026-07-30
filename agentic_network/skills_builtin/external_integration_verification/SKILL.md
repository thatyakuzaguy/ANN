# External Integration Verification

Provider, webhook, credential-boundary, idempotency, and approved HTTPS health checks.

## Actions

- inspect: Inspect provider, webhook, credential, retry, and idempotency boundaries.
- probe: Probe explicitly allowlisted HTTPS integration health endpoints.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
