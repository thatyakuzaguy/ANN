# Schema Drift Data Evolution

ORM, migration, tenant, backfill, index, and approved schema-drift verification.

## Actions

- inspect: Compare ORM, migrations, indexes, tenant scope, backfills, and destructive operations.
- run: Run only an approved Alembic schema-drift check inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
