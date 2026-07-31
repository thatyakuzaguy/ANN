# Release Channel Management

Alpha, beta, stable, promotion, downgrade, and compatibility evidence.

## Actions

- inspect: Inspect alpha, beta, stable, promotion, downgrade, and compatibility policies.
- verify: Verify bounded release-channel evidence without publishing a release.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
