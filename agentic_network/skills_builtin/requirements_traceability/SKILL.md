# Requirements Traceability

Requirement-to-architecture, source, test, artifact, and release traceability evidence.

## Actions

- analyze: Trace requirements through architecture, source, tests, and release evidence.
- verify: Identify orphaned requirements and unsubstantiated implementation evidence.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
