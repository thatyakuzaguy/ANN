# Dependency Remediation

Bounded dependency risk ranking, update planning, verification, and rollback evidence without installs.

## Actions

- analyze: Rank vulnerable, incompatible, and stale dependencies using local manifest evidence.
- plan: Prepare a bounded dependency update, verification, and rollback plan without installing packages.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
