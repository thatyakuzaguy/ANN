# Git History Intelligence

Bounded Git churn, co-change, ownership, and regression-hotspot evidence.

## Actions

- analyze: Compute bounded churn, co-change, ownership, and regression-hotspot evidence from Git history.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
