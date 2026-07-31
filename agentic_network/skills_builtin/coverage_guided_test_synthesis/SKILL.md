# Coverage Guided Test Synthesis

Coverage-gap, surviving-mutant, branch-risk, and workspace-only test synthesis plans.

## Actions

- analyze: Rank uncovered branches and surviving mutants using supplied coverage evidence.
- generate: Generate a bounded test-gap plan only inside the skill workspace.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
