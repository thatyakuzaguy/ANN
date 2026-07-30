# Memory Profiling

CPU, RAM, GPU, handle, connection, leak-test, and approved profiling evidence.

## Actions

- inspect: Inspect CPU, RAM, GPU, handle, connection, and leak-test evidence.
- run: Run only an approved memory profiling test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
