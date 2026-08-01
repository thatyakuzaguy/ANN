# Performance Regression Bisect

Evidence-driven benchmark history localization without Git history mutation.

## Actions

- analyze: Rank supplied benchmark revisions and identify the first evidenced performance regression.
- run: Run only an approved performance-history recipe without mutating Git history.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
