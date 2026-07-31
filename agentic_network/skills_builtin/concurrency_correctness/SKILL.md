# Concurrency Correctness

Race, deadlock, lock, atomicity, cancellation, and approved concurrency verification.

## Actions

- inspect: Inspect locks, async cancellation, races, deadlocks, and atomicity boundaries.
- run: Run only approved deterministic concurrency tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
