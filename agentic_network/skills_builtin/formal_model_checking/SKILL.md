# Formal Model Checking

TLA+, PlusCal, Alloy, invariant, state-space, and approved bounded model checking.

## Actions

- inspect: Inspect TLA+, PlusCal, Alloy, and explicit invariant evidence.
- run: Run only an approved bounded model-checking recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
