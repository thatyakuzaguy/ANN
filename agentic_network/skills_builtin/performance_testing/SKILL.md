# Performance Testing

Performance budgets, benchmark readiness, and approved sandboxed performance recipes.

## Actions

- analyze: Inspect performance budgets, benchmarks, and load-test readiness.
- run: Run an allowlisted performance recipe in the project sandbox.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
