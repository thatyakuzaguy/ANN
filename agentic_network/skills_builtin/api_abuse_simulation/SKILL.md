# Api Abuse Simulation

Non-destructive authorization, rate, replay, validation, and resource-abuse verification.

## Actions

- inspect: Derive bounded authorization, rate-limit, injection, replay, and resource-abuse scenarios.
- run: Run only an approved non-destructive API abuse test recipe inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
