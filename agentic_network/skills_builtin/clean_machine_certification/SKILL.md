# Clean Machine Certification

Installer, first-run, uninstall, residue, and clean-machine evidence validation.

## Actions

- inspect: Inspect clean-machine installer, first-run, uninstall, and residue requirements.
- verify: Validate supplied clean-machine evidence without executing the installer on the host.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
