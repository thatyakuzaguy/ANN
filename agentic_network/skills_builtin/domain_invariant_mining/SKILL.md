# Domain Invariant Mining

Repository-grounded candidate business invariants and reviewable invariant catalogs.

## Actions

- analyze: Mine candidate business invariants from models, schemas, guards, tests, and requirements.
- generate: Generate a reviewable invariant catalog only inside the skill workspace.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
