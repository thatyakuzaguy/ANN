# Policy As Code

OPA, Rego, Conftest, infrastructure policy, and approved offline policy verification.

## Actions

- inspect: Inspect OPA, Rego, Conftest, infrastructure policies, and policy-test coverage.
- run: Run only an approved offline policy test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
