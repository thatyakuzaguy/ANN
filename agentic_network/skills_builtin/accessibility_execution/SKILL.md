# Accessibility Execution

Automated and manual accessibility readiness plus approved Compose-based execution.

## Actions

- inspect: Inspect automated and manual accessibility execution readiness.
- run: Run only an approved accessibility package script inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
