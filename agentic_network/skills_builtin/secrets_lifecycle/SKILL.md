# Secrets Lifecycle

Value-free secret ownership, rotation, revocation, redaction, and rollback planning.

## Actions

- inspect: Inspect secret references, ownership, rotation, revocation, redaction, and storage boundaries.
- plan: Prepare a value-free secret rotation and rollback plan requiring human approval.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
