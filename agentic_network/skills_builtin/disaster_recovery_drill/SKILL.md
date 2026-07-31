# Disaster Recovery Drill

RPO, RTO, backup, restore, isolation, and approved recovery-drill verification.

## Actions

- inspect: Inspect RPO, RTO, backup integrity, restore isolation, and recovery assertions.
- run: Run only an approved destructive-isolated disaster-recovery test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
