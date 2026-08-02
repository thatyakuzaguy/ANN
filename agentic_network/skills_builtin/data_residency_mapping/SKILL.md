# Data Residency Mapping

Regional storage, processing, backup, transfer, retention, and subprocessor evidence mapping.

## Actions

- analyze: Map regional storage, processing, backup, transfer, retention, and subprocessor evidence.
- verify: Verify attested residency evidence while preserving mandatory human legal review.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
