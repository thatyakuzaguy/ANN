# Messaging Deliverability

Messaging authentication, bounce, retry, consent, webhook, and deliverability verification.

## Actions

- inspect: Inspect email and notification authentication, bounce, retry, consent, and delivery evidence.
- run: Run only approved messaging deliverability contract tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
