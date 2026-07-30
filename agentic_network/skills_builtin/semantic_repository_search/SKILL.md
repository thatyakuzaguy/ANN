# Semantic Repository Search

Bounded intent-term repository path and symbol search without model loading.

## Actions

- query: Search bounded repository paths and symbols using intent terms without loading a model.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
