# Infrastructure Validation

Terraform, Kubernetes, Helm, CI, policy, and infrastructure safety evidence.

## Actions

- analyze: Inspect Terraform, Kubernetes, CI, secrets, and infrastructure safety.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
