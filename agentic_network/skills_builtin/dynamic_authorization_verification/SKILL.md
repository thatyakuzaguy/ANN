# Dynamic Authorization Verification

Endpoint, role, tenant, and authorization-boundary evidence plus approved tests.

## Actions

- inspect: Build an endpoint, role, tenant, and authorization-control verification matrix.
- run: Run only approved authorization-boundary tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
