# Agent Tool Contract Verification

Agent tool schema, approval, timeout, idempotency, error, and result-contract verification.

## Actions

- inspect: Inspect tool schemas, approvals, timeouts, idempotency, error handling, and result validation.
- run: Run only approved agent-tool contract tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
