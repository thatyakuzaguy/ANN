# Stateful Workflow Verification

State, transition, invariant, idempotency, and interruption-recovery verification.

## Actions

- analyze: Inspect states, transitions, invariants, idempotency, and interruption recovery.
- run: Run only approved state-machine verification tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
