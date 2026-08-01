# Installer Vm Lab

Clean-VM installation, first-run, upgrade, uninstall, rollback, and residue evidence.

## Actions

- inspect: Inspect clean-VM install, launch, upgrade, uninstall, rollback, and residue evidence.
- run: Run only an approved installer-lab evidence recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
