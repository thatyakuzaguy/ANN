# Desktop Validation

Native desktop lifecycle, packaging, accessibility, installer, and update evidence.

## Actions

- analyze: Inspect native desktop packaging, lifecycle, accessibility, and update readiness.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
