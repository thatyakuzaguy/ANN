# Service Virtualization

Deterministic workspace-only mock contracts for external service boundaries and failures.

## Actions

- inspect: Inspect external service boundaries, fixtures, webhooks, latency, and failure modes.
- generate: Generate deterministic mock-service contracts only inside the skill workspace.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
