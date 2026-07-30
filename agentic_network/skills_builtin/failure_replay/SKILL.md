# Failure Replay

Deterministic failure recipes, redacted environment evidence, seeds, verification, and approved replay.

## Actions

- prepare: Create a deterministic replay recipe from bounded failure evidence.
- verify: Validate replay completeness, redaction, environment, and seed evidence.
- run: Run an approved fixed replay recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
