# Test Generation

Repository-grounded test-gap analysis and deterministic workspace-only test skeletons.

## Actions

- analyze: Identify test gaps from source, routes, contracts, and existing test evidence.
- generate: Generate a deterministic test plan and safe test skeleton in the skill workspace.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
