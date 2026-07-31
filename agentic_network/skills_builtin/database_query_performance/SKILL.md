# Database Query Performance

Query-plan, index, N+1, lock, budget, and approved database-performance verification.

## Actions

- inspect: Inspect query plans, indexes, N+1 signals, locks, and database performance budgets.
- run: Run only an approved database-performance test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
