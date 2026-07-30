# Requirements Contract

Versioned requirements, acceptance criteria, and deterministic contract arbitration.

## Actions

- refine: Create a versioned, testable product contract from user intent.
- arbitrate: Resolve contract ownership with the existing deterministic arbitration gate.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
