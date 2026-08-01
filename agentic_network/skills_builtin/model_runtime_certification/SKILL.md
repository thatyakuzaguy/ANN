# Model Runtime Certification

Model manifest, backend, device, load-run-unload, memory, and rollback certification.

## Actions

- inspect: Inspect model manifest, backend, device, memory, load-run-unload, and rollback evidence.
- benchmark: Run only an approved model-runtime certification recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
