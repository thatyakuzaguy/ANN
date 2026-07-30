# Fuzz Property Testing

Fuzz targets, property tests, schemas, seeds, crash evidence, and approved Compose execution.

## Actions

- inspect: Inspect fuzz targets, property tests, schemas, seeds, and crash-corpus readiness.
- plan: Create bounded fuzz and property-testing targets from repository evidence.
- run: Run only an approved fuzz test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
