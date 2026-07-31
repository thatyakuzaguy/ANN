# User Journey Synthesis

Repository-grounded user journeys and workspace-only E2E journey specifications.

## Actions

- analyze: Map user stories, routes, roles, and acceptance criteria into bounded journeys.
- generate: Generate reviewable E2E journey specifications only inside the skill workspace.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
