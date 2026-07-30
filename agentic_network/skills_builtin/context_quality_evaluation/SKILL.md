# Context Quality Evaluation

Retrieval precision, recall, stale context, grounding, and token-budget quality evidence.

## Actions

- evaluate: Measure retrieval precision, recall, stale context, and token-budget quality.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
