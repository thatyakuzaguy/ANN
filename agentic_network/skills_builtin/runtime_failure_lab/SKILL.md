# Runtime Failure Lab

Controlled interruption, resource, Docker, model-integrity, packaging, and recovery verification.

## Actions

- inspect: Inspect bounded recovery evidence for interruption, resource, Docker, model, and packaging failures.
- run: Run only approved non-destructive runtime-failure tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
