# Local Resource Guardian

Bounded project capacity, quota, retention, and isolated Compose cleanup controls.

## Actions

- snapshot: Measure bounded project and local disk capacity without enumerating unrelated host data.
- plan: Create quota, retention, and cleanup recommendations without deleting host data.
- cleanup: Run only the approved isolated Compose cleanup recipe; never delete arbitrary host paths.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
