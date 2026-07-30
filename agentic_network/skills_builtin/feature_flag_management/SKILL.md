# Feature Flag Management

Feature-flag inventory, ownership, rollout, stale-flag, cleanup, and rollback evidence.

## Actions

- analyze: Inventory feature flags, defaults, ownership, rollout, and stale-flag evidence.
- cleanup_plan: Prepare a safe flag retirement and rollback plan without changing code.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
