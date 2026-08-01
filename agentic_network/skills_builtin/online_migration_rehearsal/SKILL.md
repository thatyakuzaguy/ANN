# Online Migration Rehearsal

Expand-contract, backfill, locking, compatibility, tenancy, and rollback rehearsal.

## Actions

- inspect: Inspect expand-contract ordering, locks, backfills, compatibility, and rollback evidence.
- run: Run only an approved isolated online-migration rehearsal inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
