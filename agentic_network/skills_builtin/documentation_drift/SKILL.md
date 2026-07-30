# Documentation Drift

Documentation-to-code command, route, setting, example, and approved doctest verification.

## Actions

- analyze: Compare documentation commands, routes, settings, and examples with repository evidence.
- run: Run only an approved documentation-test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
