# Architecture Refactor Execution

Entropy-driven refactor evidence and dry-run validation through existing patch gates.

## Actions

- analyze: Rank architecture refactor candidates using entropy, cycles, coupling, and impact evidence.
- prepare: Validate an explicit refactor diff through the existing dry-run Patch Workspace gate.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
