# Backup Restore

PostgreSQL backup, restore, retention, and recovery verification through approved Compose recipes.

## Actions

- inspect: Inspect backup, restore, retention, and recovery readiness.
- backup: Create an approved PostgreSQL logical backup through Compose.
- restore: Restore an approved PostgreSQL logical backup through Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
