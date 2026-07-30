# Adversarial Red Team

Non-destructive prompt, tool, approval, filesystem, and secret-boundary adversarial review.

## Actions

- analyze: Inspect prompt, tool, approval, filesystem, and secret boundaries for adversarial exposure.
- simulate: Generate a non-executing adversarial scenario matrix and expected defenses.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
