# Data Pipeline

ETL lineage, schema, quality, idempotency, and backfill evidence.

## Actions

- analyze: Inspect ETL lineage, schemas, quality checks, idempotency, and backfills.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
