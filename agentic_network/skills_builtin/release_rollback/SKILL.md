# Release Rollback

Upgrade, rollback, compatibility, data-preservation, and approved rollback verification.

## Actions

- inspect: Inspect upgrade, rollback, data preservation, and version compatibility evidence.
- run: Run only an approved release rollback verification recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
