# Temporal Monetary Correctness

Timezone, DST, currency, decimal, rounding, tax, and exchange correctness verification.

## Actions

- inspect: Inspect timezone, DST, currency, decimal, rounding, and tax correctness evidence.
- run: Run only approved temporal and monetary correctness tests inside Docker Compose.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
