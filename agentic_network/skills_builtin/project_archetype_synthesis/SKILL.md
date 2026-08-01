# Project Archetype Synthesis

Deterministic product classification and workspace-only architecture blueprint synthesis.

## Actions

- analyze: Classify the repository and requested product using deterministic cross-domain evidence.
- synthesize: Generate a bounded architecture blueprint only inside the skill workspace.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
