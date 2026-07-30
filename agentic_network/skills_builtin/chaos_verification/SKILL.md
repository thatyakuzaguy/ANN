# Chaos Verification

Bounded non-destructive fault scenarios and approved Compose recovery verification.

## Actions

- inspect: Inspect bounded fault cases, recovery assertions, timeouts, and rollback evidence.
- run: Run only an approved non-destructive chaos test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
