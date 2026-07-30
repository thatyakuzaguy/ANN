# Cloud Deployment

Provider-neutral identity, secret, region, cost, rollback, and deployment-planning evidence.

## Actions

- inspect: Inspect provider manifests, identity, secret, region, cost, and rollback boundaries.
- plan: Create a provider-neutral deployment plan without contacting or modifying cloud accounts.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
