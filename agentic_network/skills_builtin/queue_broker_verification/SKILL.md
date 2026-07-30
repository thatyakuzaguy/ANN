# Queue Broker Verification

Queue ordering, idempotency, retry, dead-letter, and approved broker-test evidence.

## Actions

- inspect: Inspect queue schemas, ordering, idempotency, retries, and dead-letter handling.
- run: Run only an approved queue/broker integration recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
