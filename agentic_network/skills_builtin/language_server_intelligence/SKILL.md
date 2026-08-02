# Language Server Intelligence

Language-server configuration, typed source coverage, diagnostics, and approved type-analysis execution.

## Actions

- inspect: Inspect language-server configuration, typed source coverage, and supplied diagnostics.
- run: Run only an approved Python or web type-analysis recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
