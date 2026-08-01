# Long Horizon Checkpoint Integrity

Checkpoint, idempotency, replay, approval, and recovery integrity evidence.

## Actions

- inspect: Inspect checkpoints, idempotency keys, replay guards, approvals, and recovery evidence.
- run: Run only an approved checkpoint-resume recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
