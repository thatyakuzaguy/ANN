# Native Ui Automation

Windows native UI automation readiness and clean-machine evidence verification without host project execution.

## Actions

- inspect: Inspect Windows UI automation configuration and native application test readiness.
- verify: Verify supplied clean-machine native UI evidence without launching project binaries on the host.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
