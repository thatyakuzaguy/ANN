# Privacy Data Governance

PII, consent, retention, deletion, export, and tenant-isolation evidence requiring legal review.

## Actions

- scan: Inspect PII, consent, retention, deletion, export, and tenant-isolation evidence.
- retention_plan: Create a data-classification and retention plan requiring human legal review.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
