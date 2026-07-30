# Visual Regression

Screenshot baselines, viewport evidence, and approved Playwright visual execution.

## Actions

- inspect: Inspect screenshot baselines, viewport coverage, masks, and visual evidence.
- run: Run only an approved Playwright visual-regression recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
