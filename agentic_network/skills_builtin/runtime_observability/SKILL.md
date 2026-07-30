# Runtime Observability

Bounded local runtime, log, port, resource, and failure-correlation evidence.

## Actions

- snapshot: Collect bounded local runtime, log, port, and resource evidence.
- correlate: Correlate runtime evidence with recent project failures.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
