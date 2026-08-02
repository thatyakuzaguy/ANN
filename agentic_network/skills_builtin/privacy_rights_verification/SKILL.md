# Privacy Rights Verification

Export, erasure, retention, consent, tenancy, audit, and approved privacy-rights execution evidence.

## Actions

- inspect: Inspect export, erasure, retention, consent, tenancy, and audit implementation evidence.
- run: Run only approved privacy-rights verification tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
