# Behavioral Acceptance Oracle

Requirement-to-observable-behavior traceability and approved acceptance verification.

## Actions

- analyze: Map requirements and acceptance criteria to observable behavior and test evidence.
- run: Run only an approved behavioral-oracle test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
