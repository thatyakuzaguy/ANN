# Mutation Testing

Mutation configuration, survivor evidence, and approved Compose mutation execution.

## Actions

- inspect: Inspect mutation configuration, test strength, and surviving-mutant evidence.
- run: Run only an approved mutation recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
