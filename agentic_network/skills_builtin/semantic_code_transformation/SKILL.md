# Semantic Code Transformation

Token-aware symbol impact analysis and workspace-only Python rename diffs.

## Actions

- analyze: Locate typed symbol rename targets and estimate their repository impact.
- prepare: Prepare a token-aware Python symbol rename diff in the skill workspace without applying it.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
