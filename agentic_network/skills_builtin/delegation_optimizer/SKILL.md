# Delegation Optimizer

Duplicate-work, ownership, context-budget, load, and skill-coverage optimization.

## Actions

- analyze: Detect duplicate delegation, missing ownership, context waste, and skill coverage gaps.
- plan: Create a bounded evidence-based delegation plan without executing subagents.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
