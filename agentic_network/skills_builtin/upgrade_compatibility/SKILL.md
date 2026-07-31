# Upgrade Compatibility

Runtime, framework, database, deprecation, migration, and approved upgrade verification.

## Actions

- inspect: Inspect runtime, framework, database, deprecation, and migration compatibility.
- run: Run only an approved upgrade-compatibility test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
