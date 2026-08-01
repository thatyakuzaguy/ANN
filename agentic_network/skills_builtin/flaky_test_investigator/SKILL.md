# Flaky Test Investigator

Repeated outcome, timing variance, shared-state, and flaky-test investigation.

## Actions

- analyze: Classify repeated test outcomes, timing variance, shared-state signals, and failure signatures.
- run: Run only an approved repeated-test investigation recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
