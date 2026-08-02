# Cross Store Consistency

Database, cache, queue, search, outbox, reconciliation, and idempotency verification.

## Actions

- inspect: Inspect database, cache, queue, search, outbox, reconciliation, and idempotency boundaries.
- run: Run only approved cross-store consistency tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
