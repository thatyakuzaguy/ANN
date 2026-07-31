# Architectural Debt Ledger

Versioned architecture debt, trend, ownership, exception, and repayment evidence.

## Actions

- snapshot: Create a bounded architecture-debt snapshot from repository evidence and supplied metrics.
- compare: Compare debt snapshots and identify improving or regressing architecture metrics.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
