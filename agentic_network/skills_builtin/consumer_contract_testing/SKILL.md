# Consumer Contract Testing

Consumer/provider contract compatibility evidence and approved Compose execution.

## Actions

- analyze: Inspect consumer/provider contracts, versions, fixtures, and compatibility evidence.
- run: Run only an approved consumer-contract recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
