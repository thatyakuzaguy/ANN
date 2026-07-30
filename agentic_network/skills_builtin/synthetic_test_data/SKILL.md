# Synthetic Test Data

Privacy-safe deterministic fixture planning and workspace-only JSON generation.

## Actions

- plan: Design privacy-safe deterministic fixture coverage from a bounded schema.
- generate: Generate deterministic synthetic JSON fixtures only inside the skill workspace.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
