# Deployment Verification

Deployment manifests, health checks, rollback, TLS, and isolated smoke verification.

## Actions

- inspect: Inspect deployment manifests, health checks, TLS, and rollback readiness.
- smoke: Start and smoke-test an approved isolated local deployment.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
